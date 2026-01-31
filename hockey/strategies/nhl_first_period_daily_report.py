#!/usr/bin/env python3
"""
NHL First Period Daily Report
Tracks specific metrics per team for 1P betting:
- % games where 1P total > 1.5 goals
- % games where team scores > 0.5 goals (at least 1 goal)
- Home/Road splits
- Recent form (last 3, 5, 10 games)
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict, deque
import argparse


class NHLFirstPeriodDailyReport:
    """Generate daily first period performance report"""

    def __init__(self):
        self.espn_api_base = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard"

        # Team stats with detailed tracking
        self.team_stats = defaultdict(lambda: {
            'games': [],  # List of game data for recent form calculation
            'total_games': 0,
            'over_1_5_total': 0,  # 1P total > 1.5
            'team_over_0_5': 0,   # Team scored 1+ goals in 1P
            'team_allows_0_5': 0,  # Team allowed 1+ goals in 1P
            'home_games': 0,
            'home_over_1_5': 0,
            'home_over_0_5': 0,
            'home_allows_0_5': 0,
            'away_games': 0,
            'away_over_1_5': 0,
            'away_over_0_5': 0,
            'away_allows_0_5': 0,
            # Road trip fatigue tracking
            'road_game_1': {'games': 0, 'allows_1plus': 0, 'scores_1plus': 0},  # 1st road game
            'road_game_2': {'games': 0, 'allows_1plus': 0, 'scores_1plus': 0},  # 2nd road game
            'road_game_3': {'games': 0, 'allows_1plus': 0, 'scores_1plus': 0},  # 3rd road game
            'road_game_4plus': {'games': 0, 'allows_1plus': 0, 'scores_1plus': 0}  # 4th+ road game
        })

        # Track team schedules for road trip context
        self.team_schedules = defaultdict(list)

        # Store all games for multi-pass analysis
        self.all_games = []

        print("🏒 NHL First Period Daily Report initialized")

    def analyze_season(self, start_date: str, end_date: str):
        """Analyze first period performance across a date range"""

        print(f"\n{'='*80}")
        print(f"🔍 ANALYZING NHL FIRST PERIOD PERFORMANCE")
        print(f"📅 From {start_date} to {end_date}")
        print(f"{'='*80}\n")

        # Fetch games in date range
        games = self._fetch_games_in_range(start_date, end_date)
        self.all_games = games

        print(f"📊 Found {len(games)} games to analyze")

        # Pass 1: Build team schedules for road trip tracking
        print(f"🗓️  Building team schedules for road trip context...")
        self._build_team_schedules(games)
        print(f"   ✅ Team schedules built\n")

        # Pass 2: Analyze first period performance with road trip context
        print(f"🔄 Analyzing first period performance...\n")

        analyzed_count = 0
        for game_data in games:
            if self._analyze_game_first_period(game_data):
                analyzed_count += 1
                if analyzed_count % 50 == 0:
                    print(f"   Analyzed {analyzed_count}/{len(games)} games...")

        print(f"\n✅ Analysis complete: {analyzed_count} games processed\n")

        return self.team_stats

    def _fetch_games_in_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Fetch all completed games in date range from ESPN API"""

        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        all_games = []
        current = start

        while current <= end:
            date_str = current.strftime('%Y%m%d')
            url = f"{self.espn_api_base}?dates={date_str}"

            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    events = data.get('events', [])

                    for event in events:
                        # Only process completed games
                        if event.get('status', {}).get('type', {}).get('completed'):
                            all_games.append({
                                'date': current.strftime('%Y-%m-%d'),
                                'event': event
                            })
            except Exception as e:
                print(f"Error fetching games for {date_str}: {e}")

            current += timedelta(days=1)

        return all_games

    def _build_team_schedules(self, games: List[Dict]):
        """Build chronological schedule for each team to track road trips"""

        for game_data in games:
            try:
                event = game_data['event']
                game_date = game_data['date']

                # Get teams
                competitions = event.get('competitions', [])
                if not competitions:
                    continue

                competition = competitions[0]
                competitors = competition.get('competitors', [])

                if len(competitors) < 2:
                    continue

                home_comp = next((c for c in competitors if c.get('homeAway') == 'home'), None)
                away_comp = next((c for c in competitors if c.get('homeAway') == 'away'), None)

                if not home_comp or not away_comp:
                    continue

                home_team = home_comp.get('team', {}).get('displayName', '')
                away_team = away_comp.get('team', {}).get('displayName', '')

                # Add to team schedules
                self.team_schedules[home_team].append({
                    'date': game_date,
                    'location': 'home',
                    'opponent': away_team
                })

                self.team_schedules[away_team].append({
                    'date': game_date,
                    'location': 'away',
                    'opponent': home_team
                })

            except Exception:
                continue

    def _get_road_trip_game_number(self, team: str, game_date: str) -> int:
        """Get which game number this is on the current road trip (1, 2, 3, 4+)"""

        team_schedule = self.team_schedules.get(team, [])

        # Count consecutive road games before this one
        consecutive_road = 0
        for game in reversed(team_schedule):
            if game['date'] >= game_date:
                continue  # Skip current game and future games

            if game['location'] == 'away':
                consecutive_road += 1
            else:
                break  # Hit a home game, road trip starts after this

        return consecutive_road + 1  # +1 for current game

    def _analyze_game_first_period(self, game_data: Dict) -> bool:
        """Analyze first period for a specific game"""

        try:
            event = game_data['event']
            game_date = game_data['date']

            # Get teams
            competitions = event.get('competitions', [])
            if not competitions:
                return False

            competition = competitions[0]
            competitors = competition.get('competitors', [])

            if len(competitors) < 2:
                return False

            home_comp = next((c for c in competitors if c.get('homeAway') == 'home'), None)
            away_comp = next((c for c in competitors if c.get('homeAway') == 'away'), None)

            if not home_comp or not away_comp:
                return False

            home_team = home_comp.get('team', {}).get('displayName', '')
            away_team = away_comp.get('team', {}).get('displayName', '')

            # Get period-by-period scoring from linescores
            home_linescores = home_comp.get('linescores', [])
            away_linescores = away_comp.get('linescores', [])

            if not home_linescores or not away_linescores:
                return False

            # First period is index 0
            home_1p_goals = int(home_linescores[0].get('value', 0)) if len(home_linescores) > 0 else 0
            away_1p_goals = int(away_linescores[0].get('value', 0)) if len(away_linescores) > 0 else 0

            total_1p_goals = home_1p_goals + away_1p_goals

            # Track game data for each team
            home_game_data = {
                'date': game_date,
                'location': 'home',
                'goals_for': home_1p_goals,
                'goals_against': away_1p_goals,
                'total': total_1p_goals,
                'over_1_5': total_1p_goals > 1.5,
                'scored_1_plus': home_1p_goals >= 1
            }

            away_game_data = {
                'date': game_date,
                'location': 'away',
                'goals_for': away_1p_goals,
                'goals_against': home_1p_goals,
                'total': total_1p_goals,
                'over_1_5': total_1p_goals > 1.5,
                'scored_1_plus': away_1p_goals >= 1
            }

            # Update home team stats
            self.team_stats[home_team]['games'].append(home_game_data)
            self.team_stats[home_team]['total_games'] += 1
            self.team_stats[home_team]['home_games'] += 1

            if total_1p_goals > 1.5:
                self.team_stats[home_team]['over_1_5_total'] += 1
                self.team_stats[home_team]['home_over_1_5'] += 1

            if home_1p_goals >= 1:
                self.team_stats[home_team]['team_over_0_5'] += 1
                self.team_stats[home_team]['home_over_0_5'] += 1

            if away_1p_goals >= 1:  # Home team allowed 1+ goals
                self.team_stats[home_team]['team_allows_0_5'] += 1
                self.team_stats[home_team]['home_allows_0_5'] += 1

            # Update away team stats
            self.team_stats[away_team]['games'].append(away_game_data)
            self.team_stats[away_team]['total_games'] += 1
            self.team_stats[away_team]['away_games'] += 1

            if total_1p_goals > 1.5:
                self.team_stats[away_team]['over_1_5_total'] += 1
                self.team_stats[away_team]['away_over_1_5'] += 1

            if away_1p_goals >= 1:
                self.team_stats[away_team]['team_over_0_5'] += 1
                self.team_stats[away_team]['away_over_0_5'] += 1

            if home_1p_goals >= 1:  # Away team allowed 1+ goals
                self.team_stats[away_team]['team_allows_0_5'] += 1
                self.team_stats[away_team]['away_allows_0_5'] += 1

            # Track road trip fatigue for away team
            road_game_num = self._get_road_trip_game_number(away_team, game_date)

            if road_game_num == 1:
                key = 'road_game_1'
            elif road_game_num == 2:
                key = 'road_game_2'
            elif road_game_num == 3:
                key = 'road_game_3'
            else:  # 4+
                key = 'road_game_4plus'

            self.team_stats[away_team][key]['games'] += 1

            if away_1p_goals >= 1:
                self.team_stats[away_team][key]['scores_1plus'] += 1

            if home_1p_goals >= 1:  # Away team allowed 1+ goals
                self.team_stats[away_team][key]['allows_1plus'] += 1

            return True

        except Exception as e:
            return False

    def generate_report(self, output_file: Optional[str] = None, csv_file: Optional[str] = None):
        """Generate formatted daily report"""

        print(f"\n{'='*80}")
        print(f"🏒 NHL FIRST PERIOD PERFORMANCE REPORT - {datetime.now().strftime('%Y-%m-%d')}")
        print(f"{'='*80}\n")

        # Sort teams alphabetically
        teams_sorted = sorted(self.team_stats.items(), key=lambda x: x[0])

        for team, stats in teams_sorted:
            if stats['total_games'] == 0:
                continue

            print(f"\n{'─'*80}")
            print(f"🏒 {team}")
            print(f"{'─'*80}")

            # Season totals
            total_games = stats['total_games']
            over_1_5_pct = (stats['over_1_5_total'] / total_games * 100) if total_games > 0 else 0
            team_over_0_5_pct = (stats['team_over_0_5'] / total_games * 100) if total_games > 0 else 0

            print(f"\n📊 SEASON STATS ({total_games} games)")
            print(f"   1P Total OVER 1.5 goals:  {over_1_5_pct:5.1f}% ({stats['over_1_5_total']}/{total_games})")
            print(f"   Team scores 1+ goals:     {team_over_0_5_pct:5.1f}% ({stats['team_over_0_5']}/{total_games})")

            # Home/Road splits
            home_games = stats['home_games']
            away_games = stats['away_games']

            if home_games > 0:
                home_over_1_5_pct = (stats['home_over_1_5'] / home_games * 100)
                home_over_0_5_pct = (stats['home_over_0_5'] / home_games * 100)

                print(f"\n🏠 HOME SPLITS ({home_games} games)")
                print(f"   1P Total OVER 1.5:  {home_over_1_5_pct:5.1f}%")
                print(f"   Team scores 1+:     {home_over_0_5_pct:5.1f}%")

            if away_games > 0:
                away_over_1_5_pct = (stats['away_over_1_5'] / away_games * 100)
                away_over_0_5_pct = (stats['away_over_0_5'] / away_games * 100)

                print(f"\n🛫 ROAD SPLITS ({away_games} games)")
                print(f"   1P Total OVER 1.5:  {away_over_1_5_pct:5.1f}%")
                print(f"   Team scores 1+:     {away_over_0_5_pct:5.1f}%")

            # Recent form (last 3, 5, 10 games)
            games = sorted(stats['games'], key=lambda x: x['date'], reverse=True)

            for period in [3, 5, 10]:
                recent_games = games[:period]
                if len(recent_games) < period:
                    continue

                over_1_5_count = sum(1 for g in recent_games if g['over_1_5'])
                scored_1_plus_count = sum(1 for g in recent_games if g['scored_1_plus'])

                over_1_5_pct_recent = (over_1_5_count / period * 100)
                scored_1_plus_pct_recent = (scored_1_plus_count / period * 100)

                print(f"\n📈 LAST {period} GAMES")
                print(f"   1P Total OVER 1.5:  {over_1_5_pct_recent:5.1f}% ({over_1_5_count}/{period})")
                print(f"   Team scores 1+:     {scored_1_plus_pct_recent:5.1f}% ({scored_1_plus_count}/{period})")

        print(f"\n{'='*80}\n")

        # Save to files if specified
        if output_file:
            self._save_json_report(output_file)

        if csv_file:
            self.save_csv_report(csv_file)

    def _save_json_report(self, output_file: str):
        """Save detailed report to JSON"""

        output = {}
        for team, stats in self.team_stats.items():
            # Don't include raw game list in JSON output
            output[team] = {
                'total_games': stats['total_games'],
                'season': {
                    'over_1_5_pct': (stats['over_1_5_total'] / stats['total_games'] * 100) if stats['total_games'] > 0 else 0,
                    'over_1_5_count': stats['over_1_5_total'],
                    'team_scores_1_plus_pct': (stats['team_over_0_5'] / stats['total_games'] * 100) if stats['total_games'] > 0 else 0,
                    'team_scores_1_plus_count': stats['team_over_0_5']
                },
                'home': {
                    'games': stats['home_games'],
                    'over_1_5_pct': (stats['home_over_1_5'] / stats['home_games'] * 100) if stats['home_games'] > 0 else 0,
                    'team_scores_1_plus_pct': (stats['home_over_0_5'] / stats['home_games'] * 100) if stats['home_games'] > 0 else 0
                },
                'away': {
                    'games': stats['away_games'],
                    'over_1_5_pct': (stats['away_over_1_5'] / stats['away_games'] * 100) if stats['away_games'] > 0 else 0,
                    'team_scores_1_plus_pct': (stats['away_over_0_5'] / stats['away_games'] * 100) if stats['away_games'] > 0 else 0
                }
            }

            # Add recent form
            games = sorted(stats['games'], key=lambda x: x['date'], reverse=True)
            for period in [3, 5, 10]:
                recent = games[:period]
                if len(recent) >= period:
                    output[team][f'last_{period}'] = {
                        'over_1_5_pct': (sum(1 for g in recent if g['over_1_5']) / period * 100),
                        'team_scores_1_plus_pct': (sum(1 for g in recent if g['scored_1_plus']) / period * 100)
                    }

        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"✅ JSON report saved to: {output_file}")

    def save_csv_report(self, output_file: str):
        """Save report to CSV format for easy sorting/filtering"""

        import csv

        # Prepare CSV data
        csv_data = []

        for team, stats in sorted(self.team_stats.items()):
            if stats['total_games'] == 0:
                continue

            row = {
                'Team': team,
                'Total_Games': stats['total_games'],

                # Season stats - Scoring
                'Season_Over_1.5_Pct': round((stats['over_1_5_total'] / stats['total_games'] * 100) if stats['total_games'] > 0 else 0, 1),
                'Season_Over_1.5_Count': stats['over_1_5_total'],
                'Season_Team_Scores_1+_Pct': round((stats['team_over_0_5'] / stats['total_games'] * 100) if stats['total_games'] > 0 else 0, 1),
                'Season_Team_Scores_1+_Count': stats['team_over_0_5'],

                # Season stats - Defense
                'Season_Team_Allows_1+_Pct': round((stats['team_allows_0_5'] / stats['total_games'] * 100) if stats['total_games'] > 0 else 0, 1),
                'Season_Team_Allows_1+_Count': stats['team_allows_0_5'],

                # Home stats
                'Home_Games': stats['home_games'],
                'Home_Over_1.5_Pct': round((stats['home_over_1_5'] / stats['home_games'] * 100) if stats['home_games'] > 0 else 0, 1),
                'Home_Team_Scores_1+_Pct': round((stats['home_over_0_5'] / stats['home_games'] * 100) if stats['home_games'] > 0 else 0, 1),
                'Home_Team_Allows_1+_Pct': round((stats['home_allows_0_5'] / stats['home_games'] * 100) if stats['home_games'] > 0 else 0, 1),

                # Road stats
                'Road_Games': stats['away_games'],
                'Road_Over_1.5_Pct': round((stats['away_over_1_5'] / stats['away_games'] * 100) if stats['away_games'] > 0 else 0, 1),
                'Road_Team_Scores_1+_Pct': round((stats['away_over_0_5'] / stats['away_games'] * 100) if stats['away_games'] > 0 else 0, 1),
                'Road_Team_Allows_1+_Pct': round((stats['away_allows_0_5'] / stats['away_games'] * 100) if stats['away_games'] > 0 else 0, 1),

                # Road trip fatigue - Goals Allowed (Defense) by game number
                'RT_Game1_Allows_Pct': round((stats['road_game_1']['allows_1plus'] / stats['road_game_1']['games'] * 100) if stats['road_game_1']['games'] > 0 else 0, 1),
                'RT_Game2_Allows_Pct': round((stats['road_game_2']['allows_1plus'] / stats['road_game_2']['games'] * 100) if stats['road_game_2']['games'] > 0 else 0, 1),
                'RT_Game3_Allows_Pct': round((stats['road_game_3']['allows_1plus'] / stats['road_game_3']['games'] * 100) if stats['road_game_3']['games'] > 0 else 0, 1),
                'RT_Game4+_Allows_Pct': round((stats['road_game_4plus']['allows_1plus'] / stats['road_game_4plus']['games'] * 100) if stats['road_game_4plus']['games'] > 0 else 0, 1),

                # Road trip fatigue - Goals Scored (Offense) by game number
                'RT_Game1_Scores_Pct': round((stats['road_game_1']['scores_1plus'] / stats['road_game_1']['games'] * 100) if stats['road_game_1']['games'] > 0 else 0, 1),
                'RT_Game2_Scores_Pct': round((stats['road_game_2']['scores_1plus'] / stats['road_game_2']['games'] * 100) if stats['road_game_2']['games'] > 0 else 0, 1),
                'RT_Game3_Scores_Pct': round((stats['road_game_3']['scores_1plus'] / stats['road_game_3']['games'] * 100) if stats['road_game_3']['games'] > 0 else 0, 1),
                'RT_Game4+_Scores_Pct': round((stats['road_game_4plus']['scores_1plus'] / stats['road_game_4plus']['games'] * 100) if stats['road_game_4plus']['games'] > 0 else 0, 1),

                # Sample sizes for road trip games
                'RT_Game1_Count': stats['road_game_1']['games'],
                'RT_Game2_Count': stats['road_game_2']['games'],
                'RT_Game3_Count': stats['road_game_3']['games'],
                'RT_Game4+_Count': stats['road_game_4plus']['games'],
            }

            # Add recent form
            games = sorted(stats['games'], key=lambda x: x['date'], reverse=True)

            for period in [3, 5, 10]:
                recent = games[:period]
                if len(recent) >= period:
                    over_1_5_count = sum(1 for g in recent if g['over_1_5'])
                    scored_1_plus_count = sum(1 for g in recent if g['scored_1_plus'])

                    row[f'Last_{period}_Over_1.5_Pct'] = round((over_1_5_count / period * 100), 1)
                    row[f'Last_{period}_Team_Scores_1+_Pct'] = round((scored_1_plus_count / period * 100), 1)
                else:
                    row[f'Last_{period}_Over_1.5_Pct'] = None
                    row[f'Last_{period}_Team_Scores_1+_Pct'] = None

            csv_data.append(row)

        # Write CSV
        if csv_data:
            with open(output_file, 'w', newline='') as f:
                fieldnames = [
                    'Team', 'Total_Games',
                    'Season_Over_1.5_Pct', 'Season_Over_1.5_Count',
                    'Season_Team_Scores_1+_Pct', 'Season_Team_Scores_1+_Count',
                    'Season_Team_Allows_1+_Pct', 'Season_Team_Allows_1+_Count',
                    'Home_Games', 'Home_Over_1.5_Pct', 'Home_Team_Scores_1+_Pct', 'Home_Team_Allows_1+_Pct',
                    'Road_Games', 'Road_Over_1.5_Pct', 'Road_Team_Scores_1+_Pct', 'Road_Team_Allows_1+_Pct',
                    # Road trip fatigue stats
                    'RT_Game1_Allows_Pct', 'RT_Game2_Allows_Pct', 'RT_Game3_Allows_Pct', 'RT_Game4+_Allows_Pct',
                    'RT_Game1_Scores_Pct', 'RT_Game2_Scores_Pct', 'RT_Game3_Scores_Pct', 'RT_Game4+_Scores_Pct',
                    'RT_Game1_Count', 'RT_Game2_Count', 'RT_Game3_Count', 'RT_Game4+_Count',
                    # Recent form
                    'Last_3_Over_1.5_Pct', 'Last_3_Team_Scores_1+_Pct',
                    'Last_5_Over_1.5_Pct', 'Last_5_Team_Scores_1+_Pct',
                    'Last_10_Over_1.5_Pct', 'Last_10_Team_Scores_1+_Pct'
                ]

                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)

            print(f"✅ CSV report saved to: {output_file}")
        else:
            print(f"⚠️  No data to save to CSV")


def main():
    parser = argparse.ArgumentParser(description='Generate NHL first period daily report')
    parser.add_argument('--start-date', type=str, default='2024-10-01',
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, default=datetime.now().strftime('%Y-%m-%d'),
                       help='End date (YYYY-MM-DD)')
    parser.add_argument('--output', type=str,
                       default='/Users/dickgibbons/betting_data/nhl_1p_daily_report.json',
                       help='Output JSON file path')
    parser.add_argument('--csv', type=str,
                       default='/Users/dickgibbons/betting_data/nhl_1p_daily_report.csv',
                       help='Output CSV file path')

    args = parser.parse_args()

    analyzer = NHLFirstPeriodDailyReport()
    analyzer.analyze_season(args.start_date, args.end_date)
    analyzer.generate_report(args.output, args.csv)


if __name__ == "__main__":
    main()
