"""
Global Soccer Schedule Dashboard
Displays game schedules for Top 50 leagues with detailed team stats
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import math
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from league_config import (
    ALL_LEAGUES, TOP_50_LEAGUES, REGIONS, LEAGUE_BY_ID,
    get_leagues_by_region, get_season_year
)
from schedule_data_fetcher import get_fetcher

# Load team stats
STATS_FILE = os.path.join(os.path.dirname(__file__), "data", "team_stats", "team_stats_current.csv")

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_team_stats():
    """Load team statistics from CSV"""
    if os.path.exists(STATS_FILE):
        df = pd.read_csv(STATS_FILE)
        # Create lookup by team name (lowercase for matching)
        return {row['team'].lower(): row.to_dict() for _, row in df.iterrows()}
    return {}

# Page configuration
st.set_page_config(
    page_title="Global Soccer Schedule",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .match-table {
        font-size: 0.85rem;
    }
    .home-row {
        background-color: #e8f4f8 !important;
    }
    .away-row {
        background-color: #fff8e8 !important;
    }
    .stat-good { color: #27ae60; font-weight: bold; }
    .stat-medium { color: #f39c12; }
    .stat-poor { color: #e74c3c; }
    div[data-testid="stDataFrame"] {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = datetime.now().date()
    if "selected_region" not in st.session_state:
        st.session_state.selected_region = "All"


def render_sidebar():
    """Render the sidebar with filters"""
    with st.sidebar:
        st.markdown("## Filters")

        # Date selection
        st.markdown("### Date")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("◀ Prev", width="stretch"):
                st.session_state.selected_date -= timedelta(days=1)
                st.rerun()
        with col2:
            if st.button("Today", width="stretch"):
                st.session_state.selected_date = datetime.now().date()
                st.rerun()
        with col3:
            if st.button("Next ▶", width="stretch"):
                st.session_state.selected_date += timedelta(days=1)
                st.rerun()

        selected_date = st.date_input(
            "Select date",
            value=st.session_state.selected_date,
            key="date_picker"
        )
        if selected_date != st.session_state.selected_date:
            st.session_state.selected_date = selected_date
            st.rerun()

        st.markdown("---")

        # Region filter
        st.markdown("### Region")
        regions = ["All"] + list(REGIONS.keys())
        selected_region = st.selectbox(
            "Select region",
            regions,
            index=regions.index(st.session_state.selected_region)
        )
        if selected_region != st.session_state.selected_region:
            st.session_state.selected_region = selected_region

        # Team search
        st.markdown("---")
        st.markdown("### Search")
        team_search = st.text_input("Search team", "")

        return team_search


def format_time(timestamp: int) -> str:
    """Format timestamp to readable time"""
    if not timestamp:
        return "TBD"
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%H:%M")
    except Exception:
        return "TBD"


def decimal_to_american(decimal_odds: float) -> str:
    """Convert decimal odds to American odds format"""
    if decimal_odds is None:
        return "-"
    try:
        d = float(decimal_odds)
    except (TypeError, ValueError):
        return "-"
    if math.isnan(d) or d <= 1:
        return "-"

    if d >= 2.0:
        # Positive American odds (underdog)
        american = (d - 1) * 100
        return f"+{int(round(american))}"
    else:
        # Negative American odds (favorite)
        american = -100 / (d - 1)
        if math.isnan(american) or math.isinf(american):
            return "-"
        return f"{int(round(american))}"


def format_standing(stats: dict) -> str:
    """Format standing as 'position/total_points pts' instead of 'position/ppg'"""
    standing = stats.get("standing", "-")
    if standing == "-" or not standing:
        return "-"

    try:
        # Parse format like "2/1.8ppg"
        if "/" in standing and "ppg" in standing.lower():
            parts = standing.split("/")
            position = parts[0]
            ppg_str = parts[1].lower().replace("ppg", "").strip()
            ppg = float(ppg_str)
            games_played = stats.get("games_played", 0)
            if games_played:
                total_points = int(round(ppg * games_played))
                return f"{position}/{total_points}pts"
        return standing
    except (ValueError, IndexError):
        return standing


def get_team_stats(team_name: str, stats_lookup: dict, location: str) -> dict:
    """Get stats for a team from the lookup"""
    # Try exact match first, then fuzzy match
    team_lower = team_name.lower()

    if team_lower in stats_lookup:
        return stats_lookup[team_lower]

    # Try partial match
    for key, stats in stats_lookup.items():
        if team_lower in key or key in team_lower:
            return stats
        # Match on key words
        team_words = set(team_lower.split())
        key_words = set(key.split())
        if team_words & key_words:
            return stats

    return {}


def create_detailed_dataframe(fixtures: list, stats_lookup: dict) -> pd.DataFrame:
    """
    Create a detailed dataframe with one row per team (2 rows per match).
    Includes all requested columns with stats from lookup.
    """
    rows = []
    match_id = 1

    for fixture in fixtures:
        time_str = format_time(fixture.get("timestamp"))
        league_name = fixture.get("league_name", "")
        league_country = fixture.get("league_country", "")

        home_team = fixture.get("home_team", "")
        away_team = fixture.get("away_team", "")

        # Get stats for both teams
        home_stats = get_team_stats(home_team, stats_lookup, "home")
        away_stats = get_team_stats(away_team, stats_lookup, "away")

        # Home team row
        home_row = {
            "Match": match_id,
            "Time": time_str,
            "Country": league_country,
            "League": league_name,
            "Location": "Home",
            "Team": home_team,
            "Opponent": away_team,
            "Record": home_stats.get("record", "-"),
            "H/A Record": home_stats.get("home_record", "-"),
            "Standing": format_standing(home_stats),
            "Avg GF": str(home_stats.get("avg_goals_for", "-")),
            "Avg GA": str(home_stats.get("avg_goals_against", "-")),
            "BTTS": home_stats.get("btts_l10", "-"),
            "BTTS L5": home_stats.get("btts_l5", "-"),
            "BTTS H/A": home_stats.get("btts_home_l10", "-"),
            "Ov 1.5": home_stats.get("over_15_pct", "-"),
            "Ov 2.5": home_stats.get("over_25_pct", "-"),
            "Ov 3.5": home_stats.get("over_35_pct", "-"),
            "Ov 1.5 H/A": home_stats.get("over_15_home_pct", "-"),
            "Ov 2.5 H/A": home_stats.get("over_25_home_pct", "-"),
            "Ov 3.5 H/A": home_stats.get("over_35_home_pct", "-"),
            "Team Ov 0.5": home_stats.get("team_over_05_pct", "-"),
            "Team Ov 1.5": home_stats.get("team_over_15_pct", "-"),
            "Team Ov 2.5": home_stats.get("team_over_25_pct", "-"),
            "Team Ov 1.5 H/A": home_stats.get("team_over_15_home_pct", "-"),
            "Team Ov 2.5 H/A": home_stats.get("team_over_25_home_pct", "-"),
            "1H Score%": home_stats.get("scored_1h_pct", "-"),
            "2H Score%": home_stats.get("scored_2h_pct", "-"),
            "1H Ov 0.5": home_stats.get("first_half_over_05_pct", "-"),
            "1H Ov 1.5": home_stats.get("first_half_over_15_pct", "-"),
            "2H Ov 0.5": home_stats.get("second_half_over_05_pct", "-"),
            "2H Ov 1.5": home_stats.get("second_half_over_15_pct", "-"),
            "H Odds": decimal_to_american(fixture.get('home_odds')),
            "D Odds": decimal_to_american(fixture.get('draw_odds')),
            "A Odds": decimal_to_american(fixture.get('away_odds')),
        }
        rows.append(home_row)

        # Away team row
        away_row = {
            "Match": match_id,
            "Time": "",
            "Country": "",
            "League": "",
            "Location": "Away",
            "Team": away_team,
            "Opponent": home_team,
            "Record": away_stats.get("record", "-"),
            "H/A Record": away_stats.get("away_record", "-"),
            "Standing": format_standing(away_stats),
            "Avg GF": str(away_stats.get("avg_goals_for", "-")),
            "Avg GA": str(away_stats.get("avg_goals_against", "-")),
            "BTTS": away_stats.get("btts_l10", "-"),
            "BTTS L5": away_stats.get("btts_l5", "-"),
            "BTTS H/A": away_stats.get("btts_away_l10", "-"),
            "Ov 1.5": away_stats.get("over_15_pct", "-"),
            "Ov 2.5": away_stats.get("over_25_pct", "-"),
            "Ov 3.5": away_stats.get("over_35_pct", "-"),
            "Ov 1.5 H/A": away_stats.get("over_15_away_pct", "-"),
            "Ov 2.5 H/A": away_stats.get("over_25_away_pct", "-"),
            "Ov 3.5 H/A": away_stats.get("over_35_away_pct", "-"),
            "Team Ov 0.5": away_stats.get("team_over_05_pct", "-"),
            "Team Ov 1.5": away_stats.get("team_over_15_pct", "-"),
            "Team Ov 2.5": away_stats.get("team_over_25_pct", "-"),
            "Team Ov 1.5 H/A": away_stats.get("team_over_15_away_pct", "-"),
            "Team Ov 2.5 H/A": away_stats.get("team_over_25_away_pct", "-"),
            "1H Score%": away_stats.get("scored_1h_pct", "-"),
            "2H Score%": away_stats.get("scored_2h_pct", "-"),
            "1H Ov 0.5": away_stats.get("first_half_over_05_pct", "-"),
            "1H Ov 1.5": away_stats.get("first_half_over_15_pct", "-"),
            "2H Ov 0.5": away_stats.get("second_half_over_05_pct", "-"),
            "2H Ov 1.5": away_stats.get("second_half_over_15_pct", "-"),
            "H Odds": "",
            "D Odds": "",
            "A Odds": "",
        }
        rows.append(away_row)

        match_id += 1

    return pd.DataFrame(rows)


def style_dataframe(df: pd.DataFrame):
    """Apply styling to the dataframe"""
    def highlight_location(row):
        if row['Location'] == 'Home':
            return ['background-color: #e8f4f8'] * len(row)
        else:
            return ['background-color: #fff8e8'] * len(row)

    return df.style.apply(highlight_location, axis=1)


def main():
    """Main application entry point"""
    init_session_state()

    # Header
    st.markdown('<div class="main-header">⚽ Global Soccer Schedule - Detailed Stats</div>', unsafe_allow_html=True)

    # Sidebar filters
    team_search = render_sidebar()

    # Display selected date
    date_str = st.session_state.selected_date.strftime("%A, %B %d, %Y")
    st.markdown(f"### {date_str}")

    # Get data fetcher
    fetcher = get_fetcher()

    # Determine which leagues to fetch
    leagues_to_fetch = get_leagues_by_region(st.session_state.selected_region)

    # Fetch fixtures with loading indicator
    with st.spinner("Loading fixtures from The Odds API..."):
        selected_date = datetime.combine(st.session_state.selected_date, datetime.min.time())
        fixtures_df = fetcher.get_fixtures_dataframe(selected_date, leagues_to_fetch)

    if fixtures_df.empty:
        st.warning("No games scheduled for this date. Try clicking 'Next' to see upcoming games.")

        # Show what dates have games
        st.markdown("### Checking upcoming dates...")
        for i in range(1, 8):
            check_date = datetime.combine(st.session_state.selected_date + timedelta(days=i), datetime.min.time())
            check_df = fetcher.get_fixtures_dataframe(check_date, leagues_to_fetch)
            if not check_df.empty:
                st.info(f"Found {len(check_df)} games on {check_date.strftime('%A, %B %d')}")
                break
        return

    fixtures_list = fixtures_df.to_dict("records")

    # Apply team search filter
    if team_search:
        search_lower = team_search.lower()
        fixtures_list = [
            f for f in fixtures_list
            if search_lower in f.get("home_team", "").lower()
            or search_lower in f.get("away_team", "").lower()
        ]

    if not fixtures_list:
        st.warning("No games match your search.")
        return

    # Load team stats and create detailed dataframe
    stats_lookup = load_team_stats()
    detailed_df = create_detailed_dataframe(fixtures_list, stats_lookup)

    # Stats summary
    num_matches = len(fixtures_list)
    num_leagues = len(set(f.get("league_name") for f in fixtures_list))

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Matches", num_matches)
    with col2:
        st.metric("Leagues", num_leagues)
    with col3:
        st.metric("Teams", num_matches * 2)

    st.markdown("---")

    # Display options
    col1, col2 = st.columns([3, 1])
    with col2:
        show_all_cols = st.checkbox("Show all columns", value=False)

    # Column selection
    if show_all_cols:
        display_cols = detailed_df.columns.tolist()
    else:
        # Default columns
        display_cols = [
            "Match", "Time", "Country", "League", "Location", "Team",
            "Record", "H/A Record", "Standing", "Avg GF", "Avg GA",
            "BTTS", "BTTS L5", "BTTS H/A",
            "Ov 1.5", "Ov 2.5", "Ov 3.5",
            "Ov 1.5 H/A", "Ov 2.5 H/A", "Ov 3.5 H/A",
            "Team Ov 1.5", "Team Ov 2.5",
            "Team Ov 1.5 H/A", "Team Ov 2.5 H/A",
            "1H Score%",
            "1H Ov 0.5", "1H Ov 1.5", "2H Ov 0.5", "2H Ov 1.5",
            "H Odds", "D Odds", "A Odds"
        ]

    # Display the dataframe
    st.dataframe(
        detailed_df[display_cols],
        width="stretch",
        height=600,
        hide_index=True,
    )

    # Export
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        csv = detailed_df.to_csv(index=False)
        st.download_button(
            label="Download Full CSV",
            data=csv,
            file_name=f"soccer_schedule_detailed_{st.session_state.selected_date}.csv",
            mime="text/csv",
            width="stretch"
        )

    # Footer with column legend
    with st.expander("Column Descriptions"):
        st.markdown("""
        | Column | Description |
        |--------|-------------|
        | Match | Match ID for grouping home/away |
        | Time | Kickoff time (local) |
        | Country | League country |
        | League | League name |
        | Location | Home or Away |
        | Team | Team name |
        | Opponent | Opposition team |
        | Record | Overall W-D-L record |
        | H/A Record | Home or Away specific record |
        | Standing | League position / total points (e.g., 2/32pts) |
        | BTTS | Both Teams To Score in last 10 games (e.g., 7/10) |
        | BTTS L5 | Both Teams To Score in last 5 games |
        | BTTS H/A | BTTS % in last 10 Home games (for home team) or Away games (for away team) |
        | Ov 1.5/2.5/3.5 | % of games over 1.5/2.5/3.5 goals |
        | Team Ov 0.5/1.5/2.5 | % team scored over X goals |
        | 1H Score% | % team scored in first half |
        | 2H Score% | % team scored in second half |
        | 1H Ov 0.5 | % of games with 1+ goals in first half |
        | 1H Ov 1.5 | % of games with 2+ goals in first half |
        | 2H Ov 0.5 | % of games with 1+ goals in second half |
        | 2H Ov 1.5 | % of games with 2+ goals in second half |
        | Corners For/Ag | Average corners for/against |
        | H/D/A Odds | Decimal odds (Home/Draw/Away) |
        """)

    st.markdown("""
    <div style="text-align: center; color: #7f8c8d; font-size: 0.8rem; margin-top: 20px;">
        Data from The Odds API | Stats columns show '-' until populated
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
