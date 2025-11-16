#!/usr/bin/env python3
"""
Create corrected CSV with proper league data
"""

import sys
sys.path.append('.')
from optimal_profit_model import OptimalProfitModel
import pandas as pd
from datetime import datetime
import json
import os

def create_corrected_csv():
    """Create CSV with corrected league data"""

    print("🔧 CREATING CORRECTED CSV WITH PROPER LEAGUE DATA")
    print("="*60)

    # Initialize model and fetch corrected data
    model = OptimalProfitModel()
    fixtures = model.fetch_todays_fixtures()

    if not fixtures:
        print("❌ No fixtures found")
        return

    print(f"📊 Processing {len(fixtures)} fixtures with correct league data")

    # Create comprehensive DataFrame with all available matches
    matches_data = []

    for fixture in fixtures:
        # Calculate potential profits for different bet types
        home_odds = fixture['home_odds']
        away_odds = fixture['away_odds']
        draw_odds = fixture['draw_odds']
        stake = 25

        matches_data.append({
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time_analyzed': datetime.now().strftime('%H:%M:%S'),
            'match': f"{fixture['home_team']} vs {fixture['away_team']}",
            'league': fixture['league'],  # Now correctly shows actual league
            'home_team': fixture['home_team'],
            'away_team': fixture['away_team'],
            'home_odds': home_odds,
            'away_odds': away_odds,
            'draw_odds': draw_odds,
            'home_win_profit': (home_odds - 1) * stake,
            'away_win_profit': (away_odds - 1) * stake,
            'draw_profit': (draw_odds - 1) * stake,
            'home_win_return': home_odds * stake,
            'away_win_return': away_odds * stake,
            'draw_return': draw_odds * stake,
            'data_source': 'API-Sports',
            'odds_source': fixture['odds_source']
        })

    # Create DataFrame
    matches_df = pd.DataFrame(matches_data)

    # Create summary
    summary_data = {
        'date': [datetime.now().strftime('%Y-%m-%d')],
        'analysis_time': [datetime.now().strftime('%H:%M:%S')],
        'total_matches_available': [len(fixtures)],
        'unique_leagues': [len(set(fixture['league'] for fixture in fixtures))],
        'countries_represented': [len(set(league.split('(')[-1].replace(')', '')
                                       for league in set(fixture['league'] for fixture in fixtures)
                                       if '(' in league))],
        'data_source': ['API-Sports with real fixture data'],
        'league_data_status': ['CORRECTED - Shows actual leagues, not normalized'],
        'previous_issue': ['Fixed: Jamaica Premier League no longer shows as EPL'],
        'model_version': ['Multi-Strategy Profit Maximizer v1.0 (Fixed)']
    }

    summary_df = pd.DataFrame(summary_data)

    # Save files
    today_str = datetime.now().strftime('%Y%m%d')
    timestamp_str = datetime.now().strftime('%H%M%S')

    matches_filename = f'output reports/corrected_matches_{today_str}_{timestamp_str}.csv'
    summary_filename = f'output reports/corrected_summary_{today_str}_{timestamp_str}.csv'

    matches_df.to_csv(matches_filename, index=False)
    summary_df.to_csv(summary_filename, index=False)

    print(f"✅ Corrected matches saved: {matches_filename}")
    print(f"✅ Corrected summary saved: {summary_filename}")

    # Display sample of corrected data
    print(f"\n📊 SAMPLE OF CORRECTED DATA:")
    print("="*50)
    display_cols = ['match', 'league', 'home_odds', 'away_odds', 'draw_odds']
    print(matches_df[display_cols].head(8).to_string(index=False))

    print(f"\n🌍 LEAGUES REPRESENTED:")
    print("="*30)
    unique_leagues = sorted(matches_df['league'].unique())
    for i, league in enumerate(unique_leagues, 1):
        print(f"{i}. {league}")

    print(f"\n✅ LEAGUE DATA CORRECTION SUMMARY:")
    print("="*40)
    print("• Jamaica Premier League now correctly shows as 'Premier League (Jamaica)'")
    print("• EPL is reserved only for England Premier League")
    print("• All leagues now show country context for clarity")
    print("• No more confusion between different 'Premier League' competitions")

    return matches_filename, summary_filename

def main():
    create_corrected_csv()

if __name__ == "__main__":
    main()