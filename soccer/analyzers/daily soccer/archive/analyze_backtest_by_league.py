#!/usr/bin/env python3
"""
Analyze Soccer Backtest Results by League
Identify which leagues perform well and which perform poorly
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Load the detailed backtest results from FootyStats
backtest_file = Path('footystats_backtest_detailed.csv')

if not backtest_file.exists():
    print("❌ Backtest file not found. Looking for alternative...")
    # Try to find any CSV with backtest data
    import glob
    csv_files = glob.glob('*backtest*.csv')
    if csv_files:
        print(f"Found: {csv_files}")
        backtest_file = csv_files[0]
    else:
        print("No backtest files found. Exiting.")
        exit(1)

print(f"📊 Loading backtest data from {backtest_file}...\n")
df = pd.read_csv(backtest_file)

print(f"Total bets: {len(df)}")
print(f"Date range: {df['match_date'].min() if 'match_date' in df.columns else 'N/A'} to {df['match_date'].max() if 'match_date' in df.columns else 'N/A'}\n")

# Identify league column name (might be 'league', 'league_name', 'competition', etc.)
league_col = None
for col in ['league', 'league_name', 'competition', 'Competition']:
    if col in df.columns:
        league_col = col
        break

if not league_col:
    print("❌ Could not find league column in data")
    print(f"Available columns: {list(df.columns)}")
    exit(1)

print(f"Using league column: '{league_col}'\n")

# Identify bet type column
bet_type_col = None
for col in ['market', 'bet_type', 'Market', 'selection']:
    if col in df.columns:
        bet_type_col = col
        break

# Identify result column
result_col = None
for col in ['correct', 'won', 'result', 'win']:
    if col in df.columns:
        result_col = col
        break

# Identify profit column
profit_col = None
for col in ['profit', 'pnl', 'profit_loss', 'return']:
    if col in df.columns:
        profit_col = col
        break

print(f"Bet type column: '{bet_type_col}'")
print(f"Result column: '{result_col}'")
print(f"Profit column: '{profit_col}'\n")

# Group by league
print("="*80)
print("📊 PERFORMANCE BY LEAGUE")
print("="*80)

league_stats = df.groupby(league_col).agg({
    result_col: ['count', 'sum', 'mean'] if result_col else 'count',
    profit_col: 'sum' if profit_col else None
}).round(3)

# Remove None aggregations
league_stats = league_stats.dropna(axis=1, how='all')

# Sort by profit if available, otherwise by count
if profit_col:
    league_stats_sorted = league_stats.sort_values((profit_col, 'sum'), ascending=False)
else:
    league_stats_sorted = league_stats.sort_values((result_col, 'count'), ascending=False)

print(f"\n{'League':<30} {'Bets':<8} {'Wins':<8} {'WR%':<8} {'Profit':<12} {'Status'}")
print("-"*85)

profitable_leagues = []
unprofitable_leagues = []

for league in league_stats_sorted.index:
    count = league_stats_sorted.loc[league, (result_col, 'count')]

    if result_col:
        wins = league_stats_sorted.loc[league, (result_col, 'sum')]
        win_rate = league_stats_sorted.loc[league, (result_col, 'mean')]
    else:
        wins = 0
        win_rate = 0

    if profit_col:
        profit = league_stats_sorted.loc[league, (profit_col, 'sum')]
    else:
        profit = 0

    # Determine status
    if profit > 10:
        status = "✅ PROFITABLE"
        profitable_leagues.append(league)
    elif profit < -10:
        status = "❌ LOSING"
        unprofitable_leagues.append(league)
    else:
        status = "⚪ NEUTRAL"

    print(f"{league:<30} {int(count):<8} {int(wins):<8} {win_rate*100:>6.1f}% ${profit:>10.2f} {status}")

# Summary
print("\n" + "="*80)
print("📈 LEAGUE FILTERING RECOMMENDATIONS")
print("="*80)

print(f"\n✅ PROFITABLE LEAGUES ({len(profitable_leagues)}) - WHITELIST:")
for league in profitable_leagues[:10]:  # Top 10
    stats = league_stats_sorted.loc[league]
    count = stats[(result_col, 'count')]
    wr = stats[(result_col, 'mean')] * 100 if result_col else 0
    profit = stats[(profit_col, 'sum')] if profit_col else 0
    print(f"  • {league:<30} ({int(count)} bets, {wr:.1f}% WR, ${profit:>8.2f})")

print(f"\n❌ LOSING LEAGUES ({len(unprofitable_leagues)}) - BLACKLIST:")
for league in unprofitable_leagues[:10]:  # Worst 10
    stats = league_stats_sorted.loc[league]
    count = stats[(result_col, 'count')]
    wr = stats[(result_col, 'mean')] * 100 if result_col else 0
    profit = stats[(profit_col, 'sum')] if profit_col else 0
    print(f"  • {league:<30} ({int(count)} bets, {wr:.1f}% WR, ${profit:>8.2f})")

# Analyze by bet type and league
if bet_type_col:
    print("\n" + "="*80)
    print("📊 PERFORMANCE BY BET TYPE AND LEAGUE")
    print("="*80)

    # Focus on match winners (most problematic)
    match_winner_bets = df[df[bet_type_col].str.contains('Win|Home|Away|Draw', case=False, na=False)]

    if len(match_winner_bets) > 0:
        print(f"\n🎯 MATCH WINNER BETS BY LEAGUE ({len(match_winner_bets)} total):")
        print("-"*85)

        mw_stats = match_winner_bets.groupby(league_col).agg({
            result_col: ['count', 'sum', 'mean'] if result_col else 'count',
            profit_col: 'sum' if profit_col else None
        }).round(3)

        mw_stats = mw_stats.dropna(axis=1, how='all')

        if profit_col:
            mw_stats_sorted = mw_stats.sort_values((profit_col, 'sum'), ascending=False)
        else:
            mw_stats_sorted = mw_stats.sort_values((result_col, 'count'), ascending=False)

        print(f"{'League':<30} {'Bets':<8} {'Wins':<8} {'WR%':<8} {'Profit':<12}")
        print("-"*85)

        for league in mw_stats_sorted.index[:15]:  # Top 15
            count = mw_stats_sorted.loc[league, (result_col, 'count')]
            wins = mw_stats_sorted.loc[league, (result_col, 'sum')] if result_col else 0
            win_rate = mw_stats_sorted.loc[league, (result_col, 'mean')] if result_col else 0
            profit = mw_stats_sorted.loc[league, (profit_col, 'sum')] if profit_col else 0

            print(f"{league:<30} {int(count):<8} {int(wins):<8} {win_rate*100:>6.1f}% ${profit:>10.2f}")

# Generate Python code for league whitelist/blacklist
print("\n" + "="*80)
print("💻 PYTHON CODE FOR LEAGUE FILTERING")
print("="*80)

print("\n# Add to soccer_best_bets_daily.py:")
print("\n# Profitable leagues (whitelist)")
print("PROFITABLE_LEAGUES = [")
for league in profitable_leagues[:15]:
    print(f"    '{league}',")
print("]")

print("\n# Losing leagues (blacklist)")
print("LOSING_LEAGUES = [")
for league in unprofitable_leagues[:15]:
    print(f"    '{league}',")
print("]")

print("\n# In predict_match() function, add this filter:")
print("""
# League filtering
league_name = match.get('league_name', '')
if league_name in LOSING_LEAGUES:
    return None  # Skip this match
""")

print("\n✅ Analysis complete!")
