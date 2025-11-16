#!/usr/bin/env python3
"""
Angle Discovery Engine - AUTOMATIC PATTERN DETECTION
Automatically tests new betting angle hypotheses and backtests promising patterns
"""

import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from collections import defaultdict
import statistics

sys.path.append('/Users/dickgibbons/hockey/daily hockey')
sys.path.append('/Users/dickgibbons/nba/daily nba')


class AngleDiscoveryEngine:
    """Automatically discover and validate new betting angles"""

    def __init__(self):
        self.discovered_patterns = []
        self.tested_hypotheses = []

        # Minimum sample size for testing
        self.min_sample_size = 30

        # Minimum edge to consider significant
        self.min_edge = 5.0  # 5% edge

        print("🔬 Angle Discovery Engine initialized")

    def discover_new_angles(self, sport: str, historical_games: List[Dict]):
        """Test multiple angle hypotheses on historical data"""

        print(f"\n{'='*80}")
        print(f"🔬 DISCOVERING NEW ANGLES - {sport}")
        print(f"{'='*80}\n")
        print(f"Analyzing {len(historical_games)} historical games...")

        discovered = []

        # Hypothesis 1: Home after long road trip
        angle = self._test_home_after_road_trip(sport, historical_games)
        if angle:
            discovered.append(angle)

        # Hypothesis 2: Days since last game (rest patterns)
        angle = self._test_rest_patterns(sport, historical_games)
        if angle:
            discovered.append(angle)

        # Hypothesis 3: Overtime game fatigue (next game)
        angle = self._test_ot_fatigue(sport, historical_games)
        if angle:
            discovered.append(angle)

        # Hypothesis 4: Time zone travel combinations
        angle = self._test_timezone_combinations(sport, historical_games)
        if angle:
            discovered.append(angle)

        # Hypothesis 5: Schedule compression (games per week)
        angle = self._test_schedule_density(sport, historical_games)
        if angle:
            discovered.append(angle)

        # Hypothesis 6: Day of week patterns
        angle = self._test_day_of_week(sport, historical_games)
        if angle:
            discovered.append(angle)

        # Hypothesis 7: Home stand length impact
        angle = self._test_home_stand_length(sport, historical_games)
        if angle:
            discovered.append(angle)

        # Hypothesis 8: Travel distance fatigue
        angle = self._test_travel_distance(sport, historical_games)
        if angle:
            discovered.append(angle)

        # Display results
        self._display_discoveries(discovered)

        return discovered

    def _test_home_after_road_trip(self, sport: str, games: List[Dict]) -> Dict:
        """Test: Do teams perform differently in first home game after road trip?"""

        # Build team schedules
        team_schedules = defaultdict(list)

        for game in sorted(games, key=lambda x: x.get('date', '')):
            date = game.get('date', '')
            home_team = game.get('home_team', '')
            away_team = game.get('away_team', '')

            if not date or not home_team or not away_team:
                continue

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

        # Check each game: is home team returning from road trip?
        first_home_after_trip = {'wins': 0, 'games': 0}

        for game in games:
            home_team = game.get('home_team', '')
            home_score = game.get('home_score', 0)
            away_score = game.get('away_score', 0)

            schedule = team_schedules[home_team]

            # Count previous consecutive road games
            consecutive_road = 0
            for prev_game in reversed(schedule):
                if prev_game['location'] == 'away':
                    consecutive_road += 1
                else:
                    break

            # If 3+ road games before this home game
            if consecutive_road >= 3:
                first_home_after_trip['games'] += 1
                if home_score > away_score:
                    first_home_after_trip['wins'] += 1

        # Check if significant
        if first_home_after_trip['games'] >= self.min_sample_size:
            win_rate = (first_home_after_trip['wins'] / first_home_after_trip['games']) * 100
            edge = win_rate - 50  # vs expected 50%

            if abs(edge) >= self.min_edge:
                return {
                    'name': 'home_after_long_road_trip',
                    'description': 'First home game after 3+ road games',
                    'win_rate': win_rate,
                    'edge': edge,
                    'sample_size': first_home_after_trip['games'],
                    'direction': 'HOME' if edge > 0 else 'AWAY',
                    'confidence': 'HIGH' if abs(edge) >= 8 else 'MEDIUM'
                }

        return None

    def _test_rest_patterns(self, sport: str, games: List[Dict]) -> Dict:
        """Test: Optimal rest days (not too much, not too little)"""

        rest_results = defaultdict(lambda: {'wins': 0, 'games': 0})

        team_schedules = defaultdict(list)

        for game in sorted(games, key=lambda x: x.get('date', '')):
            date = game.get('date', '')
            home_team = game.get('home_team', '')
            away_team = game.get('away_team', '')
            home_score = game.get('home_score', 0)
            away_score = game.get('away_score', 0)

            if not date:
                continue

            # Calculate days since last game for home team
            if home_team in team_schedules and team_schedules[home_team]:
                last_game_date = team_schedules[home_team][-1]['date']
                days_rest = (datetime.strptime(date, '%Y-%m-%d') -
                           datetime.strptime(last_game_date, '%Y-%m-%d')).days - 1

                if 0 <= days_rest <= 7:  # Cap at 7 days
                    rest_results[days_rest]['games'] += 1
                    if home_score > away_score:
                        rest_results[days_rest]['wins'] += 1

            # Update schedules
            team_schedules[home_team].append({'date': date})
            team_schedules[away_team].append({'date': date})

        # Find optimal rest period
        best_rest = None
        best_edge = 0

        for days_rest, results in rest_results.items():
            if results['games'] >= self.min_sample_size:
                win_rate = (results['wins'] / results['games']) * 100
                edge = win_rate - 50

                if abs(edge) > abs(best_edge) and abs(edge) >= self.min_edge:
                    best_edge = edge
                    best_rest = days_rest

        if best_rest is not None:
            results = rest_results[best_rest]
            win_rate = (results['wins'] / results['games']) * 100

            return {
                'name': f'optimal_rest_{best_rest}_days',
                'description': f'Teams with {best_rest} days rest',
                'win_rate': win_rate,
                'edge': best_edge,
                'sample_size': results['games'],
                'direction': 'HOME' if best_edge > 0 else 'AWAY',
                'confidence': 'HIGH' if abs(best_edge) >= 8 else 'MEDIUM'
            }

        return None

    def _test_ot_fatigue(self, sport: str, games: List[Dict]) -> Dict:
        """Test: Do teams perform worse after overtime games?"""

        after_ot = {'wins': 0, 'games': 0}
        team_schedules = defaultdict(list)

        for game in sorted(games, key=lambda x: x.get('date', '')):
            date = game.get('date', '')
            home_team = game.get('home_team', '')
            away_team = game.get('away_team', '')
            home_score = game.get('home_score', 0)
            away_score = game.get('away_score', 0)
            went_to_ot = game.get('overtime', False)  # Would need to detect OT

            # Check if either team played OT yesterday
            yesterday = (datetime.strptime(date, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')

            for team in [home_team, away_team]:
                if team in team_schedules:
                    last_game = team_schedules[team][-1] if team_schedules[team] else None

                    if last_game and last_game['date'] == yesterday and last_game.get('overtime'):
                        after_ot['games'] += 1

                        # Check if this team won today
                        if team == home_team:
                            if home_score > away_score:
                                after_ot['wins'] += 1
                        else:
                            if away_score > home_score:
                                after_ot['wins'] += 1

            # Update schedules
            team_schedules[home_team].append({'date': date, 'overtime': went_to_ot})
            team_schedules[away_team].append({'date': date, 'overtime': went_to_ot})

        # Check significance
        if after_ot['games'] >= self.min_sample_size:
            win_rate = (after_ot['wins'] / after_ot['games']) * 100
            edge = win_rate - 50

            if abs(edge) >= self.min_edge:
                return {
                    'name': 'after_overtime_game',
                    'description': 'Team playing day after overtime game',
                    'win_rate': win_rate,
                    'edge': edge,
                    'sample_size': after_ot['games'],
                    'direction': 'OPPONENT' if edge < 0 else 'TEAM',
                    'confidence': 'HIGH' if abs(edge) >= 8 else 'MEDIUM'
                }

        return None

    def _test_timezone_combinations(self, sport: str, games: List[Dict]) -> Dict:
        """Test: Specific timezone travel patterns"""
        # Would implement timezone mapping and test various travel patterns
        # Example: East→West→East (back and forth worst?)
        return None

    def _test_schedule_density(self, sport: str, games: List[Dict]) -> Dict:
        """Test: Games per week impact"""
        # Test if playing 4 games in 7 days has different impact than 3 in 7
        return None

    def _test_day_of_week(self, sport: str, games: List[Dict]) -> Dict:
        """Test: Do certain days favor home/away?"""

        day_results = defaultdict(lambda: {'wins': 0, 'games': 0})

        for game in games:
            date = game.get('date', '')
            home_score = game.get('home_score', 0)
            away_score = game.get('away_score', 0)

            if not date:
                continue

            day_of_week = datetime.strptime(date, '%Y-%m-%d').strftime('%A')

            day_results[day_of_week]['games'] += 1
            if home_score > away_score:
                day_results[day_of_week]['wins'] += 1

        # Find most significant day
        best_day = None
        best_edge = 0

        for day, results in day_results.items():
            if results['games'] >= 50:  # Need more samples for day-of-week
                win_rate = (results['wins'] / results['games']) * 100
                edge = win_rate - 50

                if abs(edge) > abs(best_edge) and abs(edge) >= 4:  # Lower threshold
                    best_edge = edge
                    best_day = day

        if best_day:
            results = day_results[best_day]
            win_rate = (results['wins'] / results['games']) * 100

            return {
                'name': f'{best_day.lower()}_home_advantage',
                'description': f'{best_day} games favor home team',
                'win_rate': win_rate,
                'edge': best_edge,
                'sample_size': results['games'],
                'direction': 'HOME' if best_edge > 0 else 'AWAY',
                'confidence': 'LOW'  # Day-of-week usually weaker
            }

        return None

    def _test_home_stand_length(self, sport: str, games: List[Dict]) -> Dict:
        """Test: Do long home stands lead to complacency?"""
        # Test if 5th+ home game in a row has different win rate
        return None

    def _test_travel_distance(self, sport: str, games: List[Dict]) -> Dict:
        """Test: Does travel distance matter beyond timezone?"""
        # Would need city location data
        return None

    def _display_discoveries(self, discoveries: List[Dict]):
        """Display discovered angles"""

        if not discoveries:
            print("\n⚠️  No significant new angles discovered")
            print("   (All tested hypotheses failed to meet significance threshold)")
            return

        print(f"\n{'='*80}")
        print(f"🔥 NEW ANGLES DISCOVERED: {len(discoveries)}")
        print(f"{'='*80}\n")

        for i, angle in enumerate(discoveries, 1):
            marker = {'HIGH': '🔥', 'MEDIUM': '✅', 'LOW': '💡'}.get(angle['confidence'], '⚪')

            print(f"{marker} DISCOVERY #{i}: {angle['name']}")
            print(f"   Description: {angle['description']}")
            print(f"   Win Rate: {angle['win_rate']:.1f}%")
            print(f"   Edge: {angle['edge']:+.1f}%")
            print(f"   Sample Size: {angle['sample_size']} games")
            print(f"   Direction: {angle['direction']}")
            print(f"   Confidence: {angle['confidence']}")
            print()

        print(f"{'='*80}")
        print(f"📊 NEXT STEPS:")
        print(f"   1. Review discoveries above")
        print(f"   2. Validate with additional seasons if needed")
        print(f"   3. Add to master_daily_betting_analyzer.py")
        print(f"   4. System will automatically use these angles tomorrow")
        print(f"{'='*80}\n")

    def generate_integration_code(self, discoveries: List[Dict], sport: str):
        """Generate code to integrate discoveries into master analyzer"""

        if not discoveries:
            return

        print(f"\n{'='*80}")
        print(f"🔧 INTEGRATION CODE")
        print(f"{'='*80}\n")
        print(f"Add this to master_daily_betting_analyzer.py proven_edges:")
        print()

        for angle in discoveries:
            print(f"    '{sport}_{angle['name']}': {{")
            print(f"        'edge': {angle['edge']:.1f},")
            print(f"        'win_rate': {angle['win_rate']:.1f},")
            print(f"        'sample_size': {angle['sample_size']},")

            # Set multiplier based on confidence
            multiplier = {'HIGH': 1.4, 'MEDIUM': 1.2, 'LOW': 1.0}[angle['confidence']]
            print(f"        'confidence_multiplier': {multiplier}")
            print(f"    }},")
            print()

        print(f"{'='*80}\n")


def main():
    """Run angle discovery on historical data"""

    engine = AngleDiscoveryEngine()

    print("🔬 Angle Discovery Engine")
    print("This will test multiple hypotheses on your historical data")
    print("to discover new profitable betting angles.\n")

    # Example: Load NHL historical data and discover angles
    # You would load actual game data here
    print("To use this engine:")
    print("1. Load historical games (from backtests or API)")
    print("2. Call engine.discover_new_angles('NHL', games)")
    print("3. Review discovered angles")
    print("4. Integrate significant discoveries into master analyzer")


if __name__ == "__main__":
    main()
