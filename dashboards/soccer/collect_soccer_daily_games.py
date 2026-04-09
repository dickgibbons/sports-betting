#!/usr/bin/env python3
"""Collect soccer games for a specific date and save to CSV.

This script fetches games from all target leagues for a given date
and saves them to a CSV file that the dashboard can read without hitting the API.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

API_KEY = "960c628e1c91c4b1f125e1eec52ad862"
BASE_URL = "https://v3.football.api-sports.io"
_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = str(
    Path(os.environ.get("SPORTS_BETTING_DAILY_REPORTS", _ROOT / "Daily Reports"))
)

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


def collect_soccer_games(date_str):
    """Fetch all soccer games for a specific date from target leagues."""
    headers = {"x-apisports-key": API_KEY}
    all_games = []

    print(f"Collecting soccer games for {date_str}...")

    # Query ALL games for this date (single API call)
    url = f"{BASE_URL}/fixtures"
    params = {"date": date_str}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=120)
        if response.status_code != 200:
            print(f"API error: {response.status_code}")
            return None

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
            teams = game.get("teams", {})
            goals = game.get("goals", {})

            # Extract time from date field
            date_field = fixture.get('date', '')
            time_str = ''
            if 'T' in date_field:
                time_part = date_field.split('T')[1]
                time_str = time_part.split('+')[0][:5]

            game_info = {
                'league': league_name,
                'country': country,
                'game_id': fixture.get('id'),
                'date': date_field,
                'time': time_str,
                'status': fixture.get('status', {}).get('short', 'NS'),
                'home_team': teams.get("home", {}).get("name", ""),
                'away_team': teams.get("away", {}).get("name", ""),
                'home_logo': teams.get("home", {}).get("logo", ""),
                'away_logo': teams.get("away", {}).get("logo", ""),
                'home_score': goals.get('home'),
                'away_score': goals.get('away'),
            }
            all_games.append(game_info)

    except Exception as e:
        print(f"Error fetching games for {date_str}: {e}")
        return None

    # Sort by league, then time
    all_games.sort(key=lambda x: (x['league'], x['time']))

    # Group by league for summary
    leagues_found = {}
    for g in all_games:
        leagues_found[g['league']] = leagues_found.get(g['league'], 0) + 1

    for league, count in sorted(leagues_found.items()):
        print(f"  {league}: {count} games")

    # Save to CSV
    output_file = f"{OUTPUT_DIR}/soccer_games_{date_str}.csv"
    if all_games:
        df = pd.DataFrame(all_games)
        df.to_csv(output_file, index=False)
        print(f"\nSaved {len(all_games)} games to {output_file}")
    else:
        # Save empty CSV with headers
        df = pd.DataFrame(columns=['league', 'country', 'game_id', 'date', 'time', 'status',
                                   'home_team', 'away_team', 'home_logo', 'away_logo',
                                   'home_score', 'away_score'])
        df.to_csv(output_file, index=False)
        print(f"\nNo games found for {date_str}. Saved empty CSV.")

    return output_file


if __name__ == "__main__":
    # Get date from command line or use today
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        date_str = datetime.now().strftime('%Y-%m-%d')

    collect_soccer_games(date_str)
