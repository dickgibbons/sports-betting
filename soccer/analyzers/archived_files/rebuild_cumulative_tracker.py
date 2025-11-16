#!/usr/bin/env python3
"""
Rebuild Cumulative Tracker with ALL Individual Picks and Results
"""

import pandas as pd
import csv
from datetime import datetime

def rebuild_cumulative_tracker():
    """Rebuild the cumulative tracker with all individual picks"""

    print('🔄 Rebuilding Cumulative Tracker with ALL Individual Picks...')
    print('=' * 60)

    # Load the all-time picks history
    all_time_file = 'output reports/all_time_picks_history_fixed.csv'

    try:
        df = pd.read_csv(all_time_file)
        print(f'📊 Loaded {len(df)} total picks from all-time history')

        # Add columns for tracking if not present
        if 'actual_result' not in df.columns:
            df['actual_result'] = 'Pending'  # Default to pending
        if 'profit_loss' not in df.columns:
            df['profit_loss'] = 0.0
        if 'bet_amount' not in df.columns:
            # Calculate bet amount from stake percentage (assuming $1000 bankroll)
            df['bet_amount'] = (df['recommended_stake_pct'] / 100) * 1000

        # Calculate running totals
        df['running_profit'] = df['profit_loss'].cumsum()
        df['pick_number'] = range(1, len(df) + 1)

        # Add bankroll tracking (starting with $1000)
        initial_bankroll = 1000
        df['running_bankroll'] = initial_bankroll + df['running_profit']

        # Calculate running win rate
        wins_so_far = []
        total_picks = []
        for i in range(len(df)):
            wins = len([x for x in df['actual_result'].iloc[:i+1] if x == 'Win'])
            total = i + 1
            wins_so_far.append(wins)
            total_picks.append(total)

        df['cumulative_wins'] = wins_so_far
        df['cumulative_picks'] = total_picks
        df['running_win_rate'] = (df['cumulative_wins'] / df['cumulative_picks'] * 100).round(1)

        # Create the proper cumulative tracker
        cumulative_tracker = df[['date', 'kick_off', 'home_team', 'away_team', 'league',
                               'market', 'bet_description', 'odds', 'recommended_stake_pct',
                               'edge_percent', 'confidence_percent', 'expected_value',
                               'bet_amount', 'actual_result', 'profit_loss', 'running_profit',
                               'running_bankroll', 'pick_number', 'cumulative_wins',
                               'cumulative_picks', 'running_win_rate']].copy()

        # Save the rebuilt cumulative tracker
        output_file = 'output reports/cumulative_picks_tracker.csv'
        cumulative_tracker.to_csv(output_file, index=False)

        print(f'✅ Rebuilt cumulative tracker with {len(cumulative_tracker)} individual picks')
        print(f'💾 Saved to: {output_file}')

        # Show summary stats
        total_picks = len(df)
        total_wins = len([x for x in df['actual_result'] if x == 'Win'])
        total_losses = len([x for x in df['actual_result'] if x == 'Loss'])
        pending = len([x for x in df['actual_result'] if x == 'Pending'])

        print(f'\n📊 CUMULATIVE STATISTICS:')
        print(f'   Total Picks: {total_picks}')
        print(f'   Wins: {total_wins}')
        print(f'   Losses: {total_losses}')
        print(f'   Pending: {pending}')
        if total_wins + total_losses > 0:
            win_rate = total_wins / (total_wins + total_losses) * 100
            print(f'   Win Rate: {win_rate:.1f}%')

        final_profit = df['running_profit'].iloc[-1] if len(df) > 0 else 0
        final_bankroll = df['running_bankroll'].iloc[-1] if len(df) > 0 else initial_bankroll
        print(f'   Total Profit/Loss: ${final_profit:.2f}')
        print(f'   Final Bankroll: ${final_bankroll:.2f}')

        return True

    except FileNotFoundError:
        print('❌ All-time picks history file not found!')
        return False
    except Exception as e:
        print(f'❌ Error: {e}')
        return False

if __name__ == "__main__":
    rebuild_cumulative_tracker()