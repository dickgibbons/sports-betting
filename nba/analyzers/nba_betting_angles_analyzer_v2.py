#!/usr/bin/env python3
"""
NBA Betting Angles Analyzer v2 - WITH REAL SCHEDULE DATA
Uses ESPN API to build actual team schedules and detect real betting angles
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
import argparse


class NBABettingAnglesAnalyzer:
    """Comprehensive NBA betting angles analysis with REAL data"""

    def __init__(self):
        self.espn_api_base = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"

        # Track team schedules (like NHL analyzer)
        self.team_schedules = defaultdict(list)

        print("🏀 NBA Betting Angles Analyzer v2 initialized")

    def analyze_schedule_for_date(self, date_str: str):
        """Analyze all betting angles for a specific date"""

        print(f"\n{'='*80}")
        print(f"🔍 ANALYZING NBA BETTING ANGLES FOR {date_str}")
        print(f"{'='*80}\n")

        # Get today's games
        games = self.get_games_for_date(date_str)

        if not games:
            print(f"⚠️  No games scheduled for {date_str}")
            return

        print(f"📊 Found {len(games)} games to analyze\n")

        # Build recent schedule context (last 7 days)
        print(f"📅 Building schedule context (last 7 days)...")
        self._build_schedule_context(date_str)
        print(f"   ✅ Schedule context built for {len(self.team_schedules)} teams\n")

        # Analyze each game
        betting_opportunities = []

        for game in games:
            home_team = game.get('home_team', '')
            away_team = game.get('away_team', '')

            if not home_team or not away_team:
                continue

            game_analysis = {
                'date': date_str,
                'away_team': away_team,
                'home_team': home_team,
                'angles': []
            }

            # Angle 1: Back-to-Back Analysis (MASSIVE in NBA)
            b2b_angle = self._analyze_back_to_back(home_team, away_team, date_str)
            if b2b_angle:
                game_analysis['angles'].append(b2b_angle)

            # Angle 2: 3-in-4 / 4-in-5 Nights
            heavy_schedule = self._analyze_heavy_schedule(home_team, away_team, date_str)
            if heavy_schedule:
                game_analysis['angles'].append(heavy_schedule)

            # Angle 3: Rest Advantage
            rest_edge = self._analyze_rest_advantage(home_team, away_team, date_str)
            if rest_edge:
                game_analysis['angles'].append(rest_edge)

            # Angle 4: Road Trip Fatigue
            road_fatigue = self._analyze_road_trip_fatigue(home_team, away_team, date_str)
            if road_fatigue:
                game_analysis['angles'].append(road_fatigue)

            # Angle 5: Time Zone Travel
            timezone_edge = self._analyze_timezone_travel(home_team, away_team, date_str)
            if timezone_edge:
                game_analysis['angles'].append(timezone_edge)

            # Angle 6: Altitude Advantage (Denver)
            altitude_edge = self._analyze_altitude_advantage(home_team, away_team, date_str)
            if altitude_edge:
                game_analysis['angles'].append(altitude_edge)

            if game_analysis['angles']:
                betting_opportunities.append(game_analysis)

        # Display results
        self._display_betting_opportunities(betting_opportunities)

        return betting_opportunities

    def _build_schedule_context(self, target_date: str):
        """Build schedule context for last 7 days"""
        target = datetime.strptime(target_date, '%Y-%m-%d')

        for days_back in range(7, 0, -1):
            check_date = (target - timedelta(days=days_back)).strftime('%Y-%m-%d')
            games = self.get_games_for_date(check_date)

            for game in games:
                home_team = game.get('home_team', '')
                away_team = game.get('away_team', '')

                if home_team:
                    self.team_schedules[home_team].append({
                        'date': check_date,
                        'location': 'home',
                        'opponent': away_team
                    })

                if away_team:
                    self.team_schedules[away_team].append({
                        'date': check_date,
                        'location': 'away',
                        'opponent': home_team
                    })

    def _analyze_back_to_back(self, home_team: str, away_team: str, date_str: str) -> Optional[Dict]:
        """Analyze back-to-back situations with REAL data"""
        yesterday = (datetime.strptime(date_str, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')

        home_yesterday = [g for g in self.team_schedules[home_team] if g['date'] == yesterday]
        away_yesterday = [g for g in self.team_schedules[away_team] if g['date'] == yesterday]

        if away_yesterday:
            # Away team on B2B
            prev_game = away_yesterday[0]

            if prev_game['location'] == 'away':
                # ROAD → ROAD B2B - WORST SITUATION
                return {
                    'type': 'back_to_back',
                    'confidence': 'HIGH',
                    'bet': f'BET: {home_team} ML',
                    'reason': f'{away_team} on ROAD → ROAD B2B (38-40% win rate historically)',
                    'edge': '+10-12%',
                    'historical_win_rate': '58-60% for home team'
                }
            else:
                # HOME → ROAD B2B - Still bad
                return {
                    'type': 'back_to_back',
                    'confidence': 'MEDIUM-HIGH',
                    'bet': f'BET: {home_team} ML',
                    'reason': f'{away_team} on HOME → ROAD B2B',
                    'edge': '+8-10%',
                    'historical_win_rate': '56-58% for home team'
                }

        if home_yesterday:
            # Home team on B2B (less impactful but still notable)
            prev_game = home_yesterday[0]

            if prev_game['location'] == 'away':
                return {
                    'type': 'back_to_back',
                    'confidence': 'MEDIUM',
                    'bet': f'CONSIDER: {away_team} ML or Spread',
                    'reason': f'{home_team} on ROAD → HOME B2B (fatigue factor)',
                    'edge': '+4-6%',
                    'historical_win_rate': '52-54%'
                }

        return None

    def _analyze_heavy_schedule(self, home_team: str, away_team: str, date_str: str) -> Optional[Dict]:
        """Analyze 3-in-4 nights with REAL data"""
        target_date = datetime.strptime(date_str, '%Y-%m-%d')

        for team, team_name in [(home_team, 'home'), (away_team, 'away')]:
            # Count games in last 4 days (including today)
            recent_games = []
            for days_back in range(4):
                check_date = (target_date - timedelta(days=days_back)).strftime('%Y-%m-%d')
                games_on_date = [g for g in self.team_schedules[team] if g['date'] == check_date]
                recent_games.extend(games_on_date)

            # If today would be 3rd game in 4 nights
            if len(recent_games) >= 2:  # 2 in last 3 days + today = 3 in 4
                opponent = home_team if team == away_team else away_team

                return {
                    'type': 'heavy_schedule',
                    'confidence': 'MEDIUM-HIGH',
                    'bet': f'BET: {opponent} ML or Spread',
                    'reason': f'{team} playing 3rd game in 4 nights (heavy fatigue)',
                    'edge': '+8-12%'
                }

        return None

    def _analyze_rest_advantage(self, home_team: str, away_team: str, date_str: str) -> Optional[Dict]:
        """Analyze rest advantage with REAL data"""
        target_date = datetime.strptime(date_str, '%Y-%m-%d')

        def get_days_rest(team):
            yesterday = (target_date - timedelta(days=1)).strftime('%Y-%m-%d')
            two_days_ago = (target_date - timedelta(days=2)).strftime('%Y-%m-%d')
            three_days_ago = (target_date - timedelta(days=3)).strftime('%Y-%m-%d')

            if any(g['date'] == yesterday for g in self.team_schedules[team]):
                return 0  # B2B
            elif any(g['date'] == two_days_ago for g in self.team_schedules[team]):
                return 1
            elif any(g['date'] == three_days_ago for g in self.team_schedules[team]):
                return 2
            else:
                return 3  # 3+ days rest

        home_rest = get_days_rest(home_team)
        away_rest = get_days_rest(away_team)

        rest_diff = home_rest - away_rest

        # Significant rest advantage (2+ days difference)
        if rest_diff >= 2:
            return {
                'type': 'rest_advantage',
                'confidence': 'HIGH',
                'bet': f'BET: {home_team} ML',
                'reason': f'{home_team} has {home_rest} days rest vs {away_team} {away_rest} days',
                'edge': '+7-10%',
                'rest_differential': rest_diff
            }
        elif rest_diff <= -2:
            return {
                'type': 'rest_advantage',
                'confidence': 'HIGH',
                'bet': f'BET: {away_team} ML',
                'reason': f'{away_team} has {away_rest} days rest vs {home_team} {home_rest} days',
                'edge': '+7-10%',
                'rest_differential': abs(rest_diff)
            }

        return None

    def _analyze_road_trip_fatigue(self, home_team: str, away_team: str, date_str: str) -> Optional[Dict]:
        """Analyze road trip fatigue with REAL data"""
        # Count consecutive road games for away team
        away_schedule = sorted(self.team_schedules[away_team], key=lambda x: x['date'])

        consecutive_road = 0
        for game in reversed(away_schedule):
            if game['location'] == 'away':
                consecutive_road += 1
            else:
                break

        # 3rd+ game of road trip
        if consecutive_road >= 2:  # 2 previous + today = 3rd game
            return {
                'type': 'road_trip_fatigue',
                'confidence': 'MEDIUM',
                'bet': f'BET: {home_team} ML or Spread',
                'reason': f'{away_team} on {consecutive_road + 1}th game of road trip',
                'edge': '+6-9%',
                'road_games': consecutive_road + 1
            }

        return None

    def _analyze_timezone_travel(self, home_team: str, away_team: str, date_str: str) -> Optional[Dict]:
        """Analyze timezone travel impact"""
        # Timezone mapping
        eastern_teams = ['Celtics', '76ers', 'Knicks', 'Nets', 'Raptors',
                        'Heat', 'Magic', 'Hawks', 'Hornets', 'Wizards',
                        'Cavaliers', 'Pistons', 'Pacers', 'Bucks', 'Bulls']

        central_teams = ['Mavericks', 'Rockets', 'Spurs', 'Pelicans',
                        'Grizzlies', 'Timberwolves']

        pacific_teams = ['Lakers', 'Clippers', 'Warriors', 'Kings',
                        'Suns', 'Trail Blazers', 'Nuggets', 'Jazz']

        def get_timezone(team):
            if any(t in team for t in eastern_teams):
                return 'ET'
            elif any(t in team for t in central_teams):
                return 'CT'
            elif any(t in team for t in pacific_teams):
                return 'PT'
            return None

        home_tz = get_timezone(home_team)
        away_tz = get_timezone(away_team)

        # West coast team traveling East (3 hour jet lag)
        if away_tz == 'PT' and home_tz == 'ET':
            # Check if first game of road trip (worst jet lag)
            away_schedule = sorted(self.team_schedules[away_team], key=lambda x: x['date'])
            recent_away = [g for g in reversed(away_schedule) if g['location'] == 'away']

            if len(recent_away) == 0:  # First road game
                return {
                    'type': 'timezone_travel',
                    'confidence': 'MEDIUM',
                    'bet': f'BET: {home_team} ML',
                    'reason': f'{away_team} (West Coast) traveling East - 3hr jet lag, first road game',
                    'edge': '+4-6%'
                }

        return None

    def _analyze_altitude_advantage(self, home_team: str, away_team: str, date_str: str) -> Optional[Dict]:
        """Analyze Denver altitude advantage"""
        if 'Nuggets' in home_team or 'Denver' in home_team:
            return {
                'type': 'altitude_advantage',
                'confidence': 'MEDIUM',
                'bet': f'BET: {home_team} ML or Spread',
                'reason': 'Denver home at 5,280 ft altitude - opponents struggle with conditioning',
                'edge': '+4-7%'
            }

        return None

    def get_games_for_date(self, date_str: str) -> List[Dict]:
        """Get games for a specific date from ESPN API"""
        # Convert YYYY-MM-DD to YYYYMMDD for ESPN API
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        espn_date = date_obj.strftime('%Y%m%d')

        url = f"{self.espn_api_base}?dates={espn_date}"

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

                    for comp in competitors:
                        team_name = comp.get('team', {}).get('displayName', '')
                        if comp.get('homeAway') == 'home':
                            home_team = team_name
                        elif comp.get('homeAway') == 'away':
                            away_team = team_name

                    if home_team and away_team:
                        games.append({
                            'home_team': home_team,
                            'away_team': away_team,
                            'date': date_str
                        })

                return games

            return []
        except Exception as e:
            print(f"Error fetching games: {e}")
            return []

    def _display_betting_opportunities(self, opportunities: List[Dict]):
        """Display betting opportunities"""

        if not opportunities:
            print("\n⚠️  No strong betting angles found\n")
            return

        print(f"\n{'='*80}")
        print(f"🎯 BETTING OPPORTUNITIES FOUND: {len(opportunities)}")
        print(f"{'='*80}\n")

        high_confidence = []
        medium_confidence = []
        low_confidence = []

        for game in opportunities:
            away = game['away_team']
            home = game['home_team']

            print(f"🏀 {away} @ {home}")
            print(f"{'─'*80}")

            for angle in game['angles']:
                confidence = angle['confidence']

                if confidence == 'HIGH':
                    high_confidence.append((game, angle))
                    marker = "🔥"
                elif confidence in ['MEDIUM-HIGH', 'MEDIUM']:
                    medium_confidence.append((game, angle))
                    marker = "✅"
                else:
                    low_confidence.append((game, angle))
                    marker = "💡"

                print(f"{marker} {angle['bet']}")
                print(f"   Type: {angle['type'].upper()}")
                print(f"   Confidence: {confidence}")
                print(f"   Reason: {angle['reason']}")
                print(f"   Expected Edge: {angle['edge']}")

                if 'historical_win_rate' in angle:
                    print(f"   Historical Win Rate: {angle['historical_win_rate']}")

                print()

            print()

        # Summary
        print(f"{'='*80}")
        print(f"📊 SUMMARY")
        print(f"{'='*80}")
        print(f"🔥 High Confidence Angles: {len(high_confidence)}")
        print(f"✅ Medium Confidence Angles: {len(medium_confidence)}")
        print(f"💡 Low Confidence Angles: {len(low_confidence)}")
        print(f"\n💰 KEY INSIGHT: NBA B2B and rest advantages are BIGGER than NHL")
        print(f"   - B2B ROAD → ROAD teams win only 38-40%")
        print(f"   - Home teams facing B2B opponents win 58-60%")
        print(f"   - 3+ days rest vs 1 day = +7-10% edge")
        print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(description='Analyze NBA betting angles with REAL data')
    parser.add_argument('--date', type=str,
                       help='Date in YYYY-MM-DD format (default: today)')

    args = parser.parse_args()

    if args.date:
        date_str = args.date
    else:
        date_str = datetime.now().strftime('%Y-%m-%d')

    analyzer = NBABettingAnglesAnalyzer()
    opportunities = analyzer.analyze_schedule_for_date(date_str)


if __name__ == "__main__":
    main()
