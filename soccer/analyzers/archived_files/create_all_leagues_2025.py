#!/usr/bin/env python3
"""
Generate comprehensive CSV of all possible leagues with 2025 season IDs
Based on common football data API structures and league patterns
"""

import csv
from datetime import datetime

def create_all_leagues_2025_csv():
    """Create comprehensive CSV of all possible leagues for 2025"""
    
    # Comprehensive leagues database with estimated season IDs for 2025
    all_leagues_2025 = [
        # ENGLAND
        {'league_name': 'Premier League', 'country': 'England', 'tier': 1, 'season_id': 1625, 'season_year': '2025-26', 'status': 'Confirmed', 'typical_start': 'August', 'typical_end': 'May'},
        {'league_name': 'Championship', 'country': 'England', 'tier': 2, 'season_id': 1626, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'August', 'typical_end': 'May'},
        {'league_name': 'League One', 'country': 'England', 'tier': 3, 'season_id': 1627, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'August', 'typical_end': 'May'},
        {'league_name': 'League Two', 'country': 'England', 'tier': 4, 'season_id': 1628, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'August', 'typical_end': 'May'},
        {'league_name': 'National League', 'country': 'England', 'tier': 5, 'season_id': 1629, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'August', 'typical_end': 'May'},
        {'league_name': 'FA Cup', 'country': 'England', 'tier': 0, 'season_id': 1630, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'August', 'typical_end': 'May'},
        {'league_name': 'EFL Cup', 'country': 'England', 'tier': 0, 'season_id': 1631, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'August', 'typical_end': 'February'},
        {'league_name': 'FA Trophy', 'country': 'England', 'tier': 3, 'season_id': 1632, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'October', 'typical_end': 'May'},
        
        # SPAIN
        {'league_name': 'La Liga', 'country': 'Spain', 'tier': 1, 'season_id': 1729, 'season_year': '2025-26', 'status': 'Confirmed', 'typical_start': 'August', 'typical_end': 'May'},
        {'league_name': 'Segunda División', 'country': 'Spain', 'tier': 2, 'season_id': 1730, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'August', 'typical_end': 'May'},
        {'league_name': 'Copa del Rey', 'country': 'Spain', 'tier': 0, 'season_id': 1731, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'October', 'typical_end': 'April'},
        
        # GERMANY
        {'league_name': 'Bundesliga', 'country': 'Germany', 'tier': 1, 'season_id': 1854, 'season_year': '2025-26', 'status': 'Confirmed', 'typical_start': 'August', 'typical_end': 'May'},
        {'league_name': '2. Bundesliga', 'country': 'Germany', 'tier': 2, 'season_id': 1855, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'August', 'typical_end': 'May'},
        {'league_name': '3. Liga', 'country': 'Germany', 'tier': 3, 'season_id': 1856, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'August', 'typical_end': 'May'},
        {'league_name': 'DFB-Pokal', 'country': 'Germany', 'tier': 0, 'season_id': 1857, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'August', 'typical_end': 'May'},
        
        # ITALY
        {'league_name': 'Serie A', 'country': 'Italy', 'tier': 1, 'season_id': 2105, 'season_year': '2025-26', 'status': 'Confirmed', 'typical_start': 'August', 'typical_end': 'May'},
        {'league_name': 'Serie B', 'country': 'Italy', 'tier': 2, 'season_id': 2106, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'August', 'typical_end': 'May'},
        {'league_name': 'Coppa Italia', 'country': 'Italy', 'tier': 0, 'season_id': 2107, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'August', 'typical_end': 'May'},
        
        # FRANCE
        {'league_name': 'Ligue 1', 'country': 'France', 'tier': 1, 'season_id': 1843, 'season_year': '2025-26', 'status': 'Confirmed', 'typical_start': 'August', 'typical_end': 'May'},
        {'league_name': 'Ligue 2', 'country': 'France', 'tier': 2, 'season_id': 1844, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'August', 'typical_end': 'May'},
        {'league_name': 'Coupe de France', 'country': 'France', 'tier': 0, 'season_id': 1845, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'November', 'typical_end': 'May'},
        
        # NETHERLANDS
        {'league_name': 'Eredivisie', 'country': 'Netherlands', 'tier': 1, 'season_id': 2200, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'August', 'typical_end': 'May'},
        {'league_name': 'Eerste Divisie', 'country': 'Netherlands', 'tier': 2, 'season_id': 2201, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'August', 'typical_end': 'May'},
        {'league_name': 'KNVB Cup', 'country': 'Netherlands', 'tier': 0, 'season_id': 2202, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'September', 'typical_end': 'April'},
        
        # PORTUGAL
        {'league_name': 'Primeira Liga', 'country': 'Portugal', 'tier': 1, 'season_id': 2300, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'August', 'typical_end': 'May'},
        {'league_name': 'LigaPro', 'country': 'Portugal', 'tier': 2, 'season_id': 2301, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'August', 'typical_end': 'May'},
        {'league_name': 'Taça de Portugal', 'country': 'Portugal', 'tier': 0, 'season_id': 2302, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'September', 'typical_end': 'May'},
        
        # BELGIUM
        {'league_name': 'Pro League', 'country': 'Belgium', 'tier': 1, 'season_id': 2400, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'August', 'typical_end': 'May'},
        {'league_name': 'Belgian Cup', 'country': 'Belgium', 'tier': 0, 'season_id': 2401, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'August', 'typical_end': 'March'},
        
        # SCOTLAND
        {'league_name': 'Scottish Premiership', 'country': 'Scotland', 'tier': 1, 'season_id': 2500, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'August', 'typical_end': 'May'},
        {'league_name': 'Scottish Championship', 'country': 'Scotland', 'tier': 2, 'season_id': 2501, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'August', 'typical_end': 'May'},
        {'league_name': 'Scottish Cup', 'country': 'Scotland', 'tier': 0, 'season_id': 2502, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'October', 'typical_end': 'May'},
        
        # EUROPEAN COMPETITIONS
        {'league_name': 'UEFA Champions League', 'country': 'Europe', 'tier': 0, 'season_id': 3000, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'September', 'typical_end': 'May'},
        {'league_name': 'UEFA Europa League', 'country': 'Europe', 'tier': 0, 'season_id': 3001, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'September', 'typical_end': 'May'},
        {'league_name': 'UEFA Europa Conference League', 'country': 'Europe', 'tier': 0, 'season_id': 3002, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'August', 'typical_end': 'May'},
        {'league_name': 'UEFA Nations League', 'country': 'Europe', 'tier': 0, 'season_id': 3003, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'September', 'typical_end': 'November'},
        
        # INTERNATIONAL COMPETITIONS
        {'league_name': 'FIFA Club World Cup', 'country': 'International', 'tier': 0, 'season_id': 4000, 'season_year': '2025', 'status': 'Estimated', 'typical_start': 'June', 'typical_end': 'July'},
        {'league_name': 'FIFA Club World Cup Playin', 'country': 'International', 'tier': 0, 'season_id': 4001, 'season_year': '2025', 'status': 'Estimated', 'typical_start': 'May', 'typical_end': 'June'},
        
        # WORLD CUP QUALIFICATIONS
        {'league_name': 'WC Qualification Europe', 'country': 'International', 'tier': 0, 'season_id': 4100, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'September', 'typical_end': 'November'},
        {'league_name': 'WC Qualification Africa', 'country': 'International', 'tier': 0, 'season_id': 4101, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'September', 'typical_end': 'November'},
        {'league_name': 'WC Qualification Asia', 'country': 'International', 'tier': 0, 'season_id': 4102, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'September', 'typical_end': 'March'},
        {'league_name': 'WC Qualification South America', 'country': 'International', 'tier': 0, 'season_id': 4103, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'September', 'typical_end': 'March'},
        {'league_name': 'WC Qualification CONCACAF', 'country': 'International', 'tier': 0, 'season_id': 4104, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'September', 'typical_end': 'March'},
        {'league_name': 'WC Qualification Oceania', 'country': 'International', 'tier': 0, 'season_id': 4105, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'September', 'typical_end': 'March'},
        
        # USA/CANADA
        {'league_name': 'MLS', 'country': 'USA', 'tier': 1, 'season_id': 5000, 'season_year': '2025', 'status': 'Estimated', 'typical_start': 'February', 'typical_end': 'November'},
        {'league_name': 'USL Championship', 'country': 'USA', 'tier': 2, 'season_id': 5001, 'season_year': '2025', 'status': 'Estimated', 'typical_start': 'March', 'typical_end': 'November'},
        {'league_name': 'USL League One', 'country': 'USA', 'tier': 3, 'season_id': 5002, 'season_year': '2025', 'status': 'Estimated', 'typical_start': 'March', 'typical_end': 'October'},
        {'league_name': 'NWSL', 'country': 'USA', 'tier': 1, 'season_id': 5003, 'season_year': '2025', 'status': 'Estimated', 'typical_start': 'March', 'typical_end': 'November'},
        {'league_name': 'US Open Cup', 'country': 'USA', 'tier': 0, 'season_id': 5004, 'season_year': '2025', 'status': 'Estimated', 'typical_start': 'April', 'typical_end': 'September'},
        {'league_name': 'Canadian Premier League', 'country': 'Canada', 'tier': 1, 'season_id': 5100, 'season_year': '2025', 'status': 'Estimated', 'typical_start': 'April', 'typical_end': 'October'},
        
        # MEXICO
        {'league_name': 'Liga MX', 'country': 'Mexico', 'tier': 1, 'season_id': 5200, 'season_year': '2025', 'status': 'Estimated', 'typical_start': 'January', 'typical_end': 'December'},
        {'league_name': 'Liga de Expansión MX', 'country': 'Mexico', 'tier': 2, 'season_id': 5201, 'season_year': '2025', 'status': 'Estimated', 'typical_start': 'January', 'typical_end': 'December'},
        {'league_name': 'Copa MX', 'country': 'Mexico', 'tier': 0, 'season_id': 5202, 'season_year': '2025', 'status': 'Estimated', 'typical_start': 'January', 'typical_end': 'April'},
        
        # SOUTH AMERICA
        {'league_name': 'Copa Libertadores', 'country': 'South America', 'tier': 0, 'season_id': 5300, 'season_year': '2025', 'status': 'Estimated', 'typical_start': 'February', 'typical_end': 'November'},
        {'league_name': 'Copa Sudamericana', 'country': 'South America', 'tier': 0, 'season_id': 5301, 'season_year': '2025', 'status': 'Estimated', 'typical_start': 'March', 'typical_end': 'November'},
        {'league_name': 'Brazil Serie A', 'country': 'Brazil', 'tier': 1, 'season_id': 5400, 'season_year': '2025', 'status': 'Estimated', 'typical_start': 'April', 'typical_end': 'December'},
        {'league_name': 'Brazil Serie B', 'country': 'Brazil', 'tier': 2, 'season_id': 5401, 'season_year': '2025', 'status': 'Estimated', 'typical_start': 'April', 'typical_end': 'November'},
        {'league_name': 'Copa do Brasil', 'country': 'Brazil', 'tier': 0, 'season_id': 5402, 'season_year': '2025', 'status': 'Estimated', 'typical_start': 'February', 'typical_end': 'October'},
        {'league_name': 'Primera División', 'country': 'Argentina', 'tier': 1, 'season_id': 5500, 'season_year': '2025', 'status': 'Estimated', 'typical_start': 'February', 'typical_end': 'December'},
        {'league_name': 'Copa Argentina', 'country': 'Argentina', 'tier': 0, 'season_id': 5501, 'season_year': '2025', 'status': 'Estimated', 'typical_start': 'February', 'typical_end': 'November'},
        
        # NORDIC COUNTRIES
        {'league_name': 'Eliteserien', 'country': 'Norway', 'tier': 1, 'season_id': 6000, 'season_year': '2025', 'status': 'Estimated', 'typical_start': 'March', 'typical_end': 'November'},
        {'league_name': 'First Division', 'country': 'Norway', 'tier': 2, 'season_id': 6001, 'season_year': '2025', 'status': 'Estimated', 'typical_start': 'April', 'typical_end': 'November'},
        {'league_name': 'Allsvenskan', 'country': 'Sweden', 'tier': 1, 'season_id': 6100, 'season_year': '2025', 'status': 'Estimated', 'typical_start': 'March', 'typical_end': 'November'},
        {'league_name': 'Superlig', 'country': 'Denmark', 'tier': 1, 'season_id': 6200, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'July', 'typical_end': 'May'},
        {'league_name': 'Veikkausliiga', 'country': 'Finland', 'tier': 1, 'season_id': 6300, 'season_year': '2025', 'status': 'Estimated', 'typical_start': 'April', 'typical_end': 'October'},
        
        # EASTERN EUROPE
        {'league_name': 'First League', 'country': 'Czech Republic', 'tier': 1, 'season_id': 6400, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'August', 'typical_end': 'May'},
        {'league_name': 'Ekstraklasa', 'country': 'Poland', 'tier': 1, 'season_id': 6500, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'July', 'typical_end': 'May'},
        {'league_name': 'Liga I', 'country': 'Romania', 'tier': 1, 'season_id': 6600, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'July', 'typical_end': 'May'},
        
        # OTHER EUROPE
        {'league_name': 'Super League', 'country': 'Switzerland', 'tier': 1, 'season_id': 6700, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'July', 'typical_end': 'May'},
        {'league_name': 'Austrian Bundesliga', 'country': 'Austria', 'tier': 1, 'season_id': 6800, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'July', 'typical_end': 'May'},
        {'league_name': 'Süper Lig', 'country': 'Turkey', 'tier': 1, 'season_id': 6900, 'season_year': '2025-26', 'status': 'Estimated', 'typical_start': 'August', 'typical_end': 'May'},
        
        # CONCACAF
        {'league_name': 'CONCACAF Champions Cup', 'country': 'International', 'tier': 0, 'season_id': 7000, 'season_year': '2025', 'status': 'Estimated', 'typical_start': 'February', 'typical_end': 'May'},
        {'league_name': 'CONCACAF Central American Cup', 'country': 'International', 'tier': 0, 'season_id': 7001, 'season_year': '2025', 'status': 'Estimated', 'typical_start': 'August', 'typical_end': 'December'},
        {'league_name': 'CONCACAF Caribbean Club Championship', 'country': 'International', 'tier': 0, 'season_id': 7002, 'season_year': '2025', 'status': 'Estimated', 'typical_start': 'May', 'typical_end': 'August'},
    ]
    
    # Create comprehensive CSV
    csv_filename = "./output reports/all_leagues_2025_season_ids.csv"
    
    fieldnames = [
        'league_name',
        'country', 
        'tier',
        'season_id',
        'season_year',
        'status',
        'typical_start',
        'typical_end',
        'estimated_matches',
        'betting_markets_available',
        'last_updated'
    ]
    
    print("🌍 Creating comprehensive 2025 leagues database...")
    
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for league in all_leagues_2025:
            # Estimate number of matches based on tier and type
            estimated_matches = estimate_matches(league)
            
            row = {
                'league_name': league['league_name'],
                'country': league['country'],
                'tier': league['tier'], 
                'season_id': league['season_id'],
                'season_year': league['season_year'],
                'status': league['status'],
                'typical_start': league['typical_start'],
                'typical_end': league['typical_end'],
                'estimated_matches': estimated_matches,
                'betting_markets_available': 'All Markets',
                'last_updated': datetime.now().strftime('%Y-%m-%d')
            }
            writer.writerow(row)
    
    print(f"✅ Database saved: all_leagues_2025_season_ids.csv")
    print(f"📊 Total leagues: {len(all_leagues_2025)}")
    
    # Generate comprehensive statistics
    generate_comprehensive_stats(all_leagues_2025)
    
    return csv_filename

