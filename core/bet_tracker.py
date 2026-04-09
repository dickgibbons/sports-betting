#!/usr/bin/env python3
"""
Bet Tracker - Track all recommended bets and their outcomes
Analyzes performance by sport, bet type, confidence level, and angle
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict


class BetTracker:
    """Track betting performance and calculate statistics"""

    def __init__(self, starting_bankroll: float = 10000):
        self.data_file = '/Users/dickgibbons/AI Projects/sports-betting/data/bet_history.json'
        self.starting_bankroll = starting_bankroll
        self.current_bankroll = starting_bankroll

        # Load existing data
        self.bet_history = self._load_history()

        # Calculate current bankroll from history
        if self.bet_history:
            self._recalculate_bankroll()

        print(f"📊 Bet Tracker initialized")
        print(f"   Starting bankroll: ${self.starting_bankroll:,.2f}")
        print(f"   Current bankroll: ${self.current_bankroll:,.2f}")
        print(f"   Total bets tracked: {len(self.bet_history)}")

    def _load_history(self) -> List[Dict]:
        """Load bet history from file"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)

        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return []

    def _save_history(self):
        """Save bet history to file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.bet_history, f, indent=2)

    def _recalculate_bankroll(self):
        """Recalculate current bankroll from bet history"""
        self.current_bankroll = self.starting_bankroll

        for bet in self.bet_history:
            if bet.get('result') == 'WIN':
                profit = bet.get('profit', 0)
                self.current_bankroll += profit
            elif bet.get('result') == 'LOSS':
                loss = bet.get('stake', 0)
                self.current_bankroll -= loss

    def log_bet(self, bet: Dict) -> str:
        """Log a new bet recommendation"""

        # Check if this exact bet already exists (prevent duplicates)
        for existing_bet in self.bet_history:
            if (existing_bet['date'] == bet['date'] and
                existing_bet['game'] == bet['game'] and
                existing_bet['bet'] == bet['bet']):
                # Bet already logged, return existing ID
                return existing_bet['bet_id']

        bet_id = f"{bet['date']}_{bet['sport']}_{len(self.bet_history)}"

        bet_record = {
            'bet_id': bet_id,
            'date': bet['date'],
            'sport': bet['sport'],
            'game': bet['game'],
            'bet_type': bet['bet_type'],
            'bet': bet['bet'],
            'odds': bet.get('odds'),
            'confidence': bet['confidence'],
            'expected_edge': bet['expected_edge'],
            'true_ev': bet.get('true_ev', bet['expected_edge']),
            'angles': [{'type': a['type'], 'reason': a['reason']} for a in bet['angles']],
            'angle_count': bet['angle_count'],
            'recommended_stake_pct': self._get_stake_pct(bet['confidence']),
            'stake': None,  # Will be filled when bet is placed
            'result': 'PENDING',
            'profit': None,
            'logged_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        self.bet_history.append(bet_record)
        self._save_history()

        return bet_id

    def _get_stake_pct(self, confidence: str) -> float:
        """Get recommended stake percentage by confidence"""
        stakes = {
            'ELITE': 2.5,    # 2-3% average
            'HIGH': 1.5,     # 1-2% average
            'MEDIUM': 0.75,  # 0.5-1% average
            'LOW': 0.5
        }
        return stakes.get(confidence, 0.5)

    def update_result(self, bet_id: str, result: str, stake: float = None):
        """Update bet result (WIN, LOSS, PUSH)"""

        for bet in self.bet_history:
            if bet['bet_id'] == bet_id:
                bet['result'] = result

                # Calculate stake if not provided
                if stake is None:
                    stake_pct = bet['recommended_stake_pct']
                    stake = (self.current_bankroll * stake_pct) / 100

                bet['stake'] = stake

                # Calculate profit/loss
                if result == 'WIN':
                    odds = bet['odds']
                    if odds is None:
                        # No odds available, assume even money (conservative)
                        profit = stake
                    elif odds > 0:  # Underdog
                        profit = stake * (odds / 100)
                    else:  # Favorite
                        profit = stake * (100 / abs(odds))
                    bet['profit'] = profit

                elif result == 'LOSS':
                    bet['profit'] = -stake

                elif result == 'PUSH':
                    bet['profit'] = 0

                bet['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                self._save_history()
                self._recalculate_bankroll()

                print(f"✅ Updated {bet_id}: {result}")
                if bet['profit']:
                    print(f"   Profit/Loss: ${bet['profit']:+,.2f}")
                print(f"   New bankroll: ${self.current_bankroll:,.2f}")

                return True

        print(f"❌ Bet {bet_id} not found")
        return False

    def get_performance_summary(self) -> Dict:
        """Get overall performance statistics"""

        settled_bets = [b for b in self.bet_history if b['result'] in ['WIN', 'LOSS', 'PUSH']]

        if not settled_bets:
            return {'error': 'No settled bets yet'}

        wins = len([b for b in settled_bets if b['result'] == 'WIN'])
        losses = len([b for b in settled_bets if b['result'] == 'LOSS'])
        pushes = len([b for b in settled_bets if b['result'] == 'PUSH'])

        total_staked = sum(b.get('stake', 0) for b in settled_bets)
        total_profit = sum(b.get('profit', 0) for b in settled_bets)

        roi = (total_profit / total_staked * 100) if total_staked > 0 else 0
        win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0

        return {
            'total_bets': len(settled_bets),
            'wins': wins,
            'losses': losses,
            'pushes': pushes,
            'win_rate': win_rate,
            'total_staked': total_staked,
            'total_profit': total_profit,
            'roi': roi,
            'bankroll_growth': ((self.current_bankroll - self.starting_bankroll) / self.starting_bankroll * 100),
            'current_bankroll': self.current_bankroll,
            'pending_bets': len([b for b in self.bet_history if b['result'] == 'PENDING'])
        }

    def get_performance_by_sport(self) -> Dict:
        """Break down performance by sport"""

        by_sport = defaultdict(lambda: {'bets': [], 'wins': 0, 'losses': 0, 'profit': 0})

        for bet in self.bet_history:
            if bet['result'] in ['WIN', 'LOSS', 'PUSH']:
                sport = bet['sport']
                by_sport[sport]['bets'].append(bet)

                if bet['result'] == 'WIN':
                    by_sport[sport]['wins'] += 1
                elif bet['result'] == 'LOSS':
                    by_sport[sport]['losses'] += 1

                by_sport[sport]['profit'] += bet.get('profit', 0)

        # Calculate stats
        results = {}
        for sport, data in by_sport.items():
            total = data['wins'] + data['losses']
            win_rate = (data['wins'] / total * 100) if total > 0 else 0

            results[sport] = {
                'total_bets': len(data['bets']),
                'wins': data['wins'],
                'losses': data['losses'],
                'win_rate': win_rate,
                'profit': data['profit']
            }

        return results

    def get_performance_by_confidence(self) -> Dict:
        """Break down performance by confidence level"""

        by_confidence = defaultdict(lambda: {'bets': [], 'wins': 0, 'losses': 0, 'profit': 0})

        for bet in self.bet_history:
            if bet['result'] in ['WIN', 'LOSS', 'PUSH']:
                conf = bet['confidence']
                by_confidence[conf]['bets'].append(bet)

                if bet['result'] == 'WIN':
                    by_confidence[conf]['wins'] += 1
                elif bet['result'] == 'LOSS':
                    by_confidence[conf]['losses'] += 1

                by_confidence[conf]['profit'] += bet.get('profit', 0)

        results = {}
        for conf, data in by_confidence.items():
            total = data['wins'] + data['losses']
            win_rate = (data['wins'] / total * 100) if total > 0 else 0

            results[conf] = {
                'total_bets': len(data['bets']),
                'wins': data['wins'],
                'losses': data['losses'],
                'win_rate': win_rate,
                'profit': data['profit']
            }

        return results

    def get_performance_by_bet_type(self) -> Dict:
        """Break down performance by bet type (ML, totals, etc.)"""

        by_type = defaultdict(lambda: {'bets': [], 'wins': 0, 'losses': 0, 'profit': 0})

        for bet in self.bet_history:
            if bet['result'] in ['WIN', 'LOSS', 'PUSH']:
                bet_type = bet['bet_type']
                by_type[bet_type]['bets'].append(bet)

                if bet['result'] == 'WIN':
                    by_type[bet_type]['wins'] += 1
                elif bet['result'] == 'LOSS':
                    by_type[bet_type]['losses'] += 1

                by_type[bet_type]['profit'] += bet.get('profit', 0)

        results = {}
        for btype, data in by_type.items():
            total = data['wins'] + data['losses']
            win_rate = (data['wins'] / total * 100) if total > 0 else 0

            results[btype] = {
                'total_bets': len(data['bets']),
                'wins': data['wins'],
                'losses': data['losses'],
                'win_rate': win_rate,
                'profit': data['profit']
            }

        return results

    def display_dashboard(self):
        """Display comprehensive performance dashboard"""

        print(f"\n{'='*80}")
        print(f"📊 BETTING PERFORMANCE DASHBOARD")
        print(f"{'='*80}\n")

        # Overall summary
        summary = self.get_performance_summary()

        if 'error' in summary:
            print("⚠️  No settled bets to analyze yet\n")
            print(f"Pending bets: {summary.get('pending_bets', 0)}")
            return

        print(f"💰 OVERALL PERFORMANCE")
        print(f"{'─'*80}")
        print(f"Starting Bankroll:  ${self.starting_bankroll:>12,.2f}")
        print(f"Current Bankroll:   ${summary['current_bankroll']:>12,.2f}")
        print(f"Total Profit:       ${summary['total_profit']:>12,.2f}")
        print(f"Bankroll Growth:    {summary['bankroll_growth']:>12.1f}%")
        print(f"\nRecord:             {summary['wins']}-{summary['losses']}-{summary['pushes']}")
        print(f"Win Rate:           {summary['win_rate']:>12.1f}%")
        print(f"ROI:                {summary['roi']:>12.1f}%")
        print(f"Total Staked:       ${summary['total_staked']:>12,.2f}")
        print(f"Pending Bets:       {summary['pending_bets']:>12}")

        # By Sport
        print(f"\n{'='*80}")
        print(f"🏒🏀⚽ PERFORMANCE BY SPORT")
        print(f"{'='*80}")

        by_sport = self.get_performance_by_sport()
        for sport, stats in sorted(by_sport.items()):
            print(f"\n{sport}:")
            print(f"  Record: {stats['wins']}-{stats['losses']} ({stats['win_rate']:.1f}% win rate)")
            print(f"  Profit: ${stats['profit']:+,.2f}")

        # By Confidence
        print(f"\n{'='*80}")
        print(f"🔥 PERFORMANCE BY CONFIDENCE LEVEL")
        print(f"{'='*80}")

        by_conf = self.get_performance_by_confidence()
        for conf in ['ELITE', 'HIGH', 'MEDIUM', 'LOW']:
            if conf in by_conf:
                stats = by_conf[conf]
                marker = {'ELITE': '🔥', 'HIGH': '✅', 'MEDIUM': '💡', 'LOW': '⚪'}[conf]
                print(f"\n{marker} {conf}:")
                print(f"  Record: {stats['wins']}-{stats['losses']} ({stats['win_rate']:.1f}% win rate)")
                print(f"  Profit: ${stats['profit']:+,.2f}")

        # By Bet Type
        print(f"\n{'='*80}")
        print(f"🎯 PERFORMANCE BY BET TYPE")
        print(f"{'='*80}")

        by_type = self.get_performance_by_bet_type()
        for bet_type, stats in sorted(by_type.items()):
            print(f"\n{bet_type}:")
            print(f"  Record: {stats['wins']}-{stats['losses']} ({stats['win_rate']:.1f}% win rate)")
            print(f"  Profit: ${stats['profit']:+,.2f}")

        print(f"\n{'='*80}\n")

    def list_pending_bets(self):
        """List all pending bets"""

        pending = [b for b in self.bet_history if b['result'] == 'PENDING']

        if not pending:
            print("\n✅ No pending bets\n")
            return

        print(f"\n{'='*80}")
        print(f"⏳ PENDING BETS ({len(pending)})")
        print(f"{'='*80}\n")

        for bet in pending:
            print(f"ID: {bet['bet_id']}")
            print(f"   {bet['sport']}: {bet['game']}")
            print(f"   BET: {bet['bet']}")
            print(f"   Confidence: {bet['confidence']} | Edge: +{bet['expected_edge']:.1f}%")
            if bet['odds']:
                print(f"   Odds: {bet['odds']:+d}")
            print()


def main():
    """Interactive bet tracking"""

    tracker = BetTracker()

    while True:
        print("\n" + "="*80)
        print("BET TRACKER MENU")
        print("="*80)
        print("1. Show performance dashboard")
        print("2. List pending bets")
        print("3. Update bet result")
        print("4. Exit")

        choice = input("\nSelect option: ").strip()

        if choice == '1':
            tracker.display_dashboard()

        elif choice == '2':
            tracker.list_pending_bets()

        elif choice == '3':
            bet_id = input("Enter bet ID: ").strip()
            result = input("Result (WIN/LOSS/PUSH): ").strip().upper()

            if result in ['WIN', 'LOSS', 'PUSH']:
                tracker.update_result(bet_id, result)
            else:
                print("❌ Invalid result. Use WIN, LOSS, or PUSH")

        elif choice == '4':
            print("\n✅ Exiting bet tracker\n")
            break

        else:
            print("❌ Invalid option")


if __name__ == "__main__":
    main()
