#!/usr/bin/env python3
"""
NBA Enhanced ML Trainer
Train models with advanced metrics from NBA Official Stats + basic stats
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
from nba_enhanced_data import NBAEnhancedData

class NBAEnhancedTrainer:
    """Train ML models with enhanced features"""

    def __init__(self):
        self.nba_stats_base = "https://stats.nba.com/stats"

        self.data_integrator = NBAEnhancedData()

        self.models = {}
        self.scaler = StandardScaler()
        self.feature_names = []

        print("🏀 NBA Enhanced ML Trainer initialized")

    def collect_enhanced_training_data(self, num_games: int = 500) -> Tuple[np.array, np.array]:
        """Collect training data with enhanced features"""

        print(f"\n📊 Collecting enhanced training data...")

        # NBA.com stats endpoints require headers
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://stats.nba.com/',
            'x-nba-stats-origin': 'stats',
            'x-nba-stats-token': 'true'
        }

        # Get completed games from current season
        url = f"{self.nba_stats_base}/leaguegamefinder"
        params = {
            'Season': '2024-25',
            'SeasonType': 'Regular Season',
            'LeagueID': '00'
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=60)

            if response.status_code != 200:
                print(f"API error: {response.status_code}")
                # Fallback: Use simpler approach with fewer games
                return self._collect_training_data_simple(num_games)

            data = response.json()
            result_sets = data.get('resultSets', [])

            if not result_sets:
                print(f"No result sets found")
                return self._collect_training_data_simple(num_games)

            # Get headers and data
            headers_list = result_sets[0].get('headers', [])
            rows = result_sets[0].get('rowSet', [])

            # Convert to DataFrame
            df_games = pd.DataFrame(rows, columns=headers_list)

            # Get unique games (each game has 2 rows - one for each team)
            unique_games = df_games.groupby('GAME_ID').first().reset_index()

            print(f"   Found {len(unique_games)} completed games")

            # Limit to num_games
            unique_games = unique_games.head(num_games)

            X = []
            y = []

            for i, game_row in unique_games.iterrows():
                game_id = game_row['GAME_ID']

                # Get both teams' data for this game
                game_data = df_games[df_games['GAME_ID'] == game_id]

                if len(game_data) < 2:
                    continue

                # Identify home and away teams
                # In NBA, home team is typically the second row (WL contains result)
                team1 = game_data.iloc[0]
                team2 = game_data.iloc[1]

                # Determine home/away based on MATCHUP (@ indicates away team)
                if '@' in str(team1['MATCHUP']):
                    away_team_name = team1['TEAM_NAME']
                    home_team_name = team2['TEAM_NAME']
                    away_pts = team1['PTS']
                    home_pts = team2['PTS']
                else:
                    home_team_name = team1['TEAM_NAME']
                    away_team_name = team2['TEAM_NAME']
                    home_pts = team1['PTS']
                    away_pts = team2['PTS']

                # Build enhanced features
                features_dict = self.data_integrator.build_enhanced_features(
                    home_team_name,
                    away_team_name,
                    2.0,  # Default odds for training
                    2.0,
                    season=2024
                )

                if not features_dict:
                    continue

                # Convert to array
                features = list(features_dict.values())

                # Get outcome (1 if home team won, 0 if away team won)
                outcome = 1 if home_pts > away_pts else 0

                X.append(features)
                y.append(outcome)

                # Store feature names from first game
                if not self.feature_names:
                    self.feature_names = list(features_dict.keys())

                # Progress
                if (i + 1) % 50 == 0:
                    print(f"   Processed {i+1}/{len(unique_games)} games... ({len(X)} valid)")
                    time.sleep(0.1)

            print(f"\n   ✅ Collected {len(X)} training samples with {len(self.feature_names)} features")

            return np.array(X), np.array(y)

        except Exception as e:
            print(f"Error: {e}")
            print("Falling back to simple training data collection...")
            return self._collect_training_data_simple(num_games)

    def _collect_training_data_simple(self, num_games: int) -> Tuple[np.array, np.array]:
        """Simplified training data collection (fallback method)"""
        print(f"\n   Using simplified training data collection...")

        # Generate synthetic training data based on team stats
        # This is a fallback - in production you'd want real historical games

        nba_data = self.data_integrator.get_nba_team_stats(2024)

        if nba_data.empty:
            print("   ❌ No NBA data available for training")
            return np.array([]), np.array([])

        teams = nba_data['team'].tolist()

        X = []
        y = []

        # Create synthetic matchups between teams
        import random
        random.seed(42)

        for _ in range(num_games):
            # Pick random home and away teams
            home_team = random.choice(teams)
            away_team = random.choice([t for t in teams if t != home_team])

            # Get team names
            home_name = self.data_integrator.team_map.get(home_team, home_team)
            away_name = self.data_integrator.team_map.get(away_team, away_team)

            # Find full team names
            for name, code in self.data_integrator.team_map.items():
                if code == home_team:
                    home_name = name
                if code == away_team:
                    away_name = name

            # Build features
            features_dict = self.data_integrator.build_enhanced_features(
                home_name,
                away_name,
                2.0,
                2.0,
                season=2024
            )

            if not features_dict:
                continue

            features = list(features_dict.values())

            # Simulate outcome based on offensive/defensive ratings
            home_off = features_dict.get('home_offRating', 110)
            away_off = features_dict.get('away_offRating', 110)
            home_def = features_dict.get('home_defRating', 110)
            away_def = features_dict.get('away_defRating', 110)

            # Home team expected points = their offense vs opponent's defense
            home_expected = (home_off + away_def) / 2
            away_expected = (away_off + home_def) / 2

            # Add home court advantage (~3 points)
            home_expected += 3

            # Determine outcome (with some randomness)
            home_wins_prob = home_expected / (home_expected + away_expected)
            outcome = 1 if random.random() < home_wins_prob else 0

            X.append(features)
            y.append(outcome)

            if not self.feature_names:
                self.feature_names = list(features_dict.keys())

        print(f"   ✅ Generated {len(X)} synthetic training samples")
        return np.array(X), np.array(y)

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

    def save_models(self, filepath: str = "nba_enhanced_models.pkl"):
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
    """Train enhanced NBA models"""

    trainer = NBAEnhancedTrainer()

    # Collect enhanced training data
    X, y = trainer.collect_enhanced_training_data(num_games=500)

    if len(X) > 0:
        # Train models
        trainer.train_models(X, y)

        # Save models
        trainer.save_models()

        print(f"\n✅ Enhanced NBA ML models ready!")
        print(f"   Models trained with {X.shape[1]} advanced features")
        print(f"   Including offensive rating, defensive rating, pace, FG%, etc.")

    else:
        print(f"\n❌ Failed to collect training data")


if __name__ == "__main__":
    main()
