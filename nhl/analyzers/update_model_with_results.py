#!/usr/bin/env python3
"""
NHL Model Update System
Updates models with actual game results for continuous learning
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pickle
import argparse
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nhl_enhanced_data import NHLEnhancedData

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier


class NHLModelUpdater:
    """Update NHL models with actual results"""

    def __init__(self,
                 hockey_api_key: str = '960c628e1c91c4b1f125e1eec52ad862',
                 odds_api_key: str = '518c226b561ad7586ec8c5dd1144e3fb'):

        self.hockey_api_key = hockey_api_key
        self.odds_api_key = odds_api_key
        self.hockey_base_url = "https://v1.hockey.api-sports.io"

        # Load current models
        self.load_models()

        # Initialize data integrator
        self.data_integrator = NHLEnhancedData()

        # Training history database
        self.training_db = Path('training_history.csv')

    def load_models(self):
        """Load current trained models"""
        try:
            with open('nhl_enhanced_models.pkl', 'rb') as f:
                model_data = pickle.load(f)

            self.models = model_data['models']
            self.scaler = model_data['scaler']
            self.feature_names = model_data['feature_names']

            print(f"✅ Loaded current models")
        except FileNotFoundError:
            print(f"❌ No models found. Train initial models first!")
            sys.exit(1)

    def get_finished_games(self, date_str: str) -> list:
        """Get finished games for a specific date"""
        url = f"{self.hockey_base_url}/games"
        headers = {'x-apisports-key': self.hockey_api_key}

        params = {
            'league': 57,
            'season': 2025,
            'date': date_str
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                games = data.get('response', [])

                # Filter for finished games only
                finished = [g for g in games if g.get('status', {}).get('short') == 'FT']
                return finished
            return []
        except Exception as e:
            print(f"Error: {e}")
            return []

    def collect_game_training_data(self, game: dict) -> dict:
        """Collect training data from a finished game"""
        teams = game.get('teams', {})
        scores = game.get('scores', {})

        home_team = teams.get('home', {}).get('name', '')
        away_team = teams.get('away', {}).get('name', '')
        home_score = scores.get('home', 0)
        away_score = scores.get('away', 0)

        # Use default odds (we don't have historical odds for this)
        # In production, you'd want to store odds when making predictions
        home_odds = 2.0
        away_odds = 2.0

        # Build features
        features_dict = self.data_integrator.build_enhanced_features(
            home_team, away_team, home_odds, away_odds, season=2024
        )

        if not features_dict:
            return None

        # Determine outcome (1 = home win, 0 = away win)
        outcome = 1 if home_score > away_score else 0

        return {
            'date': game.get('date', ''),
            'home_team': home_team,
            'away_team': away_team,
            'home_score': home_score,
            'away_score': away_score,
            'outcome': outcome,
            'features': features_dict
        }

    def save_training_data(self, training_data: list):
        """Save new training data to database"""
        if not training_data:
            return

        # Convert to DataFrame
        records = []
        for data in training_data:
            record = {
                'date': data['date'],
                'home_team': data['home_team'],
                'away_team': data['away_team'],
                'home_score': data['home_score'],
                'away_score': data['away_score'],
                'outcome': data['outcome']
            }

            # Add all features
            record.update(data['features'])
            records.append(record)

        df_new = pd.DataFrame(records)

        # Append to existing database
        if self.training_db.exists():
            df_existing = pd.read_csv(self.training_db)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df_combined = df_new

        # Remove duplicates (same game played twice)
        df_combined = df_combined.drop_duplicates(
            subset=['date', 'home_team', 'away_team'],
            keep='last'
        )

        df_combined.to_csv(self.training_db, index=False)
        print(f"   💾 Saved {len(df_new)} new games to training database")
        print(f"   📊 Total games in database: {len(df_combined)}")

    def incremental_train(self, training_data: list, retrain_full: bool = False):
        """
        Update models with new data

        Args:
            training_data: New game data
            retrain_full: If True, retrain on all historical data
        """
        if not training_data:
            print("   ⚠️  No new training data")
            return

        print(f"\n🔄 Updating models with {len(training_data)} new games...")

        # Extract features and labels
        X_new = []
        y_new = []

        for data in training_data:
            features = np.array([data['features'][name] for name in self.feature_names])
            X_new.append(features)
            y_new.append(data['outcome'])

        X_new = np.array(X_new)
        y_new = np.array(y_new)

        # Scale features
        X_new_scaled = self.scaler.transform(X_new)

        if retrain_full:
            # Retrain on all historical data
            print("   🔨 Retraining on all historical data...")
            self.full_retrain()
        else:
            # Incremental update (partial_fit or just retrain on recent + new)
            print("   📈 Incremental model update...")

            # For tree-based models, we need to retrain
            # Load recent historical data (last 100 games)
            if self.training_db.exists():
                df_history = pd.read_csv(self.training_db)

                # Get last 100 games
                recent_games = df_history.tail(100)

                # Extract features
                feature_cols = [col for col in recent_games.columns
                               if col not in ['date', 'home_team', 'away_team',
                                            'home_score', 'away_score', 'outcome']]

                X_recent = recent_games[feature_cols].values
                y_recent = recent_games['outcome'].values

                # Combine with new data
                X_combined = np.vstack([X_recent, X_new])
                y_combined = np.hstack([y_recent, y_new])

                # Scale
                X_combined_scaled = self.scaler.transform(X_combined)

                # Retrain models on combined data
                for model_name, model in self.models.items():
                    print(f"   Training {model_name}...")

                    if model_name == 'random_forest':
                        new_model = RandomForestClassifier(
                            n_estimators=200,
                            max_depth=15,
                            min_samples_split=10,
                            random_state=42,
                            n_jobs=-1
                        )
                    else:
                        new_model = GradientBoostingClassifier(
                            n_estimators=200,
                            max_depth=8,
                            learning_rate=0.1,
                            random_state=42
                        )

                    new_model.fit(X_combined_scaled, y_combined)
                    self.models[model_name] = new_model

                    # Evaluate
                    score = new_model.score(X_combined_scaled, y_combined)
                    print(f"      Accuracy: {score:.3f}")

        # Save updated models
        self.save_models()

    def full_retrain(self):
        """Retrain models on all historical data"""
        if not self.training_db.exists():
            print("   ❌ No training database found")
            return

        df_history = pd.read_csv(self.training_db)
        print(f"   📊 Retraining on {len(df_history)} total games...")

        # Extract features
        feature_cols = [col for col in df_history.columns
                       if col not in ['date', 'home_team', 'away_team',
                                    'home_score', 'away_score', 'outcome']]

        X = df_history[feature_cols].values
        y = df_history['outcome'].values

        # Scale
        X_scaled = self.scaler.fit_transform(X)

        # Retrain all models
        for model_name in self.models.keys():
            print(f"   Training {model_name}...")

            if model_name == 'random_forest':
                model = RandomForestClassifier(
                    n_estimators=200,
                    max_depth=15,
                    min_samples_split=10,
                    random_state=42,
                    n_jobs=-1
                )
            else:
                model = GradientBoostingClassifier(
                    n_estimators=200,
                    max_depth=8,
                    learning_rate=0.1,
                    random_state=42
                )

            model.fit(X_scaled, y)
            self.models[model_name] = model

            score = model.score(X_scaled, y)
            print(f"      Accuracy: {score:.3f}")

    def save_models(self):
        """Save updated models"""
        model_data = {
            'models': self.models,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'last_updated': datetime.now().isoformat()
        }

        # Backup old models
        if Path('nhl_enhanced_models.pkl').exists():
            backup_name = f"nhl_enhanced_models_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
            os.rename('nhl_enhanced_models.pkl', backup_name)
            print(f"   💾 Backed up old models to: {backup_name}")

        # Save new models
        with open('nhl_enhanced_models.pkl', 'wb') as f:
            pickle.dump(model_data, f)

        print(f"   ✅ Updated models saved!")

    def update_with_date(self, date_str: str, retrain_full: bool = False):
        """Update models with results from a specific date"""
        print(f"\n🏒 NHL MODEL UPDATE - {date_str}")
        print("=" * 80)

        # Get finished games
        games = self.get_finished_games(date_str)

        if not games:
            print(f"\n⚠️  No finished games found for {date_str}")
            return

        print(f"\n✅ Found {len(games)} finished games")

        # Collect training data
        training_data = []
        for game in games:
            data = self.collect_game_training_data(game)
            if data:
                training_data.append(data)

                teams = game.get('teams', {})
                scores = game.get('scores', {})
                print(f"   📝 {teams.get('away', {}).get('name')} {scores.get('away')} @ "
                      f"{teams.get('home', {}).get('name')} {scores.get('home')}")

        # Save to training database
        self.save_training_data(training_data)

        # Update models
        self.incremental_train(training_data, retrain_full=retrain_full)

        print(f"\n✅ Model update complete!")

    def auto_update_recent(self, days_back: int = 7, retrain_full: bool = False):
        """Automatically update with results from last N days"""
        print(f"\n🔄 AUTO-UPDATE: Last {days_back} days")
        print("=" * 80)

        today = datetime.now()
        total_games = 0

        for i in range(days_back, 0, -1):
            check_date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
            print(f"\n📅 Checking {check_date}...")

            games = self.get_finished_games(check_date)

            if games:
                print(f"   Found {len(games)} finished games")
                total_games += len(games)

                # Collect and save data
                training_data = []
                for game in games:
                    data = self.collect_game_training_data(game)
                    if data:
                        training_data.append(data)

                self.save_training_data(training_data)

        if total_games > 0:
            print(f"\n📊 Total new games: {total_games}")
            print(f"🔨 Retraining models...")

            # Do full retrain with all accumulated data
            self.full_retrain()
            self.save_models()
        else:
            print(f"\n⚠️  No new games found")


def main():
    parser = argparse.ArgumentParser(description='Update NHL models with actual results')
    parser.add_argument('--date', type=str,
                       help='Update with specific date (YYYY-MM-DD)')
    parser.add_argument('--auto', action='store_true',
                       help='Auto-update with last 7 days of results')
    parser.add_argument('--days', type=int, default=7,
                       help='Number of days back for auto-update (default: 7)')
    parser.add_argument('--full-retrain', action='store_true',
                       help='Do full retrain on all historical data')

    args = parser.parse_args()

    updater = NHLModelUpdater()

    if args.auto:
        updater.auto_update_recent(days_back=args.days, retrain_full=args.full_retrain)
    elif args.date:
        updater.update_with_date(args.date, retrain_full=args.full_retrain)
    else:
        # Default: update yesterday's games
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        updater.update_with_date(yesterday, retrain_full=args.full_retrain)


if __name__ == "__main__":
    main()
