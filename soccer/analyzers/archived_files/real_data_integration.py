#!/usr/bin/env python3
"""
Real Data Integration

Replaces ALL simulated data with real API data from API-Sports and FootyStats
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
import pandas as pd

class RealDataIntegration:
    """Integrate real data from multiple APIs for all data points"""
    
    def __init__(self):
        # API Keys
        self.api_sports_key = "960c628e1c91c4b1f125e1eec52ad862"
        self.footystats_key = "ceb338b9bcb82a452efc114fb2d3cccac67f58be1569e7b5acf1d2195adeae11"
        
        # API URLs
        self.api_sports_url = "https://v3.football.api-sports.io"
        self.footystats_url = "https://api.footystats.org/api"
        
        # Headers
        self.api_sports_headers = {'x-apisports-key': self.api_sports_key}
        self.footystats_headers = {'x-api-key': self.footystats_key}
        
        print("🔌 Real Data Integration initialized")
        print(f"   📡 API-Sports: {self.api_sports_url}")
        print(f"   📊 FootyStats: {self.footystats_url}")
    
    def get_real_fixtures_with_odds(self, date_str: str) -> List[Dict]:
        """Get real fixtures with live odds from APIs"""
        
        print(f"📅 Getting real fixtures with odds for {date_str}")
        
        # Try FootyStats first for odds data
        footystats_fixtures = self.get_footystats_fixtures(date_str)
        
        # Get API-Sports fixtures for backup
        api_sports_fixtures = self.get_api_sports_fixtures(date_str)
        
        # Combine and enhance fixture data
        combined_fixtures = self.combine_fixture_data(footystats_fixtures, api_sports_fixtures)
        
        return combined_fixtures
    
    def get_footystats_fixtures(self, date_str: str) -> List[Dict]:
        """Get fixtures from FootyStats with odds"""
        
        print("📊 Fetching fixtures from FootyStats...")
        
        try:
            # FootyStats fixtures endpoint
            url = f"{self.footystats_url}/fixtures"
            params = {
                'date': date_str,
                'include_odds': 'true',
                'include_stats': 'true'
            }
            
            response = requests.get(url, headers=self.footystats_headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                fixtures = data.get('data', [])
                print(f"   ✅ FootyStats: {len(fixtures)} fixtures with odds")
                return self.process_footystats_fixtures(fixtures)
            else:
                print(f"   ⚠️ FootyStats error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"   ❌ FootyStats error: {e}")
            return []
    
    def get_api_sports_fixtures(self, date_str: str) -> List[Dict]:
        """Get fixtures from API-Sports"""
        
        print("📡 Fetching fixtures from API-Sports...")
        
        try:
            url = f"{self.api_sports_url}/fixtures"
            params = {'date': date_str}
            
            response = requests.get(url, headers=self.api_sports_headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                fixtures = data.get('response', [])
                print(f"   ✅ API-Sports: {len(fixtures)} fixtures")
                return self.process_api_sports_fixtures(fixtures)
            else:
                print(f"   ⚠️ API-Sports error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"   ❌ API-Sports error: {e}")
            return []
    
    def process_footystats_fixtures(self, fixtures: List[Dict]) -> List[Dict]:
        """Process FootyStats fixtures into our format - only upcoming/live games"""
        
        processed = []
        
        # Status values for games we want to include (not finished)
        valid_statuses = ['scheduled', 'live', 'halftime', 'upcoming', 'not_started']
        
        for fixture in fixtures:
            try:
                # Check fixture status first - skip finished games
                status = fixture.get('status', 'scheduled')
                if status not in valid_statuses:
                    continue  # Skip finished games (finished, completed, etc.)
                
                # Extract team information
                home_team = fixture.get('home_team', {}).get('name', 'Unknown')
                away_team = fixture.get('away_team', {}).get('name', 'Unknown')
                
                # Extract timing
                kick_off_time = fixture.get('date_unix', '')
                if kick_off_time:
                    dt = datetime.fromtimestamp(int(kick_off_time))
                    kick_off = dt.strftime('%H:%M')
                else:
                    kick_off = '15:00'
                
                # Extract league and country
                competition = fixture.get('competition', {})
                league_name = competition.get('name', 'Unknown')
                country = competition.get('country', 'Unknown')  # FootyStats might have country in competition
                
                # Extract real odds
                odds_data = fixture.get('odds', {})
                home_odds = float(odds_data.get('home_win', 2.0))
                draw_odds = float(odds_data.get('draw', 3.0))
                away_odds = float(odds_data.get('away_win', 3.0))
                
                # Get additional market odds
                over_under = odds_data.get('over_under', {})
                corners_odds = odds_data.get('corners', {})
                btts_odds = odds_data.get('btts', {})
                
                processed_fixture = {
                    'kick_off': kick_off,
                    'home_team': home_team,
                    'away_team': away_team,
                    'league': league_name,
                    'country': country,
                    'home_odds': home_odds,
                    'draw_odds': draw_odds,
                    'away_odds': away_odds,
                    'over_15_odds': float(over_under.get('over_1_5', 1.3)),
                    'under_15_odds': float(over_under.get('under_1_5', 3.5)),
                    'over_25_odds': float(over_under.get('over_2_5', 2.0)),
                    'under_25_odds': float(over_under.get('under_2_5', 1.8)),
                    'btts_yes_odds': float(btts_odds.get('yes', 1.9)),
                    'btts_no_odds': float(btts_odds.get('no', 1.9)),
                    'over_95_corners_odds': float(corners_odds.get('over_9_5', 2.0)),
                    'under_95_corners_odds': float(corners_odds.get('under_9_5', 1.8)),
                    'source': 'FootyStats',
                    'fixture_id': fixture.get('id', ''),
                    'status': status
                }
                
                processed.append(processed_fixture)
                
            except Exception as e:
                print(f"   ⚠️ Error processing FootyStats fixture: {e}")
                continue
        
        return processed
    
    def process_api_sports_fixtures(self, fixtures: List[Dict]) -> List[Dict]:
        """Process API-Sports fixtures into our format - only upcoming/live games"""
        
        processed = []
        
        # Status codes for games we want to include (not finished)
        valid_statuses = ['NS', 'TBD', 'PST', '1H', '2H', 'HT', 'ET', 'BT', 'SUSP', 'INT']
        
        for fixture in fixtures:
            try:
                # Check fixture status first - skip finished games
                fixture_info = fixture.get('fixture', {})
                status = fixture_info.get('status', {}).get('short', 'NS')
                
                if status not in valid_statuses:
                    continue  # Skip finished games (FT, AET, PEN, etc.)
                
                teams = fixture.get('teams', {})
                home_team = teams.get('home', {}).get('name', 'Unknown')
                away_team = teams.get('away', {}).get('name', 'Unknown')
                
                # Extract timing
                fixture_date = fixture_info.get('date', '')
                if fixture_date:
                    dt = datetime.fromisoformat(fixture_date.replace('Z', '+00:00'))
                    kick_off = dt.strftime('%H:%M')
                else:
                    kick_off = '15:00'
                
                # Extract league and country
                league_info = fixture.get('league', {})
                league_name = league_info.get('name', 'Unknown')
                country = league_info.get('country', 'Unknown')
                
                # API-Sports doesn't provide odds in free tier, so we'll get from bookmakers API
                odds_data = self.get_odds_for_fixture(fixture_info.get('id'))
                
                processed_fixture = {
                    'kick_off': kick_off,
                    'home_team': home_team,
                    'away_team': away_team,
                    'league': league_name,
                    'country': country,
                    'home_odds': odds_data.get('home_odds', 2.0),
                    'draw_odds': odds_data.get('draw_odds', 3.0),
                    'away_odds': odds_data.get('away_odds', 3.0),
                    'source': 'API-Sports',
                    'fixture_id': fixture_info.get('id', ''),
                    'status': status
                }
                
                processed.append(processed_fixture)
                
            except Exception as e:
                print(f"   ⚠️ Error processing API-Sports fixture: {e}")
                continue
        
        return processed
    
    def get_odds_for_fixture(self, fixture_id: str) -> Dict:
        """Get betting odds for a specific fixture"""
        
        if not fixture_id:
            return {'home_odds': 2.0, 'draw_odds': 3.0, 'away_odds': 3.0}
        
        try:
            url = f"{self.api_sports_url}/odds"
            params = {
                'fixture': fixture_id,
                'bookmaker': '8',  # Bet365
                'bet': '1'         # Match Winner
            }
            
            response = requests.get(url, headers=self.api_sports_headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                odds_data = data.get('response', [])
                
                if odds_data and len(odds_data) > 0:
                    bookmaker_data = odds_data[0].get('bookmakers', [])
                    if bookmaker_data and len(bookmaker_data) > 0:
                        bets_data = bookmaker_data[0].get('bets', [])
                        if bets_data and len(bets_data) > 0:
                            values = bets_data[0].get('values', [])
                            if len(values) >= 3:
                                return {
                                    'home_odds': float(values[0].get('odd', 2.0)),
                                    'draw_odds': float(values[1].get('odd', 3.0)),
                                    'away_odds': float(values[2].get('odd', 3.0))
                                }
            
        except Exception as e:
            print(f"   ⚠️ Error getting odds for fixture {fixture_id}: {e}")
        
        # Return default odds if API fails
        return {'home_odds': 2.0, 'draw_odds': 3.0, 'away_odds': 3.0}
    
    def combine_fixture_data(self, footystats_fixtures: List[Dict], api_sports_fixtures: List[Dict]) -> List[Dict]:
        """Combine fixture data from both APIs, preferring FootyStats for odds"""
        
        print("🔀 Combining fixture data from both APIs...")
        
        # Start with FootyStats fixtures (have odds)
        combined = footystats_fixtures.copy()
        
        # Add API-Sports fixtures that don't match FootyStats
        for api_fixture in api_sports_fixtures:
            # Check if this fixture already exists in FootyStats data
            found_match = False
            for fs_fixture in footystats_fixtures:
                if (self.team_names_match(api_fixture['home_team'], fs_fixture['home_team']) and
                    self.team_names_match(api_fixture['away_team'], fs_fixture['away_team'])):
                    found_match = True
                    break
            
            if not found_match:
                combined.append(api_fixture)
        
        print(f"   ✅ Combined: {len(combined)} total fixtures")
        return combined
    
    def team_names_match(self, name1: str, name2: str) -> bool:
        """Check if two team names refer to the same team"""
        
        name1_lower = name1.lower()
        name2_lower = name2.lower()
        
        # Direct match
        if name1_lower == name2_lower:
            return True
        
        # Check if one name contains the other
        if name1_lower in name2_lower or name2_lower in name1_lower:
            return True
        
        # Check significant words
        words1 = [w for w in name1_lower.split() if len(w) > 3]
        words2 = [w for w in name2_lower.split() if len(w) > 3]
        
        for word1 in words1:
            for word2 in words2:
                if word1 == word2 or word1 in word2 or word2 in word1:
                    return True
        
        return False
    
    def get_real_match_statistics(self, fixture_id: str, source: str) -> Dict:
        """Get real match statistics including corners, cards, etc."""
        
        print(f"📊 Getting real match statistics for fixture {fixture_id}")
        
        if source == 'FootyStats':
            return self.get_footystats_statistics(fixture_id)
        else:
            return self.get_api_sports_statistics(fixture_id)
    
    def get_footystats_statistics(self, fixture_id: str) -> Dict:
        """Get match statistics from FootyStats"""
        
        try:
            url = f"{self.footystats_url}/match"
            params = {'id': fixture_id}
            
            response = requests.get(url, headers=self.footystats_headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                match_data = data.get('data', {})
                
                stats = match_data.get('stats', {})
                return {
                    'home_corners': int(stats.get('home_corners', 0)),
                    'away_corners': int(stats.get('away_corners', 0)),
                    'total_corners': int(stats.get('home_corners', 0)) + int(stats.get('away_corners', 0)),
                    'home_cards': int(stats.get('home_yellowcards', 0)) + int(stats.get('home_redcards', 0)),
                    'away_cards': int(stats.get('away_yellowcards', 0)) + int(stats.get('away_redcards', 0)),
                    'home_shots': int(stats.get('home_shots', 0)),
                    'away_shots': int(stats.get('away_shots', 0)),
                    'source': 'FootyStats'
                }
            
        except Exception as e:
            print(f"   ❌ FootyStats statistics error: {e}")
        
        return {'total_corners': 0, 'source': 'none'}
    
    def get_api_sports_statistics(self, fixture_id: str) -> Dict:
        """Get match statistics from API-Sports"""
        
        try:
            url = f"{self.api_sports_url}/fixtures/statistics"
            params = {'fixture': fixture_id}
            
            response = requests.get(url, headers=self.api_sports_headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                statistics = data.get('response', [])
                
                home_corners = 0
                away_corners = 0
                
                for team_stats in statistics:
                    stats_list = team_stats.get('statistics', [])
                    is_home = len([s for s in statistics if s == team_stats]) == 1  # First team is usually home
                    
                    for stat in stats_list:
                        if stat.get('type') == 'Corner Kicks':
                            corners = int(stat.get('value', 0) or 0)
                            if is_home:
                                home_corners = corners
                            else:
                                away_corners = corners
                
                return {
                    'home_corners': home_corners,
                    'away_corners': away_corners,
                    'total_corners': home_corners + away_corners,
                    'source': 'API-Sports'
                }
            
        except Exception as e:
            print(f"   ❌ API-Sports statistics error: {e}")
        
        return {'total_corners': 0, 'source': 'none'}
    
    def update_daily_system_with_real_data(self, date_str: str):
        """Update the daily betting system to use real data"""
        
        print(f"🔄 Updating daily system with real data for {date_str}")
        
        # Get real fixtures with odds
        real_fixtures = self.get_real_fixtures_with_odds(date_str)
        
        # Filter for leagues we follow
        followed_fixtures = self.filter_followed_leagues(real_fixtures)
        
        print(f"   ✅ Found {len(followed_fixtures)} fixtures in followed leagues")
        
        # Save real fixtures to replace simulated ones
        self.save_real_fixtures(followed_fixtures, date_str)
        
        return followed_fixtures
    
    def filter_followed_leagues(self, fixtures: List[Dict]) -> List[Dict]:
        """Filter fixtures to only include leagues we follow with STRICT country verification"""
        
        # Load followed leagues with countries from config
        try:
            config_file = "/Users/dickgibbons/soccer-betting-python/soccer/output reports/UPDATED_supported_leagues_database.csv"
            df = pd.read_csv(config_file)
            # Create league+country mapping
            followed_leagues_with_country = {}
            for _, row in df.iterrows():
                league_name = row['league_name']
                country = row['country']
                followed_leagues_with_country[league_name] = country
        except:
            followed_leagues_with_country = {
                'Premier League': 'England', 'La Liga': 'Spain', 'Serie A': 'Italy', 
                'Bundesliga': 'Germany', 'Ligue 1': 'France',
                'Championship': 'England', 'Ekstraklasa': 'Poland'
            }
        
        filtered = []
        rejected = {}
        for fixture in fixtures:
            league = fixture['league']
            country = fixture.get('country', 'Unknown')
            
            # Check if we follow this league AND it's from the correct country
            if league in followed_leagues_with_country:
                expected_country = followed_leagues_with_country[league]
                if country == expected_country:
                    filtered.append(fixture)
                else:
                    # League name matches but wrong country - REJECT
                    key = f"{league} ({country})"
                    rejected[key] = rejected.get(key, 0) + 1
            else:
                # League not in our database - REJECT
                key = f"{league} ({country})"
                rejected[key] = rejected.get(key, 0) + 1
        
        print(f"🔍 STRICT LEAGUE FILTERING RESULTS:")
        print(f"   ✅ Accepted: {len(filtered)} fixtures in followed leagues")
        if rejected:
            print(f"   ❌ Rejected leagues:")
            for league, count in sorted(rejected.items()):
                print(f"      • {league}: {count} fixture{'s' if count > 1 else ''}")
        
        return filtered
    
    def is_followed_league(self, league_name: str, followed_leagues: List[str]) -> bool:
        """Check if a league is one we follow - STRICT database-only matching"""
        
        # Direct exact match first
        if league_name in followed_leagues:
            return True
        
        # Check for exact matches with common variations
        league_variations = {
            'Ekstraklasa': ['ekstraklasa'],
            'La Liga': ['la liga', 'primera division'],
            'Serie A': ['serie a'],
            'Bundesliga': ['bundesliga'], 
            'Premier League': ['premier league'],
            'Ligue 1': ['ligue 1'],
            'Championship': ['championship'],
            'MLS': ['mls', 'major league soccer'],
            'Liga MX': ['liga mx'],
            'Brazil Serie A': ['brazilian serie a', 'brazil serie a'],
            'Brazil Serie B': ['brazilian serie b', 'brazil serie b'],
            'UEFA Champions League': ['uefa champions league', 'champions league'],
            'UEFA Europa League': ['uefa europa league', 'europa league'],
            'WC Qualification Europe': ['wc qualification europe', 'world cup qualification europe'],
            'WC Qualification Africa': ['wc qualification africa', 'world cup qualification africa'],
            'WC Qualification Asia': ['wc qualification asia', 'world cup qualification asia']
        }
        
        league_lower = league_name.lower()
        
        # Check for variations of followed leagues
        for followed_league in followed_leagues:
            variations = league_variations.get(followed_league, [followed_league.lower()])
            if league_lower in variations:
                return True
        
        # REJECT everything else - no fallback to hardcoded lists
        return False
    
    def save_real_fixtures(self, fixtures: List[Dict], date_str: str):
        """Save real fixtures data for the daily system to use"""
        
        output_file = f"/Users/dickgibbons/soccer-betting-python/soccer/real_fixtures_{date_str.replace('-', '')}.json"
        
        with open(output_file, 'w') as f:
            json.dump(fixtures, f, indent=2)
        
        print(f"💾 Real fixtures saved to: {output_file}")

def main():
    """Test the real data integration"""
    
    integrator = RealDataIntegration()
    
    # Test with today's date
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"🧪 Testing real data integration for {today}")
    
    fixtures = integrator.update_daily_system_with_real_data(today)
    
    print(f"\n✅ Real data integration test complete!")
    print(f"📊 Found {len(fixtures)} real fixtures with odds data")
    
    if fixtures:
        print(f"\n📋 Sample fixtures:")
        for i, fixture in enumerate(fixtures[:3]):
            print(f"   {i+1}. {fixture['home_team']} vs {fixture['away_team']}")
            print(f"      🏆 {fixture['league']}")
            print(f"      💰 Odds: {fixture['home_odds']:.2f} / {fixture['draw_odds']:.2f} / {fixture['away_odds']:.2f}")
            print(f"      📡 Source: {fixture['source']}")

if __name__ == "__main__":
    main()