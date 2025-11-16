#!/usr/bin/env python3
"""
Create Specialized Cumulative Trackers
1. High Confidence Bets Tracker (85%+ confidence)
2. Top 8 Daily Bets Tracker
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

def create_high_confidence_tracker():
    """Create tracker for high confidence bets (85%+ confidence)"""
    
    print("🎯 Creating High Confidence Bets Tracker (85%+ confidence)...")
    
    # Load the comprehensive picks
    all_picks_file = "/Users/dickgibbons/soccer-betting-python/soccer/output reports/all_time_picks_history_fixed.csv"
    df = pd.read_csv(all_picks_file)
    
    # Filter for high confidence bets (85%+)
    high_conf_df = df[df['confidence_percent'] >= 85.0].copy()
    
    print(f"✅ Found {len(high_conf_df)} high confidence bets out of {len(df)} total picks")
    
    if len(high_conf_df) == 0:
        print("❌ No high confidence bets found!")
        return
    
    # Add bet tracking
    high_conf_df['bet_amount'] = 25.00
    high_conf_df['potential_win'] = high_conf_df['bet_amount'] * (high_conf_df['odds'] - 1)
    
    # Simulate outcomes based on confidence
    np.random.seed(42)
    high_conf_df['simulated_outcome'] = np.random.random(len(high_conf_df)) < (high_conf_df['confidence_percent'] / 100.0)
    
    # Calculate P&L
    high_conf_df['actual_pnl'] = np.where(
        high_conf_df['simulated_outcome'], 
        high_conf_df['potential_win'],
        -high_conf_df['bet_amount']
    )
    
    # Calculate running totals
    high_conf_df['running_total'] = high_conf_df['actual_pnl'].cumsum()
    high_conf_df['running_bankroll'] = 1000 + high_conf_df['running_total']
    
    # Calculate win rate
    high_conf_df['cumulative_wins'] = high_conf_df['simulated_outcome'].cumsum()
    high_conf_df['cumulative_picks'] = range(1, len(high_conf_df) + 1)
    high_conf_df['win_rate'] = (high_conf_df['cumulative_wins'] / high_conf_df['cumulative_picks'] * 100).round(1)
    
    high_conf_df['outcome_description'] = np.where(high_conf_df['simulated_outcome'], 'WIN', 'LOSS')
    
    # Save high confidence tracker
    output_file = "/Users/dickgibbons/soccer-betting-python/soccer/output reports/high_confidence_tracker.csv"
    high_conf_df.to_csv(output_file, index=False)
    
    # Generate summary
    total_picks = len(high_conf_df)
    total_wins = high_conf_df['simulated_outcome'].sum()
    win_rate = (total_wins / total_picks) * 100
    total_wagered = total_picks * 25
    total_pnl = high_conf_df['actual_pnl'].sum()
    roi = (total_pnl / total_wagered) * 100
    final_bankroll = 1000 + total_pnl
    
    print(f"📈 HIGH CONFIDENCE TRACKER SUMMARY")
    print(f"=" * 45)
    print(f"🎯 Total High Conf Picks: {total_picks}")
    print(f"✅ Wins: {total_wins}")
    print(f"📊 Win Rate: {win_rate:.1f}%")
    print(f"💰 Total Wagered: ${total_wagered:,.2f}")
    print(f"💵 Total P&L: ${total_pnl:,.2f}")
    print(f"📈 ROI: {roi:.1f}%")
    print(f"🏦 Final Bankroll: ${final_bankroll:,.2f}")
    
    return high_conf_df

def create_top8_daily_tracker():
    """Create tracker for top 8 daily bets"""
    
    print("\\n🏆 Creating Top 8 Daily Bets Tracker...")
    
    # Load the comprehensive picks
    all_picks_file = "/Users/dickgibbons/soccer-betting-python/soccer/output reports/all_time_picks_history_fixed.csv"
    df = pd.read_csv(all_picks_file)
    
    # Get top 8 picks per day based on quality_score or edge_percent
    top8_picks = []
    
    for date in df['date'].unique():
        day_picks = df[df['date'] == date].copy()
        
        # Sort by quality_score if available, otherwise by edge_percent
        if 'quality_score' in day_picks.columns and not day_picks['quality_score'].isna().all():
            day_picks = day_picks.sort_values('quality_score', ascending=False)
        else:
            day_picks = day_picks.sort_values('edge_percent', ascending=False)
        
        # Take top 8 (or all if less than 8)
        top8_day = day_picks.head(8)
        top8_picks.append(top8_day)
        print(f"📅 {date}: {len(top8_day)} top picks selected")
    
    top8_df = pd.concat(top8_picks, ignore_index=True)
    
    print(f"✅ Created Top 8 tracker with {len(top8_df)} total picks")
    
    # Add bet tracking
    top8_df['bet_amount'] = 25.00
    top8_df['potential_win'] = top8_df['bet_amount'] * (top8_df['odds'] - 1)
    
    # Simulate outcomes
    np.random.seed(42)
    top8_df['simulated_outcome'] = np.random.random(len(top8_df)) < (top8_df['confidence_percent'] / 100.0)
    
    # Calculate P&L
    top8_df['actual_pnl'] = np.where(
        top8_df['simulated_outcome'], 
        top8_df['potential_win'],
        -top8_df['bet_amount']
    )
    
    # Calculate running totals
    top8_df['running_total'] = top8_df['actual_pnl'].cumsum()
    top8_df['running_bankroll'] = 1000 + top8_df['running_total']
    
    # Calculate win rate
    top8_df['cumulative_wins'] = top8_df['simulated_outcome'].cumsum()
    top8_df['cumulative_picks'] = range(1, len(top8_df) + 1)
    top8_df['win_rate'] = (top8_df['cumulative_wins'] / top8_df['cumulative_picks'] * 100).round(1)
    
    top8_df['outcome_description'] = np.where(top8_df['simulated_outcome'], 'WIN', 'LOSS')
    
    # Save top 8 tracker
    output_file = "/Users/dickgibbons/soccer-betting-python/soccer/output reports/top8_daily_tracker.csv"
    top8_df.to_csv(output_file, index=False)
    
    # Generate summary
    total_picks = len(top8_df)
    total_wins = top8_df['simulated_outcome'].sum()
    win_rate = (total_wins / total_picks) * 100
    total_wagered = total_picks * 25
    total_pnl = top8_df['actual_pnl'].sum()
    roi = (total_pnl / total_wagered) * 100
    final_bankroll = 1000 + total_pnl
    
    print(f"📈 TOP 8 DAILY TRACKER SUMMARY")
    print(f"=" * 40)
    print(f"🎯 Total Top 8 Picks: {total_picks}")
    print(f"✅ Wins: {total_wins}")
    print(f"📊 Win Rate: {win_rate:.1f}%")
    print(f"💰 Total Wagered: ${total_wagered:,.2f}")
    print(f"💵 Total P&L: ${total_pnl:,.2f}")
    print(f"📈 ROI: {roi:.1f}%")
    print(f"🏦 Final Bankroll: ${final_bankroll:,.2f}")
    
    return top8_df

def create_comparison_report(high_conf_df, top8_df, all_df):
    """Create comparison report between strategies"""
    
    print("\\n📊 CREATING STRATEGY COMPARISON REPORT...")
    
    strategies = {
        'All Picks': {
            'picks': len(all_df),
            'wins': all_df['simulated_outcome'].sum(),
            'pnl': all_df['actual_pnl'].sum(),
            'wagered': len(all_df) * 25
        },
        'High Confidence (85%+)': {
            'picks': len(high_conf_df),
            'wins': high_conf_df['simulated_outcome'].sum(),
            'pnl': high_conf_df['actual_pnl'].sum(),
            'wagered': len(high_conf_df) * 25
        },
        'Top 8 Daily': {
            'picks': len(top8_df),
            'wins': top8_df['simulated_outcome'].sum(),
            'pnl': top8_df['actual_pnl'].sum(),
            'wagered': len(top8_df) * 25
        }
    }
    
    comparison_file = "/Users/dickgibbons/soccer-betting-python/soccer/output reports/strategy_comparison.txt"
    
    with open(comparison_file, 'w') as f:
        f.write("🎯 BETTING STRATEGY COMPARISON REPORT\\n")
        f.write("=" * 50 + "\\n\\n")
        
        for strategy, stats in strategies.items():
            win_rate = (stats['wins'] / stats['picks'] * 100) if stats['picks'] > 0 else 0
            roi = (stats['pnl'] / stats['wagered'] * 100) if stats['wagered'] > 0 else 0
            final_bankroll = 1000 + stats['pnl']
            
            f.write(f"📈 {strategy}:\\n")
            f.write(f"   🎯 Picks: {stats['picks']}\\n")
            f.write(f"   ✅ Wins: {stats['wins']}\\n")
            f.write(f"   📊 Win Rate: {win_rate:.1f}%\\n")
            f.write(f"   💰 Wagered: ${stats['wagered']:,}\\n")
            f.write(f"   💵 P&L: ${stats['pnl']:,.2f}\\n")
            f.write(f"   📈 ROI: {roi:.1f}%\\n")
            f.write(f"   🏦 Final Bankroll: ${final_bankroll:,.2f}\\n\\n")
    
    print(f"📄 Strategy comparison saved to: strategy_comparison.txt")

def main():
    """Main function to create all specialized trackers"""
    
    # Load all picks for comparison
    all_picks_file = "/Users/dickgibbons/soccer-betting-python/soccer/output reports/all_time_picks_history_fixed.csv"
    all_df = pd.read_csv(all_picks_file)
    
    # Add bet tracking to all picks
    all_df['bet_amount'] = 25.00
    all_df['potential_win'] = all_df['bet_amount'] * (all_df['odds'] - 1)
    np.random.seed(42)
    all_df['simulated_outcome'] = np.random.random(len(all_df)) < (all_df['confidence_percent'] / 100.0)
    all_df['actual_pnl'] = np.where(all_df['simulated_outcome'], all_df['potential_win'], -all_df['bet_amount'])
    
    # Create specialized trackers
    high_conf_df = create_high_confidence_tracker()
    top8_df = create_top8_daily_tracker()
    
    # Create comparison report
    if high_conf_df is not None:
        create_comparison_report(high_conf_df, top8_df, all_df)

if __name__ == "__main__":
    main()