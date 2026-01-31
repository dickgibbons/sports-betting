#!/usr/bin/env python3
"""
ProphitBet Ensemble Integration Module

Integrates ProphitBet's XGBoost and feature engineering approach as additional
ensemble members for the existing soccer betting prediction system.

Key Features:
- Uses ProphitBet's historical team performance features (last N games stats)
- XGBoost models for match outcome, over/under, and BTTS
- Combines with existing RF/GB ensemble for improved accuracy
"""

import os
import sys
import pickle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sklearn.preprocessing import StandardScaler
from sklearn.calibration import CalibratedClassifierCV
from xgboost import XGBClassifier
import joblib
import warnings
warnings.filterwarnings('ignore')

# ProphitBet source path
PROPHITBET_PATH = "/Users/dickgibbons/Documents/GitHub/ProphitBet-Soccer-Bets-Predictor-main"

# Add ProphitBet to path for imports if needed
if PROPHITBET_PATH not in sys.path:
    sys.path.insert(0, PROPHITBET_PATH)


class ProphitBetEnsemble:
    """
    Ensemble predictor using ProphitBet's feature engineering and XGBoost models.

    This class provides predictions that can be combined with the existing
    RF/GB ensemble in soccer_best_bets_daily.py for better accuracy.
    """

    def __init__(self, model_dir: str = None):
        """
        Initialize the ProphitBet ensemble.

        Args:
            model_dir: Directory to store/load trained models
        """
        if model_dir is None:
            model_dir = os.path.join(os.path.dirname(__file__), 'models', 'prophitbet_ensemble')

        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)

        # Model storage
        self.models = {}
        self.scalers = {}
        self.feature_names = []

        # ProphitBet feature columns (excluding non-trainable columns)
        self.prophitbet_features = [
            '1', 'X', '2',  # Odds
            'HW', 'AW', 'HL', 'AL',  # Win/Loss counts
            'HGF', 'AGF', 'HAGF',  # Goals forward
            'HGA', 'AGA', 'HAGA',  # Goals against
            'HGD', 'AGD', 'HAGD',  # Goal difference
            'HWGD', 'AWGD', 'HAWGD',  # Wins by margin
            'HLGD', 'ALGD', 'HALGD',  # Losses by margin
            'HW%', 'HL%', 'AW%', 'AL%',  # Win/Loss percentages
            'HSTF', 'ASTF',  # Shots on target
            'HCF', 'ACF'  # Corners
        ]

        # Targets supported (including first half totals)
        self.targets = ['match_outcome', 'over_2_5', 'btts', 'h1_over_0_5', 'h1_over_1_5']

        print("ProphitBet Ensemble initialized")

    def load_prophitbet_data(self, league_id: str = None) -> Optional[pd.DataFrame]:
        """
        Load historical data from ProphitBet's storage.

        Args:
            league_id: League identifier (e.g., 'Premier-League-England-01')

        Returns:
            DataFrame with historical match data or None
        """
        leagues_dir = os.path.join(PROPHITBET_PATH, 'storage', 'leagues')

        if league_id:
            data_path = os.path.join(leagues_dir, league_id, 'data', 'dataset.csv')
            if os.path.exists(data_path):
                return pd.read_csv(data_path)
            return None

        # Load all available league data
        all_data = []
        if os.path.exists(leagues_dir):
            for league in os.listdir(leagues_dir):
                if league.endswith('.pkl'):
                    continue
                data_path = os.path.join(leagues_dir, league, 'data', 'dataset.csv')
                if os.path.exists(data_path):
                    df = pd.read_csv(data_path)
                    df['league_id'] = league
                    all_data.append(df)

        if all_data:
            return pd.concat(all_data, ignore_index=True)
        return None

    def prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
        """
        Prepare features from a DataFrame using ProphitBet's feature set.

        Args:
            df: DataFrame with match data

        Returns:
            Tuple of (feature array, feature names)
        """
        available_features = [f for f in self.prophitbet_features if f in df.columns]

        if not available_features:
            raise ValueError("No ProphitBet features found in DataFrame")

        # Extract features and handle missing values
        X = df[available_features].copy()
        X = X.fillna(X.mean())

        return X.values.astype(np.float32), available_features

    def prepare_targets(self, df: pd.DataFrame, target_type: str) -> np.ndarray:
        """
        Prepare target labels from DataFrame.

        Args:
            df: DataFrame with match data
            target_type: 'match_outcome', 'over_2_5', 'btts', 'h1_over_0_5', 'h1_over_1_5'

        Returns:
            Target array
        """
        if target_type == 'match_outcome':
            # H=2, D=1, A=0 (ProphitBet convention)
            return df['Result'].map({'H': 2, 'D': 1, 'A': 0}).values

        elif target_type == 'over_2_5':
            # O=1, U=0
            return df['Result-U/O'].map({'O': 1, 'U': 0}).values

        elif target_type == 'btts':
            # Calculate BTTS from goals
            btts = ((df['HG'] > 0) & (df['AG'] > 0)).astype(int)
            return btts.values

        elif target_type == 'h1_over_0_5':
            # First half Over 0.5 goals
            # Statistical proxy: ~78% of matches have at least 1 goal in H1
            # Use total goals as indicator: if total >= 1, likely H1 had goals
            # More accurate: matches with 2+ goals almost always have H1 goal
            total_goals = df['HG'] + df['AG']
            # Probability-based: 1 goal = 70% H1 hit, 2+ goals = 90% H1 hit
            h1_over_05 = (total_goals >= 1).astype(int)
            return h1_over_05.values

        elif target_type == 'h1_over_1_5':
            # First half Over 1.5 goals
            # Statistical proxy: ~35% of matches have 2+ goals in H1
            # Matches with 3+ total goals have ~60% chance of H1 Over 1.5
            total_goals = df['HG'] + df['AG']
            h1_over_15 = (total_goals >= 3).astype(int)
            return h1_over_15.values

        else:
            raise ValueError(f"Unknown target type: {target_type}")

    def build_xgboost_model(self, num_classes: int = 3) -> XGBClassifier:
        """
        Build an XGBoost classifier with ProphitBet-style configuration.

        Args:
            num_classes: Number of output classes

        Returns:
            XGBClassifier instance
        """
        return XGBClassifier(
            booster='gbtree',
            n_estimators=200,
            learning_rate=0.1,
            max_depth=6,
            min_child_weight=1,
            reg_lambda=1.0,
            reg_alpha=0.0,
            random_state=42,
            n_jobs=-1,
            objective='multi:softprob' if num_classes > 2 else 'binary:logistic',
            eval_metric='mlogloss' if num_classes > 2 else 'logloss'
        )

    def train_models(self, df: pd.DataFrame = None, calibrate: bool = True) -> Dict[str, float]:
        """
        Train XGBoost models on ProphitBet data.

        Args:
            df: Optional DataFrame (loads from ProphitBet if not provided)
            calibrate: Whether to calibrate probabilities (recommended)

        Returns:
            Dictionary of model accuracies
        """
        if df is None:
            df = self.load_prophitbet_data()
            if df is None:
                raise ValueError("No training data available. Please load data into ProphitBet first.")

        # Drop rows with missing values
        df = df.dropna()

        if len(df) < 100:
            raise ValueError(f"Insufficient training data: {len(df)} rows (need at least 100)")

        print(f"Training ProphitBet ensemble on {len(df)} matches...")

        # Prepare features
        X, feature_names = self.prepare_features(df)
        self.feature_names = feature_names

        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        self.scalers['main'] = scaler

        accuracies = {}

        for target_type in self.targets:
            print(f"  Training {target_type} model...")

            try:
                y = self.prepare_targets(df, target_type)

                # Remove any NaN targets
                valid_mask = ~np.isnan(y)
                X_train = X_scaled[valid_mask]
                y_train = y[valid_mask].astype(int)

                num_classes = len(np.unique(y_train))

                # Build and train model
                model = self.build_xgboost_model(num_classes)

                if calibrate:
                    model = CalibratedClassifierCV(
                        estimator=model,
                        method='isotonic',
                        cv=5,
                        n_jobs=-1
                    )

                model.fit(X_train, y_train)

                # Evaluate
                y_pred = model.predict(X_train)
                accuracy = (y_pred == y_train).mean()
                accuracies[target_type] = accuracy

                self.models[target_type] = model
                print(f"    {target_type}: {accuracy:.1%} accuracy")

            except Exception as e:
                print(f"    Error training {target_type}: {e}")
                continue

        # Save models
        self.save_models()

        return accuracies

    def save_models(self):
        """Save trained models to disk."""
        model_path = os.path.join(self.model_dir, 'prophitbet_xgb_ensemble.pkl')

        save_data = {
            'models': self.models,
            'scalers': self.scalers,
            'feature_names': self.feature_names
        }

        joblib.dump(save_data, model_path)
        print(f"Models saved to {model_path}")

    def load_models(self) -> bool:
        """
        Load trained models from disk.

        Returns:
            True if models loaded successfully, False otherwise
        """
        model_path = os.path.join(self.model_dir, 'prophitbet_xgb_ensemble.pkl')

        if not os.path.exists(model_path):
            return False

        try:
            save_data = joblib.load(model_path)
            self.models = save_data['models']
            self.scalers = save_data['scalers']
            self.feature_names = save_data['feature_names']
            print(f"Loaded ProphitBet models: {list(self.models.keys())}")
            return True
        except Exception as e:
            print(f"Error loading models: {e}")
            return False

    def predict_from_odds(self, odds_data: Dict) -> Optional[Dict]:
        """
        Generate predictions from odds data (compatible with existing system).

        This method creates synthetic features from odds to make predictions
        when full historical data is not available.

        Args:
            odds_data: Dictionary with odds data:
                - home_odds: Home win odds
                - draw_odds: Draw odds
                - away_odds: Away win odds
                - over_25: Over 2.5 odds
                - under_25: Under 2.5 odds
                - btts_yes: BTTS Yes odds
                - btts_no: BTTS No odds

        Returns:
            Dictionary with predictions for each target type
        """
        if not self.models:
            if not self.load_models():
                return None

        # Create synthetic features from odds
        # This is an approximation when full historical data isn't available
        home_odds = odds_data.get('home_odds', 2.0)
        draw_odds = odds_data.get('draw_odds', 3.2)
        away_odds = odds_data.get('away_odds', 3.5)

        # Convert odds to implied probabilities
        total = 1/home_odds + 1/draw_odds + 1/away_odds
        home_prob = (1/home_odds) / total
        draw_prob = (1/draw_odds) / total
        away_prob = (1/away_odds) / total

        # Estimate team strength indicators from odds
        # Higher home odds = weaker home team
        home_strength = 1 / home_odds
        away_strength = 1 / away_odds

        # Create synthetic feature vector (27 features)
        # Order must match self.prophitbet_features
        features = np.array([[
            home_odds,      # 1 (Home odds)
            draw_odds,      # X (Draw odds)
            away_odds,      # 2 (Away odds)
            # Synthetic stats based on implied strength
            max(0, 3 * home_strength),   # HW - home wins (estimated)
            max(0, 3 * away_strength),   # AW - away wins
            max(0, 2 * (1-home_strength)),  # HL - home losses
            max(0, 2 * (1-away_strength)),  # AL - away losses
            max(0, 6 * home_strength),   # HGF - home goals forward
            max(0, 5 * away_strength),   # AGF - away goals forward
            max(0, 6 * home_strength - 5 * away_strength),  # HAGF
            max(0, 4 * (1-home_strength)),  # HGA - home goals against
            max(0, 5 * (1-away_strength)),  # AGA - away goals against
            0.0,  # HAGA
            max(0, 6 * home_strength - 4 * (1-home_strength)),  # HGD
            max(0, 5 * away_strength - 5 * (1-away_strength)),  # AGD
            0.0,  # HAGD
            max(0, 1 * home_strength),   # HWGD
            max(0, 1 * away_strength),   # AWGD
            0.0,  # HAWGD
            max(0, 1 * (1-home_strength)),  # HLGD
            max(0, 1 * (1-away_strength)),  # ALGD
            0.0,  # HALGD
            home_prob * 100,  # HW%
            (1 - home_prob - draw_prob) * 100,  # HL%
            away_prob * 100,  # AW%
            (1 - away_prob - draw_prob) * 100,  # AL%
            max(0, 15 * home_strength),  # HSTF - shots on target
            max(0, 12 * away_strength),  # ASTF
            max(0, 6 * home_strength),   # HCF - corners
            max(0, 5 * away_strength),   # ACF
        ]], dtype=np.float32)

        # Use only the features the model was trained on
        if len(self.feature_names) < features.shape[1]:
            features = features[:, :len(self.feature_names)]

        # Scale features
        if 'main' in self.scalers:
            features_scaled = self.scalers['main'].transform(features)
        else:
            features_scaled = features

        predictions = {}

        for target_type, model in self.models.items():
            try:
                probs = model.predict_proba(features_scaled)[0]

                if target_type == 'match_outcome':
                    # [Away, Draw, Home] probabilities
                    predictions['match_outcome'] = {
                        'away_prob': float(probs[0]),
                        'draw_prob': float(probs[1]),
                        'home_prob': float(probs[2]) if len(probs) > 2 else 0.0
                    }

                elif target_type == 'over_2_5':
                    # [Under, Over] probabilities
                    predictions['over_2_5'] = {
                        'under_prob': float(probs[0]),
                        'over_prob': float(probs[1]) if len(probs) > 1 else 1 - float(probs[0])
                    }

                elif target_type == 'btts':
                    # [No, Yes] probabilities
                    predictions['btts'] = {
                        'no_prob': float(probs[0]),
                        'yes_prob': float(probs[1]) if len(probs) > 1 else 1 - float(probs[0])
                    }

                elif target_type == 'h1_over_0_5':
                    # [Under, Over] probabilities for H1 Over 0.5
                    predictions['h1_over_0_5'] = {
                        'under_prob': float(probs[0]),
                        'over_prob': float(probs[1]) if len(probs) > 1 else 1 - float(probs[0])
                    }

                elif target_type == 'h1_over_1_5':
                    # [Under, Over] probabilities for H1 Over 1.5
                    predictions['h1_over_1_5'] = {
                        'under_prob': float(probs[0]),
                        'over_prob': float(probs[1]) if len(probs) > 1 else 1 - float(probs[0])
                    }

            except Exception as e:
                print(f"Error predicting {target_type}: {e}")
                continue

        return predictions

    def predict_with_full_features(self, match_features: Dict) -> Optional[Dict]:
        """
        Generate predictions using full ProphitBet feature set.

        Args:
            match_features: Dictionary with all ProphitBet features

        Returns:
            Dictionary with predictions
        """
        if not self.models:
            if not self.load_models():
                return None

        # Build feature vector
        features = []
        for feat in self.feature_names:
            features.append(match_features.get(feat, 0.0))

        features = np.array([features], dtype=np.float32)

        # Scale
        if 'main' in self.scalers:
            features_scaled = self.scalers['main'].transform(features)
        else:
            features_scaled = features

        predictions = {}

        for target_type, model in self.models.items():
            try:
                probs = model.predict_proba(features_scaled)[0]

                if target_type == 'match_outcome':
                    predictions['match_outcome'] = {
                        'away_prob': float(probs[0]),
                        'draw_prob': float(probs[1]),
                        'home_prob': float(probs[2]) if len(probs) > 2 else 0.0
                    }
                elif target_type == 'over_2_5':
                    predictions['over_2_5'] = {
                        'under_prob': float(probs[0]),
                        'over_prob': float(probs[1]) if len(probs) > 1 else 1 - float(probs[0])
                    }
                elif target_type == 'btts':
                    predictions['btts'] = {
                        'no_prob': float(probs[0]),
                        'yes_prob': float(probs[1]) if len(probs) > 1 else 1 - float(probs[0])
                    }
            except Exception as e:
                print(f"Error predicting {target_type}: {e}")

        return predictions

    def get_ensemble_prediction(
        self,
        odds_data: Dict,
        existing_predictions: Dict,
        prophitbet_weight: float = 0.3
    ) -> Dict:
        """
        Combine ProphitBet predictions with existing system predictions.

        Args:
            odds_data: Odds data for ProphitBet prediction
            existing_predictions: Predictions from existing RF/GB models
            prophitbet_weight: Weight for ProphitBet predictions (0-1)

        Returns:
            Combined ensemble predictions
        """
        pb_preds = self.predict_from_odds(odds_data)

        if pb_preds is None:
            return existing_predictions

        existing_weight = 1 - prophitbet_weight
        combined = {}

        # Combine match outcome
        if 'match_outcome' in pb_preds and 'match_outcome' in existing_predictions:
            combined['match_outcome'] = {
                'home_prob': (
                    existing_weight * existing_predictions['match_outcome'].get('home_prob', 0) +
                    prophitbet_weight * pb_preds['match_outcome'].get('home_prob', 0)
                ),
                'draw_prob': (
                    existing_weight * existing_predictions['match_outcome'].get('draw_prob', 0) +
                    prophitbet_weight * pb_preds['match_outcome'].get('draw_prob', 0)
                ),
                'away_prob': (
                    existing_weight * existing_predictions['match_outcome'].get('away_prob', 0) +
                    prophitbet_weight * pb_preds['match_outcome'].get('away_prob', 0)
                )
            }

        # Combine over/under 2.5
        if 'over_2_5' in pb_preds and 'over_2_5' in existing_predictions:
            combined['over_2_5'] = {
                'over_prob': (
                    existing_weight * existing_predictions['over_2_5'].get('over_prob', 0) +
                    prophitbet_weight * pb_preds['over_2_5'].get('over_prob', 0)
                ),
                'under_prob': (
                    existing_weight * existing_predictions['over_2_5'].get('under_prob', 0) +
                    prophitbet_weight * pb_preds['over_2_5'].get('under_prob', 0)
                )
            }

        # Combine BTTS
        if 'btts' in pb_preds and 'btts' in existing_predictions:
            combined['btts'] = {
                'yes_prob': (
                    existing_weight * existing_predictions['btts'].get('yes_prob', 0) +
                    prophitbet_weight * pb_preds['btts'].get('yes_prob', 0)
                ),
                'no_prob': (
                    existing_weight * existing_predictions['btts'].get('no_prob', 0) +
                    prophitbet_weight * pb_preds['btts'].get('no_prob', 0)
                )
            }

        # Combine H1 Over 0.5
        if 'h1_over_0_5' in pb_preds and 'h1_over_0_5' in existing_predictions:
            combined['h1_over_0_5'] = {
                'over_prob': (
                    existing_weight * existing_predictions['h1_over_0_5'].get('over_prob', 0) +
                    prophitbet_weight * pb_preds['h1_over_0_5'].get('over_prob', 0)
                ),
                'under_prob': (
                    existing_weight * existing_predictions['h1_over_0_5'].get('under_prob', 0) +
                    prophitbet_weight * pb_preds['h1_over_0_5'].get('under_prob', 0)
                )
            }

        # Combine H1 Over 1.5
        if 'h1_over_1_5' in pb_preds and 'h1_over_1_5' in existing_predictions:
            combined['h1_over_1_5'] = {
                'over_prob': (
                    existing_weight * existing_predictions['h1_over_1_5'].get('over_prob', 0) +
                    prophitbet_weight * pb_preds['h1_over_1_5'].get('over_prob', 0)
                ),
                'under_prob': (
                    existing_weight * existing_predictions['h1_over_1_5'].get('under_prob', 0) +
                    prophitbet_weight * pb_preds['h1_over_1_5'].get('under_prob', 0)
                )
            }

        return combined


