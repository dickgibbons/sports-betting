#!/usr/bin/env python3
"""
API-Sports Fallback Integration
Provides fallback fixture data when FootyStats doesn't have what we need
"""

import requests
import json
from datetime import datetime, timedelta

class APISportsFallback:
    """Fallback API for fixtures when FootyStats is insufficient"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {'x-apisports-key': api_key}
        
        # League mappings from our internal IDs to API-Sports IDs
        self.league_mappings = {
            'WC Qualification Europe': 32,
            'WC Qualification Africa': 34,
            'WC Qualification Asia': 33,
            'WC Qualification South America': 35,
            'WC Qualification CONCACAF': 36,
            'WC Qualification Oceania': 37,
            'WC Qualification Intercontinental Play': 29,  # World Cup Intercontinental Play-offs
            'UEFA Nations League': 5,
            'UEFA Champions League': 2,
            'UEFA Europa League': 3,
            'UEFA Conference League': 848,
            'Premier League': 39,
            'La Liga': 140,
            'Serie A': 135,
            'Bundesliga': 78,
            'Ligue 1': 61
        }
    
    def test_connection(self):
        """Test API connection"""
        try:
            response = requests.get(f"{self.base_url}/status", 
                                  headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('response', {})
            return None
        except Exception as e:
            print(f"API-Sports connection error: {e}")
            return None
    
    def get_fixtures_for_league(self, league_name, date_str, season=None):
        """Get fixtures for a specific league"""
        api_league_id = self.league_mappings.get(league_name)
        if not api_league_id:
            return []
        
        try:
            # Try both current season and next season for international competitions
            seasons_to_try = [season] if season else [2025, 2026]
            
            for season_year in seasons_to_try:
                params = {
                    'league': api_league_id,
                    'date': date_str,
                    'season': season_year
                }
                
                response = requests.get(f"{self.base_url}/fixtures", 
                                      headers=self.headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    fixtures = data.get('response', [])
                    
                    if fixtures:
                        print(f"✅ API-Sports: Found {len(fixtures)} {league_name} fixtures for {date_str}")
                        return self.convert_api_sports_fixtures(fixtures, league_name)
                        
            print(f"⚠️ API-Sports: No {league_name} fixtures found for {date_str}")
            return []
            
        except Exception as e:
            print(f"⚠️ API-Sports error for {league_name}: {e}")
            return []
    
    def convert_api_sports_fixtures(self, api_fixtures, league_name):
        """Convert API-Sports fixtures to our standard format"""
        converted_fixtures = []
        
        for fixture in api_fixtures:
            try:
                teams = fixture.get('teams', {})
                fixture_info = fixture.get('fixture', {})
                
                # Extract time from date string
                date_str = fixture_info.get('date', '')
                if date_str:
                    try:
                        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        time_str = dt.strftime('%H:%M')
                    except:
                        time_str = '15:00'
                else:
                    time_str = '15:00'
                
                match = {
                    'kick_off': time_str,
                    'home_team': teams.get('home', {}).get('name', 'Unknown'),
                    'away_team': teams.get('away', {}).get('name', 'Unknown'),
                    'league': league_name,
                    'home_odds': 2.0,  # Default odds since API-Sports doesn't always have odds
                    'draw_odds': 3.2,
                    'away_odds': 3.5,
                    'source': 'API-Sports'
                }
                converted_fixtures.append(match)
                
            except Exception as e:
                print(f"⚠️ Error converting API-Sports fixture: {e}")
                continue
        
        return converted_fixtures
    
    def get_comprehensive_fixtures(self, date_str):
        """Get comprehensive fixtures for all supported leagues"""
        print(f"🔄 API-Sports fallback: Fetching fixtures for {date_str}...")
        
        all_fixtures = []
        
        # Priority leagues to check
        priority_leagues = [
            'WC Qualification Europe',
            'WC Qualification Africa',
            'WC Qualification Asia',
            'WC Qualification South America',
            'WC Qualification CONCACAF',
            'WC Qualification Oceania',
            'WC Qualification Intercontinental Play',
            'UEFA Nations League',
            'UEFA Champions League',
            'UEFA Europa League'
        ]
        
        for league in priority_leagues:
            fixtures = self.get_fixtures_for_league(league, date_str)
            all_fixtures.extend(fixtures)
        
        print(f"🌍 API-Sports: Total {len(all_fixtures)} fixtures retrieved")
        return all_fixtures


def main():
    """Test the API-Sports fallback"""
    api_key = "960c628e1c91c4b1f125e1eec52ad862"
    
    fallback = APISportsFallback(api_key)
    
    # Test connection
    status = fallback.test_connection()
    if status:
        print(f"✅ API-Sports connected: {status.get('subscription', {}).get('plan', 'Unknown plan')}")
        
        # Test getting fixtures
        fixtures = fallback.get_comprehensive_fixtures('2025-09-08')
        
        if fixtures:
            print(f"\n📋 Sample fixtures:")
            for fixture in fixtures[:5]:
                print(f"  {fixture['kick_off']} | {fixture['home_team']} vs {fixture['away_team']} | {fixture['league']}")
        else:
            print("No fixtures found")
    else:
        print("❌ API-Sports connection failed")


if __name__ == "__main__":
    main()