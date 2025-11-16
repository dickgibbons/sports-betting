#!/usr/bin/env python3
"""
Performance Analyzer - Identify what's working and what needs improvement
"""

import json
from collections import defaultdict
from typing import Dict, List

def analyze_betting_performance():
    """Analyze betting performance by sport, angle, and confidence level"""

    # Load betting history
    with open('/Users/dickgibbons/sports-betting/data/bet_history.json', 'r') as f:
        bets = json.load(f)

    # Filter completed bets only
    completed_bets = [b for b in bets if b['result'] in ['WIN', 'LOSS']]

    print("="*80)
    print("BETTING PERFORMANCE ANALYSIS")
    print("="*80)
    print(f"\nTotal Bets Tracked: {len(bets)}")
    print(f"Completed Bets: {len(completed_bets)}")
    print(f"Pending Bets: {len([b for b in bets if b['result'] == 'PENDING'])}")

    # Overall stats
    wins = len([b for b in completed_bets if b['result'] == 'WIN'])
    losses = len([b for b in completed_bets if b['result'] == 'LOSS'])
    total_profit = sum([b['profit'] for b in completed_bets if b['profit'] is not None])

    print(f"\n{'='*80}")
    print("OVERALL PERFORMANCE")
    print("="*80)
    print(f"Record: {wins}-{losses}")
    print(f"Win Rate: {wins/len(completed_bets)*100:.1f}%")
    print(f"Total Profit/Loss: ${total_profit:,.2f}")
    print(f"Average Profit per Bet: ${total_profit/len(completed_bets):.2f}")
    print(f"ROI: {(total_profit/10000)*100:.1f}%")

    # Performance by sport
    print(f"\n{'='*80}")
    print("PERFORMANCE BY SPORT")
    print("="*80)

    by_sport = defaultdict(lambda: {'wins': 0, 'losses': 0, 'profit': 0, 'bets': []})

    for bet in completed_bets:
        sport = bet['sport']
        by_sport[sport]['bets'].append(bet)
        if bet['result'] == 'WIN':
            by_sport[sport]['wins'] += 1
        else:
            by_sport[sport]['losses'] += 1
        by_sport[sport]['profit'] += bet['profit']

    for sport in sorted(by_sport.keys()):
        data = by_sport[sport]
        total = data['wins'] + data['losses']
        win_rate = data['wins'] / total * 100 if total > 0 else 0
        avg_profit = data['profit'] / total if total > 0 else 0

        print(f"\n{sport}:")
        print(f"  Record: {data['wins']}-{data['losses']} ({win_rate:.1f}% win rate)")
        print(f"  Profit: ${data['profit']:,.2f}")
        print(f"  Avg per bet: ${avg_profit:.2f}")
        print(f"  Status: {'✅ PROFITABLE' if data['profit'] > 0 else '❌ LOSING'}")

    # Performance by confidence level
    print(f"\n{'='*80}")
    print("PERFORMANCE BY CONFIDENCE LEVEL")
    print("="*80)

    by_confidence = defaultdict(lambda: {'wins': 0, 'losses': 0, 'profit': 0, 'bets': []})

    for bet in completed_bets:
        conf = bet['confidence']
        by_confidence[conf]['bets'].append(bet)
        if bet['result'] == 'WIN':
            by_confidence[conf]['wins'] += 1
        else:
            by_confidence[conf]['losses'] += 1
        by_confidence[conf]['profit'] += bet['profit']

    for conf in ['ELITE', 'HIGH', 'MEDIUM', 'LOW']:
        if conf in by_confidence:
            data = by_confidence[conf]
            total = data['wins'] + data['losses']
            win_rate = data['wins'] / total * 100 if total > 0 else 0
            avg_profit = data['profit'] / total if total > 0 else 0

            print(f"\n{conf}:")
            print(f"  Record: {data['wins']}-{data['losses']} ({win_rate:.1f}% win rate)")
            print(f"  Total bets: {total}")
            print(f"  Profit: ${data['profit']:,.2f}")
            print(f"  Avg per bet: ${avg_profit:.2f}")
            print(f"  Status: {'✅ PROFITABLE' if data['profit'] > 0 else '❌ LOSING'}")

    # Performance by angle type
    print(f"\n{'='*80}")
    print("PERFORMANCE BY ANGLE TYPE")
    print("="*80)

    by_angle = defaultdict(lambda: {'wins': 0, 'losses': 0, 'profit': 0, 'count': 0})

    for bet in completed_bets:
        for angle in bet.get('angles', []):
            angle_type = angle['type']
            by_angle[angle_type]['count'] += 1
            if bet['result'] == 'WIN':
                by_angle[angle_type]['wins'] += 1
            else:
                by_angle[angle_type]['losses'] += 1
            by_angle[angle_type]['profit'] += bet['profit'] / len(bet['angles'])  # Split profit

    # Sort by profitability
    sorted_angles = sorted(by_angle.items(), key=lambda x: x[1]['profit'], reverse=True)

    for angle_type, data in sorted_angles:
        total = data['wins'] + data['losses']
        win_rate = data['wins'] / total * 100 if total > 0 else 0
        avg_profit = data['profit'] / data['count'] if data['count'] > 0 else 0

        status = '✅' if data['profit'] > 0 else '❌'

        print(f"\n{status} {angle_type}:")
        print(f"  Record: {data['wins']}-{data['losses']} ({win_rate:.1f}% win rate)")
        print(f"  Appeared in: {data['count']} bets")
        print(f"  Profit: ${data['profit']:,.2f}")
        print(f"  Avg per bet: ${avg_profit:.2f}")

    # Identify biggest issues
    print(f"\n{'='*80}")
    print("KEY FINDINGS & RECOMMENDATIONS")
    print("="*80)

    findings = []

    # Check win rate
    overall_win_rate = wins / len(completed_bets) * 100
    if overall_win_rate < 50:
        findings.append(f"❌ Win rate ({overall_win_rate:.1f}%) is below break-even. Need {50 - overall_win_rate:.1f}% improvement.")

    # Check profitability by confidence
    if 'ELITE' in by_confidence and by_confidence['ELITE']['profit'] < 0:
        findings.append(f"❌ ELITE confidence bets are losing money (${by_confidence['ELITE']['profit']:.2f})")
        findings.append("   → ELITE angles may be overvalued. Consider stricter filters.")

    # Check by sport
    for sport, data in by_sport.items():
        if data['profit'] < 0:
            findings.append(f"❌ {sport} is unprofitable (${data['profit']:.2f}, {data['wins']}-{data['losses']})")

    # Check worst performing angles
    worst_angles = [(k, v) for k, v in by_angle.items() if v['profit'] < -50]
    for angle, data in worst_angles:
        findings.append(f"❌ '{angle}' angle is losing ${abs(data['profit']):.2f} ({data['wins']}-{data['losses']})")

    # Print findings
    if findings:
        print("\n🚨 ISSUES IDENTIFIED:\n")
        for finding in findings:
            print(f"  {finding}")

    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:\n")

    print("1. IMMEDIATE ACTIONS:")
    print("   • System already auto-adjusted angle weights (Road Trip, Three in Four)")
    print("   • Consider increasing minimum edge threshold from 4% to 6%")
    print("   • Focus on profitable angles: back_to_back, rest_advantage")

    print("\n2. BET SELECTION IMPROVEMENTS:")
    print("   • Be more selective with ELITE confidence bets")
    print("   • Reduce stake size on underperforming sports")
    print("   • Require multiple profitable angles (not just 1 angle)")

    print("\n3. ADD MACHINE LEARNING:")
    print("   • Complete NBA ML integration (69% accuracy)")
    print("   • Implement Soccer ML system (in progress)")
    print("   • Use ML to validate angle-based picks")

    print("\n4. RISK MANAGEMENT:")
    print("   • Consider reducing max stake from 2.5% to 2.0%")
    print("   • Implement stop-loss (pause if down 15%)")
    print("   • Track variance and adjust for hot/cold streaks")

    print("\n5. DATA-DRIVEN OPTIMIZATION:")
    print("   • Backtest all angles over 2+ seasons")
    print("   • Compare actual results to expected edge")
    print("   • Eliminate angles with <45% win rate")

    print("\n"+"="*80)


if __name__ == "__main__":
    analyze_betting_performance()
