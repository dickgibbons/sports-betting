#!/usr/bin/env python3
"""
NHL Quick Backtest - Test with Recent Completed Games
Simplified version that fetches actual NHL results and evaluates predictions
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import sys

class NHLQuickBacktest:
    """Quick backtest using NHL API for recent games"""

    def __init__(self):
        self.results = []

    def fetch_completed_games(self, date_str: str):
        """Fetch completed NHL games for a date"""

        url = f"https://api-web.nhle.com/v1/score/{date_str}"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            games = []

            for game in data.get('games', []):
                # Only include completed games
                if game.get('gameState') not in ['OFF', 'FINAL']:
                    continue

                # Updated API structure - team names are in abbrev field
                home_abbrev = game.get('homeTeam', {}).get('abbrev', 'Unknown')
                away_abbrev = game.get('awayTeam', {}).get('abbrev', 'Unknown')

                # Use common name if available, otherwise use abbrev
                home_team = game.get('homeTeam', {}).get('commonName', {}).get('default', home_abbrev)
                away_team = game.get('awayTeam', {}).get('commonName', {}).get('default', away_abbrev)

                home_score = game.get('homeTeam', {}).get('score', 0)
                away_score = game.get('awayTeam', {}).get('score', 0)

                games.append({
                    'date': date_str,
                    'home_team': home_team,
                    'away_team': away_team,
                    'home_score': home_score,
                    'away_score': away_score,
                    'total_goals': home_score + away_score,
                    'game_id': game.get('id')
                })

            return games

        except Exception as e:
            print(f"   Error fetching games: {e}")
            return []

    def generate_simple_predictions(self, game):
        """Generate simple predictions for testing"""

        predictions = []

        # Predict game total (simplified - use historical average)
        predicted_total = 6.2  # NHL average

        # Game Total O/U 6.5
        if predicted_total > 6.5:
            predictions.append({
                'game': f"{game['away_team']} @ {game['home_team']}",
                'bet_type': 'Game Total O/U 6.5',
                'pick': 'Over 6.5',
                'prediction': predicted_total,
                'actual': game['total_goals'],
                'correct': game['total_goals'] > 6.5
            })
        else:
            predictions.append({
                'game': f"{game['away_team']} @ {game['home_team']}",
                'bet_type': 'Game Total O/U 6.5',
                'pick': 'Under 6.5',
                'prediction': predicted_total,
                'actual': game['total_goals'],
                'correct': game['total_goals'] < 6.5
            })

        # Game Total O/U 5.5
        if predicted_total > 5.5:
            predictions.append({
                'game': f"{game['away_team']} @ {game['home_team']}",
                'bet_type': 'Game Total O/U 5.5',
                'pick': 'Over 5.5',
                'prediction': predicted_total,
                'actual': game['total_goals'],
                'correct': game['total_goals'] > 5.5
            })

        return predictions

    def backtest_date_range(self, start_date: str, end_date: str):
        """Backtest over a date range"""

        print("🏒 NHL QUICK BACKTEST")
        print("=" * 70)
        print(f"📅 Period: {start_date} to {end_date}")
        print("=" * 70)
        print()

        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        current = start
        all_predictions = []

        while current <= end:
            date_str = current.strftime('%Y-%m-%d')

            print(f"📅 {date_str}...")

            games = self.fetch_completed_games(date_str)

            if not games:
                print(f"   No completed games found")
                current += timedelta(days=1)
                continue

            print(f"   Found {len(games)} completed games")

            # Generate and evaluate predictions
            for game in games:
                predictions = self.generate_simple_predictions(game)
                all_predictions.extend(predictions)

            current += timedelta(days=1)

        # Analyze results
        self._analyze_results(all_predictions)

    def _analyze_results(self, predictions):
        """Analyze backtest results"""

        if not predictions:
            print("\n⚠️  No predictions to analyze")
            return

        df = pd.DataFrame(predictions)

        print(f"\n{'=' * 70}")
        print("📊 BACKTEST RESULTS")
        print(f"{'=' * 70}")

        # Overall stats
        total_bets = len(df)
        wins = df['correct'].sum()
        losses = total_bets - wins
        win_rate = wins / total_bets if total_bets > 0 else 0

        print(f"\n💰 OVERALL PERFORMANCE:")
        print(f"   Total Bets: {total_bets}")
        print(f"   Wins: {wins} | Losses: {losses}")
        print(f"   Win Rate: {win_rate*100:.1f}%")

        # By bet type
        print(f"\n📊 PERFORMANCE BY BET TYPE:")

        for bet_type in df['bet_type'].unique():
            type_df = df[df['bet_type'] == bet_type]
            type_wins = type_df['correct'].sum()
            type_total = len(type_df)
            type_win_rate = type_wins / type_total if type_total > 0 else 0

            print(f"   {bet_type}:")
            print(f"      Bets: {type_total} | Wins: {type_wins} | Win Rate: {type_win_rate*100:.1f}%")

        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"nhl_quick_backtest_{timestamp}.csv"
        df.to_csv(filename, index=False)
        print(f"\n✅ Results saved to: {filename}")


def main():
    """Run quick backtest"""

    if len(sys.argv) < 3:
        print("Usage: python3 nhl_quick_backtest.py START_DATE END_DATE")
        print("Example: python3 nhl_quick_backtest.py 2024-10-10 2024-10-18")
        sys.exit(1)

    start_date = sys.argv[1]
    end_date = sys.argv[2]

    backtest = NHLQuickBacktest()
    backtest.backtest_date_range(start_date, end_date)


if __name__ == '__main__':
    main()
