#!/usr/bin/env python3
"""
NHL Daily Matchup Moving Average Report

Shows today's games with side-by-side moving average comparisons for both teams.
Helps identify betting opportunities based on recent trends.
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
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
except ImportError:
    os.system("pip3 install matplotlib")
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec

try:
    import numpy as np
except ImportError:
    os.system("pip3 install numpy")
    import numpy as np

# Import the MA analyzer
from nhl_goals_moving_average import NHLGoalsMovingAverage


class NHLDailyMatchupMAReport:
    """Generate daily matchup report with moving average comparisons"""

    def __init__(self, use_cache: bool = True):
        self.nhl_api_base = "https://api-web.nhle.com/v1"
        self.ma_analyzer = NHLGoalsMovingAverage(use_cache=use_cache)
        self.team_data_cache = {}  # In-memory cache for this session
        cache_status = "(with SQLite cache)" if use_cache else ""
        print(f"🏒 NHL Daily Matchup MA Report initialized {cache_status}")

    def get_todays_games(self, date: str = None) -> List[Dict]:
        """Fetch today's NHL schedule"""
        date = date or datetime.now().strftime("%Y-%m-%d")
        url = f"{self.nhl_api_base}/schedule/{date}"

        try:
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                print(f"Error fetching schedule: {response.status_code}")
                return []

            data = response.json()
            games = []

            for day in data.get("gameWeek", []):
                if day.get("date") == date:
                    for game in day.get("games", []):
                        games.append({
                            "game_id": game.get("id"),
                            "time": game.get("startTimeUTC", "")[:19],
                            "home_team": game.get("homeTeam", {}).get("abbrev", ""),
                            "away_team": game.get("awayTeam", {}).get("abbrev", ""),
                            "home_name": game.get("homeTeam", {}).get("placeName", {}).get("default", ""),
                            "away_name": game.get("awayTeam", {}).get("placeName", {}).get("default", ""),
                            "venue": game.get("venue", {}).get("default", ""),
                            "game_state": game.get("gameState", ""),
                        })
                    break

            return games

        except Exception as e:
            print(f"Error fetching schedule: {e}")
            return []

    def get_team_ma_data(self, team_abbrev: str, season: str = "20242025") -> Optional[pd.DataFrame]:
        """Get or fetch team MA data (with caching)"""
        if team_abbrev in self.team_data_cache:
            return self.team_data_cache[team_abbrev]

        df = self.ma_analyzer.collect_team_data(team_abbrev, season)
        if not df.empty:
            # Calculate all MAs
            for metric in ["goals_for", "goals_against", "total_goals",
                          "period_1_for", "period_1_total"]:
                df = self.ma_analyzer.calculate_moving_averages(df, metric)
            self.team_data_cache[team_abbrev] = df

        return df if not df.empty else None

    def get_team_current_mas(self, df: pd.DataFrame) -> Dict:
        """Extract current MA values from team data"""
        if df is None or df.empty:
            return {}

        latest = df.iloc[-1]
        return {
            "games_played": len(df),
            "gf_last": latest["goals_for"],
            "gf_ma3": latest["goals_for_ma3"],
            "gf_ma5": latest["goals_for_ma5"],
            "gf_ma10": latest["goals_for_ma10"],
            "gf_season": latest["goals_for_season_avg"],
            "ga_last": latest["goals_against"],
            "ga_ma3": latest["goals_against_ma3"],
            "ga_ma5": latest["goals_against_ma5"],
            "ga_ma10": latest["goals_against_ma10"],
            "ga_season": latest["goals_against_season_avg"],
            "total_last": latest["total_goals"],
            "total_ma3": latest["total_goals_ma3"],
            "total_ma5": latest["total_goals_ma5"],
            "total_ma10": latest["total_goals_ma10"],
            "total_season": latest["total_goals_season_avg"],
            "p1_last": latest["period_1_total"],
            "p1_ma3": latest["period_1_total_ma3"],
            "p1_ma5": latest["period_1_total_ma5"],
            "p1_ma10": latest["period_1_total_ma10"],
            "p1_season": latest["period_1_total_season_avg"],
        }

    def get_trend_indicator(self, ma3: float, ma10: float, season: float) -> str:
        """Get trend indicator based on MA comparison"""
        if ma3 > ma10 * 1.15:
            return "🔥 HOT"
        elif ma3 > ma10 * 1.05:
            return "📈 Rising"
        elif ma3 < ma10 * 0.85:
            return "🥶 COLD"
        elif ma3 < ma10 * 0.95:
            return "📉 Falling"
        elif ma3 > season:
            return "↗️  Above Avg"
        elif ma3 < season:
            return "↘️  Below Avg"
        else:
            return "➡️  Average"

    def generate_matchup_report(self, date: str = None, season: str = "20242025") -> str:
        """Generate the full daily matchup MA report"""
        date = date or datetime.now().strftime("%Y-%m-%d")
        games = self.get_todays_games(date)

        lines = []
        lines.append("=" * 90)
        lines.append(f"NHL DAILY MATCHUP MOVING AVERAGE REPORT - {date}")
        lines.append("=" * 90)
        lines.append("")
        lines.append("Comparing team trends: 3-Game, 5-Game, 10-Game, and Season Moving Averages")
        lines.append("Use this to identify betting opportunities based on recent form")
        lines.append("")

        if not games:
            lines.append("No NHL games scheduled for today.")
            return "\n".join(lines)

        lines.append(f"📅 {len(games)} games scheduled")
        lines.append("")

        betting_insights = []

        for game in games:
            home = game["home_team"]
            away = game["away_team"]

            lines.append("-" * 90)
            lines.append(f"🏒 {away} @ {home}")
            lines.append(f"   Venue: {game['venue']}")
            lines.append("-" * 90)

            # Get MA data for both teams
            home_df = self.get_team_ma_data(home, season)
            away_df = self.get_team_ma_data(away, season)

            if home_df is None and away_df is None:
                lines.append("   ⚠️  Unable to fetch data for this matchup")
                lines.append("")
                continue

            home_mas = self.get_team_current_mas(home_df) if home_df is not None else {}
            away_mas = self.get_team_current_mas(away_df) if away_df is not None else {}

            # Side-by-side comparison header
            lines.append("")
            lines.append(f"{'METRIC':<20} | {away:^30} | {home:^30}")
            lines.append("-" * 90)

            # Goals For comparison
            if home_mas and away_mas:
                lines.append(f"{'GOALS FOR':<20} |{' ':^30}|{' ':^30}")
                lines.append(f"{'  Last Game':<20} | {away_mas['gf_last']:^30.0f} | {home_mas['gf_last']:^30.0f}")
                lines.append(f"{'  3-Game MA':<20} | {away_mas['gf_ma3']:^30.2f} | {home_mas['gf_ma3']:^30.2f}")
                lines.append(f"{'  5-Game MA':<20} | {away_mas['gf_ma5']:^30.2f} | {home_mas['gf_ma5']:^30.2f}")
                lines.append(f"{'  10-Game MA':<20} | {away_mas['gf_ma10']:^30.2f} | {home_mas['gf_ma10']:^30.2f}")
                lines.append(f"{'  Season Avg':<20} | {away_mas['gf_season']:^30.2f} | {home_mas['gf_season']:^30.2f}")

                away_gf_trend = self.get_trend_indicator(away_mas['gf_ma3'], away_mas['gf_ma10'], away_mas['gf_season'])
                home_gf_trend = self.get_trend_indicator(home_mas['gf_ma3'], home_mas['gf_ma10'], home_mas['gf_season'])
                lines.append(f"{'  TREND':<20} | {away_gf_trend:^30} | {home_gf_trend:^30}")
                lines.append("")

                # Goals Against comparison
                lines.append(f"{'GOALS AGAINST':<20} |{' ':^30}|{' ':^30}")
                lines.append(f"{'  3-Game MA':<20} | {away_mas['ga_ma3']:^30.2f} | {home_mas['ga_ma3']:^30.2f}")
                lines.append(f"{'  5-Game MA':<20} | {away_mas['ga_ma5']:^30.2f} | {home_mas['ga_ma5']:^30.2f}")
                lines.append(f"{'  Season Avg':<20} | {away_mas['ga_season']:^30.2f} | {home_mas['ga_season']:^30.2f}")
                lines.append("")

                # Total Goals comparison
                lines.append(f"{'TOTAL GOALS':<20} |{' ':^30}|{' ':^30}")
                lines.append(f"{'  3-Game MA':<20} | {away_mas['total_ma3']:^30.2f} | {home_mas['total_ma3']:^30.2f}")
                lines.append(f"{'  5-Game MA':<20} | {away_mas['total_ma5']:^30.2f} | {home_mas['total_ma5']:^30.2f}")
                lines.append(f"{'  10-Game MA':<20} | {away_mas['total_ma10']:^30.2f} | {home_mas['total_ma10']:^30.2f}")
                lines.append(f"{'  Season Avg':<20} | {away_mas['total_season']:^30.2f} | {home_mas['total_season']:^30.2f}")

                away_total_trend = self.get_trend_indicator(away_mas['total_ma3'], away_mas['total_ma10'], away_mas['total_season'])
                home_total_trend = self.get_trend_indicator(home_mas['total_ma3'], home_mas['total_ma10'], home_mas['total_season'])
                lines.append(f"{'  TREND':<20} | {away_total_trend:^30} | {home_total_trend:^30}")
                lines.append("")

                # 1st Period comparison
                lines.append(f"{'1ST PERIOD TOTAL':<20} |{' ':^30}|{' ':^30}")
                lines.append(f"{'  3-Game MA':<20} | {away_mas['p1_ma3']:^30.2f} | {home_mas['p1_ma3']:^30.2f}")
                lines.append(f"{'  5-Game MA':<20} | {away_mas['p1_ma5']:^30.2f} | {home_mas['p1_ma5']:^30.2f}")
                lines.append(f"{'  Season Avg':<20} | {away_mas['p1_season']:^30.2f} | {home_mas['p1_season']:^30.2f}")

                away_p1_trend = self.get_trend_indicator(away_mas['p1_ma3'], away_mas['p1_ma10'], away_mas['p1_season'])
                home_p1_trend = self.get_trend_indicator(home_mas['p1_ma3'], home_mas['p1_ma10'], home_mas['p1_season'])
                lines.append(f"{'  TREND':<20} | {away_p1_trend:^30} | {home_p1_trend:^30}")
                lines.append("")

                # Combined game projection
                combined_total_ma5 = (away_mas['total_ma5'] + home_mas['total_ma5']) / 2
                combined_total_season = (away_mas['total_season'] + home_mas['total_season']) / 2
                combined_p1_ma5 = (away_mas['p1_ma5'] + home_mas['p1_ma5']) / 2

                lines.append(f"{'COMBINED PROJECTION':<20} |{' ':^30}|{' ':^30}")
                lines.append(f"{'  Expected Total':<20} | {combined_total_ma5:^30.2f} | (5G MA avg)")
                lines.append(f"{'  Season Baseline':<20} | {combined_total_season:^30.2f} | (Season avg)")
                lines.append(f"{'  Expected 1P Total':<20} | {combined_p1_ma5:^30.2f} | (5G MA avg)")
                lines.append("")

                # Betting insight
                insight = self._generate_betting_insight(home, away, home_mas, away_mas)
                if insight:
                    betting_insights.append(insight)
                    lines.append(f"💡 INSIGHT: {insight['text']}")

            lines.append("")

        # Summary section
        lines.append("=" * 90)
        lines.append("📊 BETTING INSIGHTS SUMMARY")
        lines.append("=" * 90)

        if betting_insights:
            # Sort by confidence
            betting_insights.sort(key=lambda x: x.get('confidence', 0), reverse=True)
            for i, insight in enumerate(betting_insights, 1):
                lines.append(f"{i}. {insight['matchup']}")
                lines.append(f"   {insight['text']}")
                lines.append(f"   Confidence: {insight.get('confidence', 'N/A')}")
                lines.append("")
        else:
            lines.append("No strong betting signals detected based on MA trends.")

        lines.append("")
        lines.append("=" * 90)
        lines.append("📈 MA TREND LEGEND:")
        lines.append("   🔥 HOT = 3G MA > 10G MA by 15%+ (strong recent uptick)")
        lines.append("   📈 Rising = 3G MA > 10G MA by 5-15%")
        lines.append("   🥶 COLD = 3G MA < 10G MA by 15%+ (strong recent downturn)")
        lines.append("   📉 Falling = 3G MA < 10G MA by 5-15%")
        lines.append("=" * 90)

        return "\n".join(lines)

    def _generate_betting_insight(self, home: str, away: str,
                                   home_mas: Dict, away_mas: Dict) -> Optional[Dict]:
        """Generate betting insight based on MA comparison"""
        insights = []

        # Combined totals analysis
        combined_ma5 = (home_mas['total_ma5'] + away_mas['total_ma5']) / 2
        combined_season = (home_mas['total_season'] + away_mas['total_season']) / 2

        # Both teams hot on scoring
        if (home_mas['total_ma3'] > home_mas['total_ma10'] * 1.1 and
            away_mas['total_ma3'] > away_mas['total_ma10'] * 1.1):
            return {
                "matchup": f"{away} @ {home}",
                "text": f"OVER looks strong - Both teams trending HOT. Combined 5G MA: {combined_ma5:.1f}",
                "bet": "OVER",
                "confidence": "HIGH"
            }

        # Both teams cold on scoring
        if (home_mas['total_ma3'] < home_mas['total_ma10'] * 0.9 and
            away_mas['total_ma3'] < away_mas['total_ma10'] * 0.9):
            return {
                "matchup": f"{away} @ {home}",
                "text": f"UNDER looks strong - Both teams trending COLD. Combined 5G MA: {combined_ma5:.1f}",
                "bet": "UNDER",
                "confidence": "HIGH"
            }

        # One team very hot, other cold - look at totals
        if combined_ma5 > combined_season * 1.15:
            return {
                "matchup": f"{away} @ {home}",
                "text": f"OVER value - Combined 5G MA ({combined_ma5:.1f}) well above season avg ({combined_season:.1f})",
                "bet": "OVER",
                "confidence": "MEDIUM"
            }

        if combined_ma5 < combined_season * 0.85:
            return {
                "matchup": f"{away} @ {home}",
                "text": f"UNDER value - Combined 5G MA ({combined_ma5:.1f}) well below season avg ({combined_season:.1f})",
                "bet": "UNDER",
                "confidence": "MEDIUM"
            }

        # 1st period analysis
        combined_p1 = (home_mas['p1_ma5'] + away_mas['p1_ma5']) / 2
        combined_p1_season = (home_mas['p1_season'] + away_mas['p1_season']) / 2

        if combined_p1 > combined_p1_season * 1.2:
            return {
                "matchup": f"{away} @ {home}",
                "text": f"1P OVER value - Combined 1P MA ({combined_p1:.2f}) trending above season ({combined_p1_season:.2f})",
                "bet": "1P OVER",
                "confidence": "MEDIUM"
            }

        return None

    def create_matchup_chart(self, home: str, away: str,
                              home_df: pd.DataFrame, away_df: pd.DataFrame,
                              save_path: str = None) -> None:
        """Create side-by-side MA chart for a matchup"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))

        metrics = [("total_goals", "Total Goals"), ("period_1_total", "1st Period Total")]

        for col, (metric, label) in enumerate(metrics):
            # Away team (top row)
            ax = axes[0, col]
            if away_df is not None:
                away_df_ma = self.ma_analyzer.calculate_moving_averages(away_df.copy(), metric)
                ax.bar(away_df_ma["game_num"], away_df_ma[metric], alpha=0.3, color='#3498db')
                ax.plot(away_df_ma["game_num"], away_df_ma[f"{metric}_ma3"], 'b-', linewidth=1.5, label="3G")
                ax.plot(away_df_ma["game_num"], away_df_ma[f"{metric}_ma5"], 'purple', linewidth=2, label="5G")
                ax.plot(away_df_ma["game_num"], away_df_ma[f"{metric}_ma10"], 'orange', linewidth=2.5, label="10G")
                ax.plot(away_df_ma["game_num"], away_df_ma[f"{metric}_season_avg"], 'g--', linewidth=1.5, label="Szn")
            ax.set_title(f"{away} - {label}", fontsize=12, fontweight='bold')
            ax.legend(loc='upper left', fontsize=8)
            ax.grid(True, alpha=0.3)

            # Home team (bottom row)
            ax = axes[1, col]
            if home_df is not None:
                home_df_ma = self.ma_analyzer.calculate_moving_averages(home_df.copy(), metric)
                ax.bar(home_df_ma["game_num"], home_df_ma[metric], alpha=0.3, color='#e74c3c')
                ax.plot(home_df_ma["game_num"], home_df_ma[f"{metric}_ma3"], 'b-', linewidth=1.5, label="3G")
                ax.plot(home_df_ma["game_num"], home_df_ma[f"{metric}_ma5"], 'purple', linewidth=2, label="5G")
                ax.plot(home_df_ma["game_num"], home_df_ma[f"{metric}_ma10"], 'orange', linewidth=2.5, label="10G")
                ax.plot(home_df_ma["game_num"], home_df_ma[f"{metric}_season_avg"], 'g--', linewidth=1.5, label="Szn")
            ax.set_title(f"{home} - {label}", fontsize=12, fontweight='bold')
            ax.legend(loc='upper left', fontsize=8)
            ax.grid(True, alpha=0.3)
            ax.set_xlabel("Game #")

        fig.suptitle(f"Matchup: {away} @ {home} - Moving Average Comparison",
                     fontsize=14, fontweight='bold', y=1.02)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"   Chart saved: {save_path}")
        else:
            plt.show()

        plt.close()

    def save_report(self, date: str = None, season: str = "20242025"):
        """Generate and save the full report with charts"""
        date = date or datetime.now().strftime("%Y-%m-%d")

        # Generate text report
        report = self.generate_matchup_report(date, season)
        print(report)

        # Save report
        report_dir = Path(f"/Users/dickgibbons/sports-betting/reports/{date}/nhl_moving_averages")
        report_dir.mkdir(parents=True, exist_ok=True)

        report_path = report_dir / f"nhl_matchup_ma_report_{date}.txt"
        with open(report_path, "w") as f:
            f.write(report)

        # Also save to Daily Reports
        daily_dir = Path(f"/Users/dickgibbons/Daily Reports/{date}")
        daily_dir.mkdir(parents=True, exist_ok=True)
        daily_path = daily_dir / f"nhl_matchup_ma_report_{date}.txt"
        with open(daily_path, "w") as f:
            f.write(report)

        print(f"\n✅ Report saved to:")
        print(f"   {report_path}")
        print(f"   {daily_path}")

        # Generate matchup charts
        games = self.get_todays_games(date)
        for game in games:
            home = game["home_team"]
            away = game["away_team"]

            home_df = self.team_data_cache.get(home)
            away_df = self.team_data_cache.get(away)

            if home_df is not None or away_df is not None:
                chart_path = report_dir / f"matchup_{away}_at_{home}.png"
                self.create_matchup_chart(home, away, home_df, away_df, str(chart_path))

        return report


def main():
    """Run the daily matchup MA report"""
    import argparse

    parser = argparse.ArgumentParser(description="NHL Daily Matchup MA Report")
    parser.add_argument("--date", type=str, help="Date (YYYY-MM-DD), defaults to today")
    parser.add_argument("--season", type=str, default="20242025", help="Season")

    args = parser.parse_args()

    reporter = NHLDailyMatchupMAReport()
    reporter.save_report(args.date, args.season)


if __name__ == "__main__":
    main()
