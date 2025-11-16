#!/usr/bin/env python3
"""
Rebuild Cumulative History for Soccer Reports

This script rebuilds the cumulative summary files across all date folders
by reading the best bets data from each day and accumulating it properly.
"""

import os
import pandas as pd
from datetime import datetime

def rebuild_cumulative_history():
    """Rebuild cumulative history from all available reports"""

    reports_dir = 'reports'

    if not os.path.exists(reports_dir):
        print(f"❌ Reports directory not found: {reports_dir}")
        return

    # Get all date folders (format: YYYYMMDD)
    date_folders = sorted([
        d for d in os.listdir(reports_dir)
        if os.path.isdir(os.path.join(reports_dir, d)) and d.isdigit() and len(d) == 8
    ])

    if not date_folders:
        print("❌ No date folders found")
        return

    print(f"📊 Found {len(date_folders)} date folders: {', '.join(date_folders)}")
    print("\n" + "="*80)

    cumulative_data = []

    for date_folder in date_folders:
        # Convert YYYYMMDD to YYYY-MM-DD
        date_str = f"{date_folder[:4]}-{date_folder[4:6]}-{date_folder[6:]}"

        # Look for best bets file
        best_bets_file = os.path.join(reports_dir, date_folder, f'soccer_best_bets_{date_str}.csv')

        if not os.path.exists(best_bets_file):
            print(f"⚠️  {date_str}: No best bets file found")
            continue

        try:
            # Read the day's bets
            df = pd.read_csv(best_bets_file)

            if df.empty:
                print(f"📊 {date_str}: No bets (empty)")
                summary_row = {
                    'date': date_str,
                    'total_bets': 0,
                    'avg_confidence': 0.0,
                    'avg_odds': 0.0,
                    'total_stake_pct': 0.0,
                    'top_league': 'N/A',
                    'match_winners': 0,
                    'totals_bets': 0,
                    'btts_bets': 0,
                    'corners_bets': 0
                }
            else:
                # Calculate summary statistics
                summary_row = {
                    'date': date_str,
                    'total_bets': len(df),
                    'avg_confidence': df['confidence'].mean(),
                    'avg_odds': df['odds'].mean(),
                    'total_stake_pct': df['kelly_stake'].sum(),
                    'top_league': df['league'].value_counts().index[0] if not df.empty else 'N/A',
                    'match_winners': len(df[df['market'].str.contains('Win|Draw', na=False)]),
                    'totals_bets': len(df[df['market'].str.contains('Over|Under', na=False) & ~df['market'].str.contains('Corner', na=False)]),
                    'btts_bets': len(df[df['market'].str.contains('BTTS', na=False)]),
                    'corners_bets': len(df[df['market'].str.contains('Corner', na=False)])
                }

                print(f"✅ {date_str}: {len(df)} bets, {summary_row['avg_confidence']:.1%} confidence, {summary_row['top_league']}")

            cumulative_data.append(summary_row)

        except Exception as e:
            print(f"❌ {date_str}: Error reading file - {e}")
            continue

    if not cumulative_data:
        print("\n❌ No data collected")
        return

    # Create cumulative DataFrame
    cumulative_df = pd.DataFrame(cumulative_data)

    print("\n" + "="*80)
    print(f"✅ Cumulative data built: {len(cumulative_df)} days")
    print("\nSummary:")
    print(cumulative_df.to_string(index=False))

    # Save cumulative file to each date folder
    print("\n" + "="*80)
    print("💾 Saving cumulative files to each date folder...")

    for i, date_folder in enumerate(date_folders):
        date_str = f"{date_folder[:4]}-{date_folder[4:6]}-{date_folder[6:]}"

        # Get cumulative data up to and including this date
        cumulative_up_to_date = cumulative_df[cumulative_df['date'] <= date_str].copy()

        # Save to this date folder
        cumulative_file = os.path.join(reports_dir, date_folder, f'soccer_cumulative_summary_{date_str}.csv')
        cumulative_up_to_date.to_csv(cumulative_file, index=False)

        print(f"  ✅ {date_str}: {len(cumulative_up_to_date)} days of history")

    print("\n✅ Cumulative history rebuilt successfully!")
    print(f"📊 Total days tracked: {len(cumulative_df)}")
    print(f"📊 Total bets across all days: {cumulative_df['total_bets'].sum()}")
    print(f"📊 Average confidence: {cumulative_df['avg_confidence'].mean():.1%}")


if __name__ == "__main__":
    print("⚽ REBUILDING SOCCER CUMULATIVE HISTORY")
    print("="*80 + "\n")
    rebuild_cumulative_history()
