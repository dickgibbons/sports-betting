#!/usr/bin/env python3
"""
Enhanced Daily Picks Report with Clear Team Names and Bet Types
"""

import pandas as pd
import numpy as np
from datetime import datetime
import csv

def create_enhanced_picks_report():
    """Create enhanced report with clear team names and bet descriptions"""
    
    # Load the detailed backtest results
    detailed_file = "./output reports/multi_market_backtest_detailed_20250906_094318.csv"
    
    try:
        # Read detailed results
        detailed_df = pd.read_csv(detailed_file)
        
        print(f"📊 Processing {len(detailed_df)} bets for enhanced report")
        
        # Create enhanced picks report
        enhanced_picks = []
        
        for idx, bet in detailed_df.iterrows():
            # Parse team names from match string
            home_team, away_team = parse_team_names(bet['match'])
            
            # Get clear bet description
            bet_description = get_bet_description(bet['market'])
            
            # Create enhanced record
            enhanced_pick = {
                # Date and Match Info
                'date': bet['date'],
                'day_of_week': pd.to_datetime(bet['date']).strftime('%A'),
                'home_team': home_team,
                'away_team': away_team,
                'league': bet['league'],
                
                # Clear Bet Information
                'bet_type': bet['market'],
                'bet_description': bet_description,
                'odds': round(bet['odds'], 2),
                'stake': round(bet['stake'], 2),
                
                # Prediction Quality
                'edge_percent': round(bet['edge'] * 100, 1),
                'confidence_percent': round(bet['confidence'] * 100, 1),
                
                # Results
                'result': 'WIN' if bet['bet_won'] else 'LOSS',
                'profit_loss': round(bet['profit_loss'], 2),
                'bet_roi_percent': round((bet['profit_loss'] / bet['stake']) * 100, 1) if bet['stake'] > 0 else 0,
                
                # Bankroll Info
                'bankroll_before': round(bet['bankroll_before'], 2),
                'bankroll_after': round(bet['bankroll_after'], 2),
                'total_return_percent': round(((bet['bankroll_after'] - 300) / 300) * 100, 1),
                
                # Market Classification
                'market_category': classify_market_category(bet['market']),
                'risk_level': get_risk_level(bet['odds']),
                
                # Match Context
                'match_display': f"{home_team} vs {away_team}",
                'full_description': f"{bet_description} @ {bet['odds']:.2f}"
            }
            
            enhanced_picks.append(enhanced_pick)
        
        # Create DataFrame
        picks_df = pd.DataFrame(enhanced_picks)
        
        # Add running totals
        picks_df['cumulative_profit'] = picks_df['profit_loss'].cumsum()
        picks_df['bet_number'] = range(1, len(picks_df) + 1)
        
        # Save to CSV
        output_file = "./output reports/enhanced_daily_picks_report.csv"
        picks_df.to_csv(output_file, index=False)
        
        print(f"✅ Enhanced picks report saved: enhanced_daily_picks_report.csv")
        
        # Show sample
        sample_cols = ['date', 'home_team', 'away_team', 'bet_description', 'odds', 'stake', 'result', 'profit_loss']
        print(f"\n📋 Sample of enhanced report:")
        print(picks_df[sample_cols].head(10).to_string(index=False))
        
        # Generate summary by bet type
        generate_bet_type_summary(picks_df)
        
        return picks_df
        
    except Exception as e:
        print(f"❌ Error creating enhanced report: {e}")
        return None

def parse_team_names(match_string):
    """Parse team names from match string"""
    try:
        if " vs " in match_string:
            home_team, away_team = match_string.split(" vs ", 1)
            return home_team.strip(), away_team.strip()
        else:
            # Fallback for other formats
            return match_string, "Unknown"
    except:
        return "Team A", "Team B"

