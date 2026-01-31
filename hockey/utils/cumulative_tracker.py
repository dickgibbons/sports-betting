#!/usr/bin/env python3
"""
NHL Cumulative Results Tracker
Tracks performance of all recommended bets over time
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import argparse


class CumulativeTracker:
    """Track cumulative betting performance"""

    def __init__(self, initial_bankroll: float = 1000.0):
        self.initial_bankroll = initial_bankroll
        self.tracker_file = Path('cumulative_results.csv')
        self.recommendations_dir = Path('.')

    def load_existing_tracker(self) -> pd.DataFrame:
        """Load existing cumulative results"""
        if self.tracker_file.exists():
            return pd.read_csv(self.tracker_file)
        else:
            return pd.DataFrame(columns=[
                'Date', 'Game', 'Bet_Type', 'Pick', 'Odds', 'Odds_Source', 'Units',
                'Result', 'Profit_Loss', 'Running_Bankroll', 'ROI'
            ])

    def get_game_result(self, game_date: str, home_team: str, away_team: str):
        """
        Get actual game result from training history
        Returns: (home_score, away_score, winner)
        """
        history_file = Path('training_history.csv')

        if not history_file.exists():
            return None, None, None

        df_history = pd.read_csv(history_file)

        # Find matching game
        for idx, row in df_history.iterrows():
            if row['date'][:10] == game_date:
                if (home_team.lower() in row['home_team'].lower() or row['home_team'].lower() in home_team.lower()) and \
                   (away_team.lower() in row['away_team'].lower() or row['away_team'].lower() in away_team.lower()):

                    home_score = row.get('home_score', 0)
                    away_score = row.get('away_score', 0)
                    winner = row['home_team'] if row['outcome'] == 1 else row['away_team']

                    return home_score, away_score, winner

        return None, None, None

    def update_with_recommendations(self, date_str: str):
        """Update tracker with recommendations from a specific date"""

        rec_file = Path(f'bet_recommendations_{date_str}.csv')

        if not rec_file.exists():
            print(f"⚠️  No recommendations file for {date_str}")
            return

        df_recs = pd.read_csv(rec_file)

        if df_recs.empty:
            print(f"✅ No bets recommended for {date_str}")
            return

        df_tracker = self.load_existing_tracker()

        # Get current bankroll
        if len(df_tracker) > 0:
            current_bankroll = df_tracker.iloc[-1]['Running_Bankroll']
        else:
            current_bankroll = self.initial_bankroll

        new_results = []

        print(f"\n📊 Processing {len(df_recs)} recommendations from {date_str}...")

        for idx, rec in df_recs.iterrows():
            # Parse game teams
            game_parts = rec['Game'].split(' @ ')
            away_team = game_parts[0]
            home_team = game_parts[1]

            # Get actual result
            home_score, away_score, winner = self.get_game_result(date_str, home_team, away_team)

            if winner is None:
                print(f"   ⏳ Game not finished yet: {rec['Game']}")
                continue

            # Determine bet result
            bet_won = self._check_bet_result(rec, home_team, away_team, home_score, away_score, winner)

            # Calculate profit/loss
            units = self._parse_units(rec['Recommended_Unit'])
            bet_amount = current_bankroll * (units * 0.01)  # 1 unit = 1% of bankroll

            odds = float(rec['Odds'])

            if bet_won:
                profit_loss = bet_amount * (odds - 1)
                result = '✅ Win'
            else:
                profit_loss = -bet_amount
                result = '❌ Loss'

            current_bankroll += profit_loss
            roi = ((current_bankroll - self.initial_bankroll) / self.initial_bankroll) * 100

            # Get odds source from recommendation - prefer specific sportsbook
            odds_source = rec.get('sportsbook', rec.get('Odds_Source', rec.get('odds_source', rec.get('best_sportsbook', 'DraftKings'))))

            new_results.append({
                'Date': date_str,
                'Game': rec['Game'],
                'Bet_Type': rec['Bet_Type'],
                'Pick': rec['Pick'],
                'Odds': rec['Odds'],
                'Odds_Source': odds_source,
                'Units': units,
                'Result': result,
                'Profit_Loss': round(profit_loss, 2),
                'Running_Bankroll': round(current_bankroll, 2),
                'ROI': round(roi, 2),
                'Actual_Score': f"{away_team[:3]} {away_score} @ {home_team[:3]} {home_score}"
            })

            print(f"   {result} {rec['Bet_Type']}: {rec['Pick']} @ {rec['Odds']} | "
                  f"P/L: ${profit_loss:+.2f} | Bankroll: ${current_bankroll:.2f}")

        if new_results:
            df_new = pd.DataFrame(new_results)
            df_combined = pd.concat([df_tracker, df_new], ignore_index=True)
            df_combined.to_csv(self.tracker_file, index=False)

            print(f"\n✅ Updated cumulative tracker with {len(new_results)} results")
        else:
            print(f"\n⏳ No finished games to update")

    def _check_bet_result(self, rec, home_team, away_team, home_score, away_score, winner) -> bool:
        """Check if bet won based on type"""

        bet_type = rec['Bet_Type']
        pick = rec['Pick']

        if bet_type == 'Moneyline':
            return pick.lower() in winner.lower()

        elif 'Total' in bet_type:
            total_goals = home_score + away_score
            line = float(pick.split()[-1])

            if 'Over' in bet_type:
                return total_goals > line
            else:
                return total_goals < line

        elif 'Puck Line' in bet_type or 'Spread' in bet_type:
            # Parse puck line
            if home_team.lower() in pick.lower():
                # Home team covering
                return (home_score - away_score) > 1.5
            else:
                # Away team covering
                return (away_score - home_score) > 1.5

        return False

    def _parse_units(self, unit_str: str) -> float:
        """Parse unit string to float"""
        if '3' in unit_str:
            return 3.0
        elif '2' in unit_str:
            return 2.0
        else:
            return 1.0

    def generate_summary_report(self, output_file: str = None):
        """Generate comprehensive summary report"""

        df_tracker = self.load_existing_tracker()

        if df_tracker.empty:
            print("📊 No results to report yet")
            return

        if output_file is None:
            use_date = datetime.now().strftime('%Y-%m-%d')
            # Create date-based folder structure: reports/YYYYMMDD/
            import os
            date_folder = use_date.replace('-', '')  # Convert 2025-10-17 to 20251017
            reports_dir = os.path.join('reports', date_folder)
            os.makedirs(reports_dir, exist_ok=True)
            output_file = os.path.join(reports_dir, f"cumulative_summary_{use_date}.csv")

        # Calculate statistics
        total_bets = len(df_tracker)
        wins = len(df_tracker[df_tracker['Result'].str.contains('Win')])
        losses = total_bets - wins
        win_rate = (wins / total_bets * 100) if total_bets > 0 else 0

        total_profit = df_tracker['Profit_Loss'].sum()
        current_bankroll = df_tracker.iloc[-1]['Running_Bankroll']
        current_roi = df_tracker.iloc[-1]['ROI']

        # Best/worst bets
        best_bet = df_tracker.loc[df_tracker['Profit_Loss'].idxmax()] if total_bets > 0 else None
        worst_bet = df_tracker.loc[df_tracker['Profit_Loss'].idxmin()] if total_bets > 0 else None

        # Performance by bet type
        by_type = df_tracker.groupby('Bet_Type').agg({
            'Result': lambda x: (x.str.contains('Win').sum(), len(x)),
            'Profit_Loss': 'sum'
        })

        print(f"\n{'='*100}")
        print(f"🏒 NHL CUMULATIVE BETTING PERFORMANCE")
        print(f"{'='*100}\n")

        print(f"📊 OVERALL STATISTICS:")
        print(f"   Initial Bankroll: ${self.initial_bankroll:.2f}")
        print(f"   Current Bankroll: ${current_bankroll:.2f}")
        print(f"   Total Profit/Loss: ${total_profit:+.2f}")
        print(f"   ROI: {current_roi:+.2f}%")
        print(f"")
        print(f"   Total Bets: {total_bets}")
        print(f"   Wins: {wins} ({win_rate:.1f}%)")
        print(f"   Losses: {losses} ({100-win_rate:.1f}%)")
        print(f"")

        if best_bet is not None:
            print(f"🔥 BEST BET:")
            print(f"   {best_bet['Date']}: {best_bet['Bet_Type']} - {best_bet['Pick']}")
            print(f"   Profit: ${best_bet['Profit_Loss']:+.2f}")
            print(f"")

        if worst_bet is not None:
            print(f"❌ WORST BET:")
            print(f"   {worst_bet['Date']}: {worst_bet['Bet_Type']} - {worst_bet['Pick']}")
            print(f"   Loss: ${worst_bet['Profit_Loss']:+.2f}")
            print(f"")

        print(f"📈 PERFORMANCE BY BET TYPE:")
        for bet_type, stats in by_type.iterrows():
            type_wins, type_total = stats['Result']
            type_profit = stats['Profit_Loss']
            type_wr = (type_wins / type_total * 100) if type_total > 0 else 0
            print(f"   {bet_type:15} | {type_wins}W-{type_total-type_wins}L ({type_wr:.1f}%) | ${type_profit:+.2f}")

        print(f"\n{'='*100}")

        # Save detailed tracker
        df_tracker.to_csv(output_file, index=False)
        print(f"\n✅ Full results saved to: {output_file}")

        return df_tracker


def main():
    parser = argparse.ArgumentParser(description='Track cumulative betting results')
    parser.add_argument('--update', type=str,
                       help='Update with results from date (YYYY-MM-DD)')
    parser.add_argument('--summary', action='store_true',
                       help='Generate summary report')
    parser.add_argument('--bankroll', type=float, default=1000.0,
                       help='Initial bankroll (default: 1000)')

    args = parser.parse_args()

    tracker = CumulativeTracker(initial_bankroll=args.bankroll)

    if args.update:
        tracker.update_with_recommendations(args.update)

    if args.summary or not args.update:
        tracker.generate_summary_report()


if __name__ == "__main__":
    main()
