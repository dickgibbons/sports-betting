#!/usr/bin/env python3
"""
NHL 1st Period Totals Analysis UI

Shows daily schedule with team's "Scored" trends vs opponent's "Allowed" trends.
Layout matches Excel format with color-coded cells.
Now includes Moving Average visualizations!
"""

import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import os
import sys
from pathlib import Path

# Add analysis and utils paths for imports
PROJECT_DIR = "/Users/dickgibbons/sports-betting"
ANALYZERS_PATH = os.path.join(PROJECT_DIR, "nhl", "analysis")
UTILS_PATH = os.path.join(PROJECT_DIR, "nhl", "utils")
sys.path.insert(0, ANALYZERS_PATH)
sys.path.insert(0, UTILS_PATH)

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except ImportError:
    os.system("pip3 install plotly")
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots


# Team name mappings (API abbreviation -> Excel abbreviation)
TEAM_ABBREV_MAP = {
    'ANA': 'ANA', 'ARI': 'ARI', 'BOS': 'BOS', 'BUF': 'BUF', 'CGY': 'CGY',
    'CAR': 'CAR', 'CHI': 'CHI', 'COL': 'COL', 'CBJ': 'CBJ', 'DAL': 'DAL',
    'DET': 'DET', 'EDM': 'EDM', 'FLA': 'FLA', 'LAK': 'LAK', 'MIN': 'MIN',
    'MTL': 'MTL', 'NSH': 'NSH', 'NJD': 'NJD', 'NYI': 'NYI', 'NYR': 'NYR',
    'OTT': 'OTT', 'PHI': 'PHI', 'PIT': 'PIT', 'SJS': 'SJS', 'SEA': 'SEA',
    'STL': 'STL', 'TBL': 'TBL', 'TOR': 'TOR', 'VAN': 'VAN', 'VGK': 'VGK',
    'WSH': 'WSH', 'WPG': 'WPG', 'UTA': 'UTA'
}

# Full team names
TEAM_NAMES = {
    'ANA': 'Anaheim Ducks', 'ARI': 'Arizona Coyotes', 'BOS': 'Boston Bruins',
    'BUF': 'Buffalo Sabres', 'CGY': 'Calgary Flames', 'CAR': 'Carolina Hurricanes',
    'CHI': 'Chicago Blackhawks', 'COL': 'Colorado Avalanche', 'CBJ': 'Columbus Blue Jackets',
    'DAL': 'Dallas Stars', 'DET': 'Detroit Red Wings', 'EDM': 'Edmonton Oilers',
    'FLA': 'Florida Panthers', 'LAK': 'Los Angeles Kings', 'MIN': 'Minnesota Wild',
    'MTL': 'Montreal Canadiens', 'NSH': 'Nashville Predators', 'NJD': 'New Jersey Devils',
    'NYI': 'New York Islanders', 'NYR': 'New York Rangers', 'OTT': 'Ottawa Senators',
    'PHI': 'Philadelphia Flyers', 'PIT': 'Pittsburgh Penguins', 'SJS': 'San Jose Sharks',
    'SEA': 'Seattle Kraken', 'STL': 'St. Louis Blues', 'TBL': 'Tampa Bay Lightning',
    'TOR': 'Toronto Maple Leafs', 'VAN': 'Vancouver Canucks', 'VGK': 'Vegas Golden Knights',
    'WSH': 'Washington Capitals', 'WPG': 'Winnipeg Jets', 'UTA': 'Utah Hockey Club'
}


