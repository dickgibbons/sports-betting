#!/usr/bin/env python3
"""
First Half Goals Backtest

Backtests the strategy of betting "First Half Over 0.5 Goals" when both teams
have historically high first-half scoring rates.

Usage:
    python3 first_half_backtest.py --start-date 2024-08-01 --end-date 2024-10-24
"""

import argparse
import sys
from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict
from footystats_api import FootyStatsAPI

# FootyStats API Key
API_KEY = "ceb338b9bcb82a452efc114fb2d3cccac67f58be1569e7b5acf1d2195adeae11"

# Backtest configuration
INITIAL_BANKROLL = 1000.0
FIXED_STAKE_PCT = 0.02  # 2% of bankroll per bet

# Betting threshold - only bet if BOTH teams score in H1 at least this % of time
MIN_H1_RATE = 50.0  # 50% - both teams must score in H1 at least half the time


class FirstHalfBacktest:
    """Backtest first half over 0.5 goals strategy"""

    def __init__(self, start_date: str, end_date: str):
        """Initialize backtest"""
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d')
        self.api = FootyStatsAPI(API_KEY)

        self.bankroll = INITIAL_BANKROLL
        self.initial_bankroll = INITIAL_BANKROLL

        # Team first half stats (built from training period)
        self.team_h1_stats = defaultdict(lambda: {
            'games': 0,
            'h1_scored': 0,  # Games where team scored in H1
        })

        self.bets = []
        self.daily_results = []

    def build_team_stats(self, end_date: datetime):
        """Build team H1 stats from training data"""
        print(f"\n📊 Building team first half statistics (training period)...")
        print(f"   Training from {self.start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

        current_date = self.start_date

        training_matches = 0

        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')

            try:
                matches = self.api.get_matches_by_date(date_str)

                for match in matches:
                    # Skip if no halftime data
                    if 'halftime_score' not in match:
                        continue

                    halftime_score = match.get('halftime_score', '')
                    if not halftime_score or '-' not in halftime_score:
                        continue

                    try:
                        h1_home, h1_away = map(int, halftime_score.split('-'))
                    except:
                        continue

                    home_team = match['home_team']
                    away_team = match['away_team']

                    # Update stats
                    self.team_h1_stats[home_team]['games'] += 1
                    self.team_h1_stats[away_team]['games'] += 1

                    if h1_home > 0:
                        self.team_h1_stats[home_team]['h1_scored'] += 1
                    if h1_away > 0:
                        self.team_h1_stats[away_team]['h1_scored'] += 1

                    training_matches += 1

            except Exception as e:
                pass

            current_date += timedelta(days=1)

        # Calculate rates
        teams_with_data = 0
        for team, stats in self.team_h1_stats.items():
            if stats['games'] > 0:
                stats['h1_rate'] = (stats['h1_scored'] / stats['games']) * 100
                teams_with_data += 1

        print(f"   ✅ Processed {training_matches} matches")
        print(f"   ✅ {teams_with_data} teams with H1 statistics")

    def should_bet_h1_over(self, home_team: str, away_team: str) -> bool:
        """Determine if we should bet H1 Over 0.5 goals"""
        home_stats = self.team_h1_stats.get(home_team)
        away_stats = self.team_h1_stats.get(away_team)

        if not home_stats or not away_stats:
            return False

        if home_stats['games'] < 5 or away_stats['games'] < 5:
            return False

        home_h1_rate = home_stats.get('h1_rate', 0)
        away_h1_rate = away_stats.get('h1_rate', 0)

        # Both teams must score in H1 frequently
        return home_h1_rate >= MIN_H1_RATE and away_h1_rate >= MIN_H1_RATE

    def backtest_date(self, date_str: str) -> Dict:
        """Backtest a single date"""
        try:
            matches = self.api.get_matches_by_date(date_str)
        except Exception as e:
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
            home_team = match['home_team']
            away_team = match['away_team']

            # Check if we should bet
            if not self.should_bet_h1_over(home_team, away_team):
                continue

            # Get halftime score
            halftime_score = match.get('halftime_score', '')
            if not halftime_score or '-' not in halftime_score:
                continue

            try:
                h1_home, h1_away = map(int, halftime_score.split('-'))
            except:
                continue

            h1_total = h1_home + h1_away

            # Place bet: H1 Over 0.5
            odds = 1.8  # Typical odds for H1 Over 0.5 (estimate, not from API)
            stake_amount = self.bankroll * FIXED_STAKE_PCT

            is_correct = h1_total > 0  # Over 0.5 means at least 1 goal in H1

            if is_correct:
                profit = stake_amount * (odds - 1)
                daily_profit += profit
                daily_wins += 1
            else:
                profit = -stake_amount
                daily_profit += profit
                daily_losses += 1

            daily_bets += 1

            # Get team H1 rates for logging
            home_h1_rate = self.team_h1_stats[home_team].get('h1_rate', 0)
            away_h1_rate = self.team_h1_stats[away_team].get('h1_rate', 0)

            # Store bet
            self.bets.append({
                'date': date_str,
                'home_team': home_team,
                'away_team': away_team,
                'home_h1_rate': home_h1_rate,
                'away_h1_rate': away_h1_rate,
                'h1_score': halftime_score,
                'h1_total': h1_total,
                'correct': is_correct,
                'stake': stake_amount,
                'profit': profit,
                'bankroll_after': self.bankroll + profit
            })

        # Update bankroll
        self.bankroll += daily_profit

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
        print(f"⚽ FIRST HALF OVER 0.5 GOALS BACKTEST")
        print(f"{'='*80}")
        print(f"Period: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        print(f"Strategy: Bet H1 Over 0.5 when both teams score in H1 >= {MIN_H1_RATE}% of time")
        print(f"Initial Bankroll: ${self.initial_bankroll:.2f}")
        print(f"Stake per bet: {FIXED_STAKE_PCT*100:.0f}% of bankroll")
        print(f"{'='*80}")

        # Build team stats from first 30% of data
        training_days = int((self.end_date - self.start_date).days * 0.3)
        training_end = self.start_date + timedelta(days=training_days)
        self.build_team_stats(training_end)

        # Backtest from after training period
        current_date = training_end + timedelta(days=1)

        print(f"\n{'='*80}")
        print(f"📊 BACKTESTING RESULTS")
        print(f"{'='*80}\n")

        days_processed = 0
        total_days = (self.end_date - current_date).days + 1

        while current_date <= self.end_date:
            date_str = current_date.strftime('%Y-%m-%d')

            try:
                daily_result = self.backtest_date(date_str)
                self.daily_results.append(daily_result)

                if daily_result['bets'] > 0:
                    print(f"{date_str}: {daily_result['bets']} bets | "
                          f"{daily_result['wins']}W-{daily_result['losses']}L | "
                          f"P/L: ${daily_result['profit']:+.2f}")

            except Exception as e:
                pass

            current_date += timedelta(days=1)
            days_processed += 1

            if days_processed % 10 == 0:
                progress = (days_processed / total_days) * 100
                print(f"\n📅 Progress: {days_processed}/{total_days} days ({progress:.1f}%)\n")

        # Generate report
        self.generate_report()

    def generate_report(self):
        """Generate backtest report"""
        print(f"\n{'='*80}")
        print(f"📊 BACKTEST SUMMARY")
        print(f"{'='*80}")

        if not self.bets:
            print("⚠️  No bets placed")
            return

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

        # Save results
        import pandas as pd
        df = pd.DataFrame(self.bets)
        bets_file = f'first_half_backtest_bets.csv'
        df.to_csv(bets_file, index=False)
        print(f"\n✅ Detailed bets saved to: {bets_file}")

        daily_df = pd.DataFrame(self.daily_results)
        daily_file = f'first_half_backtest_daily.csv'
        daily_df.to_csv(daily_file, index=False)
        print(f"✅ Daily summary saved to: {daily_file}")

        print(f"\n{'='*80}\n")


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Backtest first half over 0.5 goals strategy')
    parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')

    args = parser.parse_args()

    try:
        backtester = FirstHalfBacktest(args.start_date, args.end_date)
        backtester.run_backtest()

    except Exception as e:
        print(f"\n❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
