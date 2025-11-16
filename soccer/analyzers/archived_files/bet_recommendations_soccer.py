#!/usr/bin/env python3
"""
Soccer Bet Recommendations
Filters high-value betting opportunities from daily report
Matches NHL bet_recommendations.py structure
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import argparse
import joblib

class SoccerBetRecommendations:
    """Filter and recommend high-value soccer bets"""

    def __init__(self, min_edge: float = 0.08, min_confidence: float = 0.55):
        self.min_edge = min_edge  # Minimum 8% edge
        self.min_confidence = min_confidence  # Minimum 55% confidence
        self.models_file = Path('soccer_ml_models.pkl')

    def load_daily_report(self, date_str: str):
        """Load daily predictions report"""

        report_file = f"soccer_daily_report_{date_str}.csv"

        if not Path(report_file).exists():
            print(f"❌ Daily report not found: {report_file}")
            print("   Run daily_soccer_report.py first")
            return None

        df = pd.read_csv(report_file)
        print(f"📊 Loaded {len(df)} matches from daily report")
        return df

    def calculate_betting_value(self, predicted_prob: float, odds: float):
        """Calculate betting edge"""

        if odds <= 1.0:
            return 0.0

        implied_prob = 1.0 / odds
        edge = (predicted_prob - implied_prob) / implied_prob

        return edge

    def find_betting_opportunities(self, df_report):
        """Find high-value betting opportunities"""

        recommendations = []

        for idx, row in df_report.iterrows():
            # Extract match info
            match = f"{row['Home_Team']} vs {row['Away_Team']}"
            kickoff = row['Kickoff']

            # Parse probabilities (remove % sign)
            home_prob = float(row['Home_Win_Prob'].strip('%')) / 100
            draw_prob = float(row['Draw_Prob'].strip('%')) / 100
            away_prob = float(row['Away_Win_Prob'].strip('%')) / 100
            over25_prob = float(row['Over_2.5_Prob'].strip('%')) / 100
            btts_prob = float(row['BTTS_Yes_Prob'].strip('%')) / 100
            corners85_prob = float(row['Over_8.5_Corners_Prob'].strip('%')) / 100
            corners105_prob = float(row['Over_10.5_Corners_Prob'].strip('%')) / 100

            # Typical odds (would come from odds API in production)
            # For now, use implied odds from probabilities
            home_odds = 1.0 / home_prob if home_prob > 0 else 5.0
            draw_odds = 1.0 / draw_prob if draw_prob > 0 else 3.5
            away_odds = 1.0 / away_prob if away_prob > 0 else 4.0
            over25_odds = 1.0 / over25_prob if over25_prob > 0 else 2.0
            btts_odds = 1.0 / btts_prob if btts_prob > 0 else 2.0
            corners85_odds = 1.0 / corners85_prob if corners85_prob > 0 else 1.8
            corners105_odds = 1.0 / corners105_prob if corners105_prob > 0 else 2.2

            # Check each market for value
            markets_to_check = [
                ('Match Result - Home', home_prob, home_odds, row['Home_Team']),
                ('Match Result - Draw', draw_prob, draw_odds, 'Draw'),
                ('Match Result - Away', away_prob, away_odds, row['Away_Team']),
                ('Over 2.5 Goals', over25_prob, over25_odds, 'Over 2.5'),
                ('BTTS Yes', btts_prob, btts_odds, 'Both Teams Score'),
                ('Over 8.5 Corners', corners85_prob, corners85_odds, 'Over 8.5 Corners'),
                ('Over 10.5 Corners', corners105_prob, corners105_odds, 'Over 10.5 Corners'),
            ]

            for market, prob, odds, pick in markets_to_check:
                # Calculate edge
                edge = self.calculate_betting_value(prob, odds)

                # Check if meets criteria
                if prob >= self.min_confidence and edge >= self.min_edge:
                    # Determine unit size
                    if edge >= 0.15 and prob >= 0.70:
                        units = 3
                        size = "🔥 3 Units (Strong)"
                    elif edge >= 0.10 and prob >= 0.60:
                        units = 2
                        size = "⭐ 2 Units (Medium)"
                    else:
                        units = 1
                        size = "💡 1 Unit (Value)"

                    recommendation = {
                        'Match': match,
                        'Kickoff': kickoff,
                        'League': row['League'],
                        'Market': market,
                        'Pick': pick,
                        'Odds': f"{odds:.2f}",
                        'Confidence': f"{prob:.1%}",
                        'Edge': f"{edge:+.1%}",
                        'Recommended_Unit': size,
                        'Units': units,
                        'Reason': f"Strong edge ({edge:+.1%}) with {prob:.1%} confidence"
                    }

                    recommendations.append(recommendation)

        return recommendations

    def generate_recommendations(self, date_str: str):
        """Generate filtered bet recommendations"""

        print(f"\n{'='*70}")
        print(f"🎯 SOCCER BET RECOMMENDATIONS - {date_str}")
        print(f"{'='*70}")
        print(f"Criteria: Min Edge {self.min_edge:.0%} | Min Confidence {self.min_confidence:.0%}")
        print(f"{'='*70}\n")

        # Load daily report
        df_report = self.load_daily_report(date_str)

        if df_report is None:
            return

        # Find betting opportunities
        recommendations = self.find_betting_opportunities(df_report)

        if not recommendations:
            print("❌ No bets meet the criteria today")
            print("   Consider lowering thresholds or waiting for better opportunities\n")

            # Save empty recommendations
            df_empty = pd.DataFrame([{
                'Date': date_str,
                'Message': 'No recommendations today',
                'Criteria': f'Min Edge {self.min_edge:.0%}, Min Confidence {self.min_confidence:.0%}'
            }])
            output_file = f"bet_recommendations_soccer_{date_str}.csv"
            df_empty.to_csv(output_file, index=False)
            return

        # Sort by edge (highest first)
        recommendations = sorted(recommendations, key=lambda x: float(x['Edge'].strip('%+')), reverse=True)

        # Create DataFrame
        df_recs = pd.DataFrame(recommendations)

        # Save to CSV
        output_file = f"bet_recommendations_soccer_{date_str}.csv"
        df_recs.to_csv(output_file, index=False)

        print(f"✅ Saved: {output_file}")
        print(f"📊 {len(df_recs)} recommended bets\n")

        # Print formatted recommendations
        self.print_recommendations(df_recs)

        return df_recs

    def print_recommendations(self, df_recs):
        """Print formatted recommendations"""

        print(f"{'='*70}")
        print("🎯 TODAY'S BET RECOMMENDATIONS")
        print(f"{'='*70}\n")

        for idx, rec in df_recs.iterrows():
            print(f"⚽ MATCH {idx+1}: {rec['Match']}")
            print(f"   ⏰ {rec['Kickoff']}")
            print(f"   🎲 {rec['Market']}: {rec['Pick']}")
            print(f"   💰 Odds: {rec['Odds']} | Edge: {rec['Edge']}")
            print(f"   📊 Confidence: {rec['Confidence']}")
            print(f"   💵 Bet Size: {rec['Recommended_Unit']}")
            print(f"   📝 {rec['Reason']}")
            print()


def main():
    parser = argparse.ArgumentParser(description='Generate soccer bet recommendations')
    parser.add_argument('--date', type=str, help='Date for recommendations (YYYY-MM-DD)')
    parser.add_argument('--min-edge', type=float, default=0.08, help='Minimum edge (default 0.08)')
    parser.add_argument('--min-confidence', type=float, default=0.55, help='Minimum confidence (default 0.55)')

    args = parser.parse_args()

    # Determine date
    if args.date:
        date_str = args.date
    else:
        date_str = datetime.now().strftime('%Y-%m-%d')

    # Generate recommendations
    recommender = SoccerBetRecommendations(
        min_edge=args.min_edge,
        min_confidence=args.min_confidence
    )

    recommender.generate_recommendations(date_str)


if __name__ == "__main__":
    main()
