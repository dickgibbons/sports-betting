#!/usr/bin/env python3
"""
NHL Top 5 Best Bets Daily Report
Extracts and highlights the top 5 best betting opportunities from daily predictions
"""

import pandas as pd
import argparse
from datetime import datetime
import sys


class Top5BestBets:
    """Generate top 5 best bets report"""

    def __init__(self):
        pass

    def generate_top5(self, date_str: str = None) -> pd.DataFrame:
        """Generate top 5 best bets from bet recommendations"""

        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')

        filename = f"bet_recommendations_{date_str}.csv"

        try:
            # Read bet recommendations
            df = pd.read_csv(filename)

            if df.empty:
                print(f"⚠️  No recommendations found for {date_str}")
                return pd.DataFrame()

            # Parse edge percentage to numeric
            df['Edge_Numeric'] = df['Edge'].str.replace('%', '').str.replace('+', '').astype(float)

            # Sort by edge (highest first)
            df_sorted = df.sort_values('Edge_Numeric', ascending=False)

            # Get top 5
            top5 = df_sorted.head(5).copy()

            # Add rank
            top5.insert(0, 'Rank', range(1, len(top5) + 1))

            return top5

        except FileNotFoundError:
            print(f"❌ Bet recommendations file not found: {filename}")
            return pd.DataFrame()
        except Exception as e:
            print(f"❌ Error reading recommendations: {e}")
            return pd.DataFrame()

    def save_report(self, df: pd.DataFrame, date_str: str = None):
        """Save and display top 5 report"""

        if df.empty:
            print("No data to save")
            return

        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')

        # Create date-based folder structure: reports/YYYYMMDD/
        import os
        date_folder = date_str.replace('-', '')  # Convert 2025-10-17 to 20251017
        reports_dir = os.path.join('reports', date_folder)
        os.makedirs(reports_dir, exist_ok=True)

        filename = os.path.join(reports_dir, f"top5_best_bets_{date_str}.csv")

        # Save to CSV
        df.to_csv(filename, index=False)
        print(f"\n✅ Top 5 Best Bets saved to: {filename}")

        # Display formatted report
        print("\n" + "=" * 100)
        print("🏆 TOP 5 BEST BETS OF THE DAY")
        print("=" * 100)
        print(f"📅 Date: {date_str}")
        print("=" * 100)

        for idx, row in df.iterrows():
            rank = row['Rank']
            game = row['Game']
            bet_type = row['Bet_Type']
            pick = row['Pick']
            odds = row['Odds']
            confidence = row['Confidence']
            edge = row['Edge']
            units = row['Recommended_Unit']

            # Emoji based on rank
            emoji = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣'][rank-1]

            print(f"\n{emoji} PICK #{rank}")
            print(f"   Game: {game}")
            print(f"   Bet: {bet_type} - {pick}")
            print(f"   Odds: {odds}")
            print(f"   Edge: {edge} | Confidence: {confidence}")
            print(f"   Stake: {units}")

        print("\n" + "=" * 100)
        print(f"📊 {len(df)} high-value betting opportunities identified")
        print("=" * 100)


def main():
    parser = argparse.ArgumentParser(description='Generate top 5 best bets report')
    parser.add_argument('--date', type=str,
                       help='Date in YYYY-MM-DD format (default: today)')

    args = parser.parse_args()

    print("🏒 NHL TOP 5 BEST BETS")
    print("=" * 100)

    generator = Top5BestBets()
    df_top5 = generator.generate_top5(args.date)

    if not df_top5.empty:
        generator.save_report(df_top5, args.date)
    else:
        print("\n⚠️  No top picks available")


if __name__ == "__main__":
    main()
