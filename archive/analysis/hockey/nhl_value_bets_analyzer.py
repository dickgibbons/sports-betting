#!/usr/bin/env python3
"""
NHL Value Bets Analyzer

Focuses on finding +EV betting opportunities with PLUS ODDS:
1. 1P Under 0.5 (team shutout in 1P) - teams with low 1P scoring rates
2. 1P Total Under 1.5 - defensive matchups
3. Game Total Under/Over - based on matchup trends
4. 1P Moneyline Dogs - underdogs with strong 1P history

AVOIDS: Heavy favorites with juiced odds (the current losing strategy)
"""

import requests
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    os.system("pip3 install pandas")
    import pandas as pd

try:
    import numpy as np
except ImportError:
    os.system("pip3 install numpy")
    import numpy as np


class NHLValueBetsAnalyzer:
    """Find value betting opportunities in NHL games"""

    def __init__(self):
        self.nhl_api_base = "https://api-web.nhle.com/v1"
        self.team_stats_cache = {}
        print("🎯 NHL Value Bets Analyzer initialized")
        print("   Focus: PLUS ODDS opportunities, avoiding heavy juice")

    def get_todays_games(self, date: str = None) -> List[Dict]:
        """Fetch today's NHL schedule"""
        date = date or datetime.now().strftime("%Y-%m-%d")
        url = f"{self.nhl_api_base}/schedule/{date}"

        try:
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                return []

            data = response.json()
            games = []

            for day in data.get("gameWeek", []):
                if day.get("date") == date:
                    for game in day.get("games", []):
                        games.append({
                            "game_id": game.get("id"),
                            "home_team": game.get("homeTeam", {}).get("abbrev", ""),
                            "away_team": game.get("awayTeam", {}).get("abbrev", ""),
                            "venue": game.get("venue", {}).get("default", ""),
                        })
                    break

            return games
        except Exception as e:
            print(f"Error fetching schedule: {e}")
            return []

    def get_team_season_stats(self, team_abbrev: str, season: str = "20252026") -> Dict:
        """Get comprehensive 1P and game stats for a team"""
        if team_abbrev in self.team_stats_cache:
            return self.team_stats_cache[team_abbrev]

        # Fetch team's game log
        url = f"{self.nhl_api_base}/club-schedule-season/{team_abbrev}/{season}"

        try:
            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                return {}

            data = response.json()
            games = data.get("games", [])

            # Filter to completed games only
            completed = [g for g in games if g.get("gameState") == "OFF"]

            if len(completed) < 5:
                return {}

            # Calculate stats
            stats = {
                "games_played": len(completed),
                "p1_goals_for": [],
                "p1_goals_against": [],
                "p1_totals": [],
                "game_totals": [],
                "wins": 0,
                "home_p1_totals": [],
                "away_p1_totals": [],
            }

            for game in completed[-30:]:  # Last 30 games
                game_id = game.get("id")
                is_home = game.get("homeTeam", {}).get("abbrev") == team_abbrev

                # Get period scores from game details
                p1_for, p1_against, game_total = self._get_period_scores(game_id, team_abbrev)

                if p1_for is not None:
                    stats["p1_goals_for"].append(p1_for)
                    stats["p1_goals_against"].append(p1_against)
                    stats["p1_totals"].append(p1_for + p1_against)

                    if is_home:
                        stats["home_p1_totals"].append(p1_for + p1_against)
                    else:
                        stats["away_p1_totals"].append(p1_for + p1_against)

                if game_total is not None:
                    stats["game_totals"].append(game_total)

                # Track wins
                outcome = game.get("gameOutcome", {}).get("lastPeriodType", "")
                if outcome:
                    home_score = game.get("homeTeam", {}).get("score", 0)
                    away_score = game.get("awayTeam", {}).get("score", 0)
                    if is_home and home_score > away_score:
                        stats["wins"] += 1
                    elif not is_home and away_score > home_score:
                        stats["wins"] += 1

            # Calculate percentages
            if stats["p1_goals_for"]:
                stats["p1_scoring_rate"] = sum(1 for g in stats["p1_goals_for"] if g > 0) / len(stats["p1_goals_for"])
                stats["p1_shutout_rate"] = sum(1 for g in stats["p1_goals_for"] if g == 0) / len(stats["p1_goals_for"])
                stats["p1_avg_for"] = np.mean(stats["p1_goals_for"])
                stats["p1_avg_against"] = np.mean(stats["p1_goals_against"])
                stats["p1_avg_total"] = np.mean(stats["p1_totals"])
                stats["p1_over_1_5_rate"] = sum(1 for t in stats["p1_totals"] if t > 1.5) / len(stats["p1_totals"])
                stats["p1_under_1_5_rate"] = sum(1 for t in stats["p1_totals"] if t <= 1.5) / len(stats["p1_totals"])

            if stats["game_totals"]:
                stats["game_avg_total"] = np.mean(stats["game_totals"])
                stats["game_over_5_5_rate"] = sum(1 for t in stats["game_totals"] if t > 5.5) / len(stats["game_totals"])
                stats["game_under_5_5_rate"] = sum(1 for t in stats["game_totals"] if t <= 5.5) / len(stats["game_totals"])

            self.team_stats_cache[team_abbrev] = stats
            return stats

        except Exception as e:
            print(f"Error fetching stats for {team_abbrev}: {e}")
            return {}

    def _get_period_scores(self, game_id: int, team_abbrev: str) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        """Get period-by-period scores for a game using play-by-play endpoint"""
        url = f"{self.nhl_api_base}/gamecenter/{game_id}/play-by-play"

        try:
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                return None, None, None

            data = response.json()

            home_team_info = data.get("homeTeam", {})
            away_team_info = data.get("awayTeam", {})
            home_id = home_team_info.get("id")
            home_abbrev = home_team_info.get("abbrev", "")

            is_home = home_abbrev == team_abbrev

            # Count 1P goals from plays
            plays = data.get("plays", [])
            p1_home = 0
            p1_away = 0

            for play in plays:
                period = play.get("periodDescriptor", {}).get("number")
                if period == 1 and play.get("typeDescKey") == "goal":
                    team_id = play.get("details", {}).get("eventOwnerTeamId")
                    if team_id == home_id:
                        p1_home += 1
                    else:
                        p1_away += 1

            if is_home:
                p1_for = p1_home
                p1_against = p1_away
            else:
                p1_for = p1_away
                p1_against = p1_home

            # Game total from final scores
            game_total = home_team_info.get("score", 0) + away_team_info.get("score", 0)

            return p1_for, p1_against, game_total

        except:
            return None, None, None

    def find_1p_under_opportunities(self, games: List[Dict]) -> List[Dict]:
        """Find teams likely to be shut out in 1P (good for Under 0.5)"""
        opportunities = []

        for game in games:
            home = game["home_team"]
            away = game["away_team"]

            home_stats = self.get_team_season_stats(home)
            away_stats = self.get_team_season_stats(away)

            if not home_stats or not away_stats:
                continue

            # Check if home team has high shutout rate (good for HOME Under 0.5)
            if home_stats.get("p1_shutout_rate", 0) >= 0.30:  # 30%+ shutout rate in 1P
                opp_allowed = away_stats.get("p1_avg_against", 1)
                if opp_allowed <= 0.85:  # Opponent allows <0.85 goals in 1P
                    opportunities.append({
                        "game": f"{away} @ {home}",
                        "bet": f"{home} Under 0.5 Goals (1P)",
                        "type": "1P Under 0.5",
                        "rationale": f"{home} blanked in 1P {home_stats['p1_shutout_rate']*100:.0f}% of games, {away} allows only {opp_allowed:.2f} 1P goals",
                        "confidence": home_stats["p1_shutout_rate"],
                        "approx_odds": "+130",
                        "needed_win_rate": "43%"
                    })

            # Check if away team has high shutout rate
            if away_stats.get("p1_shutout_rate", 0) >= 0.30:
                opp_allowed = home_stats.get("p1_avg_against", 1)
                if opp_allowed <= 0.85:
                    opportunities.append({
                        "game": f"{away} @ {home}",
                        "bet": f"{away} Under 0.5 Goals (1P)",
                        "type": "1P Under 0.5",
                        "rationale": f"{away} blanked in 1P {away_stats['p1_shutout_rate']*100:.0f}% of games, {home} allows only {opp_allowed:.2f} 1P goals",
                        "confidence": away_stats["p1_shutout_rate"],
                        "approx_odds": "+130",
                        "needed_win_rate": "43%"
                    })

        return sorted(opportunities, key=lambda x: x["confidence"], reverse=True)

    def find_1p_total_under_opportunities(self, games: List[Dict]) -> List[Dict]:
        """Find matchups likely to have 0-1 goals in 1P"""
        opportunities = []

        for game in games:
            home = game["home_team"]
            away = game["away_team"]

            home_stats = self.get_team_season_stats(home)
            away_stats = self.get_team_season_stats(away)

            if not home_stats or not away_stats:
                continue

            # Both teams have low 1P totals
            home_under = home_stats.get("p1_under_1_5_rate", 0)
            away_under = away_stats.get("p1_under_1_5_rate", 0)

            if home_under >= 0.50 and away_under >= 0.50:  # Both 50%+ under 1.5 rate
                combined_rate = (home_under + away_under) / 2
                avg_1p_total = (home_stats.get("p1_avg_total", 2) + away_stats.get("p1_avg_total", 2)) / 2

                if avg_1p_total <= 1.5:  # Combined avg 1P total under 1.5
                    opportunities.append({
                        "game": f"{away} @ {home}",
                        "bet": "1P Total Under 1.5",
                        "type": "1P Total Under",
                        "rationale": f"Combined 1P avg: {avg_1p_total:.2f} goals. {home} U1.5 rate: {home_under*100:.0f}%, {away}: {away_under*100:.0f}%",
                        "confidence": combined_rate,
                        "approx_odds": "+110",
                        "needed_win_rate": "48%"
                    })

        return sorted(opportunities, key=lambda x: x["confidence"], reverse=True)

    def find_game_total_opportunities(self, games: List[Dict]) -> List[Dict]:
        """Find game total over/under opportunities"""
        opportunities = []

        for game in games:
            home = game["home_team"]
            away = game["away_team"]

            home_stats = self.get_team_season_stats(home)
            away_stats = self.get_team_season_stats(away)

            if not home_stats or not away_stats:
                continue

            home_avg = home_stats.get("game_avg_total", 6)
            away_avg = away_stats.get("game_avg_total", 6)
            combined_avg = (home_avg + away_avg) / 2

            # Strong Under candidates
            home_under = home_stats.get("game_under_5_5_rate", 0)
            away_under = away_stats.get("game_under_5_5_rate", 0)

            if home_under >= 0.55 and away_under >= 0.55 and combined_avg <= 5.5:
                opportunities.append({
                    "game": f"{away} @ {home}",
                    "bet": "Game Total Under 5.5",
                    "type": "Game Under",
                    "rationale": f"Combined avg: {combined_avg:.1f} goals. {home} U5.5: {home_under*100:.0f}%, {away}: {away_under*100:.0f}%",
                    "confidence": (home_under + away_under) / 2,
                    "approx_odds": "-110",
                    "needed_win_rate": "52.4%"
                })

            # Strong Over candidates
            home_over = home_stats.get("game_over_5_5_rate", 0)
            away_over = away_stats.get("game_over_5_5_rate", 0)

            if home_over >= 0.55 and away_over >= 0.55 and combined_avg >= 6.0:
                opportunities.append({
                    "game": f"{away} @ {home}",
                    "bet": "Game Total Over 5.5",
                    "type": "Game Over",
                    "rationale": f"Combined avg: {combined_avg:.1f} goals. {home} O5.5: {home_over*100:.0f}%, {away}: {away_over*100:.0f}%",
                    "confidence": (home_over + away_over) / 2,
                    "approx_odds": "-110",
                    "needed_win_rate": "52.4%"
                })

        return sorted(opportunities, key=lambda x: x["confidence"], reverse=True)

    def find_1p_ml_dog_opportunities(self, games: List[Dict]) -> List[Dict]:
        """Find underdog 1P ML opportunities - teams with high 1P scoring rates

        Concept: 1P ML underdogs typically pay +140 to +200 (need 33-42% to profit)
        If a team scores in 1P 50%+ of the time, betting their 1P ML as underdog has value
        """
        opportunities = []

        for game in games:
            home = game["home_team"]
            away = game["away_team"]

            home_stats = self.get_team_season_stats(home)
            away_stats = self.get_team_season_stats(away)

            if not home_stats or not away_stats:
                continue

            # Team scoring rates in 1P (probability of scoring at least 1 goal)
            home_scoring_rate = home_stats.get("p1_scoring_rate", 0)
            away_scoring_rate = away_stats.get("p1_scoring_rate", 0)

            # Away team as potential underdog - scores 55%+ in 1P
            # At +150 odds (40% implied), 55% actual = +15% edge
            if away_scoring_rate >= 0.55:
                opp_defense = home_stats.get("p1_avg_against", 1)  # What home allows
                if opp_defense >= 0.8:  # Home allows decent goals in 1P
                    opportunities.append({
                        "game": f"{away} @ {home}",
                        "bet": f"{away} 1P ML (if underdog)",
                        "type": "1P ML Dog",
                        "rationale": f"{away} scores in 1P {away_scoring_rate*100:.0f}% of games, {home} allows {opp_defense:.2f} 1P goals/game",
                        "confidence": away_scoring_rate,
                        "approx_odds": "+150",
                        "needed_win_rate": "40%",
                        "actual_rate": f"{away_scoring_rate*100:.0f}%"
                    })

            # Home team as potential underdog - scores 55%+ in 1P
            if home_scoring_rate >= 0.55:
                opp_defense = away_stats.get("p1_avg_against", 1)  # What away allows
                if opp_defense >= 0.8:  # Away allows decent goals in 1P
                    opportunities.append({
                        "game": f"{away} @ {home}",
                        "bet": f"{home} 1P ML (if underdog)",
                        "type": "1P ML Dog",
                        "rationale": f"{home} scores in 1P {home_scoring_rate*100:.0f}% of games, {away} allows {opp_defense:.2f} 1P goals/game",
                        "confidence": home_scoring_rate,
                        "approx_odds": "+150",
                        "needed_win_rate": "40%",
                        "actual_rate": f"{home_scoring_rate*100:.0f}%"
                    })

        return sorted(opportunities, key=lambda x: x["confidence"], reverse=True)

    def generate_daily_report(self, date: str = None) -> str:
        """Generate a value bets report for today's games"""
        date = date or datetime.now().strftime("%Y-%m-%d")
        games = self.get_todays_games(date)

        if not games:
            return f"No games found for {date}"

        print(f"\n🔍 Analyzing {len(games)} games for {date}...")

        # Find all opportunities
        under_05 = self.find_1p_under_opportunities(games)
        under_15 = self.find_1p_total_under_opportunities(games)
        game_totals = self.find_game_total_opportunities(games)
        ml_dogs = self.find_1p_ml_dog_opportunities(games)

        # Build report
        lines = []
        lines.append("=" * 70)
        lines.append("🎯 NHL VALUE BETS REPORT - PLUS ODDS FOCUS")
        lines.append(f"   Date: {date}")
        lines.append(f"   Games: {len(games)}")
        lines.append("=" * 70)
        lines.append("")
        lines.append("STRATEGY: Avoid heavy favorites. Focus on plus-odds opportunities")
        lines.append("          that only require 43-52% hit rate to profit.")
        lines.append("")

        # 1P Under 0.5 (Team)
        lines.append("-" * 70)
        lines.append("🥅 1P TEAM UNDER 0.5 (Shutout in 1P) - Approx +130 odds (need 43%)")
        lines.append("-" * 70)
        if under_05:
            for opp in under_05[:5]:
                lines.append(f"  {opp['game']}")
                lines.append(f"    BET: {opp['bet']}")
                lines.append(f"    Why: {opp['rationale']}")
                lines.append(f"    Confidence: {opp['confidence']*100:.0f}%")
                lines.append("")
        else:
            lines.append("  No strong opportunities found")
            lines.append("")

        # 1P Total Under 1.5
        lines.append("-" * 70)
        lines.append("⬇️ 1P TOTAL UNDER 1.5 - Approx +110 odds (need 48%)")
        lines.append("-" * 70)
        if under_15:
            for opp in under_15[:5]:
                lines.append(f"  {opp['game']}")
                lines.append(f"    BET: {opp['bet']}")
                lines.append(f"    Why: {opp['rationale']}")
                lines.append(f"    Confidence: {opp['confidence']*100:.0f}%")
                lines.append("")
        else:
            lines.append("  No strong opportunities found")
            lines.append("")

        # Game Totals
        lines.append("-" * 70)
        lines.append("📊 GAME TOTALS - Standard -110 odds (need 52.4%)")
        lines.append("-" * 70)
        if game_totals:
            for opp in game_totals[:5]:
                lines.append(f"  {opp['game']}")
                lines.append(f"    BET: {opp['bet']}")
                lines.append(f"    Why: {opp['rationale']}")
                lines.append(f"    Confidence: {opp['confidence']*100:.0f}%")
                lines.append("")
        else:
            lines.append("  No strong opportunities found")
            lines.append("")

        # 1P ML Dogs
        lines.append("-" * 70)
        lines.append("🐕 1P MONEYLINE DOGS - Plus odds ~+150 (need 40%)")
        lines.append("-" * 70)
        lines.append("  NOTE: Only bet if team is actually underdog on 1P ML")
        lines.append("")
        if ml_dogs:
            for opp in ml_dogs[:5]:
                lines.append(f"  {opp['game']}")
                lines.append(f"    BET: {opp['bet']}")
                lines.append(f"    Why: {opp['rationale']}")
                lines.append(f"    Actual 1P scoring rate: {opp['actual_rate']}")
                lines.append("")
        else:
            lines.append("  No strong opportunities found")
            lines.append("")

        # Summary
        total_opps = len(under_05) + len(under_15) + len(game_totals) + len(ml_dogs)
        lines.append("=" * 70)
        lines.append(f"TOTAL OPPORTUNITIES: {total_opps}")
        lines.append("")
        lines.append("REMINDER: These bets have LOWER juice than Team Over 0.5 (1P)")
        lines.append("          You need ~48% hit rate to profit, NOT 61%!")
        lines.append("=" * 70)

        report = "\n".join(lines)

        # Save to file
        report_dir = Path("/Users/dickgibbons/AI Projects/sports-betting/Daily Reports") / date
        report_dir.mkdir(parents=True, exist_ok=True)
        report_file = report_dir / "NHL_VALUE_BETS.txt"
        with open(report_file, "w") as f:
            f.write(report)

        print(f"\n📄 Report saved to: {report_file}")

        return report


def main():
    import sys

    date = sys.argv[1] if len(sys.argv) > 1 else None

    analyzer = NHLValueBetsAnalyzer()
    report = analyzer.generate_daily_report(date)
    print(report)


if __name__ == "__main__":
    main()
