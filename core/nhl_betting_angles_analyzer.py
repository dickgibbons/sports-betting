#!/usr/bin/env python3
"""
NHL Betting Angles Analyzer
Identifies profitable betting situations across multiple dimensions:
- Schedule spots (B2B, 3-in-4, road trips)
- Rest advantages
- Travel/timezone impacts
- Situational edges (division games, revenge games)
- Statistical mismatches
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
import argparse
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from team_weights_loader import TeamWeightsLoader


class NHLBettingAnglesAnalyzer:
    """Comprehensive betting angles analysis"""

    def __init__(self):
        self.nhl_api_base = "https://api-web.nhle.com/v1"

        # Track team schedules
        self.team_schedules = defaultdict(list)

        # Analytics
        self.angles = {
            'back_to_back': [],
            'three_in_four': [],
            'rest_advantage': [],
            'road_trip_fatigue': [],
            'home_stand_length': [],
            'timezone_travel': [],
            'division_games': [],
            'revenge_games': []
        }

        # Team-specific weights
        try:
            self.team_weights = TeamWeightsLoader('NHL')
        except Exception as e:
            print(f"⚠️  Could not load team weights: {e}")
            self.team_weights = None

        print("🏒 NHL Betting Angles Analyzer initialized")

    def analyze_schedule_for_date(self, date_str: str):
        """Analyze all betting angles for a specific date"""

        print(f"\n{'='*80}")
        print(f"🔍 ANALYZING BETTING ANGLES FOR {date_str}")
        print(f"{'='*80}\n")

        # Get today's games
        games = self.get_games_for_date(date_str)

        if not games:
            print(f"⚠️  No games scheduled for {date_str}")
            return

        print(f"📊 Found {len(games)} games to analyze\n")

        # Build recent schedule context (last 7 days)
        self._build_schedule_context(date_str)

        # Analyze each game
        betting_opportunities = []

        for game in games:
            home_team = game.get('homeTeam', {})
            away_team = game.get('awayTeam', {})

            home_abbr = home_team.get('abbrev', '')
            away_abbr = away_team.get('abbrev', '')

            if not home_abbr or not away_abbr:
                continue

            game_analysis = {
                'date': date_str,
                'away_team': away_abbr,
                'home_team': home_abbr,
                'angles': []
            }

            # Angle 1: Back-to-Back Analysis
            b2b_angle = self._analyze_back_to_back(home_abbr, away_abbr, date_str)
            if b2b_angle:
                game_analysis['angles'].append(b2b_angle)

            # Angle 2: 3-in-4 Nights Analysis
            three_in_four = self._analyze_three_in_four(home_abbr, away_abbr, date_str)
            if three_in_four:
                game_analysis['angles'].append(three_in_four)

            # Angle 3: Rest Advantage
            rest_edge = self._analyze_rest_advantage(home_abbr, away_abbr, date_str)
            if rest_edge:
                game_analysis['angles'].append(rest_edge)

            # Angle 4: Road Trip Fatigue
            road_fatigue = self._analyze_road_trip_fatigue(home_abbr, away_abbr, date_str)
            if road_fatigue:
                game_analysis['angles'].append(road_fatigue)

            # Angle 5: Time Zone Travel
            timezone_edge = self._analyze_timezone_travel(home_abbr, away_abbr, date_str)
            if timezone_edge:
                game_analysis['angles'].append(timezone_edge)

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
                home_team = game.get('homeTeam', {}).get('abbrev', '')
                away_team = game.get('awayTeam', {}).get('abbrev', '')

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
        """Analyze back-to-back situations - ONLY HOME→ROAD (80% win rate)

        Data shows ONLY HOME→ROAD B2B is profitable:
        - HOME→ROAD: 80% win rate, +$372 profit, +37% ROI ✅
        - ROAD→ROAD: 40% win rate, -$446 profit, -37% ROI ❌
        - ROAD→HOME: 33% win rate, -$281 profit, -34% ROI ❌
        """
        yesterday = (datetime.strptime(date_str, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')

        away_yesterday = [g for g in self.team_schedules[away_team] if g['date'] == yesterday]

        if away_yesterday:
            # Away team on B2B - check if it's HOME→ROAD
            prev_game = away_yesterday[0]

            if prev_game['location'] == 'home':
                # HOME → ROAD B2B - THE ONLY PROFITABLE VARIANT!
                # Team played at home yesterday, traveling to away game today
                # Maximum fatigue: travel + hotel + unfamiliar arena

                # Apply team-specific weights
                if self.team_weights:
                    should_filter, reason = self.team_weights.should_filter_angle(away_team, 'back_to_back')
                    if should_filter:
                        # Team performs WELL on B2B - don't bet against them
                        return None

                    # Get team multiplier
                    weight_info = self.team_weights.get_team_multiplier(away_team, 'back_to_back')
                    base_edge = 12.0
                    adjusted_edge = weight_info.get('multiplier', 1.0) * base_edge

                    # Adjust confidence based on team performance
                    confidence = 'HIGH'  # Base confidence
                    if weight_info.get('confidence_boost'):
                        if 'ELITE' in weight_info['confidence_boost']:
                            confidence = 'ELITE'

                    reason_text = f'{away_team} on HOME → ROAD B2B (80% win rate historical)'
                    if weight_info.get('action') in ['AMPLIFY', 'REDUCE']:
                        team_record = weight_info.get('team_record', '')
                        reason_text += f" | {away_team} is {team_record} in B2B situations"

                    return {
                        'type': 'back_to_back',
                        'confidence': confidence,
                        'bet': f'BET: {home_team} ML',
                        'reason': reason_text,
                        'edge': f'+{adjusted_edge:.1f}%',
                        'historical_win_rate': '80%',
                        'team_multiplier': weight_info.get('multiplier', 1.0)
                    }
                else:
                    # No team weights - use default
                    return {
                        'type': 'back_to_back',
                        'confidence': 'HIGH',
                        'bet': f'BET: {home_team} ML',
                        'reason': f'{away_team} on HOME → ROAD B2B (80% win rate historical)',
                        'edge': '+12%',
                        'historical_win_rate': '80%'
                    }
            # Filter out ROAD→ROAD (not profitable)

        # Filter out ROAD→HOME (not profitable)
        return None

    def _analyze_three_in_four(self, home_team: str, away_team: str, date_str: str) -> Optional[Dict]:
        """Analyze 3 games in 4 nights situations"""
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
                    'type': 'three_in_four',
                    'confidence': 'MEDIUM-HIGH',
                    'bet': f'BET: {opponent} ML',
                    'reason': f'{team} playing 3rd game in 4 nights (heavy fatigue)',
                    'edge': '+5-8%',
                    'historical_win_rate': '54-57%'
                }

        return None

    def _analyze_rest_advantage(self, home_team: str, away_team: str, date_str: str) -> Optional[Dict]:
        """Analyze rest advantage (3+ days vs 1 day)"""
        target_date = datetime.strptime(date_str, '%Y-%m-%d')

        # Calculate days of rest for each team
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
                'confidence': 'MEDIUM',
                'bet': f'BET: {home_team} ML',
                'reason': f'{home_team} has {home_rest} days rest vs {away_team} {away_rest} days',
                'edge': '+4-6%',
                'rest_differential': rest_diff
            }
        elif rest_diff <= -2:
            return {
                'type': 'rest_advantage',
                'confidence': 'MEDIUM',
                'bet': f'BET: {away_team} ML',
                'reason': f'{away_team} has {away_rest} days rest vs {home_team} {home_rest} days',
                'edge': '+4-6%',
                'rest_differential': abs(rest_diff)
            }

        return None

    def _analyze_road_trip_fatigue(self, home_team: str, away_team: str, date_str: str) -> Optional[Dict]:
        """Analyze fatigue from long road trips"""
        # Count consecutive road games for away team
        away_schedule = sorted(self.team_schedules[away_team], key=lambda x: x['date'])

        consecutive_road = 0
        for game in reversed(away_schedule):
            if game['location'] == 'away':
                consecutive_road += 1
            else:
                break

        # 4th+ game of road trip (where real edge exists)
        if consecutive_road >= 3:  # 3 previous + today = 4th game
            # Apply team-specific weights
            if self.team_weights:
                should_filter, reason = self.team_weights.should_filter_angle(away_team, 'road_trip_fatigue')
                if should_filter:
                    # Team performs WELL on road trips - don't bet against them
                    # E.g. Chicago (66.7%, 4-2) handles fatigue better than average
                    return None

                # Get team multiplier
                weight_info = self.team_weights.get_team_multiplier(away_team, 'road_trip_fatigue')
                base_edge = 7.4
                adjusted_edge = weight_info.get('multiplier', 1.0) * base_edge

                # Adjust confidence based on team performance
                confidence = 'HIGH'  # Base confidence
                if weight_info.get('confidence_boost'):
                    if 'ELITE' in weight_info['confidence_boost']:
                        confidence = 'ELITE'

                reason_text = f'{away_team} on {consecutive_road + 1}th game of road trip'
                if weight_info.get('action') in ['AMPLIFY', 'REDUCE']:
                    team_record = weight_info.get('team_record', '')
                    reason_text += f" | {away_team} is {team_record} on 4th+ road games"

                return {
                    'type': 'road_trip_fatigue',
                    'confidence': confidence,
                    'bet': f'BET: {home_team} ML or Puck Line',
                    'reason': reason_text,
                    'edge': f'+{adjusted_edge:.1f}%',
                    'road_games': consecutive_road + 1,
                    'team_multiplier': weight_info.get('multiplier', 1.0)
                }
            else:
                # No team weights - use default
                return {
                    'type': 'road_trip_fatigue',
                    'confidence': 'HIGH',
                    'bet': f'BET: {home_team} ML or Puck Line',
                    'reason': f'{away_team} on {consecutive_road + 1}th game of road trip',
                    'edge': '+7.4%',
                    'road_games': consecutive_road + 1
                }

        return None

    def _analyze_timezone_travel(self, home_team: str, away_team: str, date_str: str) -> Optional[Dict]:
        """Analyze timezone travel impact"""
        # Timezone mapping (simplified)
        eastern_teams = ['BOS', 'BUF', 'DET', 'FLA', 'MTL', 'OTT', 'TBL', 'TOR',
                        'CAR', 'CBJ', 'NJD', 'NYI', 'NYR', 'PHI', 'PIT', 'WSH']
        central_teams = ['CHI', 'COL', 'DAL', 'MIN', 'NSH', 'STL', 'WPG', 'ARI']
        pacific_teams = ['ANA', 'CGY', 'EDM', 'LAK', 'SJS', 'SEA', 'VAN', 'VGK']

        def get_timezone(team):
            if team in eastern_teams:
                return 'ET'
            elif team in central_teams:
                return 'CT'
            elif team in pacific_teams:
                return 'PT'
            return None

        home_tz = get_timezone(home_team)
        away_tz = get_timezone(away_team)

        # West coast team traveling East (jet lag disadvantage)
        if away_tz == 'PT' and home_tz == 'ET':
            # Check if this is first game of road trip (worst jet lag)
            away_schedule = sorted(self.team_schedules[away_team], key=lambda x: x['date'])
            recent_away = [g for g in reversed(away_schedule) if g['location'] == 'away']

            if len(recent_away) == 0:  # First road game
                return {
                    'type': 'timezone_travel',
                    'confidence': 'MEDIUM',
                    'bet': f'BET: {home_team} ML',
                    'reason': f'{away_team} (West Coast) traveling East - 3hr time difference, first road game',
                    'edge': '+3-5%',
                    'timezone_diff': '3 hours'
                }

        return None

    def get_games_for_date(self, date_str: str) -> List[Dict]:
        """Get games for a specific date"""
        url = f"{self.nhl_api_base}/schedule/{date_str}"

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
            print(f"Error fetching games: {e}")
            return []

    def _display_betting_opportunities(self, opportunities: List[Dict]):
        """Display betting opportunities in readable format"""

        if not opportunities:
            print("\n⚠️  No strong betting angles found for this date\n")
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

            print(f"🏒 {away} @ {home}")
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
        print(f"\n💰 RECOMMENDED: Focus on HIGH and MEDIUM-HIGH confidence angles")
        print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(description='Analyze NHL betting angles')
    parser.add_argument('--date', type=str,
                       help='Date in YYYY-MM-DD format (default: today)')

    args = parser.parse_args()

    if args.date:
        date_str = args.date
    else:
        date_str = datetime.now().strftime('%Y-%m-%d')

    analyzer = NHLBettingAnglesAnalyzer()
    opportunities = analyzer.analyze_schedule_for_date(date_str)


if __name__ == "__main__":
    main()
