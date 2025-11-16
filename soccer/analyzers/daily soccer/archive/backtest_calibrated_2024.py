#!/usr/bin/env python3
"""
Historical Soccer Backtesting - RELAXED SETTINGS for Model Evaluation

Test form-enhanced models with relaxed confidence thresholds to evaluate
actual model performance without strict production filters.

Usage:
    python3 backtest_historical_2024_relaxed.py --start-date 2024-08-15 --end-date 2024-10-17
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

# Temporarily modify the production settings for testing
os.environ['BACKTEST_MODE'] = '1'

# Import the betting generator class
from soccer_best_bets_daily import SoccerBestBetsGenerator

# API Configuration
API_KEY = "960c628e1c91c4b1f125e1eec52ad862"
API_BASE = "https://v3.football.api-sports.io"

# RELAXED thresholds for testing model performance
MIN_CONFIDENCE = 0.60  # 60% instead of 99%
MIN_TOTALS_CONFIDENCE = 0.60  # 60% instead of 99%
MIN_BTTS_CONFIDENCE = 0.60  # 60% instead of 98.5%

# Bankroll settings
INITIAL_BANKROLL = 1000.0
KELLY_FRACTION = 0.25
MAX_BET_SIZE = 0.05


class RelaxedBacktester:
    """Backtest with relaxed settings to evaluate model performance"""

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

    def predict_match_relaxed(self, match: Dict) -> Optional[Dict]:
        """Predict match with RELAXED thresholds (no league filters)"""
        if self.generator.models is None:
            return None

        # REMOVE league blacklist for testing
        feature_dict = self.generator.extract_features(match)
        if feature_dict is None:
            return None

        try:
            odds = feature_dict['odds_data']
            predictions = []

            # Check if form features are available
            has_form_features = (feature_dict.get('home_form') is not None and
                               feature_dict.get('away_form') is not None)

            # Create feature vector (with or without form)
            if has_form_features:
                match_features = self.generator.create_features_with_form(
                    odds, feature_dict['home_form'], feature_dict['away_form']
                )
            else:
                match_features = self.generator.create_features_from_odds(odds)

            # Scale features
            if self.generator.scaler is not None:
                match_features_scaled = self.generator.scaler.transform(match_features)
            else:
                match_features_scaled = match_features

            # Match Outcome predictions
            if 'rf_match_outcome' in self.generator.models and 'gb_match_outcome' in self.generator.models:
                rf_probs = self.generator.models['rf_match_outcome'].predict_proba(match_features_scaled)[0]
                gb_probs = self.generator.models['gb_match_outcome'].predict_proba(match_features_scaled)[0]
                match_probs = (rf_probs + gb_probs) / 2

                if len(match_probs) == 3:
                    away_prob = match_probs[0]
                    draw_prob = match_probs[1]
                    home_prob = match_probs[2]

                    # Home win (RELAXED 60% threshold)
                    if home_prob >= MIN_CONFIDENCE:
                        kelly = self.generator.calculate_kelly(home_prob, odds['home_odds'])
                        if kelly > 0:
                            predictions.append({
                                'market': 'Home Win',
                                'selection': match.get('home_name', 'Home'),
                                'odds': odds['home_odds'],
                                'confidence': home_prob,
                                'kelly_stake': kelly,
                                'market_type': 'winner'
                            })

                    # Draw
                    if draw_prob >= MIN_CONFIDENCE:
                        kelly = self.generator.calculate_kelly(draw_prob, odds['draw_odds'])
                        if kelly > 0:
                            predictions.append({
                                'market': 'Draw',
                                'selection': 'Draw',
                                'odds': odds['draw_odds'],
                                'confidence': draw_prob,
                                'kelly_stake': kelly,
                                'market_type': 'winner'
                            })

                    # Away win
                    if away_prob >= MIN_CONFIDENCE:
                        kelly = self.generator.calculate_kelly(away_prob, odds['away_odds'])
                        if kelly > 0:
                            predictions.append({
                                'market': 'Away Win',
                                'selection': match.get('away_name', 'Away'),
                                'odds': odds['away_odds'],
                                'confidence': away_prob,
                                'kelly_stake': kelly,
                                'market_type': 'winner'
                            })

            # Over/Under 2.5
            if 'rf_over_2_5' in self.generator.models and 'gb_over_2_5' in self.generator.models:
                rf_probs = self.generator.models['rf_over_2_5'].predict_proba(match_features_scaled)[0]
                gb_probs = self.generator.models['gb_over_2_5'].predict_proba(match_features_scaled)[0]
                ou_probs = (rf_probs + gb_probs) / 2

                if len(ou_probs) == 2:
                    under_prob = ou_probs[0]
                    over_prob = ou_probs[1]

                    if over_prob >= MIN_TOTALS_CONFIDENCE:
                        kelly = self.generator.calculate_kelly(over_prob, odds['over_25'])
                        if kelly > 0:
                            predictions.append({
                                'market': 'Over 2.5',
                                'selection': 'Over 2.5 Goals',
                                'odds': odds['over_25'],
                                'confidence': over_prob,
                                'kelly_stake': kelly,
                                'market_type': 'totals'
                            })

                    if under_prob >= MIN_TOTALS_CONFIDENCE:
                        kelly = self.generator.calculate_kelly(under_prob, odds['under_25'])
                        if kelly > 0:
                            predictions.append({
                                'market': 'Under 2.5',
                                'selection': 'Under 2.5 Goals',
                                'odds': odds['under_25'],
                                'confidence': under_prob,
                                'kelly_stake': kelly,
                                'market_type': 'totals'
                            })

            # BTTS (NO WHITELIST)
            if 'rf_btts' in self.generator.models and 'gb_btts' in self.generator.models:
                rf_probs = self.generator.models['rf_btts'].predict_proba(match_features_scaled)[0]
                gb_probs = self.generator.models['gb_btts'].predict_proba(match_features_scaled)[0]
                btts_probs = (rf_probs + gb_probs) / 2

                if len(btts_probs) == 2:
                    btts_no_prob = btts_probs[0]
                    btts_yes_prob = btts_probs[1]

                    if btts_yes_prob >= MIN_BTTS_CONFIDENCE:
                        kelly = self.generator.calculate_kelly(btts_yes_prob, odds['btts_yes'])
                        if kelly > 0:
                            predictions.append({
                                'market': 'BTTS Yes',
                                'selection': 'Both Teams Score',
                                'odds': odds['btts_yes'],
                                'confidence': btts_yes_prob,
                                'kelly_stake': kelly,
                                'market_type': 'btts'
                            })

                    if btts_no_prob >= MIN_BTTS_CONFIDENCE:
                        kelly = self.generator.calculate_kelly(btts_no_prob, odds['btts_no'])
                        if kelly > 0:
                            predictions.append({
                                'market': 'BTTS No',
                                'selection': 'Not Both Teams Score',
                                'odds': odds['btts_no'],
                                'confidence': btts_no_prob,
                                'kelly_stake': kelly,
                                'market_type': 'btts'
                            })

            if predictions:
                return {
                    'match': match,
                    'predictions': predictions
                }

            return None

        except Exception as e:
            print(f"   ⚠️  Prediction error: {e}")
            return None

    def evaluate_prediction(self, prediction: Dict, actual_result: Dict) -> bool:
        """Check if prediction was correct"""
        market = prediction['market']

        if 'Home Win' in market:
            return actual_result['result'] == 'Home'
        elif 'Away Win' in market:
            return actual_result['result'] == 'Away'
        elif market == 'Draw':
            return actual_result['result'] == 'Draw'
        elif 'Over 2.5' in market:
            return actual_result['total_goals'] > 2.5
        elif 'Under 2.5' in market:
            return actual_result['total_goals'] < 2.5
        elif 'BTTS Yes' in market:
            return actual_result['btts'] == True
        elif 'BTTS No' in market:
            return actual_result['btts'] == False

        return False

    def backtest_date(self, date_str: str) -> Dict:
        """Backtest a single date"""
        print(f"\n{'='*80}")
        print(f"📅 Backtesting {date_str}")
        print(f"{'='*80}")

        matches = self.fetch_completed_matches(date_str)

        if not matches:
            return {'date': date_str, 'bets': 0, 'wins': 0, 'losses': 0, 'profit': 0, 'roi': 0, 'bankroll': self.bankroll}

        wins = 0
        losses = 0
        daily_profit = 0
        bets_made = 0

        for match in matches:
            result = self.predict_match_relaxed(match)

            if result and result['predictions']:
                for pred in result['predictions']:
                    is_correct = self.evaluate_prediction(pred, match)

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

                    print(f"   {result_symbol} {match['home_name']} vs {match['away_name']} | {pred['market']} @ {pred['odds']:.2f} ({pred['confidence']:.1%}) | P/L: ${profit:.2f}")

                    bets_made += 1

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

        self.bankroll += daily_profit

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
            print(f"\n📊 Daily Summary: {bets_made} bets | {wins}W-{losses}L ({win_rate:.1f}%) | P/L: ${daily_profit:.2f} | Bankroll: ${self.bankroll:.2f}")

        return daily_summary

    def run_backtest(self):
        """Run backtest for entire date range"""
        print(f"\n{'='*80}")
        print(f"⚽ FORM-ENHANCED BACKTEST - RELAXED SETTINGS")
        print(f"{'='*80}")
        print(f"Start Date: {self.start_date.strftime('%Y-%m-%d')}")
        print(f"End Date: {self.end_date.strftime('%Y-%m-%d')}")
        print(f"Initial Bankroll: ${self.initial_bankroll:.2f}")
        print(f"RELAXED Thresholds: {MIN_CONFIDENCE:.0%} (ALL markets enabled, NO filters)")
        print(f"{'='*80}")

        current_date = self.start_date

        while current_date <= self.end_date:
            date_str = current_date.strftime('%Y-%m-%d')

            try:
                self.backtest_date(date_str)
            except Exception as e:
                print(f"❌ Error backtesting {date_str}: {e}")
                import traceback
                traceback.print_exc()

            current_date += timedelta(days=1)
            time.sleep(2)

        self.generate_report()

    def generate_report(self):
        """Generate comprehensive report"""
        print(f"\n{'='*80}")
        print(f"📊 BACKTEST RESULTS - FORM-ENHANCED MODELS (RELAXED)")
        print(f"{'='*80}")

        if not self.results:
            print("⚠️  No results to report")
            return

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

        results_df = pd.DataFrame(self.results)

        print(f"\n📊 Performance by Market:")
        market_stats = results_df.groupby('market').agg({
            'correct': ['count', 'sum', 'mean'],
            'profit': 'sum',
            'confidence': 'mean'
        }).round(3)

        for market in market_stats.index:
            count = market_stats.loc[market, ('correct', 'count')]
            wins = market_stats.loc[market, ('correct', 'sum')]
            win_rate = market_stats.loc[market, ('correct', 'mean')] * 100
            profit = market_stats.loc[market, ('profit', 'sum')]
            avg_conf = market_stats.loc[market, ('confidence', 'mean')] * 100

            print(f"   {market}: {int(count)} bets | {int(wins)}W | {win_rate:.1f}% WR | ${profit:.2f} | Avg Conf: {avg_conf:.1f}%")

        print(f"\n📊 Performance by League:")
        league_stats = results_df.groupby('league').agg({
            'correct': ['count', 'sum', 'mean'],
            'profit': 'sum'
        }).round(3).sort_values(('profit', 'sum'), ascending=False)

        for league in league_stats.head(10).index:
            count = league_stats.loc[league, ('correct', 'count')]
            wins = league_stats.loc[league, ('correct', 'sum')]
            win_rate = league_stats.loc[league, ('correct', 'mean')] * 100
            profit = league_stats.loc[league, ('profit', 'sum')]

            print(f"   {league}: {int(count)} bets | {int(wins)}W | {win_rate:.1f}% WR | ${profit:.2f}")

        # Save results
        results_df.to_csv('backtest_2024_relaxed_detailed.csv', index=False)
        print(f"\n✅ Detailed results saved to: backtest_2024_relaxed_detailed.csv")

        daily_df = pd.DataFrame(self.daily_results)
        daily_df.to_csv('backtest_2024_relaxed_daily.csv', index=False)
        print(f"✅ Daily summary saved to: backtest_2024_relaxed_daily.csv")


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Backtest with relaxed settings')
    parser.add_argument('--start-date', default='2024-08-15', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', default='2024-10-17', help='End date (YYYY-MM-DD)')

    args = parser.parse_args()

    try:
        backtester = RelaxedBacktester(args.start_date, args.end_date)
        backtester.run_backtest()

    except Exception as e:
        print(f"\n❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
