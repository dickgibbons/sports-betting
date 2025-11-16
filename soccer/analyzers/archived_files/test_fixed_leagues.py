#!/usr/bin/env python3
"""
Test the fixed league normalization and show corrected data
"""

import sys
sys.path.append('.')
from optimal_profit_model import OptimalProfitModel

def test_fixed_leagues():
    """Test the fixed league parsing and show corrected league names"""

    print("🔍 TESTING FIXED LEAGUE NORMALIZATION")
    print("="*50)

    model = OptimalProfitModel()

    # Fetch fixtures with corrected parsing
    fixtures = model.fetch_todays_fixtures()

    if fixtures:
        print(f"✅ Found {len(fixtures)} fixtures with corrected league data:")
        print("\n📊 CORRECTED LEAGUE DATA:")
        print("="*60)

        for i, fixture in enumerate(fixtures[:10], 1):
            print(f"{i}. {fixture['home_team']} vs {fixture['away_team']}")
            print(f"   League: {fixture['league']}")
            print(f"   Odds: H:{fixture['home_odds']} A:{fixture['away_odds']} D:{fixture['draw_odds']}")
            print()

        # Show unique leagues
        unique_leagues = set(fixture['league'] for fixture in fixtures)
        print(f"🌍 UNIQUE LEAGUES FOUND ({len(unique_leagues)}):")
        print("="*40)
        for league in sorted(unique_leagues):
            print(f"• {league}")

    else:
        print("❌ No fixtures found")

if __name__ == "__main__":
    test_fixed_leagues()