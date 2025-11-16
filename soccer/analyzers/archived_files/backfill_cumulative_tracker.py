#!/usr/bin/env python3
"""
Backfill Cumulative Tracker

Adds historical picks from September 7, 2025 onwards to the cumulative tracker
"""

from cumulative_picks_tracker import CumulativePicksTracker
from datetime import datetime, timedelta
import os

def backfill_historical_picks():
    """Backfill cumulative tracker with historical picks since September 7"""
    
    api_key = 'ceb338b9bcb82a452efc114fb2d3cccac67f58be1569e7b5acf1d2195adeae11'
    tracker = CumulativePicksTracker(api_key)
    
    # Start from September 1, 2025  
    start_date = datetime(2025, 9, 1)
    current_date = datetime.now()
    
    print("📈 Backfilling cumulative tracker with historical picks...")
    print(f"📅 Date range: {start_date.strftime('%Y-%m-%d')} to {current_date.strftime('%Y-%m-%d')}")
    
    date = start_date
    total_added = 0
    
    while date <= current_date:
        date_str = date.strftime('%Y%m%d')
        picks_file = f"./soccer/output reports/daily_picks_{date_str}.csv"
        
        if os.path.exists(picks_file):
            print(f"📊 Processing {date.strftime('%Y-%m-%d')}...")
            try:
                tracker.add_daily_picks_to_tracker(date_str)
                total_added += 1
            except Exception as e:
                print(f"⚠️ Error processing {date_str}: {e}")
        
        date += timedelta(days=1)
    
    print(f"\n✅ Backfill complete! Processed {total_added} days of historical picks")
    
    # Generate final report
    if total_added > 0:
        tracker.generate_cumulative_report()

if __name__ == "__main__":
    backfill_historical_picks()