def get_bet_description(market):
    """Convert market code to human-readable description"""
    descriptions = {
        # Match Result
        'Home': 'Home Team Win',
        'Draw': 'Match Draw',
        'Away': 'Away Team Win',
        
        # Goals Totals
        'Over 1.5': 'Over 1.5 Goals in Match',
        'Under 1.5': 'Under 1.5 Goals in Match',
        'Over 2.5': 'Over 2.5 Goals in Match',
        'Under 2.5': 'Under 2.5 Goals in Match',
        'Over 3.5': 'Over 3.5 Goals in Match',
        'Under 3.5': 'Under 3.5 Goals in Match',
        
        # Both Teams to Score
        'BTTS Yes': 'Both Teams to Score - Yes',
        'BTTS No': 'Both Teams to Score - No',
        
        # Team Totals
        'Home Over 1.5': 'Home Team Over 1.5 Goals',
        'Home Under 1.5': 'Home Team Under 1.5 Goals',
        'Away Over 1.5': 'Away Team Over 1.5 Goals',  
        'Away Under 1.5': 'Away Team Under 1.5 Goals',
        
        # Double Chance
        'Home/Draw': 'Home Win or Draw',
        'Home/Away': 'Home Win or Away Win (No Draw)',
        'Draw/Away': 'Draw or Away Win',
        
        # Corners
        'Over 9.5 Corners': 'Over 9.5 Total Corners',
        'Under 9.5 Corners': 'Under 9.5 Total Corners',
        'Over 11.5 Corners': 'Over 11.5 Total Corners',
        'Under 11.5 Corners': 'Under 11.5 Total Corners',
        
        # Asian Handicap
        'Home -1': 'Home Team -1 Goal Handicap',
        'Home +1': 'Home Team +1 Goal Handicap',
        'Away -1': 'Away Team -1 Goal Handicap',
        'Away +1': 'Away Team +1 Goal Handicap',
    }
    
    return descriptions.get(market, market)

def classify_market_category(market):
    """Classify market into main categories"""
    if market in ['Home', 'Draw', 'Away']:
        return 'Match Winner'
    elif any(x in market for x in ['Over', 'Under']) and 'Corner' not in market:
        if any(x in market for x in ['Home', 'Away']) and any(y in market for y in ['1.5']):
            return 'Team Goals'
        else:
            return 'Total Goals'
    elif 'BTTS' in market:
        return 'Both Teams to Score'
    elif '/' in market:
        return 'Double Chance'
    elif 'Corner' in market:
        return 'Corners'
    elif any(x in market for x in ['+', '-']):
        return 'Asian Handicap'
    else:
        return 'Other'

def get_risk_level(odds):
    """Classify risk based on odds"""
    if odds <= 1.5:
        return 'Low Risk'
    elif odds <= 2.5:
        return 'Medium Risk'
    else:
        return 'High Risk'

def generate_bet_type_summary(picks_df):
    """Generate summary by bet type"""
    
    print(f"\n📊 PERFORMANCE BY BET TYPE")
    print("=" * 80)
    
    # Summary by bet description
    bet_summary = picks_df.groupby('bet_description').agg({
        'result': lambda x: (x == 'WIN').sum(),
        'bet_description': 'count',
        'profit_loss': 'sum',
        'stake': 'sum'
    }).rename(columns={'bet_description': 'total_bets', 'result': 'wins'})
    
    bet_summary['win_rate'] = (bet_summary['wins'] / bet_summary['total_bets']) * 100
    bet_summary['roi'] = (bet_summary['profit_loss'] / bet_summary['stake']) * 100
    
    # Sort by total profit
    bet_summary = bet_summary.sort_values('profit_loss', ascending=False)
    
    print(f"{'Bet Type':<35} {'Bets':<5} {'Wins':<5} {'Win%':<6} {'Profit':<10} {'ROI%':<6}")
    print("-" * 80)
    
    for bet_type, stats in bet_summary.head(20).iterrows():
        print(f"{bet_type[:34]:<35} {stats['total_bets']:>4} {stats['wins']:>4} {stats['win_rate']:>5.1f}% ${stats['profit_loss']:>8.0f} {stats['roi']:>5.1f}%")
    
    # Summary by market category
    print(f"\n📈 PERFORMANCE BY MARKET CATEGORY")
    print("=" * 60)
    
    category_summary = picks_df.groupby('market_category').agg({
        'result': lambda x: (x == 'WIN').sum(),
        'market_category': 'count',
        'profit_loss': 'sum',
        'stake': 'sum'
    }).rename(columns={'market_category': 'total_bets', 'result': 'wins'})
    
    category_summary['win_rate'] = (category_summary['wins'] / category_summary['total_bets']) * 100
    category_summary['roi'] = (category_summary['profit_loss'] / category_summary['stake']) * 100
    category_summary = category_summary.sort_values('profit_loss', ascending=False)
    
    for category, stats in category_summary.iterrows():
        print(f"{category:<20} {stats['total_bets']:>3} bets, {stats['win_rate']:>5.1f}% WR, ${stats['profit_loss']:>8.0f} profit, {stats['roi']:>5.1f}% ROI")

def main():
    """Generate enhanced daily picks report"""
    print("🎯 Generating Enhanced Daily Picks Report")
    print("=" * 50)
    
    picks_df = create_enhanced_picks_report()
    
    if picks_df is not None:
        print(f"\n✅ Enhanced Report Generated Successfully!")
        print(f"📁 File: enhanced_daily_picks_report.csv")
        print(f"📊 Contains {len(picks_df)} individual bets")

if __name__ == "__main__":
    main()