#!/usr/bin/env python3
"""
NBA Road Trip Backtest
Analyzes how NBA teams perform on long road trips (3+, 4+, 5+ games)
Specifically: Does the LAST game of a road trip show different patterns?

Note: NBA road trips should show BIGGER fatigue impact than NHL due to more running
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict
import argparse


class NBARoadTripBacktest:
    """Backtest NBA road trip performance patterns"""

    def __init__(self):
        self.espn_api_base = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"

        # Track results by road trip game number
        self.results = {
            '3rd_of_3': {'wins': 0, 'games': 0},
            '4th_of_4': {'wins': 0, 'games': 0},
            '5th_of_5': {'wins': 0, 'games': 0},
            '3rd_of_4+': {'wins': 0, 'games': 0},
            '4th_of_5+': {'wins': 0, 'games': 0},
            'any_3rd+': {'wins': 0, 'games': 0},
            'any_4th+': {'wins': 0, 'games': 0},
            'any_5th+': {'wins': 0, 'games': 0},
        }

        # Detailed game log
        self.detailed_games = []

        print("🏀 NBA Road Trip Backtest initialized")

    def get_games_for_date_range(self, start_date: str, end_date: str):
        """Get all games between two dates"""
        print(f"\n📅 Fetching games from {start_date} to {end_date}...")

        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        all_games = []
        current_date = start
        days_processed = 0

        while current_date <= end:
            date_str = current_date.strftime('%Y%m%d')  # ESPN format

            try:
                url = f"{self.espn_api_base}?dates={date_str}"
                response = requests.get(url, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    events = data.get('events', [])

                    for event in events:
                        if not event.get('competitions'):
                            continue

                        competition = event['competitions'][0]
                        competitors = competition.get('competitors', [])

                        if len(competitors) < 2:
                            continue

                        # Check if game is completed
                        status = competition.get('status', {}).get('type', {}).get('name', '')
                        if status != 'STATUS_FINAL':
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
                            all_games.append({
                                'date': current_date.strftime('%Y-%m-%d'),
                                'home_team': home_team,
                                'away_team': away_team,
                                'home_score': home_score,
                                'away_score': away_score
                            })

            except Exception as e:
                pass

            current_date += timedelta(days=1)
            days_processed += 1

            # Progress update every 30 days
            if days_processed % 30 == 0:
                print(f"   Processed {days_processed} days, found {len(all_games)} completed games...")

        print(f"   ✅ Found {len(all_games)} completed NBA games")
        return all_games

    def build_road_trip_context(self, all_games: List[Dict]):
        """Build road trip context for each game"""

        print(f"\n🔍 Analyzing NBA road trip patterns...")

        # Sort games by date
        all_games.sort(key=lambda x: x['date'])

        # Track each team's recent games
        team_schedules = defaultdict(list)

        for game in all_games:
            date = game['date']
            home_team = game['home_team']
            away_team = game['away_team']

            # Check away team's road trip status
            away_schedule = team_schedules[away_team]

            # Count consecutive road games before this one
            consecutive_road = 0
            for prev_game in reversed(away_schedule):
                if prev_game['location'] == 'away':
                    consecutive_road += 1
                else:
                    break

            road_trip_game_num = consecutive_road + 1  # +1 for current game

            # Check if this is LAST game of road trip
            is_last_of_trip = self._is_last_road_game(away_team, date, all_games)

            # Record result
            away_won = game['away_score'] > game['home_score']

            # Track results by road trip length
            if road_trip_game_num >= 3:
                self.results['any_3rd+']['games'] += 1
                if away_won:
                    self.results['any_3rd+']['wins'] += 1

                # If it's the last game of a 3-game trip
                if is_last_of_trip and consecutive_road == 2:
                    self.results['3rd_of_3']['games'] += 1
                    if away_won:
                        self.results['3rd_of_3']['wins'] += 1

                # If it's 3rd game but trip continues
                if not is_last_of_trip and consecutive_road == 2:
                    self.results['3rd_of_4+']['games'] += 1
                    if away_won:
                        self.results['3rd_of_4+']['wins'] += 1

            if road_trip_game_num >= 4:
                self.results['any_4th+']['games'] += 1
                if away_won:
                    self.results['any_4th+']['wins'] += 1

                # If it's the last game of a 4-game trip
                if is_last_of_trip and consecutive_road == 3:
                    self.results['4th_of_4']['games'] += 1
                    if away_won:
                        self.results['4th_of_4']['wins'] += 1

                # If it's 4th game but trip continues
                if not is_last_of_trip and consecutive_road == 3:
                    self.results['4th_of_5+']['games'] += 1
                    if away_won:
                        self.results['4th_of_5+']['wins'] += 1

            if road_trip_game_num >= 5:
                self.results['any_5th+']['games'] += 1
                if away_won:
                    self.results['any_5th+']['wins'] += 1

                # If it's the last game of a 5-game trip
                if is_last_of_trip and consecutive_road == 4:
                    self.results['5th_of_5']['games'] += 1
                    if away_won:
                        self.results['5th_of_5']['wins'] += 1

            # Store detailed game info
            if road_trip_game_num >= 3:
                self.detailed_games.append({
                    'date': date,
                    'away_team': away_team,
                    'home_team': home_team,
                    'road_game_num': road_trip_game_num,
                    'is_last_of_trip': is_last_of_trip,
                    'away_won': away_won,
                    'score': f"{game['away_score']}-{game['home_score']}"
                })

            # Add this game to team's schedule
            team_schedules[home_team].append({
                'date': date,
                'location': 'home',
                'opponent': away_team
            })

            team_schedules[away_team].append({
                'date': date,
                'location': 'away',
                'opponent': home_team
            })

        print(f"   ✅ Analyzed {len(self.detailed_games)} road trip games (3rd+ game)")

    def _is_last_road_game(self, team: str, current_date: str, all_games: List[Dict]) -> bool:
        """Check if this is the team's last road game before returning home"""

        current = datetime.strptime(current_date, '%Y-%m-%d')

        # Look at next 3 days for this team
        for days_ahead in range(1, 4):
            check_date = (current + timedelta(days=days_ahead)).strftime('%Y-%m-%d')

            # Find team's next game
            for game in all_games:
                if game['date'] == check_date:
                    if game['home_team'] == team:
                        # Next game is at home - this was last road game
                        return True
                    elif game['away_team'] == team:
                        # Next game is also away - road trip continues
                        return False

        # No game found in next 3 days - assume trip ended
        return True

    def display_results(self):
        """Display backtest results"""

        print(f"\n{'='*80}")
        print(f"📊 NBA ROAD TRIP BACKTEST RESULTS")
        print(f"{'='*80}\n")

        print(f"🎯 KEY QUESTION: Does performance differ on LAST game of road trip?")
        print(f"💡 NOTE: NBA fatigue should be BIGGER than NHL (more running)\n")

        # Overall road trip performance
        print(f"{'─'*80}")
        print(f"📈 OVERALL ROAD TRIP PERFORMANCE:")
        print(f"{'─'*80}")

        for key in ['any_3rd+', 'any_4th+', 'any_5th+']:
            data = self.results[key]
            if data['games'] > 0:
                win_rate = (data['wins'] / data['games']) * 100
                vs_expected = win_rate - 50

                label = {
                    'any_3rd+': '3rd+ Game of Road Trip',
                    'any_4th+': '4th+ Game of Road Trip',
                    'any_5th+': '5th+ Game of Road Trip'
                }[key]

                print(f"\n{label}:")
                print(f"   Games: {data['games']}")
                print(f"   Away Wins: {data['wins']}")
                print(f"   Win Rate: {win_rate:.1f}%")
                print(f"   vs Expected 50%: {vs_expected:+.1f}%")

        # Last game vs continuing trip
        print(f"\n{'─'*80}")
        print(f"🔥 LAST GAME OF TRIP vs TRIP CONTINUES:")
        print(f"{'─'*80}")

        # 3-game trips
        last_3 = self.results['3rd_of_3']
        cont_3 = self.results['3rd_of_4+']

        if last_3['games'] > 0:
            wr_last_3 = (last_3['wins'] / last_3['games']) * 100
            print(f"\n3rd Game (LAST of 3-game trip):")
            print(f"   Games: {last_3['games']}")
            print(f"   Win Rate: {wr_last_3:.1f}%")
            print(f"   vs Expected: {wr_last_3 - 50:+.1f}%")

        if cont_3['games'] > 0:
            wr_cont_3 = (cont_3['wins'] / cont_3['games']) * 100
            print(f"\n3rd Game (trip continues to 4+):")
            print(f"   Games: {cont_3['games']}")
            print(f"   Win Rate: {wr_cont_3:.1f}%")
            print(f"   vs Expected: {wr_cont_3 - 50:+.1f}%")

        # 4-game trips
        last_4 = self.results['4th_of_4']
        cont_4 = self.results['4th_of_5+']

        if last_4['games'] > 0:
            wr_last_4 = (last_4['wins'] / last_4['games']) * 100
            print(f"\n4th Game (LAST of 4-game trip):")
            print(f"   Games: {last_4['games']}")
            print(f"   Win Rate: {wr_last_4:.1f}%")
            print(f"   vs Expected: {wr_last_4 - 50:+.1f}%")

        if cont_4['games'] > 0:
            wr_cont_4 = (cont_4['wins'] / cont_4['games']) * 100
            print(f"\n4th Game (trip continues to 5+):")
            print(f"   Games: {cont_4['games']}")
            print(f"   Win Rate: {wr_cont_4:.1f}%")
            print(f"   vs Expected: {wr_cont_4 - 50:+.1f}%")

        # 5-game trips
        last_5 = self.results['5th_of_5']

        if last_5['games'] > 0:
            wr_last_5 = (last_5['wins'] / last_5['games']) * 100
            print(f"\n5th Game (LAST of 5-game trip):")
            print(f"   Games: {last_5['games']}")
            print(f"   Win Rate: {wr_last_5:.1f}%")
            print(f"   vs Expected: {wr_last_5 - 50:+.1f}%")

        # Betting recommendation
        print(f"\n{'='*80}")
        print(f"💰 BETTING RECOMMENDATIONS:")
        print(f"{'='*80}")

        any_4th = self.results['any_4th+']
        if any_4th['games'] > 0:
            wr = (any_4th['wins'] / any_4th['games']) * 100
            home_wr = 100 - wr

            if home_wr > 52.4:  # Breakeven at -110 odds
                edge = home_wr - 50
                print(f"\n✅ BET ON HOME TEAM when opponent is on 4th+ road game")
                print(f"   Historical home win rate: {home_wr:.1f}%")
                print(f"   Edge: +{edge:.1f}%")
                print(f"   Sample size: {any_4th['games']} games")
            else:
                print(f"\n⚠️  No significant edge found on 4th+ road game")

        print(f"\n{'='*80}\n")

    def run_backtest(self, start_date: str, end_date: str):
        """Run backtest for date range"""

        print(f"\n{'='*80}")
        print(f"🏀 NBA ROAD TRIP BACKTEST")
        print(f"{'='*80}")
        print(f"Period: {start_date} to {end_date}")
        print(f"{'='*80}")

        # Get all games for period
        all_games = self.get_games_for_date_range(start_date, end_date)

        # Analyze road trip patterns
        self.build_road_trip_context(all_games)

        # Display results
        self.display_results()


def main():
    parser = argparse.ArgumentParser(description='Backtest NBA road trip patterns')
    parser.add_argument('--start', default='2023-10-01', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', default='2024-04-30', help='End date (YYYY-MM-DD)')

    args = parser.parse_args()

    backtester = NBARoadTripBacktest()
    backtester.run_backtest(args.start, args.end)


if __name__ == "__main__":
    main()
