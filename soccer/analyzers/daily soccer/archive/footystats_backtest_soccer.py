#!/usr/bin/env python3
"""
FootyStats Soccer Backtesting - Test Enhanced Models on Historical Data

Backtest the enhanced soccer betting system from August 1, 2024 to October 17, 2024
using FootyStats API for historical match data.

Usage:
    python3 footystats_backtest_soccer.py --start-date 2024-08-01 --end-date 2024-10-17
"""

import os
import sys
import numpy as np
import pandas as pd
import joblib
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
import argparse

# Import the FootyStats API and betting generator
from footystats_api import FootyStatsAPI
from soccer_best_bets_daily import SoccerBestBetsGenerator

# FootyStats API Key
FOOTYSTATS_API_KEY = "ceb338b9bcb82a452efc114fb2d3cccac67f58be1569e7b5acf1d2195adeae11"

# Minimum confidence thresholds (same as production)
MIN_CONFIDENCE = 0.990
MIN_TOTALS_CONFIDENCE = 0.990
MIN_BTTS_CONFIDENCE = 0.985
MIN_CORNERS_CONFIDENCE = 0.980

# Bankroll settings
INITIAL_BANKROLL = 1000.0
KELLY_FRACTION = 0.25
MAX_BET_SIZE = 0.05


