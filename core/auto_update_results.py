#!/usr/bin/env python3
"""
Automatic Bet Results Updater
Fetches game results from APIs and automatically updates bet tracker
"""

import sys
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional
from bet_tracker import BetTracker

import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'analyzers'))

from nhl_betting_angles_analyzer import NHLBettingAnglesAnalyzer
from nba_betting_angles_analyzer_v2 import NBABettingAnglesAnalyzer


class AutoResultsUpdater:
    """Automatically fetch game results and update bet tracker"""

    def __init__(self):
        self.tracker = BetTracker()
        self.nhl_analyzer = NHLBettingAnglesAnalyzer()
        self.nba_analyzer = NBABettingAnglesAnalyzer()

        print("🤖 Automatic Results Updater initialized")

    def update_all_pending_bets(self):
        """Update all pending bets with game results"""

        pending = [b for b in self.tracker.bet_history if b['result'] == 'PENDING']

        if not pending:
            print("\n✅ No pending bets to update")
            return

        print(f"\n{'='*80}")
        print(f"🔄 UPDATING {len(pending)} PENDING BETS")
        print(f"{'='*80}\n")

        updated_count = 0
        skipped_count = 0

        for bet in pending:
            bet_id = bet['bet_id']
            date = bet['date']
            sport = bet['sport']
            game = bet['game']

            # Only update bets from past dates
            bet_date = datetime.strptime(date, '%Y-%m-%d').date()
            today = datetime.now().date()

            if bet_date >= today:
                # Game hasn't happened yet or is today
                skipped_count += 1
                continue

            print(f"Checking {bet_id}...")

            # Get game result
            if sport == 'NHL':
                result = self._get_nhl_result(date, game, bet)
            elif sport == 'NBA':
                result = self._get_nba_result(date, game, bet)
            else:
                print(f"   ⚠️  Sport {sport} not supported for auto-update")
                continue

            if result:
                self.tracker.update_result(bet_id, result)
                updated_count += 1
            else:
                print(f"   ⚠️  Could not determine result")

        print(f"\n{'='*80}")
        print(f"✅ UPDATED: {updated_count} bets")
        print(f"⏳ SKIPPED: {skipped_count} bets (games not yet played)")
        print(f"{'='*80}\n")

        # Show updated dashboard
        if updated_count > 0:
            self.tracker.display_dashboard()

    def _get_nhl_result(self, date: str, game_str: str, bet: Dict) -> Optional[str]:
        """Get NHL game result and determine if bet won"""

        try:
            # Parse teams from game string (e.g., "BOS @ NYR")
            parts = game_str.split('@')
            if len(parts) != 2:
                return None

            away_team = parts[0].strip()
            home_team = parts[1].strip()

            # Fetch NHL schedule with scores
            url = f"https://api-web.nhle.com/v1/schedule/{date}"
            response = requests.get(url, timeout=30)

            if response.status_code != 200:
                return None

            data = response.json()
            game_week = data.get('gameWeek', [])

            for day in game_week:
                if day.get('date') == date:
                    games = day.get('games', [])

                    for game in games:
                        game_home = game.get('homeTeam', {}).get('abbrev', '')
                        game_away = game.get('awayTeam', {}).get('abbrev', '')

                        # Match teams
                        if game_home == home_team and game_away == away_team:
                            # Check if game is final
                            game_state = game.get('gameState', '')
                            if game_state not in ['OFF', 'FINAL']:
                                print(f"   ⏳ Game not final yet (state: {game_state})")
                                return None

                            # Get score
                            home_score = game.get('homeTeam', {}).get('score')
                            away_score = game.get('awayTeam', {}).get('score')

                            if home_score is None or away_score is None:
                                return None

                            # Convert to int to avoid comparison issues
                            home_score = int(home_score)
                            away_score = int(away_score)

                            # Determine winner
                            home_won = home_score > away_score

                            # Check if our bet won
                            bet_text = bet['bet']

                            if home_team in bet_text or f"{home_team} ML" in bet_text:
                                result = 'WIN' if home_won else 'LOSS'
                                print(f"   {result}: {home_team} {home_score} - {away_team} {away_score}")
                                return result
                            elif away_team in bet_text or f"{away_team} ML" in bet_text:
                                result = 'WIN' if not home_won else 'LOSS'
                                print(f"   {result}: {away_team} {away_score} - {home_team} {home_score}")
                                return result

        except Exception as e:
            print(f"   ❌ Error: {e}")

        return None

    def _get_nba_result(self, date: str, game_str: str, bet: Dict) -> Optional[str]:
        """Get NBA game result and determine if bet won"""

        try:
            # Parse teams from game string
            parts = game_str.split('@')
            if len(parts) != 2:
                return None

            away_team = parts[0].strip()
            home_team = parts[1].strip()

            # Fetch NBA scoreboard for that date
            url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
            params = {'dates': date.replace('-', '')}  # ESPN uses YYYYMMDD format

            response = requests.get(url, params=params, timeout=30)

            if response.status_code != 200:
                return None

            data = response.json()
            events = data.get('events', [])

            for event in events:
                competitions = event.get('competitions', [])
                if not competitions:
                    continue

                competition = competitions[0]
                competitors = competition.get('competitors', [])

                if len(competitors) < 2:
                    continue

                # Find home and away teams
                home = next((c for c in competitors if c.get('homeAway') == 'home'), None)
                away = next((c for c in competitors if c.get('homeAway') == 'away'), None)

                if not home or not away:
                    continue

                game_home = home.get('team', {}).get('displayName', '')
                game_away = away.get('team', {}).get('displayName', '')

                # Match teams (fuzzy)
                if (home_team in game_home or game_home in home_team) and \
                   (away_team in game_away or game_away in away_team):

                    # Check if game is complete
                    status = competition.get('status', {}).get('type', {}).get('state', '')
                    if status != 'post':
                        print(f"   ⏳ Game not complete yet (status: {status})")
                        return None

                    # Get scores
                    home_score = int(home.get('score', 0))
                    away_score = int(away.get('score', 0))

                    if home_score == 0 and away_score == 0:
                        return None

                    # Determine winner
                    home_won = home_score > away_score

                    # Check if our bet won
                    bet_text = bet['bet']

                    if home_team in bet_text:
                        result = 'WIN' if home_won else 'LOSS'
                        print(f"   {result}: {home_team} {home_score} - {away_team} {away_score}")
                        return result
                    elif away_team in bet_text:
                        result = 'WIN' if not home_won else 'LOSS'
                        print(f"   {result}: {away_team} {away_score} - {home_team} {home_score}")
                        return result

        except Exception as e:
            print(f"   ❌ Error: {e}")

        return None


def main():
    updater = AutoResultsUpdater()
    updater.update_all_pending_bets()


if __name__ == "__main__":
    main()
