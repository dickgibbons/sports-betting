#!/usr/bin/env python3
"""
Team-Level Situation Profiler
Analyzes how individual teams perform in specific situations:
- Back-to-back games (HOME→ROAD)
- Road trip fatigue (4th+ game)
- 3-in-4 nights
- Rest advantages

Key insight: Some teams might OUTPERFORM league averages in certain spots,
while others underperform. This allows for team-specific angle weighting.
"""
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict


class TeamSituationProfiler:
    """Profile team-specific performance in situational spots"""

    def __init__(self, sport: str = 'nhl'):
        self.sport = sport.upper()

        if sport.upper() == 'NHL':
            self.api_base = "https://api-web.nhle.com/v1"
        elif sport.upper() == 'NBA':
            self.api_base = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"

        # Team-level statistics
        self.team_stats = defaultdict(lambda: {
            'back_to_back_home_to_road': {'games': 0, 'wins': 0, 'losses': 0},
            'road_trip_4th_plus': {'games': 0, 'wins': 0, 'losses': 0},
            'three_in_four': {'games': 0, 'wins': 0, 'losses': 0},
            'rest_advantage_2plus': {'games': 0, 'wins': 0, 'losses': 0},
            'overall': {'games': 0, 'wins': 0, 'losses': 0}
        })

        print(f"🔍 {self.sport} Team Situation Profiler initialized")

    def analyze_season(self, start_date: str, end_date: str):
        """Analyze entire season of data to build team profiles"""

        print(f"\n{'='*80}")
        print(f"📊 BUILDING TEAM PROFILES: {start_date} to {end_date}")
        print(f"{'='*80}\n")

        current = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        games_analyzed = 0

        # Build schedule history
        team_schedules = defaultdict(list)

        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            games = self._get_games_for_date(date_str)

            if games:
                print(f"📅 Processing {date_str}: {len(games)} games")

                for game in games:
                    games_analyzed += 1

                    if self.sport == 'NHL':
                        home_team = game.get('homeTeam', {}).get('abbrev', '')
                        away_team = game.get('awayTeam', {}).get('abbrev', '')
                        home_score = game.get('homeTeam', {}).get('score', 0)
                        away_score = game.get('awayTeam', {}).get('score', 0)
                    else:  # NBA
                        home_team = game.get('home_team', '')
                        away_team = game.get('away_team', '')
                        home_score = game.get('home_score', 0)
                        away_score = game.get('away_score', 0)

                    if not home_team or not away_team:
                        continue

                    # Determine winner
                    home_won = home_score > away_score

                    # Analyze situational angles for away team
                    self._check_back_to_back(away_team, date_str, team_schedules, not home_won)
                    self._check_road_trip_fatigue(away_team, date_str, team_schedules, not home_won)
                    self._check_three_in_four(away_team, date_str, team_schedules, not home_won)

                    # Update schedules
                    team_schedules[home_team].append({
                        'date': date_str,
                        'location': 'home',
                        'opponent': away_team,
                        'won': home_won
                    })

                    team_schedules[away_team].append({
                        'date': date_str,
                        'location': 'away',
                        'opponent': home_team,
                        'won': not home_won
                    })

                    # Overall stats
                    self.team_stats[home_team]['overall']['games'] += 1
                    self.team_stats[away_team]['overall']['games'] += 1

                    if home_won:
                        self.team_stats[home_team]['overall']['wins'] += 1
                        self.team_stats[away_team]['overall']['losses'] += 1
                    else:
                        self.team_stats[home_team]['overall']['losses'] += 1
                        self.team_stats[away_team]['overall']['wins'] += 1

            current += timedelta(days=1)

        print(f"\n✅ Analysis complete: {games_analyzed} games processed\n")

        return self.team_stats

    def _check_back_to_back(self, team: str, date_str: str, schedules: Dict, team_won: bool):
        """Check if team is on HOME→ROAD back-to-back"""
        yesterday = (datetime.strptime(date_str, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')

        yesterday_games = [g for g in schedules[team] if g['date'] == yesterday]

        if yesterday_games and yesterday_games[0]['location'] == 'home':
            # HOME → ROAD B2B detected!
            self.team_stats[team]['back_to_back_home_to_road']['games'] += 1
            if team_won:
                self.team_stats[team]['back_to_back_home_to_road']['wins'] += 1
            else:
                self.team_stats[team]['back_to_back_home_to_road']['losses'] += 1

    def _check_road_trip_fatigue(self, team: str, date_str: str, schedules: Dict, team_won: bool):
        """Check if team is on 4th+ game of road trip"""
        team_schedule = sorted(schedules[team], key=lambda x: x['date'])

        consecutive_road = 0
        for game in reversed(team_schedule):
            if game['location'] == 'away':
                consecutive_road += 1
            else:
                break

        if consecutive_road >= 3:  # 3 previous + today = 4th game
            self.team_stats[team]['road_trip_4th_plus']['games'] += 1
            if team_won:
                self.team_stats[team]['road_trip_4th_plus']['wins'] += 1
            else:
                self.team_stats[team]['road_trip_4th_plus']['losses'] += 1

    def _check_three_in_four(self, team: str, date_str: str, schedules: Dict, team_won: bool):
        """Check if team is playing 3rd game in 4 nights"""
        target_date = datetime.strptime(date_str, '%Y-%m-%d')

        recent_games = []
        for days_back in range(1, 4):
            check_date = (target_date - timedelta(days=days_back)).strftime('%Y-%m-%d')
            games_on_date = [g for g in schedules[team] if g['date'] == check_date]
            recent_games.extend(games_on_date)

        if len(recent_games) >= 2:  # 2 in last 3 days + today = 3 in 4
            self.team_stats[team]['three_in_four']['games'] += 1
            if team_won:
                self.team_stats[team]['three_in_four']['wins'] += 1
            else:
                self.team_stats[team]['three_in_four']['losses'] += 1

    def _get_games_for_date(self, date_str: str) -> List[Dict]:
        """Get games for specific date"""
        if self.sport == 'NHL':
            url = f"{self.api_base}/schedule/{date_str}"

            try:
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    game_week = data.get('gameWeek', [])

                    for day in game_week:
                        if day.get('date') == date_str:
                            return day.get('games', [])

                    return []
                return []
            except Exception as e:
                return []

        elif self.sport == 'NBA':
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            espn_date = date_obj.strftime('%Y%m%d')
            url = f"{self.api_base}?dates={espn_date}"

            try:
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    events = data.get('events', [])

                    games = []
                    for event in events:
                        if not event.get('competitions'):
                            continue

                        competition = event['competitions'][0]
                        competitors = competition.get('competitors', [])

                        if len(competitors) < 2:
                            continue

                        home_team = None
                        away_team = None
                        home_score = 0
                        away_score = 0

                        for comp in competitors:
                            team_name = comp.get('team', {}).get('displayName', '')
                            score = int(comp.get('score', 0))

                            if comp.get('homeAway') == 'home':
                                home_team = team_name
                                home_score = score
                            elif comp.get('homeAway') == 'away':
                                away_team = team_name
                                away_score = score

                        if home_team and away_team:
                            games.append({
                                'home_team': home_team,
                                'away_team': away_team,
                                'home_score': home_score,
                                'away_score': away_score,
                                'date': date_str
                            })

                    return games

                return []
            except Exception as e:
                return []

        return []

    def generate_team_report(self, output_file: str = None):
        """Generate comprehensive team profiling report"""

        print(f"\n{'='*80}")
        print(f"📊 TEAM SITUATION PERFORMANCE PROFILES")
        print(f"{'='*80}\n")

        # Calculate league averages
        league_averages = {
            'back_to_back_home_to_road': {'games': 0, 'wins': 0},
            'road_trip_4th_plus': {'games': 0, 'wins': 0},
            'three_in_four': {'games': 0, 'wins': 0}
        }

        for team, stats in self.team_stats.items():
            for situation in ['back_to_back_home_to_road', 'road_trip_4th_plus', 'three_in_four']:
                league_averages[situation]['games'] += stats[situation]['games']
                league_averages[situation]['wins'] += stats[situation]['wins']

        # Print league averages
        print("🌐 LEAGUE AVERAGES:")
        print("─" * 80)
        for situation, totals in league_averages.items():
            if totals['games'] > 0:
                win_rate = (totals['wins'] / totals['games']) * 100
                print(f"{situation}: {totals['wins']}-{totals['games'] - totals['wins']} ({win_rate:.1f}% win rate, {totals['games']} games)")

        print(f"\n{'='*80}")
        print("🔍 TEAM-SPECIFIC PERFORMANCE (vs League Average)")
        print("="*80)

        # Analyze each team
        team_insights = []

        for team in sorted(self.team_stats.keys()):
            stats = self.team_stats[team]
            team_analysis = {'team': team, 'situations': {}}

            for situation in ['back_to_back_home_to_road', 'road_trip_4th_plus', 'three_in_four']:
                team_data = stats[situation]

                if team_data['games'] >= 5:  # Minimum sample size
                    team_win_rate = (team_data['wins'] / team_data['games']) * 100
                    league_win_rate = (league_averages[situation]['wins'] / league_averages[situation]['games']) * 100

                    differential = team_win_rate - league_win_rate

                    team_analysis['situations'][situation] = {
                        'win_rate': team_win_rate,
                        'games': team_data['games'],
                        'differential': differential,
                        'record': f"{team_data['wins']}-{team_data['losses']}"
                    }

            if team_analysis['situations']:
                team_insights.append(team_analysis)

        # Print top performers and underperformers
        for situation in ['back_to_back_home_to_road', 'road_trip_4th_plus']:
            print(f"\n📈 {situation.upper().replace('_', ' ')}:")
            print("─" * 80)

            # Sort by differential
            situation_data = [(t['team'], t['situations'].get(situation, {})) for t in team_insights if situation in t['situations']]
            situation_data.sort(key=lambda x: x[1].get('differential', 0), reverse=True)

            # Top 5 performers
            print("\n🔥 TOP PERFORMERS (Better than league average):")
            for team, data in situation_data[:5]:
                if data.get('differential', 0) > 0:
                    print(f"   {team}: {data['record']} ({data['win_rate']:.1f}%, {data['differential']:+.1f}% vs league avg, {data['games']} games)")

            # Bottom 5 performers
            print("\n❌ UNDERPERFORMERS (Worse than league average):")
            for team, data in situation_data[-5:]:
                if data.get('differential', 0) < 0:
                    print(f"   {team}: {data['record']} ({data['win_rate']:.1f}%, {data['differential']:+.1f}% vs league avg, {data['games']} games)")

        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump({
                    'league_averages': league_averages,
                    'team_stats': {team: dict(stats) for team, stats in self.team_stats.items()},
                    'team_insights': team_insights
                }, f, indent=2)

            print(f"\n💾 Team profiles saved to: {output_file}")

        return team_insights


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Analyze team-specific situation performance')
    parser.add_argument('--sport', type=str, default='NHL', choices=['NHL', 'NBA'],
                       help='Sport to analyze')
    parser.add_argument('--start-date', type=str, required=True,
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, required=True,
                       help='End date (YYYY-MM-DD)')
    parser.add_argument('--output', type=str,
                       help='Output file for team profiles (JSON)')

    args = parser.parse_args()

    profiler = TeamSituationProfiler(sport=args.sport)
    profiler.analyze_season(args.start_date, args.end_date)

    output_file = args.output or f"/Users/dickgibbons/AI Projects/sports-betting/data/team_profiles_{args.sport.lower()}_{args.start_date}_{args.end_date}.json"
    profiler.generate_team_report(output_file)


if __name__ == "__main__":
    main()
