#!/usr/bin/env python3
"""
Automatic Bet Result Updater
Checks pending bets against game results and updates them automatically
"""

import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from bet_tracker import BetTracker
from footystats_api import FootyStatsAPI
from api_football import APIFootball


class BetResultUpdater:
    """Automatically update bet results by checking game scores"""

    def __init__(self, api_football_key: Optional[str] = None):
        self.tracker = BetTracker()
        self.espn_base = "https://site.api.espn.com/apis/site/v2/sports"

        # Initialize soccer APIs
        # FootyStats API (for historical data)
        self.footystats = FootyStatsAPI("ceb338b9bcb82a452efc114fb2d3cccac67f58be1569e7b5acf1d2195adeae11")

        # API-Football (for live scores) - optional
        self.api_football = None
        if api_football_key:
            self.api_football = APIFootball(api_football_key)
            print("✅ API-Football enabled for live soccer scores")

    def get_pending_bets(self) -> List[Dict]:
        """Get all pending bets"""
        return [b for b in self.tracker.bet_history if b['result'] == 'PENDING']

    def fetch_game_result(self, sport: str, date: str, home_team: str, away_team: str) -> Dict:
        """Fetch game result from ESPN API"""

        # Map sport to ESPN endpoint
        sport_map = {
            'NHL': 'hockey/nhl',
            'NBA': 'basketball/nba',
            'NCAA': 'basketball/mens-college-basketball'
        }

        if sport not in sport_map:
            return None

        endpoint = sport_map[sport]

        # Try the game date and next day (for late games)
        for day_offset in [0, 1]:
            check_date = (datetime.strptime(date, '%Y-%m-%d') + timedelta(days=day_offset)).strftime('%Y%m%d')
            url = f"{self.espn_base}/{endpoint}/scoreboard?dates={check_date}"

            try:
                response = requests.get(url, timeout=10)
                data = response.json()

                # Find the game
                for event in data.get('events', []):
                    competitions = event.get('competitions', [])
                    if not competitions:
                        continue

                    comp = competitions[0]
                    competitors = comp.get('competitors', [])

                    if len(competitors) < 2:
                        continue

                    # Get team names
                    home = next((c for c in competitors if c.get('homeAway') == 'home'), None)
                    away = next((c for c in competitors if c.get('homeAway') == 'away'), None)

                    if not home or not away:
                        continue

                    home_name = home.get('team', {}).get('displayName', '')
                    away_name = away.get('team', {}).get('displayName', '')

                    # Check if this is our game (flexible matching)
                    if (home_team.lower() in home_name.lower() and away_team.lower() in away_name.lower()) or \
                       (away_team.lower() in away_name.lower() and home_team.lower() in home_name.lower()):

                        # Check if game is completed
                        status = comp.get('status', {}).get('type', {}).get('completed', False)

                        if status:
                            return {
                                'home_team': home_name,
                                'away_team': away_name,
                                'home_score': int(home.get('score', 0)),
                                'away_score': int(away.get('score', 0)),
                                'completed': True
                            }

            except Exception as e:
                print(f"   Error fetching {sport} game: {e}")
                continue

        return None

    def fetch_soccer_result(self, date: str, home_team: str, away_team: str) -> Optional[Dict]:
        """Fetch soccer game result using API-Football or FootyStats"""

        # Try API-Football first (if available) - better for current season
        if self.api_football:
            try:
                result = self.api_football.find_match(date, home_team, away_team)
                if result:
                    return result
            except Exception as e:
                print(f"   ⚠️  API-Football error: {e}")

        # Fall back to FootyStats (better for historical data)
        try:
            matches = self.footystats.get_matches_by_date(date)

            if not matches:
                return None

            # Find the matching game
            for match in matches:
                match_home = match.get('home_team', '')
                match_away = match.get('away_team', '')

                # Flexible team matching
                home_match = home_team.lower() in match_home.lower() or match_home.lower() in home_team.lower()
                away_match = away_team.lower() in match_away.lower() or match_away.lower() in away_team.lower()

                if home_match and away_match:
                    return {
                        'home_team': match_home,
                        'away_team': match_away,
                        'home_score': match.get('home_score', 0),
                        'away_score': match.get('away_score', 0),
                        'completed': True
                    }

            return None

        except Exception as e:
            print(f"   ⚠️  FootyStats error: {e}")
            return None

    def determine_bet_result(self, bet: Dict, game_result: Dict) -> str:
        """Determine if bet won or lost based on game result"""

        bet_text = bet['bet'].upper()

        # Extract team name from bet
        bet_team = None
        if ' ML' in bet_text:
            bet_team = bet_text.replace(' ML', '').strip()
        elif 'MONEYLINE' in bet_text.upper():
            # Extract team before "ML" or "Moneyline"
            parts = bet_text.split()
            if len(parts) >= 2:
                bet_team = ' '.join(parts[:-1])

        if not bet_team:
            print(f"   ⚠️  Could not parse bet team from: {bet['bet']}")
            return None

        # Determine if bet team is home or away
        home_team = game_result['home_team']
        away_team = game_result['away_team']
        home_score = game_result['home_score']
        away_score = game_result['away_score']

        # Flexible team matching
        is_home_team = bet_team.lower() in home_team.lower()
        is_away_team = bet_team.lower() in away_team.lower()

        if not is_home_team and not is_away_team:
            print(f"   ⚠️  Could not match bet team '{bet_team}' to game teams")
            print(f"       Game: {away_team} @ {home_team}")
            return None

        # Check result
        if is_home_team:
            return 'WIN' if home_score > away_score else 'LOSS'
        else:
            return 'WIN' if away_score > home_score else 'LOSS'

    def update_pending_bets(self, max_days_old: int = 7):
        """Update all pending bets from recent games"""

        pending = self.get_pending_bets()

        if not pending:
            print("✅ No pending bets to update")
            return

        print(f"\n{'='*80}")
        print(f"🔄 UPDATING PENDING BET RESULTS")
        print(f"{'='*80}\n")
        print(f"Found {len(pending)} pending bets\n")

        # Filter to recent bets only
        cutoff_date = (datetime.now() - timedelta(days=max_days_old)).strftime('%Y-%m-%d')
        recent_pending = [b for b in pending if b['date'] >= cutoff_date]

        if len(recent_pending) < len(pending):
            print(f"⏭️  Skipping {len(pending) - len(recent_pending)} old bets (older than {max_days_old} days)")
            print(f"   Checking {len(recent_pending)} recent bets\n")

        updated_count = 0
        error_count = 0

        for bet in recent_pending:
            print(f"Checking: {bet['bet_id']}")
            print(f"   {bet['sport']}: {bet['game']}")
            print(f"   BET: {bet['bet']}")

            # Parse teams from game string
            if '@' in bet['game']:
                parts = bet['game'].split('@')
                away_team = parts[0].strip()
                home_team = parts[1].strip()
            else:
                print(f"   ⚠️  Cannot parse game format")
                error_count += 1
                continue

            # Fetch game result (use different API based on sport)
            if bet['sport'] == 'SOCCER':
                result = self.fetch_soccer_result(bet['date'], home_team, away_team)
            else:
                result = self.fetch_game_result(bet['sport'], bet['date'], home_team, away_team)

            if not result:
                print(f"   ⏳ Game not finished or not found")
                continue

            if not result.get('completed'):
                print(f"   ⏳ Game in progress")
                continue

            # Determine bet outcome
            outcome = self.determine_bet_result(bet, result)

            if not outcome:
                error_count += 1
                continue

            # Update bet
            print(f"   📊 Score: {result['away_team']} {result['away_score']} @ {result['home_team']} {result['home_score']}")
            print(f"   🎯 Result: {outcome}")

            self.tracker.update_result(bet['bet_id'], outcome)
            updated_count += 1
            print()

        print(f"{'='*80}")
        print(f"✅ RESULTS UPDATE COMPLETE")
        print(f"{'='*80}")
        print(f"Updated: {updated_count}")
        print(f"Still Pending: {len(self.get_pending_bets())}")
        print(f"Errors: {error_count}")
        print(f"{'='*80}\n")


def main():
    updater = BetResultUpdater()
    updater.update_pending_bets(max_days_old=14)  # Check last 14 days


if __name__ == "__main__":
    main()
