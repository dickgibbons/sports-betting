#!/usr/bin/env python3
"""
Soccer Bet Tracker - Daily Results Tracking
Tracks actual results vs predictions and maintains cumulative performance
"""

import pandas as pd
import os
from datetime import datetime, timedelta
from typing import Dict, List
import requests
import time

class SoccerBetTracker:
    """Track soccer bet results and maintain cumulative performance"""

    def __init__(self):
        self.reports_dir = "Soccer reports"
        self.cumulative_file = "soccer_cumulative_performance.csv"
        self.api_key = "960c628e1c91c4b1f125e1eec52ad862"
        self.api_base = "https://v3.football.api-sports.io"
        self.initial_bankroll = 1000.0  # Starting bankroll

    def track_daily_results(self, date_str: str):
        """
        Track results for a specific date

        Args:
            date_str: Date in format 'YYYY-MM-DD'
        """

        print(f"⚽ SOCCER BET TRACKER - {date_str}")
        print("=" * 80)

        # Load today's recommendations
        recommendations = self._load_recommendations(date_str)

        if not recommendations:
            print(f"⚠️  No recommendations found for {date_str}")
            return

        print(f"📊 Found {len(recommendations)} recommended bets")

        # Fetch actual game results
        game_results = self._fetch_game_results(date_str)

        if not game_results:
            print(f"⚠️  No completed games found for {date_str}")
            print("   Games may not have finished yet or date may be in future")
            return

        print(f"✅ Found {len(game_results)} completed games")

        # Evaluate each bet
        evaluated_bets = []

        for bet in recommendations:
            result = self._evaluate_bet(bet, game_results)
            evaluated_bets.append(result)

        # Calculate daily performance
        wins = sum(1 for bet in evaluated_bets if bet['correct'])
        losses = len(evaluated_bets) - wins
        win_rate = wins / len(evaluated_bets) if evaluated_bets else 0

        total_profit = sum(bet['profit'] for bet in evaluated_bets)
        total_stake = sum(bet['stake_amount'] for bet in evaluated_bets)
        roi = (total_profit / total_stake) * 100 if total_stake > 0 else 0

        # Print summary
        print(f"\n📈 DAILY PERFORMANCE:")
        print(f"   Bets: {len(evaluated_bets)}")
        print(f"   Wins: {wins} | Losses: {losses}")
        print(f"   Win Rate: {win_rate*100:.1f}%")
        print(f"   Total Stake: ${total_stake:.2f}")
        print(f"   Total P/L: ${total_profit:+.2f}")
        print(f"   ROI: {roi:+.1f}%")

        # Performance by bet type
        df_bets = pd.DataFrame(evaluated_bets)

        print(f"\n📊 PERFORMANCE BY BET TYPE:")
        for market in df_bets['market'].unique():
            market_bets = df_bets[df_bets['market'] == market]
            market_wins = market_bets['correct'].sum()
            market_total = len(market_bets)
            market_win_rate = market_wins / market_total if market_total > 0 else 0
            market_profit = market_bets['profit'].sum()

            print(f"   {market}: {market_wins}/{market_total} wins ({market_win_rate*100:.1f}%) | ${market_profit:+.2f}")

        # Update cumulative performance
        self._update_cumulative(date_str, evaluated_bets, wins, losses, win_rate, total_profit, total_stake, roi)

        # Save detailed results
        self._save_daily_results(date_str, evaluated_bets)

    def _load_recommendations(self, date_str: str) -> List[Dict]:
        """Load bet recommendations from CSV"""

        # Format: YYYYMMDD
        date_folder = date_str.replace('-', '')

        csv_path = os.path.join(self.reports_dir, date_folder, f"soccer_best_bets_{date_str}.csv")

        if not os.path.exists(csv_path):
            return []

        df = pd.read_csv(csv_path)

        recommendations = []
        for _, row in df.iterrows():
            # Calculate stake amount (assuming 5% of initial bankroll for now)
            stake_pct = row['kelly_stake']
            stake_amount = self.initial_bankroll * stake_pct

            recommendations.append({
                'country': row['country'],
                'league': row['league'],
                'date': row['date'],
                'time': row['time'],
                'home_team': row['home_team'],
                'away_team': row['away_team'],
                'market': row['market'],
                'selection': row['selection'],
                'odds': row['odds'],
                'confidence': row['confidence'],
                'kelly_stake': stake_pct,
                'stake_amount': stake_amount,
                'expected_value': row['expected_value']
            })

        return recommendations

    def _fetch_game_results(self, date_str: str) -> Dict[str, Dict]:
        """Fetch actual game results from API-Sports"""

        headers = {'x-apisports-key': self.api_key}
        results = {}

        # Get leagues from yesterday's predictions
        date_folder = date_str.replace('-', '')
        csv_path = os.path.join(self.reports_dir, date_folder, f"soccer_best_bets_{date_str}.csv")

        if not os.path.exists(csv_path):
            return {}

        df = pd.read_csv(csv_path)

        # Group by league to fetch fixtures
        for league in df['league'].unique():
            try:
                # We need to map league names to league IDs
                # For now, fetch all fixtures for the date
                url = f"{self.api_base}/fixtures"
                params = {
                    'date': date_str
                }

                response = requests.get(url, params=params, headers=headers, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    fixtures = data.get('response', [])

                    for fixture in fixtures:
                        fixture_data = fixture.get('fixture', {})
                        status = fixture_data.get('status', {}).get('short', '')

                        # Only completed matches
                        if status == 'FT':
                            home_team = fixture.get('teams', {}).get('home', {}).get('name', '')
                            away_team = fixture.get('teams', {}).get('away', {}).get('name', '')

                            goals = fixture.get('goals', {})
                            home_goals = goals.get('home', 0)
                            away_goals = goals.get('away', 0)

                            # Get halftime score
                            score = fixture.get('score', {})
                            halftime = score.get('halftime', {})
                            h1_home = halftime.get('home', 0) if halftime else 0
                            h1_away = halftime.get('away', 0) if halftime else 0

                            game_key = f"{home_team}_{away_team}"

                            results[game_key] = {
                                'home_team': home_team,
                                'away_team': away_team,
                                'home_goals': home_goals,
                                'away_goals': away_goals,
                                'total_goals': home_goals + away_goals,
                                'h1_home': h1_home,
                                'h1_away': h1_away,
                                'h1_total': (h1_home or 0) + (h1_away or 0),
                                'btts': home_goals > 0 and away_goals > 0,
                                'result': 'Home' if home_goals > away_goals else ('Away' if away_goals > home_goals else 'Draw')
                            }

                time.sleep(0.5)  # Rate limiting

            except Exception as e:
                print(f"   ⚠️  Error fetching results for {league}: {e}")
                continue

        return results

    def _evaluate_bet(self, bet: Dict, game_results: Dict) -> Dict:
        """Evaluate if a bet won or lost"""

        # Find matching game (fuzzy match on team names)
        game_result = None
        game_key = f"{bet['home_team']}_{bet['away_team']}"

        if game_key in game_results:
            game_result = game_results[game_key]
        else:
            # Try fuzzy matching
            for key, result in game_results.items():
                if (bet['home_team'].lower() in result['home_team'].lower() or
                    result['home_team'].lower() in bet['home_team'].lower()) and \
                   (bet['away_team'].lower() in result['away_team'].lower() or
                    result['away_team'].lower() in bet['away_team'].lower()):
                    game_result = result
                    break

        if not game_result:
            # Game not found or not completed
            return {
                **bet,
                'correct': False,
                'profit': 0,
                'actual_score': 'Game not found',
                'actual_result': 'Not found'
            }

        # Evaluate based on market
        is_correct = False
        market = bet['market']

        # Match Winner
        if 'Win' in market or market in ['Home', 'Away', 'Draw']:
            if 'Home' in market:
                is_correct = game_result['result'] == 'Home'
            elif 'Away' in market:
                is_correct = game_result['result'] == 'Away'
            elif 'Draw' in market:
                is_correct = game_result['result'] == 'Draw'

        # BTTS
        elif 'BTTS' in market:
            if 'Yes' in market or ('Both Teams Score' in bet['selection'] and 'Not' not in bet['selection']):
                is_correct = game_result['btts']
            else:  # BTTS No
                is_correct = not game_result['btts']

        # Over/Under Totals
        elif 'Over' in market or 'Under' in market:
            # Parse threshold
            if '2.5' in market:
                threshold = 2.5
            elif '1.5' in market:
                threshold = 1.5
            elif '3.5' in market:
                threshold = 3.5
            else:
                threshold = 2.5

            # Check if it's team totals or game totals
            if 'Home' in market:
                score = game_result['home_goals']
            elif 'Away' in market:
                score = game_result['away_goals']
            elif 'H1' in market or '1st Half' in market:
                score = game_result['h1_total']
            else:
                score = game_result['total_goals']

            if 'Over' in market:
                is_correct = score > threshold
            else:
                is_correct = score < threshold

        # Calculate profit
        if is_correct:
            profit = bet['stake_amount'] * (bet['odds'] - 1)
        else:
            profit = -bet['stake_amount']

        actual_score = f"{game_result['home_team']} {game_result['home_goals']}-{game_result['away_goals']} {game_result['away_team']}"

        return {
            **bet,
            'correct': is_correct,
            'profit': profit,
            'actual_score': actual_score,
            'actual_result': game_result['result'],
            'actual_total_goals': game_result['total_goals'],
            'actual_btts': game_result['btts']
        }

    def _update_cumulative(self, date_str: str, bets: List[Dict], wins: int, losses: int,
                           win_rate: float, profit: float, stake: float, roi: float):
        """Update cumulative performance file"""

        # Load existing cumulative data
        if os.path.exists(self.cumulative_file):
            df_cum = pd.read_csv(self.cumulative_file)
        else:
            df_cum = pd.DataFrame()

        # Calculate running bankroll
        if len(df_cum) > 0:
            previous_bankroll = df_cum.iloc[-1]['bankroll']
        else:
            previous_bankroll = self.initial_bankroll

        current_bankroll = previous_bankroll + profit

        # Calculate bet type performance
        df_bets = pd.DataFrame(bets)

        # Count by market type
        market_counts = {}
        for market in ['Home Win', 'Away Win', 'Draw', 'BTTS Yes', 'BTTS No',
                       'Over 2.5', 'Under 2.5', 'Over 1.5', 'Under 1.5']:
            count = len(df_bets[df_bets['market'].str.contains(market, case=False, na=False)])
            if count > 0:
                market_counts[f"{market.replace(' ', '_').lower()}_bets"] = count

                # Calculate win rate for this market
                market_bets = df_bets[df_bets['market'].str.contains(market, case=False, na=False)]
                if len(market_bets) > 0:
                    market_wins = market_bets['correct'].sum()
                    market_wr = market_wins / len(market_bets)
                    market_counts[f"{market.replace(' ', '_').lower()}_wr"] = market_wr

        # Create today's row
        today_row = {
            'date': date_str,
            'total_bets': len(bets),
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'total_stake': stake,
            'profit': profit,
            'roi': roi / 100,  # Store as decimal
            'bankroll': current_bankroll,
            'bankroll_change': profit,
            'avg_odds': df_bets['odds'].mean() if len(df_bets) > 0 else 0,
            'avg_confidence': df_bets['confidence'].mean() if len(df_bets) > 0 else 0,
            **market_counts
        }

        # Append to cumulative
        df_cum = pd.concat([df_cum, pd.DataFrame([today_row])], ignore_index=True)

        # Calculate cumulative stats
        total_profit = df_cum['profit'].sum()
        total_roi = (total_profit / (len(df_cum) * self.initial_bankroll)) if len(df_cum) > 0 else 0

        print(f"\n💰 CUMULATIVE PERFORMANCE:")
        print(f"   Total Days: {len(df_cum)}")
        print(f"   Total Bets: {df_cum['total_bets'].sum()}")
        print(f"   Overall Win Rate: {(df_cum['wins'].sum() / df_cum['total_bets'].sum() * 100):.1f}%")
        print(f"   Total Profit: ${total_profit:+.2f}")
        print(f"   Current Bankroll: ${current_bankroll:.2f}")
        print(f"   Bankroll Growth: {((current_bankroll / self.initial_bankroll - 1) * 100):+.1f}%")

        # Save
        df_cum.to_csv(self.cumulative_file, index=False)
        print(f"\n✅ Updated cumulative performance: {self.cumulative_file}")

    def _save_daily_results(self, date_str: str, bets: List[Dict]):
        """Save detailed daily results"""

        date_folder = date_str.replace('-', '')
        results_dir = os.path.join(self.reports_dir, date_folder)

        os.makedirs(results_dir, exist_ok=True)

        filepath = os.path.join(results_dir, f"soccer_bet_results_{date_str}.csv")

        df = pd.DataFrame(bets)
        df.to_csv(filepath, index=False)

        print(f"✅ Saved daily results: {filepath}")


def main():
    """Run bet tracker"""

    import sys

    if len(sys.argv) < 2:
        # Default to yesterday (results typically available next day)
        date_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    else:
        date_str = sys.argv[1]

    tracker = SoccerBetTracker()
    tracker.track_daily_results(date_str)


if __name__ == '__main__':
    main()
