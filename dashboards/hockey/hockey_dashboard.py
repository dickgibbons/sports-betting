#!/usr/bin/env python3
"""Flask-based Hockey Dashboard showing daily schedule with team stats."""

from flask import Flask, render_template, jsonify, request
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pandas as pd
import os
from pathlib import Path

_FLASK_APP_DIR = Path(__file__).resolve().parent
app = Flask(
    __name__,
    root_path=str(_FLASK_APP_DIR),
    template_folder="templates",
)
app.config["TEMPLATES_AUTO_RELOAD"] = True

_SPORTS_BETTING_ROOT = Path(__file__).resolve().parents[2]
_DAILY_REPORTS = Path(
    os.environ.get("SPORTS_BETTING_DAILY_REPORTS", _SPORTS_BETTING_ROOT / "Daily Reports")
)

API_KEY = "960c628e1c91c4b1f125e1eec52ad862"
BASE_URL = "https://v1.hockey.api-sports.io"

# DraftKings leagues (ID, Name)
DRAFTKINGS_LEAGUES = {
    57: "NHL",
    16: "Finnish - SM Liiga",
    47: "Sweden - SHL",
    49: "Sweden - HockeyAllsvenskan",
    69: "Alps Hockey League",
    70: "Austria Ice Hockey League",
    146: "Champions Hockey League",
    11: "Czech - Chance Liga",
    12: "Denmark - Metal Ligaen",
    14: "Finnish - Mestis",
    18: "France - Ligue Magnus",
    19: "German - DEL",
    26: "Latvia - Premjer Liga",
    86: "Norway - EHL",
    30: "Norway - 1st Division",
    32: "Poland - Extraliga",
    261: "PWHL Women",
    91: "Slovakia - Extraliga",
    42: "Slovakia - Liga1",
    51: "Swiss - National League",
    52: "Switzerland - Swiss League",
}

# Stat file paths for each period
STATS_FILES = {
    "season": str(_DAILY_REPORTS / "draftkings_hockey_team_stats_with_1p.csv"),
    "L10": str(_DAILY_REPORTS / "draftkings_hockey_team_stats_L10.csv"),
    "L5": str(_DAILY_REPORTS / "draftkings_hockey_team_stats_L5.csv"),
}

# Load team stats for all periods
ALL_TEAM_STATS = {}  # {period: {(league, team): stats}}
ALL_LEAGUE_AVERAGES = {}  # {period: {league: averages}}

# Standings cache
STANDINGS_CACHE = {}  # {(league_id, team_name): standings_info}
STANDINGS_CACHE_TIME = None

