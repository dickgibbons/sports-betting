#!/usr/bin/env python3
"""
Test FootyStats API with the provided key
"""

import requests
import json
from datetime import datetime

def test_footystats_with_real_key():
    """Test FootyStats API with the provided key"""

    print("🔑 TESTING FOOTYSTATS WITH PROVIDED API KEY")
    print("="*50)

    api_key = "ceb338b9bcb82a452efc114fb2d3cccac67f58be1569e7b5acf1d2195adeae11"
    today = datetime.now().strftime('%Y-%m-%d')

    # Test different FootyStats endpoints
    endpoints = [
        {
            'name': 'League fixtures by date',
            'url': f'https://api.footystats.org/league-fixtures?key={api_key}&date={today}',
        },
        {
            'name': 'All fixtures by date',
            'url': f'https://api.footystats.org/fixtures?key={api_key}&date={today}',
        },
        {
            'name': 'Live fixtures',
            'url': f'https://api.footystats.org/live-fixtures?key={api_key}',
        },
        {
            'name': 'Today\'s fixtures (alternative)',
            'url': f'https://api.footystats.org/today-fixtures?key={api_key}',
        }
    ]

    working_endpoints = []

    for endpoint in endpoints:
        print(f"\n🧪 Testing: {endpoint['name']}")
        print(f"URL: {endpoint['url'][:60]}...")

        try:
            response = requests.get(endpoint['url'], timeout=15)
            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ SUCCESS!")

                    # Analyze response structure
                    if isinstance(data, dict):
                        print(f"Response keys: {list(data.keys())}")

                        if 'data' in data:
                            fixtures = data['data']
                            print(f"Fixtures found: {len(fixtures) if isinstance(fixtures, list) else 'Not a list'}")

                            if isinstance(fixtures, list) and len(fixtures) > 0:
                                print("Sample fixture keys:", list(fixtures[0].keys()) if fixtures[0] else "Empty")

                                # Show sample match
                                sample = fixtures[0]
                                home_team = sample.get('home_name', 'Unknown')
                                away_team = sample.get('away_name', 'Unknown')
                                league = sample.get('league_name', 'Unknown')
                                date = sample.get('date_unix', 'Unknown')

                                print(f"Sample match: {home_team} vs {away_team} ({league})")
                                working_endpoints.append(endpoint)

                        elif 'success' in data:
                            print(f"API Success: {data['success']}")
                            if data.get('success'):
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
    print(f"\n📊 FOOTYSTATS API TEST SUMMARY:")
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
            'api_key': api_key
        }
    else:
        print(f"❌ No working endpoints found")
        return {'status': 'failed'}

def main():
    """Test FootyStats API"""
    result = test_footystats_with_real_key()

    if result['status'] == 'working':
        print(f"\n🎉 FOOTYSTATS API IS NOW WORKING!")
        print(f"Best endpoint: {result['best_endpoint']['name']}")
        print(f"✅ Ready to integrate into betting models")
    else:
        print(f"\n❌ FootyStats API still not working with provided key")

if __name__ == "__main__":
    main()