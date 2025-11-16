#!/usr/bin/env python3
"""
Debug fixture retrieval to see what we're actually getting from APIs
"""
import requests
import json
from datetime import datetime

def test_api_sports_fixtures():
    """Test what API-Sports returns for today"""
    
    api_key = "960c628e1c91c4b1f125e1eec52ad862"
    headers = {'x-apisports-key': api_key}
    
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"🔍 Testing API-Sports for date: {today}")
    
    url = "https://v3.football.api-sports.io/fixtures"
    params = {'date': today}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            fixtures = data.get('response', [])
            
            print(f"✅ Found {len(fixtures)} fixtures from API-Sports")
            
            # Analyze fixture statuses
            status_counts = {}
            upcoming_games = []
            
            for fixture in fixtures:
                fixture_info = fixture.get('fixture', {})
                status = fixture_info.get('status', {}).get('short', 'Unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
                
                # Collect upcoming games (not finished)
                if status in ['NS', 'TBD', 'PST', 'CANC', '1H', '2H', 'HT', 'ET']:
                    teams = fixture.get('teams', {})
                    league = fixture.get('league', {})
                    
                    date_time = fixture_info.get('date', 'Unknown')
                    home_team = teams.get('home', {}).get('name', 'Unknown')
                    away_team = teams.get('away', {}).get('name', 'Unknown')
                    league_name = league.get('name', 'Unknown')
                    country = league.get('country', 'Unknown')
                    
                    upcoming_games.append({
                        'date_time': date_time,
                        'home_team': home_team,
                        'away_team': away_team,
                        'league': league_name,
                        'country': country,
                        'status': status
                    })
            
            print(f"\n📊 Fixture Status Summary:")
            for status, count in sorted(status_counts.items()):
                print(f"   {status}: {count} matches")
            
            print(f"\n🎯 Upcoming/Live Games ({len(upcoming_games)}):")
            for i, game in enumerate(upcoming_games[:10]):
                print(f"{i+1}. {game['date_time']} | {game['home_team']} vs {game['away_team']}")
                print(f"   League: {game['league']} | Country: {game.get('country', 'Unknown')} | Status: {game['status']}")
                
        else:
            print(f"❌ API-Sports error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_api_sports_fixtures()