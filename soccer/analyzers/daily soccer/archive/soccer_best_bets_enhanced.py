#!/usr/bin/env python3
"""
Soccer Best Bets Enhanced - Using Enhanced Models with All Markets

New markets supported:
- Home Team Totals: O/U 0.5, 1.5, 2.5
- Away Team Totals: O/U 0.5, 1.5, 2.5
- First Half: O/U 0.5, 1.5
- Second Half: O/U 0.5, 1.5
- Double Chance: Home/Draw, Away/Draw, Home/Away
"""

import os
import sys
import requests
import numpy as np
import pandas as pd
import joblib
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Minimum confidence thresholds (ULTRA STRICT - top 10-20 picks per day maximum)
MIN_CONFIDENCE = 0.975  # 97.5% for match winners
MIN_TOTALS_CONFIDENCE = 0.975  # 97.5% for game totals
MIN_TEAM_TOTALS_CONFIDENCE = 0.97  # 97% for team totals
MIN_HALF_CONFIDENCE = 0.96  # 96% for half markets
MIN_DOUBLE_CHANCE_CONFIDENCE = 0.98  # 98% for double chance

# Kelly Criterion parameters
KELLY_FRACTION = 0.25  # Conservative quarter-Kelly
MAX_BET_SIZE = 0.05  # Maximum 5% of bankroll

# API Configuration
API_KEY = "960c628e1c91c4b1f125e1eec52ad862"
API_BASE = "https://v3.football.api-sports.io"


