#!/usr/bin/env python3
"""
NHL First Period Performance Analyzer
Identifies "fast start" vs "slow start" teams for 1st period betting

Tracks per-team:
- 1st period moneyline wins/losses/ties
- 1st period goals scored/against
- 1st period totals (O/U patterns)
- Home vs road first period performance
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
import argparse


class NHLFirstPeriodAnalyzer:
    """Analyze NHL team first period performance"""

    def __init__(self):
        self.nhl_api_base = "https://statsapi.web.nhl.com/api/v1"

        # Team stats
        self.team_stats = defaultdict(lambda: {
            'first_period_wins': 0,
            'first_period_losses': 0,
            'first_period_ties': 0,
            'first_period_goals_for': 0,
            'first_period_goals_against': 0,
            'first_period_total_goals': 0,
            'games_analyzed': 0,
            'home_1p_wins': 0,
            'home_1p_losses': 0,
            'home_1p_ties': 0,
            'away_1p_wins': 0,
            'away_1p_losses': 0,
            'away_1p_ties': 0
        })

        print("🏒 NHL First Period Analyzer initialized")

    def analyze_season(self, start_date: str, end_date: str):
        """Analyze first period performance across a date range"""

        print(f"\n{'='*80}")
        print(f"🔍 ANALYZING NHL FIRST PERIOD PERFORMANCE")
        print(f"📅 From {start_date} to {end_date}")
        print(f"{'='*80}\n")

        # Fetch games in date range
        games = self._fetch_games_in_range(start_date, end_date)

        print(f"📊 Found {len(games)} games to analyze")
        print(f"🔄 Analyzing first period performance...\n")

        analyzed_count = 0
        for game_id in games:
            if self._analyze_game_first_period(game_id):
                analyzed_count += 1
                if analyzed_count % 50 == 0:
                    print(f"   Analyzed {analyzed_count}/{len(games)} games...")

        print(f"\n✅ Analysis complete: {analyzed_count} games processed\n")

        # Calculate and display results
        self._calculate_team_metrics()
        self._display_results()

        return self.team_stats

    def _fetch_games_in_range(self, start_date: str, end_date: str) -> List[int]:
        """Fetch all game IDs in date range"""

        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        game_ids = []
        current = start

        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            url = f"{self.nhl_api_base}/schedule?date={date_str}"

            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    dates = data.get('dates', [])
                    for date_obj in dates:
                        games = date_obj.get('games', [])
                        for game in games:
                            # Only include regular/playoff games, not preseason
                            if game.get('gameType') in ['R', 'P']:
                                game_ids.append(game['gamePk'])
            except Exception as e:
                print(f"Error fetching schedule for {date_str}: {e}")

            current += timedelta(days=1)

        return game_ids

    def _analyze_game_first_period(self, game_id: int) -> bool:
        """Analyze first period for a specific game"""

        try:
            # Fetch linescore (includes period-by-period scoring)
            url = f"{self.nhl_api_base}/game/{game_id}/linescore"
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                return False

            data = response.json()

            # Get teams
            away_team = data.get('teams', {}).get('away', {}).get('team', {}).get('name', '')
            home_team = data.get('teams', {}).get('home', {}).get('team', {}).get('name', '')

            if not away_team or not home_team:
                return False

            # Get first period scores
            periods = data.get('periods', [])
            if len(periods) < 1:
                # Game not completed or no period data
                return False

            first_period = periods[0]
            away_goals_1p = first_period.get('away', {}).get('goals', 0)
            home_goals_1p = first_period.get('home', {}).get('goals', 0)

            # Update team stats
            total_goals_1p = away_goals_1p + home_goals_1p

            # Away team stats
            self.team_stats[away_team]['games_analyzed'] += 1
            self.team_stats[away_team]['first_period_goals_for'] += away_goals_1p
            self.team_stats[away_team]['first_period_goals_against'] += home_goals_1p
            self.team_stats[away_team]['first_period_total_goals'] += total_goals_1p

            if away_goals_1p > home_goals_1p:
                self.team_stats[away_team]['first_period_wins'] += 1
                self.team_stats[away_team]['away_1p_wins'] += 1
            elif away_goals_1p < home_goals_1p:
                self.team_stats[away_team]['first_period_losses'] += 1
                self.team_stats[away_team]['away_1p_losses'] += 1
            else:
                self.team_stats[away_team]['first_period_ties'] += 1
                self.team_stats[away_team]['away_1p_ties'] += 1

            # Home team stats
            self.team_stats[home_team]['games_analyzed'] += 1
            self.team_stats[home_team]['first_period_goals_for'] += home_goals_1p
            self.team_stats[home_team]['first_period_goals_against'] += away_goals_1p
            self.team_stats[home_team]['first_period_total_goals'] += total_goals_1p

            if home_goals_1p > away_goals_1p:
                self.team_stats[home_team]['first_period_wins'] += 1
                self.team_stats[home_team]['home_1p_wins'] += 1
            elif home_goals_1p < away_goals_1p:
                self.team_stats[home_team]['first_period_losses'] += 1
                self.team_stats[home_team]['home_1p_losses'] += 1
            else:
                self.team_stats[home_team]['first_period_ties'] += 1
                self.team_stats[home_team]['home_1p_ties'] += 1

            return True

        except Exception as e:
            # Skip games with errors
            return False

    def _calculate_team_metrics(self):
        """Calculate win rates, scoring averages, etc."""

        for team, stats in self.team_stats.items():
            games = stats['games_analyzed']
            if games == 0:
                continue

            # First period moneyline win rate
            wins = stats['first_period_wins']
            losses = stats['first_period_losses']
            ties = stats['first_period_ties']

            stats['1p_win_rate'] = (wins / games) * 100 if games > 0 else 0
            stats['1p_loss_rate'] = (losses / games) * 100 if games > 0 else 0
            stats['1p_tie_rate'] = (ties / games) * 100 if games > 0 else 0

            # Goals per first period
            stats['1p_goals_for_avg'] = stats['first_period_goals_for'] / games
            stats['1p_goals_against_avg'] = stats['first_period_goals_against'] / games
            stats['1p_goal_differential'] = stats['1p_goals_for_avg'] - stats['1p_goals_against_avg']

            # Total goals average (for O/U)
            stats['1p_total_avg'] = stats['first_period_total_goals'] / games

            # Home vs road splits
            home_games = stats['home_1p_wins'] + stats['home_1p_losses'] + stats['home_1p_ties']
            away_games = stats['away_1p_wins'] + stats['away_1p_losses'] + stats['away_1p_ties']

            stats['home_1p_win_rate'] = (stats['home_1p_wins'] / home_games * 100) if home_games > 0 else 0
            stats['away_1p_win_rate'] = (stats['away_1p_wins'] / away_games * 100) if away_games > 0 else 0

    def _display_results(self):
        """Display team first period performance"""

        print(f"\n{'='*80}")
        print(f"🏒 NHL FIRST PERIOD PERFORMANCE RANKINGS")
        print(f"{'='*80}\n")

        # Sort teams by 1P win rate
        teams_sorted = sorted(
            self.team_stats.items(),
            key=lambda x: x[1].get('1p_win_rate', 0),
            reverse=True
        )

        print(f"{'='*80}")
        print(f"🔥 TOP 10 FAST STARTERS (1st Period ML Win Rate)")
        print(f"{'='*80}\n")

        for i, (team, stats) in enumerate(teams_sorted[:10], 1):
            win_rate = stats.get('1p_win_rate', 0)
            record = f"{stats['first_period_wins']}-{stats['first_period_losses']}-{stats['first_period_ties']}"
            goals_diff = stats.get('1p_goal_differential', 0)
            goals_for = stats.get('1p_goals_for_avg', 0)

            print(f"{i:2d}. {team:30s} {win_rate:5.1f}% ({record:10s}) | "
                  f"GF/1P: {goals_for:.2f} | Diff: {goals_diff:+.2f}")

        print(f"\n{'='*80}")
        print(f"❄️  BOTTOM 10 SLOW STARTERS (1st Period ML Win Rate)")
        print(f"{'='*80}\n")

        for i, (team, stats) in enumerate(teams_sorted[-10:], 1):
            win_rate = stats.get('1p_win_rate', 0)
            record = f"{stats['first_period_wins']}-{stats['first_period_losses']}-{stats['first_period_ties']}"
            goals_diff = stats.get('1p_goal_differential', 0)
            goals_against = stats.get('1p_goals_against_avg', 0)

            print(f"{i:2d}. {team:30s} {win_rate:5.1f}% ({record:10s}) | "
                  f"GA/1P: {goals_against:.2f} | Diff: {goals_diff:+.2f}")

        # High-scoring first periods
        teams_by_total = sorted(
            self.team_stats.items(),
            key=lambda x: x[1].get('1p_total_avg', 0),
            reverse=True
        )

        print(f"\n{'='*80}")
        print(f"🎯 TOP 10 HIGHEST FIRST PERIOD TOTALS (For OVER Betting)")
        print(f"{'='*80}\n")

        for i, (team, stats) in enumerate(teams_by_total[:10], 1):
            total_avg = stats.get('1p_total_avg', 0)
            games = stats['games_analyzed']

            print(f"{i:2d}. {team:30s} Avg 1P Total: {total_avg:.2f} goals/game ({games} games)")

        print(f"\n{'='*80}")
        print(f"💤 BOTTOM 10 LOWEST FIRST PERIOD TOTALS (For UNDER Betting)")
        print(f"{'='*80}\n")

        for i, (team, stats) in enumerate(teams_by_total[-10:], 1):
            total_avg = stats.get('1p_total_avg', 0)
            games = stats['games_analyzed']

            print(f"{i:2d}. {team:30s} Avg 1P Total: {total_avg:.2f} goals/game ({games} games)")

    def save_results(self, output_file: str):
        """Save analysis to JSON"""

        # Convert defaultdict to regular dict for JSON serialization
        output = {}
        for team, stats in self.team_stats.items():
            output[team] = dict(stats)

        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\n✅ Results saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Analyze NHL first period performance by team')
    parser.add_argument('--start-date', type=str, default='2024-10-01',
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, default=datetime.now().strftime('%Y-%m-%d'),
                       help='End date (YYYY-MM-DD)')
    parser.add_argument('--output', type=str,
                       default='/Users/dickgibbons/betting_data/nhl_first_period_stats.json',
                       help='Output file path')

    args = parser.parse_args()

    analyzer = NHLFirstPeriodAnalyzer()
    analyzer.analyze_season(args.start_date, args.end_date)
    analyzer.save_results(args.output)


if __name__ == "__main__":
    main()
