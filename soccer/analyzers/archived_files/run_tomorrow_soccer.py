#!/usr/bin/env python3

"""
Run Soccer Betting Report for Tomorrow
=====================================
Generates betting picks for tomorrow's matches
"""

from datetime import datetime, timedelta
from daily_betting_report_generator import DailyBettingReportGenerator

def run_tomorrow_report():
    """Run soccer betting report for tomorrow"""
    
    # Calculate tomorrow's date
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow_str = tomorrow.strftime('%Y-%m-%d')
    day_name = tomorrow.strftime('%A')
    
    print(f"🚀 GENERATING SOCCER REPORT FOR TOMORROW")
    print(f"📅 Date: {day_name}, {tomorrow_str}")
    print("="*50)
    
    # API key
    API_KEY = "960c628e1c91c4b1f125e1eec52ad862"
    
    try:
        # Initialize generator with tomorrow's date
        generator = DailyBettingReportGenerator(API_KEY)
        generator.today = tomorrow_str
        generator.day_name = day_name
        
        print(f"⚽ Generating report for {day_name}, {tomorrow_str}...")
        
        # Generate the report
        daily_report = generator.generate_daily_report()
        
        if daily_report:
            print("\n" + "="*50)
            print("✅ TOMORROW'S SOCCER BETTING REPORT COMPLETED!")
            print("="*50)
            
            total_matches = daily_report.get('total_matches', 0)
            recommended_bets = daily_report.get('recommended_bets', 0)
            
            print(f"📊 Total Matches Analyzed: {total_matches}")
            print(f"🎯 Recommended Bets: {recommended_bets}")
            
            if recommended_bets > 0:
                print(f"\n📋 REPORTS GENERATED:")
                date_str = tomorrow_str.replace('-', '')
                print(f"   • daily_picks_{date_str}.csv - Main betting strategy")
                print(f"   • high_confidence_picks_{date_str}.csv - Conservative picks") 
                print(f"   • daily_report_{date_str}.txt - Formatted report")
                print(f"\n📁 Location: output reports/")
            else:
                print(f"⚠️ No betting opportunities found for tomorrow")
                print(f"   This could mean:")
                print(f"   • No matches scheduled in followed leagues")
                print(f"   • No opportunities met filtering criteria")
                
        else:
            print("\n❌ No report generated")
            print("   Check if there are fixtures tomorrow")
            
    except Exception as e:
        print(f"\n❌ ERROR GENERATING TOMORROW'S REPORT:")
        print(f"   {str(e)}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        
    print(f"\n🎯 Tomorrow's report generation complete")

if __name__ == "__main__":
    run_tomorrow_report()