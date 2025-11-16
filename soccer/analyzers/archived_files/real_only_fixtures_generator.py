#!/usr/bin/env python3
"""
Real-Only Daily Fixtures Generator
ONLY uses real API data - NO simulated/generated fixtures
"""

import requests
import json
from datetime import datetime
from api_sports_fallback import APISportsFallback

class RealOnlyFixturesGenerator:
    """Generate daily fixtures from REAL API sources only"""

    def __init__(self, api_key, api_sports_key="960c628e1c91c4b1f125e1eec52ad862"):
        self.api_key = api_key
        self.football_api_base_url = "https://api.football-data-api.com"
        self.api_sports_fallback = APISportsFallback(api_sports_key)

    def get_api_fixtures(self):
        """Get fixtures from FootyStats API"""
        try:
            test_url = f"{self.football_api_base_url}/test-call?key={self.api_key}"
            test_response = requests.get(test_url, timeout=10)

            if test_response.status_code != 200:
                print(f"⚠️ FootyStats API test failed: {test_response.status_code}")
                return []

            fixtures_url = f"{self.football_api_base_url}/todays-matches?key={self.api_key}"
            response = requests.get(fixtures_url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            else:
                print(f"⚠️ FootyStats API failed: {response.status_code}")
                return []

        except Exception as e:
            print(f"❌ FootyStats API error: {e}")
            return []

    def convert_api_fixtures(self, api_fixtures):
        """Convert API fixtures to standard format"""
        converted_fixtures = []

        for fixture in api_fixtures:
            try:
                # Get time from unix timestamp
                time_str = datetime.fromtimestamp(fixture.get('date_unix', 0)).strftime('%H:%M')

                match = {
                    'kick_off': time_str,
                    'home_team': fixture.get('home_name', 'Unknown'),
                    'away_team': fixture.get('away_name', 'Unknown'),
                    'league': fixture.get('competition_name', 'Unknown'),
                    'country': fixture.get('country', 'Unknown'),
                    'home_odds': fixture.get('odds_ft_1', 0),
                    'draw_odds': fixture.get('odds_ft_x', 0),
                    'away_odds': fixture.get('odds_ft_2', 0),
                    'source': 'FootyStats API',
                    'fixture_id': fixture.get('id', 0),
                    'status': fixture.get('status', 'NS')
                }
                converted_fixtures.append(match)
            except Exception as e:
                print(f"⚠️ Error converting fixture: {e}")

        return converted_fixtures

    def get_real_fixtures_only(self):
        """Get ONLY real fixtures from APIs - NO generated data"""

        current_date = datetime.now()
        date_str = current_date.strftime('%Y-%m-%d')
        print(f"\n🌍 REAL-ONLY FIXTURES for {current_date.strftime('%A, %B %d, %Y')}")
        print("=" * 70)

        all_real_fixtures = []

        # 1. Get FootyStats API fixtures
        print(f"\n📡 Fetching from FootyStats API...")
        footystats_raw = self.get_api_fixtures()
        footystats_fixtures = self.convert_api_fixtures(footystats_raw)
        print(f"   ✅ FootyStats: {len(footystats_fixtures)} real fixtures")
        all_real_fixtures.extend(footystats_fixtures)

        # 2. Get API-Sports fixtures
        print(f"\n📡 Fetching from API-Sports...")
        try:
            api_sports_fixtures = self.api_sports_fallback.get_comprehensive_fixtures(date_str)
            print(f"   ✅ API-Sports: {len(api_sports_fixtures)} real fixtures")
            all_real_fixtures.extend(api_sports_fixtures)
        except Exception as e:
            print(f"   ❌ API-Sports error: {e}")

        # Remove duplicates based on home/away team combination
        unique_fixtures = []
        seen_matches = set()

        for fixture in all_real_fixtures:
            match_key = f"{fixture.get('home_team', '')}-{fixture.get('away_team', '')}-{fixture.get('league', '')}"
            if match_key not in seen_matches:
                unique_fixtures.append(fixture)
                seen_matches.add(match_key)

        # Sort by kick-off time
        unique_fixtures.sort(key=lambda x: x.get('kick_off', '00:00'))

        print(f"\n{'='*70}")
        print(f"📊 TOTAL REAL FIXTURES: {len(unique_fixtures)}")
        print(f"{'='*70}")

        # Show breakdown by league and source
        if unique_fixtures:
            league_counts = {}
            for fixture in unique_fixtures:
                league = fixture.get('league', 'Unknown')
                source = fixture.get('source', 'Unknown')
                key = f"{league} ({source})"
                league_counts[key] = league_counts.get(key, 0) + 1

            print(f"\n🏆 LEAGUES WITH REAL DATA TODAY:")
            for league_source, count in sorted(league_counts.items()):
                print(f"   ✅ {league_source}: {count} match{'es' if count > 1 else ''}")
        else:
            print(f"\n⚠️  NO REAL FIXTURES AVAILABLE TODAY")
            print(f"   This could mean:")
            print(f"   - No matches scheduled in tracked leagues")
            print(f"   - API rate limits reached")
            print(f"   - API subscription issues")

        print(f"\n{'='*70}\n")

        return unique_fixtures

    def save_fixtures_to_file(self, fixtures, filename=None):
        """Save fixtures to JSON file"""
        if filename is None:
            date_str = datetime.now().strftime('%Y%m%d')
            filename = f"real_fixtures_{date_str}.json"

        with open(filename, 'w') as f:
            json.dump(fixtures, f, indent=2)

        print(f"💾 Saved {len(fixtures)} real fixtures to: {filename}")
        return filename


def main():
    """Main execution"""
    API_KEY = "ceb338b9bcb82a452efc114fb2d3cccac67f58be1569e7b5acf1d2195adeae11"

    generator = RealOnlyFixturesGenerator(API_KEY)

    # Get ONLY real fixtures
    real_fixtures = generator.get_real_fixtures_only()

    # Save to file
    generator.save_fixtures_to_file(real_fixtures)

    return real_fixtures


if __name__ == "__main__":
    main()
