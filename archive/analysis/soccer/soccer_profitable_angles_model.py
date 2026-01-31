#!/usr/bin/env python3
"""
Soccer Profitable Angles Model

Based on investigation of 7,272 matches (2023-2025), this model focuses on
the statistically profitable betting angles:

TOP ANGLES:
1. Over 2.5 Goals in: Bundesliga (+16.5%), Premier League (+15.3%),
   Eredivisie (+13.6%), MLS (+11.4%)
2. BTTS Yes in: Bundesliga (+10.1%), Premier League (+10.0%), MLS (+9.8%)
3. HT Over 0.5 in: Bundesliga (+13.6%), Premier League (+9.7%), Eredivisie (+7.9%)

AVOID:
- BTTS No (ROI -17.3%)
- Over 3.5 (ROI -39.5%)
- Moneylines (mostly negative)
"""

import os
import sys
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

# Add parent paths
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import requests
except ImportError:
    print("Installing requests...")
    os.system("pip3 install requests")
    import requests


class ProfitableAnglesModel:
    """
    Model that targets statistically profitable soccer betting angles.
    Based on 2-year historical analysis of 7,272 matches.
    """

    # Profitable league-angle combinations from investigation
    PROFITABLE_ANGLES = {
        "Premier League": {
            "over_2_5": {"roi": 15.3, "hit_rate": 0.607, "threshold": 0.55},
            "btts_yes": {"roi": 10.0, "hit_rate": 0.595, "threshold": 0.55},
            "ht_over_0_5": {"roi": 9.7, "hit_rate": 0.757, "threshold": 0.70},
        },
        "Bundesliga": {
            "over_2_5": {"roi": 16.5, "hit_rate": 0.613, "threshold": 0.55},
            "btts_yes": {"roi": 10.1, "hit_rate": 0.595, "threshold": 0.55},
            "ht_over_0_5": {"roi": 13.6, "hit_rate": 0.784, "threshold": 0.70},
        },
        "Eredivisie": {
            "over_2_5": {"roi": 13.6, "hit_rate": 0.598, "threshold": 0.55},
            "ht_over_0_5": {"roi": 7.9, "hit_rate": 0.744, "threshold": 0.70},
        },
        "MLS": {
            "over_2_5": {"roi": 11.4, "hit_rate": 0.587, "threshold": 0.55},
            "btts_yes": {"roi": 9.8, "hit_rate": 0.593, "threshold": 0.55},
        },
        "La Liga": {
            "over_2_5": {"roi": 5.2, "hit_rate": 0.556, "threshold": 0.55},
        },
        "Serie A": {
            "over_2_5": {"roi": 4.8, "hit_rate": 0.552, "threshold": 0.55},
        },
    }

    # API-Football league IDs
    LEAGUE_IDS = {
        "Premier League": 39,
        "La Liga": 140,
        "Serie A": 135,
        "Bundesliga": 78,
        "Ligue 1": 61,
        "Eredivisie": 88,
        "MLS": 253,
    }

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("API_FOOTBALL_KEY")
        self.base_url = "https://v3.football.api-sports.io"
        self.db_path = Path(__file__).parent / "soccer_investigation.db"

    def get_todays_fixtures(self, date: str = None) -> List[Dict]:
        """Get today's fixtures from API-Football."""
        if not self.api_key:
            print("Warning: No API key. Using cached/mock data.")
            return self._get_mock_fixtures()

        date = date or datetime.now().strftime("%Y-%m-%d")

        fixtures = []
        for league_name, league_id in self.LEAGUE_IDS.items():
            if league_name not in self.PROFITABLE_ANGLES:
                continue

            try:
                response = requests.get(
                    f"{self.base_url}/fixtures",
                    headers={"x-apisports-key": self.api_key},
                    params={"league": league_id, "date": date, "season": 2024}
                )
                data = response.json()

                if data.get("results", 0) > 0:
                    for fixture in data["response"]:
                        fixtures.append({
                            "fixture_id": fixture["fixture"]["id"],
                            "date": fixture["fixture"]["date"],
                            "league": league_name,
                            "league_id": league_id,
                            "home_team": fixture["teams"]["home"]["name"],
                            "away_team": fixture["teams"]["away"]["name"],
                            "home_id": fixture["teams"]["home"]["id"],
                            "away_id": fixture["teams"]["away"]["id"],
                        })
            except Exception as e:
                print(f"Error fetching {league_name}: {e}")

        return fixtures

    def get_team_stats(self, team_id: int, league_id: int) -> Dict:
        """Get team statistics for prediction features."""
        if not self.api_key:
            return self._get_default_stats()

        try:
            response = requests.get(
                f"{self.base_url}/teams/statistics",
                headers={"x-apisports-key": self.api_key},
                params={"team": team_id, "league": league_id, "season": 2024}
            )
            data = response.json()

            if data.get("results", 0) > 0:
                stats = data["response"]
                return {
                    "goals_for_avg": stats["goals"]["for"]["average"]["total"],
                    "goals_against_avg": stats["goals"]["against"]["average"]["total"],
                    "clean_sheets": stats["clean_sheet"]["total"],
                    "failed_to_score": stats["failed_to_score"]["total"],
                    "games_played": stats["fixtures"]["played"]["total"],
                }
        except Exception as e:
            print(f"Error fetching team stats: {e}")

        return self._get_default_stats()

    def _get_default_stats(self) -> Dict:
        """Default stats when API unavailable."""
        return {
            "goals_for_avg": 1.4,
            "goals_against_avg": 1.3,
            "clean_sheets": 5,
            "failed_to_score": 5,
            "games_played": 20,
        }

    def predict_over_2_5(self, home_stats: Dict, away_stats: Dict) -> float:
        """Predict probability of Over 2.5 goals."""
        # Combined expected goals
        expected_goals = (
            home_stats["goals_for_avg"] +
            away_stats["goals_for_avg"] +
            home_stats["goals_against_avg"] * 0.3 +
            away_stats["goals_against_avg"] * 0.3
        ) / 2

        # Simple probability model based on expected goals
        # Poisson approximation: P(X > 2.5) when mean = expected_goals
        import math
        prob = 1 - sum(
            (expected_goals ** k) * math.exp(-expected_goals) / math.factorial(k)
            for k in range(3)
        )

        # Adjust for historical hit rates
        # If expected goals > 2.7, historical shows ~65% hit rate
        if expected_goals > 2.8:
            prob = max(prob, 0.60)
        elif expected_goals > 2.5:
            prob = max(prob, 0.55)

        return min(0.75, max(0.35, prob))

    def predict_btts(self, home_stats: Dict, away_stats: Dict) -> float:
        """Predict probability of Both Teams To Score."""
        # Probability each team scores
        home_scores_prob = 1 - (home_stats.get("failed_to_score", 5) /
                                max(1, home_stats.get("games_played", 20)))
        away_scores_prob = 1 - (away_stats.get("failed_to_score", 5) /
                                max(1, away_stats.get("games_played", 20)))

        # Clean sheet factor
        home_cs_rate = home_stats.get("clean_sheets", 5) / max(1, home_stats.get("games_played", 20))
        away_cs_rate = away_stats.get("clean_sheets", 5) / max(1, away_stats.get("games_played", 20))

        # BTTS = both teams score
        btts_prob = home_scores_prob * away_scores_prob * (1 - (home_cs_rate + away_cs_rate) / 4)

        return min(0.75, max(0.35, btts_prob))

    def predict_ht_over_0_5(self, home_stats: Dict, away_stats: Dict) -> float:
        """Predict probability of First Half Over 0.5 goals."""
        # Most games have a first half goal (~72% historical)
        base_prob = 0.72

        # Adjust based on scoring rates
        total_scoring = home_stats["goals_for_avg"] + away_stats["goals_for_avg"]

        if total_scoring > 3.0:
            prob = base_prob + 0.08
        elif total_scoring > 2.5:
            prob = base_prob + 0.04
        elif total_scoring < 2.0:
            prob = base_prob - 0.08
        else:
            prob = base_prob

        return min(0.85, max(0.60, prob))

    def generate_predictions(self, fixtures: List[Dict] = None) -> pd.DataFrame:
        """Generate predictions for fixtures."""
        if fixtures is None:
            fixtures = self.get_todays_fixtures()

        predictions = []

        for fixture in fixtures:
            league = fixture["league"]

            if league not in self.PROFITABLE_ANGLES:
                continue

            # Get team stats
            home_stats = self.get_team_stats(fixture["home_id"], fixture["league_id"])
            away_stats = self.get_team_stats(fixture["away_id"], fixture["league_id"])

            # Check each profitable angle for this league
            angles = self.PROFITABLE_ANGLES[league]

            for angle, params in angles.items():
                threshold = params["threshold"]
                historical_roi = params["roi"]

                # Calculate prediction
                if angle == "over_2_5":
                    prob = self.predict_over_2_5(home_stats, away_stats)
                elif angle == "btts_yes":
                    prob = self.predict_btts(home_stats, away_stats)
                elif angle == "ht_over_0_5":
                    prob = self.predict_ht_over_0_5(home_stats, away_stats)
                else:
                    continue

                # Only recommend if above threshold
                if prob >= threshold:
                    confidence = "HIGH" if prob >= threshold + 0.10 else "MEDIUM"

                    predictions.append({
                        "date": fixture["date"][:10],
                        "league": league,
                        "match": f"{fixture['home_team']} vs {fixture['away_team']}",
                        "home_team": fixture["home_team"],
                        "away_team": fixture["away_team"],
                        "bet_type": self._format_angle(angle),
                        "probability": round(prob * 100, 1),
                        "confidence": confidence,
                        "historical_roi": f"+{historical_roi}%",
                        "edge": round((prob - 0.526) * 100, 1),  # Edge vs -110 odds
                    })

        df = pd.DataFrame(predictions)
        if not df.empty:
            df = df.sort_values(["confidence", "edge"], ascending=[True, False])

        return df

    def _format_angle(self, angle: str) -> str:
        """Format angle name for display."""
        formats = {
            "over_2_5": "Over 2.5 Goals",
            "btts_yes": "BTTS Yes",
            "ht_over_0_5": "1H Over 0.5 Goals",
        }
        return formats.get(angle, angle)

    def _get_mock_fixtures(self) -> List[Dict]:
        """Return sample fixtures for testing without API."""
        return [
            {
                "fixture_id": 1,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "league": "Premier League",
                "league_id": 39,
                "home_team": "Arsenal",
                "away_team": "Chelsea",
                "home_id": 42,
                "away_id": 49,
            },
            {
                "fixture_id": 2,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "league": "Bundesliga",
                "league_id": 78,
                "home_team": "Bayern Munich",
                "away_team": "Dortmund",
                "home_id": 157,
                "away_id": 165,
            },
        ]

    def print_analysis_summary(self):
        """Print summary of profitable angles from investigation."""
        print("\n" + "=" * 70)
        print("SOCCER PROFITABLE ANGLES - INVESTIGATION SUMMARY")
        print("=" * 70)
        print(f"\nBased on analysis of 7,272 matches (2023-2025 seasons)")
        print("\n📈 TOP PROFITABLE ANGLES:\n")

        all_angles = []
        for league, angles in self.PROFITABLE_ANGLES.items():
            for angle, data in angles.items():
                all_angles.append({
                    "league": league,
                    "angle": self._format_angle(angle),
                    "roi": data["roi"],
                    "hit_rate": data["hit_rate"] * 100,
                })

        df = pd.DataFrame(all_angles)
        df = df.sort_values("roi", ascending=False)

        for _, row in df.iterrows():
            print(f"  {row['league']:20} | {row['angle']:18} | "
                  f"ROI: +{row['roi']:5.1f}% | Hit Rate: {row['hit_rate']:.1f}%")

        print("\n⛔ ANGLES TO AVOID:")
        print("  - BTTS No: ROI -17.3%")
        print("  - Over 3.5 Goals: ROI -39.5%")
        print("  - Most Moneylines: Negative ROI")
        print("  - First Half Over 1.5: ROI -24.2%")
        print("\n" + "=" * 70)


