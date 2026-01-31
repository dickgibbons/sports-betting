"""
Quick test to verify DataGolf API connection
Run: python test_api.py YOUR_API_KEY
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.datagolf_client import DataGolfClient


def test_api(api_key: str):
    """Test basic API connectivity"""
    print("Testing DataGolf API connection...\n")
    
    client = DataGolfClient(api_key)
    
    # Test 1: Rankings
    print("1. Testing DG Rankings endpoint...")
    try:
        df = client.get_dg_rankings()
        print(f"   ✓ Success! Retrieved {len(df)} players")
        print(f"   Top 5: {df.head()['player_name'].tolist()}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    print()
    
    # Test 2: Schedule
    print("2. Testing Schedule endpoint...")
    try:
        df = client.get_tour_schedule(tour="pga", season=2025)
        print(f"   ✓ Success! Retrieved {len(df)} events for 2025")
        upcoming = df[df['event_completed'] == False] if 'event_completed' in df.columns else df
        if len(upcoming) > 0:
            print(f"   Next event: {upcoming.iloc[0].get('event_name', 'Unknown')}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print()
    
    # Test 3: Skill Ratings
    print("3. Testing Skill Ratings endpoint...")
    try:
        df = client.get_player_skill_ratings()
        print(f"   ✓ Success! Retrieved skill ratings for {len(df)} players")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print()
    
    # Test 4: Pre-tournament predictions
    print("4. Testing Pre-Tournament Predictions endpoint...")
    try:
        df = client.get_pre_tournament_predictions(tour="pga")
        print(f"   ✓ Success! Retrieved predictions for {len(df)} players")
        if len(df) > 0 and 'win' in df.columns:
            top_pick = df.nsmallest(1, 'win')
            print(f"   Favorite: {top_pick.iloc[0].get('player_name', 'Unknown')}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print()
    
    # Test 5: Historical events
    print("5. Testing Historical Events List endpoint...")
    try:
        df = client.get_historical_events_list()
        print(f"   ✓ Success! Retrieved {len(df)} historical events")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print()
    print("=" * 50)
    print("API connection test complete!")
    print("=" * 50)
    
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_api.py YOUR_API_KEY")
        sys.exit(1)
    
    api_key = sys.argv[1]
    test_api(api_key)
