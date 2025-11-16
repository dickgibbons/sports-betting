#!/usr/bin/env python3
"""
Hockey Betting System Configuration
Target leagues and settings
"""

# API Configuration
API_KEY = "960c628e1c91c4b1f125e1eec52ad862"
BASE_URL = "https://v1.hockey.api-sports.io"

# Target Leagues for Betting System
TARGET_LEAGUES = {
    'NHL': {
        'id': 57,
        'name': 'NHL',
        'country': 'USA/Canada',
        'season': 2025,
        'enabled': True
    },
    'SHL': {
        'id': 47,
        'name': 'SHL',
        'country': 'Sweden',
        'season': 2025,
        'enabled': True
    },
    'Liiga': {
        'id': 16,
        'name': 'Liiga',
        'country': 'Finland',
        'season': 2025,
        'enabled': True
    },
    'DEL': {
        'id': 19,
        'name': 'DEL',
        'country': 'Germany',
        'season': 2025,
        'enabled': True
    }
}

# Betting Configuration
INITIAL_BANKROLL = 300.0
MAX_DAILY_RISK = 0.25  # 25% of bankroll per day
MAX_BET_SIZE = 0.15    # 15% per single bet
MIN_EDGE = 0.10        # 10% minimum edge (increased from 5% for better win rate)
MIN_CONFIDENCE = 0.65  # 65% minimum confidence (increased from 60% for better win rate)

# Model Settings
MODEL_PATH = "hockey_models.pkl"
FEATURES = [
    'home_odds',
    'draw_odds',
    'away_odds',
    'home_form',
    'away_form',
    'head_to_head',
    'goals_scored_avg',
    'goals_conceded_avg'
]

def get_enabled_leagues():
    """Get list of enabled leagues"""
    return {k: v for k, v in TARGET_LEAGUES.items() if v['enabled']}

def get_league_ids():
    """Get list of enabled league IDs"""
    return [v['id'] for v in TARGET_LEAGUES.values() if v['enabled']]

def print_config():
    """Print current configuration"""
    print("🏒 HOCKEY BETTING SYSTEM CONFIGURATION")
    print("=" * 60)
    print(f"\n💰 Bankroll Settings:")
    print(f"   Initial Bankroll: ${INITIAL_BANKROLL:.2f}")
    print(f"   Max Daily Risk: {MAX_DAILY_RISK*100:.0f}%")
    print(f"   Max Bet Size: {MAX_BET_SIZE*100:.0f}%")
    print(f"   Min Edge: {MIN_EDGE*100:.0f}%")
    print(f"   Min Confidence: {MIN_CONFIDENCE*100:.0f}%")

    print(f"\n🏒 Target Leagues:")
    for name, config in TARGET_LEAGUES.items():
        status = "✅ Enabled" if config['enabled'] else "❌ Disabled"
        print(f"   {name:15} | ID: {config['id']:3} | {config['country']:15} | {status}")

    print(f"\n📊 Total Enabled Leagues: {len(get_enabled_leagues())}")
    print("=" * 60)

if __name__ == "__main__":
    print_config()
