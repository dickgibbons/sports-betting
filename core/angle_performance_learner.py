#!/usr/bin/env python3
"""
Angle Performance Learner - SELF-LEARNING SYSTEM
Analyzes bet results and automatically adjusts angle weights
"""

import json
import os
from collections import defaultdict
from typing import Dict, List
from bet_tracker import BetTracker


class AnglePerformanceLearner:
    """Learn from actual bet performance and adjust angle weights"""

    def __init__(self):
        self.tracker = BetTracker()
        self.angle_weights_file = '/Users/dickgibbons/AI Projects/sports-betting/data/angle_weights.json'
        self.angle_weights = self._load_weights()

        print("🧠 Angle Performance Learner initialized")

    def _load_weights(self) -> Dict:
        """Load current angle weights"""
        if os.path.exists(self.angle_weights_file):
            with open(self.angle_weights_file, 'r') as f:
                return json.load(f)

        # Initialize with default weights (1.0 = neutral)
        return {
            'back_to_back': 1.0,
            'three_in_four': 1.0,
            'rest_advantage': 1.0,
            'road_trip_fatigue': 1.0,
            'timezone_travel': 1.0,
            'altitude_advantage': 1.0
        }

    def _save_weights(self):
        """Save updated angle weights"""
        os.makedirs(os.path.dirname(self.angle_weights_file), exist_ok=True)
        with open(self.angle_weights_file, 'w') as f:
            json.dump(self.angle_weights, f, indent=2)

    def analyze_and_adjust(self):
        """Analyze bet performance and adjust angle weights"""

        print(f"\n{'='*80}")
        print(f"🧠 ANALYZING ANGLE PERFORMANCE")
        print(f"{'='*80}\n")

        # Get settled bets
        settled = [b for b in self.tracker.bet_history
                   if b['result'] in ['WIN', 'LOSS']]

        if len(settled) < 20:
            print(f"⚠️  Only {len(settled)} settled bets. Need 20+ for reliable adjustments.")
            print(f"   Current system will track performance but not adjust weights yet.\n")
            self._display_angle_performance()
            return

        # Group bets by angle
        angle_performance = defaultdict(lambda: {
            'wins': 0, 'losses': 0, 'profit': 0, 'count': 0
        })

        for bet in settled:
            angles = bet.get('angles', [])
            result = bet['result']
            profit = bet.get('profit', 0)

            for angle in angles:
                angle_type = angle.get('type', '')

                angle_performance[angle_type]['count'] += 1

                if result == 'WIN':
                    angle_performance[angle_type]['wins'] += 1
                elif result == 'LOSS':
                    angle_performance[angle_type]['losses'] += 1

                angle_performance[angle_type]['profit'] += profit

        # Calculate performance and adjust weights
        adjustments_made = []

        for angle_type, stats in angle_performance.items():
            if stats['count'] < 10:  # Need minimum sample
                continue

            win_rate = (stats['wins'] / stats['count']) * 100
            avg_profit = stats['profit'] / stats['count']

            current_weight = self.angle_weights.get(angle_type, 1.0)

            # Determine if angle is over/underperforming
            if win_rate >= 65 and avg_profit > 0:
                # Strong performer - increase weight
                new_weight = min(current_weight * 1.15, 1.5)  # Cap at 1.5x
                adjustment = "INCREASE"
            elif win_rate >= 55 and avg_profit > 0:
                # Good performer - slight increase
                new_weight = min(current_weight * 1.05, 1.3)
                adjustment = "SLIGHT INCREASE"
            elif win_rate <= 45 or avg_profit < 0:
                # Underperformer - decrease weight
                new_weight = max(current_weight * 0.85, 0.5)  # Floor at 0.5x
                adjustment = "DECREASE"
            elif win_rate <= 35:
                # Poor performer - significant decrease
                new_weight = max(current_weight * 0.7, 0.3)  # Floor at 0.3x
                adjustment = "MAJOR DECREASE"
            else:
                # Neutral - no change
                new_weight = current_weight
                adjustment = "NO CHANGE"

            if new_weight != current_weight:
                self.angle_weights[angle_type] = round(new_weight, 3)
                adjustments_made.append({
                    'angle': angle_type,
                    'old_weight': current_weight,
                    'new_weight': new_weight,
                    'adjustment': adjustment,
                    'win_rate': win_rate,
                    'avg_profit': avg_profit,
                    'sample': stats['count']
                })

        # Display results
        self._display_adjustments(adjustments_made)

        # Save updated weights
        if adjustments_made:
            self._save_weights()
            print(f"\n✅ Updated angle weights saved to: {self.angle_weights_file}")
            print(f"   These will be used in tomorrow's betting recommendations")

    def _display_angle_performance(self):
        """Display current angle performance without adjusting"""

        settled = [b for b in self.tracker.bet_history
                   if b['result'] in ['WIN', 'LOSS']]

        angle_performance = defaultdict(lambda: {
            'wins': 0, 'losses': 0, 'profit': 0, 'count': 0
        })

        for bet in settled:
            angles = bet.get('angles', [])
            result = bet['result']
            profit = bet.get('profit', 0)

            for angle in angles:
                angle_type = angle.get('type', '')
                angle_performance[angle_type]['count'] += 1

                if result == 'WIN':
                    angle_performance[angle_type]['wins'] += 1
                elif result == 'LOSS':
                    angle_performance[angle_type]['losses'] += 1

                angle_performance[angle_type]['profit'] += profit

        print(f"📊 ANGLE PERFORMANCE (tracking, not adjusting yet):")
        print(f"{'─'*80}\n")

        for angle_type, stats in sorted(angle_performance.items(),
                                       key=lambda x: x[1]['count'],
                                       reverse=True):
            if stats['count'] == 0:
                continue

            win_rate = (stats['wins'] / stats['count']) * 100
            avg_profit = stats['profit'] / stats['count']
            current_weight = self.angle_weights.get(angle_type, 1.0)

            print(f"{angle_type.replace('_', ' ').title()}:")
            print(f"  Record: {stats['wins']}-{stats['losses']} ({win_rate:.1f}% win rate)")
            print(f"  Avg Profit: ${avg_profit:+.2f}")
            print(f"  Sample: {stats['count']} bets")
            print(f"  Current Weight: {current_weight:.2f}x")
            print()

    def _display_adjustments(self, adjustments: List[Dict]):
        """Display weight adjustments"""

        if not adjustments:
            print(f"✅ All angles performing as expected - no adjustments needed\n")
            return

        print(f"\n{'='*80}")
        print(f"🔧 ANGLE WEIGHT ADJUSTMENTS")
        print(f"{'='*80}\n")

        for adj in adjustments:
            symbol = "⬆️" if "INCREASE" in adj['adjustment'] else "⬇️"

            print(f"{symbol} {adj['angle'].replace('_', ' ').title()}: "
                  f"{adj['old_weight']:.2f}x → {adj['new_weight']:.2f}x")
            print(f"   Reason: {adj['adjustment']}")
            print(f"   Performance: {adj['win_rate']:.1f}% win rate, "
                  f"${adj['avg_profit']:+.2f} avg profit ({adj['sample']} bets)")
            print()

    def get_adjusted_edge(self, angle_type: str, base_edge: float) -> float:
        """Get adjusted edge based on learned weights"""
        weight = self.angle_weights.get(angle_type, 1.0)
        return base_edge * weight

    def generate_recommendations_report(self):
        """Generate report on which angles to trust more/less"""

        print(f"\n{'='*80}")
        print(f"💡 BETTING RECOMMENDATIONS BASED ON LEARNING")
        print(f"{'='*80}\n")

        high_trust = []
        medium_trust = []
        low_trust = []

        for angle_type, weight in self.angle_weights.items():
            if weight >= 1.2:
                high_trust.append((angle_type, weight))
            elif weight >= 0.9:
                medium_trust.append((angle_type, weight))
            else:
                low_trust.append((angle_type, weight))

        if high_trust:
            print(f"✅ HIGH TRUST ANGLES (weight ≥1.2x):")
            for angle, weight in sorted(high_trust, key=lambda x: x[1], reverse=True):
                print(f"   • {angle.replace('_', ' ').title()}: {weight:.2f}x")
            print()

        if medium_trust:
            print(f"💡 MEDIUM TRUST ANGLES (weight 0.9-1.2x):")
            for angle, weight in sorted(medium_trust, key=lambda x: x[1], reverse=True):
                print(f"   • {angle.replace('_', ' ').title()}: {weight:.2f}x")
            print()

        if low_trust:
            print(f"⚠️  LOW TRUST ANGLES (weight <0.9x):")
            for angle, weight in sorted(low_trust, key=lambda x: x[1], reverse=True):
                print(f"   • {angle.replace('_', ' ').title()}: {weight:.2f}x")
            print(f"\n   → Consider reducing stake or skipping these angles")
            print()


def main():
    learner = AnglePerformanceLearner()
    learner.analyze_and_adjust()
    learner.generate_recommendations_report()


if __name__ == "__main__":
    main()
