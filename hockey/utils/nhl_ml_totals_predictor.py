#!/usr/bin/env python3
"""
NHL ML-Based Totals Predictor
Uses multiple machine learning models to predict:
- Game totals (vs market lines)
- First period team over 0.5 goals probability
- First period over 1.5 total goals probability
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
# import xgboost as xgb  # Temporarily disabled due to sklearn compatibility
import joblib
import os
from collections import defaultdict


class NHLMLTotalsPredictor:
    """ML-based NHL totals and first period predictions"""

    def __init__(self):
        self.nhl_api_base = "https://api-web.nhle.com/v1"
        self.odds_api_key = '518c226b561ad7586ec8c5dd1144e3fb'

        # Models for game totals
        self.totals_models = {
            'linear': LinearRegression(),
            'ridge': Ridge(alpha=1.0),
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boost': GradientBoostingRegressor(n_estimators=100, random_state=42),
            # 'xgboost': xgb.XGBRegressor(n_estimators=100, random_state=42)  # Temporarily disabled
        }

        # Models for first period probabilities
        self.first_period_models = {
            'home_over_half': RandomForestClassifier(n_estimators=100, random_state=42),
            'away_over_half': RandomForestClassifier(n_estimators=100, random_state=42),
            'period_over_1_5': RandomForestClassifier(n_estimators=100, random_state=42)
        }

        self.scaler = StandardScaler()
        self.team_stats = {}
        self.model_dir = '/Users/dickgibbons/AI Projects/sports-betting/nhl/models'
        os.makedirs(self.model_dir, exist_ok=True)

        print("🏒 NHL ML Totals Predictor initialized")

    def fetch_historical_data(self, start_date: str, end_date: str):
        """Fetch historical NHL game data for training using new API"""

        print(f"\n📊 Fetching NHL historical data from {start_date} to {end_date}...")

        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        games_data = []
        current = start

        while current <= end:
            date_str = current.strftime('%Y-%m-%d')

            try:
                # Use new NHL API format
                url = f"{self.nhl_api_base}/score/{date_str}"
                response = requests.get(url, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    games = data.get('games', [])

                    for game in games:
                        # Only regular season, completed games
                        if game.get('gameType') == 2 and game.get('gameState') == 'OFF':
                            game_data = self._extract_game_features_new_api(game, date_str)
                            if game_data:
                                games_data.append(game_data)

                if len(games_data) % 100 == 0 and len(games_data) > 0:
                    print(f"   Fetched {len(games_data)} games...")

            except Exception as e:
                # Silently continue on errors (no games that day)
                pass

            current += timedelta(days=1)

        print(f"✅ Fetched {len(games_data)} completed games\n")

        return pd.DataFrame(games_data)

    def _extract_game_features_new_api(self, game, date_str):
        """Extract features from a game using new API format"""

        try:
            # Get teams
            home_team = game.get('homeTeam', {}).get('name', {}).get('default', '')
            away_team = game.get('awayTeam', {}).get('name', {}).get('default', '')

            # Get final scores
            home_score = game.get('homeTeam', {}).get('score', 0)
            away_score = game.get('awayTeam', {}).get('score', 0)
            total_goals = home_score + away_score

            # Get first period goals from landing API
            home_1p_goals = 0
            away_1p_goals = 0

            game_id = game.get('id')
            home_team_abbrev = game.get('homeTeam', {}).get('abbrev', '')

            if game_id:
                try:
                    # Use landing endpoint to get period-by-period scoring
                    landing_url = f"{self.nhl_api_base}/gamecenter/{game_id}/landing"
                    landing_response = requests.get(landing_url, timeout=5)

                    if landing_response.status_code == 200:
                        landing_data = landing_response.json()

                        # Extract goals from first period using summary/scoring
                        if 'summary' in landing_data and 'scoring' in landing_data['summary']:
                            scoring_by_period = landing_data['summary']['scoring']

                            # Find period 1
                            for period in scoring_by_period:
                                if period.get('periodDescriptor', {}).get('number') == 1:
                                    goals_in_period = period.get('goals', [])

                                    for goal in goals_in_period:
                                        # Check if goal was scored by home or away team
                                        goal_team = goal.get('teamAbbrev', {}).get('default', '')
                                        if goal_team == home_team_abbrev:
                                            home_1p_goals += 1
                                        else:
                                            away_1p_goals += 1
                                    break
                except:
                    pass

            first_period_total = home_1p_goals + away_1p_goals

            # Get shots
            home_shots = game.get('homeTeam', {}).get('sog', 0)
            away_shots = game.get('awayTeam', {}).get('sog', 0)

            return {
                'date': date_str,
                'home_team': home_team,
                'away_team': away_team,
                'home_score': home_score,
                'away_score': away_score,
                'total_goals': total_goals,
                'home_1p_goals': home_1p_goals,
                'away_1p_goals': away_1p_goals,
                'first_period_total': first_period_total,
                'home_over_half_1p': 1 if home_1p_goals >= 1 else 0,
                'away_over_half_1p': 1 if away_1p_goals >= 1 else 0,
                'period_over_1_5': 1 if first_period_total >= 2 else 0,
                'home_shots': home_shots,
                'away_shots': away_shots
            }

        except Exception as e:
            return None

    def calculate_team_stats(self, df):
        """Calculate rolling team statistics with recent form and home/away splits"""

        print("📈 Calculating team statistics with recent form & home/away splits...")

        team_stats = defaultdict(lambda: {
            'games_played': 0,
            'goals_for': 0,
            'goals_against': 0,
            '1p_goals_for': 0,
            '1p_goals_against': 0,
            'shots_for': 0,
            'shots_against': 0,
            # Home/Away splits for first period
            'home_1p_goals_for': 0,
            'home_1p_goals_against': 0,
            'home_games': 0,
            'away_1p_goals_for': 0,
            'away_1p_goals_against': 0,
            'away_games': 0,
            # Recent form tracking (last 5 games)
            'recent_games': [],  # List of recent game results
            'recent_goals_for': [],
            'recent_goals_against': [],
            'recent_1p_goals_for': [],
            'recent_1p_goals_against': []
        })

        # Process games chronologically
        df_sorted = df.sort_values('date')

        enhanced_data = []

        for idx, row in df_sorted.iterrows():
            home = row['home_team']
            away = row['away_team']

            # Get current stats (before this game)
            home_stats = team_stats[home]
            away_stats = team_stats[away]

            # Calculate season-long features
            home_gpg = home_stats['goals_for'] / home_stats['games_played'] if home_stats['games_played'] > 0 else 3.0
            home_gaa = home_stats['goals_against'] / home_stats['games_played'] if home_stats['games_played'] > 0 else 3.0
            away_gpg = away_stats['goals_for'] / away_stats['games_played'] if away_stats['games_played'] > 0 else 3.0
            away_gaa = away_stats['goals_against'] / away_stats['games_played'] if away_stats['games_played'] > 0 else 3.0

            home_1p_gpg = home_stats['1p_goals_for'] / home_stats['games_played'] if home_stats['games_played'] > 0 else 0.5
            home_1p_gaa = home_stats['1p_goals_against'] / home_stats['games_played'] if home_stats['games_played'] > 0 else 0.5
            away_1p_gpg = away_stats['1p_goals_for'] / away_stats['games_played'] if away_stats['games_played'] > 0 else 0.5
            away_1p_gaa = away_stats['1p_goals_against'] / away_stats['games_played'] if away_stats['games_played'] > 0 else 0.5

            # Calculate home/away 1P splits (home team is at home, away team is on road)
            home_1p_home_gpg = home_stats['home_1p_goals_for'] / home_stats['home_games'] if home_stats['home_games'] > 0 else 0.5
            home_1p_home_gaa = home_stats['home_1p_goals_against'] / home_stats['home_games'] if home_stats['home_games'] > 0 else 0.5

            away_1p_road_gpg = away_stats['away_1p_goals_for'] / away_stats['away_games'] if away_stats['away_games'] > 0 else 0.5
            away_1p_road_gaa = away_stats['away_1p_goals_against'] / away_stats['away_games'] if away_stats['away_games'] > 0 else 0.5

            # Calculate recent form (last 5 games)
            home_recent_gpg = np.mean(home_stats['recent_goals_for'][-5:]) if len(home_stats['recent_goals_for']) > 0 else 3.0
            home_recent_gaa = np.mean(home_stats['recent_goals_against'][-5:]) if len(home_stats['recent_goals_against']) > 0 else 3.0
            away_recent_gpg = np.mean(away_stats['recent_goals_for'][-5:]) if len(away_stats['recent_goals_for']) > 0 else 3.0
            away_recent_gaa = np.mean(away_stats['recent_goals_against'][-5:]) if len(away_stats['recent_goals_against']) > 0 else 3.0

            home_recent_1p_gpg = np.mean(home_stats['recent_1p_goals_for'][-5:]) if len(home_stats['recent_1p_goals_for']) > 0 else 0.5
            home_recent_1p_gaa = np.mean(home_stats['recent_1p_goals_against'][-5:]) if len(home_stats['recent_1p_goals_against']) > 0 else 0.5
            away_recent_1p_gpg = np.mean(away_stats['recent_1p_goals_for'][-5:]) if len(away_stats['recent_1p_goals_for']) > 0 else 0.5
            away_recent_1p_gaa = np.mean(away_stats['recent_1p_goals_against'][-5:]) if len(away_stats['recent_1p_goals_against']) > 0 else 0.5

            # Create feature row
            enhanced_row = row.copy()
            # Season-long stats
            enhanced_row['home_gpg'] = home_gpg
            enhanced_row['home_gaa'] = home_gaa
            enhanced_row['away_gpg'] = away_gpg
            enhanced_row['away_gaa'] = away_gaa
            enhanced_row['home_1p_gpg'] = home_1p_gpg
            enhanced_row['home_1p_gaa'] = home_1p_gaa
            enhanced_row['away_1p_gpg'] = away_1p_gpg
            enhanced_row['away_1p_gaa'] = away_1p_gaa
            # Home/Away 1P splits
            enhanced_row['home_1p_home_gpg'] = home_1p_home_gpg
            enhanced_row['home_1p_home_gaa'] = home_1p_home_gaa
            enhanced_row['away_1p_road_gpg'] = away_1p_road_gpg
            enhanced_row['away_1p_road_gaa'] = away_1p_road_gaa
            # Recent form
            enhanced_row['home_recent_gpg'] = home_recent_gpg
            enhanced_row['home_recent_gaa'] = home_recent_gaa
            enhanced_row['away_recent_gpg'] = away_recent_gpg
            enhanced_row['away_recent_gaa'] = away_recent_gaa
            enhanced_row['home_recent_1p_gpg'] = home_recent_1p_gpg
            enhanced_row['home_recent_1p_gaa'] = home_recent_1p_gaa
            enhanced_row['away_recent_1p_gpg'] = away_recent_1p_gpg
            enhanced_row['away_recent_1p_gaa'] = away_recent_1p_gaa
            enhanced_row['implied_total'] = home_gpg + away_gpg + home_gaa + away_gaa

            # Only add if teams have played at least 5 games
            if home_stats['games_played'] >= 5 and away_stats['games_played'] >= 5:
                enhanced_data.append(enhanced_row)

            # Update stats with this game's results

            # Home team (playing at home)
            team_stats[home]['games_played'] += 1
            team_stats[home]['goals_for'] += row['home_score']
            team_stats[home]['goals_against'] += row['away_score']
            team_stats[home]['1p_goals_for'] += row['home_1p_goals']
            team_stats[home]['1p_goals_against'] += row['away_1p_goals']
            team_stats[home]['shots_for'] += row.get('home_shots', 0)
            team_stats[home]['shots_against'] += row.get('away_shots', 0)

            # Home/away splits for home team (this is a home game)
            team_stats[home]['home_games'] += 1
            team_stats[home]['home_1p_goals_for'] += row['home_1p_goals']
            team_stats[home]['home_1p_goals_against'] += row['away_1p_goals']

            # Recent form tracking (keep last 10, use last 5)
            team_stats[home]['recent_goals_for'].append(row['home_score'])
            team_stats[home]['recent_goals_against'].append(row['away_score'])
            team_stats[home]['recent_1p_goals_for'].append(row['home_1p_goals'])
            team_stats[home]['recent_1p_goals_against'].append(row['away_1p_goals'])
            if len(team_stats[home]['recent_goals_for']) > 10:
                team_stats[home]['recent_goals_for'] = team_stats[home]['recent_goals_for'][-10:]
                team_stats[home]['recent_goals_against'] = team_stats[home]['recent_goals_against'][-10:]
                team_stats[home]['recent_1p_goals_for'] = team_stats[home]['recent_1p_goals_for'][-10:]
                team_stats[home]['recent_1p_goals_against'] = team_stats[home]['recent_1p_goals_against'][-10:]

            # Away team (playing on road)
            team_stats[away]['games_played'] += 1
            team_stats[away]['goals_for'] += row['away_score']
            team_stats[away]['goals_against'] += row['home_score']
            team_stats[away]['1p_goals_for'] += row['away_1p_goals']
            team_stats[away]['1p_goals_against'] += row['home_1p_goals']
            team_stats[away]['shots_for'] += row.get('away_shots', 0)
            team_stats[away]['shots_against'] += row.get('home_shots', 0)

            # Home/away splits for away team (this is a road game)
            team_stats[away]['away_games'] += 1
            team_stats[away]['away_1p_goals_for'] += row['away_1p_goals']
            team_stats[away]['away_1p_goals_against'] += row['home_1p_goals']

            # Recent form tracking
            team_stats[away]['recent_goals_for'].append(row['away_score'])
            team_stats[away]['recent_goals_against'].append(row['home_score'])
            team_stats[away]['recent_1p_goals_for'].append(row['away_1p_goals'])
            team_stats[away]['recent_1p_goals_against'].append(row['home_1p_goals'])
            if len(team_stats[away]['recent_goals_for']) > 10:
                team_stats[away]['recent_goals_for'] = team_stats[away]['recent_goals_for'][-10:]
                team_stats[away]['recent_goals_against'] = team_stats[away]['recent_goals_against'][-10:]
                team_stats[away]['recent_1p_goals_for'] = team_stats[away]['recent_1p_goals_for'][-10:]
                team_stats[away]['recent_1p_goals_against'] = team_stats[away]['recent_1p_goals_against'][-10:]

        self.team_stats = dict(team_stats)

        print(f"✅ Calculated stats for {len(enhanced_data)} games with sufficient history\n")

        return pd.DataFrame(enhanced_data)

    def train_models(self, df):
        """Train all ML models"""

        print("🤖 Training ML models...\n")

        # Prepare features
        feature_cols = ['home_gpg', 'home_gaa', 'away_gpg', 'away_gaa',
                       'home_1p_gpg', 'home_1p_gaa', 'away_1p_gpg', 'away_1p_gaa',
                       'home_1p_home_gpg', 'home_1p_home_gaa',
                       'away_1p_road_gpg', 'away_1p_road_gaa',
                       'home_recent_gpg', 'home_recent_gaa',
                       'away_recent_gpg', 'away_recent_gaa',
                       'home_recent_1p_gpg', 'home_recent_1p_gaa',
                       'away_recent_1p_gpg', 'away_recent_1p_gaa']

        X = df[feature_cols].values

        # Target: Total goals
        y_total = df['total_goals'].values

        # Targets: First period probabilities
        y_home_over_half = df['home_over_half_1p'].values
        y_away_over_half = df['away_over_half_1p'].values
        y_period_over_1_5 = df['period_over_1_5'].values

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Train totals models
        print("📊 Training game totals models:")
        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_total, test_size=0.2, random_state=42)

        model_scores = {}

        for name, model in self.totals_models.items():
            model.fit(X_train, y_train)
            score = model.score(X_test, y_test)
            cv_score = cross_val_score(model, X_scaled, y_total, cv=5).mean()
            model_scores[name] = {'r2': score, 'cv_r2': cv_score}
            print(f"   {name:20s}: R² = {score:.4f} | CV R² = {cv_score:.4f}")

        # Train first period models
        print("\n🎯 Training first period probability models:")

        # Home team over 0.5
        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_home_over_half, test_size=0.2, random_state=42)
        self.first_period_models['home_over_half'].fit(X_train, y_train)
        home_score = self.first_period_models['home_over_half'].score(X_test, y_test)
        print(f"   Home over 0.5 1P   : Accuracy = {home_score:.4f}")

        # Away team over 0.5
        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_away_over_half, test_size=0.2, random_state=42)
        self.first_period_models['away_over_half'].fit(X_train, y_train)
        away_score = self.first_period_models['away_over_half'].score(X_test, y_test)
        print(f"   Away over 0.5 1P   : Accuracy = {away_score:.4f}")

        # Period over 1.5
        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_period_over_1_5, test_size=0.2, random_state=42)
        self.first_period_models['period_over_1_5'].fit(X_train, y_train)
        period_score = self.first_period_models['period_over_1_5'].score(X_test, y_test)
        print(f"   Period over 1.5    : Accuracy = {period_score:.4f}")

        print("\n✅ All models trained successfully!")

        # Find best totals model
        best_model = max(model_scores.items(), key=lambda x: x[1]['cv_r2'])
        print(f"🏆 Best totals model: {best_model[0]} (CV R² = {best_model[1]['cv_r2']:.4f})\n")

        self.best_totals_model = best_model[0]

        return model_scores

    def save_models(self):
        """Save trained models to disk"""

        print("💾 Saving models...")

        # Save totals models
        for name, model in self.totals_models.items():
            joblib.dump(model, f"{self.model_dir}/totals_{name}.pkl")

        # Save first period models
        for name, model in self.first_period_models.items():
            joblib.dump(model, f"{self.model_dir}/first_period_{name}.pkl")

        # Save scaler and team stats
        joblib.dump(self.scaler, f"{self.model_dir}/scaler.pkl")
        joblib.dump(self.team_stats, f"{self.model_dir}/team_stats.pkl")
        joblib.dump(self.best_totals_model, f"{self.model_dir}/best_model_name.pkl")

        print(f"✅ Models saved to {self.model_dir}/\n")

    def load_models(self):
        """Load trained models from disk"""

        print("📂 Loading models...")

        try:
            # Load totals models
            for name in self.totals_models.keys():
                self.totals_models[name] = joblib.load(f"{self.model_dir}/totals_{name}.pkl")

            # Load first period models
            for name in self.first_period_models.keys():
                self.first_period_models[name] = joblib.load(f"{self.model_dir}/first_period_{name}.pkl")

            # Load scaler and team stats
            self.scaler = joblib.load(f"{self.model_dir}/scaler.pkl")
            self.team_stats = joblib.load(f"{self.model_dir}/team_stats.pkl")
            self.best_totals_model = joblib.load(f"{self.model_dir}/best_model_name.pkl")

            print(f"✅ Models loaded successfully (Best: {self.best_totals_model})\n")
            return True

        except Exception as e:
            print(f"❌ Error loading models: {e}")
            return False

    def predict_game(self, home_team, away_team):
        """Predict totals and probabilities for a game"""

        if home_team not in self.team_stats or away_team not in self.team_stats:
            return None

        home_stats = self.team_stats[home_team]
        away_stats = self.team_stats[away_team]

        # Calculate features
        home_gpg = home_stats['goals_for'] / home_stats['games_played'] if home_stats['games_played'] > 0 else 3.0
        home_gaa = home_stats['goals_against'] / home_stats['games_played'] if home_stats['games_played'] > 0 else 3.0
        away_gpg = away_stats['goals_for'] / away_stats['games_played'] if away_stats['games_played'] > 0 else 3.0
        away_gaa = away_stats['goals_against'] / away_stats['games_played'] if away_stats['games_played'] > 0 else 3.0

        home_1p_gpg = home_stats['1p_goals_for'] / home_stats['games_played'] if home_stats['games_played'] > 0 else 0.5
        home_1p_gaa = home_stats['1p_goals_against'] / home_stats['games_played'] if home_stats['games_played'] > 0 else 0.5
        away_1p_gpg = away_stats['1p_goals_for'] / away_stats['games_played'] if away_stats['games_played'] > 0 else 0.5
        away_1p_gaa = away_stats['1p_goals_against'] / away_stats['games_played'] if away_stats['games_played'] > 0 else 0.5

        # Calculate home/away 1P splits
        home_1p_home_gpg = home_stats['home_1p_goals_for'] / home_stats['home_games'] if home_stats['home_games'] > 0 else 0.5
        home_1p_home_gaa = home_stats['home_1p_goals_against'] / home_stats['home_games'] if home_stats['home_games'] > 0 else 0.5
        away_1p_road_gpg = away_stats['away_1p_goals_for'] / away_stats['away_games'] if away_stats['away_games'] > 0 else 0.5
        away_1p_road_gaa = away_stats['away_1p_goals_against'] / away_stats['away_games'] if away_stats['away_games'] > 0 else 0.5

        # Calculate recent form (last 5 games)
        home_recent_gpg = np.mean(home_stats['recent_goals_for'][-5:]) if len(home_stats['recent_goals_for']) > 0 else 3.0
        home_recent_gaa = np.mean(home_stats['recent_goals_against'][-5:]) if len(home_stats['recent_goals_against']) > 0 else 3.0
        away_recent_gpg = np.mean(away_stats['recent_goals_for'][-5:]) if len(away_stats['recent_goals_for']) > 0 else 3.0
        away_recent_gaa = np.mean(away_stats['recent_goals_against'][-5:]) if len(away_stats['recent_goals_against']) > 0 else 3.0

        home_recent_1p_gpg = np.mean(home_stats['recent_1p_goals_for'][-5:]) if len(home_stats['recent_1p_goals_for']) > 0 else 0.5
        home_recent_1p_gaa = np.mean(home_stats['recent_1p_goals_against'][-5:]) if len(home_stats['recent_1p_goals_against']) > 0 else 0.5
        away_recent_1p_gpg = np.mean(away_stats['recent_1p_goals_for'][-5:]) if len(away_stats['recent_1p_goals_for']) > 0 else 0.5
        away_recent_1p_gaa = np.mean(away_stats['recent_1p_goals_against'][-5:]) if len(away_stats['recent_1p_goals_against']) > 0 else 0.5

        features = np.array([[home_gpg, home_gaa, away_gpg, away_gaa,
                            home_1p_gpg, home_1p_gaa, away_1p_gpg, away_1p_gaa,
                            home_1p_home_gpg, home_1p_home_gaa,
                            away_1p_road_gpg, away_1p_road_gaa,
                            home_recent_gpg, home_recent_gaa,
                            away_recent_gpg, away_recent_gaa,
                            home_recent_1p_gpg, home_recent_1p_gaa,
                            away_recent_1p_gpg, away_recent_1p_gaa]])

        features_scaled = self.scaler.transform(features)

        # Get predictions from all totals models
        totals_predictions = {}
        for name, model in self.totals_models.items():
            totals_predictions[name] = model.predict(features_scaled)[0]

        # Get best model prediction
        best_total = totals_predictions[self.best_totals_model]

        # Get first period probabilities (handle single-class edge case)
        try:
            home_over_half_prob = self.first_period_models['home_over_half'].predict_proba(features_scaled)[0][1]
        except IndexError:
            home_over_half_prob = 1.0 if self.first_period_models['home_over_half'].classes_[0] == 1 else 0.0

        try:
            away_over_half_prob = self.first_period_models['away_over_half'].predict_proba(features_scaled)[0][1]
        except IndexError:
            away_over_half_prob = 1.0 if self.first_period_models['away_over_half'].classes_[0] == 1 else 0.0

        try:
            period_over_1_5_prob = self.first_period_models['period_over_1_5'].predict_proba(features_scaled)[0][1]
        except IndexError:
            period_over_1_5_prob = 1.0 if self.first_period_models['period_over_1_5'].classes_[0] == 1 else 0.0

        return {
            'home_team': home_team,
            'away_team': away_team,
            'predicted_total': best_total,
            'model_predictions': totals_predictions,
            'home_over_0_5_1p_prob': home_over_half_prob * 100,
            'away_over_0_5_1p_prob': away_over_half_prob * 100,
            'period_over_1_5_prob': period_over_1_5_prob * 100
        }


if __name__ == '__main__':
    # Training example
    predictor = NHLMLTotalsPredictor()

    # Fetch data from start of 2024-25 season
    start_date = '2024-10-08'
    end_date = '2024-11-18'

    df = predictor.fetch_historical_data(start_date, end_date)

    if len(df) > 0:
        df_enhanced = predictor.calculate_team_stats(df)

        if len(df_enhanced) > 100:
            scores = predictor.train_models(df_enhanced)
            predictor.save_models()

            print("🎉 Training complete! Models ready for daily predictions.")
        else:
            print("⚠️  Not enough data for training (need at least 100 games)")
    else:
        print("❌ No historical data fetched")
