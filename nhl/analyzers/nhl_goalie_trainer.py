#!/usr/bin/env python3
"""
NHL Goalie Saves Prediction Model Trainer
Builds ML models to predict saves per goalie using historical boxscore data
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pickle
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import argparse
import sys


class NHLGoalieTrainer:
    """Train ML models to predict goalie saves"""

    def __init__(self):
        self.nhl_base_url = "https://api-web.nhle.com/v1"
        self.goalies_data = []
        self.models = {}
        self.scaler = None
        self.feature_names = []

    def get_team_goalies(self, team_abbrev: str, season: int = 2024) -> list:
        """Get team's goalies with player IDs"""
        try:
            url = f"{self.nhl_base_url}/roster/{team_abbrev}/{season}{season+1}"
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                goalies = []

                for goalie in data.get('goalies', []):
                    goalies.append({
                        'id': goalie.get('id'),
                        'name': goalie.get('firstName', {}).get('default', '') + ' ' +
                               goalie.get('lastName', {}).get('default', ''),
                        'position': 'G',
                        'team': team_abbrev
                    })

                return goalies
            return []
        except Exception as e:
            print(f"Error getting goalies for {team_abbrev}: {e}")
            return []

    def get_game_boxscore(self, game_id: int) -> dict:
        """Get boxscore data for a completed game"""
        try:
            url = f"{self.nhl_base_url}/gamecenter/{game_id}/boxscore"
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error getting boxscore for game {game_id}: {e}")
            return None

    def get_goalie_season_stats(self, goalie_id: int, season: str = "20242025") -> dict:
        """Get goalie's season statistics"""
        try:
            url = f"{self.nhl_base_url}/player/{goalie_id}/landing"
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()

                # Find current season stats
                for stat_season in data.get('featuredStats', {}).get('regularSeason', {}).get('subSeason', []):
                    if str(stat_season.get('season')) == season:
                        return {
                            'games_played': stat_season.get('gamesPlayed', 0),
                            'games_started': stat_season.get('gamesStarted', 0),
                            'wins': stat_season.get('wins', 0),
                            'losses': stat_season.get('losses', 0),
                            'saves': stat_season.get('saves', 0),
                            'shots_against': stat_season.get('shotsAgainst', 0),
                            'save_pct': stat_season.get('savePct', 0),
                            'gaa': stat_season.get('goalsAgainstAvg', 0),
                            'shutouts': stat_season.get('shutouts', 0)
                        }

                return None
            return None
        except Exception as e:
            return None

    def get_completed_games(self, start_date: str, end_date: str) -> list:
        """Get list of completed games in date range"""
        games = []
        current = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            try:
                url = f"{self.nhl_base_url}/schedule/{date_str}"
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    for day in data.get('gameWeek', []):
                        if day.get('date') == date_str:
                            for game in day.get('games', []):
                                if game.get('gameState') in ['OFF', 'FINAL']:
                                    games.append({
                                        'id': game.get('id'),
                                        'date': date_str,
                                        'home': game.get('homeTeam', {}).get('abbrev', ''),
                                        'away': game.get('awayTeam', {}).get('abbrev', '')
                                    })
            except:
                pass

            current += timedelta(days=1)

        return games

    def extract_goalie_features(self, game_data: dict, goalie_id: int, team: str) -> dict:
        """Extract features for a goalie from game data"""
        boxscore = game_data.get('boxscore', {})
        player_stats = boxscore.get('playerByGameStats', {})

        # Determine if home or away
        is_home = team == game_data.get('home')
        team_data = player_stats.get('homeTeam' if is_home else 'awayTeam', {})
        opp_data = player_stats.get('awayTeam' if is_home else 'homeTeam', {})

        # Find goalie
        goalie_game_stats = None
        for goalie in team_data.get('goalies', []):
            if goalie.get('playerId') == goalie_id:
                goalie_game_stats = goalie
                break

        if not goalie_game_stats:
            return None

        # Only include starters or goalies who played significant time
        if not goalie_game_stats.get('starter', False) and goalie_game_stats.get('shotsAgainst', 0) < 5:
            return None

        # Extract actual saves (target variable)
        actual_saves = goalie_game_stats.get('saves', 0)
        shots_against = goalie_game_stats.get('shotsAgainst', 0)

        if shots_against == 0:
            return None

        # Get season stats
        season_stats = game_data.get('goalie_season_stats', {}).get(goalie_id, {})

        # Calculate averages
        games_played = season_stats.get('games_played', 1)
        total_saves = season_stats.get('saves', 0)
        avg_saves_per_game = total_saves / games_played if games_played > 0 else 0

        # Get opponent shooting strength (total shots in this game)
        opp_total_shots = sum([
            p.get('sog', 0) for p in opp_data.get('forwards', [])
        ]) + sum([
            p.get('sog', 0) for p in opp_data.get('defense', [])
        ])

        features = {
            # Goalie season stats
            'avg_saves_per_game': avg_saves_per_game,
            'season_save_pct': season_stats.get('save_pct', 0.900),
            'season_gaa': season_stats.get('gaa', 3.0),
            'games_played': games_played,
            'is_starter': 1 if goalie_game_stats.get('starter', False) else 0,

            # Opponent strength
            'opp_shots_total': opp_total_shots,
            'opp_shooting_strength': opp_total_shots / 30.0 if opp_total_shots > 0 else 1.0,

            # Game context
            'is_home': 1 if is_home else 0,

            # Target variables
            'actual_saves': actual_saves,
            'actual_shots_against': shots_against,
            'actual_save_pct': actual_saves / shots_against if shots_against > 0 else 0
        }

        return features

    def build_training_dataset(self, days_back: int = 30):
        """Build training dataset from recent games"""
        print(f"\n📊 Building goalie saves training dataset...")
        print(f"   Looking back {days_back} days")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        # Get completed games
        games = self.get_completed_games(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )

        print(f"   Found {len(games)} completed games")

        training_data = []

        for game in games[:100]:  # Limit to 100 games for initial training
            print(f"   Processing game {game['id']}...", end='\r')

            # Get boxscore
            boxscore = self.get_game_boxscore(game['id'])
            if not boxscore:
                continue

            game['boxscore'] = boxscore

            # Get season stats for goalies (cache this)
            game['goalie_season_stats'] = {}

            # Process both teams
            for team in [game['home'], game['away']]:
                goalies = self.get_team_goalies(team)

                for goalie in goalies:
                    # Get season stats
                    if goalie['id'] not in game['goalie_season_stats']:
                        stats = self.get_goalie_season_stats(goalie['id'])
                        if stats:
                            game['goalie_season_stats'][goalie['id']] = stats

                    # Extract features
                    features = self.extract_goalie_features(game, goalie['id'], team)
                    if features:
                        features['goalie_id'] = goalie['id']
                        features['goalie_name'] = goalie['name']
                        features['game_id'] = game['id']
                        training_data.append(features)

        print(f"\n   ✅ Collected {len(training_data)} goalie-game samples")

        return pd.DataFrame(training_data)

    def train_models(self, df: pd.DataFrame):
        """Train ML models on goalie saves data"""
        print(f"\n🤖 Training goalie saves prediction models...")

        # Define features
        self.feature_names = [
            'avg_saves_per_game', 'season_save_pct', 'season_gaa',
            'games_played', 'is_starter',
            'opp_shots_total', 'opp_shooting_strength',
            'is_home'
        ]

        # Prepare data
        X = df[self.feature_names].fillna(0)
        y = df['actual_saves']

        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Train Random Forest
        print("   Training Random Forest...")
        rf_model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        rf_model.fit(X_train_scaled, y_train)
        rf_score = rf_model.score(X_test_scaled, y_test)

        # Train Gradient Boosting
        print("   Training Gradient Boosting...")
        gb_model = GradientBoostingRegressor(n_estimators=100, random_state=42)
        gb_model.fit(X_train_scaled, y_train)
        gb_score = gb_model.score(X_test_scaled, y_test)

        self.models = {
            'random_forest': rf_model,
            'gradient_boosting': gb_model
        }

        print(f"\n   ✅ Random Forest R²: {rf_score:.3f}")
        print(f"   ✅ Gradient Boosting R²: {gb_score:.3f}")

        # Test predictions
        y_pred_rf = rf_model.predict(X_test_scaled)
        y_pred_gb = gb_model.predict(X_test_scaled)

        mae_rf = np.mean(np.abs(y_test - y_pred_rf))
        mae_gb = np.mean(np.abs(y_test - y_pred_gb))

        print(f"   📊 Random Forest MAE: {mae_rf:.2f} saves")
        print(f"   📊 Gradient Boosting MAE: {mae_gb:.2f} saves")

    def save_models(self, filename: str = 'nhl_goalie_models.pkl'):
        """Save trained models"""
        model_data = {
            'models': self.models,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'trained_date': datetime.now().isoformat()
        }

        with open(filename, 'wb') as f:
            pickle.dump(model_data, f)

        print(f"\n💾 Models saved to: {filename}")


def main():
    parser = argparse.ArgumentParser(description='Train NHL goalie saves prediction models')
    parser.add_argument('--days', type=int, default=30,
                       help='Days of historical data to use (default: 30)')

    args = parser.parse_args()

    print("🏒 NHL GOALIE SAVES PREDICTION TRAINER")
    print("=" * 80)

    trainer = NHLGoalieTrainer()

    # Build dataset
    df = trainer.build_training_dataset(days_back=args.days)

    if df.empty:
        print("\n❌ No training data collected")
        sys.exit(1)

    # Train models
    trainer.train_models(df)

    # Save models
    trainer.save_models()

    print("\n✅ Goalie saves models ready!")


if __name__ == "__main__":
    main()
