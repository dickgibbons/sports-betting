#!/usr/bin/env python3
"""
Historical Data Backfill Script
Fetches historical soccer matches to build training dataset
"""

import requests
import time
from datetime import datetime, timedelta
from pathlib import Path
from update_models_with_results import SoccerModelUpdater

def backfill_historical_data(api_key: str, days_back: int = 30):
    """
    Backfill historical match data for training

    Args:
        api_key: API-Football API key
        days_back: Number of days to go back (default: 30)
    """

    print(f"\n{'='*80}")
    print(f"⚽ HISTORICAL DATA BACKFILL")
    print(f"{'='*80}")
    print(f"📅 Fetching {days_back} days of historical matches\n")

    updater = SoccerModelUpdater(api_key)

    total_matches = 0
    successful_days = 0

    # Fetch data for each day
    for days_ago in range(1, days_back + 1):
        date = datetime.now() - timedelta(days=days_ago)
        date_str = date.strftime('%Y-%m-%d')

        print(f"\n📊 Day {days_ago}/{days_back}: {date_str}")
        print("-" * 80)

        try:
            # Fetch matches for this date
            fixtures = updater.fetch_finished_matches(date_str)

            if fixtures:
                # Extract features
                new_matches = []
                for fixture in fixtures:
                    features = updater.extract_match_features(fixture)
                    if features:
                        new_matches.append(features)

                if new_matches:
                    # Update training history
                    df_history = updater.update_training_history(new_matches)
                    total_matches += len(new_matches)
                    successful_days += 1

                    print(f"   ✅ Added {len(new_matches)} matches | Total: {len(df_history)}")
            else:
                print(f"   ⚠️  No matches found")

            # Rate limiting - be respectful to API
            if days_ago < days_back:
                time.sleep(1)  # 1 second delay between requests

        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue

    print(f"\n{'='*80}")
    print(f"✅ BACKFILL COMPLETE")
    print(f"{'='*80}")
    print(f"📊 Summary:")
    print(f"   Days processed: {successful_days}/{days_back}")
    print(f"   Total matches collected: {total_matches}")
    print(f"   Training data file: {updater.training_history_file}")
    print(f"\n💡 Next step: Run model retraining")
    print(f"   Command: python3 update_models_with_results.py --full-retrain")
    print(f"{'='*80}\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Backfill historical soccer match data')
    parser.add_argument('--days', type=int, default=30, help='Number of days to backfill (default: 30)')
    parser.add_argument('--full', action='store_true', help='Do full backfill (90 days)')

    args = parser.parse_args()

    # API key
    api_key = "960c628e1c91c4b1f125e1eec52ad862"

    # Determine days to backfill
    if args.full:
        days_back = 90
        print("🚀 Full backfill mode: 90 days")
    else:
        days_back = args.days

    # Confirm with user
    print(f"\n⚠️  This will fetch approximately {days_back} days of match data")
    print(f"   Estimated API calls: ~{days_back}")
    response = input(f"\n   Continue? (y/n): ")

    if response.lower() != 'y':
        print("❌ Cancelled")
        return

    # Run backfill
    backfill_historical_data(api_key, days_back)


if __name__ == "__main__":
    main()