@st.cache_data(ttl=300)
def get_team_stats_from_cache(team_abbrev: str, season: str = "20252026"):
    """Get team 1st period stats directly from SQLite cache (live API data)"""
    try:
        from nhl_game_cache import NHLGameCache
        cache = NHLGameCache()
        df = cache.build_team_dataframe(team_abbrev, season)

        if df.empty:
            return None

        # Sort by date descending (most recent first) for L10/L5/L3 calculations
        df = df.sort_values('date', ascending=False).reset_index(drop=True)

        # Extract game-by-game 1P data for last 10 games
        scored_games = []
        allowed_games = []
        total_games = []

        for i, row in df.head(10).iterrows():
            loc = 'H' if row['is_home'] else 'A'
            scored_games.append({'value': int(row['period_1_for']), 'location': loc})
            allowed_games.append({'value': int(row['period_1_against']), 'location': loc})
            total_games.append({'value': int(row['period_1_total']), 'location': loc})

        # Calculate stats
        scored_vals = [g['value'] for g in scored_games]
        allowed_vals = [g['value'] for g in allowed_games]
        total_vals = [g['value'] for g in total_games]

        # All games for season stats
        all_scored = df['period_1_for'].tolist()
        all_allowed = df['period_1_against'].tolist()
        all_total = df['period_1_total'].tolist()

        stats = {
            'team': team_abbrev,
            'scored_games': scored_games,
            'allowed_games': allowed_games,
            'total_games': total_games,
            'games_played': len(df),
        }

        # Averages
        stats['avg_scored'] = sum(scored_vals) / len(scored_vals) if scored_vals else 0
        stats['avg_allowed'] = sum(allowed_vals) / len(allowed_vals) if allowed_vals else 0
        stats['avg_total'] = sum(total_vals) / len(total_vals) if total_vals else 0

        # L3 percentages
        stats['scored_over_0_l3'] = sum(1 for v in scored_vals[:3] if v > 0) / min(3, len(scored_vals)) * 100 if scored_vals else 0
        stats['allowed_over_0_l3'] = sum(1 for v in allowed_vals[:3] if v > 0) / min(3, len(allowed_vals)) * 100 if allowed_vals else 0
        stats['total_over_1_5_l3'] = sum(1 for v in total_vals[:3] if v > 1) / min(3, len(total_vals)) * 100 if total_vals else 0

        # L5 percentages
        stats['scored_over_0_l5'] = sum(1 for v in scored_vals[:5] if v > 0) / min(5, len(scored_vals)) * 100 if scored_vals else 0
        stats['allowed_over_0_l5'] = sum(1 for v in allowed_vals[:5] if v > 0) / min(5, len(allowed_vals)) * 100 if allowed_vals else 0
        stats['total_over_1_5_l5'] = sum(1 for v in total_vals[:5] if v > 1) / min(5, len(total_vals)) * 100 if total_vals else 0

        # L10 percentages
        stats['scored_over_0_l10'] = sum(1 for v in scored_vals[:10] if v > 0) / min(10, len(scored_vals)) * 100 if scored_vals else 0
        stats['allowed_over_0_l10'] = sum(1 for v in allowed_vals[:10] if v > 0) / min(10, len(allowed_vals)) * 100 if allowed_vals else 0
        stats['total_over_1_5_l10'] = sum(1 for v in total_vals[:10] if v > 1) / min(10, len(total_vals)) * 100 if total_vals else 0

        # Season percentages
        stats['Scored>0 Season'] = sum(1 for v in all_scored if v > 0) / len(all_scored) * 100 if all_scored else 0
        stats['Allowed>0 Season'] = sum(1 for v in all_allowed if v > 0) / len(all_allowed) * 100 if all_allowed else 0
        stats['Total>1.5 Season'] = sum(1 for v in all_total if v > 1) / len(all_total) * 100 if all_total else 0

        # L3 for trend summary
        stats['Scored>0 L3'] = stats['scored_over_0_l3']
        stats['Allowed>0 L3'] = stats['allowed_over_0_l3']
        stats['Total>1.5 L3'] = stats['total_over_1_5_l3']

        return stats

    except Exception as e:
        st.error(f"Error loading cache data for {team_abbrev}: {e}")
        return None


@st.cache_data(ttl=300)
def get_nhl_schedule(date_str: str):
    """Fetch NHL schedule for a given date"""
    try:
        url = f"https://api-web.nhle.com/v1/schedule/{date_str}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            games = []
            for day in data.get('gameWeek', []):
                if day.get('date') == date_str:
                    for game in day.get('games', []):
                        games.append({
                            'away': game.get('awayTeam', {}).get('abbrev', ''),
                            'home': game.get('homeTeam', {}).get('abbrev', ''),
                            'time': game.get('startTimeUTC', ''),
                            'venue': game.get('venue', {}).get('default', ''),
                        })
            return games
    except Exception as e:
        st.error(f"Error fetching schedule: {e}")
    return []


