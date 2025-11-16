#!/usr/bin/env python3
"""
Corners Backtesting - Over/Under 9.5 Corners

Backtest betting strategies for over/under 9.5 corners per game
using historical data from the last two years.

Usage:
    python3 corners_backtest.py --start-date 2023-10-24 --end-date 2025-10-24 --strategy auto
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from footystats_api import FootyStatsAPI

# FootyStats API Key
API_KEY = "ceb338b9bcb82a452efc114fb2d3cccac67f58be1569e7b5acf1d2195adeae11"

# Betting configuration
INITIAL_BANKROLL = 1000.0
KELLY_FRACTION = 0.25  # Conservative quarter-Kelly
MAX_BET_SIZE = 0.05  # Maximum 5% of bankroll
FIXED_STAKE_PCT = 0.02  # 2% fixed stake


class CornersBacktester:
    """Backtest corners betting strategies"""

    def __init__(self, start_date: str, end_date: str, strategy: str = "auto"):
        """
        Initialize backtester

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            strategy: Betting strategy ('over', 'under', 'auto')
        """
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d')
        self.strategy = strategy
        self.api = FootyStatsAPI(API_KEY)

        self.bankroll = INITIAL_BANKROLL
        self.initial_bankroll = INITIAL_BANKROLL
        self.bets = []
        self.daily_results = []

        # League-specific statistics (will be built from data)
        self.league_stats = {}

    def calculate_implied_probability(self, odds: float) -> float:
        """Calculate implied probability from decimal odds"""
        if odds <= 1.0:
            return 0.0
        return 1.0 / odds

    def calculate_kelly_stake(self, odds: float, win_probability: float) -> float:
        """Calculate Kelly Criterion stake size"""
        if odds <= 1.0 or win_probability <= 0:
            return 0.0

        # Kelly formula: (odds * probability - 1) / (odds - 1)
        kelly = (odds * win_probability - 1) / (odds - 1)

        # Apply Kelly fraction and cap at maximum
        kelly_fraction = kelly * KELLY_FRACTION
        return min(kelly_fraction, MAX_BET_SIZE)

    def should_bet_over(self, match: Dict, league_over_rate: float) -> Tuple[bool, float]:
        """
        Determine if we should bet Over 9.5 corners

        Returns:
            (should_bet, stake_percentage)
        """
        odds = match['odds'].get('corners_over_9_5_odds', 1.9)

        # Use league-specific over rate as our probability estimate
        win_probability = league_over_rate

        # Calculate implied probability from odds
        implied_prob = self.calculate_implied_probability(odds)

        # Only bet if we have an edge (our probability > implied probability)
        if win_probability > implied_prob:
            stake = self.calculate_kelly_stake(odds, win_probability)
            return (True, stake)

        return (False, 0.0)

    def should_bet_under(self, match: Dict, league_over_rate: float) -> Tuple[bool, float]:
        """
        Determine if we should bet Under 9.5 corners

        Returns:
            (should_bet, stake_percentage)
        """
        odds = match['odds'].get('corners_under_9_5_odds', 1.9)

        # Under probability is 1 - over_rate
        win_probability = 1.0 - league_over_rate

        # Calculate implied probability from odds
        implied_prob = self.calculate_implied_probability(odds)

        # Only bet if we have an edge
        if win_probability > implied_prob:
            stake = self.calculate_kelly_stake(odds, win_probability)
            return (True, stake)

        return (False, 0.0)

    def build_league_statistics(self, training_end_date: datetime):
        """Build league statistics from training data"""
        print(f"\n📊 Building league statistics (training period)...")

        training_start = self.start_date
        current_date = training_start

        training_matches = []

        while current_date <= training_end_date:
            date_str = current_date.strftime('%Y-%m-%d')

            try:
                matches = self.api.get_matches_by_date(date_str)
                matches_with_corners = [m for m in matches if m.get('total_corners', 0) > 0]
                training_matches.extend(matches_with_corners)
            except Exception as e:
                pass

            current_date += timedelta(days=1)

        # Calculate league-specific over rates
        df = pd.DataFrame(training_matches)

        if not df.empty:
            league_stats = df.groupby('league').agg({
                'total_corners': 'count',
                'over_9_5_corners': 'mean'
            })

            for league in league_stats.index:
                self.league_stats[league] = {
                    'matches': int(league_stats.loc[league, 'total_corners']),
                    'over_rate': league_stats.loc[league, 'over_9_5_corners']
                }

        print(f"✅ League statistics built from {len(training_matches)} matches")

    def backtest_date(self, date_str: str) -> Dict:
        """Backtest a single date"""
        print(f"\n{'─'*80}")
        print(f"📅 {date_str}")

        # Fetch matches
        try:
            matches = self.api.get_matches_by_date(date_str)
        except Exception as e:
            print(f"⚠️  Error fetching matches: {e}")
            return {
                'date': date_str,
                'bets': 0,
                'wins': 0,
                'losses': 0,
                'profit': 0,
                'bankroll': self.bankroll
            }

        # Filter matches with corners data
        matches = [m for m in matches if m.get('total_corners', 0) > 0]

        if not matches:
            print(f"⚠️  No matches with corners data")
            return {
                'date': date_str,
                'bets': 0,
                'wins': 0,
                'losses': 0,
                'profit': 0,
                'bankroll': self.bankroll
            }

        daily_bets = 0
        daily_wins = 0
        daily_losses = 0
        daily_profit = 0.0

        for match in matches:
            league = match['league']

            # Skip if we don't have league statistics
            if league not in self.league_stats:
                continue

            league_over_rate = self.league_stats[league]['over_rate']

            # Determine bet based on strategy
            bet_over = False
            bet_under = False
            stake_pct = 0.0

            if self.strategy == 'over':
                should_bet, stake = self.should_bet_over(match, league_over_rate)
                bet_over = should_bet
                stake_pct = stake
            elif self.strategy == 'under':
                should_bet, stake = self.should_bet_under(match, league_over_rate)
                bet_under = should_bet
                stake_pct = stake
            elif self.strategy == 'auto':
                # Bet on whichever has better value
                should_bet_over, stake_over = self.should_bet_over(match, league_over_rate)
                should_bet_under, stake_under = self.should_bet_under(match, league_over_rate)

                if should_bet_over and stake_over > stake_under:
                    bet_over = True
                    stake_pct = stake_over
                elif should_bet_under and stake_under > stake_over:
                    bet_under = True
                    stake_pct = stake_under

            # Place bet if we have a signal
            if (bet_over or bet_under) and stake_pct > 0:
                selection = "Over 9.5" if bet_over else "Under 9.5"
                odds = match['odds'].get('corners_over_9_5_odds' if bet_over else 'corners_under_9_5_odds', 1.9)

                stake_amount = self.bankroll * stake_pct
                actual_corners = match['total_corners']
                is_correct = (actual_corners > 9.5) if bet_over else (actual_corners <= 9.5)

                if is_correct:
                    profit = stake_amount * (odds - 1)
                    daily_profit += profit
                    daily_wins += 1
                    result_icon = "✅"
                else:
                    profit = -stake_amount
                    daily_profit += profit
                    daily_losses += 1
                    result_icon = "❌"

                daily_bets += 1

                # Store bet
                self.bets.append({
                    'date': date_str,
                    'league': league,
                    'home_team': match['home_team'],
                    'away_team': match['away_team'],
                    'selection': selection,
                    'odds': odds,
                    'stake_pct': stake_pct,
                    'stake_amount': stake_amount,
                    'actual_corners': actual_corners,
                    'correct': is_correct,
                    'profit': profit,
                    'bankroll_before': self.bankroll,
                    'bankroll_after': self.bankroll + profit
                })

                print(f"  {result_icon} {match['home_team']} vs {match['away_team']}")
                print(f"     {selection} @ {odds:.2f} | Corners: {actual_corners} | P/L: ${profit:.2f}")

        # Update bankroll
        self.bankroll += daily_profit

        # Daily summary
        if daily_bets > 0:
            win_rate = (daily_wins / daily_bets) * 100
            print(f"\n  📊 Bets: {daily_bets} | Wins: {daily_wins} | Losses: {daily_losses} | WR: {win_rate:.1f}%")
            print(f"  💰 P/L: ${daily_profit:+.2f} | Bankroll: ${self.bankroll:.2f}")

        return {
            'date': date_str,
            'bets': daily_bets,
            'wins': daily_wins,
            'losses': daily_losses,
            'profit': daily_profit,
            'bankroll': self.bankroll
        }

    def run_backtest(self):
        """Run full backtest"""
        print(f"\n{'='*80}")
        print(f"⚽ CORNERS BETTING BACKTEST - Over/Under 9.5")
        print(f"{'='*80}")
        print(f"Period: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        print(f"Strategy: {self.strategy.upper()}")
        print(f"Initial Bankroll: ${self.initial_bankroll:.2f}")
        print(f"Kelly Fraction: {KELLY_FRACTION:.0%} | Max Bet: {MAX_BET_SIZE:.0%}")
        print(f"{'='*80}")

        # Build league statistics from first 30% of data
        training_days = int((self.end_date - self.start_date).days * 0.3)
        training_end = self.start_date + timedelta(days=training_days)
        self.build_league_statistics(training_end)

        print(f"\nLeague statistics:")
        for league, stats in sorted(self.league_stats.items(), key=lambda x: x[1]['over_rate'], reverse=True):
            print(f"  {league}: {stats['over_rate']*100:.1f}% over rate ({stats['matches']} matches)")

        # Start backtesting from after training period
        current_date = training_end + timedelta(days=1)

        print(f"\n{'='*80}")
        print(f"📊 BACKTESTING RESULTS")
        print(f"{'='*80}")

        while current_date <= self.end_date:
            date_str = current_date.strftime('%Y-%m-%d')

            try:
                daily_result = self.backtest_date(date_str)
                self.daily_results.append(daily_result)
            except Exception as e:
                print(f"❌ Error on {date_str}: {e}")

            current_date += timedelta(days=1)

        # Generate report
        self.generate_report()

    def generate_report(self):
        """Generate comprehensive backtest report"""
        print(f"\n{'='*80}")
        print(f"📊 BACKTEST SUMMARY")
        print(f"{'='*80}")

        if not self.bets:
            print("⚠️  No bets placed")
            return

        # Overall statistics
        total_bets = len(self.bets)
        total_wins = sum(1 for b in self.bets if b['correct'])
        total_losses = total_bets - total_wins
        win_rate = (total_wins / total_bets * 100) if total_bets > 0 else 0

        total_profit = self.bankroll - self.initial_bankroll
        roi = (total_profit / self.initial_bankroll * 100) if self.initial_bankroll > 0 else 0

        print(f"\n📈 Overall Performance:")
        print(f"   Total Bets: {total_bets}")
        print(f"   Wins: {total_wins} | Losses: {total_losses}")
        print(f"   Win Rate: {win_rate:.1f}%")
        print(f"   Total Profit: ${total_profit:+.2f}")
        print(f"   ROI: {roi:+.1f}%")
        print(f"   Final Bankroll: ${self.bankroll:.2f}")
        print(f"   Bankroll Growth: {((self.bankroll / self.initial_bankroll - 1) * 100):+.1f}%")

        # Selection breakdown
        df = pd.DataFrame(self.bets)

        print(f"\n📊 Performance by Selection:")
        selection_stats = df.groupby('selection').agg({
            'correct': ['count', 'sum', 'mean'],
            'profit': 'sum'
        })

        for selection in selection_stats.index:
            count = int(selection_stats.loc[selection, ('correct', 'count')])
            wins = int(selection_stats.loc[selection, ('correct', 'sum')])
            win_rate_sel = selection_stats.loc[selection, ('correct', 'mean')] * 100
            profit_sel = selection_stats.loc[selection, ('profit', 'sum')]

            print(f"   {selection}: {count} bets | {wins} wins | {win_rate_sel:.1f}% WR | ${profit_sel:+.2f}")

        # League breakdown
        print(f"\n📊 Performance by League:")
        league_stats = df.groupby('league').agg({
            'correct': ['count', 'sum', 'mean'],
            'profit': 'sum'
        }).sort_values(('profit', 'sum'), ascending=False)

        for league in league_stats.index:
            count = int(league_stats.loc[league, ('correct', 'count')])
            wins = int(league_stats.loc[league, ('correct', 'sum')])
            win_rate_league = league_stats.loc[league, ('correct', 'mean')] * 100
            profit_league = league_stats.loc[league, ('profit', 'sum')]

            print(f"   {league}: {count} bets | {wins} wins | {win_rate_league:.1f}% WR | ${profit_league:+.2f}")

        # Save results
        bets_file = f'corners_backtest_bets_{self.strategy}.csv'
        df.to_csv(bets_file, index=False)
        print(f"\n✅ Detailed bets saved to: {bets_file}")

        daily_df = pd.DataFrame(self.daily_results)
        daily_file = f'corners_backtest_daily_{self.strategy}.csv'
        daily_df.to_csv(daily_file, index=False)
        print(f"✅ Daily summary saved to: {daily_file}")

        print(f"\n{'='*80}\n")


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Backtest corners over/under 9.5 betting')
    parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--strategy', default='auto',
                       choices=['over', 'under', 'auto'],
                       help='Betting strategy: over, under, or auto (default: auto)')

    args = parser.parse_args()

    try:
        backtester = CornersBacktester(args.start_date, args.end_date, args.strategy)
        backtester.run_backtest()

    except Exception as e:
        print(f"\n❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
