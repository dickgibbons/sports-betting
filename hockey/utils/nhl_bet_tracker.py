#!/usr/bin/env python3
"""
NHL Bet Tracker - Daily Results Tracking
Tracks actual results vs predictions and maintains cumulative performance
"""

import pandas as pd
import os
from datetime import datetime
from typing import Dict, List
import requests

class NHLBetTracker:
    """Track NHL bet results and maintain cumulative performance"""

    def __init__(self):
        self.reports_dir = "reports"
        self.cumulative_file = "nhl_cumulative_performance.csv"

    def track_daily_results(self, date_str: str):
        """
        Track results for a specific date

        Args:
            date_str: Date in format 'YYYY-MM-DD'
        """

        print(f"🏒 NHL BET TRACKER - {date_str}")
        print("=" * 70)

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
        total_stake = sum(bet['stake'] for bet in evaluated_bets)
        roi = (total_profit / total_stake) * 100 if total_stake > 0 else 0

        # Print summary
        print(f"\n📈 DAILY PERFORMANCE:")
        print(f"   Bets: {len(evaluated_bets)}")
        print(f"   Wins: {wins} | Losses: {losses}")
        print(f"   Win Rate: {win_rate*100:.1f}%")
        print(f"   Total P/L: ${total_profit:+.2f}")
        print(f"   ROI: {roi:+.1f}%")

        # Performance by bet type
        df_bets = pd.DataFrame(evaluated_bets)

        print(f"\n📊 PERFORMANCE BY BET TYPE:")
        for bet_type in df_bets['bet_type'].unique():
            type_bets = df_bets[df_bets['bet_type'] == bet_type]
            type_wins = type_bets['correct'].sum()
            type_total = len(type_bets)
            type_win_rate = type_wins / type_total if type_total > 0 else 0
            type_profit = type_bets['profit'].sum()

            print(f"   {bet_type}: {type_wins}/{type_total} wins ({type_win_rate*100:.1f}%) | ${type_profit:+.2f}")

        # Update cumulative performance
        self._update_cumulative(date_str, evaluated_bets, wins, losses, win_rate, total_profit, roi)

        # Save detailed results
        self._save_daily_results(date_str, evaluated_bets)

    def _load_recommendations(self, date_str: str) -> List[Dict]:
        """Load bet recommendations from CSV"""

        # Format: YYYYMMDD
        date_folder = date_str.replace('-', '')

        csv_path = os.path.join(self.reports_dir, date_folder, f"bet_recommendations_enhanced_{date_str}.csv")

        if not os.path.exists(csv_path):
            return []

        df = pd.read_csv(csv_path)

        recommendations = []
        for _, row in df.iterrows():
            recommendations.append({
                'game': row['Game'],
                'date': row['Date'],
                'bet_type': row['Bet_Type'],
                'pick': row['Pick'],
                'odds': row['Odds'],
                'confidence': float(row['Confidence'].strip('%')) / 100,
                'edge': float(row['Edge'].strip('%').replace('+', '')) / 100,
                'stake': 100.0  # Placeholder - would use Kelly calculation
            })

        return recommendations

    def _fetch_game_results(self, date_str: str) -> Dict[str, Dict]:
        """Fetch actual game results from NHL API"""

        url = f"https://api-web.nhle.com/v1/score/{date_str}"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            results = {}

            for game in data.get('games', []):
                if game.get('gameState') not in ['OFF', 'FINAL']:
                    continue  # Skip incomplete games

                home_team = game['homeTeam']['placeName']['default']
                away_team = game['awayTeam']['placeName']['default']

                game_key = f"{away_team} @ {home_team}"

                results[game_key] = {
                    'home_team': home_team,
                    'away_team': away_team,
                    'home_score': game['homeTeam']['score'],
                    'away_score': game['awayTeam']['score'],
                    'p1_home_score': game.get('periodScores', {}).get('1', {}).get('home', 0),
                    'p1_away_score': game.get('periodScores', {}).get('1', {}).get('away', 0)
                }

            return results

        except Exception as e:
            print(f"   Error fetching results: {e}")
            return {}

    def _evaluate_bet(self, bet: Dict, game_results: Dict) -> Dict:
        """Evaluate if a bet won or lost"""

        # Find matching game
        game_result = None
        for game_key, result in game_results.items():
            if result['home_team'] in bet['game'] or result['away_team'] in bet['game']:
                game_result = result
                break

        if not game_result:
            # Game not found or not completed
            return {
                **bet,
                'correct': False,
                'profit': 0,
                'actual_result': 'Game not found'
            }

        # Evaluate based on bet type
        is_correct = False
        actual_result = f"{game_result['away_team']} {game_result['away_score']} @ {game_result['home_team']} {game_result['home_score']}"

        # Moneyline
        if bet['bet_type'] == 'Moneyline':
            if game_result['home_team'] in bet['pick']:
                is_correct = game_result['home_score'] > game_result['away_score']
            else:
                is_correct = game_result['away_score'] > game_result['home_score']

        # Team Totals
        elif 'Total Over' in bet['bet_type'] or 'Total Under' in bet['bet_type']:
            # Parse threshold
            if 'Over 2.5' in bet['bet_type']:
                threshold = 2.5
                over = 'Over' in bet['bet_type']
            elif 'Over 3.5' in bet['bet_type'] or 'Under 3.5' in bet['bet_type']:
                threshold = 3.5
                over = 'Over' in bet['bet_type']
            else:
                threshold = 2.5
                over = True

            # Determine which team
            if game_result['home_team'] in bet['bet_type']:
                team_score = game_result['home_score']
            else:
                team_score = game_result['away_score']

            if over:
                is_correct = team_score > threshold
            else:
                is_correct = team_score < threshold

        # Game Totals
        elif 'Game Total' in bet['bet_type']:
            total_score = game_result['home_score'] + game_result['away_score']

            if 'O/U 5.5' in bet['bet_type']:
                threshold = 5.5
            elif 'O/U 6.5' in bet['bet_type']:
                threshold = 6.5
            else:
                threshold = 6.0

            if 'Over' in bet['pick']:
                is_correct = total_score > threshold
            else:
                is_correct = total_score < threshold

        # P1 Totals
        elif 'P1' in bet['bet_type']:
            p1_total = game_result['p1_home_score'] + game_result['p1_away_score']

            if 'Over 1.5' in bet['pick']:
                is_correct = p1_total > 1.5
            else:
                is_correct = p1_total < 1.5

        # Calculate profit
        if is_correct:
            profit = bet['stake'] * (bet['odds'] - 1)
        else:
            profit = -bet['stake']

        return {
            **bet,
            'correct': is_correct,
            'profit': profit,
            'actual_result': actual_result
        }

    def _update_cumulative(self, date_str: str, bets: List[Dict], wins: int, losses: int,
                           win_rate: float, profit: float, roi: float):
        """Update cumulative performance file"""

        # Load existing cumulative data
        if os.path.exists(self.cumulative_file):
            df_cum = pd.read_csv(self.cumulative_file)
        else:
            df_cum = pd.DataFrame()

        # Calculate bet type performance
        df_bets = pd.DataFrame(bets)

        bet_type_stats = {}
        for bet_type in df_bets['bet_type'].unique():
            type_bets = df_bets[df_bets['bet_type'] == bet_type]
            type_wins = type_bets['correct'].sum()
            type_total = len(type_bets)
            type_win_rate = type_wins / type_total if type_total > 0 else 0

            bet_type_stats[f"{bet_type}_win_rate"] = type_win_rate

        # Create today's row
        today_row = {
            'date': date_str,
            'total_bets': len(bets),
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'profit': profit,
            'roi': roi,
            **bet_type_stats
        }

        # Append to cumulative
        df_cum = pd.concat([df_cum, pd.DataFrame([today_row])], ignore_index=True)

        # Save
        df_cum.to_csv(self.cumulative_file, index=False)
        print(f"\n✅ Updated cumulative performance: {self.cumulative_file}")

    def _save_daily_results(self, date_str: str, bets: List[Dict]):
        """Save detailed daily results"""

        date_folder = date_str.replace('-', '')
        results_dir = os.path.join(self.reports_dir, date_folder)

        os.makedirs(results_dir, exist_ok=True)

        filepath = os.path.join(results_dir, f"bet_results_{date_str}.csv")

        df = pd.DataFrame(bets)
        df.to_csv(filepath, index=False)

        print(f"✅ Saved daily results: {filepath}")


def main():
    """Run bet tracker"""

    import sys

    if len(sys.argv) < 2:
        # Default to yesterday (results typically available next day)
        from datetime import datetime, timedelta
        date_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    else:
        date_str = sys.argv[1]

    tracker = NHLBetTracker()
    tracker.track_daily_results(date_str)


if __name__ == '__main__':
    main()
