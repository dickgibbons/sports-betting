#!/usr/bin/env python3
"""
Debug the real odds parsing to ensure we're getting actual FanDuel/DraftKings data
"""

import requests
import json
from datetime import datetime

def debug_odds_parsing():
    """Debug odds parsing from The Odds API"""

    print("🔍 DEBUGGING REAL ODDS PARSING")
    print("="*40)

    api_key = "518c226b561ad7586ec8c5dd1144e3fb"
    base_url = "https://api.the-odds-api.com/v4"

    # Test EPL odds specifically
    url = f"{base_url}/sports/soccer_epl/odds"
    params = {
        'apiKey': api_key,
        'regions': 'us',
        'markets': 'h2h,spreads,totals',
        'bookmakers': 'fanduel,draftkings,betmgm',
        'oddsFormat': 'decimal',
        'dateFormat': 'iso'
    }

    try:
        response = requests.get(url, params=params, timeout=15)

        if response.status_code == 200:
            data = response.json()

            print(f"✅ Got {len(data)} EPL matches")

            # Show detailed parsing for all matches to check dates
            for i, match in enumerate(data):
                print(f"\n🏈 MATCH {i+1}: Raw Data Analysis")
                print("="*50)

                home_team = match.get('home_team', 'Unknown')
                away_team = match.get('away_team', 'Unknown')

                print(f"Teams: {home_team} vs {away_team}")
                print(f"Commence: {match.get('commence_time', 'Unknown')}")

                bookmakers = match.get('bookmakers', [])
                print(f"Bookmakers available: {len(bookmakers)}")

                for book in bookmakers:
                    book_name = book.get('title', 'Unknown')
                    markets = book.get('markets', [])

                    print(f"\n📊 {book_name}:")

                    for market in markets:
                        market_key = market.get('key', 'Unknown')
                        outcomes = market.get('outcomes', [])

                        print(f"  Market: {market_key}")

                        for outcome in outcomes:
                            name = outcome.get('name', 'Unknown')
                            price = outcome.get('price', 'Unknown')
                            point = outcome.get('point', '')

                            if point:
                                print(f"    {name} {point}: {price}")
                            else:
                                print(f"    {name}: {price}")

                print("-" * 50)

        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"❌ Exception: {e}")

def main():
    debug_odds_parsing()

if __name__ == "__main__":
    main()