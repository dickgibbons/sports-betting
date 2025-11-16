#!/usr/bin/env python3
"""
Generate comprehensive daily picks report from multi-market backtest results
"""

import pandas as pd
import numpy as np
from datetime import datetime
import csv

def create_comprehensive_picks_report():
    """Create a detailed daily picks report with enhanced formatting"""
    
    # Load the detailed backtest results
    detailed_file = "./output reports/Older/comprehensive_backtest_aug01_sep09.csv"
    summary_file = "./output reports/Older/improved_backtest_summary_20250904_202853.csv"
    
    try:
        # Read detailed results
        detailed_df = pd.read_csv(detailed_file)
        summary_df = pd.read_csv(summary_file)
        
        print(f"📊 Processing {len(detailed_df)} individual bets from {len(summary_df)} trading days")
        
        # Create enhanced picks report
        enhanced_picks = []
        
        # Group by date for daily summary
        daily_groups = detailed_df.groupby('date')
        
        for date, daily_bets in daily_groups:
            # Get daily summary stats
            daily_summary = summary_df[summary_df['date'] == date].iloc[0] if len(summary_df[summary_df['date'] == date]) > 0 else None
            
            daily_profit = daily_bets['profit_loss'].sum()
            daily_stakes = daily_bets['stake'].sum()
            wins = len(daily_bets[daily_bets['bet_won'] == True])
            total_bets = len(daily_bets)
            win_rate = (wins / total_bets * 100) if total_bets > 0 else 0
            
            # Process each bet
            for idx, bet in daily_bets.iterrows():
                enhanced_pick = {
                    # Date and Match Info
                    'date': bet['date'],
                    'day_of_week': pd.to_datetime(bet['date']).strftime('%A'),
                    'match': bet['match'],
                    'league': bet['league'],
                    
                    # Bet Details
                    'market': bet['market'],
                    'odds': round(bet['odds'], 2),
                    'stake': round(bet['stake'], 2),
                    'stake_pct_bankroll': round((bet['stake'] / bet['bankroll_before']) * 100, 1),
                    
                    # Prediction Confidence
                    'edge': round(bet['edge'] * 100, 1),  # Convert to percentage
                    'confidence': round(bet['confidence'] * 100, 1),  # Convert to percentage
                    
                    # Results
                    'result': 'WIN' if bet['bet_won'] else 'LOSS',
                    'profit_loss': round(bet['profit_loss'], 2),
                    'roi_bet': round((bet['profit_loss'] / bet['stake']) * 100, 1) if bet['stake'] > 0 else 0,
                    
                    # Bankroll Tracking
                    'bankroll_before': round(bet['bankroll_before'], 2),
                    'bankroll_after': round(bet['bankroll_after'], 2),
                    
                    # Daily Context
                    'daily_bet_number': list(daily_bets.index).index(idx) + 1,
                    'daily_total_bets': total_bets,
                    'daily_profit_loss': round(daily_profit, 2),
                    'daily_win_rate': round(win_rate, 1),
                    'daily_roi': round((daily_profit / daily_stakes * 100), 1) if daily_stakes > 0 else 0,
                    
                    # Market Classification
                    'market_type': classify_market(bet['market']),
                    'risk_level': classify_risk_level(bet['odds'], bet['edge']),
                    
                    # Performance Metrics
                    'running_total_return': round(((bet['bankroll_after'] - 300) / 300) * 100, 1),  # % return from start
                    'peak_bankroll': round(max(detailed_df[detailed_df.index <= idx]['bankroll_after']), 2),
                    'drawdown_from_peak': round(((round(max(detailed_df[detailed_df.index <= idx]['bankroll_after']), 2) - bet['bankroll_after']) / round(max(detailed_df[detailed_df.index <= idx]['bankroll_after']), 2)) * 100, 1)
                }
                
                enhanced_picks.append(enhanced_pick)
        
        # Create DataFrame
        picks_df = pd.DataFrame(enhanced_picks)
        
        # Add some calculated fields
        picks_df['cumulative_profit'] = picks_df['profit_loss'].cumsum()
        picks_df['bet_sequence'] = range(1, len(picks_df) + 1)
        
        # Save to CSV
        output_file = "./comprehensive_daily_picks_report.csv"
        picks_df.to_csv(output_file, index=False)
        
        print(f"✅ Comprehensive picks report saved: comprehensive_daily_picks_report.csv")
        
        # Generate summary statistics
        generate_summary_stats(picks_df)
        
        return picks_df
        
    except Exception as e:
        print(f"❌ Error creating picks report: {e}")
        return None

def classify_market(market):
    """Classify betting market type"""
    if market in ['Home', 'Draw', 'Away']:
        return 'Match_Result'
    elif 'Over' in market or 'Under' in market:
        if 'Corner' in market:
            return 'Corners'
        elif any(x in market for x in ['1.5', '2.5', '3.5']):
            return 'Goals_Total'
        else:
            return 'Team_Total'
    elif 'BTTS' in market:
        return 'BTTS'
    elif '/' in market:
        return 'Double_Chance'
    elif '+' in market or '-' in market:
        return 'Asian_Handicap'
    else:
        return 'Other'

def classify_risk_level(odds, edge):
    """Classify risk level based on odds and edge"""
    if odds <= 1.5:
        return 'Low_Risk'
    elif odds <= 2.5:
        if edge > 0.1:  # 10%+ edge
            return 'Medium_Risk'
        else:
            return 'High_Risk'
    else:
        if edge > 0.15:  # 15%+ edge on higher odds
            return 'Medium_Risk'
        else:
            return 'High_Risk'

