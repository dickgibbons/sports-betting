#!/usr/bin/env python3
"""Flask-based Soccer Dashboard showing daily schedule with team stats."""

from flask import Flask, render_template, jsonify, request, Response
import requests
from datetime import datetime, timedelta
import pandas as pd
import os
import io
import csv

app = Flask(__name__, template_folder='templates')

API_KEY = "960c628e1c91c4b1f125e1eec52ad862"
BASE_URL = "https://v3.football.api-sports.io"

def get_season_for_date(date_str):
    """Determine the football season for a given date.

    European football seasons run Aug-May, so:
    - Dates Jan-Jul use the current year as season (e.g., Jan 2025 = 2024 season)
    - Dates Aug-Dec use the current year as season (e.g., Dec 2025 = 2025 season)
    """
    date = datetime.strptime(date_str, '%Y-%m-%d')
    # If before August, it's the previous year's season
    if date.month < 8:
        return date.year - 1
    return date.year

# TOP 50 LEAGUES BY AVERAGE GOALS PER GAME - (league_name, country)
SOCCER_LEAGUES = {
    # Top Tier - 3.0+ goals per game
    384: ("Israeli Premier", "Israel"),
    91: ("Fortuna Liga", "Slovakia"),
    164: ("Úrvalsdeild", "Iceland"),
    207: ("Swiss Super League", "Switzerland"),
    238: ("Primera A", "Colombia"),
    88: ("Eredivisie", "Netherlands"),
    188: ("K League 1", "South Korea"),
    119: ("Superliga", "Denmark"),
    366: ("Botola Pro", "Morocco"),
    78: ("Bundesliga", "Germany"),
    253: ("MLS", "USA"),
    169: ("UAE Pro League", "UAE"),
    373: ("Prva Liga", "Slovenia"),
    271: ("NB I", "Hungary"),
    79: ("2. Bundesliga", "Germany"),
    89: ("Eerste Divisie", "Netherlands"),
    108: ("Premijer Liga", "Bosnia"),
    # High Tier - 2.7-3.0 goals per game
    307: ("Saudi Pro League", "Saudi Arabia"),
    117: ("Meistriliiga", "Estonia"),
    106: ("Ekstraklasa", "Poland"),
    61: ("Ligue 1", "France"),
    39: ("Premier League", "England"),
    332: ("A Lyga", "Lithuania"),
    265: ("Primera Division", "Peru"),
    383: ("Egyptian Premier", "Egypt"),
    218: ("Austrian Bundesliga", "Austria"),
    286: ("Super Liga", "Serbia"),
    262: ("Liga MX", "Mexico"),
    210: ("HNL", "Croatia"),
    # Mid-High Tier - 2.5-2.7 goals per game
    98: ("J1 League", "Japan"),
    94: ("Primeira Liga", "Portugal"),
    40: ("Championship", "England"),
    42: ("League Two", "England"),
    281: ("Primera Division PY", "Paraguay"),
    197: ("Greek Super League", "Greece"),
    318: ("Virsliga", "Latvia"),
    345: ("Czech First League", "Czech Republic"),
    292: ("A-League", "Australia"),
    68: ("Thai League 1", "Thailand"),
    203: ("Turkish Super Lig", "Turkey"),
    333: ("Premier League", "Ukraine"),
    327: ("1. Division", "Cyprus"),
    41: ("League One", "England"),
    179: ("Scottish Premiership", "Scotland"),
    62: ("Ligue 2", "France"),
    140: ("La Liga", "Spain"),
    141: ("La Liga 2", "Spain"),
    235: ("Premier League RU", "Russia"),
    266: ("Primera Division", "Chile"),
    283: ("Liga 1", "Romania"),
    144: ("Jupiler Pro League", "Belgium"),
    136: ("Serie B", "Italy"),
}

# Build a lookup from league_name -> country
LEAGUE_COUNTRIES = {name: country for _, (name, country) in SOCCER_LEAGUES.items()}

# Stat file paths for each period
STATS_FILES = {
    'season': "/Users/dickgibbons/Daily Reports/soccer_team_complete_stats.csv",
    'L10': "/Users/dickgibbons/Daily Reports/soccer_team_stats_L10.csv",
    'L5': "/Users/dickgibbons/Daily Reports/soccer_team_stats_L5.csv",
}

