#!/usr/bin/env python3
"""
Soccer Cumulative Results Tracker
Tracks performance of all recommended bets over time
Matches NHL cumulative_tracker.py structure
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import argparse
import requests

class SoccerCumulativeTracker:
    """Track cumulative soccer betting performance"""

    def __init__(self, initial_bankroll: float = 1000.0, api_key: str = None):
        self.initial_bankroll = initial_bankroll
        self.api_key = api_key
        self.tracker_file = Path('cumulative_results_soccer.csv')
        self.recommendations_dir = Path('.')
        self.api_base = "https://v3.football.api-sports.io"
        self.headers = {
            "x-apisports-key": api_key
        }

    def load_existing_tracker(self) -> pd.DataFrame:
        """Load existing cumulative results"""

        if self.tracker_file.exists():
            return pd.read_csv(self.tracker_file)
        else:
            return pd.DataFrame(columns=[
                'Date', 'Match', 'League', 'Market', 'Pick', 'Odds', 'Odds_Source', 'Units',
                'Result', 'Profit_Loss', 'Running_Bankroll', 'ROI'
            ])

    def get_match_result(self, home_team: str, away_team: str, match_date: str):
        """Get actual match result from API"""

        try:
            url = f"{self.api_base}/fixtures"
            params = {
                "date": match_date
            }

            response = requests.get(url, headers=self.headers, params=params)

            if response.status_code == 200:
                data = response.json()
                fixtures = data.get('response', [])

                # Find matching fixture
                for fixture in fixtures:
                    fixture_home = fixture['teams']['home']['name']
                    fixture_away = fixture['teams']['away']['name']

                    if (home_team.lower() in fixture_home.lower() or fixture_home.lower() in home_team.lower()) and \
                       (away_team.lower() in fixture_away.lower() or fixture_away.lower() in away_team.lower()):

                        if fixture['fixture']['status']['short'] == 'FT':
                            home_score = fixture['goals']['home']
                            away_score = fixture['goals']['away']

                            # Get statistics if available
                            stats = fixture.get('statistics', [])
                            total_corners = 0

                            if len(stats) >= 2:
                                for team_stats in stats:
                                    for stat in team_stats['statistics']:
                                        if stat['type'] == 'Corner Kicks' and stat['value']:
                                            total_corners += int(stat['value'])

                            return {
                                'home_score': home_score,
                                'away_score': away_score,
                                'total_goals': home_score + away_score,
                                'total_corners': total_corners,
                                'btts': (home_score > 0 and away_score > 0)
                            }

            return None

        except Exception as e:
            print(f"   ❌ Error fetching result: {e}")
            return None

    def update_with_recommendations(self, date_str: str):
        """Update tracker with recommendations from a specific date"""

        rec_file = Path(f'bet_recommendations_soccer_{date_str}.csv')

        if not rec_file.exists():
            print(f"⚠️  No recommendations file for {date_str}")
            return

        df_recs = pd.read_csv(rec_file)

        # Check if it's an empty recommendations file
        if 'Message' in df_recs.columns:
            print(f"✅ No bets recommended for {date_str}")
            return

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
            # Parse match teams
            match_parts = rec['Match'].split(' vs ')
            if len(match_parts) != 2:
                continue

            home_team = match_parts[0]
            away_team = match_parts[1]

            # Get actual result
            result = self.get_match_result(home_team, away_team, date_str)

            if result is None:
                print(f"   ⏳ Match not finished yet: {rec['Match']}")
                continue

            # Determine bet result
            bet_won = self._check_bet_result(rec, result)

            # Calculate profit/loss
            units = rec['Units']
            bet_amount = current_bankroll * (units * 0.01)  # 1 unit = 1% of bankroll
            odds = float(rec['Odds'])

            if bet_won:
                profit_loss = bet_amount * (odds - 1)
                result_str = '✅ Win'
            else:
                profit_loss = -bet_amount
                result_str = '❌ Loss'

            current_bankroll += profit_loss
            roi = ((current_bankroll - self.initial_bankroll) / self.initial_bankroll) * 100

            # Get odds source from recommendation - prefer specific sportsbook
            odds_source = rec.get('sportsbook', rec.get('Odds_Source', rec.get('odds_source', rec.get('best_sportsbook', 'DraftKings'))))

            new_results.append({
                'Date': date_str,
                'Match': rec['Match'],
                'League': rec['League'],
                'Market': rec['Market'],
                'Pick': rec['Pick'],
                'Odds': rec['Odds'],
                'Odds_Source': odds_source,
                'Units': units,
                'Result': result_str,
                'Profit_Loss': round(profit_loss, 2),
                'Running_Bankroll': round(current_bankroll, 2),
                'ROI': round(roi, 2)
            })

            print(f"   {result_str} {rec['Market']}: {rec['Pick']} @ {rec['Odds']} | "
                  f"P/L: ${profit_loss:+.2f} | Bankroll: ${current_bankroll:.2f}")

        if new_results:
            df_new = pd.DataFrame(new_results)
            df_combined = pd.concat([df_tracker, df_new], ignore_index=True)
            df_combined.to_csv(self.tracker_file, index=False)

            print(f"\n✅ Updated cumulative tracker with {len(new_results)} results")
        else:
            print(f"\n⏳ No finished matches to update")

    def _check_bet_result(self, rec, result) -> bool:
        """Check if bet won based on market type"""

        market = rec['Market'].lower()
        pick = rec['Pick'].lower()

        if 'match result' in market:
            if 'home' in market and result['home_score'] > result['away_score']:
                return True
            elif 'away' in market and result['away_score'] > result['home_score']:
                return True
            elif 'draw' in market and result['home_score'] == result['away_score']:
                return True
            else:
                return False

        elif 'over 2.5 goals' in market:
            return result['total_goals'] > 2.5

        elif 'btts' in market or 'both teams score' in market:
            return result['btts']

        elif 'corner' in market:
            if 'over 8.5' in market:
                return result['total_corners'] > 8.5
            elif 'over 10.5' in market:
                return result['total_corners'] > 10.5

        return False

    def generate_summary_report(self, output_file: str = None):
        """Generate comprehensive summary report"""

        df_tracker = self.load_existing_tracker()

        if df_tracker.empty:
            print("📊 No results to report yet")
            return

        if output_file is None:
            output_file = f"cumulative_summary_soccer_{datetime.now().strftime('%Y-%m-%d')}.csv"

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

        # Performance by market
        by_market = df_tracker.groupby('Market').agg({
            'Result': lambda x: (x.str.contains('Win').sum(), len(x)),
            'Profit_Loss': 'sum'
        })

        print(f"\n{'='*100}")
        print(f"⚽ SOCCER CUMULATIVE BETTING PERFORMANCE")
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
            print(f"   {best_bet['Date']}: {best_bet['Market']} - {best_bet['Pick']}")
            print(f"   Profit: ${best_bet['Profit_Loss']:+.2f}")
            print(f"")

        if worst_bet is not None:
            print(f"❌ WORST BET:")
            print(f"   {worst_bet['Date']}: {worst_bet['Market']} - {worst_bet['Pick']}")
            print(f"   Loss: ${worst_bet['Profit_Loss']:+.2f}")
            print(f"")

        print(f"📈 PERFORMANCE BY MARKET:")
        for market, stats in by_market.iterrows():
            market_wins, market_total = stats['Result']
            market_profit = stats['Profit_Loss']
            market_wr = (market_wins / market_total * 100) if market_total > 0 else 0
            print(f"   {market:30} | {market_wins}W-{market_total-market_wins}L ({market_wr:.1f}%) | ${market_profit:+.2f}")

        print(f"\n{'='*100}")

        # Save detailed tracker
        df_tracker.to_csv(output_file, index=False)
        print(f"\n✅ Full results saved to: {output_file}")

        return df_tracker


def main():
    parser = argparse.ArgumentParser(description='Track cumulative soccer betting results')
    parser.add_argument('--update', type=str, help='Update with results from date (YYYY-MM-DD)')
    parser.add_argument('--summary', action='store_true', help='Generate summary report')
    parser.add_argument('--bankroll', type=float, default=1000.0, help='Initial bankroll (default: 1000)')

    args = parser.parse_args()

    # API key
    api_key = "960c628e1c91c4b1f125e1eec52ad862"

    tracker = SoccerCumulativeTracker(initial_bankroll=args.bankroll, api_key=api_key)

    if args.update:
        tracker.update_with_recommendations(args.update)

    if args.summary or not args.update:
        tracker.generate_summary_report()


if __name__ == "__main__":
    main()
