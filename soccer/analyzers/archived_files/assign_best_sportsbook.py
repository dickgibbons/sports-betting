#!/usr/bin/env python3
"""
Assign Best Sportsbook to Picks
Uses us_sportsbooks_comparison data to determine which sportsbook (DK or FD) has better odds
"""

import pandas as pd
import glob
import os
from datetime import datetime

def find_best_sportsbook(home, away, market, sportsbooks_df):
    """Find which sportsbook has the best odds for a given match/market"""

    # Normalize team names for matching
    home_lower = home.lower().strip()
    away_lower = away.lower().strip()
    market_lower = market.lower().strip()

    # Try exact match first
    match = sportsbooks_df[
        (sportsbooks_df['home_team'].str.lower().str.strip() == home_lower) &
        (sportsbooks_df['away_team'].str.lower().str.strip() == away_lower)
    ]

    # If no exact match, try partial
    if match.empty:
        home_first = home.split()[0] if home else ""
        away_first = away.split()[0] if away else ""

        match = sportsbooks_df[
            (sportsbooks_df['home_team'].str.contains(home_first, case=False, na=False, regex=False)) &
            (sportsbooks_df['away_team'].str.contains(away_first, case=False, na=False, regex=False))
        ]

    if match.empty:
        return 'DraftKings'  # Default

    row = match.iloc[0]

    # Determine market type and get better sportsbook
    if 'over' in market_lower and '2.5' in market_lower:
        better = row.get('over_2.5_better', 'DraftKings')
    elif 'under' in market_lower and '2.5' in market_lower:
        better = row.get('under_2.5_better', 'DraftKings')
    elif 'home' in market_lower and 'over' not in market_lower and 'under' not in market_lower:
        better = row.get('home_better', 'DraftKings')
    elif 'away' in market_lower and 'over' not in market_lower and 'under' not in market_lower:
        better = row.get('away_better', 'DraftKings')
    elif 'draw' in market_lower:
        better = row.get('draw_better', 'DraftKings')
    else:
        # For other markets (corners, BTTS, etc), default to home/away based on team
        better = row.get('home_better', 'DraftKings')

    # Convert 'Equal' to DraftKings
    if better == 'Equal' or pd.isna(better):
        better = 'DraftKings'

    return better

def assign_best_sportsbooks():
    """Assign best sportsbook to all picks based on comparison data"""

    print("🎯 ASSIGNING BEST SPORTSBOOK TO PICKS")
    print("=" * 50)

    # Find all daily picks with sportsbook column
    picks_files = glob.glob("output reports/daily_picks_*.csv")
    picks_files.extend(glob.glob("output reports/Older/daily_picks_*.csv"))
    picks_files.sort()

    updated_count = 0
    total_dk = 0
    total_fd = 0

    for picks_file in picks_files:
        try:
            # Extract date
            date_str = picks_file.split('_')[-1].replace('.csv', '')
            if len(date_str) != 8:
                continue

            # Load picks
            picks_df = pd.read_csv(picks_file)

            # Skip if no sportsbook column
            if 'sportsbook' not in picks_df.columns:
                continue

            # Skip "no picks" files
            if len(picks_df) > 0 and 'No picks today' in str(picks_df.iloc[0].get('home_team', '')):
                continue

            # Find sportsbooks comparison file
            sportsbooks_file = f"output reports/us_sportsbooks_comparison_{date_str}.csv"

            if not os.path.exists(sportsbooks_file):
                print(f"⚠️  {date_str}: No sportsbooks data, keeping defaults")
                continue

            # Load sportsbooks data
            sportsbooks_df = pd.read_csv(sportsbooks_file)

            if sportsbooks_df.empty:
                continue

            # Assign best sportsbook for each pick
            new_books = []
            for idx, pick in picks_df.iterrows():
                home = pick.get('home_team', '')
                away = pick.get('away_team', '')
                market = pick.get('market', '')

                best_book = find_best_sportsbook(home, away, market, sportsbooks_df)
                new_books.append(best_book)

                if best_book == 'DraftKings':
                    total_dk += 1
                else:
                    total_fd += 1

            # Update sportsbook column
            picks_df['sportsbook'] = new_books

            # Save
            picks_df.to_csv(picks_file, index=False)

            dk_count = new_books.count('DraftKings')
            fd_count = new_books.count('FanDuel')

            print(f"✅ {date_str}: DK={dk_count}, FD={fd_count}")
            updated_count += 1

        except Exception as e:
            print(f"❌ Error processing {picks_file}: {e}")
            continue

    print(f"\n📊 SUMMARY:")
    print(f"   Files updated: {updated_count}")
    print(f"   Total DraftKings picks: {total_dk}")
    print(f"   Total FanDuel picks: {total_fd}")

    if total_dk + total_fd > 0:
        dk_pct = (total_dk / (total_dk + total_fd)) * 100
        fd_pct = (total_fd / (total_dk + total_fd)) * 100
        print(f"   DraftKings: {dk_pct:.1f}%")
        print(f"   FanDuel: {fd_pct:.1f}%")

    return updated_count

if __name__ == "__main__":
    assign_best_sportsbooks()
