#!/usr/bin/env python3
"""
Add Sportsbook Column to Daily Picks
Enriches daily picks files with which sportsbook (DraftKings or FanDuel) offers the best odds
"""

import pandas as pd
import glob
import os
from datetime import datetime

def get_best_sportsbook_for_match(home_team, away_team, market, date_str, sportsbooks_df):
    """Determine which sportsbook has better odds for a specific match and market"""

    # Find matching match in sportsbooks comparison
    match_data = sportsbooks_df[
        (sportsbooks_df['home_team'].str.lower() == home_team.lower()) &
        (sportsbooks_df['away_team'].str.lower() == away_team.lower())
    ]

    if match_data.empty:
        # Try partial matching
        match_data = sportsbooks_df[
            (sportsbooks_df['home_team'].str.contains(home_team.split()[0], case=False, na=False)) &
            (sportsbooks_df['away_team'].str.contains(away_team.split()[0], case=False, na=False))
        ]

    if match_data.empty:
        return 'DraftKings'  # Default

    match_row = match_data.iloc[0]

    # Determine best sportsbook based on market type
    market_lower = market.lower()

    if 'home' in market_lower or 'away' in market_lower:
        # Check home/away market
        if 'home' in market_lower:
            better = match_row.get('home_better', 'DraftKings')
        else:
            better = match_row.get('away_better', 'DraftKings')
    elif 'draw' in market_lower:
        better = match_row.get('draw_better', 'DraftKings')
    elif 'over' in market_lower or 'under' in market_lower:
        if 'over' in market_lower:
            better = match_row.get('over_2.5_better', 'DraftKings')
        else:
            better = match_row.get('under_2.5_better', 'DraftKings')
    else:
        better = 'DraftKings'  # Default

    # Handle 'Equal' case
    if better == 'Equal':
        better = 'DraftKings'

    return better

def add_sportsbook_column_to_picks():
    """Add sportsbook column to all daily picks files"""

    print("📊 ADDING SPORTSBOOK COLUMN TO DAILY PICKS")
    print("=" * 50)

    # Find all daily picks files
    picks_files = glob.glob("output reports/daily_picks_*.csv")
    picks_files.extend(glob.glob("output reports/Older/daily_picks_*.csv"))
    picks_files.sort()

    print(f"📋 Found {len(picks_files)} daily picks files")

    updated_count = 0

    for picks_file in picks_files:
        try:
            # Extract date from filename
            date_str = picks_file.split('_')[-1].replace('.csv', '')
            if len(date_str) != 8:  # YYYYMMDD format
                continue

            # Convert to readable date for matching
            try:
                date_obj = datetime.strptime(date_str, '%Y%m%d')
                formatted_date = date_obj.strftime('%Y%m%d')
            except:
                continue

            # Find corresponding sportsbooks comparison file
            sportsbooks_file = f"output reports/us_sportsbooks_comparison_{formatted_date}.csv"
            if not os.path.exists(sportsbooks_file):
                print(f"⚠️  No sportsbooks data for {date_str}, using default (DraftKings)")
                # Still add column with default value
                df = pd.read_csv(picks_file)

                # Skip if already has sportsbook column
                if 'sportsbook' in df.columns:
                    continue

                # Add sportsbook column with default
                df['sportsbook'] = 'DraftKings'
                df.to_csv(picks_file, index=False)
                updated_count += 1
                continue

            # Load both files
            picks_df = pd.read_csv(picks_file)

            # Skip files with just messages (no real picks)
            if 'No picks today' in picks_df['home_team'].values[0] if len(picks_df) > 0 else False:
                continue

            # Skip if already has sportsbook column
            if 'sportsbook' in picks_df.columns:
                print(f"✅ {date_str} already has sportsbook column")
                continue

            sportsbooks_df = pd.read_csv(sportsbooks_file)

            # Add sportsbook column
            sportsbooks = []
            for idx, pick in picks_df.iterrows():
                home = pick.get('home_team', '')
                away = pick.get('away_team', '')
                market = pick.get('market', '')

                best_book = get_best_sportsbook_for_match(home, away, market, date_str, sportsbooks_df)
                sportsbooks.append(best_book)

            picks_df['sportsbook'] = sportsbooks

            # Reorder columns to put sportsbook after odds
            cols = picks_df.columns.tolist()
            if 'odds' in cols and 'sportsbook' in cols:
                # Remove sportsbook from current position
                cols.remove('sportsbook')
                # Insert after odds
                odds_idx = cols.index('odds')
                cols.insert(odds_idx + 1, 'sportsbook')
                picks_df = picks_df[cols]

            # Save updated file
            picks_df.to_csv(picks_file, index=False)

            dk_count = sum(1 for s in sportsbooks if s == 'DraftKings')
            fd_count = sum(1 for s in sportsbooks if s == 'FanDuel')

            print(f"✅ {date_str}: Added sportsbook data (DK: {dk_count}, FD: {fd_count})")
            updated_count += 1

        except Exception as e:
            print(f"❌ Error processing {picks_file}: {e}")
            continue

    print(f"\n✅ Updated {updated_count} picks files with sportsbook information")
    return updated_count

if __name__ == "__main__":
    add_sportsbook_column_to_picks()
