#!/usr/bin/env python3
"""
NHL Enhanced ML Trainer
Train models with advanced metrics from MoneyPuck + basic stats
"""

import requests
import json
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
import pickle
from datetime import datetime
from typing import Dict, List, Tuple
import time
from nhl_enhanced_data import NHLEnhancedData

class NHLEnhancedTrainer:
    """Train ML models with enhanced features"""

    def __init__(self, hockey_api_key: str = "960c628e1c91c4b1f125e1eec52ad862"):
        self.hockey_api_key = hockey_api_key
        self.base_url = "https://v1.hockey.api-sports.io"
        self.headers = {'x-apisports-key': hockey_api_key}

        self.data_integrator = NHLEnhancedData()

        self.models = {}
        self.scaler = StandardScaler()
        self.feature_names = []

        print("🏒 NHL Enhanced ML Trainer initialized")

    def collect_enhanced_training_data(self, num_games: int = 400) -> Tuple[np.array, np.array]:
        """Collect training data with enhanced features"""

        print(f"\n📊 Collecting enhanced training data...")

        # Get completed games
        url = f"{self.base_url}/games"
        params = {'league': 57, 'season': 2024}

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=60)

            if response.status_code != 200:
                print(f"API error: {response.status_code}")
                return np.array([]), np.array([])

            data = response.json()
            games = data.get('response', [])

            # Filter completed
            completed = [g for g in games if g.get('status', {}).get('short') == 'FT']
            print(f"   Found {len(completed)} completed games")

            completed = completed[:num_games]

            X = []
            y = []

            for i, game in enumerate(completed):
                teams = game.get('teams', {})
                home_team = teams.get('home', {}).get('name', '')
                away_team = teams.get('away', {}).get('name', '')

                if not home_team or not away_team:
                    continue

                # Build enhanced features
                features_dict = self.data_integrator.build_enhanced_features(
                    home_team,
                    away_team,
                    2.0,  # Default odds for training
                    2.0,
                    season=2024
                )

                if not features_dict:
                    continue

                # Convert to array
                features = list(features_dict.values())

                # Get outcome
                scores = game.get('scores', {})
                home_score = scores.get('home', 0)
                away_score = scores.get('away', 0)

                outcome = 1 if home_score > away_score else 0

                X.append(features)
                y.append(outcome)

                # Store feature names from first game
                if not self.feature_names:
                    self.feature_names = list(features_dict.keys())

                # Progress
                if (i + 1) % 50 == 0:
                    print(f"   Processed {i+1}/{len(completed)} games... ({len(X)} valid)")
                    time.sleep(0.3)

            print(f"\n   ✅ Collected {len(X)} training samples with {len(self.feature_names)} features")

            return np.array(X), np.array(y)

        except Exception as e:
            print(f"Error: {e}")
            return np.array([]), np.array([])

    def train_models(self, X: np.array, y: np.array):
        """Train enhanced ML models"""

        print(f"\n🤖 Training Enhanced ML Models...")
        print(f"   Samples: {len(X)}")
        print(f"   Features: {X.shape[1]}")
        print(f"   Feature names: {len(self.feature_names)}")

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )

        # Train Random Forest
        print(f"\n   Training Random Forest...")
        rf = RandomForestClassifier(
            n_estimators=150,
            max_depth=12,
            min_samples_split=5,
            random_state=42
        )
        rf.fit(X_train, y_train)

        rf_score = rf.score(X_test, y_test)
        rf_cv = cross_val_score(rf, X_scaled, y, cv=5)

        print(f"   ✅ Random Forest")
        print(f"      Test Accuracy: {rf_score:.3f}")
        print(f"      CV Score: {rf_cv.mean():.3f} (+/- {rf_cv.std():.3f})")

        # Feature importance
        importances = rf.feature_importances_
        top_features_idx = np.argsort(importances)[-10:][::-1]

        print(f"\n   🎯 Top 10 Most Important Features:")
        for idx in top_features_idx:
            if idx < len(self.feature_names):
                print(f"      {self.feature_names[idx]}: {importances[idx]:.4f}")

        self.models['random_forest'] = rf

        # Train Gradient Boosting
        print(f"\n   Training Gradient Boosting...")
        gb = GradientBoostingClassifier(
            n_estimators=150,
            max_depth=6,
            learning_rate=0.1,
            random_state=42
        )
        gb.fit(X_train, y_train)

        gb_score = gb.score(X_test, y_test)
        gb_cv = cross_val_score(gb, X_scaled, y, cv=5)

        print(f"   ✅ Gradient Boosting")
        print(f"      Test Accuracy: {gb_score:.3f}")
        print(f"      CV Score: {gb_cv.mean():.3f} (+/- {gb_cv.std():.3f})")

        self.models['gradient_boosting'] = gb

        # Calculate baseline (majority class)
        baseline = max(sum(y), len(y) - sum(y)) / len(y)
        print(f"\n   📊 Baseline (majority class): {baseline:.3f}")
        print(f"   📈 Improvement over baseline: {(rf_score - baseline):.3f}")

        print(f"\n✅ Enhanced model training complete!")

    def save_models(self, filepath: str = "nhl_enhanced_models.pkl"):
        """Save enhanced models"""

        data = {
            'models': self.models,
            'scaler': self.scaler,
            'feature_names': self.feature_names
        }

        with open(filepath, 'wb') as f:
            pickle.dump(data, f)

        print(f"\n💾 Enhanced models saved to {filepath}")


def main():
    """Train enhanced NHL models"""

    trainer = NHLEnhancedTrainer()

    # Collect enhanced training data
    X, y = trainer.collect_enhanced_training_data(num_games=400)

    if len(X) > 0:
        # Train models
        trainer.train_models(X, y)

        # Save models
        trainer.save_models()

        print(f"\n✅ Enhanced NHL ML models ready!")
        print(f"   Models trained with {X.shape[1]} advanced features")
        print(f"   Including xGoals%, Corsi%, Fenwick%, high-danger chances")

    else:
        print(f"\n❌ Failed to collect training data")


if __name__ == "__main__":
    main()
