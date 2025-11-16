#!/usr/bin/env python3
"""
Test API-Sports with the provided key
"""

import requests
import json
from datetime import datetime

def test_api_sports_with_real_key():
    """Test API-Sports with the provided key"""

    print("🔑 TESTING API-SPORTS WITH PROVIDED API KEY")
    print("="*50)

    api_key = "960c628e1c91c4b1f125e1eec52ad862"
    today = datetime.now().strftime('%Y-%m-%d')

    # Test different API-Sports endpoints
    endpoints = [
        {
            'name': 'Fixtures by date',
            'url': f'https://v3.football.api-sports.io/fixtures?date={today}',
            'headers': {
                'X-RapidAPI-Key': api_key,
                'X-RapidAPI-Host': 'v3.football.api-sports.io'
            }
        },
        {
            'name': 'Live fixtures',
            'url': 'https://v3.football.api-sports.io/fixtures?live=all',
            'headers': {
                'X-RapidAPI-Key': api_key,
                'X-RapidAPI-Host': 'v3.football.api-sports.io'
            }
        },
        {
            'name': 'API Status',
            'url': 'https://v3.football.api-sports.io/status',
            'headers': {
                'X-RapidAPI-Key': api_key,
                'X-RapidAPI-Host': 'v3.football.api-sports.io'
            }
        },
        {
            'name': 'Yesterday fixtures (test)',
            'url': f'https://v3.football.api-sports.io/fixtures?date=2025-09-28',
            'headers': {
                'X-RapidAPI-Key': api_key,
                'X-RapidAPI-Host': 'v3.football.api-sports.io'
            }
        }
    ]

    working_endpoints = []

    for endpoint in endpoints:
        print(f"\n🧪 Testing: {endpoint['name']}")
        print(f"URL: {endpoint['url']}")

        try:
            response = requests.get(endpoint['url'], headers=endpoint['headers'], timeout=15)
            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                try:
                    data = response.json()

                    # Check for errors first
                    if 'errors' in data and data['errors']:
                        print(f"❌ API Errors: {data['errors']}")
                        continue

                    print(f"✅ SUCCESS!")

                    # Analyze response structure
                    if isinstance(data, dict):
                        print(f"Response keys: {list(data.keys())}")

                        if 'response' in data:
                            fixtures = data['response']
                            print(f"Fixtures found: {len(fixtures) if isinstance(fixtures, list) else 'Not a list'}")

                            if isinstance(fixtures, list) and len(fixtures) > 0:
                                print("Sample fixture keys:", list(fixtures[0].keys()) if fixtures[0] else "Empty")

                                # Show sample match
                                sample = fixtures[0]
                                teams = sample.get('teams', {})
                                home_team = teams.get('home', {}).get('name', 'Unknown')
                                away_team = teams.get('away', {}).get('name', 'Unknown')
                                league = sample.get('league', {}).get('name', 'Unknown')
                                fixture_date = sample.get('fixture', {}).get('date', 'Unknown')

                                print(f"Sample match: {home_team} vs {away_team} ({league})")
                                print(f"Date: {fixture_date}")
                                working_endpoints.append(endpoint)

                            elif len(fixtures) == 0:
                                print("No fixtures in response (could be valid for today)")
                                working_endpoints.append(endpoint)

                        if 'results' in data:
                            print(f"Results count: {data['results']}")

                        if endpoint['name'] == 'API Status':
                            if 'response' in data and data['response']:
                                status_info = data['response']
                                print(f"Account info: {status_info}")
                                working_endpoints.append(endpoint)

                    # Show partial response
                    response_preview = json.dumps(data, indent=2)[:500]
                    print(f"Response preview:\n{response_preview}...")

                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON response")
                    print(f"Raw response: {response.text[:200]}...")

            else:
                print(f"❌ Error {response.status_code}")
                print(f"Response: {response.text[:200]}")

        except Exception as e:
            print(f"❌ Exception: {e}")

    # Summary
    print(f"\n📊 API-SPORTS TEST SUMMARY:")
    print("="*40)
    print(f"Total endpoints tested: {len(endpoints)}")
    print(f"Working endpoints: {len(working_endpoints)}")

    if working_endpoints:
        print(f"\n✅ WORKING ENDPOINTS:")
        for endpoint in working_endpoints:
            print(f"  • {endpoint['name']}")

        # Return the best working endpoint
        best_endpoint = working_endpoints[0]
        return {
            'status': 'working',
            'best_endpoint': best_endpoint,
            'api_key': api_key,
            'headers': best_endpoint['headers']
        }
    else:
        print(f"❌ No working endpoints found")
        return {'status': 'failed'}

def main():
    """Test API-Sports"""
    result = test_api_sports_with_real_key()

    if result['status'] == 'working':
        print(f"\n🎉 API-SPORTS IS NOW WORKING!")
        print(f"Best endpoint: {result['best_endpoint']['name']}")
        print(f"✅ Ready to integrate into betting models")
    else:
        print(f"\n❌ API-Sports still not working with provided key")

if __name__ == "__main__":
    main()