def get_cell_color(value: int, threshold: int = 0):
    """Get background color based on value - green for over threshold, red for at/under"""
    if value > threshold:
        return "#90EE90"  # Light green
    else:
        return "#FFB6B6"  # Light red/salmon


def get_pct_color(pct: float):
    """Get background color based on percentage"""
    if pct >= 80:
        return "#228B22"  # Dark green
    elif pct >= 60:
        return "#90EE90"  # Light green
    elif pct >= 40:
        return "#FFFF99"  # Light yellow
    else:
        return "#FFB6B6"  # Light red


def render_game_breakdown(away_team: str, home_team: str, away_stats: dict, home_stats: dict):
    """Render the game breakdown tables matching Excel format"""

    # CSS for styling
    st.markdown("""
    <style>
    .breakdown-table {
        border-collapse: collapse;
        margin: 10px 0;
        font-size: 14px;
        width: 100%;
    }
    .breakdown-table th, .breakdown-table td {
        border: 1px solid #ddd;
        padding: 6px 10px;
        text-align: center;
    }
    .breakdown-table th {
        background-color: #f0f0f0;
        font-weight: bold;
    }
    .section-header {
        background-color: #e0e0e0 !important;
        font-weight: bold;
        text-align: center !important;
    }
    .team-label {
        text-align: left !important;
        font-weight: bold;
    }
    .green-cell { background-color: #90EE90; }
    .dark-green-cell { background-color: #228B22; color: white; }
    .red-cell { background-color: #FFB6B6; }
    .yellow-cell { background-color: #FFFF99; }
    </style>
    """, unsafe_allow_html=True)

    # Build the game-by-game data
    away_scored = away_stats['scored_games'][:10]
    home_allowed = home_stats['allowed_games'][:10]
    home_scored = home_stats['scored_games'][:10]
    away_allowed = away_stats['allowed_games'][:10]
    away_total = away_stats['total_games'][:10]
    home_total = home_stats['total_games'][:10]

    # Section 1: Goals Scored Away - Allowed Home
    st.markdown(f"**Goals Scored (Away) - Goals Allowed (Home)**")

    # Create table HTML for scored away vs allowed home
    html = '<table class="breakdown-table">'

    # Header row
    html += '<tr><th></th><th></th>'
    for i in range(min(10, len(away_scored))):
        html += f'<th>G{i+1}</th>'
    html += '<th>L10 ov .5</th><th>Avg</th></tr>'

    # Away team scored row
    html += f'<tr><td class="team-label">{away_team}</td><td>Away</td>'
    for game in away_scored[:10]:
        color_class = "green-cell" if game['value'] > 0 else "red-cell"
        loc = game['location']
        html += f'<td class="{color_class}">{game["value"]} {loc}</td>'
    # Fill empty cells
    for _ in range(10 - len(away_scored)):
        html += '<td></td>'
    html += f'<td>{away_stats["scored_over_0_l10"]:.0f}%</td>'
    html += f'<td>Avg: {away_stats["avg_scored"]:.1f}</td></tr>'

    # Home team allowed row
    html += f'<tr><td class="team-label">{home_team}</td><td>Home</td>'
    for game in home_allowed[:10]:
        color_class = "green-cell" if game['value'] > 0 else "red-cell"
        loc = game['location']
        html += f'<td class="{color_class}">{game["value"]} {loc}</td>'
    for _ in range(10 - len(home_allowed)):
        html += '<td></td>'
    html += f'<td>{home_stats["allowed_over_0_l10"]:.0f}%</td>'
    html += f'<td>Avg: {home_stats["avg_allowed"]:.1f}</td></tr>'

    html += '</table>'
    st.markdown(html, unsafe_allow_html=True)

    # Section 2: Goals Scored Home - Allowed Away
    st.markdown(f"**Goals Scored (Home) - Goals Allowed (Away)**")

    html = '<table class="breakdown-table">'
    html += '<tr><th></th><th></th>'
    for i in range(min(10, len(home_scored))):
        html += f'<th>G{i+1}</th>'
    html += '<th>L10 ov .5</th><th>Avg</th></tr>'

    # Home team scored row
    html += f'<tr><td class="team-label">{home_team}</td><td>Home</td>'
    for game in home_scored[:10]:
        color_class = "green-cell" if game['value'] > 0 else "red-cell"
        loc = game['location']
        html += f'<td class="{color_class}">{game["value"]} {loc}</td>'
    for _ in range(10 - len(home_scored)):
        html += '<td></td>'
    html += f'<td>{home_stats["scored_over_0_l10"]:.0f}%</td>'
    html += f'<td>Avg: {home_stats["avg_scored"]:.1f}</td></tr>'

    # Away team allowed row
    html += f'<tr><td class="team-label">{away_team}</td><td>Away</td>'
    for game in away_allowed[:10]:
        color_class = "green-cell" if game['value'] > 0 else "red-cell"
        loc = game['location']
        html += f'<td class="{color_class}">{game["value"]} {loc}</td>'
    for _ in range(10 - len(away_allowed)):
        html += '<td></td>'
    html += f'<td>{away_stats["allowed_over_0_l10"]:.0f}%</td>'
    html += f'<td>Avg: {away_stats["avg_allowed"]:.1f}</td></tr>'

    html += '</table>'
    st.markdown(html, unsafe_allow_html=True)

    # Section 3: Over 1.5 Total Goals
    st.markdown(f"**Total Goals (Over 1.5)**")

    html = '<table class="breakdown-table">'
    html += '<tr><th></th><th></th>'
    for i in range(min(10, len(away_total))):
        html += f'<th>G{i+1}</th>'
    html += '<th>L10 ov 1.5</th><th>Avg</th></tr>'

    # Away team total row
    html += f'<tr><td class="team-label">{away_team}</td><td>Away</td>'
    for game in away_total[:10]:
        color_class = "green-cell" if game['value'] > 1 else "red-cell"
        loc = game['location']
        html += f'<td class="{color_class}">{game["value"]} {loc}</td>'
    for _ in range(10 - len(away_total)):
        html += '<td></td>'
    html += f'<td>{away_stats["total_over_1_5_l10"]:.0f}%</td>'
    html += f'<td>Avg: {away_stats["avg_total"]:.1f}</td></tr>'

    # Home team total row
    html += f'<tr><td class="team-label">{home_team}</td><td>Home</td>'
    for game in home_total[:10]:
        color_class = "green-cell" if game['value'] > 1 else "red-cell"
        loc = game['location']
        html += f'<td class="{color_class}">{game["value"]} {loc}</td>'
    for _ in range(10 - len(home_total)):
        html += '<td></td>'
    html += f'<td>{home_stats["total_over_1_5_l10"]:.0f}%</td>'
    html += f'<td>Avg: {home_stats["avg_total"]:.1f}</td></tr>'

    html += '</table>'
    st.markdown(html, unsafe_allow_html=True)

    # Summary percentages section
    st.markdown("**Trend Summary**")

    # Get trend percentages
    away_scored_season = away_stats.get('Scored>0 Season', away_stats['scored_over_0_l10'])
    away_allowed_season = away_stats.get('Allowed>0 Season', away_stats['allowed_over_0_l10'])
    away_total_season = away_stats.get('Total>1.5 Season', away_stats['total_over_1_5_l10'])
    home_scored_season = home_stats.get('Scored>0 Season', home_stats['scored_over_0_l10'])
    home_allowed_season = home_stats.get('Allowed>0 Season', home_stats['allowed_over_0_l10'])
    home_total_season = home_stats.get('Total>1.5 Season', home_stats['total_over_1_5_l10'])

    # Format values safely
    def safe_pct(val):
        if isinstance(val, str):
            return val
        return f"{val:.0f}%"

    html = '<table class="breakdown-table">'
    html += '''<tr>
        <th>Team</th>
        <th>Scored>0 Season</th><th>Allowed>0 Season</th><th>Total>1.5 Season</th>
        <th>Scored>0 L3</th><th>Allowed>0 L3</th><th>Total>1.5 L3</th>
        <th>Scored>0 L5</th><th>Allowed>0 L5</th><th>Total>1.5 L5</th>
        <th>Scored>0 L10</th><th>Allowed>0 L10</th><th>Total>1.5 L10</th>
    </tr>'''

    # Away team summary
    html += f'<tr><td class="team-label">{away_team}</td>'
    html += f'<td>{safe_pct(away_scored_season)}</td>'
    html += f'<td>{safe_pct(away_allowed_season)}</td>'
    html += f'<td>{safe_pct(away_total_season)}</td>'
    html += f'<td>{safe_pct(away_stats.get("Scored>0 L3", "N/A"))}</td>'
    html += f'<td>{safe_pct(away_stats.get("Allowed>0 L3", "N/A"))}</td>'
    html += f'<td>{safe_pct(away_stats.get("Total>1.5 L3", "N/A"))}</td>'
    html += f'<td>{away_stats["scored_over_0_l5"]:.0f}%</td>'
    html += f'<td>{away_stats["allowed_over_0_l5"]:.0f}%</td>'
    html += f'<td>{away_stats["total_over_1_5_l5"]:.0f}%</td>'
    html += f'<td>{away_stats["scored_over_0_l10"]:.0f}%</td>'
    html += f'<td>{away_stats["allowed_over_0_l10"]:.0f}%</td>'
    html += f'<td>{away_stats["total_over_1_5_l10"]:.0f}%</td></tr>'

    # Home team summary
    html += f'<tr><td class="team-label">{home_team}</td>'
    html += f'<td>{safe_pct(home_scored_season)}</td>'
    html += f'<td>{safe_pct(home_allowed_season)}</td>'
    html += f'<td>{safe_pct(home_total_season)}</td>'
    html += f'<td>{safe_pct(home_stats.get("Scored>0 L3", "N/A"))}</td>'
    html += f'<td>{safe_pct(home_stats.get("Allowed>0 L3", "N/A"))}</td>'
    html += f'<td>{safe_pct(home_stats.get("Total>1.5 L3", "N/A"))}</td>'
    html += f'<td>{home_stats["scored_over_0_l5"]:.0f}%</td>'
    html += f'<td>{home_stats["allowed_over_0_l5"]:.0f}%</td>'
    html += f'<td>{home_stats["total_over_1_5_l5"]:.0f}%</td>'
    html += f'<td>{home_stats["scored_over_0_l10"]:.0f}%</td>'
    html += f'<td>{home_stats["allowed_over_0_l10"]:.0f}%</td>'
    html += f'<td>{home_stats["total_over_1_5_l10"]:.0f}%</td></tr>'

    html += '</table>'
    st.markdown(html, unsafe_allow_html=True)