def train_prophitbet_ensemble():
    """Utility function to train the ProphitBet ensemble models."""
    print("\n" + "="*60)
    print("TRAINING PROPHITBET ENSEMBLE MODELS")
    print("="*60 + "\n")

    ensemble = ProphitBetEnsemble()

    # Try to load data from ProphitBet
    df = ensemble.load_prophitbet_data()

    if df is None or len(df) < 100:
        print("Insufficient ProphitBet data. Please:")
        print("1. Open ProphitBet GUI")
        print("2. Create a league and download historical data")
        print("3. Run this training script again")
        print("\nAlternatively, you can manually add CSV data to:")
        print(f"  {PROPHITBET_PATH}/storage/leagues/[league-name]/data/dataset.csv")
        return False

    print(f"Found {len(df)} historical matches")

    # Train models
    accuracies = ensemble.train_models(df)

    print("\n" + "="*60)
    print("TRAINING COMPLETE")
    print("="*60)
    print("\nModel Accuracies:")
    for target, acc in accuracies.items():
        print(f"  {target}: {acc:.1%}")

    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='ProphitBet Ensemble Integration')
    parser.add_argument('--train', action='store_true', help='Train ensemble models')
    parser.add_argument('--test', action='store_true', help='Test with sample odds')
    args = parser.parse_args()

    if args.train:
        train_prophitbet_ensemble()

    elif args.test:
        print("Testing ProphitBet Ensemble...")
        ensemble = ProphitBetEnsemble()

        if not ensemble.load_models():
            print("No trained models found. Run with --train first.")
            sys.exit(1)

        # Test prediction
        test_odds = {
            'home_odds': 1.74,
            'draw_odds': 3.83,
            'away_odds': 4.49,
            'over_25': 1.85,
            'under_25': 1.95,
            'btts_yes': 1.80,
            'btts_no': 2.00
        }

        predictions = ensemble.predict_from_odds(test_odds)

        if predictions:
            print("\nPredictions for test odds:")
            for target, probs in predictions.items():
                print(f"\n{target}:")
                for key, val in probs.items():
                    print(f"  {key}: {val:.1%}")

    else:
        parser.print_help()
