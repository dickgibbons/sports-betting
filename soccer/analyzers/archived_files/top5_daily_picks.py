#!/usr/bin/env python3
"""
Soccer Top 5 Best Picks Daily Report
Extracts and highlights the top 5 best betting opportunities from daily predictions
"""

import pandas as pd
from datetime import datetime
import sys


class Top5BestPicks:
    """Generate top 5 best picks report"""

    def __init__(self):
        pass

    def generate_top5(self, date_str: str = None) -> pd.DataFrame:
        """Generate top 5 best picks from daily picks"""

        if not date_str:
            date_str = datetime.now().strftime('%Y%m%d')

        filename = f"output reports/daily_picks_{date_str}.csv"

        try:
            # Read daily picks
            df = pd.read_csv(filename)

            # Check if conservative mode
            if df.empty or 'No picks today' in str(df.iloc[0].values):
                print(f"⚠️  No picks available for {date_str} (Conservative mode)")
                return pd.DataFrame()

            # If we have real picks, sort by confidence
            if 'confidence' in df.columns:
                df_sorted = df.sort_values('confidence', ascending=False)
            else:
                df_sorted = df

            # Get top 5
            top5 = df_sorted.head(5).copy()

            # Add rank
            top5.insert(0, 'Rank', range(1, len(top5) + 1))

            return top5

        except FileNotFoundError:
            print(f"❌ Daily picks file not found: {filename}")
            return pd.DataFrame()
        except Exception as e:
            print(f"❌ Error reading picks: {e}")
            return pd.DataFrame()

    def save_report(self, df: pd.DataFrame, date_str: str = None):
        """Save and display top 5 report"""

        if df.empty:
            print("No picks to save - System in conservative mode")
            return

        if not date_str:
            date_str = datetime.now().strftime('%Y%m%d')

        filename = f"output reports/top5_best_picks_{date_str}.csv"

        # Save to CSV
        df.to_csv(filename, index=False)
        print(f"\n✅ Top 5 Best Picks saved to: {filename}")

        # Display formatted report
        print("\n" + "=" * 100)
        print("⚽ TOP 5 BEST SOCCER PICKS OF THE DAY")
        print("=" * 100)
        print(f"📅 Date: {date_str}")
        print("=" * 100)

        for idx, row in df.iterrows():
            rank = row['Rank']
            home = row.get('home_team', 'Unknown')
            away = row.get('away_team', 'Unknown')
            league = row.get('league', 'Unknown')
            market = row.get('market', 'Unknown')
            odds = row.get('odds', 'N/A')
            confidence = row.get('confidence', 'N/A')
            stake = row.get('stake_pct', 'N/A')

            # Emoji based on rank
            emoji = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣'][rank-1]

            print(f"\n{emoji} PICK #{rank}")
            print(f"   Match: {home} vs {away}")
            print(f"   League: {league}")
            print(f"   Market: {market}")
            print(f"   Odds: {odds}")
            print(f"   Confidence: {confidence}")
            print(f"   Stake: {stake}")

        print("\n" + "=" * 100)
        print(f"📊 {len(df)} top picks identified")
        print("=" * 100)


def main():
    date_str = datetime.now().strftime('%Y%m%d')

    print("⚽ SOCCER TOP 5 BEST PICKS")
    print("=" * 100)

    generator = Top5BestPicks()
    df_top5 = generator.generate_top5(date_str)

    if not df_top5.empty:
        generator.save_report(df_top5, date_str)
    else:
        print("\n⚠️  No top picks available (Conservative mode or insufficient data)")


if __name__ == "__main__":
    main()