def main():
    """Run the profitable angles model."""
    print("\n" + "=" * 70)
    print("SOCCER PROFITABLE ANGLES MODEL")
    print("=" * 70)

    model = ProfitableAnglesModel()

    # Print analysis summary
    model.print_analysis_summary()

    # Generate predictions
    print("\n📊 TODAY'S PREDICTIONS:\n")
    predictions = model.generate_predictions()

    if predictions.empty:
        print("No high-confidence predictions for today's matches.")
        print("(This may be due to no API key or no matches in profitable leagues)")
    else:
        # Display predictions
        for _, pred in predictions.iterrows():
            print(f"\n{pred['league']} - {pred['match']}")
            print(f"  BET: {pred['bet_type']}")
            print(f"  Probability: {pred['probability']}%")
            print(f"  Confidence: {pred['confidence']}")
            print(f"  Historical ROI: {pred['historical_roi']}")
            print(f"  Edge: +{pred['edge']}%")

    # Save predictions
    date_str = datetime.now().strftime("%Y-%m-%d")
    report_dir = Path("/Users/dickgibbons/sports-betting/reports") / date_str
    report_dir.mkdir(parents=True, exist_ok=True)

    if not predictions.empty:
        predictions.to_csv(report_dir / f"soccer_profitable_angles_{date_str}.csv", index=False)

        # Text report
        with open(report_dir / f"soccer_profitable_angles_{date_str}.txt", "w") as f:
            f.write(f"SOCCER PROFITABLE ANGLES - {date_str}\n")
            f.write("=" * 60 + "\n\n")
            f.write("Based on 7,272 match analysis (2023-2025)\n")
            f.write("Focus: Leagues/angles with ROI > 5%\n\n")
            f.write("-" * 60 + "\n\n")

            for _, pred in predictions.iterrows():
                f.write(f"MATCH: {pred['match']}\n")
                f.write(f"League: {pred['league']}\n")
                f.write(f"BET: {pred['bet_type']}\n")
                f.write(f"Probability: {pred['probability']}%\n")
                f.write(f"Confidence: {pred['confidence']}\n")
                f.write(f"Historical ROI: {pred['historical_roi']}\n")
                f.write(f"Edge: +{pred['edge']}%\n")
                f.write("\n")

            f.write("-" * 60 + "\n")
            f.write(f"Total Recommendations: {len(predictions)}\n")

        print(f"\n✅ Predictions saved to: {report_dir}")

    return predictions


if __name__ == "__main__":
    main()