# ============================================================================
# MOVING AVERAGES SECTION
# ============================================================================

@st.cache_resource
def get_ma_analyzer():
    """Get the Moving Average analyzer with cache"""
    try:
        from nhl_game_cache import NHLGameCache
        return NHLGameCache()
    except ImportError:
        st.error("Cache module not found. Run from the nhl/ui directory.")
        return None


@st.cache_data(ttl=300)
def get_team_ma_dataframe(team_abbrev: str, season: str = "20252026"):
    """Get team data with moving averages calculated - 1st Period focused"""
    cache = get_ma_analyzer()
    if cache is None:
        return None

    df = cache.build_team_dataframe(team_abbrev, season)

    if df.empty:
        return None

    # Calculate moving averages for 1st period metrics
    for col in ["period_1_for", "period_1_against", "period_1_total"]:
        df[f"{col}_ma3"] = df[col].rolling(window=3, min_periods=1).mean()
        df[f"{col}_ma5"] = df[col].rolling(window=5, min_periods=1).mean()
        df[f"{col}_ma10"] = df[col].rolling(window=10, min_periods=1).mean()
        df[f"{col}_season"] = df[col].expanding().mean()

    return df


def create_ma_chart(df: pd.DataFrame, team: str, metric: str = "period_1_total"):
    """Create an interactive Plotly moving average chart - 1st Period focused"""
    if df is None or df.empty:
        return None

    metric_labels = {
        "period_1_for": "1P Goals For",
        "period_1_against": "1P Goals Against",
        "period_1_total": "1P Total Goals"
    }

    label = metric_labels.get(metric, metric)

    # Create figure
    fig = go.Figure()

    # Add bars for actual values
    colors = ['#2ecc71' if v >= df[metric].mean() else '#e74c3c' for v in df[metric]]

    fig.add_trace(go.Bar(
        x=df["game_num"],
        y=df[metric],
        name="Actual",
        marker_color=colors,
        opacity=0.4,
        hovertemplate="Game %{x}<br>%{y} goals<extra></extra>"
    ))

    # Add MA lines
    fig.add_trace(go.Scatter(
        x=df["game_num"], y=df[f"{metric}_ma3"],
        mode='lines', name='3-Game MA',
        line=dict(color='#3498db', width=2),
        hovertemplate="Game %{x}<br>3G MA: %{y:.2f}<extra></extra>"
    ))

    fig.add_trace(go.Scatter(
        x=df["game_num"], y=df[f"{metric}_ma5"],
        mode='lines', name='5-Game MA',
        line=dict(color='#9b59b6', width=2.5),
        hovertemplate="Game %{x}<br>5G MA: %{y:.2f}<extra></extra>"
    ))

    fig.add_trace(go.Scatter(
        x=df["game_num"], y=df[f"{metric}_ma10"],
        mode='lines', name='10-Game MA',
        line=dict(color='#e67e22', width=3),
        hovertemplate="Game %{x}<br>10G MA: %{y:.2f}<extra></extra>"
    ))

    fig.add_trace(go.Scatter(
        x=df["game_num"], y=df[f"{metric}_season"],
        mode='lines', name='Season Avg',
        line=dict(color='#1abc9c', width=2, dash='dash'),
        hovertemplate="Game %{x}<br>Season: %{y:.2f}<extra></extra>"
    ))

    fig.update_layout(
        title=f"{team} - {label} Moving Averages",
        xaxis_title="Game Number",
        yaxis_title=label,
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=400,
        margin=dict(l=50, r=50, t=80, b=50)
    )

    return fig


