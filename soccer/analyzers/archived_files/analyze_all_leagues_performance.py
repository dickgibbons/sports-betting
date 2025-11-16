#!/usr/bin/env python3

"""
Analyze All Leagues Performance from Backtest Data
==================================================
Determine which of the top 30 major leagues globally would be profitable to include
"""

import pandas as pd
import numpy as np

def analyze_all_leagues_performance():
    """Analyze performance of all leagues in backtest data"""
    
    print("🌍 ANALYZING ALL LEAGUES PERFORMANCE FROM BACKTEST DATA")
    print("="*60)
    
    # Read the comprehensive backtest data
    try:
        df = pd.read_csv('output reports/backtest_detailed_20240801_20250904.csv')
        print(f"📊 Loaded {len(df):,} betting records")
    except Exception as e:
        print(f"❌ Error loading backtest data: {e}")
        return
    
    print()
    
    # Analyze league performance
    league_stats = df.groupby('league').agg({
        'bet_won': ['count', 'sum'],  # Total bets, wins
        'profit_loss': 'sum',         # Total P&L
        'stake': 'sum',               # Total staked
        'edge': 'mean',               # Average edge
        'confidence': 'mean'          # Average confidence
    }).round(3)
    
    # Calculate derived metrics
    league_analysis = []
    
    for league in league_stats.index:
        total_bets = league_stats.loc[league, ('bet_won', 'count')]
        wins = league_stats.loc[league, ('bet_won', 'sum')]
        profit = league_stats.loc[league, ('profit_loss', 'sum')]
        stake = league_stats.loc[league, ('stake', 'sum')]
        avg_edge = league_stats.loc[league, ('edge', 'mean')]
        avg_confidence = league_stats.loc[league, ('confidence', 'mean')]
        
        win_rate = (wins / total_bets * 100) if total_bets > 0 else 0
        roi = (profit / stake * 100) if stake > 0 else 0
        avg_profit_per_bet = profit / total_bets if total_bets > 0 else 0
        
        league_analysis.append({
            'league': league,
            'total_bets': int(total_bets),
            'win_rate': win_rate,
            'roi': roi,
            'total_profit': profit,
            'avg_profit_per_bet': avg_profit_per_bet,
            'avg_edge': avg_edge,
            'avg_confidence': avg_confidence
        })
    
    # Convert to DataFrame for easy sorting
    analysis_df = pd.DataFrame(league_analysis)
    
    print("🏆 TOP PERFORMING LEAGUES (by ROI):")
    print("-" * 40)
    top_performers = analysis_df.sort_values('roi', ascending=False).head(15)
    
    for i, row in top_performers.iterrows():
        print(f"{row['league']:25} | {row['total_bets']:3d} bets | {row['win_rate']:5.1f}% WR | {row['roi']:+7.1f}% ROI | ${row['total_profit']:+8.2f}")
    
    print()
    print("💸 WORST PERFORMING LEAGUES (by ROI):")
    print("-" * 40)
    worst_performers = analysis_df.sort_values('roi', ascending=True).head(10)
    
    for i, row in worst_performers.iterrows():
        print(f"{row['league']:25} | {row['total_bets']:3d} bets | {row['win_rate']:5.1f}% WR | {row['roi']:+7.1f}% ROI | ${row['total_profit']:+8.2f}")
    
    print()
    print("📊 VOLUME LEADERS (by total bets):")
    print("-" * 40)
    volume_leaders = analysis_df.sort_values('total_bets', ascending=False).head(10)
    
    for i, row in volume_leaders.iterrows():
        print(f"{row['league']:25} | {row['total_bets']:3d} bets | {row['win_rate']:5.1f}% WR | {row['roi']:+7.1f}% ROI | ${row['total_profit']:+8.2f}")
    
    print()
    
    # Identify top 30 major leagues criteria
    print("🌟 TOP 30 MAJOR LEAGUES RECOMMENDATION:")
    print("-" * 50)
    
    # Filter criteria:
    # 1. Minimum volume (at least 5 bets in dataset)
    # 2. Reasonable performance (ROI > -50% to exclude disasters)
    # 3. Global significance
    
    qualified_leagues = analysis_df[
        (analysis_df['total_bets'] >= 3) &  # Minimum volume
        (analysis_df['roi'] > -50)          # Not disasters
    ].sort_values('roi', ascending=False)
    
    print("✅ QUALIFIED LEAGUES FOR EXPANSION:")
    profitable_count = 0
    breakeven_count = 0
    minor_loss_count = 0
    
    for i, row in qualified_leagues.iterrows():
        status = "🟢 PROFITABLE" if row['roi'] > 0 else ("🟡 BREAKEVEN" if row['roi'] > -10 else "🔴 LOSING")
        print(f"{row['league']:25} | {row['total_bets']:3d} bets | {row['roi']:+6.1f}% ROI | {status}")
        
        if row['roi'] > 0:
            profitable_count += 1
        elif row['roi'] > -10:
            breakeven_count += 1
        else:
            minor_loss_count += 1
    
    print()
    print("📈 EXPANSION IMPACT ANALYSIS:")
    print("-" * 35)
    print(f"🟢 Profitable leagues: {profitable_count}")
    print(f"🟡 Near-breakeven leagues: {breakeven_count}")
    print(f"🔴 Minor loss leagues: {minor_loss_count}")
    print(f"📊 Total qualified leagues: {len(qualified_leagues)}")
    
    # Calculate potential impact
    profitable_leagues = qualified_leagues[qualified_leagues['roi'] > 0]
    if len(profitable_leagues) > 0:
        avg_profitable_roi = profitable_leagues['roi'].mean()
        total_profitable_volume = profitable_leagues['total_bets'].sum()
        print(f"💰 Average ROI of profitable leagues: {avg_profitable_roi:+.1f}%")
        print(f"📊 Total volume from profitable leagues: {total_profitable_volume} bets")
    
    print()
    print("🎯 RECOMMENDATION:")
    if profitable_count >= 10:
        print("✅ EXPAND to top 30 major leagues - significant profitable opportunities found")
        print("🎯 Focus on implementing tiered strategy:")
        print("   • Tier 1 (High ROI): Full stakes")
        print("   • Tier 2 (Positive ROI): 75% stakes") 
        print("   • Tier 3 (Near breakeven): 50% stakes")
    elif profitable_count >= 5:
        print("🟡 SELECTIVE EXPANSION - expand to profitable leagues only")
        print("🎯 Add profitable leagues gradually with monitoring")
    else:
        print("🔴 MAINTAIN CURRENT FOCUS - insufficient profitable opportunities")
        print("🎯 Stick to current followed leagues until market conditions improve")
    
    return qualified_leagues

