#!/usr/bin/env python3
"""
Debug the league data from API to see what's actually returned
"""

import requests
from datetime import datetime

def debug_api_sports_leagues():
    """Check what league data is actually returned by API-Sports"""

    print("🔍 DEBUGGING LEAGUE DATA FROM API-SPORTS")
    print("="*50)

    api_key = '960c628e1c91c4b1f125e1eec52ad862'
    today = datetime.now().strftime('%Y-%m-%d')

    url = f"https://v3.football.api-sports.io/fixtures?date={today}"
    headers = {
        'X-RapidAPI-Key': api_key,
        'X-RapidAPI-Host': 'v3.football.api-sports.io'
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code == 200:
            data = response.json()

            if 'response' in data and data['response']:
                fixtures = data['response']
                print(f"📊 Found {len(fixtures)} fixtures")

                print(f"\n🏈 SAMPLE MATCHES WITH ACTUAL LEAGUE DATA:")
                print("="*60)

                for i, fixture in enumerate(fixtures[:10]):  # Show first 10 matches
                    try:
                        teams = fixture.get('teams', {})
                        league = fixture.get('league', {})

                        home_team = teams.get('home', {}).get('name', 'Unknown')
                        away_team = teams.get('away', {}).get('name', 'Unknown')
                        league_name = league.get('name', 'Unknown')
                        league_country = league.get('country', 'Unknown')
                        league_id = league.get('id', 'Unknown')

                        print(f"\n{i+1}. {home_team} vs {away_team}")
                        print(f"   League: {league_name}")
                        print(f"   Country: {league_country}")
                        print(f"   League ID: {league_id}")

                        # Check if these match our problem cases
                        problem_matches = [
                            'El Gouna FC',
                            'Ceramica Cleopatra',
                            'Montego Bay United',
                            'Spanish Town Police',
                            'BKMA',
                            'Ararat-Armenia'
                        ]

                        if any(team in home_team or team in away_team for team in problem_matches):
                            print(f"   ⚠️ PROBLEM MATCH FOUND!")
                            print(f"   Raw league data: {league}")

                    except Exception as e:
                        print(f"   ❌ Error parsing fixture: {e}")

                # Show unique leagues found
                unique_leagues = set()
                for fixture in fixtures:
                    league_name = fixture.get('league', {}).get('name', 'Unknown')
                    league_country = fixture.get('league', {}).get('country', 'Unknown')
                    unique_leagues.add(f"{league_name} ({league_country})")

                print(f"\n📋 UNIQUE LEAGUES FOUND TODAY:")
                print("="*40)
                for league in sorted(list(unique_leagues)[:15]):  # Show first 15 leagues
                    print(f"• {league}")

                if len(unique_leagues) > 15:
                    print(f"... and {len(unique_leagues) - 15} more leagues")

            else:
                print("❌ No fixtures found in API response")

        else:
            print(f"❌ API Error: {response.status_code}")

    except Exception as e:
        print(f"❌ Exception: {e}")

def main():
    debug_api_sports_leagues()

if __name__ == "__main__":
    main()