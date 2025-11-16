#!/usr/bin/env python3
"""
Generate CSV file of all supported leagues with IDs and seasons
"""

import csv
from datetime import datetime

def create_leagues_csv():
    """Create comprehensive CSV of all supported leagues"""
    
    # All leagues from multi_league_predictor.py with additional details
    leagues_data = [
        # Europe - Major Leagues
        {'league_name': 'Premier League', 'league_id': 1625, 'country': 'England', 'tier': 1, 'season_format': '2025-26', 'status': 'Active'},
        {'league_name': 'Championship', 'league_id': 1626, 'country': 'England', 'tier': 2, 'season_format': '2025-26', 'status': 'Active'},
        {'league_name': 'FA Trophy', 'league_id': 1626, 'country': 'England', 'tier': 3, 'season_format': '2025-26', 'status': 'Active'},
        {'league_name': 'La Liga', 'league_id': 1729, 'country': 'Spain', 'tier': 1, 'season_format': '2025-26', 'status': 'Active'},
        {'league_name': 'Bundesliga', 'league_id': 1854, 'country': 'Germany', 'tier': 1, 'season_format': '2025-26', 'status': 'Active'},
        {'league_name': 'Serie A', 'league_id': 2105, 'country': 'Italy', 'tier': 1, 'season_format': '2025-26', 'status': 'Active'},
        {'league_name': 'Ligue 1', 'league_id': 1843, 'country': 'France', 'tier': 1, 'season_format': '2025-26', 'status': 'Active'},
        {'league_name': 'Eredivisie', 'league_id': 2200, 'country': 'Netherlands', 'tier': 1, 'season_format': '2025-26', 'status': 'Active'},
        
        # European Cups
        {'league_name': 'UEFA Champions League', 'league_id': 3000, 'country': 'Europe', 'tier': 0, 'season_format': '2025-26', 'status': 'Active'},
        {'league_name': 'UEFA Europa League', 'league_id': 3001, 'country': 'Europe', 'tier': 0, 'season_format': '2025-26', 'status': 'Active'},
        {'league_name': 'UEFA Europa Conference League', 'league_id': 3002, 'country': 'Europe', 'tier': 0, 'season_format': '2025-26', 'status': 'Active'},
        
        # FIFA Club World Cup
        {'league_name': 'FIFA Club World Cup', 'league_id': 4000, 'country': 'International', 'tier': 0, 'season_format': '2025', 'status': 'Active'},
        {'league_name': 'FIFA Club World Cup Playin', 'league_id': 4001, 'country': 'International', 'tier': 0, 'season_format': '2025', 'status': 'Active'},
        
        # World Cup Qualifications
        {'league_name': 'WC Qualification Europe', 'league_id': 4100, 'country': 'International', 'tier': 0, 'season_format': '2025-26', 'status': 'Active'},
        {'league_name': 'WC Qualification Africa', 'league_id': 4101, 'country': 'International', 'tier': 0, 'season_format': '2025-26', 'status': 'Active'},
        {'league_name': 'WC Qualification Asia', 'league_id': 4102, 'country': 'International', 'tier': 0, 'season_format': '2025-26', 'status': 'Active'},
        {'league_name': 'WC Qualification South America', 'league_id': 4103, 'country': 'International', 'tier': 0, 'season_format': '2025-26', 'status': 'Active'},
        {'league_name': 'WC Qualification CONCACAF', 'league_id': 4104, 'country': 'International', 'tier': 0, 'season_format': '2025-26', 'status': 'Active'},
        {'league_name': 'WC Qualification Oceania', 'league_id': 4105, 'country': 'International', 'tier': 0, 'season_format': '2025-26', 'status': 'Active'},
        
        # Americas
        {'league_name': 'MLS', 'league_id': 5000, 'country': 'USA', 'tier': 1, 'season_format': '2025', 'status': 'Active'},
        {'league_name': 'USL League One', 'league_id': 5002, 'country': 'USA', 'tier': 2, 'season_format': '2025', 'status': 'Active'},
        {'league_name': 'NWSL', 'league_id': 5003, 'country': 'USA', 'tier': 1, 'season_format': '2025', 'status': 'Active'},
        {'league_name': 'Liga MX', 'league_id': 5200, 'country': 'Mexico', 'tier': 1, 'season_format': '2025', 'status': 'Active'},
        {'league_name': 'Copa MX', 'league_id': 5202, 'country': 'Mexico', 'tier': 2, 'season_format': '2025', 'status': 'Active'},
        {'league_name': 'Brazil Serie A', 'league_id': 5400, 'country': 'Brazil', 'tier': 1, 'season_format': '2025', 'status': 'Active'},
        {'league_name': 'Brazil Serie B', 'league_id': 5401, 'country': 'Brazil', 'tier': 2, 'season_format': '2025', 'status': 'Active'},
        {'league_name': 'Primera División', 'league_id': 5500, 'country': 'Argentina', 'tier': 1, 'season_format': '2025', 'status': 'Active'},
        {'league_name': 'Copa Libertadores', 'league_id': 5300, 'country': 'South America', 'tier': 0, 'season_format': '2025', 'status': 'Active'},
        
        # Other European Leagues
        {'league_name': 'Pro League', 'league_id': 2400, 'country': 'Belgium', 'tier': 1, 'season_format': '2025-26', 'status': 'Active'},
        {'league_name': 'Superlig', 'league_id': 6200, 'country': 'Denmark', 'tier': 1, 'season_format': '2025-26', 'status': 'Active'},
        {'league_name': 'First League', 'league_id': 6400, 'country': 'Czech Republic', 'tier': 1, 'season_format': '2025-26', 'status': 'Active'},
        {'league_name': 'Eliteserien', 'league_id': 6000, 'country': 'Norway', 'tier': 1, 'season_format': '2025', 'status': 'Active'},
        {'league_name': 'First Division', 'league_id': 6001, 'country': 'Norway', 'tier': 2, 'season_format': '2025', 'status': 'Active'},
        {'league_name': 'LigaPro', 'league_id': 2300, 'country': 'Portugal', 'tier': 2, 'season_format': '2025-26', 'status': 'Active'},
        {'league_name': 'Super League', 'league_id': 6700, 'country': 'Switzerland', 'tier': 1, 'season_format': '2025-26', 'status': 'Active'},
        {'league_name': 'Süper Lig', 'league_id': 6900, 'country': 'Turkey', 'tier': 1, 'season_format': '2025-26', 'status': 'Active'},
        
        # CONCACAF
        {'league_name': 'CONCACAF Central American Cup', 'league_id': 7001, 'country': 'International', 'tier': 0, 'season_format': '2025', 'status': 'Active'},
        {'league_name': 'CONCACAF Caribbean Club Championship', 'league_id': 7002, 'country': 'International', 'tier': 0, 'season_format': '2025', 'status': 'Active'},
    ]
    
    # Create CSV file in output reports directory
    csv_filename = "./output reports/supported_leagues_database.csv"
    
    fieldnames = [
        'league_name',
        'league_id', 
        'country',
        'tier',
        'season_format',
        'current_season',
        'status',
        'betting_factors_configured',
        'last_updated'
    ]
    
    print("📊 Creating comprehensive leagues database...")
    
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for league in leagues_data:
            # Add additional fields
            current_season = get_current_season(league['season_format'])
            
            row = {
                'league_name': league['league_name'],
                'league_id': league['league_id'] if league['league_id'] else 'TBD',
                'country': league['country'],
                'tier': league['tier'],
                'season_format': league['season_format'],
                'current_season': current_season,
                'status': league['status'],
                'betting_factors_configured': 'Yes',
                'last_updated': datetime.now().strftime('%Y-%m-%d')
            }
            writer.writerow(row)
    
    print(f"✅ Database saved: supported_leagues_database.csv")
    print(f"📈 Total leagues: {len(leagues_data)}")
    
    # Generate summary statistics
    generate_summary_stats(leagues_data)
    
    return csv_filename

