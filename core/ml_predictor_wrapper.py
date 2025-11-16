#!/usr/bin/env python3
"""
ML Predictor Wrapper
Interfaces with the NBA-Machine-Learning-Sports-Betting system
to get ML predictions for today's NBA games
"""

import sys
import os
import subprocess
import re
from typing import Dict, List, Optional
from datetime import datetime

class MLPredictorWrapper:
    """Wrapper for the ML prediction system"""

    def __init__(self, ml_repo_path: str = None):
        """Initialize ML predictor wrapper"""
        if ml_repo_path is None:
            ml_repo_path = os.path.expanduser('~/sports-betting/nba/ml_system')

        self.ml_repo_path = ml_repo_path
        self.predictions = {}

        if not os.path.exists(ml_repo_path):
            print(f"⚠️  ML repo not found at {ml_repo_path}")
            print("   ML predictions will not be available")
            self.available = False
        else:
            self.available = True
            print("🤖 ML Predictor initialized")

    def get_predictions(self, date: str = None) -> Dict:
        """
        Get ML predictions for today's games

        Returns dict like:
        {
            'Milwaukee Bucks:Charlotte Hornets': {
                'home_team': 'Milwaukee Bucks',
                'away_team': 'Charlotte Hornets',
                'predicted_winner': 'Milwaukee Bucks',  # or away_team
                'ml_confidence': 65.3,  # percentage
                'predicted_total': 'OVER',  # or 'UNDER'
                'uo_confidence': 58.2  # percentage
            }
        }
        """

        if not self.available:
            return {}

        try:
            # Run the ML prediction script
            cmd = [
                'python3', 'main.py',
                '-xgb',  # Use XGBoost (68.7% accuracy)
                '-odds', 'fanduel'  # Fetch odds
            ]

            result = subprocess.run(
                cmd,
                cwd=self.ml_repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            # Parse the output
            predictions = self._parse_ml_output(result.stdout)

            return predictions

        except subprocess.TimeoutExpired:
            print("   ⚠️  ML prediction timeout")
            return {}
        except Exception as e:
            print(f"   ⚠️  ML prediction error: {e}")
            return {}

    def _parse_ml_output(self, output: str) -> Dict:
        """Parse ML prediction output"""
        predictions = {}

        lines = output.split('\n')

        # FIRST PASS: Parse Expected Value section
        ev_section = False
        ev_values = {}

        for line in lines:
            # Check if we're in the Expected Value section
            if 'Expected Value' in line:
                ev_section = True
                continue
            if ev_section and '---' in line:
                ev_section = False
                break  # We're done with EV section

            # Parse EV lines (format: "Team Name EV: 12.34")
            if ev_section and 'EV:' in line:
                try:
                    parts = line.split('EV:')
                    if len(parts) == 2:
                        team = parts[0].strip()
                        ev = float(parts[1].strip())
                        ev_values[team] = ev
                except Exception as e:
                    pass

        # SECOND PASS: Parse predictions and match with EV values
        for line in lines:
            # Skip non-prediction lines
            if 'vs' not in line or '(' not in line:
                continue

            # Extract teams and confidences
            # This is a simplified parser - may need refinement based on actual output
            try:
                # Try to extract team names and confidences
                # Format varies, but generally: WINNER (conf%) vs LOSER: prediction
                parts = line.split('vs')
                if len(parts) != 2:
                    continue

                left_part = parts[0].strip()
                right_part = parts[1].strip()

                # Extract confidence from first team (winner)
                conf_match = re.search(r'\((\d+\.?\d*)%\)', left_part)
                if conf_match:
                    ml_confidence = float(conf_match.group(1))
                    home_team = re.sub(r'\([^)]*\)', '', left_part).strip()
                    home_team = home_team.replace('\x1b[32m', '').replace('\x1b[0m', '').replace('\x1b[36m', '').strip()
                else:
                    # Confidence might be on second team
                    conf_match = re.search(r'\((\d+\.?\d*)%\)', right_part)
                    if not conf_match:
                        continue
                    ml_confidence = float(conf_match.group(1))

                # Extract away team
                away_parts = right_part.split(':')
                if len(away_parts) > 0:
                    away_team = away_parts[0].strip()
                    away_team = re.sub(r'\([^)]*\)', '', away_team).strip()
                    away_team = away_team.replace('\x1b[31m', '').replace('\x1b[0m', '').strip()

                # Determine predicted winner (team with GREEN color code or higher position)
                if '\x1b[32m' in parts[0] or '(confidence%)' in left_part:
                    predicted_winner = home_team
                else:
                    predicted_winner = away_team

                # Extract over/under prediction
                predicted_total = 'UNKNOWN'
                uo_confidence = 50.0

                if 'OVER' in line:
                    predicted_total = 'OVER'
                    uo_match = re.search(r'OVER[^(]*\((\d+\.?\d*)%\)', line)
                    if uo_match:
                        uo_confidence = float(uo_match.group(1))
                elif 'UNDER' in line:
                    predicted_total = 'UNDER'
                    uo_match = re.search(r'UNDER[^(]*\((\d+\.?\d*)%\)', line)
                    if uo_match:
                        uo_confidence = float(uo_match.group(1))

                # Create prediction entry
                game_key = f"{away_team}:{home_team}"

                # Get EV for both teams (if available)
                home_ev = ev_values.get(home_team, 0.0)
                away_ev = ev_values.get(away_team, 0.0)

                predictions[game_key] = {
                    'home_team': home_team,
                    'away_team': away_team,
                    'predicted_winner': predicted_winner,
                    'ml_confidence': ml_confidence,
                    'predicted_total': predicted_total,
                    'uo_confidence': uo_confidence,
                    'home_ev': home_ev,
                    'away_ev': away_ev,
                    'predicted_ev': home_ev if predicted_winner == home_team else away_ev
                }

            except Exception as e:
                # Skip malformed lines
                continue

        return predictions

    def get_prediction_for_game(self, home_team: str, away_team: str) -> Optional[Dict]:
        """Get ML prediction for a specific game"""
        if not self.predictions:
            self.predictions = self.get_predictions()

        # Try different key formats
        keys = [
            f"{away_team}:{home_team}",
            f"{home_team}:{away_team}",
            f"{away_team} @ {home_team}"
        ]

        for key in keys:
            if key in self.predictions:
                return self.predictions[key]

        # Try fuzzy matching (team names might differ slightly)
        for game_key, prediction in self.predictions.items():
            if (home_team in prediction['home_team'] or prediction['home_team'] in home_team) and \
               (away_team in prediction['away_team'] or prediction['away_team'] in away_team):
                return prediction

        return None


if __name__ == "__main__":
    # Test the wrapper
    ml = MLPredictorWrapper()
    predictions = ml.get_predictions()

    print("\n🤖 ML PREDICTIONS")
    print("="*80)

    for game, pred in predictions.items():
        print(f"\n{pred['away_team']} @ {pred['home_team']}")
        print(f"   Winner: {pred['predicted_winner']} ({pred['ml_confidence']}% confidence)")
        print(f"   Total: {pred['predicted_total']} ({pred['uo_confidence']}% confidence)")
