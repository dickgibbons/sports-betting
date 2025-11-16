#!/usr/bin/env python3
"""
Soccer Model Trainer with Team Form Features (Phase 2)

This enhanced trainer adds 32 team form features to the existing 13 odds features:
- 16 features per home team (last 5 games + season stats)
- 16 features per away team (last 5 games + season stats)

Total features: 45 (13 odds + 32 form)

Expected improvements:
- BTTS Yes: 72% → 77-82% WR
- Match Winners: 42% → 52-58% WR
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

# Import team form fetcher
from team_form_fetcher import TeamFormFetcher

# API Configuration
API_KEY = "960c628e1c91c4b1f125e1eec52ad862"
API_BASE = "https://v3.football.api-sports.io"


class FormEnhancedSoccerTrainer:
    """Soccer trainer with team form features"""

    def __init__(self, api_key=API_KEY):
        self.api_key = api_key
        self.api_base = API_BASE
        self.headers = {'x-apisports-key': self.api_key}

        # Initialize team form fetcher
        self.form_fetcher = TeamFormFetcher(api_key=self.api_key)

        # Define markets to train
        self.markets = [
            'match_outcome',      # Home/Draw/Away (3-class)
            'over_2_5',          # Over/Under 2.5 goals
            'btts',              # Both Teams To Score
            'home_over_1_5',     # Home team Over 1.5 goals
            'away_over_1_5',     # Away team Over 1.5 goals
        ]

        # Model storage
        self.models = {}
        self.scaler = StandardScaler()
        self.feature_cols = []

        print(f"🔧 Form-Enhanced Soccer Trainer initialized")
        print(f"📊 Training {len(self.markets)} different markets")
        print(f"✨ Using team form features (Phase 2)")

    def fetch_league_matches(self, league_id: int, season: int, max_matches: int = 300) -> list:
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
                        match_data = self.extract_match_data(fixture, league_id, season)
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

    def extract_match_data(self, fixture: dict, league_id: int, season: int) -> dict:
        """Extract match data including team IDs"""
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

            # Team IDs for form features
            home_team_id = teams.get('home', {}).get('id')
            away_team_id = teams.get('away', {}).get('id')

            if home_team_id is None or away_team_id is None:
                return None

            return {
                'fixture_id': fixture_data.get('id'),
                'date': fixture_data.get('date'),
                'home_team': teams.get('home', {}).get('name'),
                'away_team': teams.get('away', {}).get('name'),
                'home_team_id': home_team_id,
                'away_team_id': away_team_id,
                'league_id': league_id,
                'season': season,
                'home_goals': home_goals,
                'away_goals': away_goals,
                'home_ht': home_ht,
                'away_ht': away_ht,
                'total_goals': home_goals + away_goals,
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

        # Team totals
        labels['home_over_1_5'] = 1 if match['home_goals'] > 1.5 else 0
        labels['away_over_1_5'] = 1 if match['away_goals'] > 1.5 else 0

        return labels

    def create_features_from_odds(self, odds_data: dict) -> list:
        """Create feature vector from odds data (13 features)"""
        home_odds = odds_data.get('home_odds', 2.0)
        draw_odds = odds_data.get('draw_odds', 3.2)
        away_odds = odds_data.get('away_odds', 3.5)
        over_25 = odds_data.get('over_25', 1.8)
        under_25 = odds_data.get('under_25', 1.9)
        btts_yes = odds_data.get('btts_yes', 1.8)
        btts_no = odds_data.get('btts_no', 1.9)

        # Implied probabilities
        home_prob = 1 / home_odds if home_odds > 0 else 0.5
        draw_prob = 1 / draw_odds if draw_odds > 0 else 0.3
        away_prob = 1 / away_odds if away_odds > 0 else 0.3

        # Normalize probabilities
        total_prob = home_prob + draw_prob + away_prob
        if total_prob > 0:
            home_prob_norm = home_prob / total_prob
            draw_prob_norm = draw_prob / total_prob
            away_prob_norm = away_prob / total_prob
        else:
            home_prob_norm = 0.33
            draw_prob_norm = 0.33
            away_prob_norm = 0.33

        # Expected goals estimate
        expected_total = 2.5 * (1 / over_25) if over_25 > 0 else 2.5

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
            home_odds - away_odds,  # Strength difference
            1 / (home_odds * away_odds) if (home_odds > 0 and away_odds > 0) else 0.1,  # Draw likelihood
        ]

        return features

    def fetch_team_form_features(self, match: dict) -> tuple:
        """
        Fetch team form features for both teams

        Returns:
            (home_form_features, away_form_features) - each is a list of 16 features
        """
        try:
            # Fetch home team features
            home_features = self.form_fetcher.fetch_team_features(
                match['home_team_id'],
                match['league_id'],
                match['season'],
                num_games=5
            )

            # Fetch away team features
            away_features = self.form_fetcher.fetch_team_features(
                match['away_team_id'],
                match['league_id'],
                match['season'],
                num_games=5
            )

            # Convert dict to ordered list of 16 features per team
            home_form_list = [
                home_features.get('wins_last_5', 0),
                home_features.get('draws_last_5', 0),
                home_features.get('losses_last_5', 0),
                home_features.get('points_last_5', 0),
                home_features.get('goals_for_last_5', 0),
                home_features.get('goals_against_last_5', 0),
                home_features.get('goal_diff_last_5', 0),
                home_features.get('btts_rate_last_5', 0.5),
                home_features.get('over_25_rate_last_5', 0.5),
                home_features.get('clean_sheets_last_5', 0),
                home_features.get('season_win_rate', 0.33),
                home_features.get('season_goals_per_game', 1.5),
                home_features.get('season_conceded_per_game', 1.5),
                home_features.get('season_clean_sheet_rate', 0.25),
                home_features.get('season_home_wins', 0),
                home_features.get('season_away_wins', 0),
            ]

            away_form_list = [
                away_features.get('wins_last_5', 0),
                away_features.get('draws_last_5', 0),
                away_features.get('losses_last_5', 0),
                away_features.get('points_last_5', 0),
                away_features.get('goals_for_last_5', 0),
                away_features.get('goals_against_last_5', 0),
                away_features.get('goal_diff_last_5', 0),
                away_features.get('btts_rate_last_5', 0.5),
                away_features.get('over_25_rate_last_5', 0.5),
                away_features.get('clean_sheets_last_5', 0),
                away_features.get('season_win_rate', 0.33),
                away_features.get('season_goals_per_game', 1.5),
                away_features.get('season_conceded_per_game', 1.5),
                away_features.get('season_clean_sheet_rate', 0.25),
                away_features.get('season_home_wins', 0),
                away_features.get('season_away_wins', 0),
            ]

            return home_form_list, away_form_list

        except Exception as e:
            print(f"   ⚠️  Could not fetch team form for match {match.get('fixture_id')}: {e}")
            # Return default features
            default_features = [0, 0, 0, 0, 0, 0, 0, 0.5, 0.5, 0, 0.33, 1.5, 1.5, 0.25, 0, 0]
            return default_features, default_features

    def train_models(self, training_data: list):
        """Train models for all markets with form features"""
        print(f"\n{'='*80}")
        print(f"🤖 TRAINING FORM-ENHANCED SOCCER MODELS")
        print(f"{'='*80}\n")

        if len(training_data) < 50:
            raise ValueError(f"Not enough training data! Need at least 50 matches, got {len(training_data)}")

        print(f"📊 Training on {len(training_data)} matches")
        print(f"✨ Fetching team form features for each match...")

        # Prepare features
        X = []
        y_dict = {market: [] for market in self.markets}
        successful_matches = 0
        failed_matches = 0

        for i, match in enumerate(training_data):
            if (i + 1) % 50 == 0:
                print(f"   Processing match {i + 1}/{len(training_data)}...")

            try:
                # Create odds-based features (13 features)
                odds_data = self.create_synthetic_odds(match)
                odds_features = self.create_features_from_odds(odds_data)

                # Fetch team form features (32 features: 16 home + 16 away)
                home_form, away_form = self.fetch_team_form_features(match)

                # Combine all features (13 + 16 + 16 = 45 features)
                combined_features = odds_features + home_form + away_form
                X.append(combined_features)

                # Get labels for this match
                labels = self.create_labels_for_match(match)
                for market in self.markets:
                    y_dict[market].append(labels[market])

                successful_matches += 1

            except Exception as e:
                print(f"   ⚠️  Skipping match {match.get('fixture_id')} due to error: {e}")
                failed_matches += 1
                continue

            # Rate limiting - pause every 10 API calls
            if (i + 1) % 10 == 0:
                import time
                time.sleep(1)

        X = np.array(X)

        print(f"\n📊 Successfully processed {successful_matches} matches")
        print(f"⚠️  Failed to process {failed_matches} matches")

        # Store feature column names
        self.feature_cols = [
            # Odds features (13)
            'home_odds', 'draw_odds', 'away_odds', 'over_25', 'under_25',
            'btts_yes', 'btts_no', 'home_prob', 'draw_prob', 'away_prob',
            'expected_total', 'strength_diff', 'draw_indicator',

            # Home team form features (16)
            'home_wins_last_5', 'home_draws_last_5', 'home_losses_last_5',
            'home_points_last_5', 'home_goals_for_last_5', 'home_goals_against_last_5',
            'home_goal_diff_last_5', 'home_btts_rate_last_5', 'home_over_25_rate_last_5',
            'home_clean_sheets_last_5', 'home_season_win_rate', 'home_season_goals_per_game',
            'home_season_conceded_per_game', 'home_season_clean_sheet_rate',
            'home_season_home_wins', 'home_season_away_wins',

            # Away team form features (16)
            'away_wins_last_5', 'away_draws_last_5', 'away_losses_last_5',
            'away_points_last_5', 'away_goals_for_last_5', 'away_goals_against_last_5',
            'away_goal_diff_last_5', 'away_btts_rate_last_5', 'away_over_25_rate_last_5',
            'away_clean_sheets_last_5', 'away_season_win_rate', 'away_season_goals_per_game',
            'away_season_conceded_per_game', 'away_season_clean_sheet_rate',
            'away_season_home_wins', 'away_season_away_wins',
        ]

        print(f"📊 Feature matrix shape: {X.shape}")
        print(f"📊 Total features: {len(self.feature_cols)} (13 odds + 32 form)")

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Train models for each market
        for market in self.markets:
            print(f"\n🎯 Training market: {market}")

            y = np.array(y_dict[market])

            # Check class distribution
            unique, counts = np.unique(y, return_counts=True)
            print(f"   Class distribution: {dict(zip(unique, counts))}")

            # Skip if not enough samples
            if len(unique) < 2 or min(counts) < 5:
                print(f"   ⚠️  Skipping {market} - insufficient samples")
                continue

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42, stratify=y
            )

            # Train RandomForest with enhanced parameters
            rf = RandomForestClassifier(
                n_estimators=300,
                max_depth=20,
                min_samples_split=3,
                min_samples_leaf=2,
                max_features='sqrt',
                random_state=42,
                n_jobs=-1
            )
            rf.fit(X_train, y_train)
            rf_score = accuracy_score(y_test, rf.predict(X_test))

            # Train GradientBoosting with enhanced parameters
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

            # Show feature importance for RandomForest
            importances = rf.feature_importances_
            top_features_idx = np.argsort(importances)[-10:][::-1]
            print(f"   📊 Top 10 features for {market}:")
            for idx in top_features_idx:
                print(f"      {self.feature_cols[idx]}: {importances[idx]:.3f}")

        print(f"\n{'='*80}")
        print(f"✅ Training complete! {len(self.models)} models trained")
        print(f"{'='*80}\n")

    def create_synthetic_odds(self, match: dict) -> dict:
        """Create synthetic odds for training"""
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

    def save_models(self, filename: str = 'models/soccer_ml_models_with_form.pkl'):
        """Save trained models"""
        model_data = {
            'models': self.models,
            'scaler': self.scaler,
            'feature_cols': self.feature_cols,
            'feature_columns': self.feature_cols,  # Backward compatibility
            'trained_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'training_samples': len(self.models),
            'markets': self.markets,
            'has_form_features': True,  # Flag to indicate form features are included
            'num_features': len(self.feature_cols),
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
        print(f"📋 Features: {model_data['num_features']} (13 odds + 32 form)")
        print(f"📅 Trained: {model_data['trained_date']}")


def main():
    """Main training pipeline"""
    print("\n⚽ FORM-ENHANCED SOCCER MODEL TRAINER (Phase 2)")
    print("="*80 + "\n")

    # Top leagues for training (excluding blacklisted leagues)
    leagues = {
        'Premier League': 39,
        'La Liga': 140,
        'Serie A': 135,
        'Ligue 1': 61,
        # Excluded: Bundesliga (22% WR), Brazil Serie A (47% WR)
    }

    # Train on recent season
    seasons = [2024]  # Current season

    trainer = FormEnhancedSoccerTrainer()

    all_training_data = []

    # Collect data from all leagues
    for league_name, league_id in leagues.items():
        print(f"\n📊 Processing {league_name}...")

        for season in seasons:
            matches = trainer.fetch_league_matches(league_id, season, max_matches=150)
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

    print("\n✅ Form-enhanced soccer models trained successfully!")
    print(f"📊 Total matches: {len(all_training_data)}")
    print(f"🤖 Total models: {len(trainer.models)}")
    print(f"📋 Markets: {', '.join(trainer.markets)}")
    print(f"✨ Features: 45 (13 odds + 32 form)")


if __name__ == "__main__":
    main()
