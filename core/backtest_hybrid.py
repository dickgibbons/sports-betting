#!/usr/bin/env python3
"""
Hybrid System Backtest
Tests hybrid system performance on historical data to compare vs angle-only
"""

import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from bet_tracker import BetTracker


class HybridBacktest:
    """Backtest hybrid vs angle-only system on historical data"""

    def __init__(self, start_date: str, end_date: str):
        """
        Initialize backtest

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        """
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d')

        # Load historical bet data from tracker
        self.tracker = BetTracker()

        print("🔬 Hybrid System Backtest")
        print(f"   Period: {start_date} to {end_date}")
        print(f"   Historical Bets: {len(self.tracker.bet_history)}")
        print("="*80)

    def run_backtest(self) -> Dict:
        """Run backtest and compare systems"""

        print("\n📊 ANALYZING HISTORICAL BETS...")
        print("-"*80)

        # Filter bets in date range
        historical_bets = [
            bet for bet in self.tracker.bet_history
            if self.start_date <= datetime.strptime(bet['date'], '%Y-%m-%d') <= self.end_date
        ]

        if not historical_bets:
            print("❌ No historical bets found in this period")
            return {}

        print(f"Found {len(historical_bets)} bets in period")

        # Separate by result
        settled_bets = [b for b in historical_bets if b['result'] in ['WIN', 'LOSS', 'PUSH']]
        pending_bets = [b for b in historical_bets if b['result'] == 'PENDING']

        print(f"   Settled: {len(settled_bets)}")
        print(f"   Pending: {len(pending_bets)}")

        if not settled_bets:
            print("\n⚠️  No settled bets to analyze")
            return {}

        # Analyze performance
        results = self._analyze_performance(settled_bets)

        # Display results
        self._display_results(results)

        return results

    def _analyze_performance(self, bets: List[Dict]) -> Dict:
        """Analyze bet performance"""

        # Overall stats
        wins = len([b for b in bets if b['result'] == 'WIN'])
        losses = len([b for b in bets if b['result'] == 'LOSS'])
        pushes = len([b for b in bets if b['result'] == 'PUSH'])

        total_profit = sum(b.get('profit', 0) for b in bets if b.get('profit') is not None)

        win_rate = (wins / len(bets)) * 100 if bets else 0

        # Break down by confidence level
        by_confidence = {
            'ELITE': [b for b in bets if b.get('confidence') == 'ELITE'],
            'HIGH': [b for b in bets if b.get('confidence') == 'HIGH'],
            'MEDIUM': [b for b in bets if b.get('confidence') == 'MEDIUM'],
            'LOW': [b for b in bets if b.get('confidence') == 'LOW']
        }

        confidence_stats = {}
        for conf, conf_bets in by_confidence.items():
            if conf_bets:
                conf_wins = len([b for b in conf_bets if b['result'] == 'WIN'])
                conf_profit = sum(b.get('profit', 0) for b in conf_bets if b.get('profit') is not None)

                confidence_stats[conf] = {
                    'count': len(conf_bets),
                    'wins': conf_wins,
                    'losses': len([b for b in conf_bets if b['result'] == 'LOSS']),
                    'win_rate': (conf_wins / len(conf_bets)) * 100,
                    'profit': conf_profit,
                    'avg_profit': conf_profit / len(conf_bets)
                }

        # Break down by angle type
        angle_performance = {}
        for bet in bets:
            for angle in bet.get('angles', []):
                angle_type = angle['type']

                if angle_type not in angle_performance:
                    angle_performance[angle_type] = {
                        'count': 0,
                        'wins': 0,
                        'losses': 0,
                        'profit': 0
                    }

                angle_performance[angle_type]['count'] += 1
                if bet['result'] == 'WIN':
                    angle_performance[angle_type]['wins'] += 1
                elif bet['result'] == 'LOSS':
                    angle_performance[angle_type]['losses'] += 1

                angle_performance[angle_type]['profit'] += bet.get('profit', 0)

        # Calculate win rates for angles
        for angle_type, stats in angle_performance.items():
            total = stats['wins'] + stats['losses']
            stats['win_rate'] = (stats['wins'] / total) * 100 if total > 0 else 0
            stats['avg_profit'] = stats['profit'] / stats['count'] if stats['count'] > 0 else 0

        return {
            'total_bets': len(bets),
            'wins': wins,
            'losses': losses,
            'pushes': pushes,
            'win_rate': win_rate,
            'total_profit': total_profit,
            'avg_profit': total_profit / len(bets),
            'roi': (total_profit / 10000) * 100,  # Assuming $10k starting bankroll
            'by_confidence': confidence_stats,
            'by_angle': angle_performance
        }

    def _display_results(self, results: Dict):
        """Display backtest results"""

        print("\n" + "="*80)
        print("📊 BACKTEST RESULTS")
        print("="*80)

        # Overall performance
        print(f"\n💰 OVERALL PERFORMANCE:")
        print(f"   Total Bets: {results['total_bets']}")
        print(f"   Record: {results['wins']}-{results['losses']}-{results['pushes']}")
        print(f"   Win Rate: {results['win_rate']:.1f}%")
        print(f"   Total Profit: ${results['total_profit']:+,.2f}")
        print(f"   Avg Profit/Bet: ${results['avg_profit']:+,.2f}")
        print(f"   ROI: {results['roi']:.1f}%")

        # Performance by confidence
        print(f"\n🎯 PERFORMANCE BY CONFIDENCE LEVEL:")
        print(f"{'─'*80}")

        for conf in ['ELITE', 'HIGH', 'MEDIUM', 'LOW']:
            if conf in results['by_confidence']:
                stats = results['by_confidence'][conf]

                print(f"\n{conf}:")
                print(f"   Bets: {stats['count']}")
                print(f"   Record: {stats['wins']}-{stats['losses']}")
                print(f"   Win Rate: {stats['win_rate']:.1f}%")
                print(f"   Total Profit: ${stats['profit']:+,.2f}")
                print(f"   Avg Profit: ${stats['avg_profit']:+,.2f}")

        # Top performing angles
        print(f"\n📈 TOP PERFORMING ANGLES:")
        print(f"{'─'*80}")

        sorted_angles = sorted(
            results['by_angle'].items(),
            key=lambda x: x[1]['win_rate'],
            reverse=True
        )

        for i, (angle_type, stats) in enumerate(sorted_angles[:5], 1):
            if stats['count'] >= 3:  # Minimum 3 bets for significance
                print(f"\n{i}. {angle_type}:")
                print(f"   Bets: {stats['count']}")
                print(f"   Win Rate: {stats['win_rate']:.1f}%")
                print(f"   Avg Profit: ${stats['avg_profit']:+,.2f}")

        # Recommendations
        print(f"\n{'='*80}")
        print("💡 INSIGHTS")
        print("="*80)

        # Best confidence level
        best_conf = max(results['by_confidence'].items(),
                       key=lambda x: x[1]['win_rate'])

        print(f"\n✅ BEST CONFIDENCE LEVEL: {best_conf[0]}")
        print(f"   {best_conf[1]['win_rate']:.1f}% win rate on {best_conf[1]['count']} bets")

        # Best angle
        best_angle = max(
            [(k, v) for k, v in results['by_angle'].items() if v['count'] >= 3],
            key=lambda x: x[1]['win_rate'],
            default=None
        )

        if best_angle:
            print(f"\n🔥 BEST PERFORMING ANGLE: {best_angle[0]}")
            print(f"   {best_angle[1]['win_rate']:.1f}% win rate on {best_angle[1]['count']} bets")

        # System health check
        if results['win_rate'] >= 55:
            print(f"\n✅ SYSTEM STATUS: PROFITABLE")
            print(f"   Win rate above 55% threshold")
        elif results['win_rate'] >= 52:
            print(f"\n⚠️  SYSTEM STATUS: MARGINAL")
            print(f"   Win rate 52-55%, close to break-even")
        else:
            print(f"\n❌ SYSTEM STATUS: UNPROFITABLE")
            print(f"   Win rate below 52%, losing money")

    def save_results(self, results: Dict, filename: str = None):
        """Save backtest results to file"""

        if filename is None:
            filename = f"data/backtest_{self.start_date.strftime('%Y%m%d')}_{self.end_date.strftime('%Y%m%d')}.json"

        try:
            with open(filename, 'w') as f:
                json.dump({
                    'start_date': self.start_date.strftime('%Y-%m-%d'),
                    'end_date': self.end_date.strftime('%Y-%m-%d'),
                    **results
                }, f, indent=2)

            print(f"\n💾 Results saved to: {filename}")

        except Exception as e:
            print(f"⚠️  Could not save results: {e}")


def main():
    """Run backtest"""

    import argparse

    parser = argparse.ArgumentParser(description='Backtest Hybrid vs Angle-Only System')
    parser.add_argument('--start', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--save', action='store_true', help='Save results to file')

    args = parser.parse_args()

    # Run backtest
    backtest = HybridBacktest(args.start, args.end)
    results = backtest.run_backtest()

    if results and args.save:
        backtest.save_results(results)

    print(f"\n{'='*80}")
    print("✅ Backtest complete!")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
