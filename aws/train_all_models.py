#!/usr/bin/env python3
"""
AWS EC2 NHL Model Training Script
Trains all NHL models with sklearn 1.6.1 for compatibility
"""

import os
import sys
import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
import pickle
import time

# Output directory for models
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "trained_models")
os.makedirs(OUTPUT_DIR, exist_ok=True)

class NHLModelTrainer:
    """Unified NHL model trainer for EC2"""

    def __init__(self):
        self.nhl_api_base = "https://api-web.nhle.com/v1"
        self.hockey_api_key = "960c628e1c91c4b1f125e1eec52ad862"
        self.hockey_api_base = "https://v1.hockey.api-sports.io"
        self.hockey_headers = {'x-apisports-key': self.hockey_api_key}

        print("=" * 60)
        print("NHL EC2 Model Training Script")
        print(f"sklearn version: {self._get_sklearn_version()}")
        print(f"Output directory: {OUTPUT_DIR}")
        print("=" * 60)

    def _get_sklearn_version(self):
        import sklearn
        return sklearn.__version__

    def fetch_nhl_games(self, start_date: str, end_date: str) -> list:
        """Fetch completed NHL games in date range"""
        games = []
        current = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            url = f"{self.nhl_api_base}/score/{date_str}"

            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    day_games = data.get('games', [])

                    for game in day_games:
                        state = game.get('gameState', '')
                        if state in ['FINAL', 'OFF']:
                            games.append(game)
            except Exception as e:
                print(f"Error fetching {date_str}: {e}")

            current += timedelta(days=1)
            time.sleep(0.1)  # Rate limiting

        return games

    def get_first_period_goals(self, game_id: int, home_team_id: int) -> tuple:
        """Get first period goals from play-by-play"""
        try:
            url = f"{self.nhl_api_base}/gamecenter/{game_id}/play-by-play"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                home_1p = 0
                away_1p = 0

                for play in data.get('plays', []):
                    if play.get('typeDescKey') == 'goal':
                        period = play.get('periodDescriptor', {}).get('number', 0)
                        if period == 1:
                            team_id = play.get('details', {}).get('eventOwnerTeamId')
                            if team_id == home_team_id:
                                home_1p += 1
                            else:
                                away_1p += 1

                return home_1p, away_1p
        except:
            pass

        return 0, 0

    def build_totals_dataset(self, games: list) -> pd.DataFrame:
        """Build training dataset for totals prediction"""
        print(f"\nBuilding totals dataset from {len(games)} games...")

        rows = []
        for i, game in enumerate(games):
            try:
                home = game.get('homeTeam', {})
                away = game.get('awayTeam', {})

                home_score = home.get('score', 0)
                away_score = away.get('score', 0)
                total = home_score + away_score

                game_id = game.get('id')
                home_team_id = home.get('id')

                # Get first period goals
                home_1p, away_1p = self.get_first_period_goals(game_id, home_team_id)

                # Extract features
                row = {
                    'home_team': home.get('abbrev', ''),
                    'away_team': away.get('abbrev', ''),
                    'home_score': home_score,
                    'away_score': away_score,
                    'total_goals': total,
                    'home_1p_goals': home_1p,
                    'away_1p_goals': away_1p,
                    'first_period_total': home_1p + away_1p,
                    'home_over_half_1p': 1 if home_1p >= 1 else 0,
                    'away_over_half_1p': 1 if away_1p >= 1 else 0,
                    'period_over_1_5': 1 if (home_1p + away_1p) >= 2 else 0,
                }
                rows.append(row)

                if (i + 1) % 50 == 0:
                    print(f"  Processed {i+1}/{len(games)} games")

            except Exception as e:
                continue

        df = pd.DataFrame(rows)
        print(f"  Dataset built: {len(df)} rows")
        return df

    def train_totals_models(self, df: pd.DataFrame):
        """Train game totals prediction models"""
        print("\n" + "=" * 60)
        print("Training Game Totals Models")
        print("=" * 60)

        # Prepare features
        team_dummies = pd.get_dummies(df[['home_team', 'away_team']], prefix=['home', 'away'])
        X = team_dummies
        y = df['total_goals']

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        models = {
            'linear': LinearRegression(),
            'ridge': Ridge(alpha=1.0),
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boost': GradientBoostingRegressor(n_estimators=100, random_state=42),
        }

        trained_models = {}
        for name, model in models.items():
            print(f"\n  Training {name}...")
            model.fit(X_train, y_train)
            score = model.score(X_test, y_test)
            print(f"    R2 Score: {score:.4f}")
            trained_models[name] = model

        # Save models
        filepath = os.path.join(OUTPUT_DIR, "nhl_totals_models.pkl")
        with open(filepath, 'wb') as f:
            pickle.dump({
                'models': trained_models,
                'feature_names': list(X.columns),
                'sklearn_version': self._get_sklearn_version()
            }, f)
        print(f"\n  Saved to {filepath}")

        return trained_models

    def train_first_period_models(self, df: pd.DataFrame):
        """Train first period prediction models"""
        print("\n" + "=" * 60)
        print("Training First Period Models")
        print("=" * 60)

        team_dummies = pd.get_dummies(df[['home_team', 'away_team']], prefix=['home', 'away'])
        X = team_dummies

        targets = {
            'home_over_half_1p': df['home_over_half_1p'],
            'away_over_half_1p': df['away_over_half_1p'],
            'period_over_1_5': df['period_over_1_5']
        }

        trained_models = {}
        for target_name, y in targets.items():
            print(f"\n  Training {target_name}...")
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)

            score = model.score(X_test, y_test)
            print(f"    Accuracy: {score:.4f}")

            trained_models[target_name] = model

        # Save models
        filepath = os.path.join(OUTPUT_DIR, "nhl_first_period_models.pkl")
        with open(filepath, 'wb') as f:
            pickle.dump({
                'models': trained_models,
                'feature_names': list(X.columns),
                'sklearn_version': self._get_sklearn_version()
            }, f)
        print(f"\n  Saved to {filepath}")

        return trained_models

    def train_moneyline_models(self):
        """Train moneyline prediction models using hockey API"""
        print("\n" + "=" * 60)
        print("Training Moneyline Models (Hockey API)")
        print("=" * 60)

        url = f"{self.hockey_api_base}/games"
        params = {'league': 57, 'season': 2024}

        try:
            response = requests.get(url, headers=self.hockey_headers, params=params, timeout=60)
            if response.status_code != 200:
                print(f"  API error: {response.status_code}")
                return None

            data = response.json()
            games = data.get('response', [])
            completed = [g for g in games if g.get('status', {}).get('short') == 'FT']
            print(f"  Found {len(completed)} completed games")

            # Build dataset
            rows = []
            for game in completed[:400]:
                teams = game.get('teams', {})
                scores = game.get('scores', {})

                home = teams.get('home', {}).get('name', '')
                away = teams.get('away', {}).get('name', '')
                home_score = scores.get('home', 0)
                away_score = scores.get('away', 0)

                if home and away:
                    rows.append({
                        'home_team': home,
                        'away_team': away,
                        'home_win': 1 if home_score > away_score else 0
                    })

            df = pd.DataFrame(rows)
            print(f"  Dataset: {len(df)} games")

            # Train model
            team_dummies = pd.get_dummies(df[['home_team', 'away_team']], prefix=['home', 'away'])
            X = team_dummies
            y = df['home_win']

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            models = {}

            print("\n  Training Random Forest...")
            rf = RandomForestClassifier(n_estimators=150, max_depth=12, random_state=42)
            rf.fit(X_train, y_train)
            print(f"    Accuracy: {rf.score(X_test, y_test):.4f}")
            models['random_forest'] = rf

            print("\n  Training Gradient Boosting...")
            gb = GradientBoostingClassifier(n_estimators=150, max_depth=6, random_state=42)
            gb.fit(X_train, y_train)
            print(f"    Accuracy: {gb.score(X_test, y_test):.4f}")
            models['gradient_boosting'] = gb

            # Save
            scaler = StandardScaler()
            scaler.fit(X)

            filepath = os.path.join(OUTPUT_DIR, "nhl_enhanced_models.pkl")
            with open(filepath, 'wb') as f:
                pickle.dump({
                    'models': models,
                    'scaler': scaler,
                    'feature_names': list(X.columns),
                    'sklearn_version': self._get_sklearn_version()
                }, f)
            print(f"\n  Saved to {filepath}")

            return models

        except Exception as e:
            print(f"  Error: {e}")
            return None


def main():
    print("\n" + "=" * 60)
    print("AWS EC2 NHL MODEL TRAINING")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    trainer = NHLModelTrainer()

    # Get date range (last 45 days of games)
    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=45)

    # Fetch games
    print(f"\nFetching games from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
    games = trainer.fetch_nhl_games(
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d')
    )
    print(f"Fetched {len(games)} completed games")

    if len(games) > 0:
        # Build dataset
        df = trainer.build_totals_dataset(games)

        # Train models
        trainer.train_totals_models(df)
        trainer.train_first_period_models(df)
        trainer.train_moneyline_models()

        print("\n" + "=" * 60)
        print("TRAINING COMPLETE")
        print(f"Models saved to: {OUTPUT_DIR}")
        print("=" * 60)

        # List output files
        print("\nGenerated files:")
        for f in os.listdir(OUTPUT_DIR):
            filepath = os.path.join(OUTPUT_DIR, f)
            size = os.path.getsize(filepath) / 1024
            print(f"  {f}: {size:.1f} KB")
    else:
        print("No games found - training aborted")


if __name__ == "__main__":
    main()
