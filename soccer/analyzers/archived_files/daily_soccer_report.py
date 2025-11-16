#!/usr/bin/env python3
"""
Daily Soccer Report Generator
Generates predictions for ALL matches scheduled for a given date
Similar to NHL daily_nhl_report.py
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import argparse
import joblib
import requests
import time

class DailySoccerReport:
    """Generate comprehensive daily soccer predictions"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.models_file = Path('soccer_ml_models.pkl')
        self.stats_file = Path('team_statistics.json')
        self.leagues_file = Path('output reports/Older/UPDATED_supported_leagues_database.csv')
        self.api_base = "https://v3.football.api-sports.io"
        self.headers = {
            "x-apisports-key": api_key
        }
        self.load_models()
        self.load_team_stats()
        self.load_supported_leagues()

    def load_models(self):
        """Load trained ML models"""
        if not self.models_file.exists():
            print(f"❌ Models file not found: {self.models_file}")
            print("   Please run update_models_with_results.py first")
            raise FileNotFoundError("Models not trained yet")

        model_data = joblib.load(self.models_file)
        self.models = model_data['models']
        self.feature_cols = model_data.get('feature_cols', model_data.get('feature_columns', []))
        print(f"✅ Loaded models: {list(self.models.keys())}")

    def load_team_stats(self):
        """Load team statistics from cache"""
        if self.stats_file.exists():
            import json
            with open(self.stats_file, 'r') as f:
                self.team_stats = json.load(f)
            print(f"✅ Loaded statistics for {len(self.team_stats)} teams")
        else:
            self.team_stats = {}
            print("⚠️  No team statistics found - predictions will use league averages")

    def load_supported_leagues(self):
        """Load list of supported league IDs"""
        if self.leagues_file.exists():
            df = pd.read_csv(self.leagues_file)
            self.supported_league_ids = set(df['league_id'].astype(int).tolist())
            print(f"✅ Loaded {len(self.supported_league_ids)} supported leagues")
        else:
            print("⚠️  No leagues file found - will analyze all leagues")
            self.supported_league_ids = None

    def get_team_stats(self, team_id: int, season: int = 2024):
        """Get statistics for a specific team"""
        team_key = f"{team_id}_{season}"
        return self.team_stats.get(team_key, None)

    def fetch_fixtures_for_date(self, date_str: str):
        """Fetch all fixtures scheduled for a specific date"""

        print(f"\n📅 Fetching fixtures for {date_str}...")

        try:
            url = f"{self.api_base}/fixtures"
            params = {
                "date": date_str
            }

            response = requests.get(url, headers=self.headers, params=params)

            if response.status_code == 200:
                data = response.json()
                all_fixtures = data.get('response', [])

                # Filter by supported leagues
                if self.supported_league_ids:
                    fixtures = [f for f in all_fixtures if f['league']['id'] in self.supported_league_ids]
                    print(f"   ✅ Found {len(fixtures)} fixtures in supported leagues ({len(all_fixtures)} total)")
                else:
                    fixtures = all_fixtures
                    print(f"   ✅ Found {len(fixtures)} fixtures")

                return fixtures
            else:
                print(f"   ❌ API error: {response.status_code}")
                return []

        except Exception as e:
            print(f"   ❌ Error fetching fixtures: {e}")
            return []

    def build_prediction_features(self, fixture):
        """Build feature vector for prediction using team-specific statistics"""

        home_team_id = fixture['teams']['home']['id']
        away_team_id = fixture['teams']['away']['id']

        # Get team statistics
        home_stats = self.get_team_stats(home_team_id)
        away_stats = self.get_team_stats(away_team_id)

        # League averages (fallback if no team stats available)
        league_avg = {
            'shots': 12.0,
            'shots_on_target': 5.0,
            'possession': 50.0,
            'corners': 5.0,
            'fouls': 11.5,
            'goals_for': 1.3,
            'goals_against': 1.3
        }

        # Build features from team stats or use league averages
        if home_stats and home_stats.get('played', 0) > 0:
            home_goals_for = home_stats.get('goals_for_avg_home', league_avg['goals_for'])
            home_goals_against = home_stats.get('goals_against_avg_home', league_avg['goals_against'])
            # Estimate shots based on goals (rough approximation: ~10 shots per goal)
            home_shots = home_goals_for * 9.0 + 3.0
            home_shots_on_target = home_goals_for * 4.0 + 1.0
        else:
            home_shots = league_avg['shots']
            home_shots_on_target = league_avg['shots_on_target']
            home_goals_for = league_avg['goals_for']
            home_goals_against = league_avg['goals_against']

        if away_stats and away_stats.get('played', 0) > 0:
            away_goals_for = away_stats.get('goals_for_avg_away', league_avg['goals_for'])
            away_goals_against = away_stats.get('goals_against_avg_away', league_avg['goals_against'])
            away_shots = away_goals_for * 9.0 + 1.0
            away_shots_on_target = away_goals_for * 3.5 + 0.5
        else:
            away_shots = league_avg['shots'] - 2.0  # Away teams typically have fewer shots
            away_shots_on_target = league_avg['shots_on_target'] - 1.0
            away_goals_for = league_avg['goals_for']
            away_goals_against = league_avg['goals_against']

        # Calculate derived features
        xg_diff = home_goals_for - away_goals_against
        shots_diff = home_shots - away_shots

        features = {
            'home_shots': home_shots,
            'away_shots': away_shots,
            'home_shots_on_target': home_shots_on_target,
            'away_shots_on_target': away_shots_on_target,
            'home_possession': 50.0 + (home_goals_for - away_goals_for) * 3.0,  # Estimated possession based on attack strength
            'away_possession': 50.0 + (away_goals_for - home_goals_for) * 3.0,
            'home_corners': home_shots / 2.2,  # Rough approximation
            'away_corners': away_shots / 2.2,
            'home_fouls': league_avg['fouls'],
            'away_fouls': league_avg['fouls'],
            'xg_diff': xg_diff,
            'shots_diff': shots_diff
        }

        return features

    def make_predictions(self, features):
        """Make predictions using all models"""

        X = pd.DataFrame([features])[self.feature_cols]

        predictions = {}

        # Match Result - handle models that may not have all 3 classes
        match_proba = self.models['match_outcome'].predict_proba(X)[0]

        # Ensure we have 3 classes (home, draw, away)
        if len(match_proba) == 3:
            predictions['home_win_prob'] = match_proba[0]
            predictions['draw_prob'] = match_proba[1]
            predictions['away_win_prob'] = match_proba[2]
            predictions['predicted_winner'] = ['Home', 'Draw', 'Away'][np.argmax(match_proba)]
        elif len(match_proba) == 2:
            # Model only trained on 2 classes - assume home/away
            predictions['home_win_prob'] = match_proba[0]
            predictions['draw_prob'] = 0.25  # Default
            predictions['away_win_prob'] = match_proba[1]
            predictions['predicted_winner'] = 'Home' if match_proba[0] > match_proba[1] else 'Away'
        else:
            # Fallback defaults
            predictions['home_win_prob'] = 0.40
            predictions['draw_prob'] = 0.30
            predictions['away_win_prob'] = 0.30
            predictions['predicted_winner'] = 'Home'

        predictions['win_confidence'] = max([predictions['home_win_prob'],
                                             predictions['draw_prob'],
                                             predictions['away_win_prob']])

        # Over 2.5 Goals
        over25_proba = self.models['over_2_5'].predict_proba(X)[0]
        predictions['over_2_5_prob'] = over25_proba[1] if len(over25_proba) > 1 else 0.5
        predictions['under_2_5_prob'] = over25_proba[0]

        # BTTS
        btts_proba = self.models['btts'].predict_proba(X)[0]
        predictions['btts_yes_prob'] = btts_proba[1] if len(btts_proba) > 1 else 0.5
        predictions['btts_no_prob'] = btts_proba[0]

        # Corners
        corners85_proba = self.models['over_8_5_corners'].predict_proba(X)[0]
        predictions['over_8_5_corners_prob'] = corners85_proba[1] if len(corners85_proba) > 1 else 0.5

        corners105_proba = self.models['over_10_5_corners'].predict_proba(X)[0]
        predictions['over_10_5_corners_prob'] = corners105_proba[1] if len(corners105_proba) > 1 else 0.5

        return predictions

    def generate_daily_report(self, date_str: str):
        """Generate complete daily report for all matches"""

        print(f"\n{'='*70}")
        print(f"⚽ DAILY SOCCER PREDICTIONS - {date_str}")
        print(f"{'='*70}\n")

        # Fetch fixtures
        fixtures = self.fetch_fixtures_for_date(date_str)

        if not fixtures:
            print("❌ No fixtures found for this date")
            return

        print(f"📊 Generating predictions for {len(fixtures)} matches...\n")

        # Generate predictions for each match
        report_data = []

        for fixture in fixtures:
            try:
                home_team = fixture['teams']['home']['name']
                away_team = fixture['teams']['away']['name']
                league = fixture['league']['name']
                kickoff = fixture['fixture']['date']

                print(f"   Analyzing: {home_team} vs {away_team}")

                # Build features
                features = self.build_prediction_features(fixture)

                # Make predictions
                preds = self.make_predictions(features)

                # Compile report entry
                report_entry = {
                    'Date': date_str,
                    'Kickoff': kickoff,
                    'Home_Team': home_team,
                    'Away_Team': away_team,
                    'League': league,

                    # Match Result
                    'Predicted_Winner': preds['predicted_winner'],
                    'Win_Confidence': f"{preds['win_confidence']:.1%}",
                    'Home_Win_Prob': f"{preds['home_win_prob']:.1%}",
                    'Draw_Prob': f"{preds['draw_prob']:.1%}",
                    'Away_Win_Prob': f"{preds['away_win_prob']:.1%}",

                    # Goals
                    'Over_2.5_Prob': f"{preds['over_2_5_prob']:.1%}",
                    'Under_2.5_Prob': f"{preds['under_2_5_prob']:.1%}",

                    # BTTS
                    'BTTS_Yes_Prob': f"{preds['btts_yes_prob']:.1%}",
                    'BTTS_No_Prob': f"{preds['btts_no_prob']:.1%}",

                    # Corners
                    'Over_8.5_Corners_Prob': f"{preds['over_8_5_corners_prob']:.1%}",
                    'Over_10.5_Corners_Prob': f"{preds['over_10_5_corners_prob']:.1%}",
                }

                report_data.append(report_entry)

            except Exception as e:
                print(f"   ❌ Error processing {home_team} vs {away_team}: {e}")

        # Create DataFrame
        df_report = pd.DataFrame(report_data)

        # Save to CSV
        output_file = f"soccer_daily_report_{date_str}.csv"
        df_report.to_csv(output_file, index=False)

        print(f"\n✅ Report saved: {output_file}")
        print(f"📊 {len(df_report)} matches analyzed\n")

        # Print summary
        self.print_summary(df_report)

        return df_report

    def print_summary(self, df_report):
        """Print formatted summary of predictions"""

        print(f"\n{'='*70}")
        print("📋 PREDICTION SUMMARY")
        print(f"{'='*70}\n")

        for idx, row in df_report.iterrows():
            print(f"⚽ {row['Home_Team']} vs {row['Away_Team']}")
            print(f"   🏆 {row['League']} | 🕒 {row['Kickoff']}")
            print(f"   🎯 Prediction: {row['Predicted_Winner']} ({row['Win_Confidence']})")
            print(f"   📊 H: {row['Home_Win_Prob']} | D: {row['Draw_Prob']} | A: {row['Away_Win_Prob']}")
            print(f"   ⚽ Over 2.5: {row['Over_2.5_Prob']} | BTTS: {row['BTTS_Yes_Prob']}")
            print(f"   🚩 Corners: O8.5 {row['Over_8.5_Corners_Prob']} | O10.5 {row['Over_10.5_Corners_Prob']}")
            print()


def main():
    parser = argparse.ArgumentParser(description='Generate daily soccer predictions')
    parser.add_argument('--date', type=str, help='Date for predictions (YYYY-MM-DD)')

    args = parser.parse_args()

    # API key
    api_key = "960c628e1c91c4b1f125e1eec52ad862"

    reporter = DailySoccerReport(api_key)

    # Determine date
    if args.date:
        date_str = args.date
    else:
        # Default: today
        date_str = datetime.now().strftime('%Y-%m-%d')

    # Generate report
    reporter.generate_daily_report(date_str)


if __name__ == "__main__":
    main()