# Load team stats for all periods
ALL_TEAM_STATS = {}  # {period: {(league, team): stats}}
ALL_LEAGUE_AVERAGES = {}  # {period: {league: averages}}

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
            team_stats[key] = {
                'games': row['games'],
                'avg_total': row['avg_total'],
                'avg_scored': row.get('avg_scored', 0),
                'avg_conceded': row.get('avg_conceded', 0),
                'h1_over_05_pct': row['h1_over_05_pct'],
                'over_15_pct': row['over_15_pct'],
                'over_25_pct': row['over_25_pct'],
                'over_35_pct': row['over_35_pct'],
                'h1_over_15_pct': row['h1_over_15_pct'],
                'h2_over_15_pct': row['h2_over_15_pct'],
                'h1_scored_pct': row['h1_scored_pct'],
                'h2_scored_pct': row['h2_scored_pct'],
                'h1_avg_total': row['h1_avg_total'],
                'h2_avg_total': row['h2_avg_total'],
            }
    return team_stats, league_averages

# Pre-load all period stats at startup
for period in STATS_FILES.keys():
    ALL_TEAM_STATS[period], ALL_LEAGUE_AVERAGES[period] = load_stats_for_period(period)

# Default to season for backwards compatibility
TEAM_STATS = ALL_TEAM_STATS.get('season', {})
LEAGUE_AVERAGES = ALL_LEAGUE_AVERAGES.get('season', {})

# Daily games CSV directory
GAMES_CSV_DIR = "/Users/dickgibbons/Daily Reports"


def load_games_from_csv(date_str):
    """Load games from daily CSV file if it exists.

    Returns:
        List of game dicts if CSV exists, None otherwise
    """
    csv_file = f"{GAMES_CSV_DIR}/soccer_games_{date_str}.csv"
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
                'country': row['country'],
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

def get_games_for_date(date_str, period='season'):
    """Get all games for a specific date across target leagues.

    Tries to load from daily CSV first (zero API calls).
    Falls back to API if CSV doesn't exist.

    Args:
        date_str: Date in YYYY-MM-DD format
        period: Stats period to use - 'season', 'L10', or 'L5'
    """
    # Get stats for the requested period
    team_stats = ALL_TEAM_STATS.get(period, TEAM_STATS)
    league_averages = ALL_LEAGUE_AVERAGES.get(period, LEAGUE_AVERAGES)

    # Try to load from CSV first (zero API calls)
    csv_games = load_games_from_csv(date_str)
    if csv_games is not None:
        # Enrich CSV data with team stats
        all_games = []
        for game in csv_games:
            league_name = game['league']
            country = game['country']
            home_team = game['home_team']
            away_team = game['away_team']

            home_stats = team_stats.get((league_name, home_team), {})
            away_stats = team_stats.get((league_name, away_team), {})
            league_avgs = league_averages.get(league_name, {})

            game_info = {
                'league_id': None,  # Not stored in CSV
                'league': league_name,
                'country': country,
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

    # Query ALL games for this date (no league/season filter)
    url = f"{BASE_URL}/fixtures"
    params = {"date": date_str}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=120)
        if response.status_code != 200:
            print(f"API error: {response.status_code}")
            return all_games

        data = response.json()
        games = data.get("response", [])
        print(f"Found {len(games)} total games for {date_str}")

        for game in games:
            league_info = game.get("league", {})
            league_id = league_info.get("id")

            # Only include games from our target leagues
            if league_id not in SOCCER_LEAGUES:
                continue

            league_name, country = SOCCER_LEAGUES[league_id]
            fixture = game.get("fixture", {})
            game_id = fixture.get("id")
            teams = game.get("teams", {})
            goals = game.get("goals", {})

            home_team = teams.get("home", {}).get("name", "")
            away_team = teams.get("away", {}).get("name", "")

            # Get team stats for the selected period
            home_stats = team_stats.get((league_name, home_team), {})
            away_stats = team_stats.get((league_name, away_team), {})

            # Extract time from date field
            date_field = fixture.get('date', '')
            time_str = ''
            if 'T' in date_field:
                time_part = date_field.split('T')[1]
                time_str = time_part.split('+')[0][:5]

            # Get status
            status_info = fixture.get('status', {})
            status = status_info.get('short', 'NS')

            # Get league averages for this league
            league_avgs = league_averages.get(league_name, {})

            game_info = {
                'league_id': league_id,
                'league': league_name,
                'country': country,
                'game_id': game_id,
                'date': date_field,
                'time': time_str,
                'status': status,
                'home_team': home_team,
                'away_team': away_team,
                'home_logo': teams.get("home", {}).get("logo", ""),
                'away_logo': teams.get("away", {}).get("logo", ""),
                'home_score': goals.get('home'),
                'away_score': goals.get('away'),
                'home_stats': home_stats,
                'away_stats': away_stats,
                'league_avg_scored': league_avgs.get('avg_scored', 0),
                'league_avg_conceded': league_avgs.get('avg_conceded', 0),
            }
            all_games.append(game_info)

    except Exception as e:
        print(f"Error fetching games for {date_str}: {e}")

    # Sort by league, then time
    all_games.sort(key=lambda x: (x['league'], x['time']))
    return all_games