class FootyStatsBacktester:
    """Backtest soccer betting system using FootyStats historical data"""

    def __init__(self, start_date: str, end_date: str):
        """Initialize backtester with date range"""
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d')

        # Initialize FootyStats API
        self.footystats = FootyStatsAPI(FOOTYSTATS_API_KEY)

        # Initialize betting generator
        self.generator = SoccerBestBetsGenerator()

        # Backtest state
        self.bankroll = INITIAL_BANKROLL
        self.initial_bankroll = INITIAL_BANKROLL
        self.results = []
        self.daily_results = []

    def evaluate_prediction(self, prediction: Dict, actual_match: Dict) -> bool:
        """Check if prediction was correct based on actual match results"""
        market = prediction['market']
        selection = prediction['selection']

        # Get actual results from match
        outcome = actual_match['outcome']  # 'home', 'away', or 'draw'
        over_2_5 = actual_match['over_2_5']
        btts = actual_match['btts']
        total_goals = actual_match['home_score'] + actual_match['away_score']

        # Match outcome predictions
        if 'Home Win' in market or market == 'Match Winner (Home)':
            return outcome == 'home'
        elif 'Away Win' in market or market == 'Match Winner (Away)':
            return outcome == 'away'
        elif market == 'Draw':
            return outcome == 'draw'

        # Over/Under predictions
        elif 'Over 2.5' in market:
            return over_2_5 == True
        elif 'Under 2.5' in market:
            return over_2_5 == False

        # BTTS predictions
        elif 'BTTS Yes' in market or market == 'Both Teams Score':
            return btts == True
        elif 'BTTS No' in market or market == 'Not Both Teams Score':
            return btts == False

        # Unknown market
        print(f"⚠️  Unknown market type: {market}")
        return False

    def backtest_date(self, date_str: str) -> Dict:
        """Backtest a single date"""
        print(f"\n{'='*80}")
        print(f"📅 Backtesting {date_str}")
        print(f"{'='*80}")

        # Fetch historical matches from FootyStats
        try:
            historical_matches = self.footystats.get_matches_by_date(date_str)
        except Exception as e:
            print(f"❌ Error fetching matches: {e}")
            return {
                'date': date_str,
                'bets': 0,
                'wins': 0,
                'losses': 0,
                'profit': 0,
                'roi': 0,
                'bankroll': self.bankroll
            }

        if not historical_matches:
            print(f"⚠️  No matches found for {date_str}")
            return {
                'date': date_str,
                'bets': 0,
                'wins': 0,
                'losses': 0,
                'profit': 0,
                'roi': 0,
                'bankroll': self.bankroll
            }

        # Convert historical matches to the format expected by the generator
        # Create match data in the format expected by predict_match()
        predictions = []
        for match in historical_matches:
            match_data = {
                'id': f"{match['home_team']}_{match['away_team']}",
                'home_name': match['home_team'],
                'away_name': match['away_team'],
                'league_name': match['league'],
                'league_country': match['country'],
                'date': match['date'],
                'time': match['time'],
                'odds_ft_1': match['odds']['home_odds'],
                'odds_ft_x': match['odds']['draw_odds'],
                'odds_ft_2': match['odds']['away_odds'],
                'over_25': match['odds'].get('over_2_5_odds', 1.9),
                'under_25': match['odds'].get('under_2_5_odds', 1.9),
                'btts_yes': match['odds'].get('btts_yes_odds', 1.8),
                'btts_no': match['odds'].get('btts_no_odds', 1.9),
            }

            # Generate predictions for this match
            result = self.generator.predict_match(match_data)
            if result and result.get('predictions'):
                for pred in result['predictions']:
                    predictions.append({
                        'home_team': match['home_team'],
                        'away_team': match['away_team'],
                        'league': match['league'],
                        'country': match['country'],
                        'date': match['date'],
                        'time': match['time'],
                        'market': pred['market'],
                        'selection': pred['selection'],
                        'odds': pred['odds'],
                        'confidence': pred['confidence'],
                        'kelly_stake': pred['kelly_stake'],
                        'expected_value': (pred['confidence'] * pred['odds']) - 1
                    })

        if not predictions:
            print(f"⚠️  No bets generated for {date_str}")
            return {
                'date': date_str,
                'bets': 0,
                'wins': 0,
                'losses': 0,
                'profit': 0,
                'roi': 0,
                'bankroll': self.bankroll
            }

        # Convert predictions to DataFrame
        df = pd.DataFrame(predictions)

        # Apply quality filters (same as production)
        df = df[df['odds'] >= 1.50].copy()  # Min odds filter
        df['match_key'] = df['home_team'] + ' vs ' + df['away_team']
        df = df.sort_values('expected_value', ascending=False).groupby('match_key').first().reset_index()
        df = df.sort_values('expected_value', ascending=False).head(10)  # Top 10
        df = df.drop(columns=['match_key'], errors='ignore')

        if df.empty:
            print(f"⚠️  No bets passed quality filters for {date_str}")
            return {
                'date': date_str,
                'bets': 0,
                'wins': 0,
                'losses': 0,
                'profit': 0,
                'roi': 0,
                'bankroll': self.bankroll
            }

        print(f"\n📊 Generated {len(df)} bets for {date_str}")

        # Evaluate each prediction against actual results
        wins = 0
        losses = 0
        daily_profit = 0

        for idx, row in df.iterrows():
            home_team = row['home_team']
            away_team = row['away_team']

            # Find matching historical result
            actual_match = None
            for match in historical_matches:
                if match['home_team'] == home_team and match['away_team'] == away_team:
                    actual_match = match
                    break

            if not actual_match:
                print(f"   ⚠️  Could not find result for {home_team} vs {away_team}")
                continue

            # Evaluate prediction
            prediction = {
                'market': row['market'],
                'selection': row['selection'],
                'odds': row['odds']
            }

            is_correct = self.evaluate_prediction(prediction, actual_match)

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

            print(f"   {result_symbol} {home_team} vs {away_team}")
            print(f"      {row['market']} @ {row['odds']:.2f} | Stake: ${stake_amount:.2f} | Profit: ${profit:.2f}")
            print(f"      Actual: {actual_match['home_score']}-{actual_match['away_score']} ({actual_match['outcome']})")

            # Store individual bet result
            self.results.append({
                'date': date_str,
                'home_team': home_team,
                'away_team': away_team,
                'league': actual_match['league'],
                'market': row['market'],
                'selection': row['selection'],
                'odds': row['odds'],
                'confidence': row['confidence'],
                'stake_pct': stake_pct,
                'stake_amount': stake_amount,
                'actual_score': f"{actual_match['home_score']}-{actual_match['away_score']}",
                'actual_result': actual_match['outcome'],
                'correct': is_correct,
                'profit': profit,
                'bankroll_before': self.bankroll,
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
            'profit': daily_profit,
            'roi': roi,
            'bankroll': self.bankroll,
            'win_rate': win_rate
        }

        self.daily_results.append(daily_summary)

        print(f"\n📊 Daily Summary:")
        print(f"   Bets: {total_bets} | Wins: {wins} | Losses: {losses}")
        print(f"   Win Rate: {win_rate:.1f}%")
        print(f"   Daily P/L: ${daily_profit:.2f} | ROI: {roi:.1f}%")
        print(f"   Bankroll: ${self.bankroll:.2f}")

        return daily_summary

    def run_backtest(self):
        """Run backtest for entire date range"""
        print(f"\n{'='*80}")
        print(f"⚽ SOCCER BETTING BACKTEST (FootyStats API)")
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

            # Rate limiting - FootyStats has 1800 requests/hour = 0.5s between requests
            time.sleep(0.6)

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

        # League-specific performance
        print(f"\n📊 Performance by League:")
        league_stats = results_df.groupby('league').agg({
            'correct': ['count', 'sum', 'mean'],
            'profit': 'sum'
        }).round(2)

        for league in league_stats.index:
            count = league_stats.loc[league, ('correct', 'count')]
            wins = league_stats.loc[league, ('correct', 'sum')]
            win_rate = league_stats.loc[league, ('correct', 'mean')] * 100
            profit = league_stats.loc[league, ('profit', 'sum')]

            print(f"   {league}: {int(count)} bets | {int(wins)} wins | {win_rate:.1f}% | ${profit:.2f}")

        # Save detailed results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f'footystats_backtest_detailed_{timestamp}.csv'
        results_df.to_csv(results_file, index=False)
        print(f"\n✅ Detailed results saved to: {results_file}")

        # Save daily summary
        daily_df = pd.DataFrame(self.daily_results)
        daily_file = f'footystats_backtest_daily_{timestamp}.csv'
        daily_df.to_csv(daily_file, index=False)
        print(f"✅ Daily summary saved to: {daily_file}")

        # Plot bankroll growth (if matplotlib available)
        try:
            import matplotlib.pyplot as plt

            plt.figure(figsize=(14, 7))

            # Bankroll growth chart
            plt.subplot(1, 2, 1)
            plt.plot(daily_df['date'], daily_df['bankroll'], marker='o', linewidth=2, color='#2ecc71')
            plt.axhline(y=self.initial_bankroll, color='r', linestyle='--', label='Initial Bankroll', linewidth=1.5)
            plt.title('Bankroll Growth Over Time', fontsize=14, fontweight='bold')
            plt.xlabel('Date', fontsize=11)
            plt.ylabel('Bankroll ($)', fontsize=11)
            plt.xticks(rotation=45, ha='right')
            plt.grid(True, alpha=0.3)
            plt.legend()

            # Win rate chart
            plt.subplot(1, 2, 2)
            plt.plot(daily_df['date'], daily_df['win_rate'], marker='s', linewidth=2, color='#3498db')
            plt.axhline(y=50, color='orange', linestyle='--', label='Break-even (50%)', linewidth=1.5)
            plt.title('Daily Win Rate', fontsize=14, fontweight='bold')
            plt.xlabel('Date', fontsize=11)
            plt.ylabel('Win Rate (%)', fontsize=11)
            plt.xticks(rotation=45, ha='right')
            plt.grid(True, alpha=0.3)
            plt.legend()

            plt.tight_layout()

            chart_file = f'footystats_backtest_charts_{timestamp}.png'
            plt.savefig(chart_file, dpi=150, bbox_inches='tight')
            print(f"✅ Charts saved to: {chart_file}")

        except ImportError:
            print("⚠️  matplotlib not available - skipping chart generation")


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Backtest soccer betting system with FootyStats')
    parser.add_argument('--start-date', default='2024-08-01',
                       help='Start date (YYYY-MM-DD) - use 2024 dates!')
    parser.add_argument('--end-date', default='2024-10-17',
                       help='End date (YYYY-MM-DD) - use 2024 dates!')

    args = parser.parse_args()

    # Validate dates are in 2024 (season covered by FootyStats)
    start_year = int(args.start_date.split('-')[0])
    end_year = int(args.end_date.split('-')[0])

    if start_year != 2024 or end_year != 2024:
        print("⚠️  WARNING: FootyStats season IDs are configured for 2024/2025 season")
        print("   Dates should be in 2024 (Aug 1, 2024 - Dec 31, 2024)")
        print(f"   You specified: {args.start_date} to {args.end_date}")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)

    try:
        backtester = FootyStatsBacktester(args.start_date, args.end_date)
        backtester.run_backtest()

    except Exception as e:
        print(f"\n❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
