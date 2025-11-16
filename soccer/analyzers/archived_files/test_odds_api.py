#!/usr/bin/env python3
"""
Test The Odds API for FanDuel and DraftKings soccer odds
"""

import requests
import json
from datetime import datetime

def test_odds_api():
    """Test The Odds API for soccer odds from major sportsbooks"""

    print("🎯 TESTING THE ODDS API FOR FANDUEL & DRAFTKINGS SOCCER ODDS")
    print("="*70)

    # The Odds API endpoints
    base_url = "https://api.the-odds-api.com/v4"

    # Try with demo key first (they usually provide one for testing)
    api_key = "demo"  # We'll need a real key for production

    # Soccer leagues/sports to test
    soccer_sports = [
        'soccer_epl',              # English Premier League
        'soccer_germany_bundesliga', # German Bundesliga
        'soccer_spain_la_liga',    # Spanish La Liga
        'soccer_italy_serie_a',    # Italian Serie A
        'soccer_france_ligue_one', # French Ligue 1
        'soccer_usa_mls'           # Major League Soccer
    ]

    # Bookmakers we want (FanDuel, DraftKings, etc.)
    bookmakers = "fanduel,draftkings,betmgm,caesars"

    # Test each soccer league
    for sport in soccer_sports:
        print(f"\n🏈 Testing {sport.replace('_', ' ').title()}...")

        url = f"{base_url}/sports/{sport}/odds"
        params = {
            'apiKey': api_key,
            'regions': 'us',  # US region for FanDuel/DraftKings
            'markets': 'h2h,spreads,totals',  # Head-to-head, spreads, over/under
            'bookmakers': bookmakers,
            'oddsFormat': 'decimal',
            'dateFormat': 'iso'
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                if isinstance(data, list) and len(data) > 0:
                    print(f"✅ Found {len(data)} upcoming matches")

                    # Show sample match with odds
                    sample_match = data[0]
                    home_team = sample_match.get('home_team', 'Unknown')
                    away_team = sample_match.get('away_team', 'Unknown')
                    commence_time = sample_match.get('commence_time', 'Unknown')

                    print(f"Sample match: {home_team} vs {away_team}")
                    print(f"Kick-off: {commence_time}")

                    # Check for bookmaker odds
                    bookmakers_data = sample_match.get('bookmakers', [])
                    print(f"Bookmakers with odds: {len(bookmakers_data)}")

                    for bookmaker in bookmakers_data[:3]:  # Show first 3 bookmakers
                        book_name = bookmaker.get('title', 'Unknown')
                        markets = bookmaker.get('markets', [])

                        print(f"  📊 {book_name}:")
                        for market in markets:
                            market_key = market.get('key', 'Unknown')
                            outcomes = market.get('outcomes', [])

                            if market_key == 'h2h':
                                print(f"    Head-to-Head:")
                                for outcome in outcomes:
                                    name = outcome.get('name', 'Unknown')
                                    price = outcome.get('price', 'N/A')
                                    print(f"      {name}: {price}")

                            elif market_key == 'totals':
                                print(f"    Over/Under:")
                                for outcome in outcomes:
                                    name = outcome.get('name', 'Unknown')
                                    price = outcome.get('price', 'N/A')
                                    point = outcome.get('point', 'N/A')
                                    print(f"      {name} {point}: {price}")

                elif isinstance(data, list) and len(data) == 0:
                    print("📋 No upcoming matches in this league")
                else:
                    print(f"🔍 Unexpected response format: {type(data)}")

            elif response.status_code == 401:
                print("❌ Unauthorized - need valid API key")
            elif response.status_code == 429:
                print("❌ Rate limit exceeded")
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text[:200]}")

        except Exception as e:
            print(f"❌ Exception: {e}")

    # Test getting available sports
    print(f"\n📋 TESTING AVAILABLE SPORTS...")
    sports_url = f"{base_url}/sports"
    params = {'apiKey': api_key}

    try:
        response = requests.get(sports_url, params=params, timeout=10)
        if response.status_code == 200:
            sports_data = response.json()
            soccer_sports_found = [sport for sport in sports_data if 'soccer' in sport.get('key', '')]

            print(f"✅ Available soccer sports ({len(soccer_sports_found)}):")
            for sport in soccer_sports_found[:10]:  # Show first 10
                print(f"  • {sport.get('title', 'Unknown')} ({sport.get('key', 'Unknown')})")

        else:
            print(f"❌ Error getting sports list: {response.status_code}")

    except Exception as e:
        print(f"❌ Exception getting sports: {e}")

def get_real_api_key_info():
    """Show how to get a real API key"""

    print(f"\n🔑 HOW TO GET REAL API KEY:")
    print("="*35)
    print("1. Go to: https://the-odds-api.com/")
    print("2. Sign up for free account")
    print("3. Free tier includes 500 requests/month")
    print("4. Paid plans start at $30/month for 20,000 requests")
    print("5. Covers FanDuel, DraftKings, BetMGM, Caesars")
    print("6. Includes soccer leagues: EPL, Bundesliga, La Liga, Serie A, MLS")

    print(f"\n💰 PRICING BREAKDOWN:")
    print("• Free: 500 requests/month")
    print("• Starter: $30/month - 20K requests")
    print("• Pro: $79/month - 50K requests")
    print("• Premium: $149/month - 100K requests")

def main():
    """Test The Odds API"""

    test_odds_api()
    get_real_api_key_info()

if __name__ == "__main__":
    main()