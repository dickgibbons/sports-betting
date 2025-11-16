#!/usr/bin/env python3
"""
Analyze optimal confidence thresholds for calibrated predictions
"""

import pandas as pd
import numpy as np

# Load the UNCALIBRATED backtest results
df = pd.read_csv('backtest_2024_relaxed_detailed.csv')

print('='*80)
print('THRESHOLD OPTIMIZATION ANALYSIS')
print('='*80)
print()

# Analyze different confidence thresholds
thresholds = [0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90]

print('Testing different confidence thresholds on UNCALIBRATED data:')
print()
print('Threshold | Bets  | Win Rate | Avg Odds | Total Profit | ROI    ')
print('-'*80)

for threshold in thresholds:
    filtered = df[df['confidence'] >= threshold]

    if len(filtered) > 0:
        bets = len(filtered)
        wins = filtered['correct'].sum()
        win_rate = wins / bets
        avg_odds = filtered['odds'].mean()
        total_profit = filtered['profit'].sum()
        total_staked = filtered['stake_amount'].sum()
        roi = (total_profit / total_staked * 100) if total_staked > 0 else 0

        print(f'{threshold:.0%}      | {bets:5d} | {win_rate:7.1%} | {avg_odds:8.2f} | ${total_profit:11.2f} | {roi:6.1f}%')
    else:
        print(f'{threshold:.0%}      | {0:5d} | {0:7.1%} | {0:8.2f} | ${0:11.2f} | {0:6.1f}%')

print()
print('='*80)
print('BY MARKET ANALYSIS')
print('='*80)
print()

for market in ['Home Win', 'Under 2.5', 'BTTS No']:
    market_df = df[df['market'] == market]

    if len(market_df) > 0:
        print(f'{market}:')
        print(f'  Threshold | Bets  | Win Rate | Profit     | ROI')
        print(f'  ' + '-'*60)

        for threshold in [0.60, 0.65, 0.70, 0.75, 0.80, 0.85]:
            filtered = market_df[market_df['confidence'] >= threshold]

            if len(filtered) > 0:
                bets = len(filtered)
                wins = filtered['correct'].sum()
                win_rate = wins / bets
                total_profit = filtered['profit'].sum()
                total_staked = filtered['stake_amount'].sum()
                roi = (total_profit / total_staked * 100) if total_staked > 0 else 0

                print(f'  {threshold:.0%}      | {bets:5d} | {win_rate:7.1%} | ${total_profit:10.2f} | {roi:6.1f}%')
        print()
