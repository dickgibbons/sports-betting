#!/usr/bin/env python3
"""
Simple Soccer Betting Predictor using FootyStats API

A simplified version that tests the API connection and basic prediction logic
without heavy dependencies.
"""

import requests
import json
import time
import logging
from datetime import datetime

class FootyStatsAPI:
    """Simplified client for FootyStats API interactions"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.football-data-api.com"
        self.session = requests.Session()
        self.rate_limit_delay = 1
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def make_request(self, endpoint: str, params: dict = None) -> dict:
        """Make API request with error handling"""
        url = f"{self.base_url}/{endpoint}"
        
        if params is None:
            params = {}
        params['key'] = self.api_key
        
        try:
            time.sleep(self.rate_limit_delay)
            self.logger.info(f"Making request to: {endpoint}")
            response = self.session.get(url, params=params)
            
            self.logger.info(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"Response received with {len(data.get('data', []))} items")
                return data
            else:
                self.logger.error(f"API request failed: {response.status_code} - {response.text}")
                return {'error': f"HTTP {response.status_code}", 'message': response.text}
                
        except Exception as e:
            self.logger.error(f"Request exception: {e}")
            return {'error': str(e)}
    
    def get_league_matches(self, league_id: int, season: str = None) -> list:
        """Fetch matches for a specific league"""
        params = {'league_id': league_id}
        if season:
            params['season'] = season
            
        data = self.make_request('league-matches', params)
        return data.get('data', [])

def test_api_connection(api_key: str):
    """Test the API connection with various league IDs"""
    
    print("🏈 Testing FootyStats API Connection")
    print("=" * 40)
    
    api = FootyStatsAPI(api_key)
    
    # Test different league IDs
    test_leagues = [
        {'id': 1625, 'name': 'Premier League'},
        {'id': 1729, 'name': 'La Liga'}, 
        {'id': 1854, 'name': 'Bundesliga'},
        {'id': 2105, 'name': 'Serie A'},
        {'id': 1843, 'name': 'Ligue 1'},
    ]
    
    for league in test_leagues:
        print(f"\n📊 Testing {league['name']} (ID: {league['id']})")
        
        matches = api.get_league_matches(league['id'])
        
        if isinstance(matches, list) and len(matches) > 0:
            print(f"✅ Success! Found {len(matches)} matches")
            
            # Show sample match data structure
            sample_match = matches[0]
            print(f"📝 Sample match data keys: {list(sample_match.keys())}")
            
            # Extract basic info if available
            if 'home_team' in sample_match and 'away_team' in sample_match:
                home_team = sample_match.get('home_team', {}).get('name', 'Unknown')
                away_team = sample_match.get('away_team', {}).get('name', 'Unknown')
                match_date = sample_match.get('date', 'Unknown')
                print(f"🏆 Sample: {home_team} vs {away_team} ({match_date})")
        else:
            print(f"❌ No data received for {league['name']}")
            if isinstance(matches, dict) and 'error' in matches:
                print(f"   Error: {matches['error']}")

def simple_prediction_example(matches_data: list):
    """Simple prediction logic example"""
    
    if not matches_data:
        print("❌ No match data available for prediction")
        return
    
    print("\n🔮 Simple Prediction Example")
    print("=" * 30)
    
    # Take first match as example
    match = matches_data[0]
    
    print("📊 Match Analysis:")
    
    # Extract basic info
    home_team = match.get('home_team', {}).get('name', 'Unknown')
    away_team = match.get('away_team', {}).get('name', 'Unknown')
    
    print(f"🏠 Home Team: {home_team}")
    print(f"🚌 Away Team: {away_team}")
    
    # Simple prediction based on available data
    prediction_factors = []
    
    # Check if we have odds data
    if 'odds' in match:
        odds = match['odds']
        home_odds = odds.get('home', 2.0)
        draw_odds = odds.get('draw', 3.0) 
        away_odds = odds.get('away', 2.0)
        
        print(f"💰 Odds - Home: {home_odds}, Draw: {draw_odds}, Away: {away_odds}")
        
        # Simple logic: lower odds = higher probability
        if home_odds < away_odds and home_odds < draw_odds:
            prediction_factors.append("Home team favored (lowest odds)")
        elif away_odds < home_odds and away_odds < draw_odds:
            prediction_factors.append("Away team favored (lowest odds)")
        else:
            prediction_factors.append("Draw likely (lowest odds)")
    
    # Check for form data
    home_form = match.get('home_team_form', [])
    away_form = match.get('away_team_form', [])
    
    if home_form and away_form:
        home_points = sum(3 if result == 'W' else 1 if result == 'D' else 0 for result in home_form[-5:])
        away_points = sum(3 if result == 'W' else 1 if result == 'D' else 0 for result in away_form[-5:])
        
        print(f"📈 Recent Form - Home: {home_points}/15 points, Away: {away_points}/15 points")
        
        if home_points > away_points:
            prediction_factors.append("Home team has better recent form")
        elif away_points > home_points:
            prediction_factors.append("Away team has better recent form")
        else:
            prediction_factors.append("Both teams have similar form")
    
    # Make simple prediction
    print(f"\n🎯 Prediction Factors:")
    for factor in prediction_factors:
        print(f"   • {factor}")
    
    if not prediction_factors:
        print("   • Insufficient data for detailed analysis")
        print("   • Prediction: Check odds and team news")
    
    print("\n💡 Recommendation:")
    print("   This is a basic example. For real betting decisions:")
    print("   • Analyze more historical data")
    print("   • Consider team injuries and suspensions")
    print("   • Look at head-to-head records")
    print("   • Consider home/away performance")
    print("   • Use multiple prediction models")

def main():
    """Test the API and show basic prediction example"""
    
    API_KEY = "ceb338b9bcb82a452efc114fb2d3cccac67f58be1569e7b5acf1d2195adeae11"
    
    print("🚀 Starting Soccer Prediction System Test")
    print("=" * 50)
    
    # Test API connection
    test_api_connection(API_KEY)
    
    # Get some sample data for prediction example
    print(f"\n🔄 Fetching sample data for prediction demo...")
    api = FootyStatsAPI(API_KEY)
    
    # Try to get Premier League data
    sample_matches = api.get_league_matches(1625)  # Premier League
    
    if isinstance(sample_matches, list) and len(sample_matches) > 0:
        simple_prediction_example(sample_matches)
    else:
        print("❌ Could not fetch sample data for prediction demo")
    
    print(f"\n✨ Test complete!")
    print("\n⚠️  Next steps:")
    print("   • Verify which league IDs work with your API key")  
    print("   • Collect historical data for model training")
    print("   • Implement more sophisticated prediction algorithms")
    print("   • Add proper data validation and error handling")
    print("   • Consider betting bankroll management strategies")

if __name__ == "__main__":
    main()