def generate_summary_stats(picks_df):
    """Generate and save summary statistics"""
    
    print(f"\n📊 COMPREHENSIVE PICKS REPORT SUMMARY")
    print("=" * 60)
    
    # Overall Performance
    total_bets = len(picks_df)
    total_wins = len(picks_df[picks_df['result'] == 'WIN'])
    overall_win_rate = (total_wins / total_bets) * 100
    
    total_profit = picks_df['profit_loss'].sum()
    total_stakes = picks_df['stake'].sum()
    overall_roi = (total_profit / total_stakes) * 100
    
    initial_bankroll = 300.0
    final_bankroll = picks_df['bankroll_after'].iloc[-1]
    total_return = ((final_bankroll - initial_bankroll) / initial_bankroll) * 100
    
    print(f"🎯 Overall Performance:")
    print(f"   Total Bets: {total_bets:,}")
    print(f"   Wins: {total_wins:,} ({overall_win_rate:.1f}%)")
    print(f"   Total Profit: ${total_profit:,.2f}")
    print(f"   Total Return: {total_return:+.1f}%")
    print(f"   ROI: {overall_roi:+.1f}%")
    
    # Market Performance
    print(f"\n🏆 Performance by Market Type:")
    market_performance = picks_df.groupby('market_type').agg({
        'result': lambda x: (x == 'WIN').sum(),
        'market_type': 'count',
        'profit_loss': 'sum',
        'stake': 'sum'
    }).rename(columns={'market_type': 'total_bets', 'result': 'wins'})
    
    market_performance['win_rate'] = (market_performance['wins'] / market_performance['total_bets']) * 100
    market_performance['roi'] = (market_performance['profit_loss'] / market_performance['stake']) * 100
    
    for market, stats in market_performance.iterrows():
        print(f"   {market:<15} {stats['total_bets']:>3} bets, {stats['win_rate']:>5.1f}% WR, {stats['roi']:>+6.1f}% ROI, ${stats['profit_loss']:>+8.2f}")
    
    # Monthly Performance
    print(f"\n📅 Monthly Performance:")
    picks_df['month'] = pd.to_datetime(picks_df['date']).dt.to_period('M')
    monthly_performance = picks_df.groupby('month').agg({
        'profit_loss': 'sum',
        'stake': 'sum',
        'result': lambda x: (x == 'WIN').sum(),
        'date': 'count'
    }).rename(columns={'date': 'total_bets', 'result': 'wins'})
    
    monthly_performance['win_rate'] = (monthly_performance['wins'] / monthly_performance['total_bets']) * 100
    monthly_performance['roi'] = (monthly_performance['profit_loss'] / monthly_performance['stake']) * 100
    
    for month, stats in monthly_performance.iterrows():
        print(f"   {str(month):<8} ${stats['profit_loss']:>+8.2f} ({stats['roi']:>+5.1f}% ROI), {stats['wins']:>3}/{stats['total_bets']:>3} wins ({stats['win_rate']:>5.1f}%)")
    
    # Best and Worst Bets
    print(f"\n🌟 Best Performing Bets:")
    best_bets = picks_df.nlargest(5, 'profit_loss')[['date', 'match', 'market', 'odds', 'stake', 'profit_loss']]
    for idx, bet in best_bets.iterrows():
        print(f"   {bet['date']} {bet['market']} @ {bet['odds']:.2f} - ${bet['profit_loss']:+.2f}")
    
    print(f"\n💸 Worst Performing Bets:")
    worst_bets = picks_df.nsmallest(5, 'profit_loss')[['date', 'match', 'market', 'odds', 'stake', 'profit_loss']]
    for idx, bet in worst_bets.iterrows():
        print(f"   {bet['date']} {bet['market']} @ {bet['odds']:.2f} - ${bet['profit_loss']:+.2f}")
    
    # Save detailed summary
    summary_stats = {
        'overall': {
            'total_bets': int(total_bets),
            'wins': int(total_wins),
            'win_rate': round(overall_win_rate, 2),
            'total_profit': round(total_profit, 2),
            'total_return': round(total_return, 2),
            'roi': round(overall_roi, 2)
        },
        'by_market': market_performance.round(2).to_dict('index'),
        'monthly': monthly_performance.round(2).to_dict('index')
    }
    
    import json
    with open("./picks_summary_stats.json", 'w') as f:
        json.dump(summary_stats, f, indent=2, default=str)
    
    print(f"\n💾 Summary statistics saved: picks_summary_stats.json")

def main():
    """Generate comprehensive daily picks report"""
    print("🎯 Generating Comprehensive Daily Picks Report")
    print("=" * 50)
    
    picks_df = create_comprehensive_picks_report()
    
    if picks_df is not None:
        print(f"\n✅ Report Generation Complete!")
        print(f"📁 Files created:")
        print(f"   • comprehensive_daily_picks_report.csv")
        print(f"   • picks_summary_stats.json")
        
        # Show sample of the data
        print(f"\n📋 Sample of generated report (first 5 rows):")
        sample_cols = ['date', 'match', 'market', 'odds', 'stake', 'result', 'profit_loss', 'bankroll_after']
        print(picks_df[sample_cols].head().to_string(index=False))

if __name__ == "__main__":
    main()