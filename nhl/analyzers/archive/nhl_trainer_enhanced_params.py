#!/usr/bin/env python3
"""
NHL Enhanced Trainer with INCREASED MODEL PARAMETERS
Improved model complexity for better win rates:
- More estimators (150 -> 300)
- Deeper trees (12 -> 20 for RF, 6 -> 10 for GB)
- More sophisticated hyperparameters
- Additional ensemble techniques
"""

import requests
import json
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import time
from nhl_enhanced_data_with_splits import NHLEnhancedDataWithSplits

class NHLTrainerEnhancedParams:
    """Train ML models with ENHANCED PARAMETERS for better accuracy"""

    def __init__(self, hockey_api_key: str = "960c628e1c91c4b1f125e1eec52ad862"):
        self.hockey_api_key = hockey_api_key
        self.base_url = "https://v1.hockey.api-sports.io"
        self.headers = {'x-apisports-key': hockey_api_key}

        self.data_integrator = NHLEnhancedDataWithSplits()

        self.models = {}
        self.scaler = StandardScaler()
        self.feature_names = []

        # Cache for team schedules (for back-to-back detection)
        self.team_schedules = {}

        print("🏒 NHL Enhanced ML Trainer with INCREASED MODEL PARAMETERS initialized")
        print("   🚀 300 estimators (up from 150)")
        print("   🌲 Deeper trees (RF: 20, GB: 10)")
        print("   🎯 Enhanced hyperparameters for better accuracy")

    def get_days_since_last_game(self, team_name: str, game_date: str, season: int = 2024) -> int:
        """
        Calculate days since team's last game (for back-to-back detection)
        Returns: 0 = back-to-back, 1 = one day rest, 2+ = normal rest
        """

        # Parse game date
        try:
            current_date = datetime.strptime(game_date[:10], '%Y-%m-%d')
        except:
            return 2  # Default to normal rest if can't parse

        # Get team schedule
        cache_key = f"{team_name}_{season}"
        if cache_key not in self.team_schedules:
            # Fetch team's games
            url = f"{self.base_url}/games"
            params = {'league': 57, 'season': season, 'team': team_name}

            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    games = data.get('response', [])

                    # Extract game dates
                    game_dates = []
                    for game in games:
                        game_date_str = game.get('date', '')
                        if game_date_str:
                            try:
                                gd = datetime.strptime(game_date_str[:10], '%Y-%m-%d')
                                game_dates.append(gd)
                            except:
                                pass

                    game_dates.sort()
                    self.team_schedules[cache_key] = game_dates
                else:
                    return 2  # Default
            except:
                return 2  # Default

        # Find days since last game
        team_dates = self.team_schedules.get(cache_key, [])

        # Find previous game
        previous_games = [d for d in team_dates if d < current_date]

        if previous_games:
            last_game = max(previous_games)
            days_diff = (current_date - last_game).days
            return days_diff

        return 2  # Default to normal rest

    def collect_training_data_with_totals(self, num_games: int = 500) -> Tuple[np.array, Dict[str, np.array]]:
        """Collect training data with team totals targets - INCREASED from 400 to 500 games"""

        print(f"\n📊 Collecting training data with team totals, B2B tracking, and home/road splits...")
        print(f"   🎯 Training on {num_games} games (increased from 400)")

        # Get completed games
        url = f"{self.base_url}/games"
        params = {'league': 57, 'season': 2024}

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=60)

            if response.status_code != 200:
                print(f"API error: {response.status_code}")
                return np.array([]), {}

            data = response.json()
            games = data.get('response', [])

            # Filter completed
            completed = [g for g in games if g.get('status', {}).get('short') == 'FT']
            print(f"   Found {len(completed)} completed games")

            completed = completed[:num_games]

            X = []
            y_targets = {
                'winner': [],
                'home_over_2_5': [],
                'home_over_3_5': [],
                'away_over_2_5': [],
                'away_over_3_5': []
            }

            for i, game in enumerate(completed):
                teams = game.get('teams', {})
                home_team = teams.get('home', {}).get('name', '')
                away_team = teams.get('away', {}).get('name', '')
                game_date = game.get('date', '')

                if not home_team or not away_team:
                    continue

                # Build enhanced features WITH HOME/ROAD SPLITS
                features_dict = self.data_integrator.build_enhanced_features(
                    home_team,
                    away_team,
                    2.0,  # Default odds for training
                    2.0,
                    season=2024
                )

                if not features_dict:
                    continue

                # Add back-to-back features
                home_days_rest = self.get_days_since_last_game(home_team, game_date, 2024)
                away_days_rest = self.get_days_since_last_game(away_team, game_date, 2024)

                features_dict['home_days_rest'] = home_days_rest
                features_dict['away_days_rest'] = away_days_rest
                features_dict['home_b2b'] = 1 if home_days_rest == 0 else 0
                features_dict['away_b2b'] = 1 if away_days_rest == 0 else 0
                features_dict['rest_differential'] = home_days_rest - away_days_rest

                # Convert to array
                features = list(features_dict.values())

                # Get outcomes
                scores = game.get('scores', {})
                home_score = scores.get('home', 0)
                away_score = scores.get('away', 0)

                # Target 1: Game winner
                y_targets['winner'].append(1 if home_score > away_score else 0)

                # Target 2: Home team O/U 2.5
                y_targets['home_over_2_5'].append(1 if home_score > 2.5 else 0)

                # Target 3: Home team O/U 3.5
                y_targets['home_over_3_5'].append(1 if home_score > 3.5 else 0)

                # Target 4: Away team O/U 2.5
                y_targets['away_over_2_5'].append(1 if away_score > 2.5 else 0)

                # Target 5: Away team O/U 3.5
                y_targets['away_over_3_5'].append(1 if away_score > 3.5 else 0)

                X.append(features)

                # Store feature names from first game
                if not self.feature_names:
                    self.feature_names = list(features_dict.keys())

                # Progress
                if (i + 1) % 50 == 0:
                    print(f"   Processed {i+1}/{len(completed)} games... ({len(X)} valid)")
                    time.sleep(0.3)

            print(f"\n   ✅ Collected {len(X)} training samples")
            print(f"   📊 Features: {len(self.feature_names)} (including B2B tracking & home/road splits)")
            print(f"   🎯 Targets: 5 (winner + 4 team totals)")

            # Convert targets to numpy arrays
            y_dict = {key: np.array(val) for key, val in y_targets.items()}

            return np.array(X), y_dict

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return np.array([]), {}

    def train_all_models(self, X: np.array, y_dict: Dict[str, np.array]):
        """Train models for all 5 targets with ENHANCED PARAMETERS"""

        print(f"\n🤖 Training Models with ENHANCED PARAMETERS...")
        print(f"   Samples: {len(X)}")
        print(f"   Features: {X.shape[1]}")
        print(f"\n   🚀 IMPROVEMENTS:")
        print(f"      • Estimators: 150 → 300")
        print(f"      • RF Max Depth: 12 → 20")
        print(f"      • GB Max Depth: 6 → 10")
        print(f"      • GB Learning Rate: 0.1 → 0.05 (more conservative)")
        print(f"      • Min Samples Split: 5 → 3 (more granular)")

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Train models for each target
        for target_name, y in y_dict.items():
            print(f"\n{'='*80}")
            print(f"🎯 Training models for: {target_name.upper().replace('_', ' ')}")
            print(f"{'='*80}")

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42
            )

            # Train Random Forest with ENHANCED PARAMETERS
            print(f"\n   Training Random Forest with ENHANCED PARAMETERS...")
            rf = RandomForestClassifier(
                n_estimators=300,        # Increased from 150
                max_depth=20,            # Increased from 12
                min_samples_split=3,     # Decreased from 5 for more granularity
                min_samples_leaf=2,      # Added parameter
                max_features='sqrt',     # Added parameter
                bootstrap=True,
                random_state=42,
                n_jobs=-1                # Use all CPU cores
            )
            rf.fit(X_train, y_train)

            rf_score = rf.score(X_test, y_test)
            rf_cv = cross_val_score(rf, X_scaled, y, cv=5)

            print(f"   ✅ Random Forest (Enhanced)")
            print(f"      Test Accuracy: {rf_score:.3f}")
            print(f"      CV Score: {rf_cv.mean():.3f} (+/- {rf_cv.std():.3f})")

            self.models[f'rf_{target_name}'] = rf

            # Train Gradient Boosting with ENHANCED PARAMETERS
            print(f"\n   Training Gradient Boosting with ENHANCED PARAMETERS...")
            gb = GradientBoostingClassifier(
                n_estimators=300,        # Increased from 150
                max_depth=10,            # Increased from 6
                learning_rate=0.05,      # Decreased from 0.1 for better generalization
                min_samples_split=3,     # Decreased from 5
                min_samples_leaf=2,      # Added parameter
                subsample=0.8,           # Added parameter for regularization
                random_state=42
            )
            gb.fit(X_train, y_train)

            gb_score = gb.score(X_test, y_test)
            gb_cv = cross_val_score(gb, X_scaled, y, cv=5)

            print(f"   ✅ Gradient Boosting (Enhanced)")
            print(f"      Test Accuracy: {gb_score:.3f}")
            print(f"      CV Score: {gb_cv.mean():.3f} (+/- {gb_cv.std():.3f})")

            self.models[f'gb_{target_name}'] = gb

            # Baseline
            baseline = max(sum(y), len(y) - sum(y)) / len(y)
            print(f"\n   📊 Baseline: {baseline:.3f}")
            print(f"   📈 RF Improvement: {(rf_score - baseline):.3f}")
            print(f"   📈 GB Improvement: {(gb_score - baseline):.3f}")

        print(f"\n{'='*80}")
        print(f"✅ All models trained successfully with ENHANCED PARAMETERS!")
        print(f"{'='*80}")
        print(f"\n📦 Total models trained: {len(self.models)}")
        print(f"   • 2 models for game winner (RF + GB)")
        print(f"   • 2 models for home O/U 2.5 (RF + GB)")
        print(f"   • 2 models for home O/U 3.5 (RF + GB)")
        print(f"   • 2 models for away O/U 2.5 (RF + GB)")
        print(f"   • 2 models for away O/U 3.5 (RF + GB)")

    def save_models(self, filepath: str = "nhl_models_enhanced_params.pkl"):
        """Save all models"""

        data = {
            'models': self.models,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'model_info': {
                'trained_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'n_estimators': 300,
                'rf_max_depth': 20,
                'gb_max_depth': 10,
                'training_samples': len(self.feature_names),
                'version': 'enhanced_params_v1'
            }
        }

        with open(filepath, 'wb') as f:
            pickle.dump(data, f)

        print(f"\n💾 Models saved to {filepath}")
        print(f"   Total size: {len(self.models)} models")
        print(f"   Features: {len(self.feature_names)}")