def create_top30_leagues_list(analysis_df):
    """Create a curated list of top 30 major global leagues"""
    
    # Major global leagues by region (based on FIFA rankings, attendance, TV deals, etc.)
    top30_major_leagues = [
        # Europe - Top Tier
        'Premier League',           # England
        'La Liga',                 # Spain  
        'Bundesliga',              # Germany
        'Serie A',                 # Italy
        'Ligue 1',                 # France
        'Eredivisie',              # Netherlands
        'Primeira Liga',           # Portugal
        'Belgian Pro League',      # Belgium
        'Swiss Super League',      # Switzerland
        'Austrian Bundesliga',     # Austria
        
        # Europe - Second Tier
        'Scottish Premiership',    # Scotland
        'Russian Premier League',  # Russia
        'Ukrainian Premier League', # Ukraine
        'Turkish Super Lig',       # Turkey
        'Greek Super League',      # Greece
        'Czech First League',      # Czech Republic
        'Polish Ekstraklasa',      # Poland
        'Norwegian Eliteserien',   # Norway
        'Swedish Allsvenskan',     # Sweden
        'Danish Superliga',        # Denmark
        
        # Americas
        'MLS',                     # USA/Canada
        'Liga MX',                 # Mexico
        'Brazilian Serie A',       # Brazil
        'Argentine Primera División', # Argentina
        'Chilean Primera División', # Chile
        'Colombian Primera A',     # Colombia
        
        # Asia/Others
        'J1 League',               # Japan
        'K League 1',              # South Korea
        'Chinese Super League',    # China
        'A-League'                 # Australia
    ]
    
    print("🌍 TOP 30 MAJOR GLOBAL LEAGUES:")
    print("=" * 40)
    
    for i, league in enumerate(top30_major_leagues, 1):
        # Check if we have data for this league
        league_data = analysis_df[analysis_df['league'] == league]
        if len(league_data) > 0:
            row = league_data.iloc[0]
            status = f"{row['total_bets']:3d} bets, {row['roi']:+5.1f}% ROI"
            recommendation = "✅" if row['roi'] > 0 else ("🟡" if row['roi'] > -10 else "🔴")
        else:
            status = "No data available"
            recommendation = "❓"
        
        print(f"{i:2d}. {league:25} | {status} {recommendation}")
    
    return top30_major_leagues

if __name__ == "__main__":
    qualified_leagues = analyze_all_leagues_performance()
    print("\n" + "="*60)
    create_top30_leagues_list(qualified_leagues)