def create_matchup_comparison_chart(away_df: pd.DataFrame, home_df: pd.DataFrame,
                                     away_team: str, home_team: str,
                                     metric: str = "period_1_total"):
    """Create side-by-side MA comparison for a matchup - 1st Period focused"""
    metric_labels = {
        "period_1_for": "1P Goals For",
        "period_1_against": "1P Goals Against",
        "period_1_total": "1P Total Goals"
    }
    label = metric_labels.get(metric, metric)

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=[f"{away_team} (Away)", f"{home_team} (Home)"],
        horizontal_spacing=0.08
    )

    # Away team
    if away_df is not None and not away_df.empty:
        colors_away = ['#3498db' if v >= away_df[metric].mean() else '#95a5a6' for v in away_df[metric]]
        fig.add_trace(go.Bar(x=away_df["game_num"], y=away_df[metric],
                             marker_color=colors_away, opacity=0.4, showlegend=False), row=1, col=1)
        fig.add_trace(go.Scatter(x=away_df["game_num"], y=away_df[f"{metric}_ma3"],
                                  mode='lines', name='3G MA', line=dict(color='#3498db', width=2)), row=1, col=1)
        fig.add_trace(go.Scatter(x=away_df["game_num"], y=away_df[f"{metric}_ma5"],
                                  mode='lines', name='5G MA', line=dict(color='#9b59b6', width=2.5)), row=1, col=1)
        fig.add_trace(go.Scatter(x=away_df["game_num"], y=away_df[f"{metric}_ma10"],
                                  mode='lines', name='10G MA', line=dict(color='#e67e22', width=3)), row=1, col=1)

    # Home team
    if home_df is not None and not home_df.empty:
        colors_home = ['#e74c3c' if v >= home_df[metric].mean() else '#95a5a6' for v in home_df[metric]]
        fig.add_trace(go.Bar(x=home_df["game_num"], y=home_df[metric],
                             marker_color=colors_home, opacity=0.4, showlegend=False), row=1, col=2)
        fig.add_trace(go.Scatter(x=home_df["game_num"], y=home_df[f"{metric}_ma3"],
                                  mode='lines', showlegend=False, line=dict(color='#3498db', width=2)), row=1, col=2)
        fig.add_trace(go.Scatter(x=home_df["game_num"], y=home_df[f"{metric}_ma5"],
                                  mode='lines', showlegend=False, line=dict(color='#9b59b6', width=2.5)), row=1, col=2)
        fig.add_trace(go.Scatter(x=home_df["game_num"], y=home_df[f"{metric}_ma10"],
                                  mode='lines', showlegend=False, line=dict(color='#e67e22', width=3)), row=1, col=2)

    fig.update_layout(
        title=f"Matchup: {away_team} @ {home_team} - {label}",
        height=350,
        legend=dict(orientation="h", yanchor="bottom", y=1.08, xanchor="center", x=0.5),
        margin=dict(l=50, r=50, t=100, b=50)
    )

    fig.update_xaxes(title_text="Game #", row=1, col=1)
    fig.update_xaxes(title_text="Game #", row=1, col=2)

    return fig