def estimate_matches(league):
    """Estimate number of matches per season"""
    tier = league['tier']
    country = league['country']
    league_name = league['league_name'].lower()
    
    # Cup competitions
    if any(word in league_name for word in ['cup', 'trophy', 'copa', 'coupe', 'pokal']):
        if 'champions' in league_name:
            return 125  # Champions League style
        elif any(word in league_name for word in ['world cup', 'libertadores']):
            return 150
        else:
            return 63   # Domestic cups
    
    # International competitions
    if country == 'International':
        if 'qualification' in league_name:
            return 80
        else:
            return 100
    
    # League competitions by tier
    if tier == 1:  # Top tier
        if country in ['USA', 'Brazil', 'Argentina', 'Mexico']:
            return 380  # American style
        else:
            return 380  # European style (20 teams)
    elif tier == 2:
        return 552  # Championship style (24 teams)
    elif tier >= 3:
        return 462  # League One/Two style (24 teams)
    
    return 300  # Default estimate

def generate_comprehensive_stats(leagues_data):
    """Generate comprehensive statistics"""
    
    print("\n🌍 COMPREHENSIVE LEAGUE STATISTICS:")
    print("=" * 60)
    
    # Count by region
    regions = {
        'Europe': ['England', 'Spain', 'Germany', 'Italy', 'France', 'Netherlands', 'Belgium', 'Scotland', 'Portugal', 'Switzerland', 'Austria', 'Turkey', 'Norway', 'Sweden', 'Denmark', 'Finland', 'Czech Republic', 'Poland', 'Romania', 'Europe'],
        'Americas': ['USA', 'Canada', 'Mexico', 'Brazil', 'Argentina', 'South America'],
        'International': ['International']
    }
    
    region_counts = {region: 0 for region in regions.keys()}
    
    for league in leagues_data:
        country = league['country']
        for region, countries in regions.items():
            if country in countries:
                region_counts[region] += 1
                break
    
    print("🗺️  BY REGION:")
    for region, count in region_counts.items():
        print(f"   {region}: {count} leagues")
    
    # Count by tier
    tier_counts = {}
    for league in leagues_data:
        tier = league['tier']
        tier_name = {0: 'Cups/International', 1: 'Top Division', 2: 'Second Division', 3: 'Third Division', 4: 'Fourth Division', 5: 'Fifth Division'}.get(tier, f'Tier {tier}')
        tier_counts[tier_name] = tier_counts.get(tier_name, 0) + 1
    
    print(f"\n🏆 BY DIVISION:")
    for tier, count in sorted(tier_counts.items()):
        print(f"   {tier}: {count} leagues")
    
    # Count by status
    status_counts = {}
    for league in leagues_data:
        status = league['status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print(f"\n📊 BY STATUS:")
    for status, count in status_counts.items():
        print(f"   {status}: {count} leagues")
    
    # Estimated total matches
    total_matches = sum(estimate_matches(league) for league in leagues_data)
    print(f"\n⚽ ESTIMATED TOTAL MATCHES: {total_matches:,}")
    
    confirmed_leagues = [l for l in leagues_data if l['status'] == 'Confirmed']
    print(f"\n✅ API Integration Status: {len(confirmed_leagues)}/{len(leagues_data)} confirmed")

if __name__ == "__main__":
    create_all_leagues_2025_csv()