#!/usr/bin/env python3
"""
Daily NHL Betting Report Generator
Creates comprehensive CSV report with predictions, confidence, edges, and totals
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime
import pickle
import argparse
import sys
import os
from typing import Optional

# Add utils and strategies to path
utils_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils')
strategies_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, utils_dir)
sys.path.insert(0, strategies_dir)
from nhl_enhanced_data import NHLEnhancedData
from nhl_odds_api_failover import NHLOddsFailover
from nhl_stats_api_failover import NHLStatsFailover


class NHLDailyReport:
    """Generate daily NHL betting report"""

    def __init__(self,
                 hockey_api_key: str = '960c628e1c91c4b1f125e1eec52ad862',
                 odds_api_key: str = '518c226b561ad7586ec8c5dd1144e3fb'):

        self.hockey_api_key = hockey_api_key
        self.odds_api_key = odds_api_key
        self.hockey_base_url = "https://v1.hockey.api-sports.io"
        self.odds_base_url = "https://api.the-odds-api.com/v4"

        # Load trained models
        try:
            model_path = os.path.join(strategies_dir, 'nhl_enhanced_models.pkl')
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)

            self.models = model_data['models']
            self.scaler = model_data['scaler']
            self.feature_names = model_data.get('feature_names', model_data.get('feature_cols', []))

            print(f"✅ Loaded NHL models: {list(self.models.keys())}")
        except FileNotFoundError:
            print(f"❌ Models not found. Run nhl_enhanced_trainer.py first!")
            sys.exit(1)

        self.data_integrator = NHLEnhancedData()

        # Initialize failover systems
        self.odds_failover = NHLOddsFailover(odds_api_key)
        self.stats_failover = NHLStatsFailover()

        print("✅ Failover systems initialized (NO simulated data will be used)")

    def get_upcoming_games(self, date_str: str = None) -> list:
        """Get upcoming NHL games from official NHL API"""
        # Default to today if no date provided
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')

        # Use official NHL API
        nhl_schedule_url = f"https://api-web.nhle.com/v1/schedule/{date_str}"

        try:
            response = requests.get(nhl_schedule_url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                game_week = data.get('gameWeek', [])

                all_games = []
                for day in game_week:
                    if day.get('date') == date_str:
                        games = day.get('games', [])

                        # Convert to our format
                        for game in games:
                            game_state = game.get('gameState', 'UNKNOWN')

                            # Only include games that haven't started or are in progress
                            if game_state in ['FUT', 'LIVE', 'CRIT']:
                                converted_game = {
                                    'teams': {
                                        'home': {
                                            'name': game.get('homeTeam', {}).get('placeName', {}).get('default', 'Unknown')
                                        },
                                        'away': {
                                            'name': game.get('awayTeam', {}).get('placeName', {}).get('default', 'Unknown')
                                        }
                                    },
                                    'status': {
                                        'short': 'NS' if game_state == 'FUT' else 'LIVE'
                                    },
                                    'date': game.get('startTimeUTC', ''),
                                    'id': game.get('id', 0)
                                }
                                all_games.append(converted_game)

                        return all_games

                return []
            return []
        except Exception as e:
            print(f"Error fetching games: {e}")
            return []

    def get_game_odds(self, home_team: str, away_team: str) -> Optional[dict]:
        """
        Get real odds using failover system.
        Returns None if no real odds available (game will be skipped)
        NO SIMULATED DATA EVER RETURNED
        """
        return self.odds_failover.get_odds(home_team, away_team)

    def estimate_goals_total(self, features_dict: dict) -> dict:
        """Estimate expected total goals based on xG"""
        home_xg = features_dict.get('home_xGF_per_game', 2.5)
        away_xg = features_dict.get('away_xGF_per_game', 2.5)

        expected_total = home_xg + away_xg

        # Estimate over/under probability based on historical data
        # NHL games average ~6.5 goals, std ~2.5
        std_dev = 2.5
        total_line = 6.5

        # Z-score for over probability
        z_score = (expected_total - total_line) / std_dev

        # Convert to probability (using normal distribution approximation)
        from scipy import stats
        try:
            over_prob = 1 - stats.norm.cdf(z_score)
        except:
            # Fallback if scipy not available
            if expected_total > total_line:
                over_prob = 0.6
            else:
                over_prob = 0.4

        return {
            'expected_total': round(expected_total, 1),
            'over_probability': round(over_prob, 3),
            'under_probability': round(1 - over_prob, 3)
        }

    def predict_puck_line(self, home_prob: float, away_prob: float,
                         home_xg: float, away_xg: float) -> dict:
        """Predict -1.5 puck line (winning by 2+ goals)"""

        # Estimate goal differential
        expected_diff = home_xg - away_xg

        # Home team covering -1.5 (winning by 2+)
        # Higher probability if:
        # 1. Strong win probability (>60%)
        # 2. Expected to score 1+ more goals

        home_cover_prob = 0.0
        away_cover_prob = 0.0

        if home_prob > 0.6 and expected_diff > 0.8:
            home_cover_prob = min(0.45, home_prob * 0.6)  # Max 45%

        if away_prob > 0.6 and expected_diff < -0.8:
            away_cover_prob = min(0.45, away_prob * 0.6)  # Max 45%

        # Confidence based on margin
        if expected_diff > 1.5:
            confidence = "High"
        elif expected_diff > 0.8:
            confidence = "Medium"
        elif expected_diff < -1.5:
            confidence = "High"
        elif expected_diff < -0.8:
            confidence = "Medium"
        else:
            confidence = "Low"

        return {
            'home_puck_line_prob': round(home_cover_prob, 3),
            'away_puck_line_prob': round(away_cover_prob, 3),
            'puck_line_confidence': confidence,
            'expected_goal_diff': round(expected_diff, 1)
        }

    def generate_daily_report(self, date_str: str = None) -> pd.DataFrame:
        """Generate comprehensive daily report"""

        games = self.get_upcoming_games(date_str)

        if not games:
            print(f"⚠️  No games found for {date_str or 'today'}")
            return pd.DataFrame()

        print(f"📊 Generating report for {len(games)} games...")

        report_data = []

        for game in games:
            teams = game.get('teams', {})
            home_team = teams.get('home', {}).get('name', 'Unknown')
            away_team = teams.get('away', {}).get('name', 'Unknown')
            game_date = game.get('date', '')
            game_time = datetime.fromisoformat(game_date.replace('Z', '+00:00')).strftime('%H:%M') if game_date else 'TBD'

            # Get odds (REAL DATA ONLY - no simulation)
            odds = self.get_game_odds(home_team, away_team)

            # Skip game if no real odds available
            if odds is None:
                print(f"   ⚠️  Skipping {away_team} @ {home_team} - no real odds available")
                continue

            # Ensure we have complete odds data
            if not odds.get('home_odds') or not odds.get('away_odds'):
                print(f"   ⚠️  Skipping {away_team} @ {home_team} - incomplete odds data")
                continue

            # Build features
            features_dict = self.data_integrator.build_enhanced_features(
                home_team, away_team,
                odds['home_odds'], odds['away_odds'],
                season=2024
            )

            if not features_dict:
                print(f"   ⚠️  Skipping {away_team} @ {home_team} - no stats data available")
                continue

            # Make predictions
            features = np.array([features_dict[name] for name in self.feature_names])
            features_scaled = self.scaler.transform([features])

            # Average across models
            all_home_probs = []
            all_away_probs = []

            for model_name, model in self.models.items():
                probs = model.predict_proba(features_scaled)[0]
                all_home_probs.append(probs[1])
                all_away_probs.append(probs[0])

            avg_home_prob = np.mean(all_home_probs)
            avg_away_prob = np.mean(all_away_probs)

            # Determine winner
            predicted_winner = home_team if avg_home_prob > avg_away_prob else away_team
            winner_confidence = max(avg_home_prob, avg_away_prob)

            # Calculate edge
            if predicted_winner == home_team:
                implied_prob = 1 / odds['home_odds']
                edge = (avg_home_prob - implied_prob) / implied_prob
                winner_odds = odds['home_odds']
            else:
                implied_prob = 1 / odds['away_odds']
                edge = (avg_away_prob - implied_prob) / implied_prob
                winner_odds = odds['away_odds']

            # Estimate totals
            totals_pred = self.estimate_goals_total(features_dict)

            # Total edge
            total_line = odds['total_line']
            over_implied = 1 / odds['over_odds']
            total_edge = (totals_pred['over_probability'] - over_implied) / over_implied

            # Puck line prediction
            puck_line = self.predict_puck_line(
                avg_home_prob, avg_away_prob,
                features_dict.get('home_xGF_per_game', 2.5),
                features_dict.get('away_xGF_per_game', 2.5)
            )

            # Build report row
            report_data.append({
                'Date': game_date[:10] if game_date else '',
                'Time': game_time,
                'Away_Team': away_team,
                'Home_Team': home_team,
                'Predicted_Winner': predicted_winner,
                'Win_Confidence': f"{winner_confidence*100:.1f}%",
                'Winner_Odds': f"{winner_odds:.2f}",
                'Win_Edge': f"{edge*100:+.1f}%",
                'Expected_Total': totals_pred['expected_total'],
                'Total_Line': total_line,
                'Over_Probability': f"{totals_pred['over_probability']*100:.1f}%",
                'Total_Edge': f"{total_edge*100:+.1f}%",
                'Puck_Line_-1.5': f"{predicted_winner} ({puck_line['puck_line_confidence']})",
                'Puck_Line_Home_Prob': f"{puck_line['home_puck_line_prob']*100:.1f}%",
                'Puck_Line_Away_Prob': f"{puck_line['away_puck_line_prob']*100:.1f}%",
                'Expected_Goal_Diff': puck_line['expected_goal_diff'],
                'Home_Odds': f"{odds['home_odds']:.2f}",
                'Away_Odds': f"{odds['away_odds']:.2f}",
                'Bookmaker': odds['bookmaker'],
                'Odds_Source': self.odds_failover.get_last_source(),  # Track which API was used
                'Stats_Source': self.stats_failover.get_last_source()  # Track stats source too
            })

        df_report = pd.DataFrame(report_data)
        return df_report

    def save_report(self, df: pd.DataFrame, date_str: str = None):
        """Save report to CSV"""
        if df.empty:
            print("No data to save")
            return

        if date_str:
            use_date = date_str
        else:
            use_date = datetime.now().strftime('%Y-%m-%d')

        # Create date-based folder structure: reports/YYYYMMDD/
        date_folder = use_date.replace('-', '')  # Convert 2025-10-17 to 20251017
        reports_dir = os.path.join('reports', date_folder)
        os.makedirs(reports_dir, exist_ok=True)

        filename = os.path.join(reports_dir, f"nhl_daily_report_{use_date}.csv")

        df.to_csv(filename, index=False)
        print(f"\n✅ Report saved to: {filename}")
        print(f"📊 {len(df)} games analyzed")

        # Print summary
        print(f"\n📋 SUMMARY:")
        print(f"{'='*80}")

        for idx, row in df.iterrows():
            print(f"\n🏒 {row['Away_Team']} @ {row['Home_Team']}")
            print(f"   Predicted Winner: {row['Predicted_Winner']} ({row['Win_Confidence']}) | Edge: {row['Win_Edge']}")
            print(f"   Expected Total: {row['Expected_Total']} (O/U {row['Total_Line']}) | Over: {row['Over_Probability']}")
            print(f"   Puck Line -1.5: {row['Puck_Line_-1.5']}")


def main():
    parser = argparse.ArgumentParser(description='Generate daily NHL betting report')
    parser.add_argument('--date', type=str,
                       help='Date in YYYY-MM-DD format (default: next available games)')
    parser.add_argument('--output', type=str,
                       help='Output CSV filename (default: auto-generated)')

    args = parser.parse_args()

    print("🏒 NHL DAILY BETTING REPORT GENERATOR")
    print("=" * 80)

    reporter = NHLDailyReport()
    df_report = reporter.generate_daily_report(args.date)

    if not df_report.empty:
        reporter.save_report(df_report, args.date)
    else:
        print("\n⚠️  No games to report")


if __name__ == "__main__":
    main()
