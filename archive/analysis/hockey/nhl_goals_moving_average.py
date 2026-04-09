#!/usr/bin/env python3
"""
NHL Goals Moving Average Visualizer

Creates stock-chart-style moving average visualizations for NHL team metrics:
- 3-game, 5-game, 10-game, and season moving averages
- Goals For, Goals Against, Total Goals
- First Period Goals
- Shots, xGoals, Corsi metrics

Visual output similar to stock trading charts with MA lines.
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import os

try:
    import pandas as pd
except ImportError:
    os.system("pip3 install pandas")
    import pandas as pd

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
except ImportError:
    os.system("pip3 install matplotlib")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

try:
    import numpy as np
except ImportError:
    os.system("pip3 install numpy")
    import numpy as np


class NHLGoalsMovingAverage:
    """NHL Goals Moving Average Analysis with Stock-Style Charts"""

    TEAM_ABBREVS = {
        'Anaheim Ducks': 'ANA', 'Arizona Coyotes': 'ARI', 'Boston Bruins': 'BOS',
        'Buffalo Sabres': 'BUF', 'Calgary Flames': 'CGY', 'Carolina Hurricanes': 'CAR',
        'Chicago Blackhawks': 'CHI', 'Colorado Avalanche': 'COL', 'Columbus Blue Jackets': 'CBJ',
        'Dallas Stars': 'DAL', 'Detroit Red Wings': 'DET', 'Edmonton Oilers': 'EDM',
        'Florida Panthers': 'FLA', 'Los Angeles Kings': 'LAK', 'Minnesota Wild': 'MIN',
        'Montreal Canadiens': 'MTL', 'Montréal Canadiens': 'MTL', 'Nashville Predators': 'NSH',
        'New Jersey Devils': 'NJD', 'New York Islanders': 'NYI', 'New York Rangers': 'NYR',
        'Ottawa Senators': 'OTT', 'Philadelphia Flyers': 'PHI', 'Pittsburgh Penguins': 'PIT',
        'San Jose Sharks': 'SJS', 'Seattle Kraken': 'SEA', 'St. Louis Blues': 'STL',
        'Tampa Bay Lightning': 'TBL', 'Toronto Maple Leafs': 'TOR', 'Utah Hockey Club': 'UTA',
        'Vancouver Canucks': 'VAN', 'Vegas Golden Knights': 'VGK', 'Washington Capitals': 'WSH',
        'Winnipeg Jets': 'WPG'
    }

    def __init__(self, use_cache: bool = True):
        self.nhl_api_base = "https://api-web.nhle.com/v1"
        self.team_games = defaultdict(list)  # team -> list of game data
        self.use_cache = use_cache
        self.cache = None

        if use_cache:
            try:
                from nhl_game_cache import NHLGameCache
                self.cache = NHLGameCache()
                print("🏒 NHL Goals Moving Average Visualizer initialized (with SQLite cache)")
            except ImportError:
                print("⚠️  Cache module not found, falling back to direct API calls")
                self.use_cache = False

        if not self.use_cache:
            print("🏒 NHL Goals Moving Average Visualizer initialized")

    def get_team_abbrev(self, team_name: str) -> str:
        """Get team abbreviation from name"""
        if team_name in self.TEAM_ABBREVS:
            return self.TEAM_ABBREVS[team_name]
        # Fuzzy match
        for name, abbrev in self.TEAM_ABBREVS.items():
            if team_name.lower() in name.lower() or name.lower() in team_name.lower():
                return abbrev
        return team_name[:3].upper()

    def fetch_team_game_log(self, team_abbrev: str, season: str = "20242025") -> List[Dict]:
        """Fetch game-by-game results for a team"""
        url = f"{self.nhl_api_base}/club-schedule-season/{team_abbrev}/{season}"

        try:
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                print(f"Error fetching {team_abbrev}: {response.status_code}")
                return []

            data = response.json()
            games = data.get("games", [])

            # Filter to completed games only
            completed = [g for g in games if g.get("gameState") == "OFF"]
            return completed

        except Exception as e:
            print(f"Error fetching {team_abbrev}: {e}")
            return []

    def fetch_game_details(self, game_id: int) -> Optional[Dict]:
        """Fetch detailed game data including period scores"""
        # Use landing endpoint which has period-by-period scoring
        url = f"{self.nhl_api_base}/gamecenter/{game_id}/landing"

        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                return None

            return response.json()

        except Exception as e:
            return None

    def extract_period_goals(self, landing_data: Dict, team_abbrev: str, period_num: int = 1) -> Tuple[int, int]:
        """Extract goals for/against for a specific period from landing data"""
        try:
            summary = landing_data.get("summary", {})
            scoring = summary.get("scoring", [])

            goals_for = 0
            goals_against = 0

            for period in scoring:
                if period.get("periodDescriptor", {}).get("number") == period_num:
                    for goal in period.get("goals", []):
                        goal_team = goal.get("teamAbbrev", {}).get("default", "")
                        if goal_team == team_abbrev:
                            goals_for += 1
                        else:
                            goals_against += 1
                    break

            return goals_for, goals_against

        except Exception:
            return 0, 0

    def collect_team_data(self, team_abbrev: str, season: str = "20242025") -> pd.DataFrame:
        """Collect all game data for a team and build DataFrame"""
        print(f"\n📊 Collecting data for {team_abbrev}...")

        # Use cache if available (MUCH faster after first run)
        if self.use_cache and self.cache:
            df = self.cache.build_team_dataframe(team_abbrev, season)
            if not df.empty:
                print(f"   Loaded {len(df)} games from cache")
            return df

        # Fallback to direct API calls (slow)
        games = self.fetch_team_game_log(team_abbrev, season)
        print(f"   Found {len(games)} completed games")

        game_data = []

        for i, game in enumerate(games):
            game_id = game.get("id")
            game_date = game.get("gameDate", "")

            # Determine if home or away
            home_abbrev = game.get("homeTeam", {}).get("abbrev", "")
            away_abbrev = game.get("awayTeam", {}).get("abbrev", "")

            is_home = (home_abbrev == team_abbrev)

            # Get scores
            home_score = game.get("homeTeam", {}).get("score", 0)
            away_score = game.get("awayTeam", {}).get("score", 0)

            if is_home:
                goals_for = home_score
                goals_against = away_score
                opponent = away_abbrev
            else:
                goals_for = away_score
                goals_against = home_score
                opponent = home_abbrev

            total_goals = goals_for + goals_against

            # Get period scores from landing endpoint
            period_1_for = 0
            period_1_against = 0
            period_1_total = 0
            shots_for = 0
            shots_against = 0

            landing = self.fetch_game_details(game_id)
            if landing:
                # Extract 1st period goals using new method
                period_1_for, period_1_against = self.extract_period_goals(
                    landing, team_abbrev, period_num=1
                )
                period_1_total = period_1_for + period_1_against

                # Extract shots from landing data
                if is_home:
                    shots_for = landing.get("homeTeam", {}).get("sog", 0) or 0
                    shots_against = landing.get("awayTeam", {}).get("sog", 0) or 0
                else:
                    shots_for = landing.get("awayTeam", {}).get("sog", 0) or 0
                    shots_against = landing.get("homeTeam", {}).get("sog", 0) or 0

            game_data.append({
                "date": game_date,
                "game_id": game_id,
                "opponent": opponent,
                "is_home": is_home,
                "goals_for": goals_for,
                "goals_against": goals_against,
                "total_goals": total_goals,
                "period_1_for": period_1_for,
                "period_1_against": period_1_against,
                "period_1_total": period_1_total,
                "shots_for": shots_for,
                "shots_against": shots_against,
                "won": 1 if goals_for > goals_against else 0,
            })

            # Rate limiting
            if (i + 1) % 10 == 0:
                print(f"   Processed {i + 1}/{len(games)} games...")

        df = pd.DataFrame(game_data)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").reset_index(drop=True)
            df["game_num"] = range(1, len(df) + 1)

        return df

    def calculate_moving_averages(self, df: pd.DataFrame, column: str) -> pd.DataFrame:
        """Calculate 3, 5, 10-game and season moving averages"""
        df = df.copy()

        df[f"{column}_ma3"] = df[column].rolling(window=3, min_periods=1).mean()
        df[f"{column}_ma5"] = df[column].rolling(window=5, min_periods=1).mean()
        df[f"{column}_ma10"] = df[column].rolling(window=10, min_periods=1).mean()
        df[f"{column}_season_avg"] = df[column].expanding().mean()

        return df

    def plot_team_moving_averages(self, team_abbrev: str, df: pd.DataFrame,
                                   metric: str = "goals_for",
                                   save_path: str = None) -> None:
        """Create stock-style moving average chart for a team"""

        if df.empty:
            print(f"No data to plot for {team_abbrev}")
            return

        # Calculate MAs
        df = self.calculate_moving_averages(df, metric)

        # Create figure
        fig, ax = plt.subplots(figsize=(14, 8))

        # Plot actual values as bars
        colors = ['#2ecc71' if v >= df[metric].mean() else '#e74c3c'
                  for v in df[metric]]
        ax.bar(df["game_num"], df[metric], alpha=0.4, color=colors, label="Actual")

        # Plot moving averages as lines
        ax.plot(df["game_num"], df[f"{metric}_ma3"], linewidth=2,
                color='#3498db', label="3-Game MA", linestyle='-')
        ax.plot(df["game_num"], df[f"{metric}_ma5"], linewidth=2.5,
                color='#9b59b6', label="5-Game MA", linestyle='-')
        ax.plot(df["game_num"], df[f"{metric}_ma10"], linewidth=3,
                color='#e67e22', label="10-Game MA", linestyle='-')
        ax.plot(df["game_num"], df[f"{metric}_season_avg"], linewidth=2,
                color='#1abc9c', label="Season Avg", linestyle='--')

        # Formatting
        metric_labels = {
            "goals_for": "Goals For",
            "goals_against": "Goals Against",
            "total_goals": "Total Goals",
            "period_1_for": "1st Period Goals For",
            "period_1_against": "1st Period Goals Against",
            "period_1_total": "1st Period Total Goals",
            "shots_for": "Shots For",
            "shots_against": "Shots Against",
        }

        metric_label = metric_labels.get(metric, metric)

        ax.set_title(f"{team_abbrev} - {metric_label} Moving Averages",
                     fontsize=16, fontweight='bold')
        ax.set_xlabel("Game Number", fontsize=12)
        ax.set_ylabel(metric_label, fontsize=12)
        ax.legend(loc='upper left', fontsize=10)
        ax.grid(True, alpha=0.3)

        # Add current values annotation
        latest = df.iloc[-1]
        current_text = (f"Current (Game {int(latest['game_num'])}):\n"
                        f"  Actual: {latest[metric]:.1f}\n"
                        f"  3-Game MA: {latest[f'{metric}_ma3']:.2f}\n"
                        f"  5-Game MA: {latest[f'{metric}_ma5']:.2f}\n"
                        f"  10-Game MA: {latest[f'{metric}_ma10']:.2f}\n"
                        f"  Season Avg: {latest[f'{metric}_season_avg']:.2f}")

        ax.annotate(current_text, xy=(0.98, 0.98), xycoords='axes fraction',
                    fontsize=10, verticalalignment='top', horizontalalignment='right',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"   Chart saved to: {save_path}")
        else:
            plt.show()

        plt.close()

    def plot_all_metrics_dashboard(self, team_abbrev: str, df: pd.DataFrame,
                                    save_path: str = None) -> None:
        """Create a dashboard with all key metrics"""

        if df.empty:
            print(f"No data to plot for {team_abbrev}")
            return

        metrics = ["goals_for", "goals_against", "total_goals",
                   "period_1_for", "period_1_total"]

        # Calculate MAs for all metrics
        for metric in metrics:
            df = self.calculate_moving_averages(df, metric)

        # Create 3x2 subplot figure
        fig, axes = plt.subplots(3, 2, figsize=(16, 14))
        axes = axes.flatten()

        metric_labels = {
            "goals_for": "Goals For",
            "goals_against": "Goals Against",
            "total_goals": "Total Goals",
            "period_1_for": "1st Period GF",
            "period_1_total": "1st Period Total",
        }

        for i, metric in enumerate(metrics):
            ax = axes[i]

            # Plot bars
            colors = ['#2ecc71' if v >= df[metric].mean() else '#e74c3c'
                      for v in df[metric]]
            ax.bar(df["game_num"], df[metric], alpha=0.3, color=colors)

            # Plot MAs
            ax.plot(df["game_num"], df[f"{metric}_ma3"], linewidth=1.5,
                    color='#3498db', label="3G")
            ax.plot(df["game_num"], df[f"{metric}_ma5"], linewidth=2,
                    color='#9b59b6', label="5G")
            ax.plot(df["game_num"], df[f"{metric}_ma10"], linewidth=2.5,
                    color='#e67e22', label="10G")
            ax.plot(df["game_num"], df[f"{metric}_season_avg"], linewidth=1.5,
                    color='#1abc9c', label="Szn", linestyle='--')

            ax.set_title(f"{metric_labels.get(metric, metric)}", fontsize=12, fontweight='bold')
            ax.set_xlabel("Game #", fontsize=9)
            ax.legend(loc='upper left', fontsize=8)
            ax.grid(True, alpha=0.3)

            # Add current value
            latest = df.iloc[-1]
            ax.annotate(f"Now: {latest[f'{metric}_ma5']:.2f}",
                        xy=(0.95, 0.95), xycoords='axes fraction',
                        fontsize=9, ha='right', va='top',
                        bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

        # Use last subplot for summary table
        ax = axes[-1]
        ax.axis('off')

        # Create summary table
        latest = df.iloc[-1]
        summary_data = []
        for metric in metrics:
            summary_data.append([
                metric_labels.get(metric, metric),
                f"{latest[metric]:.0f}",
                f"{latest[f'{metric}_ma3']:.2f}",
                f"{latest[f'{metric}_ma5']:.2f}",
                f"{latest[f'{metric}_ma10']:.2f}",
                f"{latest[f'{metric}_season_avg']:.2f}",
            ])

        table = ax.table(
            cellText=summary_data,
            colLabels=["Metric", "Last", "3G MA", "5G MA", "10G MA", "Season"],
            loc='center',
            cellLoc='center',
        )
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.5)

        # Color code cells
        for i in range(len(summary_data)):
            for j in range(1, 6):
                cell = table[(i + 1, j)]
                cell.set_facecolor('#f8f9fa')

        ax.set_title(f"Current Moving Averages Summary", fontsize=12, fontweight='bold', pad=20)

        fig.suptitle(f"{team_abbrev} - NHL Goals Moving Average Dashboard",
                     fontsize=16, fontweight='bold', y=1.02)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"   Dashboard saved to: {save_path}")
        else:
            plt.show()

        plt.close()

    def generate_team_report(self, team_abbrev: str, df: pd.DataFrame) -> str:
        """Generate text report with moving average analysis"""

        if df.empty:
            return f"No data available for {team_abbrev}"

        metrics = ["goals_for", "goals_against", "total_goals",
                   "period_1_for", "period_1_total"]

        for metric in metrics:
            df = self.calculate_moving_averages(df, metric)

        latest = df.iloc[-1]
        games_played = len(df)

        lines = []
        lines.append("=" * 70)
        lines.append(f"NHL GOALS MOVING AVERAGE REPORT - {team_abbrev}")
        lines.append("=" * 70)
        lines.append(f"Games Played: {games_played}")
        lines.append(f"Last Game: {latest['date'].strftime('%Y-%m-%d')} vs {latest['opponent']}")
        lines.append(f"Result: {'W' if latest['won'] else 'L'} ({int(latest['goals_for'])}-{int(latest['goals_against'])})")
        lines.append("")

        lines.append("-" * 70)
        lines.append("MOVING AVERAGES (Stock-Chart Style)")
        lines.append("-" * 70)
        lines.append(f"{'Metric':<20} {'Last':>6} {'3G MA':>8} {'5G MA':>8} {'10G MA':>8} {'Season':>8}")
        lines.append("-" * 70)

        metric_labels = {
            "goals_for": "Goals For",
            "goals_against": "Goals Against",
            "total_goals": "Total Goals",
            "period_1_for": "1P Goals For",
            "period_1_total": "1P Total Goals",
        }

        for metric in metrics:
            label = metric_labels.get(metric, metric)
            lines.append(
                f"{label:<20} {latest[metric]:>6.0f} "
                f"{latest[f'{metric}_ma3']:>8.2f} "
                f"{latest[f'{metric}_ma5']:>8.2f} "
                f"{latest[f'{metric}_ma10']:>8.2f} "
                f"{latest[f'{metric}_season_avg']:>8.2f}"
            )

        lines.append("")
        lines.append("-" * 70)
        lines.append("TREND ANALYSIS")
        lines.append("-" * 70)

        # Analyze trends
        for metric in ["goals_for", "total_goals", "period_1_total"]:
            label = metric_labels.get(metric, metric)
            ma3 = latest[f'{metric}_ma3']
            ma10 = latest[f'{metric}_ma10']
            season = latest[f'{metric}_season_avg']

            if ma3 > ma10 * 1.1:
                trend = "📈 HOT (3G MA > 10G MA by 10%+)"
            elif ma3 < ma10 * 0.9:
                trend = "📉 COLD (3G MA < 10G MA by 10%+)"
            elif ma3 > season:
                trend = "↗️  Above average"
            elif ma3 < season:
                trend = "↘️  Below average"
            else:
                trend = "➡️  At average"

            lines.append(f"{label}: {trend}")

        lines.append("")
        lines.append("-" * 70)
        lines.append("BETTING INSIGHTS")
        lines.append("-" * 70)

        # Totals insight
        total_ma5 = latest['total_goals_ma5']
        total_season = latest['total_goals_season_avg']
        lines.append(f"Game Totals: 5G MA = {total_ma5:.2f}, Season = {total_season:.2f}")
        if total_ma5 > 6.0:
            lines.append("  → Recent trend suggests OVER may have value")
        elif total_ma5 < 5.0:
            lines.append("  → Recent trend suggests UNDER may have value")

        # 1st period insight
        p1_ma5 = latest['period_1_total_ma5']
        p1_season = latest['period_1_total_season_avg']
        lines.append(f"1st Period: 5G MA = {p1_ma5:.2f}, Season = {p1_season:.2f}")
        if p1_ma5 > 1.5:
            lines.append("  → Recent 1P trend is high-scoring")
        elif p1_ma5 < 1.0:
            lines.append("  → Recent 1P trend is low-scoring")

        lines.append("")
        lines.append("=" * 70)

        return "\n".join(lines)

    def analyze_all_teams(self, season: str = "20242025",
                          save_charts: bool = True,
                          output_dir: str = None) -> Dict[str, pd.DataFrame]:
        """Analyze all NHL teams and generate reports/charts"""

        output_dir = output_dir or f"/Users/dickgibbons/AI Projects/sports-betting/reports/{datetime.now().strftime('%Y-%m-%d')}/nhl_moving_averages"
        os.makedirs(output_dir, exist_ok=True)

        all_team_data = {}
        all_reports = []

        teams = list(self.TEAM_ABBREVS.values())
        teams = list(set(teams))  # Remove duplicates

        print(f"\n{'='*70}")
        print(f"NHL GOALS MOVING AVERAGE ANALYSIS - ALL TEAMS")
        print(f"Season: {season}")
        print(f"{'='*70}\n")

        for i, team in enumerate(sorted(teams)):
            print(f"\n[{i+1}/{len(teams)}] Processing {team}...")

            try:
                df = self.collect_team_data(team, season)

                if df.empty:
                    print(f"   No data for {team}")
                    continue

                all_team_data[team] = df

                # Generate report
                report = self.generate_team_report(team, df)
                all_reports.append(report)

                # Save chart
                if save_charts:
                    chart_path = os.path.join(output_dir, f"{team}_moving_averages.png")
                    self.plot_all_metrics_dashboard(team, df, save_path=chart_path)

            except Exception as e:
                print(f"   Error processing {team}: {e}")

        # Save combined report
        report_path = os.path.join(output_dir, "all_teams_moving_averages.txt")
        with open(report_path, "w") as f:
            f.write("\n\n".join(all_reports))
        print(f"\n✅ Combined report saved to: {report_path}")

        return all_team_data


def main():
    """Run the moving average analysis"""
    import argparse

    parser = argparse.ArgumentParser(description="NHL Goals Moving Average Visualizer")
    parser.add_argument("--team", type=str, help="Team abbreviation (e.g., BOS, TOR)")
    parser.add_argument("--all", action="store_true", help="Analyze all teams")
    parser.add_argument("--season", type=str, default="20242025", help="Season (e.g., 20242025)")
    parser.add_argument("--metric", type=str, default="total_goals",
                        choices=["goals_for", "goals_against", "total_goals",
                                 "period_1_for", "period_1_total", "shots_for"],
                        help="Metric to visualize")

    args = parser.parse_args()

    analyzer = NHLGoalsMovingAverage()

    if args.all:
        analyzer.analyze_all_teams(season=args.season)
    elif args.team:
        team = args.team.upper()
        df = analyzer.collect_team_data(team, args.season)

        if not df.empty:
            # Print report
            report = analyzer.generate_team_report(team, df)
            print(report)

            # Save chart
            date_str = datetime.now().strftime("%Y-%m-%d")
            output_dir = f"/Users/dickgibbons/AI Projects/sports-betting/reports/{date_str}/nhl_moving_averages"
            os.makedirs(output_dir, exist_ok=True)

            chart_path = os.path.join(output_dir, f"{team}_{args.metric}_ma.png")
            analyzer.plot_team_moving_averages(team, df, metric=args.metric, save_path=chart_path)

            dashboard_path = os.path.join(output_dir, f"{team}_dashboard.png")
            analyzer.plot_all_metrics_dashboard(team, df, save_path=dashboard_path)
    else:
        # Demo with one team
        print("Running demo analysis for Boston Bruins...")
        df = analyzer.collect_team_data("BOS", args.season)

        if not df.empty:
            report = analyzer.generate_team_report("BOS", df)
            print(report)

            date_str = datetime.now().strftime("%Y-%m-%d")
            output_dir = f"/Users/dickgibbons/AI Projects/sports-betting/reports/{date_str}/nhl_moving_averages"
            os.makedirs(output_dir, exist_ok=True)

            dashboard_path = os.path.join(output_dir, "BOS_dashboard.png")
            analyzer.plot_all_metrics_dashboard("BOS", df, save_path=dashboard_path)


if __name__ == "__main__":
    main()