def fetch_all_standings():
    """Fetch standings for all leagues and cache them."""
    global STANDINGS_CACHE, STANDINGS_CACHE_TIME

    # Cache for 1 hour
    if STANDINGS_CACHE_TIME and (datetime.now() - STANDINGS_CACHE_TIME).total_seconds() < 3600:
        return STANDINGS_CACHE

    headers = {"x-apisports-key": API_KEY}
    standings_data = {}

    # Determine current season (season starts in September)
    now = datetime.now()
    season = now.year if now.month >= 9 else now.year - 1

    for league_id, league_name in DRAFTKINGS_LEAGUES.items():
        try:
            url = f"{BASE_URL}/standings"
            params = {"league": league_id, "season": season}
            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                standings_list = data.get('response', [])

                # Find regular season standings (skip preseason)
                regular_season_teams = []
                for group in standings_list:
                    if isinstance(group, list) and group:
                        stage = group[0].get('stage', '')
                        # Skip preseason data
                        if 'Pre-season' in stage or 'Preseason' in stage:
                            continue
                        regular_season_teams.extend(group)

                # Deduplicate teams - keep only conference standings (not division)
                # For NHL: use Eastern/Western Conference (16 teams each)
                seen_teams = {}
                conference_groups = ['Conference', 'Konferenz']  # Handle different languages

                for team_data in regular_season_teams:
                    team_name = team_data.get('team', {}).get('name', '')
                    group_name = team_data.get('group', {}).get('name', '') or ''
                    position = team_data.get('position', 0)
                    points = team_data.get('points', 0)
                    games = team_data.get('games', {})

                    wins = games.get('win', {}).get('total', 0)
                    losses = games.get('lose', {}).get('total', 0)
                    otl = games.get('lose_overtime', {}).get('total', 0)
                    played = games.get('played', 0)

                    # Skip if we've seen this team and current entry is a division (prefer conference)
                    is_conference = any(c in group_name for c in conference_groups) if group_name else False

                    if team_name in seen_teams:
                        # Only replace if current is conference and previous wasn't
                        prev_is_conf = seen_teams[team_name].get('is_conference', False)
                        if not is_conference or prev_is_conf:
                            continue

                    # Format record as W-L-OTL (hockey style)
                    record = f"{wins}-{losses}-{otl}"

                    seen_teams[team_name] = {
                        'position': position,
                        'group': group_name,
                        'is_conference': is_conference,
                        'points': points,
                        'record': record,
                        'wins': wins,
                        'losses': losses,
                        'otl': otl,
                        'played': played
                    }

                # Count teams per group type for total_teams
                # For conferences, count teams in that conference
                group_counts = {}
                for team_name, info in seen_teams.items():
                    grp = info['group']
                    group_counts[grp] = group_counts.get(grp, 0) + 1

                # Add to standings data
                for team_name, info in seen_teams.items():
                    total_teams = group_counts.get(info['group'], len(seen_teams))
                    standings_data[(league_name, team_name)] = {
                        'position': info['position'],
                        'total_teams': total_teams,
                        'points': info['points'],
                        'record': info['record'],
                        'wins': info['wins'],
                        'losses': info['losses'],
                        'otl': info['otl']
                    }

        except Exception as e:
            print(f"Error fetching standings for {league_name}: {e}")
            continue

    STANDINGS_CACHE = standings_data
    STANDINGS_CACHE_TIME = datetime.now()
    print(f"Loaded standings for {len(standings_data)} teams")
    return standings_data

def load_stats_for_period(period):
    """Load team stats and league averages for a specific period."""
    stats_file = STATS_FILES.get(period)
    team_stats = {}
    league_averages = {}

    if stats_file and os.path.exists(stats_file):
        df = pd.read_csv(stats_file)

        # Calculate league averages
        league_agg = df.groupby('league').agg({
            'avg_scored': 'mean',
            'avg_conceded': 'mean'
        }).round(2)
        for league_name in league_agg.index:
            league_averages[league_name] = {
                'avg_scored': league_agg.loc[league_name, 'avg_scored'],
                'avg_conceded': league_agg.loc[league_name, 'avg_conceded']
            }

        for _, row in df.iterrows():
            key = (row['league'], row['team'])
            # Calculate 1P conceded (allowed) from total - scored
            avg_1p_total = row.get('avg_1p_total', 0) or 0
            avg_1p_scored = row.get('avg_1p_scored', 0) or 0
            avg_1p_conceded = round(avg_1p_total - avg_1p_scored, 2) if avg_1p_total and avg_1p_scored else 0
            # Estimate pct_1p_conceded (% of games where team allowed 1P goal)
            # This is approximate - ideally would be calculated from raw data
            pct_1p_scored = row.get('pct_1p_scored', 0) or 0
            pct_1p_over_1_5 = row.get('pct_1p_over_1_5', 0) or 0
            # Rough estimate: if 1P avg is high and team scores often, opponent likely scores too
            pct_1p_conceded = round(min(100, max(0, pct_1p_over_1_5 + (50 - pct_1p_scored) * 0.5)), 1) if pct_1p_over_1_5 else 0

            team_stats[key] = {
                'games': row['games'],
                'avg_total': row['avg_total'],
                'avg_scored': row['avg_scored'],
                'avg_conceded': row['avg_conceded'],
                'avg_1p_total': row['avg_1p_total'],
                'pct_1p_over_1_5': row['pct_1p_over_1_5'],
                'avg_1p_scored': row.get('avg_1p_scored', 0),
                'pct_1p_scored': row.get('pct_1p_scored', 0),
                'avg_1p_conceded': avg_1p_conceded,
                'pct_1p_conceded': pct_1p_conceded,
                'pct_scored_over_1_5': row.get('pct_scored_over_1_5', 0),
                'pct_scored_over_2_5': row.get('pct_scored_over_2_5', 0),
                'pct_scored_over_3_5': row.get('pct_scored_over_3_5', 0),
                # Game total over percentages
                'pct_over_5_5': row.get('pct_over_5_5', 0),
                'pct_over_6_5': row.get('pct_over_6_5', 0),
                'pct_over_7_5': row.get('pct_over_7_5', 0),
            }

    return team_stats, league_averages