def get_current_season(season_format):
    """Generate current season based on format"""
    if '-' in season_format:
        return season_format  # e.g., "2025-26"
    else:
        return season_format  # e.g., "2025"

def generate_summary_stats(leagues_data):
    """Generate summary statistics"""
    
    print("\n📊 LEAGUE STATISTICS:")
    print("=" * 50)
    
    # Count by country
    countries = {}
    tiers = {}
    status_count = {}
    
    for league in leagues_data:
        # Count by country
        country = league['country']
        countries[country] = countries.get(country, 0) + 1
        
        # Count by tier
        tier = league['tier']
        tier_name = {0: 'International/Cups', 1: 'Top Tier', 2: 'Second Tier', 3: 'Third Tier'}.get(tier, f'Tier {tier}')
        tiers[tier_name] = tiers.get(tier_name, 0) + 1
        
        # Count by status
        status = league['status']
        status_count[status] = status_count.get(status, 0) + 1
    
    print("🌍 BY COUNTRY/REGION:")
    for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True):
        print(f"   {country}: {count} leagues")
    
    print(f"\n🏆 BY TIER:")
    for tier, count in sorted(tiers.items()):
        print(f"   {tier}: {count} leagues")
    
    print(f"\n📋 BY STATUS:")
    for status, count in status_count.items():
        print(f"   {status}: {count} leagues")
    
    # Leagues with confirmed IDs
    confirmed_ids = [l for l in leagues_data if l['league_id'] is not None]
    print(f"\n✅ Confirmed API IDs: {len(confirmed_ids)}/{len(leagues_data)} leagues")

if __name__ == "__main__":
    create_leagues_csv()