#!/usr/bin/env python3
"""
Fetch Team-Specific Statistics
Pulls historical team performance data from API to improve predictions
"""

import requests
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

class TeamStatisticsFetcher:
    """Fetch and store team-specific statistics"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_base = "https://v3.football.api-sports.io"
        self.headers = {"x-apisports-key": api_key}
        self.stats_file = Path('team_statistics.json')
        self.team_stats = self.load_existing_stats()

    def load_existing_stats(self):
        """Load existing team statistics"""
        if self.stats_file.exists():
            with open(self.stats_file, 'r') as f:
                stats = json.load(f)
                print(f"📚 Loaded statistics for {len(stats)} teams")
                return stats
        return {}

    def save_stats(self):
        """Save team statistics to file"""
        with open(self.stats_file, 'w') as f:
            json.dump(self.team_stats, f, indent=2)
        print(f"💾 Saved statistics for {len(self.team_stats)} teams")

    def find_team_league(self, team_id: int, season: int = 2024):
        """Find the league ID for a team from recent fixtures"""

        try:
            # Look at recent fixtures to find the team's league
            url = f"{self.api_base}/fixtures"
            params = {
                "team": team_id,
                "season": season,
                "last": 10  # Check last 10 fixtures
            }

            response = requests.get(url, headers=self.headers, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                fixtures = data.get('response', [])

                if fixtures:
                    # Use the league from the most recent fixture
                    league_id = fixtures[0]['league']['id']
                    return league_id

            return None

        except Exception as e:
            print(f"   ⚠️  Error finding league: {e}")
            return None

    def fetch_team_statistics(self, team_id: int, season: int = 2024, league_id: int = None):
        """Fetch detailed statistics for a specific team"""

        # Check if we already have recent stats
        team_key = f"{team_id}_{season}"
        if team_key in self.team_stats:
            # If stats are less than 7 days old, use cached version
            last_updated = datetime.fromisoformat(self.team_stats[team_key].get('last_updated', '2000-01-01'))
            if (datetime.now() - last_updated).days < 7:
                return self.team_stats[team_key]

        # If no league specified, try to find it from recent fixtures
        if league_id is None:
            league_id = self.find_team_league(team_id, season)
            if league_id is None:
                print(f"   ⚠️  Could not determine league for team {team_id}")
                return None

        try:
            # Fetch team statistics
            url = f"{self.api_base}/teams/statistics"
            params = {
                "team": team_id,
                "season": season,
                "league": league_id
            }

            response = requests.get(url, headers=self.headers, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                response_data = data.get('response', {})

                if response_data:
                    # Extract key statistics
                    stats = {
                        'team_id': team_id,
                        'season': season,
                        'last_updated': datetime.now().isoformat(),

                        # Match stats
                        'played': response_data.get('fixtures', {}).get('played', {}).get('total', 0),
                        'wins_home': response_data.get('fixtures', {}).get('wins', {}).get('home', 0),
                        'wins_away': response_data.get('fixtures', {}).get('wins', {}).get('away', 0),
                        'draws_home': response_data.get('fixtures', {}).get('draws', {}).get('home', 0),
                        'draws_away': response_data.get('fixtures', {}).get('draws', {}).get('away', 0),
                        'loses_home': response_data.get('fixtures', {}).get('loses', {}).get('home', 0),
                        'loses_away': response_data.get('fixtures', {}).get('loses', {}).get('away', 0),

                        # Goals
                        'goals_for_avg_home': float(response_data.get('goals', {}).get('for', {}).get('average', {}).get('home', '0') or 0),
                        'goals_for_avg_away': float(response_data.get('goals', {}).get('for', {}).get('average', {}).get('away', '0') or 0),
                        'goals_against_avg_home': float(response_data.get('goals', {}).get('against', {}).get('average', {}).get('home', '0') or 0),
                        'goals_against_avg_away': float(response_data.get('goals', {}).get('against', {}).get('average', {}).get('away', '0') or 0),

                        # Clean sheets
                        'clean_sheets_home': response_data.get('clean_sheet', {}).get('home', 0),
                        'clean_sheets_away': response_data.get('clean_sheet', {}).get('away', 0),
                        'failed_to_score_home': response_data.get('failed_to_score', {}).get('home', 0),
                        'failed_to_score_away': response_data.get('failed_to_score', {}).get('away', 0),
                    }

                    # Store in cache
                    self.team_stats[team_key] = stats
                    return stats

            return None

        except Exception as e:
            print(f"   ❌ Error fetching team {team_id}: {e}")
            return None

    def fetch_teams_from_recent_matches(self, days_back: int = 7):
        """Fetch team IDs from recent matches"""

        print(f"\n📊 Fetching teams from matches in last {days_back} days...")

        teams_found = set()

        for days_ago in range(days_back):
            date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')

            try:
                url = f"{self.api_base}/fixtures"
                params = {"date": date}

                response = requests.get(url, headers=self.headers, params=params, timeout=15)

                if response.status_code == 200:
                    data = response.json()
                    fixtures = data.get('response', [])

                    for fixture in fixtures:
                        home_id = fixture['teams']['home']['id']
                        away_id = fixture['teams']['away']['id']
                        teams_found.add(home_id)
                        teams_found.add(away_id)

                    print(f"   {date}: {len(fixtures)} matches, {len(teams_found)} unique teams so far")

                time.sleep(0.5)  # Rate limiting

            except Exception as e:
                print(f"   ⚠️  Error on {date}: {e}")
                continue

        return list(teams_found)

    def backfill_team_stats(self, season: int = 2024, limit: int = 100):
        """Backfill statistics for recently active teams"""

        print(f"\n{'='*70}")
        print(f"⚽ TEAM STATISTICS BACKFILL - Season {season}")
        print(f"{'='*70}\n")

        # Get teams from recent matches
        team_ids = self.fetch_teams_from_recent_matches(days_back=7)

        if not team_ids:
            print("❌ No teams found")
            return

        print(f"\n📊 Fetching statistics for {len(team_ids)} teams (limit: {limit})...")

        success_count = 0
        for i, team_id in enumerate(team_ids[:limit], 1):
            print(f"\n   [{i}/{min(len(team_ids), limit)}] Team ID: {team_id}")

            stats = self.fetch_team_statistics(team_id, season)

            if stats:
                success_count += 1
                print(f"      ✅ Fetched stats")
            else:
                print(f"      ⚠️  No stats available")

            # Rate limiting - API-Football allows requests per minute
            if i % 10 == 0:
                print(f"\n   ⏸️  Pausing for rate limit...")
                time.sleep(6)  # 6 seconds pause every 10 requests
            else:
                time.sleep(1)  # 1 second between requests

        # Save all stats
        self.save_stats()

        print(f"\n{'='*70}")
        print(f"✅ BACKFILL COMPLETE")
        print(f"{'='*70}")
        print(f"   Teams processed: {min(len(team_ids), limit)}")
        print(f"   Successful: {success_count}")
        print(f"   Stats file: {self.stats_file}")
        print(f"{'='*70}\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Fetch team-specific statistics')
    parser.add_argument('--season', type=int, default=2024, help='Season year (default: 2024)')
    parser.add_argument('--limit', type=int, default=100, help='Max teams to fetch (default: 100)')

    args = parser.parse_args()

    # API key
    api_key = "960c628e1c91c4b1f125e1eec52ad862"

    # Confirm with user
    print(f"\n⚠️  This will fetch team statistics for up to {args.limit} teams")
    print(f"   Season: {args.season}")
    print(f"   Estimated API calls: ~{args.limit}")
    print(f"   Estimated time: ~{args.limit // 10 + 1} minutes")
    response = input(f"\n   Continue? (y/n): ")

    if response.lower() != 'y':
        print("❌ Cancelled")
        return

    # Run backfill
    fetcher = TeamStatisticsFetcher(api_key)
    fetcher.backfill_team_stats(season=args.season, limit=args.limit)


if __name__ == "__main__":
    main()
