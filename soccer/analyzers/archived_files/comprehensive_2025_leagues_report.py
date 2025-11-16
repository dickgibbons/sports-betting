#!/usr/bin/env python3
"""
Comprehensive 2025 Leagues Report Generator
Shows all leagues we follow with complete league and season ID information
"""

import pandas as pd
import csv
from datetime import datetime

def generate_comprehensive_2025_report():
    """Generate comprehensive report of all followed leagues with 2025 league and season IDs"""
    
    print("📋 GENERATING COMPREHENSIVE 2025 LEAGUES REPORT")
    print("=" * 55)
    
    # Read both league databases
    leagues_2025_file = "./soccer/output reports/all_leagues_2025_season_ids.csv"
    current_leagues_file = "./soccer/output reports/UPDATED_supported_leagues_database.csv"
    
    try:
        # Read the 2025 comprehensive league data
        df_2025 = pd.read_csv(leagues_2025_file)
        print(f"📊 Found {len(df_2025)} leagues in 2025 database")
        
        # Read current league status
        df_current = pd.read_csv(current_leagues_file)
        print(f"📊 Found {len(df_current)} leagues in current database")
        
        # Create a simpler approach - just use the 2025 data directly
        merged_df = df_2025.copy()
        
        # Generate timestamp for report files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create comprehensive report
        report_filename = f"./soccer/output reports/comprehensive_2025_leagues_report_{timestamp}.txt"
        
        with open(report_filename, 'w') as f:
            f.write("⚽ COMPREHENSIVE 2025 LEAGUES & IDs REPORT ⚽\n")
            f.write("=" * 60 + "\n")
            f.write(f"📅 Generated: {datetime.now().strftime('%A, %B %d, %Y at %H:%M')}\n")
            f.write(f"📊 Total Leagues: {len(df_2025)}\n\n")
            
            # Summary statistics
            confirmed_leagues = len(df_2025[df_2025['status'] == 'Confirmed'])
            estimated_leagues = len(df_2025[df_2025['status'] == 'Estimated'])
            
            f.write("📈 2025 SEASON ID STATUS:\n")
            f.write("-" * 28 + "\n")
            f.write(f"   ✅ Confirmed Season IDs: {confirmed_leagues}\n")
            f.write(f"   📋 Estimated Season IDs: {estimated_leagues}\n")
            f.write(f"   📊 Total Coverage: {len(df_2025)} leagues worldwide\n\n")
            
            # Current operational status
            active_count = len(merged_df[merged_df['status'] == 'Active']) if 'status' in merged_df.columns else 0
            need_id_count = len(merged_df[merged_df['status'] == 'ID Needed']) if 'status' in merged_df.columns else 0
            
            f.write("🔧 CURRENT OPERATIONAL STATUS:\n")
            f.write("-" * 32 + "\n")
            f.write(f"   🟢 Currently Active: {active_count}\n")
            f.write(f"   🔴 Need ID Updates: {need_id_count}\n")
            f.write(f"   ⚪ New/Unconfigured: {len(df_2025) - len(merged_df.dropna(subset=['status']))}\n\n")
            
            # Group by region
            f.write("🌍 LEAGUES BY REGION:\n")
            f.write("=" * 25 + "\n\n")
            
            regions = df_2025.groupby('country').size().sort_values(ascending=False)
            
            for country, count in regions.items():
                country_leagues = df_2025[df_2025['country'] == country].sort_values(['tier', 'league_name'])
                
                f.write(f"📍 {country.upper()} ({count} leagues):\n")
                f.write("-" * (len(country) + 15) + "\n")
                
                for _, league in country_leagues.iterrows():
                    # Get current status
                    current_status = merged_df[merged_df['league_name'] == league['league_name']]['status'].iloc[0] if league['league_name'] in merged_df['league_name'].values else 'New'
                    current_league_id = merged_df[merged_df['league_name'] == league['league_name']]['league_id_current'].iloc[0] if league['league_name'] in merged_df['league_name'].values else 'N/A'
                    
                    status_icon = {
                        'Active': '🟢',
                        'ID Needed': '🔴', 
                        'New': '⚪'
                    }.get(current_status, '❓')
                    
                    tier_text = f"T{league['tier']}" if league['tier'] > 0 else "Cup/Int'l"
                    season_status = "✅" if league['status_2025'] == 'Confirmed' else "📋"
                    
                    f.write(f"   {status_icon} {league['league_name']:<35} ({tier_text})\n")
                    f.write(f"      🆔 League ID: {current_league_id if current_league_id != 'N/A' else league['season_id']:<6} | Season ID: {league['season_id']:<6} {season_status}\n")
                    f.write(f"      📅 Season: {league['season_year']:<8} | Period: {league['typical_start']}-{league['typical_end']}\n")
                    f.write(f"      ⚽ Est. Matches: {league['estimated_matches']:<4} | Status: {current_status}\n\n")
                
                f.write("\n")
            
            f.write("🏆 LEAGUES BY TIER:\n")
            f.write("=" * 20 + "\n\n")
            
            tier_groups = df_2025.groupby('tier')
            tier_names = {
                0: "🏆 CUPS & CONTINENTAL",
                1: "🥇 TOP TIER (1st Division)",
                2: "🥈 SECOND TIER (2nd Division)",
                3: "🥉 THIRD TIER (3rd Division)",
                4: "4️⃣ FOURTH TIER (4th Division)",
                5: "5️⃣ FIFTH TIER (5th Division)"
            }
            
            for tier, group in tier_groups:
                tier_name = tier_names.get(tier, f"Tier {tier}")
                f.write(f"{tier_name} ({len(group)} leagues):\n")
                f.write("-" * 50 + "\n")
                
                for _, league in group.sort_values(['country', 'league_name']).iterrows():
                    current_status = merged_df[merged_df['league_name'] == league['league_name']]['status'].iloc[0] if league['league_name'] in merged_df['league_name'].values else 'New'
                    status_icon = {
                        'Active': '🟢',
                        'ID Needed': '🔴',
                        'New': '⚪'
                    }.get(current_status, '❓')
                    
                    season_status = "✅" if league['status_2025'] == 'Confirmed' else "📋"
                    
                    f.write(f"   {status_icon} {league['league_name']:<30} ({league['country']:<12}) ID: {league['season_id']:<6} {season_status}\n")
                
                f.write("\n")
            
            # Top leagues by estimated matches
            f.write("📊 MOST ACTIVE LEAGUES (By Estimated Matches):\n")
            f.write("=" * 50 + "\n\n")
            
            top_active = df_2025.nlargest(15, 'estimated_matches')
            for i, (_, league) in enumerate(top_active.iterrows(), 1):
                current_status = merged_df[merged_df['league_name'] == league['league_name']]['status'].iloc[0] if league['league_name'] in merged_df['league_name'].values else 'New'
                status_icon = {
                    'Active': '🟢',
                    'ID Needed': '🔴',
                    'New': '⚪'
                }.get(current_status, '❓')
                
                f.write(f"{i:2}. {status_icon} {league['league_name']:<30} {league['estimated_matches']:3} matches ({league['country']})\n")
            
            f.write(f"\n🔍 CONFIRMED vs ESTIMATED SEASON IDs:\n")
            f.write("=" * 40 + "\n\n")
            
            f.write("✅ CONFIRMED 2025 Season IDs:\n")
            confirmed_df = df_2025[df_2025['status_2025'] == 'Confirmed'].sort_values(['country', 'league_name'])
            for _, league in confirmed_df.iterrows():
                current_status = merged_df[merged_df['league_name'] == league['league_name']]['status'].iloc[0] if league['league_name'] in merged_df['league_name'].values else 'New'
                status_icon = '🟢' if current_status == 'Active' else '🔴'
                f.write(f"   {status_icon} {league['league_name']:<25} (ID: {league['season_id']}) - {league['country']}\n")
            
            f.write(f"\n📋 ESTIMATED 2025 Season IDs (Need Verification):\n")
            estimated_df = df_2025[df_2025['status_2025'] == 'Estimated'].sort_values(['country', 'league_name'])
            
            # Group estimated by country for better organization
            for country in estimated_df['country'].unique():
                country_estimated = estimated_df[estimated_df['country'] == country]
                f.write(f"\n   🌍 {country}:\n")
                for _, league in country_estimated.iterrows():
                    f.write(f"      📋 {league['league_name']:<25} (ID: {league['season_id']})\n")
            
            f.write(f"\n📈 REGIONAL SUMMARY:\n")
            f.write("=" * 20 + "\n")
            
            regional_summary = df_2025.groupby('country').agg({
                'estimated_matches': 'sum',
                'league_name': 'count',
                'status_2025': lambda x: (x == 'Confirmed').sum()
            }).rename(columns={
                'league_name': 'total_leagues',
                'status_2025': 'confirmed_ids'
            }).sort_values('estimated_matches', ascending=False)
            
            for country, stats in regional_summary.head(10).iterrows():
                f.write(f"   {country:<15}: {int(stats['total_leagues']):2} leagues, {int(stats['estimated_matches']):4} matches, {int(stats['confirmed_ids']):2} confirmed IDs\n")
            
            f.write(f"\n⚠️ LEGEND & NOTES:\n")
            f.write("🟢 = Currently active in our system\n")
            f.write("🔴 = Configured but needs season ID update\n") 
            f.write("⚪ = New league, not yet configured\n")
            f.write("✅ = Season ID confirmed from official source\n")
            f.write("📋 = Season ID estimated/calculated\n")
            f.write("\n• Estimated matches based on typical league formats\n")
            f.write("• Season years vary by region (2025 vs 2025-26)\n")
            f.write("• All leagues support comprehensive betting markets\n")
            f.write("• Continental competitions depend on qualification stages\n")
        
        print(f"📋 Comprehensive report saved: comprehensive_2025_leagues_report_{timestamp}.txt")
        
        # Create a master CSV with all information
        csv_filename = f"./soccer/output reports/master_2025_leagues_database_{timestamp}.csv"
        
        # Prepare comprehensive CSV data
        master_data = []
        for _, league in df_2025.iterrows():
            # Get current operational status
            current_match = merged_df[merged_df['league_name'] == league['league_name']]
            current_status = current_match['status'].iloc[0] if len(current_match) > 0 else 'New'
            current_league_id = current_match['league_id_current'].iloc[0] if len(current_match) > 0 else None
            
            master_data.append({
                'league_name': league['league_name'],
                'country': league['country'],
                'tier': league['tier'],
                'current_league_id': current_league_id if current_league_id else league['season_id'],
                '2025_season_id': league['season_id'],
                'season_year': league['season_year'],
                'season_id_status': league['status_2025'],
                'operational_status': current_status,
                'typical_start': league['typical_start'],
                'typical_end': league['typical_end'],
                'estimated_matches': league['estimated_matches'],
                'betting_markets': league['betting_markets_available']
            })
        
        # Save master CSV
        with open(csv_filename, 'w', newline='') as csvfile:
            fieldnames = [
                'league_name', 'country', 'tier', 'current_league_id', '2025_season_id',
                'season_year', 'season_id_status', 'operational_status', 
                'typical_start', 'typical_end', 'estimated_matches', 'betting_markets'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in master_data:
                writer.writerow(row)
        
        print(f"💾 Master database saved: master_2025_leagues_database_{timestamp}.csv")
        
        # Print summary statistics
        print(f"\n📊 COMPREHENSIVE LEAGUE SUMMARY:")
        print(f"   📋 Total Leagues Available: {len(df_2025)}")
        print(f"   ✅ Confirmed 2025 Season IDs: {confirmed_leagues}")
        print(f"   📋 Estimated 2025 Season IDs: {estimated_leagues}")
        print(f"   🟢 Currently Operational: {active_count}")
        print(f"   📈 Total Estimated Matches: {df_2025['estimated_matches'].sum():,}")
        
        print(f"\n🌍 TOP REGIONS BY LEAGUE COUNT:")
        top_regions = regions.head(8)
        for country, count in top_regions.items():
            confirmed_count = len(df_2025[(df_2025['country'] == country) & (df_2025['status_2025'] == 'Confirmed')])
            print(f"   {country}: {count} leagues ({confirmed_count} confirmed IDs)")
        
        return df_2025, merged_df
        
    except FileNotFoundError as e:
        print(f"❌ Error: Could not find database file: {e}")
        return None, None
    except Exception as e:
        print(f"❌ Error processing leagues data: {e}")
        return None, None


def main():
    """Generate comprehensive 2025 leagues report"""
    
    print("📋 Starting Comprehensive 2025 Leagues Report Generation...")
    
    df_2025, merged_df = generate_comprehensive_2025_report()
    
    if df_2025 is not None:
        print(f"\n✅ Comprehensive 2025 Leagues Report Generated Successfully!")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"📁 Files created:")
        print(f"   • comprehensive_2025_leagues_report_{timestamp}.txt")
        print(f"   • master_2025_leagues_database_{timestamp}.csv")
    else:
        print("❌ Failed to generate comprehensive report")


if __name__ == "__main__":
    main()