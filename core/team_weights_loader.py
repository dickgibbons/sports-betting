#!/usr/bin/env python3
"""
Team-Specific Weights Loader
Loads team profiles and provides multipliers for angle detection.

Key insight: Some teams massively outperform/underperform league averages:
- Boston Celtics: 100% on 4th+ road trips (vs 41.2% league avg)
- Utah Jazz: 11.1% on 4th+ road trips (vs 41.2% league avg)

This system amplifies angles for strong teams and filters for weak teams.
"""
import json
from typing import Dict, Optional


class TeamWeightsLoader:
    """Load and apply team-specific performance multipliers"""

    def __init__(self, sport: str = 'NHL'):
        self.sport = sport.upper()
        self.team_profiles = {}
        self.league_averages = {}

        # Load team profiles
        self._load_profiles()

        print(f"✅ Team Weights Loader initialized for {self.sport}")
        if self.team_profiles:
            print(f"   Loaded profiles for {len(self.team_profiles)} teams")

    def _load_profiles(self):
        """Load team profiles from JSON"""
        try:
            if self.sport == 'NHL':
                profile_path = '/Users/dickgibbons/AI Projects/sports-betting/data/team_profiles_nhl_2024-25.json'
            elif self.sport == 'NBA':
                profile_path = '/Users/dickgibbons/AI Projects/sports-betting/data/team_profiles_nba_2024-25.json'
            else:
                print(f"⚠️  Sport {self.sport} not supported for team weights")
                return

            with open(profile_path, 'r') as f:
                data = json.load(f)
                self.team_profiles = data.get('team_stats', {})
                self.league_averages = data.get('league_averages', {})

        except FileNotFoundError:
            print(f"⚠️  Team profiles not found at {profile_path}")
            print("   Run team profiler first: python3 team_situation_profiler.py")
        except Exception as e:
            print(f"⚠️  Error loading team profiles: {e}")

    def get_team_multiplier(self, team: str, angle_type: str) -> Dict:
        """
        Get team-specific multiplier for an angle

        Returns dict with:
        - multiplier: float (0.0 to 2.0+)
        - action: str ('AMPLIFY', 'NORMAL', 'REDUCE', 'FILTER')
        - confidence_boost: str (upgrade confidence level if applicable)
        - team_win_rate: float
        - team_record: str
        - differential: float (vs league avg)
        """

        if not self.team_profiles or team not in self.team_profiles:
            return {
                'multiplier': 1.0,
                'action': 'NORMAL',
                'confidence_boost': None,
                'reason': 'No team data available'
            }

        team_data = self.team_profiles[team]

        # Map angle types to profile keys
        angle_map = {
            'back_to_back': 'back_to_back_home_to_road',
            'road_trip_fatigue': 'road_trip_4th_plus',
            'three_in_four': 'three_in_four'
        }

        profile_key = angle_map.get(angle_type)
        if not profile_key:
            return {
                'multiplier': 1.0,
                'action': 'NORMAL',
                'confidence_boost': None,
                'reason': f'Angle type {angle_type} not tracked'
            }

        situation_data = team_data.get(profile_key, {})
        games = situation_data.get('games', 0)
        wins = situation_data.get('wins', 0)
        losses = situation_data.get('losses', 0)

        # Need minimum 5 games for statistical significance
        if games < 5:
            return {
                'multiplier': 1.0,
                'action': 'NORMAL',
                'confidence_boost': None,
                'reason': f'Insufficient data ({games} games)'
            }

        team_win_rate = (wins / games) * 100 if games > 0 else 0

        # Calculate league average
        league_data = self.league_averages.get(profile_key, {})
        league_games = league_data.get('games', 1)
        league_wins = league_data.get('wins', 0)
        league_win_rate = (league_wins / league_games) * 100 if league_games > 0 else 50.0

        differential = team_win_rate - league_win_rate

        # Determine multiplier and action based on differential
        # Team is AWAY team (we're betting on HOME team against them)
        # Lower away win rate = BETTER for our bet

        # Since we bet on home team, we want AWAY team to have LOW win rate
        # differential < 0 means away team wins LESS than average = AMPLIFY
        # differential > 0 means away team wins MORE than average = REDUCE/FILTER

        multiplier = 1.0
        action = 'NORMAL'
        confidence_boost = None

        if differential <= -20:  # Team is TERRIBLE in this situation
            multiplier = 1.5
            action = 'AMPLIFY'
            confidence_boost = 'HIGH->ELITE'
        elif differential <= -10:
            multiplier = 1.3
            action = 'AMPLIFY'
            confidence_boost = 'MEDIUM->HIGH'
        elif differential <= -5:
            multiplier = 1.1
            action = 'AMPLIFY'
        elif differential >= 20:  # Team is GREAT in this situation
            multiplier = 0.0
            action = 'FILTER'
        elif differential >= 10:
            multiplier = 0.5
            action = 'REDUCE'
        elif differential >= 5:
            multiplier = 0.8
            action = 'REDUCE'

        return {
            'multiplier': multiplier,
            'action': action,
            'confidence_boost': confidence_boost,
            'team_win_rate': round(team_win_rate, 1),
            'team_record': f"{wins}-{losses}",
            'differential': round(differential, 1),
            'league_avg': round(league_win_rate, 1),
            'games': games,
            'reason': f"{team} is {team_win_rate:.1f}% in this situation (league: {league_win_rate:.1f}%)"
        }

    def should_filter_angle(self, team: str, angle_type: str) -> tuple[bool, str]:
        """
        Determine if angle should be filtered for this team
        Returns (should_filter, reason)
        """
        result = self.get_team_multiplier(team, angle_type)

        if result['action'] == 'FILTER':
            return True, result['reason']

        return False, ''

    def get_confidence_adjustment(self, team: str, angle_type: str, current_confidence: str) -> str:
        """
        Get adjusted confidence level based on team performance
        """
        result = self.get_team_multiplier(team, angle_type)

        if result['confidence_boost']:
            boost = result['confidence_boost']
            if '->' in boost:
                old, new = boost.split('->')
                if current_confidence == old:
                    return new

        return current_confidence

    def get_edge_adjustment(self, team: str, angle_type: str, base_edge: float) -> float:
        """
        Get adjusted edge based on team performance
        """
        result = self.get_team_multiplier(team, angle_type)
        return base_edge * result['multiplier']


