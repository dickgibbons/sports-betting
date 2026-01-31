#!/usr/bin/env python3
"""
Daily NHL Player Shots Predictions Report
Generates predictions for expected shots on goal for each player in today's games
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime
import pickle
import argparse
import sys


class PlayerShotsPredictor:
    """Predict player shots for upcoming games"""

    def __init__(self):
        self.nhl_base_url = "https://api-web.nhle.com/v1"

        # Load trained models
        try:
            strategies_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(strategies_dir, 'nhl_player_models.pkl')
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)

            self.models = model_data['models']
            self.scaler = model_data['scaler']
            self.feature_names = model_data['feature_names']

            print(f"✅ Loaded player models: {list(self.models.keys())}")
        except FileNotFoundError:
            print(f"❌ Player models not found. Run nhl_player_trainer.py first!")
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

    def get_team_roster(self, team_abbrev: str, season: int = 2024) -> list:
        """Get team roster with player IDs"""
        try:
            url = f"{self.nhl_base_url}/roster/{team_abbrev}/{season}{season+1}"
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                players = []

                for position in ['forwards', 'defensemen']:
                    for player in data.get(position, []):
                        players.append({
                            'id': player.get('id'),
                            'name': player.get('firstName', {}).get('default', '') + ' ' +
                                   player.get('lastName', {}).get('default', ''),
                            'position': player.get('positionCode', ''),
                            'team': team_abbrev,
                            'sweater': player.get('sweaterNumber', 0)
                        })

                return players
            return []
        except Exception as e:
            print(f"Error getting roster for {team_abbrev}: {e}")
            return []

    def get_player_season_stats(self, player_id: int, season: str = "20242025") -> dict:
        """Get player's season statistics"""
        try:
            url = f"{self.nhl_base_url}/player/{player_id}/landing"
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
                            'goals': sub_season.get('goals', 0),
                            'assists': sub_season.get('assists', 0),
                            'points': sub_season.get('points', 0),
                            'shots': sub_season.get('shots', 0),
                            'avg_toi': sub_season.get('avgToi', '0:00')
                        }

                return None
            return None
        except Exception as e:
            return None

    def predict_player_shots(self, player: dict, season_stats: dict, is_home: bool) -> dict:
        """Predict shots for a single player"""
        if not season_stats or season_stats.get('games_played', 0) == 0:
            return None

        games_played = season_stats['games_played']
        total_shots = season_stats['shots']
        avg_shots_per_game = total_shots / games_played if games_played > 0 else 0

        # Estimate TOI based on position and role
        position = player['position']
        if position in ['C', 'LW', 'RW']:
            est_toi = 16.0  # Average forward TOI
        else:
            est_toi = 18.0  # Average defense TOI

        # Build features
        features = {
            'position_C': 1 if position == 'C' else 0,
            'position_LW': 1 if position == 'LW' else 0,
            'position_RW': 1 if position == 'RW' else 0,
            'position_D': 1 if position == 'D' else 0,
            'avg_shots_per_game': avg_shots_per_game,
            'season_shooting_pct': (season_stats['goals'] / total_shots * 100) if total_shots > 0 else 0,
            'season_points_per_game': season_stats['points'] / games_played if games_played > 0 else 0,
            'toi_minutes': est_toi,
            'is_home': 1 if is_home else 0,
            'opp_team_strength': 0.5
        }

        # Convert to array
        features_array = np.array([features[name] for name in self.feature_names])
        features_scaled = self.scaler.transform([features_array])

        # Average predictions from both models
        predictions = []
        for model_name, model in self.models.items():
            pred = model.predict(features_scaled)[0]
            predictions.append(max(0, pred))  # Don't predict negative shots

        avg_prediction = np.mean(predictions)

        # Determine if predicting over or under season average
        diff = avg_prediction - avg_shots_per_game
        diff_pct = (diff / avg_shots_per_game * 100) if avg_shots_per_game > 0 else 0

        # Clear projection indicator
        if abs(diff_pct) < 5:  # Within 5% = "Even"
            projection = f"EVEN {round(avg_prediction, 1)}"
        elif diff > 0:
            projection = f"OVER {round(avg_shots_per_game, 1)} (+{round(diff, 1)})"
        else:
            projection = f"UNDER {round(avg_shots_per_game, 1)} ({round(diff, 1)})"

        return {
            'predicted_shots': round(avg_prediction, 1),
            'season_avg': round(avg_shots_per_game, 1),
            'diff': round(diff, 1),
            'projection': projection,
            'confidence': 'High' if avg_shots_per_game > 2.0 else 'Medium' if avg_shots_per_game > 1.0 else 'Low'
        }

    def generate_report(self, date_str: str = None) -> pd.DataFrame:
        """Generate player shots report for all games"""
        games = self.get_upcoming_games(date_str)

        if not games:
            print(f"⚠️  No games found for {date_str or 'today'}")
            return pd.DataFrame()

        print(f"📊 Generating player shots predictions for {len(games)} games...")

        report_data = []

        for game in games:
            print(f"\n🏒 {game['away_name']} @ {game['home_name']}")

            # Process both teams
            for team_type in ['home', 'away']:
                team_abbrev = game[f'{team_type}_team']
                team_name = game[f'{team_type}_name']
                is_home = (team_type == 'home')

                print(f"   Loading {team_name} roster...")
                roster = self.get_team_roster(team_abbrev)

                for player in roster:
                    # Get season stats
                    stats = self.get_player_season_stats(player['id'])

                    if not stats or stats['games_played'] == 0:
                        continue

                    # Predict shots
                    prediction = self.predict_player_shots(player, stats, is_home)

                    if prediction:
                        report_data.append({
                            'Game': f"{game['away_name']} @ {game['home_name']}",
                            'Team': team_name,
                            'Player': player['name'],
                            'Position': player['position'],
                            'Number': player['sweater'],
                            'Predicted_Shots': prediction['predicted_shots'],
                            'Season_Avg_Shots': prediction['season_avg'],
                            'Diff': prediction['diff'],
                            'Projection': prediction['projection'],
                            'Games_Played': stats['games_played'],
                            'Season_Goals': stats['goals'],
                            'Season_Points': stats['points'],
                            'Confidence': prediction['confidence']
                        })

        df_report = pd.DataFrame(report_data)

        # Sort by predicted shots
        if not df_report.empty:
            df_report = df_report.sort_values('Predicted_Shots', ascending=False)

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

        filename = os.path.join(reports_dir, f"player_shots_predictions_{use_date}.csv")

        df.to_csv(filename, index=False)
        print(f"\n✅ Report saved to: {filename}")
        print(f"📊 {len(df)} players analyzed")

        # Print top predictions
        print(f"\n🎯 TOP 10 PREDICTED SHOTS:")
        print("=" * 100)

        for idx, row in df.head(10).iterrows():
            print(f"{row['Player']:25} ({row['Team']:15}) | "
                  f"Predicted: {row['Predicted_Shots']:.1f} | "
                  f"Season Avg: {row['Season_Avg_Shots']:.1f} | "
                  f"Position: {row['Position']}")


def main():
    parser = argparse.ArgumentParser(description='Generate daily player shots predictions')
    parser.add_argument('--date', type=str,
                       help='Date in YYYY-MM-DD format (default: today)')

    args = parser.parse_args()

    print("🏒 NHL PLAYER SHOTS PREDICTIONS")
    print("=" * 80)

    predictor = PlayerShotsPredictor()
    df_report = predictor.generate_report(args.date)

    if not df_report.empty:
        predictor.save_report(df_report, args.date)
    else:
        print("\n⚠️  No predictions generated")


if __name__ == "__main__":
    main()
