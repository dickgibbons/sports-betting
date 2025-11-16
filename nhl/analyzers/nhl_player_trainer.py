#!/usr/bin/env python3
"""
NHL Player Shots Prediction Model Trainer
Builds ML models to predict shots on goal per player using historical boxscore data
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


class NHLPlayerTrainer:
    """Train ML models to predict player shots on goal"""

    def __init__(self):
        self.nhl_base_url = "https://api-web.nhle.com/v1"
        self.players_data = []
        self.models = {}
        self.scaler = None
        self.feature_names = []

    def get_team_roster(self, team_abbrev: str, season: int = 2024) -> list:
        """Get team roster with player IDs"""
        try:
            url = f"{self.nhl_base_url}/roster/{team_abbrev}/{season}{season+1}"
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                players = []

                # Get forwards and defensemen
                for position in ['forwards', 'defensemen']:
                    for player in data.get(position, []):
                        players.append({
                            'id': player.get('id'),
                            'name': player.get('firstName', {}).get('default', '') + ' ' +
                                   player.get('lastName', {}).get('default', ''),
                            'position': player.get('positionCode', ''),
                            'team': team_abbrev
                        })

                return players
            return []
        except Exception as e:
            print(f"Error getting roster for {team_abbrev}: {e}")
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

    def get_player_season_stats(self, player_id: int, season: str = "20242025") -> dict:
        """Get player's season statistics"""
        try:
            url = f"{self.nhl_base_url}/player/{player_id}/landing"
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()

                # Find current season stats
                for stat_season in data.get('featuredStats', {}).get('regularSeason', {}).get('subSeason', []):
                    if str(stat_season.get('season')) == season:
                        return {
                            'games_played': stat_season.get('gamesPlayed', 0),
                            'goals': stat_season.get('goals', 0),
                            'assists': stat_season.get('assists', 0),
                            'points': stat_season.get('points', 0),
                            'shots': stat_season.get('shots', 0),
                            'avg_toi': stat_season.get('avgToi', '0:00')
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

    def extract_player_features(self, game_data: dict, player_id: int, team: str) -> dict:
        """Extract features for a player from game data"""
        boxscore = game_data.get('boxscore', {})
        player_stats = boxscore.get('playerByGameStats', {})

        # Determine if home or away
        is_home = team == game_data.get('home')
        team_data = player_stats.get('homeTeam' if is_home else 'awayTeam', {})

        # Find player in forwards or defense
        player_game_stats = None
        for position in ['forwards', 'defense']:
            for player in team_data.get(position, []):
                if player.get('playerId') == player_id:
                    player_game_stats = player
                    break
            if player_game_stats:
                break

        if not player_game_stats:
            return None

        # Extract actual shots (target variable)
        actual_shots = player_game_stats.get('sog', 0)

        # Get season stats for this player
        season_stats = game_data.get('player_season_stats', {}).get(player_id, {})

        # Calculate rolling averages (simplified - in production would use actual rolling windows)
        games_played = season_stats.get('games_played', 1)
        total_shots = season_stats.get('shots', 0)
        avg_shots_per_game = total_shots / games_played if games_played > 0 else 0

        # Get TOI
        toi_str = player_game_stats.get('toi', '0:00')
        try:
            toi_parts = toi_str.split(':')
            toi_minutes = int(toi_parts[0]) + int(toi_parts[1]) / 60
        except:
            toi_minutes = 0

        features = {
            # Player features
            'position_C': 1 if player_game_stats.get('position') == 'C' else 0,
            'position_LW': 1 if player_game_stats.get('position') == 'LW' else 0,
            'position_RW': 1 if player_game_stats.get('position') == 'RW' else 0,
            'position_D': 1 if player_game_stats.get('position') == 'D' else 0,

            # Season averages
            'avg_shots_per_game': avg_shots_per_game,
            'season_shooting_pct': (season_stats.get('goals', 0) / total_shots * 100) if total_shots > 0 else 0,
            'season_points_per_game': season_stats.get('points', 0) / games_played if games_played > 0 else 0,

            # Game context
            'toi_minutes': toi_minutes,
            'is_home': 1 if is_home else 0,

            # Opponent strength (simplified)
            'opp_team_strength': 0.5,  # Would calculate from team stats

            # Target variable
            'actual_shots': actual_shots
        }

        return features

    def build_training_dataset(self, days_back: int = 30):
        """Build training dataset from recent games"""
        print(f"\n📊 Building player shots training dataset...")
        print(f"   Looking back {days_back} days")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        # Get completed games
        games = self.get_completed_games(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )

        print(f"   Found {len(games)} completed games")

        # Get all teams
        teams = ['BOS', 'BUF', 'DET', 'FLA', 'MTL', 'OTT', 'TBL', 'TOR',
                'CAR', 'CBJ', 'NJD', 'NYI', 'NYR', 'PHI', 'PIT', 'WSH',
                'CHI', 'COL', 'DAL', 'MIN', 'NSH', 'STL', 'WPG',
                'ANA', 'CGY', 'EDM', 'LAK', 'SJS', 'SEA', 'VAN', 'VGK', 'UTA']

        training_data = []

        for game in games[:100]:  # Limit to 100 games for initial training
            print(f"   Processing game {game['id']}...", end='\r')

            # Get boxscore
            boxscore = self.get_game_boxscore(game['id'])
            if not boxscore:
                continue

            game['boxscore'] = boxscore

            # Get season stats for players (cache this)
            game['player_season_stats'] = {}

            # Process both teams
            for team in [game['home'], game['away']]:
                roster = self.get_team_roster(team)

                for player in roster:
                    # Get season stats
                    if player['id'] not in game['player_season_stats']:
                        stats = self.get_player_season_stats(player['id'])
                        if stats:
                            game['player_season_stats'][player['id']] = stats

                    # Extract features
                    features = self.extract_player_features(game, player['id'], team)
                    if features and features['toi_minutes'] > 0:  # Only include players who played
                        features['player_id'] = player['id']
                        features['player_name'] = player['name']
                        features['game_id'] = game['id']
                        training_data.append(features)

        print(f"\n   ✅ Collected {len(training_data)} player-game samples")

        return pd.DataFrame(training_data)

    def train_models(self, df: pd.DataFrame):
        """Train ML models on player shots data"""
        print(f"\n🤖 Training player shots prediction models...")

        # Define features
        self.feature_names = [
            'position_C', 'position_LW', 'position_RW', 'position_D',
            'avg_shots_per_game', 'season_shooting_pct', 'season_points_per_game',
            'toi_minutes', 'is_home', 'opp_team_strength'
        ]

        # Prepare data
        X = df[self.feature_names].fillna(0)
        y = df['actual_shots']

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

        print(f"   📊 Random Forest MAE: {mae_rf:.2f} shots")
        print(f"   📊 Gradient Boosting MAE: {mae_gb:.2f} shots")

    def save_models(self, filename: str = 'nhl_player_models.pkl'):
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
    parser = argparse.ArgumentParser(description='Train NHL player shots prediction models')
    parser.add_argument('--days', type=int, default=30,
                       help='Days of historical data to use (default: 30)')

    args = parser.parse_args()

    print("🏒 NHL PLAYER SHOTS PREDICTION TRAINER")
    print("=" * 80)

    trainer = NHLPlayerTrainer()

    # Build dataset
    df = trainer.build_training_dataset(days_back=args.days)

    if df.empty:
        print("\n❌ No training data collected")
        sys.exit(1)

    # Train models
    trainer.train_models(df)

    # Save models
    trainer.save_models()

    print("\n✅ Player shots models ready!")


if __name__ == "__main__":
    main()