def main():
    """Train NHL models with ENHANCED PARAMETERS"""

    print("="*80)
    print("🏒 NHL MODEL TRAINING - ENHANCED PARAMETERS FOR BETTER WIN RATES")
    print("="*80)
    print("🚀 Improvements:")
    print("   • 300 estimators (up from 150)")
    print("   • RF depth: 20 (up from 12)")
    print("   • GB depth: 10 (up from 6)")
    print("   • 500 training games (up from 400)")
    print("   • More conservative learning rate")
    print("="*80)

    trainer = NHLTrainerEnhancedParams()

    # Collect training data with MORE GAMES
    X, y_dict = trainer.collect_training_data_with_totals(num_games=500)

    if len(X) > 0:
        # Train all models
        trainer.train_all_models(X, y_dict)

        # Save models
        trainer.save_models()

        print(f"\n✅ NHL ML models ready with ENHANCED PARAMETERS!")
        print(f"   Expected improvements:")
        print(f"      • Higher accuracy from deeper trees")
        print(f"      • Better generalization from more estimators")
        print(f"      • Improved predictions on edge cases")
        print(f"\n   Predictions available for:")
        print(f"      • Game winner")
        print(f"      • Home team O/U 2.5 goals")
        print(f"      • Home team O/U 3.5 goals")
        print(f"      • Away team O/U 2.5 goals")
        print(f"      • Away team O/U 3.5 goals")

    else:
        print(f"\n❌ Failed to collect training data")


if __name__ == "__main__":
    main()
