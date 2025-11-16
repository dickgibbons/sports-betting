#!/usr/bin/env python3
"""
Automated Daily Report and Tracker Generator
Generates all three reports and all three trackers daily:

REPORTS:
1. Daily betting report with predictions
2. Comprehensive tracker with simulated outcomes
3. Specialized trackers (High Confidence & Top 8)

TRACKERS:
1. Comprehensive all-time picks tracker
2. High confidence bets tracker (85%+)
3. Top 8 daily bets tracker
"""

import subprocess
import sys
import os
from datetime import datetime
import pandas as pd

def run_script(script_path, description):
    """Run a Python script and return success status"""
    print(f"\n🎯 {description}...")
    print("=" * 60)
    
    try:
        result = subprocess.run([sys.executable, script_path], 
                              capture_output=True, text=True, cwd=os.path.dirname(script_path))
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            if result.stdout:
                # Show last few lines of output
                lines = result.stdout.strip().split('\n')
                for line in lines[-10:]:  # Show last 10 lines
                    print(f"   {line}")
            return True
        else:
            print(f"❌ {description} failed")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False

def update_all_time_picks():
    """Update the all-time picks history with latest daily picks"""
    print("\n📊 Updating all-time picks history...")
    
    base_dir = "/Users/dickgibbons/soccer-betting-python/soccer"
    all_time_file = f"{base_dir}/output reports/all_time_picks_history_fixed.csv"
    
    # Get today's date
    today = datetime.now().strftime("%Y%m%d")
    daily_file = f"{base_dir}/output reports/daily_picks_{today}.csv"
    
    if not os.path.exists(daily_file):
        print(f"⚠️ No daily picks file found for {today}")
        return False
    
    try:
        # Load daily picks
        daily_df = pd.read_csv(daily_file)
        print(f"📅 Found {len(daily_df)} picks for {today}")
        
        # Load existing all-time picks
        if os.path.exists(all_time_file):
            all_time_df = pd.read_csv(all_time_file)
            
            # Check if today's picks already exist
            if 'date' in all_time_df.columns:
                existing_dates = all_time_df['date'].unique()
                today_formatted = datetime.now().strftime("%Y-%m-%d")
                
                if today_formatted in existing_dates:
                    print(f"⚠️ Picks for {today_formatted} already exist in all-time history")
                    return True
            
            # Combine with existing picks
            combined_df = pd.concat([all_time_df, daily_df], ignore_index=True)
        else:
            combined_df = daily_df
        
        # Save updated all-time picks
        combined_df.to_csv(all_time_file, index=False)
        print(f"✅ Updated all-time picks history: {len(combined_df)} total picks")
        return True
        
    except Exception as e:
        print(f"❌ Error updating all-time picks: {e}")
        return False

def main():
    """Main function to generate all daily reports and trackers"""
    
    print("🚀 AUTOMATED DAILY SOCCER BETTING REPORTS & TRACKERS")
    print("=" * 70)
    print(f"📅 Date: {datetime.now().strftime('%A, %Y-%m-%d')}")
    print("=" * 70)
    
    base_dir = "/Users/dickgibbons/soccer-betting-python/soccer"
    
    # Track success of each component
    results = {}
    
    # 1. Generate daily betting report (includes cumulative tracker update)
    results['daily_report'] = run_script(
        f"{base_dir}/daily_betting_report_generator.py",
        "GENERATING DAILY BETTING REPORT"
    )
    
    # 2. Update all-time picks history
    results['all_time_update'] = update_all_time_picks()
    
    # 3. Create/update comprehensive tracker with simulated outcomes
    results['comprehensive_tracker'] = run_script(
        f"{base_dir}/create_comprehensive_tracker.py",
        "GENERATING COMPREHENSIVE PICKS TRACKER"
    )
    
    # 4. Create/update specialized trackers (High Confidence & Top 8)
    results['specialized_trackers'] = run_script(
        f"{base_dir}/create_specialized_trackers.py",
        "GENERATING SPECIALIZED TRACKERS"
    )
    
    # Generate summary report
    print("\n" + "=" * 70)
    print("📊 DAILY GENERATION SUMMARY")
    print("=" * 70)
    
    success_count = sum(results.values())
    total_tasks = len(results)
    
    for task, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{task.replace('_', ' ').title()}: {status}")
    
    print(f"\n🎯 Overall Success Rate: {success_count}/{total_tasks} ({success_count/total_tasks*100:.1f}%)")
    
    if success_count == total_tasks:
        print("🏆 ALL REPORTS AND TRACKERS GENERATED SUCCESSFULLY!")
        
        # List generated files
        print("\n📁 Generated Files:")
        today = datetime.now().strftime("%Y%m%d")
        files_to_check = [
            f"output reports/daily_picks_{today}.csv",
            f"output reports/daily_report_{today}.txt", 
            f"output reports/all_time_picks_history_fixed.csv",
            f"output reports/comprehensive_picks_tracker.csv",
            f"output reports/picks_performance_summary.txt",
            f"output reports/high_confidence_tracker.csv",
            f"output reports/top8_daily_tracker.csv",
            f"output reports/strategy_comparison.txt"
        ]
        
        for file_path in files_to_check:
            full_path = f"{base_dir}/{file_path}"
            if os.path.exists(full_path):
                size = os.path.getsize(full_path)
                print(f"   ✅ {file_path} ({size:,} bytes)")
            else:
                print(f"   ❌ {file_path} (missing)")
    else:
        print("⚠️ SOME COMPONENTS FAILED - CHECK LOGS ABOVE")
    
    print("\n" + "=" * 70)
    print("🎯 AUTOMATED DAILY GENERATION COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()