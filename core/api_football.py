#!/usr/bin/env python3
"""
API-Football Adapter
Provides live soccer scores for result checking
Free tier: 100 requests/day
"""

import requests
import time
from datetime import datetime
from typing import Dict, List, Optional


class APIFootball:
    """API-Football client for live soccer scores"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://v3.football.api-sports.io"
        self.session = requests.Session()
        self.session.headers.update({
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': 'v3.football.api-sports.io'
        })

    def get_fixtures_by_date(self, date_str: str) -> List[Dict]:
        """
        Get all fixtures for a specific date

        Args:
            date_str: Date in format 'YYYY-MM-DD'

        Returns:
            List of fixture dictionaries with team names and scores
        """
        url = f"{self.base_url}/fixtures"

        params = {
            'date': date_str,
            'status': 'FT'  # Only get finished matches
        }

        try:
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            if 'response' not in data:
                return []

            fixtures = []
            for fixture in data['response']:
                # Extract fixture details
                match_data = self._parse_fixture(fixture)
                if match_data:
                    fixtures.append(match_data)

            return fixtures

        except requests.exceptions.RequestException as e:
            print(f"   ⚠️  API-Football request failed: {str(e)}")
            return []

    def _parse_fixture(self, fixture: Dict) -> Optional[Dict]:
        """Parse API-Football fixture data into standard format"""

        try:
            # Extract teams
            teams = fixture.get('teams', {})
            home_team = teams.get('home', {}).get('name', '')
            away_team = teams.get('away', {}).get('name', '')

            # Extract scores
            goals = fixture.get('goals', {})
            home_score = goals.get('home')
            away_score = goals.get('away')

            # Ensure scores are valid
            if home_score is None or away_score is None:
                return None

            # Extract status
            status = fixture.get('fixture', {}).get('status', {})
            is_finished = status.get('short') == 'FT'  # Full Time

            if not is_finished:
                return None

            return {
                'home_team': home_team,
                'away_team': away_team,
                'home_score': int(home_score),
                'away_score': int(away_score),
                'completed': True
            }

        except Exception as e:
            return None

    def find_match(self, date_str: str, home_team: str, away_team: str) -> Optional[Dict]:
        """
        Find a specific match by date and teams

        Args:
            date_str: Date in format 'YYYY-MM-DD'
            home_team: Home team name (partial match supported)
            away_team: Away team name (partial match supported)

        Returns:
            Match data dict if found, None otherwise
        """
        fixtures = self.get_fixtures_by_date(date_str)

        for fixture in fixtures:
            match_home = fixture.get('home_team', '')
            match_away = fixture.get('away_team', '')

            # Flexible team matching (bidirectional substring matching)
            home_match = (home_team.lower() in match_home.lower() or
                         match_home.lower() in home_team.lower())
            away_match = (away_team.lower() in match_away.lower() or
                         match_away.lower() in away_team.lower())

            if home_match and away_match:
                return fixture

        return None


def test_api():
    """Test API-Football connection"""
    # You need to get an API key from https://www.api-football.com/
    # Free tier: 100 requests/day

    print("=" * 80)
    print("API-Football Test")
    print("=" * 80)
    print("\nTo use API-Football:")
    print("1. Sign up at https://www.api-football.com/")
    print("2. Get your free API key (100 requests/day)")
    print("3. Replace 'YOUR_API_KEY' in the code")
    print("\nFree tier includes:")
    print("  - 100 requests/day")
    print("  - Live scores updated every 15 seconds")
    print("  - All major leagues (Premier League, La Liga, etc.)")
    print("=" * 80)


if __name__ == '__main__':
    test_api()
