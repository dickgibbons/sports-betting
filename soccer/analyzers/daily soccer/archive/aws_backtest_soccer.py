#!/usr/bin/env python3
"""
AWS Soccer Backtesting - Test Enhanced Models on Historical Data

Backtest the enhanced soccer betting system from August 1, 2025 to present
to evaluate performance with real historical results.

Usage:
    python3 aws_backtest_soccer.py --start-date 2025-08-01 --end-date 2025-10-18
"""

import os
import sys
import json
import requests
import numpy as np
import pandas as pd
import joblib
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
import argparse

# Import the betting generator class
from soccer_best_bets_daily import SoccerBestBetsGenerator

# API Configuration
API_KEY = "960c628e1c91c4b1f125e1eec52ad862"
API_BASE = "https://v3.football.api-sports.io"

# Minimum confidence thresholds (same as production)
MIN_CONFIDENCE = 0.990
MIN_TOTALS_CONFIDENCE = 0.990
MIN_BTTS_CONFIDENCE = 0.985
MIN_CORNERS_CONFIDENCE = 0.980

# Bankroll settings
INITIAL_BANKROLL = 1000.0
KELLY_FRACTION = 0.25
MAX_BET_SIZE = 0.05


class SoccerBacktester:
    """Backtest soccer betting system on historical data"""

    def __init__(self, start_date: str, end_date: str):
        """Initialize backtester with date range"""
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d')
        self.generator = SoccerBestBetsGenerator()
        self.bankroll = INITIAL_BANKROLL
        self.initial_bankroll = INITIAL_BANKROLL
        self.results = []
        self.daily_results = []

    def fetch_historical_results(self, fixture_id: int) -> Optional[Dict]:
        """Fetch actual results for a completed fixture"""
        try:
            headers = {'x-apisports-key': API_KEY}
            url = f"{API_BASE}/fixtures"
            params = {'id': fixture_id}

            response = requests.get(url, params=params, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                fixtures = data.get('response', [])

                if fixtures:
                    fixture = fixtures[0]
                    status = fixture.get('fixture', {}).get('status', {}).get('short', '')

                    # Only process finished matches
                    if status == 'FT':
                        goals = fixture.get('goals', {})
                        home_goals = goals.get('home', 0)
                        away_goals = goals.get('away', 0)

                        # Get first half (halftime) score
                        score = fixture.get('score', {})
                        halftime = score.get('halftime', {})
                        h1_home_goals = halftime.get('home', 0) if halftime else 0
                        h1_away_goals = halftime.get('away', 0) if halftime else 0
                        h1_total_goals = (h1_home_goals or 0) + (h1_away_goals or 0)

                        return {
                            'home_goals': home_goals,
                            'away_goals': away_goals,
                            'total_goals': home_goals + away_goals,
                            'result': 'Home' if home_goals > away_goals else ('Away' if away_goals > home_goals else 'Draw'),
                            'btts': home_goals > 0 and away_goals > 0,
                            'h1_home_goals': h1_home_goals,
                            'h1_away_goals': h1_away_goals,
                            'h1_goals': h1_total_goals
                        }

            return None

        except Exception as e:
            print(f"   ⚠️  Error fetching results for fixture {fixture_id}: {e}")
            return None

    def evaluate_prediction(self, prediction: Dict, actual_result: Dict) -> bool:
        """Check if prediction was correct"""
        market = prediction['market']

        # Match outcome predictions
        if 'Home Win' in market:
            return actual_result['result'] == 'Home'
        elif 'Away Win' in market:
            return actual_result['result'] == 'Away'
        elif market == 'Draw':
            return actual_result['result'] == 'Draw'

        # Over/Under predictions
        elif 'Over 2.5' in market:
            return actual_result['total_goals'] > 2.5
        elif 'Under 2.5' in market:
            return actual_result['total_goals'] < 2.5

        # BTTS predictions
        elif 'BTTS Yes' in market:
            return actual_result['btts'] == True
        elif 'BTTS No' in market:
            return actual_result['btts'] == False

        # H1 (First Half) predictions
        elif 'H1 Over 0.5' in market:
            return actual_result.get('h1_goals', 0) > 0.5
        elif 'H1 Under 0.5' in market:
            return actual_result.get('h1_goals', 0) < 0.5
        elif 'H1 Over 1.5' in market:
            return actual_result.get('h1_goals', 0) > 1.5
        elif 'H1 Under 1.5' in market:
            return actual_result.get('h1_goals', 0) < 1.5

        # Unknown market
        return False

    def backtest_date(self, date_str: str) -> Dict:
        """Backtest a single date"""
        print(f"\n{'='*80}")
        print(f"📅 Backtesting {date_str}")
        print(f"{'='*80}")

        # Generate predictions for this date using the production system
        df = self.generator.generate_daily_report(date_str)

        if df.empty:
            print(f"⚠️  No bets generated for {date_str}")
            return {
                'date': date_str,
                'bets': 0,
                'wins': 0,
                'losses': 0,
                'pending': 0,
                'profit': 0,
                'roi': 0,
                'bankroll': self.bankroll
            }

        # Wait a bit to avoid API rate limits
        time.sleep(1)

        # Fetch actual results for each prediction
        wins = 0
        losses = 0
        pending = 0
        daily_profit = 0

        for idx, row in df.iterrows():
            # Try to get the fixture ID from the match
            # We'll need to fetch it again based on teams/league/date
            home_team = row['home_team']
            away_team = row['away_team']

            # Find the original match to get fixture_id
            matches = self.generator.fetch_upcoming_matches(date_str)
            fixture_id = None

            for match in matches:
                if match['home_name'] == home_team and match['away_name'] == away_team:
                    fixture_id = match['id']
                    break

            if not fixture_id:
                print(f"   ⚠️  Could not find fixture ID for {home_team} vs {away_team}")
                pending += 1
                continue

            # Fetch actual result
            actual_result = self.fetch_historical_results(fixture_id)

            if not actual_result:
                print(f"   ⚠️  No result found for {home_team} vs {away_team}")
                pending += 1
                continue

            # Evaluate prediction
            prediction = {
                'market': row['market'],
                'selection': row['selection'],
                'odds': row['odds']
            }

            is_correct = self.evaluate_prediction(prediction, actual_result)

            # Calculate profit/loss
            stake_pct = row['kelly_stake']
            stake_amount = self.bankroll * stake_pct

            if is_correct:
                profit = stake_amount * (row['odds'] - 1)
                daily_profit += profit
                wins += 1
                result_symbol = "✅"
            else:
                profit = -stake_amount
                daily_profit += profit
                losses += 1
                result_symbol = "❌"

            print(f"   {result_symbol} {home_team} vs {away_team} | {row['market']} @ {row['odds']:.2f} | Profit: ${profit:.2f}")

            # Store individual bet result
            self.results.append({
                'date': date_str,
                'home_team': home_team,
                'away_team': away_team,
                'market': row['market'],
                'selection': row['selection'],
                'odds': row['odds'],
                'confidence': row['confidence'],
                'stake_pct': stake_pct,
                'stake_amount': stake_amount,
                'actual_result': actual_result['result'],
                'correct': is_correct,
                'profit': profit,
                'bankroll_after': self.bankroll + profit
            })

        # Update bankroll
        self.bankroll += daily_profit

        # Daily summary
        total_bets = len(df)
        win_rate = (wins / total_bets * 100) if total_bets > 0 else 0
        roi = (daily_profit / (self.bankroll - daily_profit) * 100) if (self.bankroll - daily_profit) > 0 else 0

        daily_summary = {
            'date': date_str,
            'bets': total_bets,
            'wins': wins,
            'losses': losses,
            'pending': pending,
            'profit': daily_profit,
            'roi': roi,
            'bankroll': self.bankroll,
            'win_rate': win_rate
        }

        self.daily_results.append(daily_summary)

        print(f"\n📊 Daily Summary:")
        print(f"   Bets: {total_bets} | Wins: {wins} | Losses: {losses} | Pending: {pending}")
        print(f"   Daily P/L: ${daily_profit:.2f} | ROI: {roi:.1f}%")
        print(f"   Bankroll: ${self.bankroll:.2f}")

        return daily_summary

    def run_backtest(self):
        """Run backtest for entire date range"""
        print(f"\n{'='*80}")
        print(f"⚽ SOCCER BETTING BACKTEST")
        print(f"{'='*80}")
        print(f"Start Date: {self.start_date.strftime('%Y-%m-%d')}")
        print(f"End Date: {self.end_date.strftime('%Y-%m-%d')}")
        print(f"Initial Bankroll: ${self.initial_bankroll:.2f}")
        print(f"Thresholds: Winners {MIN_CONFIDENCE:.0%} | Totals {MIN_TOTALS_CONFIDENCE:.0%} | BTTS {MIN_BTTS_CONFIDENCE:.0%}")
        print(f"{'='*80}")

        # Iterate through each date
        current_date = self.start_date

        while current_date <= self.end_date:
            date_str = current_date.strftime('%Y-%m-%d')

            try:
                self.backtest_date(date_str)
            except Exception as e:
                print(f"❌ Error backtesting {date_str}: {e}")
                import traceback
                traceback.print_exc()

            # Move to next day
            current_date += timedelta(days=1)

            # Rate limiting - be nice to the API
            time.sleep(2)

        # Generate final report
        self.generate_report()

    def generate_report(self):
        """Generate comprehensive backtest report"""
        print(f"\n{'='*80}")
        print(f"📊 BACKTEST RESULTS")
        print(f"{'='*80}")

        if not self.results:
            print("⚠️  No results to report")
            return

        # Overall statistics
        total_bets = len(self.results)
        total_wins = sum(1 for r in self.results if r['correct'])
        total_losses = sum(1 for r in self.results if not r['correct'])

        win_rate = (total_wins / total_bets * 100) if total_bets > 0 else 0

        total_profit = self.bankroll - self.initial_bankroll
        roi = (total_profit / self.initial_bankroll * 100) if self.initial_bankroll > 0 else 0

        print(f"\n📈 Overall Performance:")
        print(f"   Total Bets: {total_bets}")
        print(f"   Wins: {total_wins} | Losses: {total_losses}")
        print(f"   Win Rate: {win_rate:.1f}%")
        print(f"   Total Profit: ${total_profit:.2f}")
        print(f"   ROI: {roi:.1f}%")
        print(f"   Final Bankroll: ${self.bankroll:.2f}")
        print(f"   Bankroll Growth: {((self.bankroll / self.initial_bankroll - 1) * 100):.1f}%")

        # Market-specific performance
        results_df = pd.DataFrame(self.results)

        print(f"\n📊 Performance by Market:")
        market_stats = results_df.groupby('market').agg({
            'correct': ['count', 'sum', 'mean'],
            'profit': 'sum'
        }).round(2)

        for market in market_stats.index:
            count = market_stats.loc[market, ('correct', 'count')]
            wins = market_stats.loc[market, ('correct', 'sum')]
            win_rate = market_stats.loc[market, ('correct', 'mean')] * 100
            profit = market_stats.loc[market, ('profit', 'sum')]

            print(f"   {market}: {int(count)} bets | {int(wins)} wins | {win_rate:.1f}% | ${profit:.2f}")

        # Save detailed results
        results_file = 'backtest_results_detailed.csv'
        results_df.to_csv(results_file, index=False)
        print(f"\n✅ Detailed results saved to: {results_file}")

        # Save daily summary
        daily_df = pd.DataFrame(self.daily_results)
        daily_file = 'backtest_results_daily.csv'
        daily_df.to_csv(daily_file, index=False)
        print(f"✅ Daily summary saved to: {daily_file}")

        # Plot bankroll growth (if matplotlib available)
        try:
            import matplotlib.pyplot as plt

            plt.figure(figsize=(12, 6))
            plt.plot(daily_df['date'], daily_df['bankroll'], marker='o', linewidth=2)
            plt.axhline(y=self.initial_bankroll, color='r', linestyle='--', label='Initial Bankroll')
            plt.title('Bankroll Growth Over Time', fontsize=16, fontweight='bold')
            plt.xlabel('Date', fontsize=12)
            plt.ylabel('Bankroll ($)', fontsize=12)
            plt.xticks(rotation=45)
            plt.grid(True, alpha=0.3)
            plt.legend()
            plt.tight_layout()

            chart_file = 'backtest_bankroll_chart.png'
            plt.savefig(chart_file, dpi=150)
            print(f"✅ Bankroll chart saved to: {chart_file}")

        except ImportError:
            print("⚠️  matplotlib not available - skipping chart generation")


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Backtest soccer betting system')
    parser.add_argument('--start-date', default='2025-08-01',
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', default='2025-10-18',
                       help='End date (YYYY-MM-DD)')

    args = parser.parse_args()

    try:
        backtester = SoccerBacktester(args.start_date, args.end_date)
        backtester.run_backtest()

    except Exception as e:
        print(f"\n❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
