#!/usr/bin/env python3
"""
Enhanced Soccer Model Trainer with Additional Markets

New markets added:
1. Home Team Total O/U 1.5
2. Away Team Total O/U 0.5
3. First Half Total O/U 0.5, 1.5
4. Second Half Total O/U 0.5, 1.5
5. Double Chance (Home/Draw, Away/Draw, Home/Away)

Similar to NHL enhanced models - trains on more features and markets
"""

import os
import sys
import json
import requests
import numpy as np
import pandas as pd
import joblib
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report
import warnings
warnings.filterwarnings('ignore')

# API Configuration - API-Sports (same as daily script)
API_KEY = "960c628e1c91c4b1f125e1eec52ad862"
API_BASE = "https://v3.football.api-sports.io"


class EnhancedSoccerTrainer:
    """Enhanced soccer trainer with additional betting markets"""

    def __init__(self, api_key=API_KEY):
        self.api_key = api_key
        self.api_base = API_BASE
        self.headers = {'x-apisports-key': self.api_key}

        # Define all markets to train
        self.markets = [
            # Existing markets
            'match_outcome',      # Home/Draw/Away
            'over_2_5',          # Over/Under 2.5 goals
            'btts',              # Both Teams To Score

            # Home team total markets
            'home_over_0_5',     # Home team Over 0.5 goals
            'home_over_1_5',     # Home team Over 1.5 goals
            'home_over_2_5',     # Home team Over 2.5 goals

            # Away team total markets
            'away_over_0_5',     # Away team Over 0.5 goals
            'away_over_1_5',     # Away team Over 1.5 goals
            'away_over_2_5',     # Away team Over 2.5 goals

            # New half markets
            'first_half_over_0_5',   # 1H Over 0.5 goals
            'first_half_over_1_5',   # 1H Over 1.5 goals
            'second_half_over_0_5',  # 2H Over 0.5 goals
            'second_half_over_1_5',  # 2H Over 1.5 goals

            # New double chance markets
            'double_chance_home_draw',  # Home or Draw
            'double_chance_away_draw',  # Away or Draw
            'double_chance_home_away',  # Home or Away (no draw)
        ]

        # Model storage
        self.models = {}
        self.scaler = StandardScaler()
        self.feature_cols = []

        print(f"🔧 Enhanced Soccer Trainer initialized")
        print(f"📊 Training {len(self.markets)} different markets")

    def fetch_league_matches(self, league_id: int, season: int, max_matches: int = 500) -> list:
        """Fetch historical matches for a league"""
        print(f"📥 Fetching matches for league {league_id}, season {season}...")

        all_matches = []

        # Fetch matches from the season
        url = f"{self.api_base}/fixtures"
        params = {
            'league': league_id,
            'season': season
        }

        try:
            response = requests.get(url, params=params, headers=self.headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                fixtures = data.get('response', [])

                # Filter to completed matches with full data
                for fixture in fixtures:
                    status = fixture.get('fixture', {}).get('status', {}).get('short', '')

                    if status == 'FT':  # Full Time - completed match
                        match_data = self.extract_match_data(fixture)
                        if match_data:
                            all_matches.append(match_data)

                        if len(all_matches) >= max_matches:
                            break

                print(f"   ✅ Found {len(all_matches)} completed matches")
                return all_matches
            else:
                print(f"   ❌ API error: {response.status_code}")
                return []

        except Exception as e:
            print(f"   ❌ Error fetching matches: {e}")
            return []

    def extract_match_data(self, fixture: dict) -> dict:
        """Extract relevant data from API fixture"""
        try:
            fixture_data = fixture.get('fixture', {})
            teams = fixture.get('teams', {})
            goals = fixture.get('goals', {})
            score = fixture.get('score', {})

            # Full time scores
            home_goals = goals.get('home')
            away_goals = goals.get('away')

            if home_goals is None or away_goals is None:
                return None

            # Half time scores
            halftime = score.get('halftime', {})
            home_ht = halftime.get('home')
            away_ht = halftime.get('away')

            if home_ht is None or away_ht is None:
                return None

            # Second half scores (derived)
            home_2h = home_goals - home_ht
            away_2h = away_goals - away_ht

            return {
                'fixture_id': fixture_data.get('id'),
                'date': fixture_data.get('date'),
                'home_team': teams.get('home', {}).get('name'),
                'away_team': teams.get('away', {}).get('name'),
                'home_goals': home_goals,
                'away_goals': away_goals,
                'home_ht': home_ht,
                'away_ht': away_ht,
                'home_2h': home_2h,
                'away_2h': away_2h,
                'total_goals': home_goals + away_goals,
                'ht_total': home_ht + away_ht,
                '2h_total': home_2h + away_2h,
            }
        except Exception as e:
            return None

    def create_labels_for_match(self, match: dict) -> dict:
        """Create binary labels for all markets"""
        labels = {}

        # Match outcome (0=Away, 1=Draw, 2=Home)
        if match['home_goals'] > match['away_goals']:
            labels['match_outcome'] = 2
        elif match['home_goals'] < match['away_goals']:
            labels['match_outcome'] = 0
        else:
            labels['match_outcome'] = 1

        # Over/Under markets
        labels['over_2_5'] = 1 if match['total_goals'] > 2.5 else 0
        labels['btts'] = 1 if match['home_goals'] > 0 and match['away_goals'] > 0 else 0

        # Home team totals
        labels['home_over_0_5'] = 1 if match['home_goals'] > 0.5 else 0
        labels['home_over_1_5'] = 1 if match['home_goals'] > 1.5 else 0
        labels['home_over_2_5'] = 1 if match['home_goals'] > 2.5 else 0

        # Away team totals
        labels['away_over_0_5'] = 1 if match['away_goals'] > 0.5 else 0
        labels['away_over_1_5'] = 1 if match['away_goals'] > 1.5 else 0
        labels['away_over_2_5'] = 1 if match['away_goals'] > 2.5 else 0

        # First half markets
        labels['first_half_over_0_5'] = 1 if match['ht_total'] > 0.5 else 0
        labels['first_half_over_1_5'] = 1 if match['ht_total'] > 1.5 else 0

        # Second half markets
        labels['second_half_over_0_5'] = 1 if match['2h_total'] > 0.5 else 0
        labels['second_half_over_1_5'] = 1 if match['2h_total'] > 1.5 else 0

        # Double chance markets
        home_win = match['home_goals'] > match['away_goals']
        away_win = match['home_goals'] < match['away_goals']
        draw = match['home_goals'] == match['away_goals']

        labels['double_chance_home_draw'] = 1 if (home_win or draw) else 0
        labels['double_chance_away_draw'] = 1 if (away_win or draw) else 0
        labels['double_chance_home_away'] = 1 if (home_win or away_win) else 0

        return labels

    def create_features_from_odds(self, odds_data: dict) -> list:
        """Create feature vector from odds data"""
        # For now, use simple odds-based features
        # In production, you'd add team form, head-to-head, etc.

        home_odds = odds_data.get('home_odds', 2.0)
        draw_odds = odds_data.get('draw_odds', 3.2)
        away_odds = odds_data.get('away_odds', 3.5)
        over_25 = odds_data.get('over_25', 1.8)
        under_25 = odds_data.get('under_25', 1.9)
        btts_yes = odds_data.get('btts_yes', 1.8)
        btts_no = odds_data.get('btts_no', 1.9)

        # Implied probabilities
        home_prob = 1 / home_odds
        draw_prob = 1 / draw_odds
        away_prob = 1 / away_odds

        # Normalize probabilities (remove bookmaker margin)
        total_prob = home_prob + draw_prob + away_prob
        home_prob_norm = home_prob / total_prob
        draw_prob_norm = draw_prob / total_prob
        away_prob_norm = away_prob / total_prob

        # Expected goals estimate from odds
        expected_total = 2.5 * (1 / over_25) + 2.5 * (1 / under_25)

        features = [
            home_odds,
            draw_odds,
            away_odds,
            over_25,
            under_25,
            btts_yes,
            btts_no,
            home_prob_norm,
            draw_prob_norm,
            away_prob_norm,
            expected_total,
            home_odds - away_odds,  # Strength difference indicator
            1 / (home_odds * away_odds),  # Draw likelihood proxy
        ]

        return features

    def train_models(self, training_data: list):
        """Train models for all markets"""
        print(f"\n{'='*80}")
        print(f"🤖 TRAINING ENHANCED SOCCER MODELS")
        print(f"{'='*80}\n")

        if len(training_data) < 50:
            raise ValueError(f"Not enough training data! Need at least 50 matches, got {len(training_data)}")

        print(f"📊 Training on {len(training_data)} matches")

        # Prepare features (using synthetic odds for demonstration)
        # In production, you'd fetch historical odds
        X = []
        y_dict = {market: [] for market in self.markets}

        for match in training_data:
            # Create synthetic odds based on match outcome
            # In production, fetch real historical odds from API
            odds_data = self.create_synthetic_odds(match)
            features = self.create_features_from_odds(odds_data)
            X.append(features)

            # Get labels for this match
            labels = self.create_labels_for_match(match)
            for market in self.markets:
                y_dict[market].append(labels[market])

        X = np.array(X)

        # Store feature column names
        self.feature_cols = [
            'home_odds', 'draw_odds', 'away_odds', 'over_25', 'under_25',
            'btts_yes', 'btts_no', 'home_prob', 'draw_prob', 'away_prob',
            'expected_total', 'strength_diff', 'draw_indicator'
        ]

        print(f"📊 Feature matrix shape: {X.shape}")
        print(f"📊 Features: {len(self.feature_cols)}")

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Train models for each market
        for market in self.markets:
            print(f"\n🎯 Training market: {market}")

            y = np.array(y_dict[market])

            # Check class distribution
            unique, counts = np.unique(y, return_counts=True)
            print(f"   Class distribution: {dict(zip(unique, counts))}")

            # Skip if not enough samples of minority class
            if len(unique) < 2 or min(counts) < 5:
                print(f"   ⚠️  Skipping {market} - insufficient samples")
                continue

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42, stratify=y
            )

            # Train RandomForest - enhanced parameters
            rf = RandomForestClassifier(
                n_estimators=300,  # More trees for better accuracy
                max_depth=20,
                min_samples_split=3,
                min_samples_leaf=2,
                max_features='sqrt',
                random_state=42,
                n_jobs=-1
            )
            rf.fit(X_train, y_train)
            rf_score = accuracy_score(y_test, rf.predict(X_test))

            # Train GradientBoosting - enhanced parameters
            gb = GradientBoostingClassifier(
                n_estimators=300,
                max_depth=10,
                learning_rate=0.05,
                min_samples_split=3,
                min_samples_leaf=2,
                subsample=0.8,
                random_state=42
            )
            gb.fit(X_train, y_train)
            gb_score = accuracy_score(y_test, gb.predict(X_test))

            # Store models
            self.models[f'rf_{market}'] = rf
            self.models[f'gb_{market}'] = gb

            print(f"   ✅ RandomForest accuracy: {rf_score:.3f}")
            print(f"   ✅ GradientBoosting accuracy: {gb_score:.3f}")

        print(f"\n{'='*80}")
        print(f"✅ Training complete! {len(self.models)} models trained")
        print(f"{'='*80}\n")

    def create_synthetic_odds(self, match: dict) -> dict:
        """Create synthetic odds for training (placeholder)"""
        # In production, fetch real historical odds
        # For now, create plausible odds based on outcome

        home_goals = match['home_goals']
        away_goals = match['away_goals']
        total_goals = match['total_goals']

        # Simple odds generation based on actual outcome
        if home_goals > away_goals:
            home_odds = np.random.uniform(1.5, 2.5)
            away_odds = np.random.uniform(2.5, 4.5)
        elif away_goals > home_goals:
            home_odds = np.random.uniform(2.5, 4.5)
            away_odds = np.random.uniform(1.5, 2.5)
        else:
            home_odds = np.random.uniform(2.0, 3.0)
            away_odds = np.random.uniform(2.0, 3.0)

        draw_odds = np.random.uniform(3.0, 3.5)
        over_25 = 2.2 if total_goals > 2.5 else 1.7
        under_25 = 1.7 if total_goals <= 2.5 else 2.2
        btts_yes = 1.8 if (home_goals > 0 and away_goals > 0) else 2.1
        btts_no = 2.1 if (home_goals > 0 and away_goals > 0) else 1.8

        return {
            'home_odds': home_odds,
            'draw_odds': draw_odds,
            'away_odds': away_odds,
            'over_25': over_25,
            'under_25': under_25,
            'btts_yes': btts_yes,
            'btts_no': btts_no
        }

    def save_models(self, filename: str = 'models/soccer_ml_models_enhanced.pkl'):
        """Save trained models"""
        model_data = {
            'models': self.models,
            'scaler': self.scaler,
            'feature_cols': self.feature_cols,
            'feature_columns': self.feature_cols,  # Backward compatibility
            'trained_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'training_samples': len(self.models),
            'markets': self.markets
        }

        # Ensure models directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        # Backup existing model
        if os.path.exists(filename):
            backup_file = filename.replace('.pkl', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pkl')
            os.rename(filename, backup_file)
            print(f"📦 Backed up existing model to {backup_file}")

        joblib.dump(model_data, filename)
        print(f"💾 Models saved to {filename}")
        print(f"📊 Saved {len(self.models)} models")
        print(f"📅 Trained: {model_data['trained_date']}")


def main():
    """Main training pipeline"""
    print("\n⚽ ENHANCED SOCCER MODEL TRAINER")
    print("="*80 + "\n")

    # Top leagues for training
    leagues = {
        'Premier League': 39,
        'La Liga': 140,
        'Serie A': 135,
        'Bundesliga': 78,
        'Ligue 1': 61,
    }

    # Train on recent seasons
    seasons = [2024, 2023]  # Last 2 seasons

    trainer = EnhancedSoccerTrainer()

    all_training_data = []

    # Collect data from all leagues
    for league_name, league_id in leagues.items():
        print(f"\n📊 Processing {league_name}...")

        for season in seasons:
            matches = trainer.fetch_league_matches(league_id, season, max_matches=200)
            all_training_data.extend(matches)

            # Rate limiting
            import time
            time.sleep(2)

    print(f"\n{'='*80}")
    print(f"📊 Total training data: {len(all_training_data)} matches")
    print(f"{'='*80}\n")

    if len(all_training_data) < 100:
        print("❌ Not enough training data collected!")
        sys.exit(1)

    # Train models
    trainer.train_models(all_training_data)

    # Save models
    trainer.save_models()

    print("\n✅ Enhanced soccer models trained successfully!")
    print(f"📊 Total matches: {len(all_training_data)}")
    print(f"🤖 Total models: {len(trainer.models)}")
    print(f"📋 Markets: {', '.join(trainer.markets)}")


if __name__ == "__main__":
    main()
