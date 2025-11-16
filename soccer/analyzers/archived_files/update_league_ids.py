#!/usr/bin/env python3
"""
Update League IDs from API-Football
Fetches current league IDs for all supported leagues and updates the database
"""

import requests
import pandas as pd
import time
from datetime import datetime

def fetch_api_leagues(api_key: str, season: int = 2024):
    """Fetch all leagues from API for given season"""
    url = 'https://v3.football.api-sports.io/leagues'
    headers = {'x-apisports-key': api_key}
    params = {'season': season}

    response = requests.get(url, headers=headers, params=params, timeout=30)
    if response.status_code == 200:
        data = response.json()
        return data.get('response', [])
    return []

def create_api_lookup(api_leagues):
    """Create lookup dictionary from API leagues"""
    lookup = {}

    for league_data in api_leagues:
        league = league_data.get('league', {})
        league_name = league.get('name', '')
        league_id = league.get('id', 0)
        league_type = league.get('type', '')

        country_data = league_data.get('country', {})
        country = country_data.get('name', '')

        # Store by name and country
        key = f"{league_name}_{country}".lower()

        if key not in lookup:
            lookup[key] = []

        lookup[key].append({
            'id': league_id,
            'name': league_name,
            'country': country,
            'type': league_type
        })

    return lookup

def match_league(our_name, our_country, api_lookup):
    """Try to match our league with API league"""

    # Try exact match
    key = f"{our_name}_{our_country}".lower()
    if key in api_lookup:
        # If multiple matches, prefer 'League' type over 'Cup'
        matches = api_lookup[key]
        for match in matches:
            if match['type'] == 'League':
                return match
        return matches[0]

    # Try alternative names
    alternatives = {
        'Primera División': ['Liga Profesional Argentina', 'Argentine Liga Profesional'],
        'Pro League': ['Pro League', 'Jupiler Pro League'],
        'Brazil Serie A': ['Serie A', 'Brasileiro Série A', 'Brasileirão Serie A'],
        'Brazil Serie B': ['Serie B', 'Brasileiro Série B', 'Brasileirão Serie B'],
        'First League': ['First League', '1. Liga'],
        'Superlig': ['Super Lig', 'Süper Lig'],
        'UEFA Champions League': ['Champions League', 'UEFA Champions League'],
        'UEFA Europa League': ['Europa League', 'UEFA Europa League'],
        'UEFA Europa Conference League': ['Conference League', 'UEFA Conference League', 'Europa Conference League'],
        'WC Qualification Europe': ['World Cup Qualification', 'World Cup - Qualification Europe'],
        'WC Qualification Africa': ['World Cup - Qualification Africa'],
        'WC Qualification Asia': ['World Cup - Qualification Asia'],
        'WC Qualification South America': ['World Cup - Qualification South America'],
        'WC Qualification CONCACAF': ['World Cup - Qualification CONCACAF'],
        'WC Qualification Oceania': ['World Cup - Qualification Oceania'],
        'FIFA Club World Cup': ['Club World Cup', 'FIFA Club World Cup'],
    }

    if our_name in alternatives:
        for alt_name in alternatives[our_name]:
            key = f"{alt_name}_{our_country}".lower()
            if key in api_lookup:
                matches = api_lookup[key]
                for match in matches:
                    if match['type'] == 'League':
                        return match
                return matches[0]

            # Try without country (for international competitions)
            key = alt_name.lower()
            for api_key, matches in api_lookup.items():
                if alt_name.lower() in api_key:
                    return matches[0]

    return None

def main():
    api_key = '960c628e1c91c4b1f125e1eec52ad862'

    # Load current database
    df = pd.read_csv('output reports/Older/UPDATED_supported_leagues_database.csv')
    print(f"📊 Loaded {len(df)} leagues from database")

    # Fetch API leagues for 2024 season
    print(f"\n🔄 Fetching leagues from API-Football (2024 season)...")
    api_leagues = fetch_api_leagues(api_key, 2024)
    print(f"✅ Fetched {len(api_leagues)} leagues from API")

    # Create lookup
    api_lookup = create_api_lookup(api_leagues)
    print(f"✅ Created lookup for {len(api_lookup)} unique league-country combinations")

    # Match and update
    print(f"\n{'='*100}")
    print(f"{'League Name':<40} {'Country':<20} {'Old ID':<10} {'New ID':<10} {'Status':<20}")
    print(f"{'='*100}")

    updated_count = 0
    not_found_count = 0
    same_count = 0

    for idx, row in df.iterrows():
        our_name = row['league_name']
        our_country = row['country']
        our_id = row['league_id']

        match = match_league(our_name, our_country, api_lookup)

        if match:
            new_id = match['id']
            if new_id != our_id:
                df.at[idx, 'league_id'] = new_id
                df.at[idx, 'last_updated'] = datetime.now().strftime('%m/%d/%y')
                status = '⚠️  UPDATED'
                updated_count += 1
            else:
                status = '✅ Same'
                same_count += 1

            print(f"{our_name:<40} {our_country:<20} {our_id:<10} {new_id:<10} {status:<20}")
        else:
            status = '❌ Not found'
            not_found_count += 1
            print(f"{our_name:<40} {our_country:<20} {our_id:<10} {'N/A':<10} {status:<20}")

    # Save updated database
    output_file = 'output reports/Older/UPDATED_supported_leagues_database.csv'
    df.to_csv(output_file, index=False)

    print(f"\n{'='*100}")
    print(f"📊 SUMMARY:")
    print(f"   ✅ {same_count} leagues unchanged")
    print(f"   ⚠️  {updated_count} leagues updated")
    print(f"   ❌ {not_found_count} leagues not found (may need manual review)")
    print(f"\n✅ Updated database saved to: {output_file}")

if __name__ == "__main__":
    main()
