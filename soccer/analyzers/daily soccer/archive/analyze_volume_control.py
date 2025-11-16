#!/usr/bin/env python3
"""
Analyze backtest results with volume control applied.
Simulates top-N selection by EV (weekday: 7 max, weekend: 15 max)
"""

import pandas as pd
from datetime import datetime

# Load detailed backtest results
df = pd.read_csv('backtest_2024_relaxed_detailed.csv')

print("=" * 80)
print("📊 VOLUME CONTROL SIMULATION")
print("=" * 80)
print(f"Original backtest: {len(df)} total bets")
print()

# Parse date and calculate expected value
df['date'] = pd.to_datetime(df['date'])
df['expected_value'] = (df['confidence'] * df['odds']) - 1

# Add day of week (0=Mon, 6=Sun)
df['day_of_week'] = df['date'].dt.dayofweek
df['is_weekend'] = df['day_of_week'] >= 4  # Friday=4, Sat=5, Sun=6

# Volume control constants
WEEKDAY_MAX = 7
WEEKEND_MAX = 15

# Apply volume control: group by date, take top N by EV
def apply_volume_control(group):
    """Apply volume control to a single day's bets"""
    is_weekend = group['is_weekend'].iloc[0]
    max_bets = WEEKEND_MAX if is_weekend else WEEKDAY_MAX

    # Filter: odds >= 1.50
    group = group[group['odds'] >= 1.50].copy()

    # Keep only best bet per match
    group['match_key'] = group['home_team'] + ' vs ' + group['away_team']
    group = group.sort_values('expected_value', ascending=False).groupby('match_key').first().reset_index(drop=True)

    # Take top N by EV
    return group.nlargest(max_bets, 'expected_value')

# Apply volume control to each day
filtered_df = df.groupby('date').apply(apply_volume_control).reset_index(drop=True)

print(f"After volume control: {len(filtered_df)} bets")
print()

# Infer market type from market column
def get_market_type(market):
    if 'BTTS' in market:
        return 'btts'
    elif 'Home Win' in market or 'Away Win' in market or 'Draw' in market:
        return 'match_winner'
    elif 'Over' in market or 'Under' in market:
        return 'totals'
    else:
        return 'other'

filtered_df['market_type'] = filtered_df['market'].apply(get_market_type)

# Calculate performance with PROPER sequential bankroll tracking
wins = filtered_df['correct'].sum()
losses = len(filtered_df) - wins
win_rate = (wins / len(filtered_df)) * 100

# Recalculate P&L sequentially (can't just sum profits from original backtest)
bankroll = 1000.0
total_pl = 0

for _, bet in filtered_df.iterrows():
    stake = bet['stake_pct'] * bankroll  # Use original Kelly % from backtest
    if bet['correct']:  # Win
        profit = stake * (bet['odds'] - 1)
    else:  # Loss
        profit = -stake

    total_pl += profit
    bankroll += profit

roi = (total_pl / 1000) * 100
final_bankroll = bankroll

print("=" * 80)
print("📈 VOLUME-CONTROLLED RESULTS")
print("=" * 80)
print(f"Total Bets: {len(filtered_df)}")
print(f"Wins: {wins} | Losses: {losses}")
print(f"Win Rate: {win_rate:.1f}%")
print(f"Total Profit: ${total_pl:.2f}")
print(f"ROI: {roi:.1f}%")
print(f"Initial Bankroll: $1,000.00")
print(f"Final Bankroll: ${final_bankroll:.2f}")
print(f"Bankroll Growth: {((final_bankroll - 1000) / 1000 * 100):.1f}%")
print()

# Performance by market
print("=" * 80)
print("📊 PERFORMANCE BY MARKET (Volume Controlled)")
print("=" * 80)

for market in sorted(filtered_df['market_type'].unique()):
    market_df = filtered_df[filtered_df['market_type'] == market]
    market_wins = market_df['correct'].sum()
    market_losses = len(market_df) - market_wins
    market_wr = (market_wins / len(market_df)) * 100 if len(market_df) > 0 else 0

    # Recalculate P/L sequentially for this market
    market_bankroll = 1000.0
    market_pl = 0
    for _, bet in market_df.iterrows():
        stake = bet['stake_pct'] * market_bankroll
        if bet['correct']:
            profit = stake * (bet['odds'] - 1)
        else:
            profit = -stake
        market_pl += profit
        market_bankroll += profit

    avg_conf = market_df['confidence'].mean() * 100

    print(f"{market}: {len(market_df)} bets | {market_wins}W-{market_losses}L | "
          f"{market_wr:.1f}% WR | ${market_pl:.2f} | Avg Conf: {avg_conf:.1f}%")

print()

# Performance by league (top 10)
print("=" * 80)
print("📊 TOP 10 LEAGUES BY PROFIT (Volume Controlled)")
print("=" * 80)

league_stats = []
for league in filtered_df['league'].unique():
    league_df = filtered_df[filtered_df['league'] == league]
    league_wins = league_df['correct'].sum()
    league_wr = (league_wins / len(league_df)) * 100 if len(league_df) > 0 else 0

    # Recalculate P/L sequentially for this league
    league_bankroll = 1000.0
    league_pl = 0
    for _, bet in league_df.iterrows():
        stake = bet['stake_pct'] * league_bankroll
        if bet['correct']:
            profit = stake * (bet['odds'] - 1)
        else:
            profit = -stake
        league_pl += profit
        league_bankroll += profit

    league_stats.append({
        'league': league,
        'bets': len(league_df),
        'wins': league_wins,
        'wr': league_wr,
        'pl': league_pl
    })

# Sort by profit and show top 10
league_stats_df = pd.DataFrame(league_stats).sort_values('pl', ascending=False)
for _, row in league_stats_df.head(10).iterrows():
    print(f"{row['league']}: {row['bets']} bets | {row['wins']}W | "
          f"{row['wr']:.1f}% WR | ${row['pl']:.2f}")

print()

# Daily stats
print("=" * 80)
print("📊 DAILY BETTING VOLUME")
print("=" * 80)

daily_counts = filtered_df.groupby(['date', 'is_weekend']).size().reset_index(name='count')
weekday_avg = daily_counts[~daily_counts['is_weekend']]['count'].mean()
weekend_avg = daily_counts[daily_counts['is_weekend']]['count'].mean()

print(f"Weekday average: {weekday_avg:.1f} bets/day (target: max {WEEKDAY_MAX})")
print(f"Weekend average: {weekend_avg:.1f} bets/day (target: max {WEEKEND_MAX})")
print()

# Comparison to original
print("=" * 80)
print("📊 COMPARISON: ORIGINAL vs VOLUME CONTROLLED")
print("=" * 80)
print(f"Original: 3,545 bets | 52.1% WR | -$1,000.00 profit | -100.0% ROI")
print(f"Volume Controlled: {len(filtered_df)} bets | {win_rate:.1f}% WR | ${total_pl:.2f} profit | {roi:.1f}% ROI")
print(f"\nBet reduction: {((len(df) - len(filtered_df)) / len(df) * 100):.1f}%")
print(f"Profit improvement: ${total_pl - (-1000):.2f}")
print()

print("✅ Analysis complete!")
