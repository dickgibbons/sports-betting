#!/usr/bin/env python3
"""
Historical Soccer Backtesting - Test Form-Enhanced Models on 2024 Completed Matches

Backtest the form-enhanced soccer betting system on August-October 2024 data
to evaluate performance improvements from Phase 2 team form features.

Usage:
    python3 backtest_historical_2024.py --start-date 2024-08-15 --end-date 2024-10-17
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

# Bankroll settings
INITIAL_BANKROLL = 1000.0
KELLY_FRACTION = 0.25
MAX_BET_SIZE = 0.05


class HistoricalBacktester:
    """Backtest form-enhanced models on 2024 historical data"""

    def __init__(self, start_date: str, end_date: str):
        """Initialize backtester with date range"""
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d')
        self.generator = SoccerBestBetsGenerator()
        self.bankroll = INITIAL_BANKROLL
        self.initial_bankroll = INITIAL_BANKROLL
        self.results = []
        self.daily_results = []

    def fetch_completed_matches(self, date_str: str) -> List[Dict]:
        """Fetch COMPLETED matches (status='FT') for a historical date"""
        print(f"📊 Fetching completed matches for {date_str}...")

        all_matches = []
        headers = {'x-apisports-key': API_KEY}

        # Get top tier leagues only
        top_leagues = self.generator.leagues[self.generator.leagues['tier'] <= 1]

        for _, league in top_leagues.iterrows():
            league_id = league['league_id']

            try:
                # Determine season
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                season = date_obj.year if date_obj.month >= 8 else date_obj.year - 1

                url = f"{API_BASE}/fixtures"
                params = {
                    'league': league_id,
                    'date': date_str,
                    'season': season
                }

                response = requests.get(url, params=params, headers=headers, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    fixtures = data.get('response', [])

                    completed_matches = 0
                    for fixture in fixtures:
                        fixture_data = fixture.get('fixture', {})
                        status = fixture_data.get('status', {}).get('short', '')

                        # ONLY COMPLETED MATCHES (FT = Full Time)
                        if status == 'FT':
                            fixture_id = fixture_data.get('id')

                            # Get match result
                            goals = fixture.get('goals', {})
                            home_goals = goals.get('home', 0)
                            away_goals = goals.get('away', 0)

                            # Get halftime score
                            score = fixture.get('score', {})
                            halftime = score.get('halftime', {})
                            h1_home_goals = halftime.get('home', 0) if halftime else 0
                            h1_away_goals = halftime.get('away', 0) if halftime else 0

                            # Fetch odds for this fixture (historical odds)
                            odds_data = self.generator.fetch_odds_for_fixture(fixture_id, headers)

                            # Store match data
                            match = {
                                'id': fixture_id,
                                'date': fixture_data.get('date'),
                                'home_name': fixture.get('teams', {}).get('home', {}).get('name', 'Unknown'),
                                'away_name': fixture.get('teams', {}).get('away', {}).get('name', 'Unknown'),
                                'home_team_id': fixture.get('teams', {}).get('home', {}).get('id'),
                                'away_team_id': fixture.get('teams', {}).get('away', {}).get('id'),
                                'league_name': league['league_name'],
                                'league_id': league_id,
                                'league_country': league['country'],
                                'league_tier': league['tier'],
                                'season': season,
                                # Actual result
                                'home_goals': home_goals,
                                'away_goals': away_goals,
                                'total_goals': home_goals + away_goals,
                                'result': 'Home' if home_goals > away_goals else ('Away' if away_goals > home_goals else 'Draw'),
                                'btts': home_goals > 0 and away_goals > 0,
                                'h1_home_goals': h1_home_goals,
                                'h1_away_goals': h1_away_goals,
                                'h1_goals': (h1_home_goals or 0) + (h1_away_goals or 0)
                            }

                            # Add odds data
                            match.update(odds_data)

                            all_matches.append(match)
                            completed_matches += 1

                    if completed_matches > 0:
                        print(f"   ✅ {league['league_name']}: {completed_matches} completed matches")

                # Rate limiting
                time.sleep(0.5)

            except Exception as e:
                print(f"   ⚠️  Error fetching {league['league_name']}: {e}")
                continue

        print(f"📊 Total completed matches found: {len(all_matches)}")
        return all_matches

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

        # H1 predictions
        elif 'H1 Over 0.5' in market:
            return actual_result.get('h1_goals', 0) > 0.5
        elif 'H1 Under 0.5' in market:
            return actual_result.get('h1_goals', 0) < 0.5
        elif 'H1 Over 1.5' in market:
            return actual_result.get('h1_goals', 0) > 1.5
        elif 'H1 Under 1.5' in market:
            return actual_result.get('h1_goals', 0) < 0.5

        return False

    def backtest_date(self, date_str: str) -> Dict:
        """Backtest a single date with form-enhanced models"""
        print(f"\n{'='*80}")
        print(f"📅 Backtesting {date_str}")
        print(f"{'='*80}")

        # Fetch completed matches for this date
        matches = self.fetch_completed_matches(date_str)

        if not matches:
            print(f"⚠️  No completed matches for {date_str}")
            return {
                'date': date_str,
                'bets': 0,
                'wins': 0,
                'losses': 0,
                'profit': 0,
                'roi': 0,
                'bankroll': self.bankroll
            }

        # Generate predictions for each match
        wins = 0
        losses = 0
        daily_profit = 0
        bets_made = 0

        for match in matches:
            # Generate prediction using form-enhanced model
            result = self.generator.predict_match(match)

            if result and result['predictions']:
                for pred in result['predictions']:
                    # Evaluate prediction
                    is_correct = self.evaluate_prediction(pred, match)

                    # Calculate profit/loss
                    stake_pct = pred['kelly_stake']
                    stake_amount = self.bankroll * stake_pct

                    if is_correct:
                        profit = stake_amount * (pred['odds'] - 1)
                        daily_profit += profit
                        wins += 1
                        result_symbol = "✅"
                    else:
                        profit = -stake_amount
                        daily_profit += profit
                        losses += 1
                        result_symbol = "❌"

                    print(f"   {result_symbol} {match['home_name']} vs {match['away_name']} | {pred['market']} @ {pred['odds']:.2f} | Profit: ${profit:.2f}")

                    bets_made += 1

                    # Store bet result
                    self.results.append({
                        'date': date_str,
                        'league': match['league_name'],
                        'home_team': match['home_name'],
                        'away_team': match['away_name'],
                        'market': pred['market'],
                        'selection': pred['selection'],
                        'odds': pred['odds'],
                        'confidence': pred['confidence'],
                        'stake_pct': stake_pct,
                        'stake_amount': stake_amount,
                        'actual_result': match['result'],
                        'actual_score': f"{match['home_goals']}-{match['away_goals']}",
                        'correct': is_correct,
                        'profit': profit,
                        'bankroll_after': self.bankroll + daily_profit
                    })

        # Update bankroll
        self.bankroll += daily_profit

        # Daily summary
        win_rate = (wins / bets_made * 100) if bets_made > 0 else 0
        roi = (daily_profit / (self.bankroll - daily_profit) * 100) if (self.bankroll - daily_profit) > 0 else 0

        daily_summary = {
            'date': date_str,
            'bets': bets_made,
            'wins': wins,
            'losses': losses,
            'profit': daily_profit,
            'roi': roi,
            'bankroll': self.bankroll,
            'win_rate': win_rate
        }

        self.daily_results.append(daily_summary)

        if bets_made > 0:
            print(f"\n📊 Daily Summary:")
            print(f"   Bets: {bets_made} | Wins: {wins} | Losses: {losses}")
            print(f"   Daily P/L: ${daily_profit:.2f} | ROI: {roi:.1f}%")
            print(f"   Bankroll: ${self.bankroll:.2f}")

        return daily_summary

    def run_backtest(self):
        """Run backtest for entire date range"""
        print(f"\n{'='*80}")
        print(f"⚽ HISTORICAL BACKTEST - FORM-ENHANCED MODELS (Phase 2)")
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

            # Rate limiting
            time.sleep(2)

        # Generate final report
        self.generate_report()

    def generate_report(self):
        """Generate comprehensive backtest report"""
        print(f"\n{'='*80}")
        print(f"📊 BACKTEST RESULTS - FORM-ENHANCED MODELS")
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

            print(f"   {market}: {int(count)} bets | {int(wins)} wins | {win_rate:.1f}% WR | ${profit:.2f}")

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

            print(f"   {league}: {int(count)} bets | {int(wins)} wins | {win_rate:.1f}% WR | ${profit:.2f}")

        # Save detailed results
        results_file = 'backtest_2024_detailed.csv'
        results_df.to_csv(results_file, index=False)
        print(f"\n✅ Detailed results saved to: {results_file}")

        # Save daily summary
        daily_df = pd.DataFrame(self.daily_results)
        daily_file = 'backtest_2024_daily.csv'
        daily_df.to_csv(daily_file, index=False)
        print(f"✅ Daily summary saved to: {daily_file}")


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Backtest form-enhanced models on 2024 data')
    parser.add_argument('--start-date', default='2024-08-15',
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', default='2024-10-17',
                       help='End date (YYYY-MM-DD)')

    args = parser.parse_args()

    try:
        backtester = HistoricalBacktester(args.start_date, args.end_date)
        backtester.run_backtest()

    except Exception as e:
        print(f"\n❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
