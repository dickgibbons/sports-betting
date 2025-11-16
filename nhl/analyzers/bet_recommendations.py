#!/usr/bin/env python3
"""
NHL Bet Recommendations Generator
Creates focused report with only recommended bets based on edge thresholds
"""

import pandas as pd
import numpy as np
from datetime import datetime
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from daily_nhl_report import NHLDailyReport


class BetRecommendations:
    """Generate bet recommendations with filtering criteria"""

    def __init__(self, min_edge: float = 0.08, min_confidence: float = 0.55):
        self.min_edge = min_edge
        self.min_confidence = min_confidence
        self.reporter = NHLDailyReport()

    def generate_recommendations(self, date_str: str = None) -> pd.DataFrame:
        """Generate filtered bet recommendations"""

        # Get full daily report
        df_full = self.reporter.generate_daily_report(date_str)

        if df_full.empty:
            return pd.DataFrame()

        recommendations = []

        for idx, row in df_full.iterrows():
            # Extract numeric values
            win_confidence = float(row['Win_Confidence'].strip('%')) / 100
            win_edge = float(row['Win_Edge'].strip('%').strip('+')) / 100
            over_prob = float(row['Over_Probability'].strip('%')) / 100
            total_edge = float(row['Total_Edge'].strip('%').strip('+')) / 100

            bets_found = []

            # Check moneyline bet
            if win_edge >= self.min_edge and win_confidence >= self.min_confidence:
                bets_found.append({
                    'Game': f"{row['Away_Team']} @ {row['Home_Team']}",
                    'Date': row['Date'],
                    'Time': row['Time'],
                    'Bet_Type': 'Moneyline',
                    'Pick': row['Predicted_Winner'],
                    'Odds': row['Winner_Odds'],
                    'Confidence': row['Win_Confidence'],
                    'Edge': row['Win_Edge'],
                    'Recommended_Unit': self._calculate_units(win_edge, win_confidence),
                    'Reason': f"Strong edge ({row['Win_Edge']}) with {row['Win_Confidence']} confidence"
                })

            # Check totals bet
            if abs(total_edge) >= self.min_edge:
                over_under = 'Over' if total_edge > 0 else 'Under'
                total_odds = row.get('Over_Odds', '1.90') if total_edge > 0 else row.get('Under_Odds', '1.90')

                # Calculate confidence for the bet
                total_confidence = over_prob if total_edge > 0 else (1 - over_prob)

                # ONLY recommend if confidence meets minimum threshold
                if total_confidence >= self.min_confidence:
                    bets_found.append({
                        'Game': f"{row['Away_Team']} @ {row['Home_Team']}",
                        'Date': row['Date'],
                        'Time': row['Time'],
                        'Bet_Type': f"Total {over_under}",
                        'Pick': f"{over_under} {row['Total_Line']}",
                        'Odds': total_odds,
                        'Confidence': row['Over_Probability'] if total_edge > 0 else f"{100-float(row['Over_Probability'].strip('%')):.1f}%",
                        'Edge': f"{abs(total_edge)*100:+.1f}%",
                        'Recommended_Unit': self._calculate_units(abs(total_edge), total_confidence),
                        'Reason': f"Expected total {row['Expected_Total']} vs line {row['Total_Line']}"
                    })

            recommendations.extend(bets_found)

        if not recommendations:
            return pd.DataFrame()

        df_recs = pd.DataFrame(recommendations)

        # Sort by edge
        df_recs['Edge_Numeric'] = df_recs['Edge'].str.strip('%').str.strip('+').astype(float)
        df_recs = df_recs.sort_values('Edge_Numeric', ascending=False)
        df_recs = df_recs.drop('Edge_Numeric', axis=1)

        return df_recs

    def _calculate_units(self, edge: float, confidence: float) -> str:
        """Calculate recommended bet units using Kelly Criterion"""
        # Kelly fraction = (edge * confidence) / edge
        # Use fractional Kelly (0.25 = quarter Kelly) for safety

        kelly = edge * 0.25  # Quarter Kelly
        units = min(kelly * 10, 3)  # Cap at 3 units

        if units >= 2.5:
            return "🔥 3 Units (Strong)"
        elif units >= 1.5:
            return "⭐ 2 Units (Medium)"
        else:
            return "💡 1 Unit (Value)"

    def save_recommendations(self, df: pd.DataFrame, date_str: str = None):
        """Save recommendations to CSV"""

        if df.empty:
            print("✅ No bets meet recommendation criteria today")
            print(f"   Criteria: {self.min_edge*100:.0f}% min edge, {self.min_confidence*100:.0f}% min confidence")
            return

        if date_str:
            filename = f"bet_recommendations_{date_str}.csv"
        else:
            filename = f"bet_recommendations_{datetime.now().strftime('%Y-%m-%d')}.csv"

        df.to_csv(filename, index=False)

        print(f"\n✅ Bet Recommendations Saved: {filename}")
        print(f"📊 {len(df)} recommended bets")
        print(f"\n{'='*100}")
        print("🎯 TODAY'S BET RECOMMENDATIONS")
        print(f"{'='*100}\n")

        for idx, row in df.iterrows():
            print(f"🏒 GAME {idx+1}: {row['Game']}")
            print(f"   ⏰ {row['Date']} {row['Time']}")
            print(f"   🎲 {row['Bet_Type']}: {row['Pick']}")
            print(f"   💰 Odds: {row['Odds']} | Edge: {row['Edge']}")
            print(f"   📊 Confidence: {row['Confidence']}")
            print(f"   💵 Bet Size: {row['Recommended_Unit']}")
            print(f"   📝 {row['Reason']}")
            print()


def main():
    parser = argparse.ArgumentParser(description='Generate NHL bet recommendations')
    parser.add_argument('--date', type=str,
                       help='Date in YYYY-MM-DD format (default: today)')
    parser.add_argument('--min-edge', type=float, default=0.08,
                       help='Minimum edge threshold (default: 0.08 = 8%%)')
    parser.add_argument('--min-confidence', type=float, default=0.55,
                       help='Minimum confidence threshold (default: 0.55 = 55%%)')

    args = parser.parse_args()

    print("🏒 NHL BET RECOMMENDATIONS GENERATOR")
    print("=" * 100)
    print(f"Criteria: Min Edge {args.min_edge*100:.0f}% | Min Confidence {args.min_confidence*100:.0f}%")
    print("=" * 100)

    recommender = BetRecommendations(
        min_edge=args.min_edge,
        min_confidence=args.min_confidence
    )

    df_recommendations = recommender.generate_recommendations(args.date)
    recommender.save_recommendations(df_recommendations, args.date)


if __name__ == "__main__":
    main()
