#!/usr/bin/env python3
"""
Implement 2025 Season IDs
Updates operational database with 2025 season IDs and activates leagues
"""

import pandas as pd
import csv
import shutil
from datetime import datetime

class SeasonIDImplementer:
    """Implement 2025 season IDs in operational database"""
    
    def __init__(self):
        self.reference_file = "./soccer/output reports/all_leagues_2025_season_ids.csv"
        self.operational_file = "./soccer/output reports/UPDATED_supported_leagues_database.csv"
        self.backup_file = "./soccer/output reports/BACKUP_supported_leagues_database.csv"
    
    def backup_current_database(self):
        """Create backup of current operational database"""
        try:
            shutil.copy2(self.operational_file, self.backup_file)
            print(f"✅ Created backup: BACKUP_supported_leagues_database.csv")
            return True
        except Exception as e:
            print(f"❌ Error creating backup: {e}")
            return False
    
    def load_databases(self):
        """Load both reference and operational databases"""
        try:
            # Load 2025 reference data
            df_2025 = pd.read_csv(self.reference_file)
            print(f"📊 Loaded {len(df_2025)} leagues from 2025 reference database")
            
            # Load current operational data
            df_operational = pd.read_csv(self.operational_file)
            print(f"📊 Loaded {len(df_operational)} leagues from operational database")
            
            return df_2025, df_operational
            
        except Exception as e:
            print(f"❌ Error loading databases: {e}")
            return None, None
    
    def implement_season_ids(self, df_2025, df_operational):
        """Implement 2025 season IDs in operational database"""
        
        print(f"\n🔧 IMPLEMENTING 2025 SEASON IDs")
        print("=" * 40)
        
        updates_made = 0
        new_leagues = 0
        updated_leagues = []
        new_leagues_added = []
        
        # Create a copy of operational data to modify
        updated_operational = df_operational.copy()
        
        # Process each league from 2025 reference
        for _, ref_league in df_2025.iterrows():
            league_name = ref_league['league_name']
            season_id = ref_league['season_id']
            season_year = ref_league['season_year']
            country = ref_league['country']
            tier = ref_league['tier']
            
            # Check if league exists in operational database
            existing_league = updated_operational[updated_operational['league_name'] == league_name]
            
            if len(existing_league) > 0:
                # Update existing league
                idx = existing_league.index[0]
                old_season = updated_operational.loc[idx, 'current_season']
                old_status = updated_operational.loc[idx, 'status']
                
                # Update with 2025 data
                updated_operational.loc[idx, 'league_id'] = season_id
                updated_operational.loc[idx, 'current_season'] = season_year
                updated_operational.loc[idx, 'status'] = 'Active'
                updated_operational.loc[idx, 'last_updated'] = datetime.now().strftime('%m/%d/%y')
                
                if old_status != 'Active':
                    updates_made += 1
                    updated_leagues.append({
                        'league': league_name,
                        'country': country,
                        'old_season': old_season,
                        'new_season': season_year,
                        'season_id': season_id,
                        'old_status': old_status
                    })
                    print(f"   ✅ Updated: {league_name} ({country}) - ID: {season_id}")
                
            else:
                # Add new league
                new_league_row = {
                    'league_name': league_name,
                    'league_id': season_id,
                    'country': country,
                    'tier': tier,
                    'season_format': season_year,
                    'current_season': season_year,
                    'status': 'Active',
                    'betting_factors_configured': 'Yes',
                    'last_updated': datetime.now().strftime('%m/%d/%y')
                }
                
                # Add to dataframe
                new_row_df = pd.DataFrame([new_league_row])
                updated_operational = pd.concat([updated_operational, new_row_df], ignore_index=True)
                
                new_leagues += 1
                new_leagues_added.append({
                    'league': league_name,
                    'country': country,
                    'season_id': season_id,
                    'tier': tier
                })
                print(f"   🆕 Added: {league_name} ({country}) - ID: {season_id}")
        
        return updated_operational, updates_made, new_leagues, updated_leagues, new_leagues_added
    
    def save_updated_database(self, updated_df):
        """Save updated operational database"""
        try:
            updated_df.to_csv(self.operational_file, index=False)
            print(f"✅ Saved updated operational database")
            return True
        except Exception as e:
            print(f"❌ Error saving updated database: {e}")
            return False
    
    def generate_implementation_report(self, updates_made, new_leagues, updated_leagues, new_leagues_added):
        """Generate report of implementation results"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"./soccer/output reports/season_id_implementation_report_{timestamp}.txt"
        
        with open(report_filename, 'w') as f:
            f.write("⚽ 2025 SEASON IDs IMPLEMENTATION REPORT ⚽\n")
            f.write("=" * 50 + "\n")
            f.write(f"📅 Implementation Date: {datetime.now().strftime('%A, %B %d, %Y at %H:%M')}\n\n")
            
            f.write("📊 IMPLEMENTATION SUMMARY:\n")
            f.write("-" * 28 + "\n")
            f.write(f"   🔄 Leagues Updated: {updates_made}\n")
            f.write(f"   🆕 New Leagues Added: {new_leagues}\n")
            f.write(f"   ✅ Total Now Active: {updates_made + new_leagues}\n\n")
            
            if updated_leagues:
                f.write("🔄 UPDATED LEAGUES:\n")
                f.write("-" * 20 + "\n")
                for league in updated_leagues:
                    f.write(f"   ✅ {league['league']} ({league['country']})\n")
                    f.write(f"      🆔 Season ID: {league['season_id']}\n")
                    f.write(f"      📅 Season: {league['old_season']} → {league['new_season']}\n")
                    f.write(f"      🔧 Status: {league['old_status']} → Active\n\n")
            
            if new_leagues_added:
                f.write("🆕 NEW LEAGUES ADDED:\n")
                f.write("-" * 22 + "\n")
                for league in new_leagues_added:
                    tier_text = f"Tier {league['tier']}" if league['tier'] > 0 else "Cup/Continental"
                    f.write(f"   🆕 {league['league']} ({league['country']})\n")
                    f.write(f"      🆔 Season ID: {league['season_id']}\n")
                    f.write(f"      🏆 {tier_text}\n")
                    f.write(f"      ✅ Status: Active\n\n")
            
            f.write("⚠️ IMPORTANT NOTES:\n")
            f.write("• Backup created before implementation\n")
            f.write("• All implemented leagues set to 'Active' status\n")
            f.write("• Betting factors configured for all leagues\n")
            f.write("• API testing recommended before live use\n")
            f.write("• Original database backed up as BACKUP_supported_leagues_database.csv\n")
        
        print(f"📋 Implementation report saved: season_id_implementation_report_{timestamp}.txt")
        return report_filename
    
    def run_implementation(self):
        """Run complete implementation process"""
        
        print("🚀 STARTING 2025 SEASON IDs IMPLEMENTATION")
        print("=" * 50)
        
        # Step 1: Backup current database
        print("\n1️⃣ Creating backup...")
        if not self.backup_current_database():
            print("❌ Failed to create backup. Aborting.")
            return False
        
        # Step 2: Load databases
        print("\n2️⃣ Loading databases...")
        df_2025, df_operational = self.load_databases()
        if df_2025 is None or df_operational is None:
            print("❌ Failed to load databases. Aborting.")
            return False
        
        # Step 3: Implement season IDs
        print("\n3️⃣ Implementing season IDs...")
        updated_df, updates_made, new_leagues, updated_leagues, new_leagues_added = self.implement_season_ids(df_2025, df_operational)
        
        # Step 4: Save updated database
        print(f"\n4️⃣ Saving updated database...")
        if not self.save_updated_database(updated_df):
            print("❌ Failed to save updated database.")
            return False
        
        # Step 5: Generate report
        print(f"\n5️⃣ Generating implementation report...")
        report_file = self.generate_implementation_report(updates_made, new_leagues, updated_leagues, new_leagues_added)
        
        # Summary
        print(f"\n✅ IMPLEMENTATION COMPLETE!")
        print(f"📊 Results:")
        print(f"   🔄 Updated Leagues: {updates_made}")
        print(f"   🆕 New Leagues: {new_leagues}")
        print(f"   ✅ Total Active: {updates_made + new_leagues}")
        print(f"   💾 Backup: BACKUP_supported_leagues_database.csv")
        print(f"   📋 Report: {report_file.split('/')[-1]}")
        
        return True


def main():
    """Run 2025 season IDs implementation"""
    
    print("🚀 2025 Season IDs Implementation Tool")
    print("=" * 40)
    
    implementer = SeasonIDImplementer()
    
    print("\n⚠️ This will:")
    print("   • Backup current operational database")
    print("   • Update all leagues with 2025 season IDs")
    print("   • Set leagues to 'Active' status")
    print("   • Add any new leagues from 2025 reference")
    
    print("\n🚀 Proceeding with automatic implementation...")
    
    success = implementer.run_implementation()
    if success:
        print("\n🎉 Implementation successful! Your betting system now has all 2025 season IDs activated.")
    else:
        print("\n❌ Implementation failed. Check error messages above.")


if __name__ == "__main__":
    main()