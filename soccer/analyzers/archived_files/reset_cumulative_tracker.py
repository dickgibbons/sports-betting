#!/usr/bin/env python3
"""
Reset Cumulative Tracker to Real Results Only

This script resets the cumulative tracker to only include entries with verified real results.
No simulated data will be included going forward.
"""

import pandas as pd
import os
from datetime import datetime

def reset_cumulative_tracker():
    """Reset tracker to only include verified results"""
    
    tracker_file = "./soccer/output reports/cumulative_picks_tracker.csv"
    
    print("🔄 Resetting cumulative tracker to real results only...")
    
    # Create new tracker with proper columns including verified_result
    columns = [
        'date', 'kick_off', 'home_team', 'away_team', 'league',
        'market', 'bet_description', 'odds', 'stake_pct', 'edge_pct',
        'confidence_pct', 'quality_score', 'match_status', 'bet_outcome',
        'home_score', 'away_score', 'total_goals', 'total_corners',
        'btts', 'bet_amount', 'potential_win', 'actual_pnl',
        'running_total', 'win_rate', 'total_picks', 'verified_result'
    ]
    
    # Create empty DataFrame with proper structure
    df = pd.DataFrame(columns=columns)
    df.to_csv(tracker_file, index=False)
    
    print(f"✅ Reset cumulative tracker: {tracker_file}")
    print("📊 New tracker will only accept verified real match results")
    print("🚫 No simulated data will be tracked going forward")
    
    return tracker_file

if __name__ == "__main__":
    reset_cumulative_tracker()