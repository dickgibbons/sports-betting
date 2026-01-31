#!/usr/bin/env python3
"""
Daily NHL Goalie Saves Predictions Report
Generates predictions for expected saves for each goalie in today's games
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime
import pickle
import argparse
import sys


class GoalieSavesPredictor:
    """Predict goalie saves for upcoming games"""

    def __init__(self):
        self.nhl_base_url = "https://api-web.nhle.com/v1"

        # Load trained models
        try:
            strategies_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(strategies_dir, 'nhl_goalie_models.pkl')
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)

            self.models = model_data['models']
            self.scaler = model_data['scaler']
            self.feature_names = model_data['feature_names']

            print(f"✅ Loaded goalie models: {list(self.models.keys())}")
        except FileNotFoundError:
            print(f"❌ Goalie models not found. Run nhl_goalie_trainer.py first!")
            sys.exit(1)

    def get_upcoming_games(self, date_str: str = None) -> list:
        """Get upcoming NHL games from official NHL API"""
        # Default to today if no date provided
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')

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

                        for game in games:
                            game_state = game.get('gameState', 'UNKNOWN')

                            if game_state in ['FUT', 'LIVE', 'CRIT']:
                                all_games.append({
                                    'id': game.get('id'),
                                    'home_team': game.get('homeTeam', {}).get('abbrev', 'Unknown'),
                                    'away_team': game.get('awayTeam', {}).get('abbrev', 'Unknown'),
                                    'home_name': game.get('homeTeam', {}).get('placeName', {}).get('default', 'Unknown'),
                                    'away_name': game.get('awayTeam', {}).get('placeName', {}).get('default', 'Unknown'),
                                    'date': game.get('startTimeUTC', '')
                                })

                        return all_games

                return []
            return []
        except Exception as e:
            print(f"Error fetching games: {e}")
            return []

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
                        'team': team_abbrev,
                        'sweater': goalie.get('sweaterNumber', 0)
                    })

                return goalies
            return []
        except Exception as e:
            print(f"Error getting goalies for {team_abbrev}: {e}")
            return []

    def get_goalie_season_stats(self, goalie_id: int, season: str = "20242025") -> dict:
        """Get goalie's season statistics"""
        try:
            url = f"{self.nhl_base_url}/player/{goalie_id}/landing"
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()

                # Check if subSeason is a dict (current season) or list (historical)
                featured_stats = data.get('featuredStats', {})
                if featured_stats.get('season') == int(season):
                    # Current season - subSeason is a dict
                    sub_season = featured_stats.get('regularSeason', {}).get('subSeason', {})
                    if sub_season:
                        return {
                            'games_played': sub_season.get('gamesPlayed', 0),
                            'games_started': sub_season.get('gamesStarted', 0),
                            'wins': sub_season.get('wins', 0),
                            'losses': sub_season.get('losses', 0),
                            'saves': sub_season.get('saves', 0),
                            'shots_against': sub_season.get('shotsAgainst', 0),
                            'save_pct': sub_season.get('savePct', 0.900),
                            'gaa': sub_season.get('goalsAgainstAvg', 3.0),
                            'shutouts': sub_season.get('shutouts', 0)
                        }

                return None
            return None
        except Exception as e:
            return None

    def predict_goalie_saves(self, goalie: dict, season_stats: dict, is_home: bool,
                            opp_shots_estimate: float = 30.0) -> dict:
        """Predict saves for a single goalie"""
        if not season_stats or season_stats.get('games_played', 0) == 0:
            return None

        games_played = season_stats['games_played']
        total_saves = season_stats['saves']
        avg_saves_per_game = total_saves / games_played if games_played > 0 else 0

        # Assume this is a starter if they've started more than 50% of games played
        is_starter = season_stats.get('games_started', 0) > (games_played * 0.5)

        # Build features
        features = {
            'avg_saves_per_game': avg_saves_per_game,
            'season_save_pct': season_stats.get('save_pct', 0.900),
            'season_gaa': season_stats.get('gaa', 3.0),
            'games_played': games_played,
            'is_starter': 1 if is_starter else 0,
            'opp_shots_total': opp_shots_estimate,
            'opp_shooting_strength': opp_shots_estimate / 30.0,
            'is_home': 1 if is_home else 0
        }

        # Convert to array
        features_array = np.array([features[name] for name in self.feature_names])
        features_scaled = self.scaler.transform([features_array])

        # Average predictions from both models
        predictions = []
        for model_name, model in self.models.items():
            pred = model.predict(features_scaled)[0]
            predictions.append(max(0, pred))  # Don't predict negative saves

        avg_prediction = np.mean(predictions)

        # Calculate expected shots against and save percentage
        expected_shots_against = opp_shots_estimate
        expected_save_pct = avg_prediction / expected_shots_against if expected_shots_against > 0 else 0

        return {
            'predicted_saves': round(avg_prediction, 1),
            'expected_shots_against': round(expected_shots_against, 1),
            'predicted_save_pct': round(expected_save_pct, 3),
            'season_avg_saves': round(avg_saves_per_game, 1),
            'season_save_pct': season_stats.get('save_pct', 0.900),
            'is_likely_starter': is_starter,
            'confidence': 'High' if is_starter else 'Medium'
        }

    def generate_report(self, date_str: str = None) -> pd.DataFrame:
        """Generate goalie saves report for all games"""
        games = self.get_upcoming_games(date_str)

        if not games:
            print(f"⚠️  No games found for {date_str or 'today'}")
            return pd.DataFrame()

        print(f"📊 Generating goalie saves predictions for {len(games)} games...")

        report_data = []

        for game in games:
            print(f"\n🏒 {game['away_name']} @ {game['home_name']}")

            # Estimate opponent shooting
            # In real implementation, would calculate from team stats
            avg_shots = 30.0

            # Process both teams
            for team_type in ['home', 'away']:
                team_abbrev = game[f'{team_type}_team']
                team_name = game[f'{team_type}_name']
                is_home = (team_type == 'home')

                # Opponent shots estimate
                opp_shots = avg_shots

                print(f"   Loading {team_name} goalies...")
                goalies = self.get_team_goalies(team_abbrev)

                for goalie in goalies:
                    # Get season stats
                    stats = self.get_goalie_season_stats(goalie['id'])

                    if not stats or stats['games_played'] == 0:
                        continue

                    # Predict saves
                    prediction = self.predict_goalie_saves(goalie, stats, is_home, opp_shots)

                    if prediction:
                        report_data.append({
                            'Game': f"{game['away_name']} @ {game['home_name']}",
                            'Team': team_name,
                            'Goalie': goalie['name'],
                            'Number': goalie['sweater'],
                            'Likely_Starter': '✓' if prediction['is_likely_starter'] else '',
                            'Predicted_Saves': prediction['predicted_saves'],
                            'Expected_Shots_Against': prediction['expected_shots_against'],
                            'Predicted_Save_Pct': f"{prediction['predicted_save_pct']:.3f}",
                            'Season_Avg_Saves': prediction['season_avg_saves'],
                            'Season_Save_Pct': f"{prediction['season_save_pct']:.3f}",
                            'Games_Played': stats['games_played'],
                            'Season_GAA': stats.get('gaa', 0),
                            'Shutouts': stats.get('shutouts', 0),
                            'Confidence': prediction['confidence']
                        })

        df_report = pd.DataFrame(report_data)

        # Sort by likely starter first, then by predicted saves
        if not df_report.empty:
            df_report['starter_sort'] = df_report['Likely_Starter'].apply(lambda x: 0 if x == '✓' else 1)
            df_report = df_report.sort_values(['starter_sort', 'Predicted_Saves'], ascending=[True, False])
            df_report = df_report.drop('starter_sort', axis=1)

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
        import os
        date_folder = use_date.replace('-', '')  # Convert 2025-10-17 to 20251017
        reports_dir = os.path.join('reports', date_folder)
        os.makedirs(reports_dir, exist_ok=True)

        filename = os.path.join(reports_dir, f"goalie_saves_predictions_{use_date}.csv")

        df.to_csv(filename, index=False)
        print(f"\n✅ Report saved to: {filename}")
        print(f"📊 {len(df)} goalies analyzed")

        # Print likely starters
        starters = df[df['Likely_Starter'] == '✓']
        if not starters.empty:
            print(f"\n🥅 LIKELY STARTING GOALIES:")
            print("=" * 120)

            for idx, row in starters.iterrows():
                print(f"{row['Goalie']:25} ({row['Team']:15}) | "
                      f"Predicted Saves: {row['Predicted_Saves']:.1f} | "
                      f"Save %: {row['Predicted_Save_Pct']} | "
                      f"Season: {row['Season_Save_Pct']} ({row['Games_Played']} GP)")


def main():
    parser = argparse.ArgumentParser(description='Generate daily goalie saves predictions')
    parser.add_argument('--date', type=str,
                       help='Date in YYYY-MM-DD format (default: today)')

    args = parser.parse_args()

    print("🏒 NHL GOALIE SAVES PREDICTIONS")
    print("=" * 80)

    predictor = GoalieSavesPredictor()
    df_report = predictor.generate_report(args.date)

    if not df_report.empty:
        predictor.save_report(df_report, args.date)
    else:
        print("\n⚠️  No predictions generated")


if __name__ == "__main__":
    main()
