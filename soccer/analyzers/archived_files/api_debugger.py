#!/usr/bin/env python3
"""
API Debugger
Debug FootyStats and API-Sports API issues
Check exact responses and identify authentication/endpoint problems
"""

import requests
import json
from datetime import datetime

def debug_api_sports():
    """Debug API-Sports (RapidAPI) issues"""

    print("🔍 DEBUGGING API-Sports (RapidAPI)")
    print("="*50)

    today = datetime.now().strftime('%Y-%m-%d')

    # Test different endpoints and headers
    endpoints_to_test = [
        {
            'name': 'Fixtures by date (demo key)',
            'url': f'https://v3.football.api-sports.io/fixtures?date={today}',
            'headers': {
                'X-RapidAPI-Key': 'demo',
                'X-RapidAPI-Host': 'v3.football.api-sports.io'
            }
        },
        {
            'name': 'Fixtures live (demo key)',
            'url': 'https://v3.football.api-sports.io/fixtures?live=all',
            'headers': {
                'X-RapidAPI-Key': 'demo',
                'X-RapidAPI-Host': 'v3.football.api-sports.io'
            }
        },
        {
            'name': 'Status endpoint',
            'url': 'https://v3.football.api-sports.io/status',
            'headers': {
                'X-RapidAPI-Key': 'demo',
                'X-RapidAPI-Host': 'v3.football.api-sports.io'
            }
        }
    ]

    for endpoint in endpoints_to_test:
        print(f"\n🧪 Testing: {endpoint['name']}")
        print(f"URL: {endpoint['url']}")

        try:
            response = requests.get(endpoint['url'], headers=endpoint['headers'], timeout=10)

            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")

            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"Response Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")

                    if 'response' in data:
                        print(f"Response array length: {len(data['response']) if isinstance(data['response'], list) else 'Not a list'}")
                        if isinstance(data['response'], list) and len(data['response']) > 0:
                            print(f"First response item keys: {list(data['response'][0].keys())}")
                        else:
                            print("Response array is empty")

                    if 'errors' in data and data['errors']:
                        print(f"❌ API Errors: {data['errors']}")

                    if 'results' in data:
                        print(f"Results count: {data['results']}")

                    # Show first few lines of response
                    response_str = json.dumps(data, indent=2)[:500]
                    print(f"Response preview:\n{response_str}...")

                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON response")
                    print(f"Raw response: {response.text[:200]}...")
            else:
                print(f"❌ Error response: {response.text[:200]}")

        except Exception as e:
            print(f"❌ Exception: {e}")

def debug_footystats():
    """Debug FootyStats API issues"""

    print("\n\n🔍 DEBUGGING FootyStats API")
    print("="*50)

    today = datetime.now().strftime('%Y-%m-%d')

    # Test different endpoints and authentication methods
    endpoints_to_test = [
        {
            'name': 'League fixtures (test key)',
            'url': f'https://api.footystats.org/league-fixtures?key=test&date={today}',
            'headers': {}
        },
        {
            'name': 'League fixtures (demo key)',
            'url': f'https://api.footystats.org/league-fixtures?key=demo&date={today}',
            'headers': {}
        },
        {
            'name': 'Fixtures endpoint alternative',
            'url': f'https://api.footystats.org/fixtures?date={today}',
            'headers': {'Authorization': 'Bearer demo'}
        },
        {
            'name': 'Free tier endpoint',
            'url': 'https://api.footystats.org/free',
            'headers': {}
        }
    ]

    for endpoint in endpoints_to_test:
        print(f"\n🧪 Testing: {endpoint['name']}")
        print(f"URL: {endpoint['url']}")

        try:
            response = requests.get(endpoint['url'], headers=endpoint['headers'], timeout=10)

            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")

            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"Response Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")

                    # Show response structure
                    response_str = json.dumps(data, indent=2)[:500]
                    print(f"Response preview:\n{response_str}...")

                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON response")
                    print(f"Raw response: {response.text[:200]}...")
            else:
                print(f"❌ Error response: {response.text[:200]}")

        except Exception as e:
            print(f"❌ Exception: {e}")

def test_alternative_endpoints():
    """Test alternative free soccer APIs"""

    print("\n\n🔍 TESTING ALTERNATIVE FREE APIs")
    print("="*50)

    today = datetime.now().strftime('%Y-%m-%d')

    alternative_apis = [
        {
            'name': 'Sport API (free tier)',
            'url': f'https://api.sport-api.com/v1/football/matches?date={today}',
            'headers': {}
        },
        {
            'name': 'API Football (alternative endpoint)',
            'url': f'https://api.api-football.com/v1/fixtures/date/{today}',
            'headers': {}
        },
        {
            'name': 'Free Football API',
            'url': f'https://free-football-soccer-api.herokuapp.com/api/v1/fixtures?date={today}',
            'headers': {}
        },
        {
            'name': 'Soccer API (free)',
            'url': f'https://soccer.sportmonks.com/api/v2.0/fixtures/date/{today}',
            'headers': {}
        }
    ]

    for api in alternative_apis:
        print(f"\n🧪 Testing: {api['name']}")
        print(f"URL: {api['url']}")

        try:
            response = requests.get(api['url'], headers=api['headers'], timeout=10)
            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ Success! Response Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")

                    response_str = json.dumps(data, indent=2)[:300]
                    print(f"Response preview:\n{response_str}...")

                except json.JSONDecodeError:
                    print(f"✅ Response received but not JSON")
                    print(f"Content type: {response.headers.get('content-type', 'Unknown')}")
            else:
                print(f"❌ Status {response.status_code}")

        except Exception as e:
            print(f"❌ Exception: {e}")

def main():
    """Run comprehensive API debugging"""

    print("🐛 API DEBUGGING SESSION")
    print("🎯 Goal: Fix FootyStats and API-Sports authentication issues")
    print("📅 Testing for today:", datetime.now().strftime('%Y-%m-%d'))

    debug_api_sports()
    debug_footystats()
    test_alternative_endpoints()

    print(f"\n\n💡 DEBUGGING COMPLETE")
    print("Check the output above to identify:")
    print("• Correct API endpoints")
    print("• Required authentication methods")
    print("• Working alternative APIs")
    print("• Response format structures")

if __name__ == "__main__":
    main()