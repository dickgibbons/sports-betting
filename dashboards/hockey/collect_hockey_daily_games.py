#!/usr/bin/env python3
"""Collect hockey games for a specific date and save to CSV.

This script fetches games from all DraftKings leagues for a given date
and saves them to a CSV file that the dashboard can read without hitting the API.
"""

import requests
import pandas as pd
from datetime import datetime
import sys
from zoneinfo import ZoneInfo

API_KEY = "960c628e1c91c4b1f125e1eec52ad862"
BASE_URL = "https://v1.hockey.api-sports.io"
OUTPUT_DIR = "/Users/dickgibbons/Daily Reports"

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


def get_season_for_date(date_str):
    """Determine the hockey season for a given date (season starts in Sept)."""
    date = datetime.strptime(date_str, '%Y-%m-%d')
    if date.month < 9:
        return date.year - 1
    return date.year


def convert_utc_to_eastern(utc_datetime_str):
    """Convert UTC datetime string to Eastern timezone."""
    try:
        if '+' in utc_datetime_str:
            dt_str = utc_datetime_str.split('+')[0]
        elif 'Z' in utc_datetime_str:
            dt_str = utc_datetime_str.replace('Z', '')
        else:
            dt_str = utc_datetime_str

        utc_dt = datetime.fromisoformat(dt_str).replace(tzinfo=ZoneInfo('UTC'))
        eastern_dt = utc_dt.astimezone(ZoneInfo('America/New_York'))

        local_date = eastern_dt.strftime('%Y-%m-%d')
        local_time = eastern_dt.strftime('%H:%M')

        return local_date, local_time
    except Exception:
        return utc_datetime_str[:10], ''


def collect_hockey_games(date_str):
    """Fetch all hockey games for a specific date across all DraftKings leagues."""
    headers = {"x-apisports-key": API_KEY}
    all_games = []
    season = get_season_for_date(date_str)

    print(f"Collecting hockey games for {date_str} (season {season})...")

    for league_id, league_name in DRAFTKINGS_LEAGUES.items():
        url = f"{BASE_URL}/games"
        params = {"league": league_id, "season": season}

        try:
            response = requests.get(url, headers=headers, params=params, timeout=60)
            if response.status_code == 200:
                data = response.json()
                all_league_games = data.get("response", [])

                # Filter games for the specific date
                for game in all_league_games:
                    utc_date = game.get('date', '')
                    if utc_date:
                        local_date, local_time = convert_utc_to_eastern(utc_date)
                        if local_date == date_str:
                            game_info = {
                                'league': league_name,
                                'game_id': game.get('id'),
                                'date': utc_date,
                                'time': local_time,
                                'status': game.get('status', {}).get('short', ''),
                                'home_team': game.get('teams', {}).get('home', {}).get('name', ''),
                                'away_team': game.get('teams', {}).get('away', {}).get('name', ''),
                                'home_logo': game.get('teams', {}).get('home', {}).get('logo', ''),
                                'away_logo': game.get('teams', {}).get('away', {}).get('logo', ''),
                                'home_score': game.get('scores', {}).get('home'),
                                'away_score': game.get('scores', {}).get('away'),
                            }
                            all_games.append(game_info)

                games_for_date = len([g for g in all_games if g['league'] == league_name])
                if games_for_date > 0:
                    print(f"  {league_name}: {games_for_date} games")
        except Exception as e:
            print(f"  Error fetching {league_name}: {e}")
            continue

    # Sort by league, then time
    all_games.sort(key=lambda x: (x['league'], x['time']))

    # Save to CSV
    output_file = f"{OUTPUT_DIR}/hockey_games_{date_str}.csv"
    if all_games:
        df = pd.DataFrame(all_games)
        df.to_csv(output_file, index=False)
        print(f"\nSaved {len(all_games)} games to {output_file}")
    else:
        # Save empty CSV with headers
        df = pd.DataFrame(columns=['league', 'game_id', 'date', 'time', 'status',
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

    collect_hockey_games(date_str)
