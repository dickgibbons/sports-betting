#!/usr/bin/env python3
"""
System Comparison Tool
Runs both Angle-Only and Hybrid systems side-by-side and compares results
"""

import sys
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple
import json


class SystemComparer:
    """Compare Angle-Only vs Hybrid betting systems"""

    def __init__(self):
        """Initialize comparer"""
        self.date = datetime.now().strftime('%Y-%m-%d')
        self.angle_bets = []
        self.hybrid_bets = []

        print("🔬 System Comparison Tool")
        print(f"   Date: {self.date}")
        print("="*80)

    def run_angle_only_system(self) -> List[Dict]:
        """Run the angle-only system"""
        print("\n📊 RUNNING ANGLE-ONLY SYSTEM...")
        print("-"*80)

        try:
            # Import and run angle-only
            from daily_betting_report import DailyBettingReport

            report = DailyBettingReport(track_bets=False)  # Don't log during comparison
            bets = report.generate_daily_report()

            print(f"✅ Angle-only system found {len(bets)} bets")
            return bets

        except Exception as e:
            print(f"❌ Angle-only system error: {e}")
            return []

    def run_hybrid_system(self) -> List[Dict]:
        """Run the hybrid system"""
        print("\n🔬 RUNNING HYBRID SYSTEM...")
        print("-"*80)

        try:
            # Import and run hybrid
            from daily_hybrid_report import DailyHybridReport

            report = DailyHybridReport(use_ml=True, track_bets=False)
            bets = report.generate_daily_report()

            print(f"✅ Hybrid system found {len(bets)} bets")
            return bets

        except Exception as e:
            print(f"❌ Hybrid system error: {e}")
            return []

    def compare_bets(self, angle_bets: List[Dict], hybrid_bets: List[Dict]):
        """Compare bets from both systems"""

        print("\n" + "="*80)
        print("📊 SYSTEM COMPARISON RESULTS")
        print("="*80)

        # Find common bets (both systems agree)
        common_bets = []
        angle_only = []
        hybrid_only = []

        for angle_bet in angle_bets:
            found = False
            for hybrid_bet in hybrid_bets:
                if self._same_bet(angle_bet, hybrid_bet):
                    common_bets.append({
                        'angle': angle_bet,
                        'hybrid': hybrid_bet
                    })
                    found = True
                    break

            if not found:
                angle_only.append(angle_bet)

        for hybrid_bet in hybrid_bets:
            found = False
            for angle_bet in angle_bets:
                if self._same_bet(angle_bet, hybrid_bet):
                    found = True
                    break

            if not found:
                hybrid_only.append(hybrid_bet)

        # Display comparison
        print(f"\n📈 SUMMARY:")
        print(f"   Angle-Only System: {len(angle_bets)} total bets")
        print(f"   Hybrid System: {len(hybrid_bets)} total bets")
        print(f"   ✅ BOTH AGREE: {len(common_bets)} bets")
        print(f"   📊 Angle-Only: {len(angle_only)} unique bets")
        print(f"   🔬 Hybrid-Only: {len(hybrid_only)} unique bets")

        # Show common bets (highest confidence)
        if common_bets:
            print(f"\n{'='*80}")
            print(f"✅ BETS WHERE BOTH SYSTEMS AGREE ({len(common_bets)})")
            print(f"{'='*80}")

            for i, bet_pair in enumerate(common_bets[:5], 1):
                angle_bet = bet_pair['angle']
                hybrid_bet = bet_pair['hybrid']

                print(f"\n#{i} {angle_bet['sport']}: {angle_bet['game']}")
                print(f"   BET: {angle_bet['bet']}")
                print(f"   Angle Confidence: {angle_bet.get('confidence', 'N/A')}")
                print(f"   Angle Edge: +{angle_bet['expected_edge']:.1f}%")

                if 'hybrid_score' in hybrid_bet:
                    print(f"   Hybrid Score: {hybrid_bet['hybrid_score']:.1f}")

                if hybrid_bet.get('has_ml'):
                    agree_emoji = "✅" if hybrid_bet.get('ml_agrees') else "❌"
                    print(f"   ML Confidence: {hybrid_bet['ml_confidence']:.1f}% {agree_emoji}")

        # Show angle-only bets
        if angle_only:
            print(f"\n{'='*80}")
            print(f"📊 ANGLE-ONLY RECOMMENDATIONS ({len(angle_only)})")
            print(f"{'='*80}")
            print("(Bets that angle system likes but hybrid filtered out)")

            for i, bet in enumerate(angle_only[:3], 1):
                print(f"\n#{i} {bet['sport']}: {bet['game']}")
                print(f"   BET: {bet['bet']}")
                print(f"   Confidence: {bet.get('confidence', 'N/A')}")
                print(f"   Edge: +{bet['expected_edge']:.1f}%")

        # Show hybrid-only bets
        if hybrid_only:
            print(f"\n{'='*80}")
            print(f"🔬 HYBRID-ONLY RECOMMENDATIONS ({len(hybrid_only)})")
            print(f"{'='*80}")
            print("(Bets that hybrid system likes but angle-only filtered out)")

            for i, bet in enumerate(hybrid_only[:3], 1):
                print(f"\n#{i} {bet['sport']}: {bet['game']}")
                print(f"   BET: {bet['bet']}")
                print(f"   Confidence: {bet.get('confidence', 'N/A')}")

                if 'hybrid_score' in bet:
                    print(f"   Hybrid Score: {bet['hybrid_score']:.1f}")

                if bet.get('has_ml'):
                    print(f"   ML Confidence: {bet['ml_confidence']:.1f}%")

        # Recommendation
        print(f"\n{'='*80}")
        print("💡 RECOMMENDATION")
        print("="*80)

        if len(common_bets) >= 3:
            print("✅ HIGH AGREEMENT: Both systems agree on multiple bets")
            print("   → Consider the common bets (highest confidence)")
        elif len(angle_only) > len(hybrid_only):
            print("📊 ANGLE-HEAVY: Angle system finds more opportunities")
            print("   → Angle system may be less conservative")
        elif len(hybrid_only) > len(angle_only):
            print("🔬 HYBRID-HEAVY: Hybrid finds unique opportunities")
            print("   → ML may be identifying patterns angles miss")
        else:
            print("⚖️  BALANCED: Both systems finding similar opportunities")

        return {
            'common': len(common_bets),
            'angle_only': len(angle_only),
            'hybrid_only': len(hybrid_only),
            'agreement_rate': len(common_bets) / max(len(angle_bets), 1) * 100
        }

    def _same_bet(self, bet1: Dict, bet2: Dict) -> bool:
        """Check if two bets are the same"""
        return (bet1['game'] == bet2['game'] and
                bet1['bet'] == bet2['bet'] and
                bet1['sport'] == bet2['sport'])

    def save_comparison(self, stats: Dict):
        """Save comparison stats"""
        filename = f"data/comparison_{self.date}.json"

        try:
            with open(filename, 'w') as f:
                json.dump({
                    'date': self.date,
                    **stats
                }, f, indent=2)

            print(f"\n💾 Comparison saved to: {filename}")

        except Exception as e:
            print(f"⚠️  Could not save comparison: {e}")


def main():
    """Run system comparison"""

    comparer = SystemComparer()

    # Run both systems
    angle_bets = comparer.run_angle_only_system()
    hybrid_bets = comparer.run_hybrid_system()

    if not angle_bets and not hybrid_bets:
        print("\n❌ Both systems returned no bets")
        return

    # Compare results
    stats = comparer.compare_bets(angle_bets, hybrid_bets)

    # Save for tracking
    comparer.save_comparison(stats)

    print(f"\n{'='*80}")
    print(f"✅ Comparison complete!")
    print(f"   Agreement Rate: {stats['agreement_rate']:.1f}%")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
