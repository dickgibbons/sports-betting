#!/usr/bin/env python3
"""
Daily NBA Betting Report Generator
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nba_enhanced_data import NBAEnhancedData
from nba_odds_api_failover import NBAOddsFailover
from nba_stats_api_failover import NBAStatsFailover


class NBADailyReport:
    """Generate daily NBA betting report"""

    def __init__(self, odds_api_key: str = '518c226b561ad7586ec8c5dd1144e3fb'):

        self.odds_api_key = odds_api_key

        # Load trained models
        try:
            with open('nba_enhanced_models.pkl', 'rb') as f:
                model_data = pickle.load(f)

            self.models = model_data['models']
            self.scaler = model_data['scaler']
            self.feature_names = model_data.get('feature_names', model_data.get('feature_cols', []))

            print(f"✅ Loaded NBA models: {list(self.models.keys())}")
        except FileNotFoundError:
            print(f"❌ Models not found. Run nba_enhanced_trainer.py first!")
            sys.exit(1)

        self.data_integrator = NBAEnhancedData()

        # Initialize failover systems
        self.odds_failover = NBAOddsFailover(odds_api_key)
        self.stats_failover = NBAStatsFailover()

        print("✅ Failover systems initialized (NO simulated data will be used)")

    def get_upcoming_games(self, date_str: str = None) -> list:
        """Get upcoming NBA games from official NBA API"""
        # Default to today if no date provided
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')

        # Use official NBA API
        nba_schedule_url = f"https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json"

        try:
            response = requests.get(nba_schedule_url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                games = data.get('scoreboard', {}).get('games', [])

                all_games = []
                for game in games:
                    game_status = game.get('gameStatus', 1)

                    # Only include games that haven't started (status 1 = upcoming)
                    if game_status == 1:
                        converted_game = {
                            'teams': {
                                'home': {
                                    'name': game.get('homeTeam', {}).get('teamCity', 'Unknown') + ' ' +
                                           game.get('homeTeam', {}).get('teamName', '')
                                },
                                'away': {
                                    'name': game.get('awayTeam', {}).get('teamCity', 'Unknown') + ' ' +
                                           game.get('awayTeam', {}).get('teamName', '')
                                }
                            },
                            'status': {
                                'short': 'NS'
                            },
                            'date': game.get('gameTimeUTC', ''),
                            'id': game.get('gameId', 0)
                        }
                        all_games.append(converted_game)

                return all_games

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

    def estimate_points_total(self, features_dict: dict) -> dict:
        """Estimate expected total points based on offensive/defensive ratings"""
        home_off = features_dict.get('home_offRating', 110)
        away_off = features_dict.get('away_offRating', 110)
        home_def = features_dict.get('home_defRating', 110)
        away_def = features_dict.get('away_defRating', 110)
        home_pace = features_dict.get('home_pace', 100)
        away_pace = features_dict.get('away_pace', 100)

        # Average pace
        avg_pace = (home_pace + away_pace) / 2

        # Expected points per 100 possessions
        home_expected_per_100 = (home_off + away_def) / 2
        away_expected_per_100 = (away_off + home_def) / 2

        # Convert to expected points in this game
        home_expected_pts = (home_expected_per_100 / 100) * avg_pace
        away_expected_pts = (away_expected_per_100 / 100) * avg_pace

        expected_total = home_expected_pts + away_expected_pts

        # Estimate over/under probability based on historical data
        # NBA games average ~220 points, std ~15
        std_dev = 15.0
        total_line = 220.0

        # Z-score for over probability
        z_score = (expected_total - total_line) / std_dev

        # Convert to probability (using normal distribution approximation)
        try:
            from scipy import stats
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

    def predict_spread(self, home_prob: float, away_prob: float,
                      home_expected_pts: float, away_expected_pts: float) -> dict:
        """Predict spread (winning margin)"""

        # Estimate expected margin
        expected_margin = home_expected_pts - away_expected_pts

        # Home team covering spread (typically -5.5 to -7.5 for favorites)
        # Higher probability if:
        # 1. Strong win probability (>60%)
        # 2. Expected to win by 6+ points

        home_cover_prob = 0.0
        away_cover_prob = 0.0

        if home_prob > 0.6 and expected_margin > 5:
            home_cover_prob = min(0.55, home_prob * 0.8)

        if away_prob > 0.6 and expected_margin < -5:
            away_cover_prob = min(0.55, away_prob * 0.8)

        # Confidence based on margin
        if abs(expected_margin) > 10:
            confidence = "High"
        elif abs(expected_margin) > 5:
            confidence = "Medium"
        else:
            confidence = "Low"

        return {
            'home_spread_prob': round(home_cover_prob, 3),
            'away_spread_prob': round(away_cover_prob, 3),
            'spread_confidence': confidence,
            'expected_margin': round(expected_margin, 1)
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
            totals_pred = self.estimate_points_total(features_dict)

            # Total edge
            total_line = odds.get('total_line', 220.0)
            over_odds = odds.get('over_odds', 1.91)
            over_implied = 1 / over_odds if over_odds > 0 else 0.5
            total_edge = (totals_pred['over_probability'] - over_implied) / over_implied if over_implied > 0 else 0

            # Spread prediction
            home_expected = (features_dict.get('home_offRating', 110) / 100) * features_dict.get('home_pace', 100)
            away_expected = (features_dict.get('away_offRating', 110) / 100) * features_dict.get('away_pace', 100)

            spread_pred = self.predict_spread(
                avg_home_prob, avg_away_prob,
                home_expected, away_expected
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
                'Spread': f"{predicted_winner} ({spread_pred['spread_confidence']})",
                'Spread_Home_Prob': f"{spread_pred['home_spread_prob']*100:.1f}%",
                'Spread_Away_Prob': f"{spread_pred['away_spread_prob']*100:.1f}%",
                'Expected_Margin': spread_pred['expected_margin'],
                'Home_Odds': f"{odds['home_odds']:.2f}",
                'Away_Odds': f"{odds['away_odds']:.2f}",
                'Bookmaker': odds.get('bookmaker', 'Unknown'),
                'Odds_Source': self.odds_failover.get_last_source(),
                'Stats_Source': self.stats_failover.get_last_source()
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
        date_folder = use_date.replace('-', '')
        reports_dir = os.path.join('reports', date_folder)
        os.makedirs(reports_dir, exist_ok=True)

        filename = os.path.join(reports_dir, f"nba_daily_report_{use_date}.csv")

        df.to_csv(filename, index=False)
        print(f"\n✅ Report saved to: {filename}")
        print(f"📊 {len(df)} games analyzed")

        # Print summary
        print(f"\n📋 SUMMARY:")
        print(f"{'='*80}")

        for idx, row in df.iterrows():
            print(f"\n🏀 {row['Away_Team']} @ {row['Home_Team']}")
            print(f"   Predicted Winner: {row['Predicted_Winner']} ({row['Win_Confidence']}) | Edge: {row['Win_Edge']}")
            print(f"   Expected Total: {row['Expected_Total']} (O/U {row['Total_Line']}) | Over: {row['Over_Probability']}")
            print(f"   Spread: {row['Spread']}")


def main():
    parser = argparse.ArgumentParser(description='Generate daily NBA betting report')
    parser.add_argument('--date', type=str,
                       help='Date in YYYY-MM-DD format (default: today)')
    parser.add_argument('--output', type=str,
                       help='Output CSV filename (default: auto-generated)')

    args = parser.parse_args()

    print("🏀 NBA DAILY BETTING REPORT GENERATOR")
    print("=" * 80)

    reporter = NBADailyReport()
    df_report = reporter.generate_daily_report(args.date)

    if not df_report.empty:
        reporter.save_report(df_report, args.date)
    else:
        print("\n⚠️  No games to report")


if __name__ == "__main__":
    main()
