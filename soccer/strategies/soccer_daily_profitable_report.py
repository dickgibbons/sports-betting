#!/usr/bin/env python3
"""
Soccer Daily Profitable Angles Report

Shows EVERY game in profitable leagues with confidence percentages for each bet type.
Based on 7,272 match analysis (2023-2025 seasons).

Profitable Leagues: Bundesliga, Premier League, Eredivisie, MLS, La Liga, Serie A
Profitable Angles: Over 2.5, BTTS Yes, 1H Over 0.5
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import json

try:
    import requests
except ImportError:
    os.system("pip3 install requests")
    import requests

try:
    import pandas as pd
except ImportError:
    os.system("pip3 install pandas")
    import pandas as pd


# API-Football key (same as used in other soccer scripts)
DEFAULT_API_KEY = "960c628e1c91c4b1f125e1eec52ad862"


class SoccerDailyProfitableReport:
    """Generate daily report for all games in profitable leagues."""

    # Historical performance from 7,272 match analysis
    LEAGUE_STATS = {
        "Premier League": {
            "over_2_5": {"hit_rate": 0.607, "roi": 15.3},
            "btts_yes": {"hit_rate": 0.595, "roi": 10.0},
            "ht_over_0_5": {"hit_rate": 0.757, "roi": 9.7},
        },
        "Bundesliga": {
            "over_2_5": {"hit_rate": 0.613, "roi": 16.5},
            "btts_yes": {"hit_rate": 0.595, "roi": 10.1},
            "ht_over_0_5": {"hit_rate": 0.784, "roi": 13.6},
        },
        "Eredivisie": {
            "over_2_5": {"hit_rate": 0.598, "roi": 13.6},
            "btts_yes": {"hit_rate": 0.545, "roi": 0.8},
            "ht_over_0_5": {"hit_rate": 0.744, "roi": 7.9},
        },
        "MLS": {
            "over_2_5": {"hit_rate": 0.587, "roi": 11.4},
            "btts_yes": {"hit_rate": 0.593, "roi": 9.8},
            "ht_over_0_5": {"hit_rate": 0.710, "roi": 2.9},
        },
        "La Liga": {
            "over_2_5": {"hit_rate": 0.556, "roi": 5.2},
            "btts_yes": {"hit_rate": 0.530, "roi": -1.9},
            "ht_over_0_5": {"hit_rate": 0.698, "roi": 1.2},
        },
        "Serie A": {
            "over_2_5": {"hit_rate": 0.552, "roi": 4.8},
            "btts_yes": {"hit_rate": 0.540, "roi": -0.1},
            "ht_over_0_5": {"hit_rate": 0.705, "roi": 2.2},
        },
        "Ligue 1": {
            "over_2_5": {"hit_rate": 0.485, "roi": -7.8},
            "btts_yes": {"hit_rate": 0.502, "roi": -7.1},
            "ht_over_0_5": {"hit_rate": 0.680, "roi": -1.4},
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
        self.api_key = api_key or os.environ.get("API_FOOTBALL_KEY") or DEFAULT_API_KEY
        self.base_url = "https://v3.football.api-sports.io"

    def get_fixtures_for_date(self, date: str = None) -> List[Dict]:
        """Get all fixtures for the target date from profitable leagues."""
        date = date or datetime.now().strftime("%Y-%m-%d")
        all_fixtures = []

        if not self.api_key:
            print("⚠️  No API key found. Set API_FOOTBALL_KEY environment variable.")
            print("   Using demonstration data.\n")
            return self._get_demo_fixtures(date)

        print(f"Fetching fixtures for {date}...\n")

        for league_name, league_id in self.LEAGUE_IDS.items():
            if league_name not in self.LEAGUE_STATS:
                continue

            try:
                # Determine season based on date
                date_obj = datetime.strptime(date, "%Y-%m-%d")
                if league_name == "MLS":
                    season = date_obj.year
                else:
                    season = date_obj.year if date_obj.month >= 7 else date_obj.year - 1

                response = requests.get(
                    f"{self.base_url}/fixtures",
                    headers={"x-apisports-key": self.api_key},
                    params={"league": league_id, "date": date, "season": season},
                    timeout=10
                )
                data = response.json()

                if data.get("results", 0) > 0:
                    for fixture in data["response"]:
                        # Get team statistics for better predictions
                        home_stats = self._get_team_stats(
                            fixture["teams"]["home"]["id"], league_id, season
                        )
                        away_stats = self._get_team_stats(
                            fixture["teams"]["away"]["id"], league_id, season
                        )

                        all_fixtures.append({
                            "fixture_id": fixture["fixture"]["id"],
                            "date": fixture["fixture"]["date"],
                            "time": fixture["fixture"]["date"][11:16],
                            "league": league_name,
                            "league_id": league_id,
                            "home_team": fixture["teams"]["home"]["name"],
                            "away_team": fixture["teams"]["away"]["name"],
                            "home_id": fixture["teams"]["home"]["id"],
                            "away_id": fixture["teams"]["away"]["id"],
                            "home_stats": home_stats,
                            "away_stats": away_stats,
                            "venue": fixture["fixture"]["venue"]["name"] if fixture["fixture"].get("venue") else "TBD",
                        })

            except Exception as e:
                print(f"  Error fetching {league_name}: {e}")

        return all_fixtures

    def _get_team_stats(self, team_id: int, league_id: int, season: int) -> Dict:
        """Get team statistics for prediction features."""
        if not self.api_key:
            return self._get_default_stats()

        try:
            response = requests.get(
                f"{self.base_url}/teams/statistics",
                headers={"x-apisports-key": self.api_key},
                params={"team": team_id, "league": league_id, "season": season},
                timeout=10
            )
            data = response.json()

            if data.get("results", 0) > 0:
                stats = data["response"]
                goals = stats.get("goals", {})
                return {
                    "goals_for_avg": float(goals.get("for", {}).get("average", {}).get("total", 1.4) or 1.4),
                    "goals_against_avg": float(goals.get("against", {}).get("average", {}).get("total", 1.3) or 1.3),
                    "clean_sheets": stats.get("clean_sheet", {}).get("total", 5) or 5,
                    "failed_to_score": stats.get("failed_to_score", {}).get("total", 5) or 5,
                    "games_played": stats.get("fixtures", {}).get("played", {}).get("total", 20) or 20,
                }
        except Exception:
            pass

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

    def calculate_confidence(self, fixture: Dict) -> Dict:
        """Calculate confidence percentages for each bet type."""
        league = fixture["league"]
        league_stats = self.LEAGUE_STATS.get(league, {})
        home_stats = fixture.get("home_stats", self._get_default_stats())
        away_stats = fixture.get("away_stats", self._get_default_stats())

        confidences = {}

        # Over 2.5 Goals confidence
        if "over_2_5" in league_stats:
            base_rate = league_stats["over_2_5"]["hit_rate"]
            expected_goals = (
                home_stats["goals_for_avg"] + away_stats["goals_for_avg"]
            )

            # Adjust based on team scoring rates
            if expected_goals > 3.0:
                adjustment = 0.08
            elif expected_goals > 2.7:
                adjustment = 0.05
            elif expected_goals > 2.4:
                adjustment = 0.02
            elif expected_goals < 2.0:
                adjustment = -0.08
            elif expected_goals < 2.2:
                adjustment = -0.04
            else:
                adjustment = 0

            conf = min(0.80, max(0.40, base_rate + adjustment))
            confidences["over_2_5"] = {
                "confidence": round(conf * 100, 1),
                "historical_roi": league_stats["over_2_5"]["roi"],
                "expected_goals": round(expected_goals, 2),
                "recommended": conf >= 0.55 and league_stats["over_2_5"]["roi"] > 5,
            }

        # BTTS Yes confidence
        if "btts_yes" in league_stats:
            base_rate = league_stats["btts_yes"]["hit_rate"]

            # Probability each team scores
            home_fts_rate = home_stats["failed_to_score"] / max(1, home_stats["games_played"])
            away_fts_rate = away_stats["failed_to_score"] / max(1, away_stats["games_played"])

            home_scores_prob = 1 - home_fts_rate
            away_scores_prob = 1 - away_fts_rate

            # Clean sheet factor
            home_cs_rate = home_stats["clean_sheets"] / max(1, home_stats["games_played"])
            away_cs_rate = away_stats["clean_sheets"] / max(1, away_stats["games_played"])

            # Calculate BTTS probability
            btts_prob = home_scores_prob * away_scores_prob * (1 - (home_cs_rate + away_cs_rate) / 3)

            # Blend with historical rate
            conf = (btts_prob * 0.4 + base_rate * 0.6)
            conf = min(0.75, max(0.40, conf))

            confidences["btts_yes"] = {
                "confidence": round(conf * 100, 1),
                "historical_roi": league_stats["btts_yes"]["roi"],
                "home_scores_prob": round(home_scores_prob * 100, 1),
                "away_scores_prob": round(away_scores_prob * 100, 1),
                "recommended": conf >= 0.55 and league_stats["btts_yes"]["roi"] > 5,
            }

        # 1H Over 0.5 confidence
        if "ht_over_0_5" in league_stats:
            base_rate = league_stats["ht_over_0_5"]["hit_rate"]
            expected_goals = home_stats["goals_for_avg"] + away_stats["goals_for_avg"]

            if expected_goals > 3.0:
                adjustment = 0.06
            elif expected_goals > 2.5:
                adjustment = 0.03
            elif expected_goals < 2.0:
                adjustment = -0.06
            else:
                adjustment = 0

            conf = min(0.88, max(0.60, base_rate + adjustment))
            confidences["ht_over_0_5"] = {
                "confidence": round(conf * 100, 1),
                "historical_roi": league_stats["ht_over_0_5"]["roi"],
                "recommended": conf >= 0.70 and league_stats["ht_over_0_5"]["roi"] > 5,
            }

        return confidences

    def generate_report(self, date: str = None) -> str:
        """Generate the full daily report."""
        date = date or datetime.now().strftime("%Y-%m-%d")
        fixtures = self.get_fixtures_for_date(date)

        # Build report
        lines = []
        lines.append("=" * 80)
        lines.append(f"SOCCER PROFITABLE ANGLES DAILY REPORT - {date}")
        lines.append("=" * 80)
        lines.append("")
        lines.append("Based on 7,272 match analysis (2023-2025 seasons)")
        lines.append("Focus: Over 2.5, BTTS Yes, 1H Over 0.5 in high-scoring leagues")
        lines.append("")

        if not fixtures:
            lines.append("No fixtures found for today in profitable leagues.")
            lines.append("")
            lines.append("This could mean:")
            lines.append("  - No games scheduled today")
            lines.append("  - API key not configured (set API_FOOTBALL_KEY)")
            lines.append("  - League is in off-season")
            return "\n".join(lines)

        # Group by league
        fixtures_by_league = {}
        for f in fixtures:
            league = f["league"]
            if league not in fixtures_by_league:
                fixtures_by_league[league] = []
            fixtures_by_league[league].append(f)

        # Sort leagues by ROI potential
        league_order = ["Bundesliga", "Premier League", "Eredivisie", "MLS", "La Liga", "Serie A", "Ligue 1"]
        sorted_leagues = sorted(
            fixtures_by_league.keys(),
            key=lambda x: league_order.index(x) if x in league_order else 99
        )

        all_recommendations = []
        total_games = 0

        for league in sorted_leagues:
            league_fixtures = fixtures_by_league[league]
            league_stats = self.LEAGUE_STATS.get(league, {})

            lines.append("-" * 80)
            lines.append(f"📊 {league.upper()}")
            if "over_2_5" in league_stats:
                lines.append(f"   Historical: Over 2.5 hits {league_stats['over_2_5']['hit_rate']*100:.1f}% (ROI +{league_stats['over_2_5']['roi']}%)")
            lines.append("-" * 80)
            lines.append("")

            for fixture in league_fixtures:
                total_games += 1
                confidences = self.calculate_confidence(fixture)

                lines.append(f"⚽ {fixture['home_team']} vs {fixture['away_team']}")
                lines.append(f"   Time: {fixture['time']} | Venue: {fixture.get('venue', 'TBD')}")
                lines.append("")

                # Display each bet type with confidence
                lines.append("   BET TYPE          | CONFIDENCE | HISTORICAL ROI | RECOMMEND")
                lines.append("   " + "-" * 60)

                for bet_type, data in confidences.items():
                    bet_name = {
                        "over_2_5": "Over 2.5 Goals",
                        "btts_yes": "BTTS Yes",
                        "ht_over_0_5": "1H Over 0.5"
                    }.get(bet_type, bet_type)

                    recommend = "✅ YES" if data["recommended"] else "   ---"
                    roi_str = f"+{data['historical_roi']}%" if data['historical_roi'] > 0 else f"{data['historical_roi']}%"

                    lines.append(
                        f"   {bet_name:17} | {data['confidence']:5.1f}%     | {roi_str:14} | {recommend}"
                    )

                    if data["recommended"]:
                        all_recommendations.append({
                            "league": league,
                            "match": f"{fixture['home_team']} vs {fixture['away_team']}",
                            "time": fixture["time"],
                            "bet": bet_name,
                            "confidence": data["confidence"],
                            "roi": data["historical_roi"],
                        })

                # Add extra details
                if "over_2_5" in confidences:
                    lines.append(f"   └─ Expected Total Goals: {confidences['over_2_5'].get('expected_goals', 'N/A')}")
                if "btts_yes" in confidences:
                    lines.append(f"   └─ Home Scores: {confidences['btts_yes'].get('home_scores_prob', 'N/A')}% | Away Scores: {confidences['btts_yes'].get('away_scores_prob', 'N/A')}%")

                lines.append("")

        # Summary section
        lines.append("=" * 80)
        lines.append("📋 SUMMARY")
        lines.append("=" * 80)
        lines.append(f"Total Games Analyzed: {total_games}")
        lines.append(f"Total Recommendations: {len(all_recommendations)}")
        lines.append("")

        if all_recommendations:
            lines.append("🎯 RECOMMENDED BETS (Confidence ≥55% & Historical ROI >5%):")
            lines.append("")

            # Sort by confidence
            all_recommendations.sort(key=lambda x: x["confidence"], reverse=True)

            for i, rec in enumerate(all_recommendations, 1):
                lines.append(f"  {i}. {rec['league']} - {rec['match']}")
                lines.append(f"     BET: {rec['bet']} @ {rec['confidence']}% confidence")
                lines.append(f"     Historical ROI: +{rec['roi']}%")
                lines.append("")

        lines.append("=" * 80)
        lines.append("⚠️  REMINDER: Only bet on angles with historical ROI > 5%")
        lines.append("   AVOID: BTTS No (-17% ROI), Over 3.5 (-40% ROI), 1H Over 1.5 (-24% ROI)")
        lines.append("=" * 80)

        return "\n".join(lines)

    def _get_demo_fixtures(self, date: str) -> List[Dict]:
        """Demo fixtures when no API key available."""
        return [
            {
                "fixture_id": 1,
                "date": date,
                "time": "15:00",
                "league": "Premier League",
                "league_id": 39,
                "home_team": "Arsenal",
                "away_team": "Chelsea",
                "home_id": 42,
                "away_id": 49,
                "home_stats": {"goals_for_avg": 2.1, "goals_against_avg": 0.9, "clean_sheets": 8, "failed_to_score": 3, "games_played": 20},
                "away_stats": {"goals_for_avg": 1.8, "goals_against_avg": 1.1, "clean_sheets": 5, "failed_to_score": 4, "games_played": 20},
                "venue": "Emirates Stadium",
            },
            {
                "fixture_id": 2,
                "date": date,
                "time": "15:30",
                "league": "Bundesliga",
                "league_id": 78,
                "home_team": "Bayern Munich",
                "away_team": "Borussia Dortmund",
                "home_id": 157,
                "away_id": 165,
                "home_stats": {"goals_for_avg": 2.5, "goals_against_avg": 1.0, "clean_sheets": 7, "failed_to_score": 2, "games_played": 18},
                "away_stats": {"goals_for_avg": 2.0, "goals_against_avg": 1.3, "clean_sheets": 4, "failed_to_score": 3, "games_played": 18},
                "venue": "Allianz Arena",
            },
            {
                "fixture_id": 3,
                "date": date,
                "time": "14:30",
                "league": "Bundesliga",
                "league_id": 78,
                "home_team": "RB Leipzig",
                "away_team": "Bayer Leverkusen",
                "home_id": 173,
                "away_id": 168,
                "home_stats": {"goals_for_avg": 1.9, "goals_against_avg": 1.2, "clean_sheets": 5, "failed_to_score": 4, "games_played": 18},
                "away_stats": {"goals_for_avg": 2.2, "goals_against_avg": 0.8, "clean_sheets": 9, "failed_to_score": 2, "games_played": 18},
                "venue": "Red Bull Arena",
            },
            {
                "fixture_id": 4,
                "date": date,
                "time": "20:00",
                "league": "MLS",
                "league_id": 253,
                "home_team": "LA Galaxy",
                "away_team": "LAFC",
                "home_id": 1600,
                "away_id": 1599,
                "home_stats": {"goals_for_avg": 1.7, "goals_against_avg": 1.4, "clean_sheets": 4, "failed_to_score": 5, "games_played": 22},
                "away_stats": {"goals_for_avg": 1.9, "goals_against_avg": 1.2, "clean_sheets": 6, "failed_to_score": 4, "games_played": 22},
                "venue": "Dignity Health Sports Park",
            },
        ]

    def save_report(self, date: str = None):
        """Generate and save the report."""
        date = date or datetime.now().strftime("%Y-%m-%d")
        report = self.generate_report(date)

        # Print to console
        print(report)

        # Save to files
        report_dir = Path("/Users/dickgibbons/AI Projects/sports-betting/reports") / date
        report_dir.mkdir(parents=True, exist_ok=True)

        # Text report
        report_path = report_dir / f"soccer_profitable_angles_{date}.txt"
        with open(report_path, "w") as f:
            f.write(report)

        # Also save to Daily Reports
        daily_dir = Path("/Users/dickgibbons/AI Projects/sports-betting/Daily Reports") / date
        daily_dir.mkdir(parents=True, exist_ok=True)
        daily_path = daily_dir / f"soccer_profitable_angles_{date}.txt"
        with open(daily_path, "w") as f:
            f.write(report)

        print(f"\n✅ Report saved to:")
        print(f"   {report_path}")
        print(f"   {daily_path}")

        return report


def main():
    """Run the daily report."""
    import argparse
    parser = argparse.ArgumentParser(description="Soccer Daily Profitable Angles Report")
    parser.add_argument("--date", type=str, help="Date to generate report for (YYYY-MM-DD)")
    args = parser.parse_args()

    reporter = SoccerDailyProfitableReport()
    reporter.save_report(args.date)


if __name__ == "__main__":
    main()
