#!/usr/bin/env python3
"""
NHL Bet Recommendations Generator with Team Totals
Creates focused report including team totals betting opportunities
"""

import pandas as pd
import numpy as np
import pickle
from datetime import datetime
import argparse
import sys
import os
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nhl_trainer_with_totals_b2b_splits import NHLTrainerWithTotalsB2BSplits


class BetRecommendationsWithTotals:
    """Generate bet recommendations including team totals"""

    def __init__(self, min_edge: float = 0.10, min_confidence: float = 0.62,
                 hockey_api_key: str = "960c628e1c91c4b1f125e1eec52ad862"):
        self.min_edge = min_edge
        self.min_confidence = min_confidence
        self.hockey_api_key = hockey_api_key
        self.base_url = "https://v1.hockey.api-sports.io"
        self.headers = {'x-apisports-key': hockey_api_key}

        # Load models
        self.load_models()

        # Initialize trainer for data functions
        self.trainer = NHLTrainerWithTotalsB2BSplits()

    def load_models(self):
        """Load trained models with totals"""
        try:
            with open('nhl_models_with_totals_b2b_splits.pkl', 'rb') as f:
                data = pickle.load(f)

            self.models = data['models']
            self.scaler = data['scaler']
            self.feature_names = data['feature_names']
            print(f"✅ Loaded {len(self.models)} models with team totals")
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            self.models = None

    def get_todays_games(self, date_str: str = None):
        """Fetch today's NHL games"""

        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')

        url = f"{self.base_url}/games"
        params = {'league': 57, 'season': 2024, 'date': date_str}

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data.get('response', [])
        except Exception as e:
            print(f"Error fetching games: {e}")

        return []

    def generate_recommendations(self, date_str: str = None) -> pd.DataFrame:
        """Generate filtered bet recommendations with team totals"""

        if self.models is None:
            print("❌ Models not loaded")
            return pd.DataFrame()

        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')

        # Get today's games
        games = self.get_todays_games(date_str)

        if not games:
            print(f"No games found for {date_str}")
            return pd.DataFrame()

        recommendations = []

        for game in games:
            teams = game.get('teams', {})
            home_team = teams.get('home', {}).get('name', '')
            away_team = teams.get('away', {}).get('name', '')
            game_time = game.get('date', '')

            if not home_team or not away_team:
                continue

            # Build features
            features_dict = self.trainer.data_integrator.build_enhanced_features(
                home_team,
                away_team,
                2.0,  # Default odds
                2.0,
                season=2024
            )

            if not features_dict:
                continue

            # Add back-to-back features
            home_days_rest = self.trainer.get_days_since_last_game(home_team, game_time, 2024)
            away_days_rest = self.trainer.get_days_since_last_game(away_team, game_time, 2024)

            features_dict['home_days_rest'] = home_days_rest
            features_dict['away_days_rest'] = away_days_rest
            features_dict['home_b2b'] = 1 if home_days_rest == 0 else 0
            features_dict['away_b2b'] = 1 if away_days_rest == 0 else 0
            features_dict['rest_differential'] = home_days_rest - away_days_rest

            # Convert to array and scale
            X = np.array([list(features_dict.values())])
            X_scaled = self.scaler.transform(X)

            # Make predictions for all markets
            predictions = self._make_predictions(X_scaled, home_team, away_team,
                                                home_days_rest, away_days_rest)

            # Check each prediction for betting opportunities
            bets_found = self._check_betting_opportunities(
                predictions, home_team, away_team, date_str, game_time
            )

            recommendations.extend(bets_found)

        if not recommendations:
            return pd.DataFrame()

        df_recs = pd.DataFrame(recommendations)

        # Sort by edge
        df_recs['Edge_Numeric'] = df_recs['Edge'].str.strip('%').str.strip('+').astype(float)
        df_recs = df_recs.sort_values('Edge_Numeric', ascending=False)
        df_recs = df_recs.drop('Edge_Numeric', axis=1)

        return df_recs

    def _make_predictions(self, X_scaled, home_team, away_team, home_rest, away_rest):
        """Make predictions for all betting markets"""

        preds = {}

        # Game Winner
        rf_win = self.models['rf_winner'].predict_proba(X_scaled)[0][1]
        gb_win = self.models['gb_winner'].predict_proba(X_scaled)[0][1]
        preds['home_win_prob'] = (rf_win + gb_win) / 2

        # Home Team Totals
        rf_h25 = self.models['rf_home_over_2_5'].predict_proba(X_scaled)[0][1]
        gb_h25 = self.models['gb_home_over_2_5'].predict_proba(X_scaled)[0][1]
        preds['home_over_2_5_prob'] = (rf_h25 + gb_h25) / 2

        rf_h35 = self.models['rf_home_over_3_5'].predict_proba(X_scaled)[0][1]
        gb_h35 = self.models['gb_home_over_3_5'].predict_proba(X_scaled)[0][1]
        preds['home_over_3_5_prob'] = (rf_h35 + gb_h35) / 2

        # Away Team Totals
        rf_a25 = self.models['rf_away_over_2_5'].predict_proba(X_scaled)[0][1]
        gb_a25 = self.models['gb_away_over_2_5'].predict_proba(X_scaled)[0][1]
        preds['away_over_2_5_prob'] = (rf_a25 + gb_a25) / 2

        rf_a35 = self.models['rf_away_over_3_5'].predict_proba(X_scaled)[0][1]
        gb_a35 = self.models['gb_away_over_3_5'].predict_proba(X_scaled)[0][1]
        preds['away_over_3_5_prob'] = (rf_a35 + gb_a35) / 2

        # Store team info and rest
        preds['home_team'] = home_team
        preds['away_team'] = away_team
        preds['home_rest'] = home_rest
        preds['away_rest'] = away_rest

        return preds

    def _check_betting_opportunities(self, preds, home_team, away_team, date_str, game_time):
        """Check all predictions for betting opportunities"""

        bets = []
        game_str = f"{away_team} @ {home_team}"

        # Default odds (would need to fetch real odds)
        default_ml_odds = 1.90
        default_total_odds = 1.90

        # Check Home Team O/U 2.5
        h25_prob = preds['home_over_2_5_prob']
        h25_edge = self._calculate_edge(h25_prob, default_total_odds)

        if abs(h25_edge) >= self.min_edge:
            bet_confidence = h25_prob if h25_edge > 0 else (1 - h25_prob)
            if bet_confidence >= self.min_confidence:
                pick = 'Over' if h25_edge > 0 else 'Under'
                reason = f"{home_team} {pick} 2.5 goals"
                if preds['home_rest'] == 0:
                    reason += " (⚠️ Team on back-to-back)"

                bets.append({
                    'Game': game_str,
                    'Date': date_str,
                    'Time': game_time[:10] if len(game_time) > 10 else game_time,
                    'Bet_Type': f'{home_team} {pick} 2.5',
                    'Pick': f'{pick} 2.5',
                    'Odds': default_total_odds,
                    'Confidence': f'{bet_confidence*100:.1f}%',
                    'Edge': f'{abs(h25_edge)*100:+.1f}%',
                    'Recommended_Unit': self._calculate_units(abs(h25_edge), bet_confidence),
                    'Reason': reason
                })

        # Check Home Team O/U 3.5
        h35_prob = preds['home_over_3_5_prob']
        h35_edge = self._calculate_edge(h35_prob, default_total_odds)

        if abs(h35_edge) >= self.min_edge:
            bet_confidence = h35_prob if h35_edge > 0 else (1 - h35_prob)
            if bet_confidence >= self.min_confidence:
                pick = 'Over' if h35_edge > 0 else 'Under'
                reason = f"{home_team} {pick} 3.5 goals"
                if preds['home_rest'] == 0:
                    reason += " (⚠️ Team on back-to-back)"

                bets.append({
                    'Game': game_str,
                    'Date': date_str,
                    'Time': game_time[:10] if len(game_time) > 10 else game_time,
                    'Bet_Type': f'{home_team} {pick} 3.5',
                    'Pick': f'{pick} 3.5',
                    'Odds': default_total_odds,
                    'Confidence': f'{bet_confidence*100:.1f}%',
                    'Edge': f'{abs(h35_edge)*100:+.1f}%',
                    'Recommended_Unit': self._calculate_units(abs(h35_edge), bet_confidence),
                    'Reason': reason
                })

        # Check Away Team O/U 2.5
        a25_prob = preds['away_over_2_5_prob']
        a25_edge = self._calculate_edge(a25_prob, default_total_odds)

        if abs(a25_edge) >= self.min_edge:
            bet_confidence = a25_prob if a25_edge > 0 else (1 - a25_prob)
            if bet_confidence >= self.min_confidence:
                pick = 'Over' if a25_edge > 0 else 'Under'
                reason = f"{away_team} {pick} 2.5 goals"
                if preds['away_rest'] == 0:
                    reason += " (⚠️ Team on back-to-back)"

                bets.append({
                    'Game': game_str,
                    'Date': date_str,
                    'Time': game_time[:10] if len(game_time) > 10 else game_time,
                    'Bet_Type': f'{away_team} {pick} 2.5',
                    'Pick': f'{pick} 2.5',
                    'Odds': default_total_odds,
                    'Confidence': f'{bet_confidence*100:.1f}%',
                    'Edge': f'{abs(a25_edge)*100:+.1f}%',
                    'Recommended_Unit': self._calculate_units(abs(a25_edge), bet_confidence),
                    'Reason': reason
                })

        # Check Away Team O/U 3.5
        a35_prob = preds['away_over_3_5_prob']
        a35_edge = self._calculate_edge(a35_prob, default_total_odds)

        if abs(a35_edge) >= self.min_edge:
            bet_confidence = a35_prob if a35_edge > 0 else (1 - a35_prob)
            if bet_confidence >= self.min_confidence:
                pick = 'Over' if a35_edge > 0 else 'Under'
                reason = f"{away_team} {pick} 3.5 goals"
                if preds['away_rest'] == 0:
                    reason += " (⚠️ Team on back-to-back)"

                bets.append({
                    'Game': game_str,
                    'Date': date_str,
                    'Time': game_time[:10] if len(game_time) > 10 else game_time,
                    'Bet_Type': f'{away_team} {pick} 3.5',
                    'Pick': f'{pick} 3.5',
                    'Odds': default_total_odds,
                    'Confidence': f'{bet_confidence*100:.1f}%',
                    'Edge': f'{abs(a35_edge)*100:+.1f}%',
                    'Recommended_Unit': self._calculate_units(abs(a35_edge), bet_confidence),
                    'Reason': reason
                })

        # Check Moneyline
        win_prob = preds['home_win_prob']
        ml_edge = self._calculate_edge(win_prob, default_ml_odds)

        if abs(ml_edge) >= self.min_edge:
            bet_confidence = win_prob if ml_edge > 0 else (1 - win_prob)
            if bet_confidence >= self.min_confidence:
                winner = home_team if ml_edge > 0 else away_team
                reason = f"{winner} to win"

                # Add rest analysis
                if preds['home_rest'] < preds['away_rest']:
                    reason += f" ({away_team} rested, {home_team} tired)"
                elif preds['away_rest'] < preds['home_rest']:
                    reason += f" ({home_team} rested, {away_team} tired)"

                bets.append({
                    'Game': game_str,
                    'Date': date_str,
                    'Time': game_time[:10] if len(game_time) > 10 else game_time,
                    'Bet_Type': 'Moneyline',
                    'Pick': winner,
                    'Odds': default_ml_odds,
                    'Confidence': f'{bet_confidence*100:.1f}%',
                    'Edge': f'{abs(ml_edge)*100:+.1f}%',
                    'Recommended_Unit': self._calculate_units(abs(ml_edge), bet_confidence),
                    'Reason': reason
                })

        return bets

    def _calculate_edge(self, probability: float, odds: float) -> float:
        """Calculate edge: model_prob - implied_prob"""
        implied_prob = 1 / odds
        return probability - implied_prob

    def _calculate_units(self, edge: float, confidence: float) -> str:
        """Calculate recommended bet units using Kelly Criterion"""
        kelly = edge * 0.25  # Quarter Kelly for safety
        units = min(kelly * 10, 3)  # Cap at 3 units

        if units >= 2.5:
            return "🔥 3 Units (Strong)"
        elif units >= 1.5:
            return "⭐ 2 Units (Medium)"
        else:
            return "💡 1 Unit (Value)"

    def save_recommendations(self, df: pd.DataFrame, date_str: str = None):
        """Save recommendations to CSV"""

        if df.empty:
            print("✅ No bets meet recommendation criteria today")
            print(f"   Criteria: {self.min_edge*100:.0f}% min edge, {self.min_confidence*100:.0f}% min confidence")
            return

        if date_str:
            use_date = date_str
        else:
            use_date = datetime.now().strftime('%Y-%m-%d')

        # Create date-based folder structure: reports/YYYYMMDD/
        date_folder = use_date.replace('-', '')  # Convert 2025-10-17 to 20251017
        reports_dir = os.path.join('reports', date_folder)
        os.makedirs(reports_dir, exist_ok=True)

        filename = os.path.join(reports_dir, f"bet_recommendations_{use_date}.csv")

        df.to_csv(filename, index=False)

        print(f"\n✅ Bet Recommendations Saved: {filename}")
        print(f"📊 {len(df)} recommended bets (including team totals)")
        print(f"\n{'='*100}")
        print("🎯 TODAY'S BET RECOMMENDATIONS - With Team Totals & B2B Analysis")
        print(f"{'='*100}\n")

        for idx, row in df.iterrows():
            print(f"🏒 BET #{idx+1}: {row['Game']}")
            print(f"   ⏰ {row['Date']} {row['Time']}")
            print(f"   🎲 {row['Bet_Type']}: {row['Pick']}")
            print(f"   💰 Odds: {row['Odds']} | Edge: {row['Edge']}")
            print(f"   📊 Confidence: {row['Confidence']}")
            print(f"   💵 Bet Size: {row['Recommended_Unit']}")
            print(f"   📝 {row['Reason']}")
            print()


def main():
    parser = argparse.ArgumentParser(description='Generate NHL bet recommendations with team totals')
    parser.add_argument('--date', type=str,
                       help='Date in YYYY-MM-DD format (default: today)')
    parser.add_argument('--min-edge', type=float, default=0.10,
                       help='Minimum edge threshold (default: 0.10 = 10%%)')
    parser.add_argument('--min-confidence', type=float, default=0.62,
                       help='Minimum confidence threshold (default: 0.62 = 62%%)')

    args = parser.parse_args()

    print("🏒 NHL BET RECOMMENDATIONS GENERATOR - With Team Totals & B2B Tracking")
    print("=" * 100)
    print(f"Criteria: Min Edge {args.min_edge*100:.0f}% | Min Confidence {args.min_confidence*100:.0f}%")
    print("=" * 100)

    recommender = BetRecommendationsWithTotals(
        min_edge=args.min_edge,
        min_confidence=args.min_confidence
    )

    df_recommendations = recommender.generate_recommendations(args.date)
    recommender.save_recommendations(df_recommendations, args.date)


if __name__ == "__main__":
    main()