# Pre-load all period stats at startup
for period in STATS_FILES.keys():
    ALL_TEAM_STATS[period], ALL_LEAGUE_AVERAGES[period] = load_stats_for_period(period)

# Default to season for backwards compatibility
TEAM_STATS = ALL_TEAM_STATS.get('season', {})
LEAGUE_AVERAGES = ALL_LEAGUE_AVERAGES.get('season', {})

# Daily games CSV directory
GAMES_CSV_DIR = str(_DAILY_REPORTS)


def load_games_from_csv(date_str):
    """Load games from daily CSV file if it exists.

    Returns:
        List of game dicts if CSV exists, None otherwise
    """
    csv_file = f"{GAMES_CSV_DIR}/hockey_games_{date_str}.csv"
    if not os.path.exists(csv_file):
        return None

    try:
        df = pd.read_csv(csv_file)
        if df.empty:
            return []

        games = []
        for _, row in df.iterrows():
            games.append({
                'league': row['league'],
                'game_id': row['game_id'],
                'date': row['date'],
                'time': row['time'],
                'status': row['status'],
                'home_team': row['home_team'],
                'away_team': row['away_team'],
                'home_logo': row['home_logo'],
                'away_logo': row['away_logo'],
                'home_score': row['home_score'] if pd.notna(row['home_score']) else None,
                'away_score': row['away_score'] if pd.notna(row['away_score']) else None,
            })
        print(f"Loaded {len(games)} games from CSV: {csv_file}")
        return games
    except Exception as e:
        print(f"Error loading CSV {csv_file}: {e}")
        return None

def get_season_for_date(date_str):
    """Determine the hockey season for a given date (season starts in Sept)."""
    date = datetime.strptime(date_str, '%Y-%m-%d')
    # If before September, use previous year as season
    if date.month < 9:
        return date.year - 1
    return date.year

def convert_utc_to_eastern(utc_datetime_str):
    """Convert UTC datetime string to Eastern timezone and return local date and time.

    Args:
        utc_datetime_str: ISO format like '2025-12-30T00:00:00+00:00'

    Returns:
        tuple: (local_date_str 'YYYY-MM-DD', local_time_str 'HH:MM')
    """
    try:
        # Parse the UTC datetime
        if '+' in utc_datetime_str:
            dt_str = utc_datetime_str.split('+')[0]
        elif 'Z' in utc_datetime_str:
            dt_str = utc_datetime_str.replace('Z', '')
        else:
            dt_str = utc_datetime_str

        utc_dt = datetime.fromisoformat(dt_str).replace(tzinfo=ZoneInfo('UTC'))

        # Convert to Eastern timezone
        eastern_dt = utc_dt.astimezone(ZoneInfo('America/New_York'))

        local_date = eastern_dt.strftime('%Y-%m-%d')
        local_time = eastern_dt.strftime('%H:%M')

        return local_date, local_time
    except Exception:
        # Fallback: just use the date portion from the original string
        return utc_datetime_str[:10], ''