def get_trend_emoji(ma3: float, ma10: float, season: float) -> str:
    """Get trend indicator emoji"""
    if ma3 > ma10 * 1.15:
        return "🔥 HOT"
    elif ma3 > ma10 * 1.05:
        return "📈 Rising"
    elif ma3 < ma10 * 0.85:
        return "🥶 COLD"
    elif ma3 < ma10 * 0.95:
        return "📉 Falling"
    else:
        return "➡️ Steady"


def render_ma_summary_table(away_df: pd.DataFrame, home_df: pd.DataFrame,
                             away_team: str, home_team: str):
    """Render a summary table of current MAs for both teams - 1st Period focused"""
    metrics = ["period_1_total", "period_1_for", "period_1_against"]
    labels = ["1P Total Goals", "1P Goals For", "1P Goals Against"]

    data = []
    for metric, label in zip(metrics, labels):
        row = {"Metric": label}

        if away_df is not None and not away_df.empty:
            latest_away = away_df.iloc[-1]
            row[f"{away_team} 3G"] = f"{latest_away[f'{metric}_ma3']:.2f}"
            row[f"{away_team} 5G"] = f"{latest_away[f'{metric}_ma5']:.2f}"
            row[f"{away_team} 10G"] = f"{latest_away[f'{metric}_ma10']:.2f}"
            row[f"{away_team} Trend"] = get_trend_emoji(
                latest_away[f'{metric}_ma3'],
                latest_away[f'{metric}_ma10'],
                latest_away[f'{metric}_season']
            )

        if home_df is not None and not home_df.empty:
            latest_home = home_df.iloc[-1]
            row[f"{home_team} 3G"] = f"{latest_home[f'{metric}_ma3']:.2f}"
            row[f"{home_team} 5G"] = f"{latest_home[f'{metric}_ma5']:.2f}"
            row[f"{home_team} 10G"] = f"{latest_home[f'{metric}_ma10']:.2f}"
            row[f"{home_team} Trend"] = get_trend_emoji(
                latest_home[f'{metric}_ma3'],
                latest_home[f'{metric}_ma10'],
                latest_home[f'{metric}_season']
            )

        data.append(row)

    return pd.DataFrame(data)


