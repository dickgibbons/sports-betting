#!/usr/bin/env python3
"""
Fixed API Configuration
Provides working configurations for soccer APIs with proper authentication
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional

class FixedAPIConfig:
    """Working API configurations with proper authentication methods"""

    def __init__(self):
        self.working_apis = self.get_working_apis()

    def get_working_apis(self) -> List[Dict]:
        """Get list of working API configurations"""

        return [
            {
                'name': 'OpenLigaDB (German)',
                'description': 'Free German football data - FULLY WORKING',
                'base_url': 'https://api.openligadb.de/getmatchdata/bl1/2025',
                'auth_method': 'none',
                'status': 'working',
                'rate_limit': 'unlimited',
                'coverage': 'German Bundesliga',
                'data_quality': 'excellent'
            },
            {
                'name': 'TheSportsDB',
                'description': 'Free community API - LIMITED BUT WORKING',
                'base_url': 'https://www.thesportsdb.com/api/v1/json/3/eventsday.php',
                'auth_method': 'none',
                'status': 'working',
                'rate_limit': '1000/hour',
                'coverage': 'Global soccer (limited)',
                'data_quality': 'basic'
            },
            {
                'name': 'API-Sports (Fixed)',
                'description': 'Requires paid subscription - PREMIUM',
                'base_url': 'https://v3.football.api-sports.io/fixtures',
                'auth_method': 'api_key_required',
                'status': 'requires_subscription',
                'rate_limit': '100/day (free), 1000/day (paid)',
                'coverage': 'Comprehensive global coverage',
                'data_quality': 'excellent',
                'signup_url': 'https://www.api-football.com/pricing',
                'free_tier': 'Very limited (100 requests/day)'
            },
            {
                'name': 'Football-Data.org (Fixed)',
                'description': 'Official UEFA partner - FREE TIER AVAILABLE',
                'base_url': 'https://api.football-data.org/v4/matches',
                'auth_method': 'api_key_required',
                'status': 'free_tier_available',
                'rate_limit': '10/minute (free), 100/minute (paid)',
                'coverage': 'Major European leagues',
                'data_quality': 'official',
                'signup_url': 'https://www.football-data.org/client/register',
                'free_tier': 'Available with registration'
            },
            {
                'name': 'FootyStats (Fixed)',
                'description': 'Statistics focused - PAID ONLY',
                'base_url': 'https://api.footystats.org/league-fixtures',
                'auth_method': 'api_key_required',
                'status': 'paid_only',
                'rate_limit': '500/day (basic), 5000/day (premium)',
                'coverage': 'Global with detailed statistics',
                'data_quality': 'statistical',
                'signup_url': 'https://footystats.org/api',
                'free_tier': 'None - paid subscriptions only'
            }
        ]

    def get_immediate_working_solutions(self) -> Dict:
        """Get APIs that work right now without any setup"""

        return {
            'primary': {
                'name': 'OpenLigaDB',
                'url': 'https://api.openligadb.de/getmatchdata/bl1/2025',
                'method': 'GET',
                'headers': {},
                'description': 'German Bundesliga - works immediately',
                'sample_code': '''
import requests
response = requests.get('https://api.openligadb.de/getmatchdata/bl1/2025')
matches = response.json()
print(f"Found {len(matches)} matches")
                '''
            },
            'secondary': {
                'name': 'TheSportsDB',
                'url': 'https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d=2025-09-29&s=Soccer',
                'method': 'GET',
                'headers': {},
                'description': 'Global soccer (limited) - works immediately',
                'sample_code': '''
import requests
from datetime import datetime
today = datetime.now().strftime('%Y-%m-%d')
url = f"https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d={today}&s=Soccer"
response = requests.get(url)
data = response.json()
events = data.get('events', [])
print(f"Found {len(events)} matches")
                '''
            }
        }

    def get_api_key_setup_guide(self) -> Dict:
        """Guide for setting up API keys for premium services"""

        return {
            'football_data_org': {
                'name': 'Football-Data.org (FREE)',
                'steps': [
                    '1. Go to https://www.football-data.org/client/register',
                    '2. Register with email (free)',
                    '3. Verify email address',
                    '4. Get API token from dashboard',
                    '5. Use header: {"X-Auth-Token": "YOUR_TOKEN"}',
                    '6. Free tier: 10 requests/minute, 100/day'
                ],
                'example_usage': '''
headers = {"X-Auth-Token": "YOUR_API_TOKEN"}
url = "https://api.football-data.org/v4/matches"
params = {"dateFrom": "2025-09-29", "dateTo": "2025-09-29"}
response = requests.get(url, headers=headers, params=params)
                ''',
                'cost': 'FREE (with limits)',
                'coverage': 'Premier League, Champions League, World Cup, etc.'
            },
            'api_sports': {
                'name': 'API-Sports/RapidAPI (FREEMIUM)',
                'steps': [
                    '1. Go to https://rapidapi.com/api-sports/api/api-football',
                    '2. Sign up for RapidAPI account',
                    '3. Subscribe to free tier (100 requests/day)',
                    '4. Get RapidAPI key from dashboard',
                    '5. Use headers: {"X-RapidAPI-Key": "YOUR_KEY", "X-RapidAPI-Host": "v3.football.api-sports.io"}',
                    '6. Free tier: 100 requests/day'
                ],
                'example_usage': '''
headers = {
    "X-RapidAPI-Key": "YOUR_RAPIDAPI_KEY",
    "X-RapidAPI-Host": "v3.football.api-sports.io"
}
url = "https://v3.football.api-sports.io/fixtures"
params = {"date": "2025-09-29"}
response = requests.get(url, headers=headers, params=params)
                ''',
                'cost': 'FREE (100/day) or $10+/month',
                'coverage': 'Comprehensive global coverage'
            },
            'footystats': {
                'name': 'FootyStats (PAID ONLY)',
                'steps': [
                    '1. Go to https://footystats.org/api',
                    '2. Choose subscription plan ($15+/month)',
                    '3. Payment required - no free tier',
                    '4. Get API key after payment',
                    '5. Use parameter: ?key=YOUR_API_KEY'
                ],
                'cost': 'PAID ONLY - starts at $15/month',
                'coverage': 'Global with detailed statistics'
            }
        }

def test_working_apis():
    """Test the APIs that work immediately"""

    print("🧪 TESTING IMMEDIATELY WORKING APIs")
    print("="*50)

    config = FixedAPIConfig()
    working = config.get_immediate_working_solutions()

    for api_type, api_info in working.items():
        print(f"\n🔍 Testing {api_info['name']} ({api_type})")
        print(f"URL: {api_info['url']}")

        try:
            response = requests.get(api_info['url'], headers=api_info['headers'], timeout=10)
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                if api_info['name'] == 'OpenLigaDB':
                    matches = data if isinstance(data, list) else []
                    print(f"✅ SUCCESS: Found {len(matches)} Bundesliga matches")

                    if matches:
                        sample_match = matches[0]
                        team1 = sample_match.get('team1', {}).get('teamName', 'Unknown')
                        team2 = sample_match.get('team2', {}).get('teamName', 'Unknown')
                        print(f"Sample: {team1} vs {team2}")

                elif api_info['name'] == 'TheSportsDB':
                    events = data.get('events', []) if data else []
                    print(f"✅ SUCCESS: Found {len(events)} soccer events")

                    if events:
                        sample_event = events[0]
                        home = sample_event.get('strHomeTeam', 'Unknown')
                        away = sample_event.get('strAwayTeam', 'Unknown')
                        print(f"Sample: {home} vs {away}")

            else:
                print(f"❌ Error: Status {response.status_code}")

        except Exception as e:
            print(f"❌ Exception: {e}")

def main():
    """Show fixed API configurations and test working ones"""

    print("🔧 FIXED API CONFIGURATION GUIDE")
    print("="*50)

    config = FixedAPIConfig()

    # Show all API status
    print("\n📊 API STATUS SUMMARY:")
    for api in config.working_apis:
        status_emoji = {
            'working': '✅',
            'requires_subscription': '💳',
            'free_tier_available': '🆓',
            'paid_only': '💰'
        }.get(api['status'], '❓')

        print(f"{status_emoji} {api['name']}: {api['status']} - {api['description']}")

    # Test working APIs
    print(f"\n🧪 TESTING WORKING APIs:")
    test_working_apis()

    # Show setup guides
    print(f"\n🔑 API KEY SETUP GUIDES:")
    print("="*30)

    setup_guide = config.get_api_key_setup_guide()

    for api_key, guide in setup_guide.items():
        print(f"\n📋 {guide['name']}")
        print(f"Cost: {guide['cost']}")
        if 'coverage' in guide:
            print(f"Coverage: {guide['coverage']}")

        print("Setup steps:")
        for step in guide['steps']:
            print(f"  {step}")

    # Immediate solutions
    print(f"\n🚀 IMMEDIATE SOLUTIONS (NO SETUP REQUIRED):")
    print("="*50)

    working = config.get_immediate_working_solutions()
    for api_type, api_info in working.items():
        print(f"\n✅ {api_info['name']} ({api_type})")
        print(f"Description: {api_info['description']}")
        print(f"URL: {api_info['url']}")
        print("Sample code:")
        print(api_info['sample_code'])

if __name__ == "__main__":
    main()