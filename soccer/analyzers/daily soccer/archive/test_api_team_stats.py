#!/usr/bin/env python3
"""
Test script to explore API-Sports team statistics endpoints
"""

import requests
import json

API_KEY = "960c628e1c91c4b1f125e1eec52ad862"
API_BASE = "https://v3.football.api-sports.io"

headers = {
    'x-apisports-key': API_KEY
}

# Test 1: Get team statistics for a specific team (Manchester City - team_id 50, EPL league 39, season 2024)
print("="*80)
print("TEST 1: Team Statistics Endpoint")
print("="*80)

url = f"{API_BASE}/teams/statistics"
params = {
    'team': 50,  # Manchester City
    'season': 2024,
    'league': 39  # Premier League
}

try:
    response = requests.get(url, params=params, headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"\n📊 Response structure:")
        print(json.dumps(data, indent=2)[:2000])  # First 2000 chars

        # Extract key statistics
        if 'response' in data:
            stats = data['response']
            print(f"\n✅ Key statistics available:")
            print(f"Available keys: {list(stats.keys()) if isinstance(stats, dict) else 'response is a list'}")
    else:
        print(f"❌ Error: {response.text}")

except Exception as e:
    print(f"❌ Exception: {e}")

# Test 2: Get recent fixtures for a team (last 10 games)
print("\n" + "="*80)
print("TEST 2: Team Recent Fixtures (Form)")
print("="*80)

url = f"{API_BASE}/fixtures"
params = {
    'team': 50,  # Manchester City
    'season': 2024,
    'league': 39,  # Premier League
    'last': 10  # Last 10 matches
}

try:
    response = requests.get(url, params=params, headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"\n📊 Response structure:")
        print(json.dumps(data, indent=2)[:2000])  # First 2000 chars

        # Extract key data
        if 'response' in data:
            fixtures = data['response']
            print(f"\n✅ Found {len(fixtures)} recent matches")

            if len(fixtures) > 0:
                first_fixture = fixtures[0]
                print(f"Sample fixture keys: {list(first_fixture.keys())}")
    else:
        print(f"❌ Error: {response.text}")

except Exception as e:
    print(f"❌ Exception: {e}")

# Test 3: Head to Head between two teams
print("\n" + "="*80)
print("TEST 3: Head-to-Head History")
print("="*80)

url = f"{API_BASE}/fixtures/headtohead"
params = {
    'h2h': '50-33',  # Manchester City vs Manchester United
    'last': 10  # Last 10 H2H matches
}

try:
    response = requests.get(url, params=params, headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"\n📊 Response structure:")
        print(json.dumps(data, indent=2)[:2000])  # First 2000 chars

        # Extract key data
        if 'response' in data:
            h2h_matches = data['response']
            print(f"\n✅ Found {len(h2h_matches)} H2H matches")
    else:
        print(f"❌ Error: {response.text}")

except Exception as e:
    print(f"❌ Exception: {e}")

print("\n" + "="*80)
print("✅ API Exploration Complete!")
print("="*80)