def get_games_for_date(date_str, period='season'):
    """Get all games for a specific date across all DraftKings leagues.

    Tries to load from daily CSV first (zero API calls).
    Falls back to API if CSV doesn't exist.
    """
    # Get stats for the requested period
    team_stats = ALL_TEAM_STATS.get(period, TEAM_STATS)
    league_averages = ALL_LEAGUE_AVERAGES.get(period, LEAGUE_AVERAGES)

    # Fetch standings (cached for 1 hour)
    standings = fetch_all_standings()

    # Try to load from CSV first (zero API calls)
    csv_games = load_games_from_csv(date_str)
    if csv_games is not None:
        # Enrich CSV data with team stats
        all_games = []
        for game in csv_games:
            league_name = game['league']
            home_team = game['home_team']
            away_team = game['away_team']

            home_stats = team_stats.get((league_name, home_team), {})
            away_stats = team_stats.get((league_name, away_team), {})

            # Calculate combined stats
            home_avg = home_stats.get('avg_total', 0)
            away_avg = away_stats.get('avg_total', 0)
            combined_avg = (home_avg + away_avg) / 2 if home_avg and away_avg else 0

            home_1p = home_stats.get('avg_1p_total', 0)
            away_1p = away_stats.get('avg_1p_total', 0)
            combined_1p = (home_1p + away_1p) / 2 if home_1p and away_1p else 0

            home_1p_pct = home_stats.get('pct_1p_over_1_5', 0)
            away_1p_pct = away_stats.get('pct_1p_over_1_5', 0)
            combined_1p_pct = (home_1p_pct + away_1p_pct) / 2 if home_1p_pct and away_1p_pct else 0

            # Game total over percentages
            home_o55 = home_stats.get('pct_over_5_5', 0)
            away_o55 = away_stats.get('pct_over_5_5', 0)
            combined_o55 = (home_o55 + away_o55) / 2 if home_o55 and away_o55 else 0

            home_o65 = home_stats.get('pct_over_6_5', 0)
            away_o65 = away_stats.get('pct_over_6_5', 0)
            combined_o65 = (home_o65 + away_o65) / 2 if home_o65 and away_o65 else 0

            home_o75 = home_stats.get('pct_over_7_5', 0)
            away_o75 = away_stats.get('pct_over_7_5', 0)
            combined_o75 = (home_o75 + away_o75) / 2 if home_o75 and away_o75 else 0

            league_avgs = league_averages.get(league_name, {})

            # Get standings info
            home_standings = standings.get((league_name, home_team), {})
            away_standings = standings.get((league_name, away_team), {})

            game_info = {
                'league_id': None,  # Not stored in CSV
                'league': league_name,
                'game_id': game['game_id'],
                'date': game['date'],
                'time': game['time'],
                'status': game['status'],
                'home_team': home_team,
                'away_team': away_team,
                'home_logo': game['home_logo'],
                'away_logo': game['away_logo'],
                'home_score': game['home_score'],
                'away_score': game['away_score'],
                'home_stats': home_stats,
                'away_stats': away_stats,
                'home_standings': home_standings,
                'away_standings': away_standings,
                'combined_avg_total': round(combined_avg, 2),
                'combined_avg_1p': round(combined_1p, 2),
                'combined_1p_over_pct': round(combined_1p_pct, 1),
                'combined_pct_over_5_5': round(combined_o55, 1),
                'combined_pct_over_6_5': round(combined_o65, 1),
                'combined_pct_over_7_5': round(combined_o75, 1),
                'league_avg_scored': league_avgs.get('avg_scored', 0),
                'league_avg_conceded': league_avgs.get('avg_conceded', 0),
            }
            all_games.append(game_info)

        all_games.sort(key=lambda x: (x['league'], x['time']))
        return all_games

    # Fall back to API if no CSV
    print(f"WARNING: No CSV found for {date_str}, fetching from API...")
    headers = {"x-apisports-key": API_KEY}
    all_games = []
    season = get_season_for_date(date_str)

    for league_id, league_name in DRAFTKINGS_LEAGUES.items():
        url = f"{BASE_URL}/games"
        # Fetch by season, then filter by date (API date format is ISO with timestamp)
        params = {"league": league_id, "season": season}

        try:
            response = requests.get(url, headers=headers, params=params, timeout=60)
            if response.status_code == 200:
                data = response.json()
                all_league_games = data.get("response", [])
                # Filter games for the specific date, converting UTC to Eastern timezone
                games = []
                for g in all_league_games:
                    utc_date = g.get('date', '')
                    if utc_date:
                        local_date, _ = convert_utc_to_eastern(utc_date)
                        if local_date == date_str:
                            games.append(g)

                for game in games:
                    home_team = game.get("teams", {}).get("home", {}).get("name", "")
                    away_team = game.get("teams", {}).get("away", {}).get("name", "")

                    # Get team stats for the selected period
                    home_stats = team_stats.get((league_name, home_team), {})
                    away_stats = team_stats.get((league_name, away_team), {})

                    # Calculate combined stats
                    home_avg = home_stats.get('avg_total', 0)
                    away_avg = away_stats.get('avg_total', 0)
                    combined_avg = (home_avg + away_avg) / 2 if home_avg and away_avg else 0

                    home_1p = home_stats.get('avg_1p_total', 0)
                    away_1p = away_stats.get('avg_1p_total', 0)
                    combined_1p = (home_1p + away_1p) / 2 if home_1p and away_1p else 0

                    home_1p_pct = home_stats.get('pct_1p_over_1_5', 0)
                    away_1p_pct = away_stats.get('pct_1p_over_1_5', 0)
                    combined_1p_pct = (home_1p_pct + away_1p_pct) / 2 if home_1p_pct and away_1p_pct else 0

                    # Game total over percentages
                    home_o55 = home_stats.get('pct_over_5_5', 0)
                    away_o55 = away_stats.get('pct_over_5_5', 0)
                    combined_o55 = (home_o55 + away_o55) / 2 if home_o55 and away_o55 else 0

                    home_o65 = home_stats.get('pct_over_6_5', 0)
                    away_o65 = away_stats.get('pct_over_6_5', 0)
                    combined_o65 = (home_o65 + away_o65) / 2 if home_o65 and away_o65 else 0

                    home_o75 = home_stats.get('pct_over_7_5', 0)
                    away_o75 = away_stats.get('pct_over_7_5', 0)
                    combined_o75 = (home_o75 + away_o75) / 2 if home_o75 and away_o75 else 0

                    # Extract time from date field, converting to Eastern time
                    date_field = game.get('date', '')
                    _, time_str = convert_utc_to_eastern(date_field)

                    # Get league averages for the selected period
                    league_avgs = league_averages.get(league_name, {})

                    # Get standings info
                    home_standings = standings.get((league_name, home_team), {})
                    away_standings = standings.get((league_name, away_team), {})

                    game_info = {
                        'league_id': league_id,
                        'league': league_name,
                        'game_id': game.get('id'),
                        'date': date_field,
                        'time': time_str,
                        'status': game.get('status', {}).get('short', ''),
                        'home_team': home_team,
                        'away_team': away_team,
                        'home_logo': game.get("teams", {}).get("home", {}).get("logo", ""),
                        'away_logo': game.get("teams", {}).get("away", {}).get("logo", ""),
                        'home_score': game.get('scores', {}).get('home'),
                        'away_score': game.get('scores', {}).get('away'),
                        'home_stats': home_stats,
                        'away_stats': away_stats,
                        'home_standings': home_standings,
                        'away_standings': away_standings,
                        'combined_avg_total': round(combined_avg, 2),
                        'combined_avg_1p': round(combined_1p, 2),
                        'combined_1p_over_pct': round(combined_1p_pct, 1),
                        'combined_pct_over_5_5': round(combined_o55, 1),
                        'combined_pct_over_6_5': round(combined_o65, 1),
                        'combined_pct_over_7_5': round(combined_o75, 1),
                        'league_avg_scored': league_avgs.get('avg_scored', 0),
                        'league_avg_conceded': league_avgs.get('avg_conceded', 0),
                    }
                    all_games.append(game_info)
        except Exception as e:
            print(f"Error fetching {league_name}: {e}")
            continue

    # Sort by league, then time
    all_games.sort(key=lambda x: (x['league'], x['time']))
    return all_games

@app.route('/')
def index():
    """Main dashboard page."""
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('index.html', default_date=today, leagues=DRAFTKINGS_LEAGUES)

@app.route('/api/games')
def api_games():
    """API endpoint to get games for a specific date and period."""
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    period = request.args.get('period', 'season')  # season, L10, or L5
    games = get_games_for_date(date_str, period=period)

    # Group by league
    games_by_league = {}
    for game in games:
        league = game['league']
        if league not in games_by_league:
            games_by_league[league] = []
        games_by_league[league].append(game)

    return jsonify({
        'date': date_str,
        'total_games': len(games),
        'games_by_league': games_by_league
    })

if __name__ == "__main__":
    port = int(os.environ.get("HOCKEY_DASHBOARD_PORT", "8503"))
    debug = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    host = os.environ.get("HOCKEY_DASHBOARD_HOST", "0.0.0.0")
    app.run(debug=debug, port=port, host=host)