class EnhancedSoccerBetsGenerator:
    """Generate betting recommendations using enhanced models"""

    def __init__(self, model_path: str = None, use_enhanced: bool = True):
        """Initialize with enhanced models"""
        if model_path is None:
            if use_enhanced and os.path.exists(os.path.join(os.path.dirname(__file__), 'models', 'soccer_ml_models_enhanced.pkl')):
                model_path = os.path.join(os.path.dirname(__file__), 'models', 'soccer_ml_models_enhanced.pkl')
                print("🚀 Using ENHANCED models with all markets")
            else:
                model_path = os.path.join(os.path.dirname(__file__), 'models', 'soccer_ml_models.pkl')
                print("⚠️  Using standard models (enhanced models not found)")

        self.model_path = model_path
        self.models = None
        self.scaler = None
        self.feature_cols = []
        self.is_enhanced = use_enhanced

        # Load models
        self.load_models()

    def load_models(self) -> bool:
        """Load trained ML models"""
        try:
            if not os.path.exists(self.model_path):
                print(f"❌ Model file not found: {self.model_path}")
                return False

            model_data = joblib.load(self.model_path)

            if isinstance(model_data, dict):
                self.models = model_data.get('models', {})
                self.scaler = model_data.get('scaler')
                self.feature_cols = model_data.get('feature_cols', [])

                if self.models:
                    print(f"✅ Models loaded from {self.model_path}")
                    print(f"   Total models: {len(self.models)}")

                    # Group models by market
                    markets = set()
                    for key in self.models.keys():
                        # Remove 'rf_' or 'gb_' prefix
                        market = key.replace('rf_', '').replace('gb_', '')
                        markets.add(market)

                    print(f"   Markets available: {len(markets)}")
                    return True
                else:
                    print(f"❌ No models found")
                    return False
            else:
                print(f"❌ Invalid model format")
                return False

        except Exception as e:
            print(f"❌ Error loading models: {e}")
            import traceback
            traceback.print_exc()
            return False

    def create_features_from_odds(self, odds_data: dict) -> np.array:
        """Create feature vector from odds matching training format"""
        home_odds = odds_data.get('home_odds', 2.0)
        draw_odds = odds_data.get('draw_odds', 3.2)
        away_odds = odds_data.get('away_odds', 3.5)
        over_25 = odds_data.get('over_25', 1.8)
        under_25 = odds_data.get('under_25', 1.9)
        btts_yes = odds_data.get('btts_yes', 1.8)
        btts_no = odds_data.get('btts_no', 1.9)

        # Implied probabilities
        home_prob = 1 / home_odds if home_odds > 0 else 0
        draw_prob = 1 / draw_odds if draw_odds > 0 else 0
        away_prob = 1 / away_odds if away_odds > 0 else 0

        # Normalize probabilities
        total_prob = home_prob + draw_prob + away_prob
        home_prob_norm = home_prob / total_prob if total_prob > 0 else 0
        draw_prob_norm = draw_prob / total_prob if total_prob > 0 else 0
        away_prob_norm = away_prob / total_prob if total_prob > 0 else 0

        # Expected goals
        expected_total = 2.5

        # Create feature vector (must match training features)
        features = [
            home_odds,
            draw_odds,
            away_odds,
            over_25,
            under_25,
            btts_yes,
            btts_no,
            home_prob_norm,
            draw_prob_norm,
            away_prob_norm,
            expected_total,
            home_odds - away_odds,  # strength diff
            1 / (home_odds * away_odds) if (home_odds * away_odds) > 0 else 0,  # draw indicator
        ]

        return np.array([features])

    def predict_with_ensemble(self, features: np.array, market: str) -> tuple:
        """Get ensemble prediction from RF and GB models"""
        rf_key = f'rf_{market}'
        gb_key = f'gb_{market}'

        if rf_key not in self.models or gb_key not in self.models:
            return None, 0.0

        # Scale features
        features_scaled = self.scaler.transform(features)

        # Get predictions from both models
        rf_probs = self.models[rf_key].predict_proba(features_scaled)[0]
        gb_probs = self.models[gb_key].predict_proba(features_scaled)[0]

        # Ensemble (average)
        ensemble_probs = (rf_probs + gb_probs) / 2

        return ensemble_probs, max(ensemble_probs)

    def generate_predictions(self, match: dict, odds_data: dict) -> list:
        """Generate predictions for all available markets"""
        predictions = []

        # Create features
        features = self.create_features_from_odds(odds_data)

        # Match Outcome
        match_probs, conf = self.predict_with_ensemble(features, 'match_outcome')
        if match_probs is not None and len(match_probs) == 3:
            away_prob, draw_prob, home_prob = match_probs

            if home_prob >= MIN_CONFIDENCE:
                predictions.append({
                    'market': 'Home Win',
                    'selection': match['home_name'],
                    'odds': odds_data['home_odds'],
                    'confidence': home_prob,
                    'market_type': 'match_outcome'
                })

            if draw_prob >= MIN_CONFIDENCE:
                predictions.append({
                    'market': 'Draw',
                    'selection': 'Draw',
                    'odds': odds_data['draw_odds'],
                    'confidence': draw_prob,
                    'market_type': 'match_outcome'
                })

            if away_prob >= MIN_CONFIDENCE:
                predictions.append({
                    'market': 'Away Win',
                    'selection': match['away_name'],
                    'odds': odds_data['away_odds'],
                    'confidence': away_prob,
                    'market_type': 'match_outcome'
                })

        # Game Total O/U 2.5
        ou_probs, conf = self.predict_with_ensemble(features, 'over_2_5')
        if ou_probs is not None and len(ou_probs) == 2:
            under_prob, over_prob = ou_probs

            if over_prob >= MIN_TOTALS_CONFIDENCE:
                predictions.append({
                    'market': 'Over 2.5',
                    'selection': 'Over 2.5 Goals',
                    'odds': odds_data.get('over_25', 1.8),
                    'confidence': over_prob,
                    'market_type': 'game_total'
                })

            if under_prob >= MIN_TOTALS_CONFIDENCE:
                predictions.append({
                    'market': 'Under 2.5',
                    'selection': 'Under 2.5 Goals',
                    'odds': odds_data.get('under_25', 1.9),
                    'confidence': under_prob,
                    'market_type': 'game_total'
                })

        # BTTS
        btts_probs, conf = self.predict_with_ensemble(features, 'btts')
        if btts_probs is not None and len(btts_probs) == 2:
            btts_no_prob, btts_yes_prob = btts_probs

            if btts_yes_prob >= MIN_TOTALS_CONFIDENCE:
                predictions.append({
                    'market': 'BTTS Yes',
                    'selection': 'Both Teams Score',
                    'odds': odds_data.get('btts_yes', 1.8),
                    'confidence': btts_yes_prob,
                    'market_type': 'btts'
                })

            if btts_no_prob >= MIN_TOTALS_CONFIDENCE:
                predictions.append({
                    'market': 'BTTS No',
                    'selection': 'Not Both Teams Score',
                    'odds': odds_data.get('btts_no', 1.9),
                    'confidence': btts_no_prob,
                    'market_type': 'btts'
                })

        # Home Team Totals
        for threshold in ['0_5', '1_5', '2_5']:
            market_key = f'home_over_{threshold}'
            probs, conf = self.predict_with_ensemble(features, market_key)

            if probs is not None and len(probs) == 2:
                under_prob, over_prob = probs
                line = threshold.replace('_', '.')

                if over_prob >= MIN_TEAM_TOTALS_CONFIDENCE:
                    predictions.append({
                        'market': f'Home Over {line}',
                        'selection': f'{match["home_name"]} Over {line}',
                        'odds': 1.9,  # Default odds
                        'confidence': over_prob,
                        'market_type': 'team_total'
                    })

        # Away Team Totals
        for threshold in ['0_5', '1_5', '2_5']:
            market_key = f'away_over_{threshold}'
            probs, conf = self.predict_with_ensemble(features, market_key)

            if probs is not None and len(probs) == 2:
                under_prob, over_prob = probs
                line = threshold.replace('_', '.')

                if over_prob >= MIN_TEAM_TOTALS_CONFIDENCE:
                    predictions.append({
                        'market': f'Away Over {line}',
                        'selection': f'{match["away_name"]} Over {line}',
                        'odds': 1.9,  # Default odds
                        'confidence': over_prob,
                        'market_type': 'team_total'
                    })

        # First Half Markets
        for threshold in ['0_5', '1_5']:
            market_key = f'first_half_over_{threshold}'
            probs, conf = self.predict_with_ensemble(features, market_key)

            if probs is not None and len(probs) == 2:
                under_prob, over_prob = probs
                line = threshold.replace('_', '.')

                if over_prob >= MIN_HALF_CONFIDENCE:
                    predictions.append({
                        'market': f'1H Over {line}',
                        'selection': f'First Half Over {line}',
                        'odds': 2.0,  # Default odds
                        'confidence': over_prob,
                        'market_type': 'half'
                    })

        # Second Half Markets
        for threshold in ['0_5', '1_5']:
            market_key = f'second_half_over_{threshold}'
            probs, conf = self.predict_with_ensemble(features, market_key)

            if probs is not None and len(probs) == 2:
                under_prob, over_prob = probs
                line = threshold.replace('_', '.')

                if over_prob >= MIN_HALF_CONFIDENCE:
                    predictions.append({
                        'market': f'2H Over {line}',
                        'selection': f'Second Half Over {line}',
                        'odds': 2.0,  # Default odds
                        'confidence': over_prob,
                        'market_type': 'half'
                    })

        # Double Chance Markets
        dc_markets = {
            'double_chance_home_draw': ('Home/Draw', 'Home or Draw'),
            'double_chance_away_draw': ('Away/Draw', 'Away or Draw'),
            'double_chance_home_away': ('Home/Away', 'Home or Away (No Draw)')
        }

        for market_key, (market_name, selection) in dc_markets.items():
            probs, conf = self.predict_with_ensemble(features, market_key)

            if probs is not None and len(probs) == 2:
                no_prob, yes_prob = probs

                if yes_prob >= MIN_DOUBLE_CHANCE_CONFIDENCE:
                    predictions.append({
                        'market': market_name,
                        'selection': selection,
                        'odds': 1.5,  # Default odds
                        'confidence': yes_prob,
                        'market_type': 'double_chance'
                    })

        return predictions

    def calculate_kelly(self, win_prob: float, odds: float) -> float:
        """Calculate Kelly Criterion stake"""
        if odds <= 1.0 or win_prob <= 0:
            return 0.0

        b = odds - 1
        p = win_prob
        q = 1 - p

        kelly_full = (b * p - q) / b
        kelly_conservative = kelly_full * KELLY_FRACTION
        kelly_final = min(kelly_conservative, MAX_BET_SIZE)

        return round(kelly_final, 4) if kelly_final >= 0.01 else 0.0

    def fetch_upcoming_matches(self, date_str: str) -> List[Dict]:
        """Fetch upcoming matches - simplified version"""
        print(f"📊 Fetching matches for {date_str}...")

        # For now, return empty list - you can add API integration
        # This is a placeholder
        return []

    def generate_daily_report(self, date_str: str, matches: List[Dict] = None) -> pd.DataFrame:
        """Generate best bets report"""
        print(f"\n{'='*80}")
        print(f"⚽ ENHANCED SOCCER BEST BETS - {date_str}")
        print(f"{'='*80}\n")

        if matches is None:
            matches = self.fetch_upcoming_matches(date_str)

        if not matches:
            print("⚠️  No matches provided")
            return pd.DataFrame()

        all_bets = []

        for match in matches:
            # Extract odds
            odds_data = {
                'home_odds': match.get('odds_ft_1', 2.0),
                'draw_odds': match.get('odds_ft_x', 3.2),
                'away_odds': match.get('odds_ft_2', 3.5),
                'over_25': match.get('over_25', 1.8),
                'under_25': match.get('under_25', 1.9),
                'btts_yes': match.get('btts_yes', 1.85),
                'btts_no': match.get('btts_no', 1.85),
            }

            predictions = self.generate_predictions(match, odds_data)

            for pred in predictions:
                kelly_stake = self.calculate_kelly(pred['confidence'], pred['odds'])

                if kelly_stake > 0:
                    all_bets.append({
                        'country': match.get('league_country', ''),
                        'league': match.get('league_name', ''),
                        'date': date_str,
                        'time': match.get('time', 'TBD'),
                        'home_team': match.get('home_name', 'Unknown'),
                        'away_team': match.get('away_name', 'Unknown'),
                        'market': pred['market'],
                        'selection': pred['selection'],
                        'odds': pred['odds'],
                        'confidence': pred['confidence'],
                        'kelly_stake': kelly_stake,
                        'expected_value': (pred['confidence'] * pred['odds']) - 1
                    })

        if not all_bets:
            print("⚠️  No high-confidence bets found")
            return pd.DataFrame()

        df = pd.DataFrame(all_bets)
        df = df.sort_values('expected_value', ascending=False)

        print(f"\n✅ Found {len(df)} high-confidence betting opportunities")
        print(f"📊 Average confidence: {df['confidence'].mean():.1%}")
        print(f"💰 Total recommended stake: {df['kelly_stake'].sum():.1%} of bankroll")

        return df


def main():
    """Main execution"""
    print("\n⚽ ENHANCED SOCCER BEST BETS GENERATOR")
    print("="*80 + "\n")
    print(f"Thresholds:")
    print(f"  Match Winners: {MIN_CONFIDENCE:.0%}")
    print(f"  Game Totals: {MIN_TOTALS_CONFIDENCE:.0%}")
    print(f"  Team Totals: {MIN_TEAM_TOTALS_CONFIDENCE:.0%}")
    print(f"  Half Markets: {MIN_HALF_CONFIDENCE:.0%}")
    print(f"  Double Chance: {MIN_DOUBLE_CHANCE_CONFIDENCE:.0%}")
    print()

    generator = EnhancedSoccerBetsGenerator()

    # Test with sample match
    print("✅ Enhanced soccer betting system ready!")
    print(f"📊 Loaded {len(generator.models)} models")


if __name__ == "__main__":
    main()