def main():
    """Test the team weights loader"""
    print("="*80)
    print("TESTING TEAM WEIGHTS LOADER")
    print("="*80)

    # Test NHL
    print("\n🏒 NHL TEAMS:")
    nhl_loader = TeamWeightsLoader('NHL')

    test_teams = ['BOS', 'UTA', 'CBJ', 'BUF', 'CHI', 'OTT']
    test_angles = ['back_to_back', 'road_trip_fatigue']

    for team in test_teams:
        print(f"\n{team}:")
        for angle in test_angles:
            result = nhl_loader.get_team_multiplier(team, angle)
            print(f"  {angle}: {result['action']} (x{result['multiplier']}) - {result.get('team_record', 'N/A')} - {result.get('reason', '')}")

    # Test NBA
    print("\n🏀 NBA TEAMS:")
    nba_loader = TeamWeightsLoader('NBA')

    test_teams = ['Boston Celtics', 'Utah Jazz', 'Golden State Warriors',
                  'Philadelphia 76ers', 'Atlanta Hawks']

    for team in test_teams:
        print(f"\n{team}:")
        for angle in test_angles:
            result = nba_loader.get_team_multiplier(team, angle)
            print(f"  {angle}: {result['action']} (x{result['multiplier']}) - {result.get('team_record', 'N/A')} - {result.get('reason', '')}")


if __name__ == "__main__":
    main()
