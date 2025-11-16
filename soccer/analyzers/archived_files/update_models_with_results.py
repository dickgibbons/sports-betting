#!/usr/bin/env python3
"""
Soccer Continuous Learning System
Updates ML models daily with real match results
Similar to NHL system - learns from every match
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import argparse
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
import requests
import json
import time

class SoccerModelUpdater:
    """Continuously update soccer models with new match results"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.models_file = Path('soccer_ml_models.pkl')
        self.training_history_file = Path('training_history.csv')
        self.api_base = "https://v3.football.api-sports.io"
        self.headers = {
            "x-apisports-key": api_key
        }

    def fetch_finished_matches(self, date_str: str):
        """Fetch finished matches from specific date"""

        print(f"\n📊 Fetching finished matches for {date_str}...")

        try:
            # API-Football date format: YYYY-MM-DD
            url = f"{self.api_base}/fixtures"
            params = {
                "date": date_str,
                "status": "FT"  # Full Time only
            }

            response = requests.get(url, headers=self.headers, params=params)

            if response.status_code == 200:
                data = response.json()
                fixtures = data.get('response', [])

                print(f"   ✅ Found {len(fixtures)} finished matches")
                return fixtures
            else:
                print(f"   ❌ API error: {response.status_code}")
                return []

        except Exception as e:
            print(f"   ❌ Error fetching matches: {e}")
            return []

    def extract_match_features(self, fixture):
        """Extract features from match data for training"""

        try:
            # Basic match info
            home_team = fixture['teams']['home']['name']
            away_team = fixture['teams']['away']['name']
            home_score = fixture['goals']['home'] or 0
            away_score = fixture['goals']['away'] or 0

            # Calculate outcomes
            if home_score > away_score:
                outcome = 0  # Home win
            elif home_score < away_score:
                outcome = 2  # Away win
            else:
                outcome = 1  # Draw

            total_goals = home_score + away_score
            over_2_5 = 1 if total_goals > 2.5 else 0
            btts = 1 if (home_score > 0 and away_score > 0) else 0

            # Get league info
            league = fixture['league']['name']

            # Get statistics if available
            stats = fixture.get('statistics', [])

            home_stats = {}
            away_stats = {}

            if len(stats) >= 2:
                for team_stats in stats:
                    team_name = team_stats['team']['name']
                    stats_dict = {stat['type']: stat['value'] for stat in team_stats['statistics']}

                    if team_name == home_team:
                        home_stats = stats_dict
                    else:
                        away_stats = stats_dict

            # Extract key stats with defaults
            features = {
                'date': fixture['fixture']['date'][:10],
                'home_team': home_team,
                'away_team': away_team,
                'league': league,
                'home_score': home_score,
                'away_score': away_score,
                'outcome': outcome,
                'total_goals': total_goals,
                'over_2_5': over_2_5,
                'btts': btts,

                # Team stats (with defaults)
                'home_shots': self._parse_stat(home_stats.get('Total Shots', 10)),
                'away_shots': self._parse_stat(away_stats.get('Total Shots', 10)),
                'home_shots_on_target': self._parse_stat(home_stats.get('Shots on Goal', 5)),
                'away_shots_on_target': self._parse_stat(away_stats.get('Shots on Goal', 5)),
                'home_possession': self._parse_stat(home_stats.get('Ball Possession', '50%')),
                'away_possession': self._parse_stat(away_stats.get('Ball Possession', '50%')),
                'home_corners': self._parse_stat(home_stats.get('Corner Kicks', 5)),
                'away_corners': self._parse_stat(away_stats.get('Corner Kicks', 5)),
                'home_fouls': self._parse_stat(home_stats.get('Fouls', 10)),
                'away_fouls': self._parse_stat(away_stats.get('Fouls', 10)),
                'home_yellow': self._parse_stat(home_stats.get('Yellow Cards', 1)),
                'away_yellow': self._parse_stat(away_stats.get('Yellow Cards', 1)),
            }

            # Calculate derived features
            features['total_corners'] = features['home_corners'] + features['away_corners']
            features['over_8_5_corners'] = 1 if features['total_corners'] > 8.5 else 0
            features['over_10_5_corners'] = 1 if features['total_corners'] > 10.5 else 0
            features['xg_diff'] = features['home_shots_on_target'] - features['away_shots_on_target']
            features['shots_diff'] = features['home_shots'] - features['away_shots']

            return features

        except Exception as e:
            print(f"   ❌ Error extracting features: {e}")
            return None

    def _parse_stat(self, value):
        """Parse stat value (handles None, strings, percentages)"""
        if value is None:
            return 0
        if isinstance(value, str):
            if '%' in value:
                return float(value.replace('%', ''))
            try:
                return float(value)
            except:
                return 0
        return float(value)

    def load_or_create_training_history(self):
        """Load existing training history or create new"""

        if self.training_history_file.exists():
            df = pd.read_csv(self.training_history_file)
            print(f"   📚 Loaded {len(df)} historical matches")
            return df
        else:
            print("   📝 Creating new training history")
            return pd.DataFrame()

    def update_training_history(self, new_matches):
        """Add new matches to training history"""

        if not new_matches:
            print("   ⚠️  No new matches to add")
            return

        df_history = self.load_or_create_training_history()
        df_new = pd.DataFrame(new_matches)

        # Combine and remove duplicates
        if not df_history.empty:
            df_combined = pd.concat([df_history, df_new], ignore_index=True)
            df_combined = df_combined.drop_duplicates(subset=['date', 'home_team', 'away_team'], keep='last')
        else:
            df_combined = df_new

        # Save updated history
        df_combined.to_csv(self.training_history_file, index=False)
        print(f"   ✅ Training history updated: {len(df_combined)} total matches (+{len(new_matches)} new)")

        return df_combined

    def retrain_models(self, df_history, full_retrain=False):
        """Retrain models with updated data"""

        if df_history.empty or len(df_history) < 50:
            print("   ⚠️  Not enough data to retrain (need at least 50 matches)")
            return

        print(f"\n🔨 {'Full' if full_retrain else 'Incremental'} model retraining...")

        # Prepare features
        feature_cols = [
            'home_shots', 'away_shots', 'home_shots_on_target', 'away_shots_on_target',
            'home_possession', 'away_possession', 'home_corners', 'away_corners',
            'home_fouls', 'away_fouls', 'xg_diff', 'shots_diff'
        ]

        X = df_history[feature_cols].fillna(0)

        # Train multiple models
        models = {}

        # 1. Match Result
        y_outcome = df_history['outcome']
        models['match_outcome'] = RandomForestClassifier(
            n_estimators=100, random_state=42, n_jobs=-1
        )
        models['match_outcome'].fit(X, y_outcome)
        acc_outcome = cross_val_score(models['match_outcome'], X, y_outcome, cv=5).mean()
        print(f"   📊 Match Result: {acc_outcome:.1%} accuracy")

        # 2. Over 2.5 Goals
        y_over25 = df_history['over_2_5']
        models['over_2_5'] = RandomForestClassifier(
            n_estimators=100, random_state=42, n_jobs=-1
        )
        models['over_2_5'].fit(X, y_over25)
        acc_over25 = cross_val_score(models['over_2_5'], X, y_over25, cv=5).mean()
        print(f"   📊 Over 2.5 Goals: {acc_over25:.1%} accuracy")

        # 3. BTTS
        y_btts = df_history['btts']
        models['btts'] = RandomForestClassifier(
            n_estimators=100, random_state=42, n_jobs=-1
        )
        models['btts'].fit(X, y_btts)
        acc_btts = cross_val_score(models['btts'], X, y_btts, cv=5).mean()
        print(f"   📊 BTTS: {acc_btts:.1%} accuracy")

        # 4. Over 8.5 Corners
        y_corners85 = df_history['over_8_5_corners']
        models['over_8_5_corners'] = RandomForestClassifier(
            n_estimators=100, random_state=42, n_jobs=-1
        )
        models['over_8_5_corners'].fit(X, y_corners85)
        acc_corners85 = cross_val_score(models['over_8_5_corners'], X, y_corners85, cv=5).mean()
        print(f"   📊 Over 8.5 Corners: {acc_corners85:.1%} accuracy")

        # 5. Over 10.5 Corners
        y_corners105 = df_history['over_10_5_corners']
        models['over_10_5_corners'] = RandomForestClassifier(
            n_estimators=100, random_state=42, n_jobs=-1
        )
        models['over_10_5_corners'].fit(X, y_corners105)
        acc_corners105 = cross_val_score(models['over_10_5_corners'], X, y_corners105, cv=5).mean()
        print(f"   📊 Over 10.5 Corners: {acc_corners105:.1%} accuracy")

        # Backup old models
        if self.models_file.exists():
            backup_name = f"soccer_ml_models_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
            self.models_file.rename(backup_name)
            print(f"   💾 Old models backed up: {backup_name}")

        # Save new models
        model_data = {
            'models': models,
            'feature_cols': feature_cols,
            'training_date': datetime.now().isoformat(),
            'training_size': len(df_history),
            'accuracies': {
                'match_outcome': acc_outcome,
                'over_2_5': acc_over25,
                'btts': acc_btts,
                'over_8_5_corners': acc_corners85,
                'over_10_5_corners': acc_corners105
            }
        }

        joblib.dump(model_data, self.models_file)
        print(f"   ✅ Models saved: {self.models_file}")

    def update_with_date(self, date_str: str, full_retrain=False):
        """Complete update workflow for a specific date"""

        print(f"\n{'='*70}")
        print(f"🔄 SOCCER MODEL UPDATE - {date_str}")
        print(f"{'='*70}")

        # Fetch finished matches
        fixtures = self.fetch_finished_matches(date_str)

        if not fixtures:
            print(f"\n⚠️  No finished matches found for {date_str}")
            return

        # Extract features from matches
        print(f"\n📊 Extracting features from {len(fixtures)} matches...")
        new_matches = []

        for fixture in fixtures:
            features = self.extract_match_features(fixture)
            if features:
                new_matches.append(features)

        print(f"   ✅ Extracted {len(new_matches)} match records")

        # Update training history
        df_history = self.update_training_history(new_matches)

        # Retrain models
        if len(new_matches) > 0:
            self.retrain_models(df_history, full_retrain=full_retrain)

        print(f"\n{'='*70}")
        print(f"✅ Model update complete!")
        print(f"   📚 Total training data: {len(df_history)} matches")
        print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(description='Update soccer models with real results')
    parser.add_argument('--date', type=str, help='Date to fetch results (YYYY-MM-DD)')
    parser.add_argument('--auto', action='store_true', help='Auto-detect yesterday')
    parser.add_argument('--days', type=int, default=1, help='Number of days back')
    parser.add_argument('--full-retrain', action='store_true', help='Full model retrain')

    args = parser.parse_args()

    # API key
    api_key = "960c628e1c91c4b1f125e1eec52ad862"

    updater = SoccerModelUpdater(api_key)

    # Determine dates to process
    if args.auto:
        # Process yesterday by default
        date = datetime.now() - timedelta(days=1)
        date_str = date.strftime('%Y-%m-%d')
        updater.update_with_date(date_str, full_retrain=args.full_retrain)
    elif args.date:
        updater.update_with_date(args.date, full_retrain=args.full_retrain)
    else:
        # Default: yesterday
        date = datetime.now() - timedelta(days=1)
        date_str = date.strftime('%Y-%m-%d')
        updater.update_with_date(date_str, full_retrain=args.full_retrain)


if __name__ == "__main__":
    main()
