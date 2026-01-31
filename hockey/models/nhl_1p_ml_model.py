#!/usr/bin/env python3
"""
NHL First Period Goals ML Model

Uses Poisson regression and XGBoost to predict 1st period goals.
Features include rolling team stats, head-to-head history, and situational factors.
"""

import os
import sys
import sqlite3
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# Install required packages if needed
try:
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    from sklearn.preprocessing import StandardScaler
except ImportError:
    os.system("pip3 install scikit-learn")
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    from sklearn.preprocessing import StandardScaler

try:
    import statsmodels.api as sm
    from statsmodels.discrete.count_model import Poisson
except ImportError:
    os.system("pip3 install statsmodels")
    import statsmodels.api as sm
    from statsmodels.discrete.count_model import Poisson

try:
    import xgboost as xgb
except ImportError:
    os.system("pip3 install xgboost")
    import xgboost as xgb

# Paths
DB_PATH = "/Users/dickgibbons/sports-betting/data/nhl_game_cache.db"
MODEL_DIR = "/Users/dickgibbons/sports-betting/nhl/models"


class NHL1PGoalsModel:
    """ML model for predicting NHL 1st period goals"""

    def __init__(self):
        self.db_path = DB_PATH
        self.model_dir = Path(MODEL_DIR)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        # Models
        self.poisson_home = None
        self.poisson_away = None
        self.xgb_home = None
        self.xgb_away = None
        self.scaler = StandardScaler()

        # Feature columns (will be set during training)
        self.feature_cols = []

    def load_all_games(self) -> pd.DataFrame:
        """Load all games with 1P data from cache"""
        conn = sqlite3.connect(self.db_path)

        query = """
        SELECT
            game_id, game_date, season,
            home_team, away_team,
            home_score, away_score,
            period_1_home, period_1_away,
            period_2_home, period_2_away,
            period_3_home, period_3_away,
            home_shots, away_shots,
            venue
        FROM games
        WHERE game_state = 'OFF'
        AND (period_1_home IS NOT NULL OR period_1_away IS NOT NULL)
        ORDER BY game_date ASC
        """

        df = pd.read_sql_query(query, conn)
        conn.close()

        df['game_date'] = pd.to_datetime(df['game_date'])
        df['period_1_total'] = df['period_1_home'].fillna(0) + df['period_1_away'].fillna(0)

        print(f"Loaded {len(df)} games with 1P data")
        return df

    def calculate_team_rolling_stats(self, df: pd.DataFrame, team: str,
                                      date: datetime, window: int = 10) -> Dict:
        """Calculate rolling stats for a team up to (but not including) a given date"""

        # Get team's previous games
        team_games = df[
            ((df['home_team'] == team) | (df['away_team'] == team)) &
            (df['game_date'] < date)
        ].tail(window)

        if len(team_games) == 0:
            return None

        stats = {}

        # Calculate stats from team's perspective
        p1_for = []
        p1_against = []
        total_for = []
        total_against = []
        shots_for = []
        shots_against = []

        for _, game in team_games.iterrows():
            if game['home_team'] == team:
                p1_for.append(game['period_1_home'] or 0)
                p1_against.append(game['period_1_away'] or 0)
                total_for.append(game['home_score'] or 0)
                total_against.append(game['away_score'] or 0)
                shots_for.append(game['home_shots'] or 0)
                shots_against.append(game['away_shots'] or 0)
            else:
                p1_for.append(game['period_1_away'] or 0)
                p1_against.append(game['period_1_home'] or 0)
                total_for.append(game['away_score'] or 0)
                total_against.append(game['home_score'] or 0)
                shots_for.append(game['away_shots'] or 0)
                shots_against.append(game['home_shots'] or 0)

        # Rolling averages
        stats['p1_goals_for_avg'] = np.mean(p1_for)
        stats['p1_goals_against_avg'] = np.mean(p1_against)
        stats['p1_total_avg'] = np.mean([f + a for f, a in zip(p1_for, p1_against)])

        stats['total_goals_for_avg'] = np.mean(total_for)
        stats['total_goals_against_avg'] = np.mean(total_against)

        stats['shots_for_avg'] = np.mean(shots_for) if any(shots_for) else 30
        stats['shots_against_avg'] = np.mean(shots_against) if any(shots_against) else 30

        # Scoring rate (goals per shot)
        if stats['shots_for_avg'] > 0:
            stats['shooting_pct'] = stats['total_goals_for_avg'] / stats['shots_for_avg']
        else:
            stats['shooting_pct'] = 0.1

        # Save rate (1 - goals against per shot)
        if stats['shots_against_avg'] > 0:
            stats['save_pct'] = 1 - (stats['total_goals_against_avg'] / stats['shots_against_avg'])
        else:
            stats['save_pct'] = 0.9

        # Variance in 1P scoring
        stats['p1_goals_for_std'] = np.std(p1_for) if len(p1_for) > 1 else 0.5
        stats['p1_goals_against_std'] = np.std(p1_against) if len(p1_against) > 1 else 0.5

        # Recent form (last 3 vs last 10)
        if len(p1_for) >= 3:
            stats['p1_goals_for_recent'] = np.mean(p1_for[-3:])
            stats['p1_goals_against_recent'] = np.mean(p1_against[-3:])
        else:
            stats['p1_goals_for_recent'] = stats['p1_goals_for_avg']
            stats['p1_goals_against_recent'] = stats['p1_goals_against_avg']

        # Games played (for confidence weighting)
        stats['games_played'] = len(team_games)

        return stats

    def get_head_to_head_stats(self, df: pd.DataFrame, home: str, away: str,
                                date: datetime, window: int = 5) -> Dict:
        """Get head-to-head history between teams"""

        h2h = df[
            (((df['home_team'] == home) & (df['away_team'] == away)) |
             ((df['home_team'] == away) & (df['away_team'] == home))) &
            (df['game_date'] < date)
        ].tail(window)

        if len(h2h) == 0:
            return {'h2h_p1_total_avg': 1.5, 'h2h_games': 0}

        p1_totals = (h2h['period_1_home'].fillna(0) + h2h['period_1_away'].fillna(0)).values

        return {
            'h2h_p1_total_avg': np.mean(p1_totals),
            'h2h_games': len(h2h)
        }

    def calculate_rest_days(self, df: pd.DataFrame, team: str, date: datetime) -> int:
        """Calculate days since team's last game"""
        prev_games = df[
            ((df['home_team'] == team) | (df['away_team'] == team)) &
            (df['game_date'] < date)
        ]

        if len(prev_games) == 0:
            return 3  # Default

        last_game = prev_games['game_date'].max()
        return (date - last_game).days

    def calculate_schedule_fatigue(self, df: pd.DataFrame, team: str, date: datetime, is_home: bool) -> Dict:
        """
        Calculate comprehensive schedule fatigue factors:
        - 3 games in 4 nights
        - Road trip game number (consecutive away games)
        - Home stand length (consecutive home games)
        - Games in last 7 days
        """
        from datetime import timedelta

        # Get team's recent games (last 14 days)
        lookback = date - timedelta(days=14)
        recent_games = df[
            ((df['home_team'] == team) | (df['away_team'] == team)) &
            (df['game_date'] < date) &
            (df['game_date'] >= lookback)
        ].sort_values('game_date', ascending=False)

        # Default values
        result = {
            'games_in_4_nights': 0,
            'is_3_in_4': 0,
            'games_in_7_days': 0,
            'road_trip_game': 0,  # 0 = home game, 1+ = nth road game
            'home_stand_game': 0,  # 0 = away game, 1+ = nth home game
            'consecutive_away': 0,
            'consecutive_home': 0,
        }

        if len(recent_games) == 0:
            return result

        # Games in last 4 nights (for 3-in-4 detection)
        four_nights_ago = date - timedelta(days=4)
        games_4_nights = recent_games[recent_games['game_date'] >= four_nights_ago]
        result['games_in_4_nights'] = len(games_4_nights)
        result['is_3_in_4'] = 1 if len(games_4_nights) >= 2 else 0  # 2 games + today = 3 in 4

        # Games in last 7 days
        seven_days_ago = date - timedelta(days=7)
        games_7_days = recent_games[recent_games['game_date'] >= seven_days_ago]
        result['games_in_7_days'] = len(games_7_days)

        # Calculate consecutive home/away games
        consecutive_away = 0
        consecutive_home = 0

        for _, game in recent_games.iterrows():
            was_home = (game['home_team'] == team)
            was_away = (game['away_team'] == team)

            if was_away:
                if consecutive_home == 0:  # Still counting away streak
                    consecutive_away += 1
                else:
                    break  # Streak ended
            elif was_home:
                if consecutive_away == 0:  # Still counting home streak
                    consecutive_home += 1
                else:
                    break  # Streak ended

        result['consecutive_away'] = consecutive_away
        result['consecutive_home'] = consecutive_home

        # Set road trip or home stand game number
        if not is_home:  # This is an away game
            result['road_trip_game'] = consecutive_away + 1  # +1 for current game
        else:  # This is a home game
            result['home_stand_game'] = consecutive_home + 1  # +1 for current game

        return result

    def build_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Build feature matrix for all games"""
        print("Building features for ML model...")

        features = []

        for idx, game in df.iterrows():
            home = game['home_team']
            away = game['away_team']
            date = game['game_date']

            # Get rolling stats for both teams
            home_stats = self.calculate_team_rolling_stats(df, home, date)
            away_stats = self.calculate_team_rolling_stats(df, away, date)

            if home_stats is None or away_stats is None:
                continue

            # Get H2H stats
            h2h = self.get_head_to_head_stats(df, home, away, date)

            # Rest days
            home_rest = self.calculate_rest_days(df, home, date)
            away_rest = self.calculate_rest_days(df, away, date)

            # Schedule fatigue features
            home_fatigue = self.calculate_schedule_fatigue(df, home, date, is_home=True)
            away_fatigue = self.calculate_schedule_fatigue(df, away, date, is_home=False)

            feature_row = {
                'game_id': game['game_id'],
                'game_date': date,
                'home_team': home,
                'away_team': away,

                # Target variables
                'period_1_home': game['period_1_home'] or 0,
                'period_1_away': game['period_1_away'] or 0,
                'period_1_total': game['period_1_total'],

                # Home team offensive features
                'home_p1_for_avg': home_stats['p1_goals_for_avg'],
                'home_p1_for_recent': home_stats['p1_goals_for_recent'],
                'home_p1_for_std': home_stats['p1_goals_for_std'],
                'home_shooting_pct': home_stats['shooting_pct'],
                'home_shots_avg': home_stats['shots_for_avg'],

                # Home team defensive features
                'home_p1_against_avg': home_stats['p1_goals_against_avg'],
                'home_p1_against_recent': home_stats['p1_goals_against_recent'],
                'home_save_pct': home_stats['save_pct'],

                # Away team offensive features
                'away_p1_for_avg': away_stats['p1_goals_for_avg'],
                'away_p1_for_recent': away_stats['p1_goals_for_recent'],
                'away_p1_for_std': away_stats['p1_goals_for_std'],
                'away_shooting_pct': away_stats['shooting_pct'],
                'away_shots_avg': away_stats['shots_for_avg'],

                # Away team defensive features
                'away_p1_against_avg': away_stats['p1_goals_against_avg'],
                'away_p1_against_recent': away_stats['p1_goals_against_recent'],
                'away_save_pct': away_stats['save_pct'],

                # Matchup features (offense vs defense)
                'home_off_vs_away_def': home_stats['p1_goals_for_avg'] - away_stats['p1_goals_against_avg'],
                'away_off_vs_home_def': away_stats['p1_goals_for_avg'] - home_stats['p1_goals_against_avg'],

                # Rest and situational
                'home_rest_days': min(home_rest, 7),  # Cap at 7
                'away_rest_days': min(away_rest, 7),
                'home_b2b': 1 if home_rest == 1 else 0,
                'away_b2b': 1 if away_rest == 1 else 0,

                # Schedule fatigue features - NEW
                'home_3_in_4': home_fatigue['is_3_in_4'],
                'away_3_in_4': away_fatigue['is_3_in_4'],
                'home_games_in_7': home_fatigue['games_in_7_days'],
                'away_games_in_7': away_fatigue['games_in_7_days'],
                'home_stand_game': home_fatigue['home_stand_game'],
                'away_road_trip_game': away_fatigue['road_trip_game'],

                # H2H
                'h2h_p1_avg': h2h['h2h_p1_total_avg'],

                # Sample size confidence
                'home_games_played': home_stats['games_played'],
                'away_games_played': away_stats['games_played'],
            }

            features.append(feature_row)

            if len(features) % 200 == 0:
                print(f"  Processed {len(features)} games...")

        feature_df = pd.DataFrame(features)
        print(f"Built features for {len(feature_df)} games")
        return feature_df

    def train(self, feature_df: pd.DataFrame = None):
        """Train both Poisson and XGBoost models"""

        if feature_df is None:
            df = self.load_all_games()
            feature_df = self.build_features(df)

        # Define feature columns (including new schedule fatigue features)
        self.feature_cols = [
            'home_p1_for_avg', 'home_p1_for_recent', 'home_p1_for_std',
            'home_shooting_pct', 'home_shots_avg',
            'home_p1_against_avg', 'home_p1_against_recent', 'home_save_pct',
            'away_p1_for_avg', 'away_p1_for_recent', 'away_p1_for_std',
            'away_shooting_pct', 'away_shots_avg',
            'away_p1_against_avg', 'away_p1_against_recent', 'away_save_pct',
            'home_off_vs_away_def', 'away_off_vs_home_def',
            'home_rest_days', 'away_rest_days', 'home_b2b', 'away_b2b',
            # Schedule fatigue features
            'home_3_in_4', 'away_3_in_4',
            'home_games_in_7', 'away_games_in_7',
            'home_stand_game', 'away_road_trip_game',
            'h2h_p1_avg'
        ]

        X = feature_df[self.feature_cols].values
        y_home = feature_df['period_1_home'].values
        y_away = feature_df['period_1_away'].values
        y_total = feature_df['period_1_total'].values

        # Handle any NaN/inf values
        X = np.nan_to_num(X, nan=0, posinf=0, neginf=0)

        # Split data (use last 20% as test)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_home_train, y_home_test = y_home[:split_idx], y_home[split_idx:]
        y_away_train, y_away_test = y_away[:split_idx], y_away[split_idx:]
        y_total_test = y_total[split_idx:]

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        print("\n" + "="*60)
        print("TRAINING MODELS")
        print("="*60)

        # Train Poisson models
        print("\n--- Poisson Regression ---")
        X_train_sm = sm.add_constant(X_train_scaled)
        X_test_sm = sm.add_constant(X_test_scaled)

        self.poisson_home = sm.GLM(y_home_train, X_train_sm,
                                    family=sm.families.Poisson()).fit()
        self.poisson_away = sm.GLM(y_away_train, X_train_sm,
                                    family=sm.families.Poisson()).fit()

        # Poisson predictions
        poisson_home_pred = self.poisson_home.predict(X_test_sm)
        poisson_away_pred = self.poisson_away.predict(X_test_sm)
        poisson_total_pred = poisson_home_pred + poisson_away_pred

        print(f"Poisson Home MAE: {mean_absolute_error(y_home_test, poisson_home_pred):.3f}")
        print(f"Poisson Away MAE: {mean_absolute_error(y_away_test, poisson_away_pred):.3f}")
        print(f"Poisson Total MAE: {mean_absolute_error(y_total_test, poisson_total_pred):.3f}")

        # Train XGBoost models
        print("\n--- XGBoost ---")
        xgb_params = {
            'objective': 'count:poisson',
            'max_depth': 4,
            'learning_rate': 0.05,
            'n_estimators': 200,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42
        }

        self.xgb_home = xgb.XGBRegressor(**xgb_params)
        self.xgb_away = xgb.XGBRegressor(**xgb_params)

        self.xgb_home.fit(X_train, y_home_train,
                         eval_set=[(X_test, y_home_test)],
                         verbose=False)
        self.xgb_away.fit(X_train, y_away_train,
                         eval_set=[(X_test, y_away_test)],
                         verbose=False)

        # XGBoost predictions
        xgb_home_pred = self.xgb_home.predict(X_test)
        xgb_away_pred = self.xgb_away.predict(X_test)
        xgb_total_pred = xgb_home_pred + xgb_away_pred

        print(f"XGBoost Home MAE: {mean_absolute_error(y_home_test, xgb_home_pred):.3f}")
        print(f"XGBoost Away MAE: {mean_absolute_error(y_away_test, xgb_away_pred):.3f}")
        print(f"XGBoost Total MAE: {mean_absolute_error(y_total_test, xgb_total_pred):.3f}")

        # Feature importance
        print("\n--- Top 10 Feature Importance (XGBoost) ---")
        importance = pd.DataFrame({
            'feature': self.feature_cols,
            'importance': self.xgb_home.feature_importances_
        }).sort_values('importance', ascending=False)
        print(importance.head(10).to_string(index=False))

        # Calculate probability accuracy for betting lines
        print("\n--- Betting Line Accuracy ---")

        # Over 1.5 Total
        actual_over_1_5 = (y_total_test > 1.5).astype(int)
        xgb_prob_over_1_5 = self._calc_poisson_prob_over(xgb_total_pred, 1.5)
        xgb_pred_over_1_5 = (xgb_prob_over_1_5 > 0.5).astype(int)
        accuracy_1_5 = np.mean(xgb_pred_over_1_5 == actual_over_1_5)
        print(f"1P Over 1.5 Accuracy: {accuracy_1_5:.1%}")

        # Team over 0.5
        actual_home_over = (y_home_test > 0.5).astype(int)
        xgb_prob_home_over = self._calc_poisson_prob_over(xgb_home_pred, 0.5)
        xgb_pred_home_over = (xgb_prob_home_over > 0.5).astype(int)
        accuracy_home = np.mean(xgb_pred_home_over == actual_home_over)
        print(f"Home Team Over 0.5 Accuracy: {accuracy_home:.1%}")

        actual_away_over = (y_away_test > 0.5).astype(int)
        xgb_prob_away_over = self._calc_poisson_prob_over(xgb_away_pred, 0.5)
        xgb_pred_away_over = (xgb_prob_away_over > 0.5).astype(int)
        accuracy_away = np.mean(xgb_pred_away_over == actual_away_over)
        print(f"Away Team Over 0.5 Accuracy: {accuracy_away:.1%}")

        # Save models
        self.save_models()

        return {
            'poisson_total_mae': mean_absolute_error(y_total_test, poisson_total_pred),
            'xgb_total_mae': mean_absolute_error(y_total_test, xgb_total_pred),
            'over_1_5_accuracy': accuracy_1_5,
            'home_over_0_5_accuracy': accuracy_home,
            'away_over_0_5_accuracy': accuracy_away
        }

    def _calc_poisson_prob_over(self, lambdas: np.ndarray, threshold: float) -> np.ndarray:
        """Calculate probability of exceeding threshold using Poisson distribution"""
        from scipy.stats import poisson

        # P(X > threshold) = 1 - P(X <= floor(threshold))
        k = int(threshold)
        probs = 1 - poisson.cdf(k, lambdas)
        return probs

    def save_models(self):
        """Save trained models to disk"""
        model_data = {
            'poisson_home': self.poisson_home,
            'poisson_away': self.poisson_away,
            'xgb_home': self.xgb_home,
            'xgb_away': self.xgb_away,
            'scaler': self.scaler,
            'feature_cols': self.feature_cols
        }

        model_path = self.model_dir / 'nhl_1p_models.pkl'
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)

        print(f"\nModels saved to: {model_path}")

    def load_models(self):
        """Load trained models from disk"""
        model_path = self.model_dir / 'nhl_1p_models.pkl'

        if not model_path.exists():
            raise FileNotFoundError(f"No trained models found at {model_path}")

        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)

        self.poisson_home = model_data['poisson_home']
        self.poisson_away = model_data['poisson_away']
        self.xgb_home = model_data['xgb_home']
        self.xgb_away = model_data['xgb_away']
        self.scaler = model_data['scaler']
        self.feature_cols = model_data['feature_cols']

        print("Models loaded successfully")

    def predict_game(self, home_team: str, away_team: str,
                     game_date: datetime = None) -> Dict:
        """Predict 1P goals for a specific matchup"""
        from scipy.stats import poisson

        if game_date is None:
            game_date = datetime.now()

        # Load historical data to calculate features
        df = self.load_all_games()

        # Calculate features for this matchup
        home_stats = self.calculate_team_rolling_stats(df, home_team, game_date)
        away_stats = self.calculate_team_rolling_stats(df, away_team, game_date)

        if home_stats is None or away_stats is None:
            return None

        h2h = self.get_head_to_head_stats(df, home_team, away_team, game_date)
        home_rest = self.calculate_rest_days(df, home_team, game_date)
        away_rest = self.calculate_rest_days(df, away_team, game_date)

        # Calculate schedule fatigue
        home_fatigue = self.calculate_schedule_fatigue(df, home_team, game_date, is_home=True)
        away_fatigue = self.calculate_schedule_fatigue(df, away_team, game_date, is_home=False)

        # Build feature vector (must match training feature order)
        features = np.array([[
            home_stats['p1_goals_for_avg'],
            home_stats['p1_goals_for_recent'],
            home_stats['p1_goals_for_std'],
            home_stats['shooting_pct'],
            home_stats['shots_for_avg'],
            home_stats['p1_goals_against_avg'],
            home_stats['p1_goals_against_recent'],
            home_stats['save_pct'],
            away_stats['p1_goals_for_avg'],
            away_stats['p1_goals_for_recent'],
            away_stats['p1_goals_for_std'],
            away_stats['shooting_pct'],
            away_stats['shots_for_avg'],
            away_stats['p1_goals_against_avg'],
            away_stats['p1_goals_against_recent'],
            away_stats['save_pct'],
            home_stats['p1_goals_for_avg'] - away_stats['p1_goals_against_avg'],
            away_stats['p1_goals_for_avg'] - home_stats['p1_goals_against_avg'],
            min(home_rest, 7),
            min(away_rest, 7),
            1 if home_rest == 1 else 0,
            1 if away_rest == 1 else 0,
            # Schedule fatigue features
            home_fatigue['is_3_in_4'],
            away_fatigue['is_3_in_4'],
            home_fatigue['games_in_7_days'],
            away_fatigue['games_in_7_days'],
            home_fatigue['home_stand_game'],
            away_fatigue['road_trip_game'],
            h2h['h2h_p1_total_avg']
        ]])

        # Handle NaN
        features = np.nan_to_num(features, nan=0, posinf=0, neginf=0)

        # XGBoost predictions (use these as primary)
        xgb_home_lambda = self.xgb_home.predict(features)[0]
        xgb_away_lambda = self.xgb_away.predict(features)[0]
        xgb_total_lambda = xgb_home_lambda + xgb_away_lambda

        # Calculate probabilities
        prob_home_over_0_5 = 1 - poisson.cdf(0, xgb_home_lambda)
        prob_away_over_0_5 = 1 - poisson.cdf(0, xgb_away_lambda)

        # For total, we need to convolve the two Poisson distributions
        # Simplified: use combined lambda
        prob_total_over_1_5 = 1 - poisson.cdf(1, xgb_total_lambda)
        prob_total_over_2_5 = 1 - poisson.cdf(2, xgb_total_lambda)

        return {
            'home_team': home_team,
            'away_team': away_team,
            'expected_home_goals': round(xgb_home_lambda, 2),
            'expected_away_goals': round(xgb_away_lambda, 2),
            'expected_total_goals': round(xgb_total_lambda, 2),
            'prob_home_over_0_5': round(prob_home_over_0_5 * 100, 1),
            'prob_away_over_0_5': round(prob_away_over_0_5 * 100, 1),
            'prob_total_over_1_5': round(prob_total_over_1_5 * 100, 1),
            'prob_total_over_2_5': round(prob_total_over_2_5 * 100, 1),
            'home_rest_days': home_rest,
            'away_rest_days': away_rest,
            'home_b2b': home_rest == 1,
            'away_b2b': away_rest == 1,
            # Schedule fatigue info
            'home_3_in_4': home_fatigue['is_3_in_4'] == 1,
            'away_3_in_4': away_fatigue['is_3_in_4'] == 1,
            'home_games_in_7': home_fatigue['games_in_7_days'],
            'away_games_in_7': away_fatigue['games_in_7_days'],
            'away_road_trip_game': away_fatigue['road_trip_game'],
        }


def main():
    """Train the model and show results"""
    model = NHL1PGoalsModel()
    results = model.train()

    print("\n" + "="*60)
    print("TRAINING COMPLETE")
    print("="*60)
    print(f"XGBoost Total Goals MAE: {results['xgb_total_mae']:.3f}")
    print(f"Over 1.5 Prediction Accuracy: {results['over_1_5_accuracy']:.1%}")
    print(f"Home Over 0.5 Accuracy: {results['home_over_0_5_accuracy']:.1%}")
    print(f"Away Over 0.5 Accuracy: {results['away_over_0_5_accuracy']:.1%}")


if __name__ == "__main__":
    main()
