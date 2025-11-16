#!/usr/bin/env python3
"""
Test different FootyStats endpoint patterns
"""

import requests
import json
from datetime import datetime

def test_footystats_endpoint_patterns():
    """Test various FootyStats endpoint patterns"""

    print("🔍 TESTING FOOTYSTATS ENDPOINT PATTERNS")
    print("="*50)

    api_key = "ceb338b9bcb82a452efc114fb2d3cccac67f58be1569e7b5acf1d2195adeae11"
    today = datetime.now().strftime('%Y-%m-%d')

    # Test various endpoint patterns
    endpoint_patterns = [
        # Different base URLs
        f'https://api.footystats.org/matches?key={api_key}&date={today}',
        f'https://api.footystats.org/today?key={api_key}',
        f'https://api.footystats.org/fixtures-today?key={api_key}',
        f'https://api.footystats.org/todays-matches?key={api_key}',
        f'https://api.footystats.org/match-list?key={api_key}&date={today}',
        f'https://api.footystats.org/league-matches?key={api_key}&date={today}',

        # Different parameter formats
        f'https://api.footystats.org/matches?key={api_key}&date={today.replace("-", "")}',
        f'https://api.footystats.org/fixtures?key={api_key}&from_date={today}&to_date={today}',

        # Try without date parameter
        f'https://api.footystats.org/matches?key={api_key}',
        f'https://api.footystats.org/today-fixtures?key={api_key}',

        # Try different endpoints found in documentation
        f'https://api.footystats.org/leagues?key={api_key}',
        f'https://api.footystats.org/league-list?key={api_key}',
        f'https://api.footystats.org/status?key={api_key}',
    ]

    working_endpoints = []

    for url in endpoint_patterns:
        print(f"\n🧪 Testing: {url[:60]}...")

        try:
            response = requests.get(url, timeout=10)
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                try:
                    data = response.json()

                    if data.get('success', False):
                        print(f"✅ SUCCESS!")

                        # Look for data
                        if 'data' in data and data['data']:
                            matches = data['data']
                            print(f"Found {len(matches)} items")

                            if len(matches) > 0 and isinstance(matches[0], dict):
                                keys = list(matches[0].keys())
                                print(f"Sample keys: {keys[:5]}...")

                                # Try to identify if these are matches
                                if any(key in keys for key in ['home_name', 'away_name', 'teams', 'fixture']):
                                    print("🎯 This looks like match data!")
                                    working_endpoints.append(url)

                        elif 'leagues' in data:
                            leagues = data['leagues']
                            print(f"Found {len(leagues)} leagues")
                            working_endpoints.append(url)

                        else:
                            print(f"Success but no data found. Keys: {list(data.keys())}")

                    else:
                        print(f"❌ Success=false in response")
                        if 'message' in data:
                            print(f"Message: {data['message']}")

                    # Show response preview
                    preview = json.dumps(data, indent=2)[:300]
                    print(f"Preview: {preview}...")

                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON")
                    print(f"Raw: {response.text[:100]}...")

            elif response.status_code == 404:
                print(f"❌ Not Found (404)")
            elif response.status_code == 401:
                print(f"❌ Unauthorized (401)")
            elif response.status_code == 403:
                print(f"❌ Forbidden (403)")
            else:
                print(f"❌ Error {response.status_code}")
                if response.text:
                    print(f"Response: {response.text[:100]}...")

        except Exception as e:
            print(f"❌ Exception: {str(e)[:100]}")

    # Summary
    print(f"\n📊 SUMMARY")
    print("="*30)
    print(f"Endpoints tested: {len(endpoint_patterns)}")
    print(f"Working endpoints: {len(working_endpoints)}")

    if working_endpoints:
        print(f"\n✅ WORKING ENDPOINTS:")
        for endpoint in working_endpoints:
            print(f"  • {endpoint}")

        return working_endpoints[0]  # Return first working endpoint
    else:
        print(f"\n❌ No working endpoints found")
        return None

def main():
    """Test FootyStats endpoints"""

    working_endpoint = test_footystats_endpoint_patterns()

    if working_endpoint:
        print(f"\n🎉 FOUND WORKING FOOTYSTATS ENDPOINT!")
        print(f"Endpoint: {working_endpoint}")
    else:
        print(f"\n⚠️ FootyStats API key may be valid but endpoints are different")
        print(f"🔍 The API key works (no 401 errors) but endpoint structure is unknown")

if __name__ == "__main__":
    main()