@app.route('/')
def index():
    """Main dashboard page."""
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('index.html', default_date=today, leagues=SOCCER_LEAGUES)

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

@app.route('/api/download_csv')
def download_csv():
    """Generate and download CSV of current games data."""
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    period = request.args.get('period', 'season')
    games = get_games_for_date(date_str, period=period)

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([
        'Country', 'League', 'Time', 'Home/Away', 'Team', 'GP', 'Avg Total',
        'Avg Scored', 'League Avg Scored', 'Avg Conceded', 'League Avg Conceded',
        'H1 O0.5%', 'H1 O1.5%', 'H1 Scored%', 'H1 Avg',
        'H2 Scored%', 'H2 Avg', 'O1.5%', 'O2.5%', 'O3.5%',
        'Comb O1.5%', 'Comb O2.5%', 'Comb O3.5%'
    ])

    # Data rows - each game has 2 rows (away, home)
    for game in games:
        home_stats = game.get('home_stats', {})
        away_stats = game.get('away_stats', {})

        # Calculate combined percentages
        comb_o15 = ''
        comb_o25 = ''
        comb_o35 = ''
        if home_stats.get('over_15_pct') and away_stats.get('over_15_pct'):
            comb_o15 = round((home_stats['over_15_pct'] + away_stats['over_15_pct']) / 2, 1)
        if home_stats.get('over_25_pct') and away_stats.get('over_25_pct'):
            comb_o25 = round((home_stats['over_25_pct'] + away_stats['over_25_pct']) / 2, 1)
        if home_stats.get('over_35_pct') and away_stats.get('over_35_pct'):
            comb_o35 = round((home_stats['over_35_pct'] + away_stats['over_35_pct']) / 2, 1)

        # Away row
        writer.writerow([
            game.get('country', ''),
            game.get('league', ''),
            game.get('time', ''),
            'A',
            game.get('away_team', ''),
            away_stats.get('games', ''),
            away_stats.get('avg_total', ''),
            away_stats.get('avg_scored', ''),
            game.get('league_avg_scored', ''),
            away_stats.get('avg_conceded', ''),
            game.get('league_avg_conceded', ''),
            away_stats.get('h1_over_05_pct', ''),
            away_stats.get('h1_over_15_pct', ''),
            away_stats.get('h1_scored_pct', ''),
            away_stats.get('h1_avg_total', ''),
            away_stats.get('h2_scored_pct', ''),
            away_stats.get('h2_avg_total', ''),
            away_stats.get('over_15_pct', ''),
            away_stats.get('over_25_pct', ''),
            away_stats.get('over_35_pct', ''),
            comb_o15,
            comb_o25,
            comb_o35
        ])

        # Home row
        writer.writerow([
            game.get('country', ''),
            game.get('league', ''),
            game.get('time', ''),
            'H',
            game.get('home_team', ''),
            home_stats.get('games', ''),
            home_stats.get('avg_total', ''),
            home_stats.get('avg_scored', ''),
            game.get('league_avg_scored', ''),
            home_stats.get('avg_conceded', ''),
            game.get('league_avg_conceded', ''),
            home_stats.get('h1_over_05_pct', ''),
            home_stats.get('h1_over_15_pct', ''),
            home_stats.get('h1_scored_pct', ''),
            home_stats.get('h1_avg_total', ''),
            home_stats.get('h2_scored_pct', ''),
            home_stats.get('h2_avg_total', ''),
            home_stats.get('over_15_pct', ''),
            home_stats.get('over_25_pct', ''),
            home_stats.get('over_35_pct', ''),
            '',  # Combined already shown in away row
            '',
            ''
        ])

    # Prepare response
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=soccer_dashboard_{date_str}_{period}.csv'}
    )

if __name__ == '__main__':
    app.run(debug=True, port=8502, host='0.0.0.0')
