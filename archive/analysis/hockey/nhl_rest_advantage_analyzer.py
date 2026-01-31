#!/usr/bin/env python3
"""
NHL Rest Advantage Analyzer

Identifies betting opportunities based on rest disparities between teams.
Research shows betting the more rested team has been profitable:
- 2023-24: 347-277 (+13.96 units, +2.2% ROI)
- Home teams on B2B: 58-61 (-10% ROI)
- Overs hit 57% when home team is tired underdog

Sources:
- VSiN NHL Scheduling Scenarios
- ESPN NHL Betting Tips
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import json


class NHLRestAdvantageAnalyzer:
    """Analyze rest advantages for NHL betting"""

    def __init__(self):
        self.nhl_api = "https://api-web.nhle.com/v1"
        self.schedule_cache = {}
        self.team_last_game = {}
        print("NHL Rest Advantage Analyzer initialized")

    def get_schedule_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Fetch NHL schedule for date range"""
        all_games = []
        current = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            games = self._get_games_for_date(date_str)
            all_games.extend(games)
            current += timedelta(days=1)

        return all_games

    def _get_games_for_date(self, date_str: str) -> List[Dict]:
        """Get games for a specific date"""
        if date_str in self.schedule_cache:
            return self.schedule_cache[date_str]

        url = f"{self.nhl_api}/schedule/{date_str}"
        try:
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                return []

            data = response.json()
            games = []

            for day in data.get("gameWeek", []):
                if day.get("date") == date_str:
                    for game in day.get("games", []):
                        games.append({
                            "game_id": game.get("id"),
                            "date": date_str,
                            "time": game.get("startTimeUTC", ""),
                            "home_team": game.get("homeTeam", {}).get("abbrev", ""),
                            "away_team": game.get("awayTeam", {}).get("abbrev", ""),
                            "home_name": game.get("homeTeam", {}).get("placeName", {}).get("default", ""),
                            "away_name": game.get("awayTeam", {}).get("placeName", {}).get("default", ""),
                            "game_state": game.get("gameState", ""),
                        })

            self.schedule_cache[date_str] = games
            return games

        except Exception as e:
            print(f"Error fetching schedule for {date_str}: {e}")
            return []

    def build_team_schedule_history(self, through_date: str, lookback_days: int = 30):
        """Build schedule history to determine rest days"""
        end_date = datetime.strptime(through_date, "%Y-%m-%d")
        start_date = end_date - timedelta(days=lookback_days)

        games = self.get_schedule_range(
            start_date.strftime("%Y-%m-%d"),
            through_date
        )

        # Build last game date for each team
        team_games = defaultdict(list)
        for game in games:
            game_date = game["date"]
            team_games[game["home_team"]].append(game_date)
            team_games[game["away_team"]].append(game_date)

        # Sort and store
        for team, dates in team_games.items():
            dates.sort()
            self.team_last_game[team] = dates

    def get_days_rest(self, team: str, game_date: str) -> int:
        """Get number of days rest for a team before a game"""
        if team not in self.team_last_game:
            return 99  # Unknown, assume well-rested

        game_dt = datetime.strptime(game_date, "%Y-%m-%d")

        # Find most recent game before this date
        for prev_date in reversed(self.team_last_game[team]):
            prev_dt = datetime.strptime(prev_date, "%Y-%m-%d")
            if prev_dt < game_dt:
                return (game_dt - prev_dt).days - 1  # Days between games, not including game days

        return 99  # No previous game found

    def is_back_to_back(self, team: str, game_date: str) -> bool:
        """Check if team is playing back-to-back"""
        return self.get_days_rest(team, game_date) == 0

    def analyze_today(self, date: str = None) -> Dict:
        """Analyze today's games for rest advantages"""
        date = date or datetime.now().strftime("%Y-%m-%d")

        # Build schedule history
        self.build_team_schedule_history(date, lookback_days=10)

        # Get today's games
        games = self._get_games_for_date(date)

        analysis = {
            "date": date,
            "games": [],
            "best_bets": []
        }

        for game in games:
            home = game["home_team"]
            away = game["away_team"]

            home_rest = self.get_days_rest(home, date)
            away_rest = self.get_days_rest(away, date)

            home_b2b = self.is_back_to_back(home, date)
            away_b2b = self.is_back_to_back(away, date)

            rest_advantage = home_rest - away_rest

            game_analysis = {
                "matchup": f"{away} @ {home}",
                "home_team": home,
                "away_team": away,
                "home_rest_days": home_rest,
                "away_rest_days": away_rest,
                "home_b2b": home_b2b,
                "away_b2b": away_b2b,
                "rest_advantage": rest_advantage,  # Positive = home more rested
                "rest_advantage_team": home if rest_advantage > 0 else (away if rest_advantage < 0 else "Even"),
                "signals": []
            }

            # Generate betting signals based on research
            signals = []

            # Signal 1: Home team on B2B - FADE them (moneyline or puck line)
            if home_b2b and not away_b2b:
                signals.append({
                    "type": "FADE_HOME_B2B",
                    "bet": f"{away} ML or +1.5",
                    "reasoning": "Home teams on B2B went 58-61 (-10% ROI) in 2023-24",
                    "confidence": "HIGH"
                })
                # Also signal game total OVER if home is underdog
                signals.append({
                    "type": "B2B_HOME_OVER",
                    "bet": "Game OVER",
                    "reasoning": "Overs hit 57% when home underdog on B2B (vs 47% normally)",
                    "confidence": "MEDIUM"
                })

            # Signal 2: Away team on B2B, home is rested - Bet HOME
            if away_b2b and not home_b2b:
                signals.append({
                    "type": "REST_ADVANTAGE_HOME",
                    "bet": f"{home} ML",
                    "reasoning": "More rested team: 347-277 (+2.2% ROI) in 2023-24",
                    "confidence": "HIGH"
                })

            # Signal 3: Significant rest disparity (3+ days difference)
            if abs(rest_advantage) >= 3:
                rested_team = home if rest_advantage > 0 else away
                tired_team = away if rest_advantage > 0 else home
                signals.append({
                    "type": "REST_DISPARITY",
                    "bet": f"{rested_team} ML",
                    "reasoning": f"{rested_team} has {abs(rest_advantage)} more days rest than {tired_team}",
                    "confidence": "MEDIUM"
                })

            game_analysis["signals"] = signals
            analysis["games"].append(game_analysis)

            # Add to best bets if there are signals
            for signal in signals:
                if signal["confidence"] == "HIGH":
                    analysis["best_bets"].append({
                        "matchup": game_analysis["matchup"],
                        "bet": signal["bet"],
                        "type": signal["type"],
                        "reasoning": signal["reasoning"]
                    })

        return analysis

    def generate_report(self, date: str = None) -> str:
        """Generate formatted report"""
        analysis = self.analyze_today(date)

        lines = []
        lines.append("=" * 80)
        lines.append(f"NHL REST ADVANTAGE REPORT - {analysis['date']}")
        lines.append("=" * 80)
        lines.append("")
        lines.append("Based on 2023-24 data:")
        lines.append("  - More rested team: 347-277 (+13.96 units, +2.2% ROI)")
        lines.append("  - Home teams on B2B: 58-61 (-10% ROI)")
        lines.append("  - Overs when home underdog on B2B: 57% hit rate")
        lines.append("")
        lines.append("-" * 80)

        if not analysis["games"]:
            lines.append("No games scheduled for this date.")
            return "\n".join(lines)

        # Best Bets Section
        if analysis["best_bets"]:
            lines.append("")
            lines.append("⭐ BEST BETS (HIGH CONFIDENCE)")
            lines.append("-" * 40)
            for i, bet in enumerate(analysis["best_bets"], 1):
                lines.append(f"{i}. {bet['matchup']}")
                lines.append(f"   BET: {bet['bet']}")
                lines.append(f"   WHY: {bet['reasoning']}")
                lines.append("")

        # All Games Analysis
        lines.append("")
        lines.append("📊 ALL GAMES ANALYSIS")
        lines.append("-" * 80)

        for game in analysis["games"]:
            lines.append("")
            lines.append(f"🏒 {game['matchup']}")
            lines.append(f"   {game['away_team']}: {game['away_rest_days']} days rest {'(B2B)' if game['away_b2b'] else ''}")
            lines.append(f"   {game['home_team']}: {game['home_rest_days']} days rest {'(B2B)' if game['home_b2b'] else ''}")

            if game["rest_advantage"] != 0:
                adv_team = game["rest_advantage_team"]
                adv_days = abs(game["rest_advantage"])
                lines.append(f"   ➡️  {adv_team} has {adv_days} day(s) rest advantage")
            else:
                lines.append(f"   ➡️  Even rest")

            if game["signals"]:
                lines.append(f"   📌 SIGNALS:")
                for signal in game["signals"]:
                    lines.append(f"      [{signal['confidence']}] {signal['bet']}")
                    lines.append(f"         {signal['reasoning']}")

        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)

    def save_report(self, date: str = None):
        """Generate and save report"""
        date = date or datetime.now().strftime("%Y-%m-%d")
        report = self.generate_report(date)
        print(report)

        # Save to Daily Reports
        from pathlib import Path
        daily_dir = Path(f"/Users/dickgibbons/Daily Reports/{date}")
        daily_dir.mkdir(parents=True, exist_ok=True)

        report_path = daily_dir / f"nhl_rest_advantage_{date}.txt"
        with open(report_path, "w") as f:
            f.write(report)

        # Also save JSON for programmatic use
        analysis = self.analyze_today(date)
        json_path = daily_dir / f"nhl_rest_advantage_{date}.json"
        with open(json_path, "w") as f:
            json.dump(analysis, f, indent=2)

        print(f"\n✅ Reports saved:")
        print(f"   {report_path}")
        print(f"   {json_path}")

        return analysis


def main():
    import argparse
    parser = argparse.ArgumentParser(description="NHL Rest Advantage Analyzer")
    parser.add_argument("--date", type=str, help="Date to analyze (YYYY-MM-DD)")
    args = parser.parse_args()

    analyzer = NHLRestAdvantageAnalyzer()
    analyzer.save_report(args.date)


if __name__ == "__main__":
    main()