def render_moving_averages_page(date_str: str):
    """Render the Moving Averages analysis page - 1st Period focused"""
    st.subheader("📈 1st Period Moving Averages")
    st.markdown("*Stock-style trend analysis for today's matchups - 1st Period Goals*")

    # Get today's games
    games = get_nhl_schedule(date_str)

    if not games:
        st.warning(f"No games found for {date_str}")
        return

    st.markdown(f"**{len(games)} games scheduled for {date_str}**")

    # Metric selector - 1st period metrics only
    metric = st.selectbox(
        "Select Metric",
        ["period_1_total", "period_1_for", "period_1_against"],
        format_func=lambda x: {
            "period_1_total": "1P Total Goals",
            "period_1_for": "1P Goals For",
            "period_1_against": "1P Goals Against"
        }.get(x, x)
    )

    # Display each matchup
    for game in games:
        away_team = game['away']
        home_team = game['home']

        with st.expander(f"🏒 **{away_team} @ {home_team}**", expanded=True):
            # Load MA data
            with st.spinner(f"Loading data for {away_team} vs {home_team}..."):
                away_df = get_team_ma_dataframe(away_team)
                home_df = get_team_ma_dataframe(home_team)

            if away_df is None and home_df is None:
                st.error("Could not load data for this matchup")
                continue

            # Summary table
            st.markdown("**Current Moving Averages**")
            summary_df = render_ma_summary_table(away_df, home_df, away_team, home_team)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)

            # Betting insight - 1st Period focused
            if away_df is not None and home_df is not None:
                away_latest = away_df.iloc[-1]
                home_latest = home_df.iloc[-1]

                combined_ma5 = (away_latest['period_1_total_ma5'] + home_latest['period_1_total_ma5']) / 2
                combined_season = (away_latest['period_1_total_season'] + home_latest['period_1_total_season']) / 2

                # Both teams hot in 1P
                if (away_latest['period_1_total_ma3'] > away_latest['period_1_total_ma10'] * 1.1 and
                    home_latest['period_1_total_ma3'] > home_latest['period_1_total_ma10'] * 1.1):
                    st.success(f"💡 **1P OVER Signal**: Both teams trending HOT in 1st period. Combined 5G MA: {combined_ma5:.2f}")
                # Both teams cold in 1P
                elif (away_latest['period_1_total_ma3'] < away_latest['period_1_total_ma10'] * 0.9 and
                      home_latest['period_1_total_ma3'] < home_latest['period_1_total_ma10'] * 0.9):
                    st.info(f"💡 **1P UNDER Signal**: Both teams trending COLD in 1st period. Combined 5G MA: {combined_ma5:.2f}")
                else:
                    st.caption(f"Combined 1P 5G MA: {combined_ma5:.2f} | Season Avg: {combined_season:.2f}")

            # Comparison chart
            fig = create_matchup_comparison_chart(away_df, home_df, away_team, home_team, metric)
            st.plotly_chart(fig, use_container_width=True)

            # Individual team charts (collapsible)
            col1, col2 = st.columns(2)
            with col1:
                if away_df is not None:
                    fig_away = create_ma_chart(away_df, away_team, metric)
                    st.plotly_chart(fig_away, use_container_width=True)
            with col2:
                if home_df is not None:
                    fig_home = create_ma_chart(home_df, home_team, metric)
                    st.plotly_chart(fig_home, use_container_width=True)


