#!/usr/bin/env python3
"""
Hockey API Integration
API-Sports Hockey API wrapper for NHL and other leagues
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class HockeyAPI:
    """Wrapper for API-Sports Hockey API"""

    def __init__(self, api_key: str = "960c628e1c91c4b1f125e1eec52ad862"):
        self.api_key = api_key
        self.base_url = "https://v1.hockey.api-sports.io"
        self.headers = {
            'x-apisports-key': api_key
        }

        # Major league IDs
        self.leagues = {
            'NHL': 57,
            'AHL': 58,
            'KHL': 35,
            'SHL': 47,
            'Liiga': 16,
            'DEL': 19,
        }

    def get_leagues(self) -> List[Dict]:
        """Get all available leagues"""

        url = f"{self.base_url}/leagues"

        try:
            response = requests.get(url, headers=self.headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                return data.get('response', [])
            else:
                print(f"❌ API error: {response.status_code}")
                return []

        except Exception as e:
            print(f"❌ Error: {e}")
            return []

    def get_games(self, league_id: int, season: int, date: str = None) -> List[Dict]:
        """Get games for a specific league and season"""

        url = f"{self.base_url}/games"
        params = {
            'league': league_id,
            'season': season
        }

        if date:
            params['date'] = date

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                return data.get('response', [])
            else:
                print(f"❌ API error: {response.status_code}")
                return []

        except Exception as e:
            print(f"❌ Error: {e}")
            return []

    def get_nhl_games(self, date: str = None) -> List[Dict]:
        """Get NHL games for a specific date (format: YYYY-MM-DD)"""

        if not date:
            date = datetime.now().strftime('%Y-%m-%d')

        return self.get_games(league_id=57, season=2025, date=date)

    def get_game_odds(self, game_id: int) -> Optional[Dict]:
        """Get betting odds for a specific game"""

        url = f"{self.base_url}/odds"
        params = {'game': game_id}

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                odds = data.get('response', [])
                return odds[0] if odds else None
            else:
                print(f"❌ API error: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Error: {e}")
            return None

    def get_standings(self, league_id: int, season: int) -> List[Dict]:
        """Get league standings"""

        url = f"{self.base_url}/standings"
        params = {
            'league': league_id,
            'season': season
        }

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                return data.get('response', [])
            else:
                print(f"❌ API error: {response.status_code}")
                return []

        except Exception as e:
            print(f"❌ Error: {e}")
            return []


def main():
    """Test the Hockey API"""

    print("🏒 Hockey API Test")
    print("=" * 50)

    api = HockeyAPI()

    # Test 1: Get today's NHL games
    print("\n📅 Today's NHL Games:")
    today = datetime.now().strftime('%Y-%m-%d')
    games = api.get_nhl_games(today)

    if games:
        print(f"Found {len(games)} games:")
        for game in games[:5]:
            teams = game.get('teams', {})
            home = teams.get('home', {}).get('name', 'Unknown')
            away = teams.get('away', {}).get('name', 'Unknown')
            status = game.get('status', {}).get('long', 'Unknown')

            print(f"  🏒 {away} @ {home} - {status}")
    else:
        print("  No games found for today")

    # Test 2: Get NHL standings
    print("\n🏆 NHL Standings (Top 5):")
    standings = api.get_standings(league_id=57, season=2025)

    if standings:
        for entry in standings[:5]:
            team = entry.get('team', {}).get('name', 'Unknown')
            position = entry.get('position', 0)
            points = entry.get('points', 0)
            games = entry.get('games', {}).get('played', 0)

            print(f"  {position}. {team}: {points} pts ({games} GP)")

    print("\n✅ API test complete!")


if __name__ == "__main__":
    main()
