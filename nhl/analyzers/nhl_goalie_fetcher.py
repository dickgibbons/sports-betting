#!/usr/bin/env python3
"""
NHL Starting Goalie Fetcher
Fetches confirmed starting goalies from Daily Faceoff and other sources
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from typing import Dict, List, Optional
import time

class NHLGoalieFetcher:
    """Fetch and parse starting goalie information"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def get_starting_goalies(self, game_date: str = None) -> Dict[str, Dict]:
        """
        Get confirmed starting goalies for today's games

        Args:
            game_date: Date in format 'YYYY-MM-DD' (default: today)

        Returns:
            Dict mapping game matchup to goalie info:
            {
                'Colorado Avalanche vs Boston Bruins': {
                    'home_team': 'Colorado Avalanche',
                    'away_team': 'Boston Bruins',
                    'home_goalie': 'Alexandar Georgiev',
                    'away_goalie': 'Linus Ullmark',
                    'home_goalie_confirmed': True,
                    'away_goalie_confirmed': True
                }
            }
        """

        # Try multiple sources in order of reliability
        goalies = {}

        # Source 1: Daily Faceoff
        try:
            df_goalies = self._fetch_daily_faceoff()
            if df_goalies:
                goalies.update(df_goalies)
                print(f"✅ Daily Faceoff: {len(df_goalies)} games")
        except Exception as e:
            print(f"⚠️  Daily Faceoff failed: {e}")

        # Source 2: NHL API (backup)
        try:
            nhl_goalies = self._fetch_nhl_api(game_date)
            if nhl_goalies:
                # Merge with existing, prefer Daily Faceoff if conflict
                for game, info in nhl_goalies.items():
                    if game not in goalies:
                        goalies[game] = info
                print(f"✅ NHL API: {len(nhl_goalies)} games")
        except Exception as e:
            print(f"⚠️  NHL API failed: {e}")

        return goalies

    def _fetch_daily_faceoff(self) -> Dict[str, Dict]:
        """Fetch from Daily Faceoff website"""

        url = "https://www.dailyfaceoff.com/starting-goalies/"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            goalies = {}

            # Find goalie starter blocks
            goalie_blocks = soup.find_all('div', class_='starting-goalies-card')

            for block in goalie_blocks:
                try:
                    # Parse game info
                    game_info = block.find('div', class_='game-info')
                    if not game_info:
                        continue

                    teams = game_info.find_all('span', class_='team-name')
                    if len(teams) != 2:
                        continue

                    away_team = teams[0].text.strip()
                    home_team = teams[1].text.strip()

                    # Parse goalie names
                    goalie_names = block.find_all('div', class_='goalie-name')
                    if len(goalie_names) != 2:
                        continue

                    away_goalie = goalie_names[0].text.strip()
                    home_goalie = goalie_names[1].text.strip()

                    # Check if confirmed
                    confirmed_icons = block.find_all('span', class_='confirmed')
                    away_confirmed = len(confirmed_icons) > 0
                    home_confirmed = len(confirmed_icons) > 1 if len(confirmed_icons) > 1 else away_confirmed

                    game_key = f"{home_team} vs {away_team}"

                    goalies[game_key] = {
                        'home_team': home_team,
                        'away_team': away_team,
                        'home_goalie': home_goalie,
                        'away_goalie': away_goalie,
                        'home_goalie_confirmed': home_confirmed,
                        'away_goalie_confirmed': away_confirmed
                    }

                except Exception as e:
                    continue

            return goalies

        except Exception as e:
            raise Exception(f"Daily Faceoff parsing error: {e}")

    def _fetch_nhl_api(self, game_date: str = None) -> Dict[str, Dict]:
        """Fetch from NHL API (backup source)"""

        if not game_date:
            game_date = datetime.now().strftime('%Y-%m-%d')

        url = f"https://api-web.nhle.com/v1/schedule/{game_date}"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            goalies = {}

            if 'gameWeek' not in data:
                return goalies

            for day in data['gameWeek']:
                for game in day.get('games', []):
                    try:
                        home_team = game['homeTeam']['placeName']['default']
                        away_team = game['awayTeam']['placeName']['default']

                        game_key = f"{home_team} vs {away_team}"

                        # NHL API may not have confirmed goalies yet
                        # This is a fallback, we'd need to scrape or use another source
                        goalies[game_key] = {
                            'home_team': home_team,
                            'away_team': away_team,
                            'home_goalie': 'TBD',
                            'away_goalie': 'TBD',
                            'home_goalie_confirmed': False,
                            'away_goalie_confirmed': False
                        }

                    except Exception as e:
                        continue

            return goalies

        except Exception as e:
            raise Exception(f"NHL API error: {e}")

    def save_to_json(self, goalies: Dict, filepath: str):
        """Save goalie data to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(goalies, f, indent=2)
        print(f"💾 Saved goalie data to {filepath}")


def main():
    """Test the goalie fetcher"""
    fetcher = NHLGoalieFetcher()

    print("🏒 Fetching starting goalies...\n")
    goalies = fetcher.get_starting_goalies()

    if not goalies:
        print("⚠️  No goalies found")
        return

    print(f"\n📊 Found {len(goalies)} games:\n")

    for game, info in goalies.items():
        print(f"🏒 {game}")
        print(f"   Home: {info['home_goalie']} {'✅' if info['home_goalie_confirmed'] else '❓'}")
        print(f"   Away: {info['away_goalie']} {'✅' if info['away_goalie_confirmed'] else '❓'}")
        print()

    # Save to file
    date_str = datetime.now().strftime('%Y-%m-%d')
    filepath = f"starting_goalies_{date_str}.json"
    fetcher.save_to_json(goalies, filepath)


if __name__ == '__main__':
    main()