def main():
    st.set_page_config(
        page_title="NHL Analysis Dashboard",
        page_icon="🏒",
        layout="wide"
    )

    st.title("🏒 NHL Analysis Dashboard")

    # Sidebar
    st.sidebar.header("Settings")

    selected_date = st.sidebar.date_input(
        "Select Date",
        value=datetime.now().date()
    )
    date_str = selected_date.strftime("%Y-%m-%d")

    # Main tabs
    tab1, tab2 = st.tabs(["📊 1st Period Totals", "📈 Moving Averages"])

    # ======== TAB 1: 1st Period Totals (now using live cache data) ========
    with tab1:
        st.markdown("*Team Scored vs Opponent Allowed Trends - Live API Data*")

        # Get schedule
        games = get_nhl_schedule(date_str)

        if not games:
            st.warning(f"No games found for {date_str}")
            st.info("Try selecting a different date.")
        else:
            st.subheader(f"Games for {date_str}")
            st.markdown(f"**{len(games)} games scheduled**")
            st.sidebar.success("Data: Live API Cache")

            # Display each matchup
            for game in games:
                away_abbrev = TEAM_ABBREV_MAP.get(game['away'], game['away'])
                home_abbrev = TEAM_ABBREV_MAP.get(game['home'], game['home'])

                # Get stats from live cache instead of Excel
                away_stats = get_team_stats_from_cache(away_abbrev)
                home_stats = get_team_stats_from_cache(home_abbrev)

                if not away_stats or not home_stats:
                    st.warning(f"Missing data for {game['away']} @ {game['home']}")
                    continue

                # Create expandable card for each game
                away_name = TEAM_NAMES.get(game['away'], game['away'])
                home_name = TEAM_NAMES.get(game['home'], game['home'])

                with st.expander(f"**{away_name} @ {home_name}**", expanded=True):
                    # Show games played count
                    st.caption(f"{away_abbrev}: {away_stats['games_played']} games | {home_abbrev}: {home_stats['games_played']} games")
                    render_game_breakdown(game['away'], game['home'], away_stats, home_stats)

            # Footer
            st.markdown("---")
            st.caption("Data source: Live NHL API via SQLite cache")
            st.caption("Green = Over threshold | Red = Under threshold")

    # ======== TAB 2: Moving Averages (new) ========
    with tab2:
        render_moving_averages_page(date_str)


if __name__ == "__main__":
    main()
