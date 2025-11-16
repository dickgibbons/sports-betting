#!/usr/bin/env python3
"""
Test The Odds API with real key to get FanDuel and DraftKings soccer odds
"""

import requests
import json
from datetime import datetime
import pandas as pd

def test_real_odds_api():
    """Test The Odds API with real key for soccer odds from major sportsbooks"""

    print("🎯 TESTING THE ODDS API WITH REAL KEY")
    print("="*50)

    # Real API key provided
    api_key = "518c226b561ad7586ec8c5dd1144e3fb"
    base_url = "https://api.the-odds-api.com/v4"

    # First, get available sports
    print("📋 Getting available soccer sports...")

    try:
        sports_url = f"{base_url}/sports"
        params = {'apiKey': api_key}

        response = requests.get(sports_url, params=params, timeout=10)

        if response.status_code == 200:
            sports_data = response.json()
            soccer_sports = [sport for sport in sports_data if 'soccer' in sport.get('key', '')]

            print(f"✅ Found {len(soccer_sports)} soccer leagues available:")
            for sport in soccer_sports:
                print(f"  • {sport.get('title', 'Unknown')} ({sport.get('key', 'Unknown')})")

            # Test a few major leagues for odds
            major_leagues = ['soccer_epl', 'soccer_germany_bundesliga', 'soccer_usa_mls']

            for league in major_leagues:
                if any(sport.get('key') == league for sport in soccer_sports):
                    print(f"\n🏈 Getting {league} odds from FanDuel & DraftKings...")
                    get_league_odds(api_key, league)

        else:
            print(f"❌ Error getting sports: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"❌ Exception: {e}")

def get_league_odds(api_key, sport_key):
    """Get odds for a specific league from FanDuel and DraftKings"""

    base_url = "https://api.the-odds-api.com/v4"
    url = f"{base_url}/sports/{sport_key}/odds"

    params = {
        'apiKey': api_key,
        'regions': 'us',  # US region for FanDuel/DraftKings
        'markets': 'h2h,spreads,totals',  # Head-to-head, spreads, over/under
        'bookmakers': 'fanduel,draftkings,betmgm,caesars',
        'oddsFormat': 'decimal',
        'dateFormat': 'iso'
    }

    try:
        response = requests.get(url, params=params, timeout=15)

        if response.status_code == 200:
            data = response.json()

            if isinstance(data, list) and len(data) > 0:
                print(f"✅ Found {len(data)} upcoming matches in {sport_key}")

                # Process each match
                matches_with_odds = []

                for match in data[:5]:  # Show first 5 matches
                    home_team = match.get('home_team', 'Unknown')
                    away_team = match.get('away_team', 'Unknown')
                    commence_time = match.get('commence_time', 'Unknown')

                    print(f"\n📊 {home_team} vs {away_team}")
                    print(f"   Kick-off: {commence_time}")

                    # Process bookmaker odds
                    bookmakers = match.get('bookmakers', [])
                    match_odds = {
                        'match': f"{home_team} vs {away_team}",
                        'commence_time': commence_time,
                        'league': sport_key
                    }

                    for bookmaker in bookmakers:
                        book_name = bookmaker.get('title', 'Unknown')

                        if book_name in ['FanDuel', 'DraftKings', 'BetMGM', 'Caesars']:
                            markets = bookmaker.get('markets', [])

                            print(f"   🏆 {book_name}:")

                            for market in markets:
                                market_key = market.get('key', 'Unknown')
                                outcomes = market.get('outcomes', [])

                                if market_key == 'h2h':
                                    for outcome in outcomes:
                                        name = outcome.get('name', 'Unknown')
                                        price = outcome.get('price', 'N/A')
                                        print(f"      {name}: {price}")

                                        # Store in match_odds
                                        if name == home_team:
                                            match_odds[f'{book_name.lower()}_home'] = price
                                        elif name == away_team:
                                            match_odds[f'{book_name.lower()}_away'] = price
                                        elif name == 'Draw':
                                            match_odds[f'{book_name.lower()}_draw'] = price

                                elif market_key == 'totals':
                                    for outcome in outcomes:
                                        name = outcome.get('name', 'Unknown')
                                        price = outcome.get('price', 'N/A')
                                        point = outcome.get('point', 'N/A')
                                        print(f"      {name} {point}: {price}")

                    matches_with_odds.append(match_odds)

                # Create DataFrame if we have odds data
                if matches_with_odds:
                    create_odds_csv(matches_with_odds, sport_key)

            else:
                print(f"📋 No upcoming matches in {sport_key}")

        elif response.status_code == 401:
            print("❌ Unauthorized - API key issue")
        elif response.status_code == 429:
            print("❌ Rate limit exceeded")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text[:200]}")

    except Exception as e:
        print(f"❌ Exception: {e}")

def create_odds_csv(matches_data, league):
    """Create CSV with real FanDuel/DraftKings odds"""

    if not matches_data:
        return

    print(f"\n📊 Creating CSV with real {league} odds...")

    df = pd.DataFrame(matches_data)

    # Create filename
    today_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'output reports/real_odds_{league}_{today_str}.csv'

    # Save CSV
    df.to_csv(filename, index=False)
    print(f"✅ Real odds saved: {filename}")

    # Display sample
    if not df.empty:
        print(f"\n📋 SAMPLE REAL ODDS DATA:")
        print("="*50)

        # Show key columns
        display_cols = ['match', 'commence_time']
        odds_cols = [col for col in df.columns if any(book in col for book in ['fanduel', 'draftkings'])]
        display_cols.extend(odds_cols[:6])  # Show first 6 odds columns

        available_cols = [col for col in display_cols if col in df.columns]
        print(df[available_cols].head().to_string(index=False))

    return filename

def main():
    """Test real odds API"""
    test_real_odds_api()

    print(f"\n🎉 REAL ODDS API TEST COMPLETE!")
    print("="*40)
    print("If successful, you now have:")
    print("• Real FanDuel odds for soccer matches")
    print("• Real DraftKings odds for soccer matches")
    print("• CSV files with actual sportsbook data")
    print("• Ready to integrate into your betting model")

if __name__ == "__main__":
    main()