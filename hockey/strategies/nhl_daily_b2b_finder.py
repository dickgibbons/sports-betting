#!/usr/bin/env python3
"""
NHL Daily Back-to-Back Finder

Identifies today's games where teams are in back-to-back situations,
with special focus on ROAD → ROAD patterns (best betting opportunity).

Usage:
    python3 nhl_daily_b2b_finder.py
    python3 nhl_daily_b2b_finder.py --date 2024-11-15
"""

import requests
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class NHLDailyB2BFinder:
    """Find back-to-back situations in today's NHL games"""

    def __init__(self):
        """Initialize the finder"""
        self.nhl_api_base = "https://api-web.nhle.com/v1"

    def fetch_schedule(self, date_str: str) -> List[Dict]:
        """Fetch NHL schedule for a specific date"""
        try:
            url = f"{self.nhl_api_base}/schedule/{date_str}"
            response = requests.get(url, timeout=30)

            if response.status_code == 200:
                data = response.json()
                game_week = data.get('gameWeek', [])

                for day in game_week:
                    if day.get('date') == date_str:
                        return day.get('games', [])

            return []
        except Exception as e:
            print(f"⚠️  Error fetching schedule: {e}")
            return []

    def get_team_last_game(self, team_abbrev: str, before_date: str) -> Optional[Dict]:
        """Get a team's most recent game before the specified date"""
        try:
            # Check yesterday
            date_obj = datetime.strptime(before_date, '%Y-%m-%d')
            yesterday = (date_obj - timedelta(days=1)).strftime('%Y-%m-%d')

            url = f"{self.nhl_api_base}/schedule/{yesterday}"
            response = requests.get(url, timeout=30)

            if response.status_code == 200:
                data = response.json()
                game_week = data.get('gameWeek', [])

                for day in game_week:
                    if day.get('date') == yesterday:
                        games = day.get('games', [])

                        for game in games:
                            game_state = game.get('gameState', 'UNKNOWN')

                            # Only consider finished games
                            if game_state in ['OFF', 'FINAL']:
                                home_team = game.get('homeTeam', {}).get('abbrev', '')
                                away_team = game.get('awayTeam', {}).get('abbrev', '')

                                if home_team == team_abbrev:
                                    return {
                                        'date': yesterday,
                                        'location': 'home',
                                        'opponent': away_team,
                                        'game': game
                                    }
                                elif away_team == team_abbrev:
                                    return {
                                        'date': yesterday,
                                        'location': 'road',
                                        'opponent': home_team,
                                        'game': game
                                    }

            return None
        except Exception as e:
            print(f"⚠️  Error fetching last game for {team_abbrev}: {e}")
            return None

    def analyze_todays_games(self, date_str: str = None):
        """Analyze today's games for back-to-back situations"""
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')

        print(f"\n{'='*80}")
        print(f"🏒 NHL DAILY BACK-TO-BACK FINDER")
        print(f"{'='*80}")
        print(f"Date: {date_str}")
        print(f"{'='*80}\n")

        # Fetch today's schedule
        todays_games = self.fetch_schedule(date_str)

        if not todays_games:
            print("⚠️  No games scheduled for today")
            return

        print(f"📊 Found {len(todays_games)} games scheduled\n")

        # Analyze each game
        b2b_situations = []

        for game in todays_games:
            game_state = game.get('gameState', 'UNKNOWN')

            # Skip finished games
            if game_state in ['OFF', 'FINAL']:
                continue

            home_team = game.get('homeTeam', {})
            away_team = game.get('awayTeam', {})

            home_abbrev = home_team.get('abbrev', 'UNK')
            away_abbrev = away_team.get('abbrev', 'UNK')

            home_name = home_team.get('placeName', {}).get('default', home_abbrev)
            away_name = away_team.get('placeName', {}).get('default', away_abbrev)

            game_time = game.get('startTimeUTC', '')

            # Check if home team played yesterday
            home_last_game = self.get_team_last_game(home_abbrev, date_str)

            # Check if away team played yesterday
            away_last_game = self.get_team_last_game(away_abbrev, date_str)

            # Determine back-to-back situations
            home_b2b_pattern = None
            away_b2b_pattern = None

            if home_last_game:
                if home_last_game['location'] == 'home':
                    home_b2b_pattern = 'HOME → HOME'
                else:
                    home_b2b_pattern = 'ROAD → HOME'

            if away_last_game:
                if away_last_game['location'] == 'home':
                    away_b2b_pattern = 'HOME → ROAD'
                else:
                    away_b2b_pattern = 'ROAD → ROAD'

            # Store the situation
            situation = {
                'game_time': game_time,
                'home_team': home_name,
                'home_abbrev': home_abbrev,
                'away_team': away_name,
                'away_abbrev': away_abbrev,
                'home_b2b': home_b2b_pattern,
                'away_b2b': away_b2b_pattern,
                'home_last_game': home_last_game,
                'away_last_game': away_last_game
            }

            b2b_situations.append(situation)

        # Display results
        self.display_results(b2b_situations)

    def display_results(self, situations: List[Dict]):
        """Display the analysis results"""

        # Filter for games with B2B situations
        b2b_games = [s for s in situations if s['home_b2b'] or s['away_b2b']]

        if not b2b_games:
            print("✅ No back-to-back situations today")
            print("   All teams are well-rested!\n")
            return

        print(f"{'='*80}")
        print(f"📊 BACK-TO-BACK SITUATIONS TODAY ({len(b2b_games)} games)")
        print(f"{'='*80}\n")

        # Priority 1: ROAD → ROAD situations (BEST BETS)
        road_road = [s for s in b2b_games if s['away_b2b'] == 'ROAD → ROAD']

        if road_road:
            print(f"🔥 BEST BETTING OPPORTUNITIES - ROAD → ROAD Pattern")
            print(f"{'─'*80}")
            print(f"Historical win rate when betting ON home team: 57.6%")
            print(f"Expected edge: +7.6% (profitable at -110 odds)")
            print(f"{'─'*80}\n")

            for idx, situation in enumerate(road_road, 1):
                self.display_situation(situation, idx, bet_recommendation='STRONG')

        # Priority 2: HOME → ROAD situations (GOOD BETS)
        home_road = [s for s in b2b_games if s['away_b2b'] == 'HOME → ROAD']

        if home_road:
            print(f"\n✅ GOOD BETTING OPPORTUNITIES - HOME → ROAD Pattern")
            print(f"{'─'*80}")
            print(f"Historical win rate when betting ON home team: 56.7%")
            print(f"Expected edge: +6.7% (profitable at -110 odds)")
            print(f"{'─'*80}\n")

            for idx, situation in enumerate(home_road, 1):
                self.display_situation(situation, idx, bet_recommendation='GOOD')

        # Priority 3: Other B2B patterns
        other_b2b = [s for s in b2b_games if s['away_b2b'] not in ['ROAD → ROAD', 'HOME → ROAD']
                     and (s['home_b2b'] or s['away_b2b'])]

        if other_b2b:
            print(f"\n📊 OTHER BACK-TO-BACK SITUATIONS")
            print(f"{'─'*80}\n")

            for idx, situation in enumerate(other_b2b, 1):
                self.display_situation(situation, idx, bet_recommendation='MONITOR')

        # Summary
        print(f"\n{'='*80}")
        print(f"📈 BETTING SUMMARY")
        print(f"{'='*80}")
        print(f"🔥 STRONG BETS (ROAD → ROAD): {len(road_road)} games")
        print(f"✅ GOOD BETS (HOME → ROAD): {len(home_road)} games")
        print(f"📊 Other B2B situations: {len(other_b2b)} games")
        print(f"{'='*80}\n")

    def display_situation(self, situation: Dict, idx: int, bet_recommendation: str):
        """Display a single back-to-back situation"""

        # Parse game time
        game_time_utc = situation['game_time']
        if game_time_utc:
            try:
                dt = datetime.fromisoformat(game_time_utc.replace('Z', '+00:00'))
                # Convert to local time (you may want to adjust timezone)
                time_str = dt.strftime('%I:%M %p')
            except:
                time_str = 'TBD'
        else:
            time_str = 'TBD'

        print(f"{idx}. {situation['away_team']} @ {situation['home_team']}")
        print(f"   Time: {time_str}")

        # Show B2B patterns
        if situation['away_b2b']:
            print(f"   ⚠️  {situation['away_team']} ({situation['away_abbrev']}): {situation['away_b2b']}")
            if situation['away_last_game']:
                print(f"      Yesterday: vs {situation['away_last_game']['opponent']}")

        if situation['home_b2b']:
            print(f"   🏠 {situation['home_team']} ({situation['home_abbrev']}): {situation['home_b2b']}")
            if situation['home_last_game']:
                print(f"      Yesterday: vs {situation['home_last_game']['opponent']}")

        # Betting recommendation
        if bet_recommendation == 'STRONG':
            print(f"   💰 BET: ON {situation['home_team']} (Strong edge: 57.6% win rate)")
            print(f"   ✅ Profitable at standard -110 odds")
        elif bet_recommendation == 'GOOD':
            print(f"   💰 BET: ON {situation['home_team']} (Good edge: 56.7% win rate)")
            print(f"   ✅ Profitable at standard -110 odds")
        elif bet_recommendation == 'MONITOR':
            if situation['away_b2b']:
                print(f"   📊 Consider: ON {situation['home_team']} (Modest edge)")
            if situation['home_b2b'] == 'ROAD → HOME':
                print(f"   📊 Consider: ON {situation['home_team']} (49.2% historical win rate)")

        print()


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Find NHL back-to-back betting opportunities')
    parser.add_argument('--date', help='Date to analyze (YYYY-MM-DD), defaults to today')

    args = parser.parse_args()

    try:
        finder = NHLDailyB2BFinder()
        finder.analyze_todays_games(args.date)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
