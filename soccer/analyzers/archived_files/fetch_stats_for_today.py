#!/usr/bin/env python3
"""
Fetch Team Statistics for Today's Matches
Uses fixture data to get the correct league for each team
"""

import requests
import json
from pathlib import Path
from datetime import datetime
import time

def fetch_stats_for_today(api_key: str, date_str: str):
    """Fetch team statistics for all teams playing today"""

    api_base = "https://v3.football.api-sports.io"
    headers = {"x-apisports-key": api_key}

    print("=" * 70)
    print(f"📊 FETCHING TEAM STATISTICS FOR {date_str}")
    print("=" * 70)

    # Load existing stats
    stats_file = Path('team_statistics.json')
    if stats_file.exists():
        with open(stats_file, 'r') as f:
            team_stats = json.load(f)
        print(f"\n✅ Loaded {len(team_stats)} existing team stats")
    else:
        team_stats = {}

    # Fetch fixtures for today
    print(f"\n📅 Fetching fixtures for {date_str}...")
    url = f"{api_base}/fixtures"
    params = {"date": date_str}
    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print(f"❌ Error fetching fixtures: {response.status_code}")
        return

    fixtures = response.json().get('response', [])
    print(f"   ✅ Found {len(fixtures)} fixtures")

    # Extract unique team/league pairs
    teams_to_fetch = {}
    for fixture in fixtures:
        home_id = fixture['teams']['home']['id']
        away_id = fixture['teams']['away']['id']
        league_id = fixture['league']['id']
        season = fixture['league']['season']

        teams_to_fetch[home_id] = {
            'name': fixture['teams']['home']['name'],
            'league_id': league_id,
            'season': season
        }
        teams_to_fetch[away_id] = {
            'name': fixture['teams']['away']['name'],
            'league_id': league_id,
            'season': season
        }

    print(f"\n📊 Need statistics for {len(teams_to_fetch)} unique teams")

    # Fetch stats for each team
    fetched_count = 0
    skipped_count = 0

    for team_id, team_info in teams_to_fetch.items():
        team_key = f"{team_id}_{team_info['season']}"

        # Skip if we already have recent stats (less than 7 days old)
        if team_key in team_stats:
            last_updated = datetime.fromisoformat(team_stats[team_key].get('last_updated', '2000-01-01'))
            if (datetime.now() - last_updated).days < 7:
                skipped_count += 1
                continue

        print(f"\n   Fetching: {team_info['name']} (Team ID: {team_id}, League: {team_info['league_id']})")

        try:
            url = f"{api_base}/teams/statistics"
            params = {
                "team": team_id,
                "season": team_info['season'],
                "league": team_info['league_id']
            }

            response = requests.get(url, headers=headers, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                response_data = data.get('response', {})

                if response_data:
                    # Extract key statistics
                    stats = {
                        'team_id': team_id,
                        'team_name': team_info['name'],
                        'league_id': team_info['league_id'],
                        'season': team_info['season'],
                        'last_updated': datetime.now().isoformat(),

                        # Match stats
                        'played': response_data.get('fixtures', {}).get('played', {}).get('total', 0),
                        'wins_home': response_data.get('fixtures', {}).get('wins', {}).get('home', 0),
                        'wins_away': response_data.get('fixtures', {}).get('wins', {}).get('away', 0),
                        'draws_home': response_data.get('fixtures', {}).get('draws', {}).get('home', 0),
                        'draws_away': response_data.get('fixtures', {}).get('draws', {}).get('away', 0),
                        'loses_home': response_data.get('fixtures', {}).get('loses', {}).get('home', 0),
                        'loses_away': response_data.get('fixtures', {}).get('loses', {}).get('away', 0),

                        # Goals
                        'goals_for_avg_home': float(response_data.get('goals', {}).get('for', {}).get('average', {}).get('home', '0') or 0),
                        'goals_for_avg_away': float(response_data.get('goals', {}).get('for', {}).get('average', {}).get('away', '0') or 0),
                        'goals_against_avg_home': float(response_data.get('goals', {}).get('against', {}).get('average', {}).get('home', '0') or 0),
                        'goals_against_avg_away': float(response_data.get('goals', {}).get('against', {}).get('average', {}).get('away', '0') or 0),

                        # Clean sheets
                        'clean_sheets_home': response_data.get('clean_sheet', {}).get('home', 0),
                        'clean_sheets_away': response_data.get('clean_sheet', {}).get('away', 0),
                        'failed_to_score_home': response_data.get('failed_to_score', {}).get('home', 0),
                        'failed_to_score_away': response_data.get('failed_to_score', {}).get('away', 0),
                    }

                    # Store in cache
                    team_stats[team_key] = stats
                    fetched_count += 1
                    print(f"      ✅ Fetched ({stats['played']} games played)")
                else:
                    print(f"      ⚠️  No data available")
            else:
                print(f"      ❌ API error: {response.status_code}")

            # Rate limiting - be conservative
            time.sleep(1.2)

        except Exception as e:
            print(f"      ❌ Error: {e}")

    # Save all stats
    with open(stats_file, 'w') as f:
        json.dump(team_stats, f, indent=2)

    print(f"\n{'='*70}")
    print(f"✅ COMPLETE")
    print(f"{'='*70}")
    print(f"   Total teams in cache: {len(team_stats)}")
    print(f"   Newly fetched: {fetched_count}")
    print(f"   Skipped (recent): {skipped_count}")
    print(f"   Stats file: {stats_file}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    import sys

    # API key
    api_key = "960c628e1c91c4b1f125e1eec52ad862"

    # Date (default: today)
    date_str = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime('%Y-%m-%d')

    fetch_stats_for_today(api_key, date_str)
