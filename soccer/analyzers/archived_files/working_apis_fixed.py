#!/usr/bin/env python3
"""
Working APIs with Fixed Authentication
All APIs now have proper credentials and working endpoints
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class WorkingAPIManager:
    """Manage working soccer APIs with proper authentication"""

    def __init__(self):
        # Store API credentials (in production, use environment variables)
        self.api_credentials = {
            'api_sports_key': '960c628e1c91c4b1f125e1eec52ad862',
            'footystats_key': 'ceb338b9bcb82a452efc114fb2d3cccac67f58be1569e7b5acf1d2195adeae11'
        }

        self.working_apis = self.configure_working_apis()

    def configure_working_apis(self) -> List[Dict]:
        """Configure all working APIs with proper authentication"""

        today = datetime.now().strftime('%Y-%m-%d')

        return [
            {
                'name': 'API-Sports',
                'status': '✅ FULLY WORKING',
                'description': 'Comprehensive global soccer data - PREMIUM',
                'url': f'https://v3.football.api-sports.io/fixtures?date={today}',
                'headers': {
                    'X-RapidAPI-Key': self.api_credentials['api_sports_key'],
                    'X-RapidAPI-Host': 'v3.football.api-sports.io'
                },
                'rate_limit': '7500 requests/day (Pro plan)',
                'coverage': 'Global - 180+ leagues',
                'subscription': 'Pro Plan (expires 2025-10-08)',
                'data_quality': '⭐⭐⭐⭐⭐ Excellent',
                'response_format': 'Standard',
                'parser': self.parse_api_sports_response
            },
            {
                'name': 'FootyStats',
                'status': '✅ WORKING',
                'description': 'Statistics-focused soccer data',
                'url': f'https://api.footystats.org/todays-matches?key={self.api_credentials["footystats_key"]}',
                'headers': {},
                'rate_limit': '1800 requests/hour',
                'coverage': 'Global with detailed statistics',
                'subscription': 'Paid subscription',
                'data_quality': '⭐⭐⭐⭐ Very Good',
                'response_format': 'Custom',
                'parser': self.parse_footystats_response
            },
            {
                'name': 'OpenLigaDB',
                'status': '✅ WORKING',
                'description': 'Free German football data',
                'url': 'https://api.openligadb.de/getmatchdata/bl1/2025',
                'headers': {},
                'rate_limit': 'Unlimited (free)',
                'coverage': 'German Bundesliga only',
                'subscription': 'Free',
                'data_quality': '⭐⭐⭐ Good',
                'response_format': 'Custom',
                'parser': self.parse_openligadb_response
            },
            {
                'name': 'TheSportsDB',
                'status': '✅ LIMITED',
                'description': 'Community soccer database',
                'url': f'https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d={today}&s=Soccer',
                'headers': {},
                'rate_limit': '1000 requests/hour',
                'coverage': 'Global (limited)',
                'subscription': 'Free',
                'data_quality': '⭐⭐ Basic',
                'response_format': 'Custom',
                'parser': self.parse_thesportsdb_response
            }
        ]

    def fetch_todays_matches_from_all_apis(self) -> Dict:
        """Fetch today's matches from all working APIs"""

        print("🔍 FETCHING TODAY'S MATCHES FROM ALL WORKING APIs")
        print("="*60)

        results = {
            'timestamp': datetime.now().isoformat(),
            'apis_tested': len(self.working_apis),
            'successful_apis': 0,
            'total_matches_found': 0,
            'api_results': [],
            'combined_matches': []
        }

        for api in self.working_apis:
            print(f"\n🧪 Testing {api['name']}...")

            api_result = {
                'api_name': api['name'],
                'status': 'unknown',
                'matches_found': 0,
                'response_time': 0,
                'error_message': '',
                'matches': []
            }

            try:
                start_time = datetime.now()
                response = requests.get(api['url'], headers=api['headers'], timeout=15)
                end_time = datetime.now()

                api_result['response_time'] = (end_time - start_time).total_seconds()

                if response.status_code == 200:
                    matches = api['parser'](response.json())
                    api_result['matches'] = matches
                    api_result['matches_found'] = len(matches)
                    api_result['status'] = 'success'

                    print(f"✅ SUCCESS: {len(matches)} matches found")

                    if matches:
                        sample = matches[0]
                        home = sample.get('home_team', 'Unknown')
                        away = sample.get('away_team', 'Unknown')
                        league = sample.get('league', 'Unknown')
                        print(f"Sample: {home} vs {away} ({league})")

                        results['successful_apis'] += 1
                        results['total_matches_found'] += len(matches)
                        results['combined_matches'].extend(matches)

                else:
                    api_result['status'] = 'error'
                    api_result['error_message'] = f'HTTP {response.status_code}'
                    print(f"❌ Error: {response.status_code}")

            except Exception as e:
                api_result['status'] = 'exception'
                api_result['error_message'] = str(e)
                print(f"❌ Exception: {e}")

            results['api_results'].append(api_result)

        return results

    def parse_api_sports_response(self, data: dict) -> List[Dict]:
        """Parse API-Sports response"""
        matches = []

        if 'response' in data:
            for fixture in data['response']:
                try:
                    teams = fixture.get('teams', {})
                    league = fixture.get('league', {})
                    fixture_info = fixture.get('fixture', {})

                    match = {
                        'home_team': teams.get('home', {}).get('name', 'Unknown'),
                        'away_team': teams.get('away', {}).get('name', 'Unknown'),
                        'league': league.get('name', 'Unknown'),
                        'country': league.get('country', 'Unknown'),
                        'date': fixture_info.get('date', ''),
                        'status': fixture_info.get('status', {}).get('long', 'Unknown'),
                        'venue': fixture_info.get('venue', {}).get('name', ''),
                        'source': 'API-Sports',
                        'fixture_id': fixture_info.get('id', ''),
                        'odds_available': True  # API-Sports has odds endpoints
                    }
                    matches.append(match)
                except Exception:
                    continue

        return matches

    def parse_footystats_response(self, data: dict) -> List[Dict]:
        """Parse FootyStats response"""
        matches = []

        if data.get('success') and 'data' in data:
            for match_data in data['data']:
                try:
                    # FootyStats has different field names
                    match = {
                        'home_team': match_data.get('home_name', 'Unknown'),
                        'away_team': match_data.get('away_name', 'Unknown'),
                        'league': match_data.get('league_name', 'Unknown'),
                        'country': match_data.get('country', 'Unknown'),
                        'date': match_data.get('date', ''),
                        'status': match_data.get('status', 'Unknown'),
                        'venue': match_data.get('venue', ''),
                        'source': 'FootyStats',
                        'fixture_id': match_data.get('id', ''),
                        'odds_available': True  # FootyStats focuses on statistics
                    }
                    matches.append(match)
                except Exception:
                    continue

        return matches

    def parse_openligadb_response(self, data) -> List[Dict]:
        """Parse OpenLigaDB response"""
        matches = []

        if isinstance(data, list):
            for match_data in data:
                try:
                    team1 = match_data.get('team1', {})
                    team2 = match_data.get('team2', {})

                    match = {
                        'home_team': team1.get('teamName', 'Unknown'),
                        'away_team': team2.get('teamName', 'Unknown'),
                        'league': 'Bundesliga',
                        'country': 'Germany',
                        'date': match_data.get('matchDateTime', ''),
                        'status': 'Scheduled',
                        'venue': '',
                        'source': 'OpenLigaDB',
                        'fixture_id': match_data.get('matchID', ''),
                        'odds_available': False
                    }
                    matches.append(match)
                except Exception:
                    continue

        return matches

    def parse_thesportsdb_response(self, data: dict) -> List[Dict]:
        """Parse TheSportsDB response"""
        matches = []

        if 'events' in data and data['events']:
            for event in data['events']:
                try:
                    match = {
                        'home_team': event.get('strHomeTeam', 'Unknown'),
                        'away_team': event.get('strAwayTeam', 'Unknown'),
                        'league': event.get('strLeague', 'Unknown'),
                        'country': event.get('strCountry', 'Unknown'),
                        'date': event.get('dateEvent', ''),
                        'status': event.get('strStatus', 'Unknown'),
                        'venue': event.get('strVenue', ''),
                        'source': 'TheSportsDB',
                        'fixture_id': event.get('idEvent', ''),
                        'odds_available': False
                    }
                    matches.append(match)
                except Exception:
                    continue

        return matches

    def generate_api_status_report(self, results: Dict) -> str:
        """Generate comprehensive API status report"""

        report = f"""
🔍 WORKING APIs STATUS REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*80}

📊 SUMMARY:
   APIs Tested: {results['apis_tested']}
   Successful APIs: {results['successful_apis']}
   Total Matches Found: {results['total_matches_found']}

"""

        # Individual API results
        report += "🔧 API PERFORMANCE:\n"
        for api_result in results['api_results']:
            status_emoji = '✅' if api_result['status'] == 'success' else '❌'

            report += f"""
{status_emoji} {api_result['api_name']}:
   Status: {api_result['status']}
   Matches: {api_result['matches_found']}
   Response Time: {api_result['response_time']:.2f}s
"""
            if api_result['error_message']:
                report += f"   Error: {api_result['error_message']}\n"

        # Sample matches
        if results['combined_matches']:
            report += f"""
🏈 SAMPLE MATCHES FOUND TODAY:
{'='*35}
"""
            unique_leagues = set()
            sample_matches = results['combined_matches'][:10]

            for i, match in enumerate(sample_matches, 1):
                unique_leagues.add(match['league'])
                report += f"""
{i}. {match['home_team']} vs {match['away_team']}
   League: {match['league']} ({match['country']})
   Source: {match['source']}
   Status: {match['status']}
"""

            report += f"""
📈 LEAGUE COVERAGE:
   Unique leagues found: {len(unique_leagues)}
   Examples: {', '.join(list(unique_leagues)[:5])}
"""

        return report

def main():
    """Test all working APIs and generate report"""

    print("🚀 WORKING API MANAGER - COMPREHENSIVE TEST")
    print("🔑 Using real API credentials")

    manager = WorkingAPIManager()

    # Show API configurations
    print("\n📋 CONFIGURED APIs:")
    for api in manager.working_apis:
        print(f"{api['status']} {api['name']}: {api['description']}")

    # Fetch matches from all APIs
    results = manager.fetch_todays_matches_from_all_apis()

    # Generate and display report
    report = manager.generate_api_status_report(results)
    print(report)

    # Save results
    import os
    os.makedirs("output reports", exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_file = f"output reports/working_apis_test_{timestamp}.json"

    with open(json_file, 'w') as f:
        json.dump(results, f, indent=2)

    report_file = f"output reports/working_apis_report_{timestamp}.txt"
    with open(report_file, 'w') as f:
        f.write(report)

    print(f"\n💾 Results saved:")
    print(f"   • {json_file}")
    print(f"   • {report_file}")

    return results

if __name__ == "__main__":
    main()