#!/usr/bin/env python3
"""
AWS Team Statistics Fetcher and Model Trainer
Fetches team statistics for all supported leagues and retrains models
"""

import requests
import pandas as pd
import json
import time
from datetime import datetime
from collections import defaultdict

class TeamStatsFetcher:
    """Fetch team statistics for supported leagues"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_base = "https://v3.football.api-sports.io"
        self.headers = {"x-apisports-key": api_key}
        self.request_count = 0
        self.max_requests = 1000  # Safety limit

    def fetch_teams_for_league(self, league_id: int, season: int = 2024):
        """Fetch all teams in a league"""
        url = f"{self.api_base}/teams"
        params = {"league": league_id, "season": season}

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            self.request_count += 1

            if response.status_code == 200:
                data = response.json()
                return data.get('response', [])
            else:
                print(f"      ⚠️  API error {response.status_code} for league {league_id}")
                return []
        except Exception as e:
            print(f"      ❌ Error fetching teams: {e}")
            return []

    def fetch_team_statistics(self, team_id: int, league_id: int, season: int = 2024):
        """Fetch statistics for a specific team"""
        url = f"{self.api_base}/teams/statistics"
        params = {"team": team_id, "league": league_id, "season": season}

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            self.request_count += 1

            if response.status_code == 200:
                data = response.json()
                return data.get('response', {})
            else:
                return None
        except Exception as e:
            return None

    def process_team_stats(self, stats_data, team_id: int, season: int):
        """Process raw API stats into our format"""
        if not stats_data:
            return None

        fixtures = stats_data.get('fixtures', {})
        played = fixtures.get('played', {}).get('total', 0)

        if played == 0:
            return None

        goals = stats_data.get('goals', {})
        goals_for = goals.get('for', {})
        goals_against = goals.get('against', {})

        # Extract statistics
        processed = {
            'team_id': team_id,
            'season': season,
            'played': played,
            'wins': fixtures.get('wins', {}).get('total', 0),
            'draws': fixtures.get('draws', {}).get('total', 0),
            'losses': fixtures.get('loses', {}).get('total', 0),

            # Goals
            'goals_for_total': goals_for.get('total', {}).get('total', 0),
            'goals_for_home': goals_for.get('total', {}).get('home', 0),
            'goals_for_away': goals_for.get('total', {}).get('away', 0),
            'goals_against_total': goals_against.get('total', {}).get('total', 0),
            'goals_against_home': goals_against.get('total', {}).get('home', 0),
            'goals_against_away': goals_against.get('total', {}).get('away', 0),

            # Calculate averages
            'goals_for_avg': goals_for.get('total', {}).get('total', 0) / played if played > 0 else 0,
            'goals_for_avg_home': goals_for.get('total', {}).get('home', 0) / (played / 2) if played > 0 else 0,
            'goals_for_avg_away': goals_for.get('total', {}).get('away', 0) / (played / 2) if played > 0 else 0,
            'goals_against_avg': goals_against.get('total', {}).get('total', 0) / played if played > 0 else 0,
            'goals_against_avg_home': goals_against.get('total', {}).get('home', 0) / (played / 2) if played > 0 else 0,
            'goals_against_avg_away': goals_against.get('total', {}).get('away', 0) / (played / 2) if played > 0 else 0,
        }

        return processed

    def fetch_all_statistics(self, leagues_file: str, season: int = 2024):
        """Fetch statistics for all teams in supported leagues"""

        # Load supported leagues
        df_leagues = pd.read_csv(leagues_file)
        print(f"📊 Loaded {len(df_leagues)} supported leagues")

        all_team_stats = {}
        total_teams = 0

        for idx, row in df_leagues.iterrows():
            league_id = row['league_id']
            league_name = row['league_name']
            country = row['country']

            if self.request_count >= self.max_requests:
                print(f"\n⚠️  Reached request limit ({self.max_requests})")
                break

            print(f"\n[{idx+1}/{len(df_leagues)}] {league_name} ({country}) - League ID: {league_id}")

            # Fetch teams in league
            teams = self.fetch_teams_for_league(league_id, season)

            if not teams:
                print(f"   ⚠️  No teams found")
                continue

            print(f"   ✅ Found {len(teams)} teams")

            # Fetch stats for each team
            league_team_count = 0
            for team_data in teams:
                if self.request_count >= self.max_requests:
                    break

                team = team_data.get('team', {})
                team_id = team.get('id')
                team_name = team.get('name')

                # Fetch team statistics
                stats_data = self.fetch_team_statistics(team_id, league_id, season)

                if stats_data:
                    processed_stats = self.process_team_stats(stats_data, team_id, season)

                    if processed_stats:
                        key = f"{team_id}_{season}"
                        all_team_stats[key] = processed_stats
                        league_team_count += 1
                        total_teams += 1

                # Rate limiting
                time.sleep(0.2)

            print(f"   📊 Fetched stats for {league_team_count} teams")
            print(f"   🔢 Total teams so far: {total_teams}")
            print(f"   📡 API requests used: {self.request_count}/{self.max_requests}")

        return all_team_stats


def main():
    print("="*80)
    print("⚽ AWS TEAM STATISTICS FETCHER & MODEL TRAINER")
    print("="*80)

    api_key = "960c628e1c91c4b1f125e1eec52ad862"

    # Step 1: Fetch team statistics
    print("\n📥 STEP 1: Fetching team statistics...")
    print("-"*80)

    fetcher = TeamStatsFetcher(api_key)
    team_stats = fetcher.fetch_all_statistics(
        'output reports/Older/UPDATED_supported_leagues_database.csv',
        season=2024
    )

    # Save statistics
    print(f"\n💾 Saving statistics...")
    stats_file = 'team_statistics.json'
    with open(stats_file, 'w') as f:
        json.dump(team_stats, f, indent=2)

    print(f"✅ Saved statistics for {len(team_stats)} teams to {stats_file}")
    print(f"📡 Total API requests: {fetcher.request_count}")

    # Step 2: Retrain models
    print(f"\n🔄 STEP 2: Retraining models with new data...")
    print("-"*80)

    import subprocess
    result = subprocess.run(['python3', 'soccer_trainer.py'], capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ Model training completed successfully")
        print(result.stdout)
    else:
        print("❌ Model training failed")
        print(result.stderr)

    print(f"\n{'='*80}")
    print(f"✅ COMPLETE")
    print(f"   - Team statistics: {len(team_stats)} teams")
    print(f"   - API requests: {fetcher.request_count}")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
