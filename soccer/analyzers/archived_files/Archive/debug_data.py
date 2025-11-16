#!/usr/bin/env python3
"""Debug script to examine actual data structure from API"""

import requests
import json

def debug_api_data(api_key: str):
    """Examine the actual data structure returned by API"""
    
    url = "https://api.football-data-api.com/league-matches"
    params = {
        'key': api_key,
        'league_id': 1625,
        'page': 1
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        matches = data.get('data', [])
        
        if matches:
            first_match = matches[0]
            print("📊 First match data structure:")
            print("=" * 50)
            
            # Print all fields and their types
            for key, value in first_match.items():
                value_type = type(value).__name__
                if isinstance(value, list):
                    sample_val = f"[list with {len(value)} items]"
                    if value:
                        sample_val += f" first: {value[0]}"
                elif isinstance(value, str):
                    sample_val = f"'{value[:50]}...'" if len(str(value)) > 50 else f"'{value}'"
                else:
                    sample_val = str(value)
                    
                print(f"{key:25} ({value_type:8}): {sample_val}")
            
            # Check specific fields we're interested in
            print("\n📋 Betting odds fields:")
            print("-" * 30)
            odds_fields = [f for f in first_match.keys() if 'odds' in f]
            for field in odds_fields[:10]:  # Show first 10 odds fields
                value = first_match.get(field)
                print(f"{field:25}: {value} ({type(value).__name__})")
                
        else:
            print("No matches found")
    else:
        print(f"API Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    API_KEY = "ceb338b9bcb82a452efc114fb2d3cccac67f58be1569e7b5acf1d2195adeae11"
    debug_api_data(API_KEY)