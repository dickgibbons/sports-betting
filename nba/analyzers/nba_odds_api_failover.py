#!/usr/bin/env python3
"""
NBA Odds API Failover System
Tries multiple real odds sources, never returns simulated data
"""

import requests
from typing import Dict, Optional
import time


class NBAOddsFailover:
    """Failover system for NBA odds - tries multiple sources"""

    def __init__(self, odds_api_key: str = '518c226b561ad7586ec8c5dd1144e3fb'):
        self.odds_api_key = odds_api_key
        self.last_source_used = None

    def get_odds(self, home_team: str, away_team: str) -> Optional[Dict]:
        """
        Try multiple odds sources in order:
        1. The-Odds-API (primary - paid, reliable)
        2. ESPN API (free, reliable)
        3. None (skip game if no real odds available)

        Returns None if no real odds found
        """

        # Try The-Odds-API first
        odds = self._try_the_odds_api(home_team, away_team)
        if odds:
            self.last_source_used = 'The-Odds-API'
            return odds

        # Try ESPN API as backup
        odds = self._try_espn_api(home_team, away_team)
        if odds:
            self.last_source_used = 'ESPN'
            return odds

        # No real odds found
        self.last_source_used = None
        print(f"   ⚠️  No real odds found for {away_team} @ {home_team} - SKIPPING GAME")
        return None

    def _try_the_odds_api(self, home_team: str, away_team: str) -> Optional[Dict]:
        """Try The-Odds-API (primary source)"""
        url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
        params = {
            'apiKey': self.odds_api_key,
            'regions': 'us',
            'markets': 'h2h,totals,spreads'
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code != 200:
                print(f"   ⚠️  The-Odds-API returned status {response.status_code}")
                return None

            data = response.json()

            # Find matching game
            for game in data:
                g_home = game.get('home_team', '').lower()
                g_away = game.get('away_team', '').lower()

                if (home_team.lower() in g_home or g_home in home_team.lower()) and \
                   (away_team.lower() in g_away or g_away in away_team.lower()):

                    # Extract odds from bookmakers
                    bookmakers = game.get('bookmakers', [])
                    if not bookmakers:
                        continue

                    book = bookmakers[0]
                    result = {
                        'home_odds': None,
                        'away_odds': None,
                        'over_odds': None,
                        'under_odds': None,
                        'total_line': None,
                        'home_spread': None,
                        'home_spread_odds': None,
                        'away_spread': None,
                        'away_spread_odds': None,
                        'bookmaker': book.get('title', 'Unknown')
                    }

                    # Get moneyline odds
                    for market in book.get('markets', []):
                        if market.get('key') == 'h2h':
                            for outcome in market.get('outcomes', []):
                                if outcome.get('name') == game.get('home_team'):
                                    result['home_odds'] = outcome.get('price')
                                elif outcome.get('name') == game.get('away_team'):
                                    result['away_odds'] = outcome.get('price')

                        # Get totals
                        elif market.get('key') == 'totals':
                            for outcome in market.get('outcomes', []):
                                if outcome.get('name') == 'Over':
                                    result['over_odds'] = outcome.get('price')
                                    result['total_line'] = outcome.get('point')
                                elif outcome.get('name') == 'Under':
                                    result['under_odds'] = outcome.get('price')

                        # Get spreads
                        elif market.get('key') == 'spreads':
                            for outcome in market.get('outcomes', []):
                                if outcome.get('name') == game.get('home_team'):
                                    result['home_spread'] = outcome.get('point')
                                    result['home_spread_odds'] = outcome.get('price')
                                elif outcome.get('name') == game.get('away_team'):
                                    result['away_spread'] = outcome.get('point')
                                    result['away_spread_odds'] = outcome.get('price')

                    # Only return if we have at least moneyline odds
                    if result['home_odds'] and result['away_odds']:
                        print(f"   ✅ The-Odds-API: Found odds for {away_team} @ {home_team}")
                        return result

            print(f"   ⚠️  The-Odds-API: Game not found")
            return None

        except Exception as e:
            print(f"   ⚠️  The-Odds-API error: {e}")
            return None

    def _try_espn_api(self, home_team: str, away_team: str) -> Optional[Dict]:
        """Try ESPN API as backup (free, no key needed)"""

        # ESPN API endpoint for NBA odds
        url = "https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/events"

        try:
            # First get current NBA events
            response = requests.get(url, params={'limit': 100}, timeout=30)
            if response.status_code != 200:
                print(f"   ⚠️  ESPN API returned status {response.status_code}")
                return None

            data = response.json()
            events = data.get('items', [])

            # Search for matching game
            for event_ref in events:
                event_url = event_ref.get('$ref')
                if not event_url:
                    continue

                # Get event details
                event_response = requests.get(event_url, timeout=30)
                if event_response.status_code != 200:
                    continue

                event = event_response.json()
                competitions = event.get('competitions', [])

                if not competitions:
                    continue

                competition = competitions[0]
                competitors = competition.get('competitors', [])

                if len(competitors) < 2:
                    continue

                # Extract team names
                event_home = None
                event_away = None
                for comp in competitors:
                    team_data = comp.get('team', {})
                    team_name = team_data.get('displayName', '')

                    if comp.get('homeAway') == 'home':
                        event_home = team_name
                    elif comp.get('homeAway') == 'away':
                        event_away = team_name

                # Check if teams match
                if event_home and event_away:
                    home_match = home_team.lower() in event_home.lower() or event_home.lower() in home_team.lower()
                    away_match = away_team.lower() in event_away.lower() or event_away.lower() in away_team.lower()

                    if home_match and away_match:
                        # Found the game, now get odds
                        odds_url = competition.get('odds', {}).get('$ref')

                        if not odds_url:
                            print(f"   ⚠️  ESPN: No odds available for this game")
                            return None

                        odds_response = requests.get(odds_url, timeout=30)
                        if odds_response.status_code != 200:
                            return None

                        odds_data = odds_response.json()
                        items = odds_data.get('items', [])

                        if not items:
                            return None

                        provider = items[0]
                        result = {
                            'home_odds': None,
                            'away_odds': None,
                            'over_odds': None,
                            'under_odds': None,
                            'total_line': None,
                            'home_spread': None,
                            'home_spread_odds': None,
                            'away_spread': None,
                            'away_spread_odds': None,
                            'bookmaker': provider.get('provider', {}).get('name', 'ESPN')
                        }

                        # Extract moneyline
                        moneyline = provider.get('moneyline')
                        if moneyline:
                            result['home_odds'] = moneyline.get('home', {}).get('value')
                            result['away_odds'] = moneyline.get('away', {}).get('value')

                        # Extract spread
                        spread = provider.get('spread')
                        if spread:
                            result['home_spread'] = spread.get('home', {}).get('spread')
                            result['home_spread_odds'] = spread.get('home', {}).get('value')
                            result['away_spread'] = spread.get('away', {}).get('spread')
                            result['away_spread_odds'] = spread.get('away', {}).get('value')

                        # Extract totals
                        over_under = provider.get('overUnder')
                        if over_under:
                            result['total_line'] = over_under.get('total')
                            result['over_odds'] = over_under.get('over', {}).get('value')
                            result['under_odds'] = over_under.get('under', {}).get('value')

                        # Only return if we have at least moneyline
                        if result['home_odds'] and result['away_odds']:
                            print(f"   ✅ ESPN API: Found odds for {away_team} @ {home_team}")
                            return result

            print(f"   ⚠️  ESPN API: Game not found")
            return None

        except Exception as e:
            print(f"   ⚠️  ESPN API error: {e}")
            return None

    def get_last_source(self) -> Optional[str]:
        """Get the last API source that successfully returned odds"""
        return self.last_source_used


def test_odds_failover():
    """Test the failover system"""
    print("🏀 Testing NBA Odds Failover System")
    print("=" * 80)

    failover = NBAOddsFailover()

    # Test with a real NBA matchup
    test_games = [
        ("Los Angeles Lakers", "Golden State Warriors"),
        ("Boston Celtics", "Miami Heat"),
    ]

    for home, away in test_games:
        print(f"\n📊 Testing: {away} @ {home}")
        odds = failover.get_odds(home, away)

        if odds:
            print(f"   ✅ Source: {failover.get_last_source()}")
            print(f"   💰 Home odds: {odds['home_odds']}")
            print(f"   💰 Away odds: {odds['away_odds']}")
            if odds['total_line']:
                print(f"   🎯 Total: {odds['total_line']}")
        else:
            print(f"   ❌ No odds found - game will be skipped")

        time.sleep(1)  # Rate limiting


if __name__ == "__main__":
    test_odds_failover()
