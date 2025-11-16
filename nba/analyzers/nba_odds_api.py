#!/usr/bin/env python3
"""
NBA Odds API - Get odds for NBA games

Uses The-Odds-API for NBA betting odds
"""

import requests
from typing import Dict, Optional, List


class NBAOddsAPI:
    """Fetch NBA odds from The-Odds-API"""

    def __init__(self, api_key: str = '518c226b561ad7586ec8c5dd1144e3fb'):
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"

    def get_upcoming_games(self) -> List[Dict]:
        """Get upcoming NBA games with odds"""
        url = f"{self.base_url}/sports/basketball_nba/odds"
        params = {
            'apiKey': self.api_key,
            'regions': 'us',
            'markets': 'h2h,spreads,totals'
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"⚠️  Error fetching NBA odds: {e}")
            return []

    def parse_game_odds(self, game: Dict) -> Optional[Dict]:
        """Parse odds from API response"""
        try:
            bookmakers = game.get('bookmakers', [])
            if not bookmakers:
                return None

            book = bookmakers[0]  # Use first available bookmaker
            markets = book.get('markets', [])

            odds_data = {
                'game_id': game.get('id'),
                'home_team': game.get('home_team'),
                'away_team': game.get('away_team'),
                'commence_time': game.get('commence_time'),
                'bookmaker': book.get('title'),
                'home_odds': None,
                'away_odds': None,
                'home_spread': None,
                'away_spread': None,
                'home_spread_odds': None,
                'away_spread_odds': None,
                'over_odds': None,
                'under_odds': None,
                'total_line': None
            }

            for market in markets:
                if market.get('key') == 'h2h':
                    # Moneyline odds
                    for outcome in market.get('outcomes', []):
                        if outcome.get('name') == odds_data['home_team']:
                            odds_data['home_odds'] = outcome.get('price')
                        elif outcome.get('name') == odds_data['away_team']:
                            odds_data['away_odds'] = outcome.get('price')

                elif market.get('key') == 'spreads':
                    # Spread odds
                    for outcome in market.get('outcomes', []):
                        if outcome.get('name') == odds_data['home_team']:
                            odds_data['home_spread'] = outcome.get('point')
                            odds_data['home_spread_odds'] = outcome.get('price')
                        elif outcome.get('name') == odds_data['away_team']:
                            odds_data['away_spread'] = outcome.get('point')
                            odds_data['away_spread_odds'] = outcome.get('price')

                elif market.get('key') == 'totals':
                    # Totals odds
                    for outcome in market.get('outcomes', []):
                        if outcome.get('name') == 'Over':
                            odds_data['over_odds'] = outcome.get('price')
                            odds_data['total_line'] = outcome.get('point')
                        elif outcome.get('name') == 'Under':
                            odds_data['under_odds'] = outcome.get('price')

            return odds_data

        except Exception as e:
            print(f"⚠️  Error parsing game odds: {e}")
            return None


def test_nba_odds():
    """Test NBA odds API"""
    print("🏀 Testing NBA Odds API\n")

    api = NBAOddsAPI()
    games = api.get_upcoming_games()

    print(f"✅ Found {len(games)} upcoming NBA games\n")

    if games:
        for game in games[:3]:
            odds = api.parse_game_odds(game)
            if odds:
                print(f"{odds['away_team']} @ {odds['home_team']}")
                print(f"  Moneyline: {odds['away_odds']} / {odds['home_odds']}")
                print(f"  Spread: {odds['away_spread']} @ {odds['away_spread_odds']} / {odds['home_spread']} @ {odds['home_spread_odds']}")
                print(f"  Total: O/U {odds['total_line']} ({odds['over_odds']}/{odds['under_odds']})")
                print()


if __name__ == "__main__":
    test_nba_odds()
