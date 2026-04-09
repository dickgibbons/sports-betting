#!/usr/bin/env python3
"""
NHL Daily Totals Report Generator
Generates daily report comparing ML predictions to market totals
"""

import sys
import os
# Add utils directory to path
utils_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils')
strategies_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, utils_dir)
sys.path.insert(0, strategies_dir)

from nhl_ml_totals_predictor import NHLMLTotalsPredictor
import requests
from datetime import datetime
import argparse


class NHLDailyTotalsReport:
    """Generate daily NHL totals predictions report"""

    def __init__(self):
        self.predictor = NHLMLTotalsPredictor()
        self.nhl_api_base = "https://api-web.nhle.com/v1"
        self.odds_api_key = '518c226b561ad7586ec8c5dd1144e3fb'

        # Load trained models
        if not self.predictor.load_models():
            print("⚠️  Models not found. Please train models first by running:")
            print("   python3 nhl_ml_totals_predictor.py")
            sys.exit(1)

    def get_todays_games(self, date_str=None):
        """Fetch today's NHL games using new API"""

        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')

        print(f"📅 Fetching NHL games for {date_str}...\n")

        url = f"{self.nhl_api_base}/score/{date_str}"

        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                game_list = data.get('games', [])

                games = []
                for game in game_list:
                    if game.get('gameType') == 2:  # Regular season (2 = regular, 3 = playoffs)
                        home_team = game.get('homeTeam', {}).get('name', {}).get('default', '')
                        away_team = game.get('awayTeam', {}).get('name', {}).get('default', '')

                        games.append({
                            'home_team': home_team,
                            'away_team': away_team,
                            'game_time': game.get('startTimeUTC', '')
                        })

                print(f"✅ Found {len(games)} NHL games\n")
                return games

        except Exception as e:
            print(f"❌ Error fetching schedule: {e}")
            return []

    def get_market_totals(self):
        """Fetch market totals from The Odds API"""

        print("💰 Fetching market totals from odds API...")

        url = f"https://api.the-odds-api.com/v4/sports/icehockey_nhl/odds/"
        params = {
            'apiKey': self.odds_api_key,
            'regions': 'us',
            'markets': 'totals',
            'oddsFormat': 'american'
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()

                market_totals = {}

                for game in data:
                    home_team = game.get('home_team', '')
                    away_team = game.get('away_team', '')

                    bookmakers = game.get('bookmakers', [])
                    if bookmakers:
                        markets = bookmakers[0].get('markets', [])

                        for market in markets:
                            if market.get('key') == 'totals':
                                outcomes = market.get('outcomes', [])
                                for outcome in outcomes:
                                    if outcome.get('name') == 'Over':
                                        total = outcome.get('point')
                                        market_totals[f"{away_team}@{home_team}"] = total
                                        break

                print(f"✅ Found market totals for {len(market_totals)} games\n")
                return market_totals

        except Exception as e:
            print(f"⚠️  Error fetching odds: {e}\n")
            return {}

    def generate_report(self, date_str=None):
        """Generate complete daily totals report"""

        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')

        print("=" * 100)
        print(f"🏒 NHL ML TOTALS PREDICTION REPORT - {date_str}")
        print("=" * 100)
        print()

        # Get today's games
        games = self.get_todays_games(date_str)

        if not games:
            print("⚠️  No NHL games scheduled for today\n")
            return

        # Get market totals
        market_totals = self.get_market_totals()

        # Generate predictions
        print("🤖 Generating ML predictions...\n")

        predictions = []

        for game in games:
            home = game['home_team']
            away = game['away_team']

            prediction = self.predictor.predict_game(home, away)

            if prediction:
                # Get market total
                game_key = f"{away}@{home}"
                market_total = market_totals.get(game_key)

                prediction['market_total'] = market_total
                prediction['game_time'] = game['game_time']

                if market_total:
                    prediction['edge'] = prediction['predicted_total'] - market_total
                else:
                    prediction['edge'] = None

                predictions.append(prediction)

        # Display report
        self._display_report(predictions, date_str)

        # Save to file
        self._save_report(predictions, date_str)

        return predictions

    def _display_report(self, predictions, date_str):
        """Display formatted report"""

        print("=" * 100)
        print("📊 GAME TOTALS PREDICTIONS")
        print("=" * 100)
        print()

        if not predictions:
            print("⚠️  No predictions available (teams may not have enough historical data)\n")
            return

        # Sort by absolute edge (biggest differences first)
        predictions_sorted = sorted(predictions, key=lambda x: abs(x['edge']) if x['edge'] is not None else 0, reverse=True)

        for idx, pred in enumerate(predictions_sorted, 1):
            print(f"GAME #{idx}: {pred['away_team']} @ {pred['home_team']}")
            print("-" * 100)

            print(f"   🤖 ML Predicted Total:  {pred['predicted_total']:.2f}")

            if pred['market_total']:
                print(f"   💰 Market Total:        {pred['market_total']:.2f}")
                edge = pred['edge']
                edge_str = f"{edge:+.2f}" if edge else "N/A"

                if edge and abs(edge) >= 0.5:
                    indicator = "🔥" if edge > 0 else "❄️"
                    print(f"   📈 Edge:                {edge_str} {indicator}")
                else:
                    print(f"   📈 Edge:                {edge_str}")
            else:
                print(f"   💰 Market Total:        Not Available")
                print(f"   📈 Edge:                N/A")

            print()
            print(f"   🎯 FIRST PERIOD PROBABILITIES:")
            print(f"      {pred['home_team'][:30]:30s} over 0.5 goals: {pred['home_over_0_5_1p_prob']:.1f}%")
            print(f"      {pred['away_team'][:30]:30s} over 0.5 goals: {pred['away_over_0_5_1p_prob']:.1f}%")
            print(f"      {'1st Period Total':30s} over 1.5 goals: {pred['period_over_1_5_prob']:.1f}%")

            print()
            print(f"   📊 MODEL PREDICTIONS:")
            for model_name, total in pred['model_predictions'].items():
                print(f"      {model_name:20s}: {total:.2f}")

            print()
            print()

        # Summary
        print("=" * 100)
        print("📋 SUMMARY")
        print("=" * 100)

        games_with_edge = [p for p in predictions if p['edge'] is not None and abs(p['edge']) >= 0.5]

        if games_with_edge:
            print(f"\n🔥 {len(games_with_edge)} games with significant edge (±0.5 goals):\n")

            for pred in sorted(games_with_edge, key=lambda x: abs(x['edge']), reverse=True):
                edge = pred['edge']
                direction = "OVER" if edge > 0 else "UNDER"
                print(f"   {pred['away_team']} @ {pred['home_team']}")
                print(f"      → Bet {direction} {pred['market_total']:.1f} (Edge: {edge:+.2f})")
                print()
        else:
            print("\n💡 No games with significant edge (±0.5 goals) today")

        print()

    def _save_report(self, predictions, date_str):
        """Save report to file"""

        output_dir = f"/Users/dickgibbons/AI Projects/sports-betting/reports/{date_str}"
        os.makedirs(output_dir, exist_ok=True)

        filename = f"{output_dir}/nhl_ml_totals_{date_str}.txt"

        with open(filename, 'w') as f:
            f.write(f"🏒 NHL ML TOTALS PREDICTION REPORT - {date_str}\n")
            f.write("=" * 100 + "\n\n")

            predictions_sorted = sorted(predictions, key=lambda x: abs(x['edge']) if x['edge'] is not None else 0, reverse=True)

            for idx, pred in enumerate(predictions_sorted, 1):
                f.write(f"GAME #{idx}: {pred['away_team']} @ {pred['home_team']}\n")
                f.write("-" * 100 + "\n")
                f.write(f"   ML Predicted Total:  {pred['predicted_total']:.2f}\n")

                if pred['market_total']:
                    f.write(f"   Market Total:        {pred['market_total']:.2f}\n")
                    f.write(f"   Edge:                {pred['edge']:+.2f}\n")
                else:
                    f.write(f"   Market Total:        Not Available\n")

                f.write(f"\n   FIRST PERIOD PROBABILITIES:\n")
                f.write(f"      {pred['home_team']:30s} over 0.5 goals: {pred['home_over_0_5_1p_prob']:.1f}%\n")
                f.write(f"      {pred['away_team']:30s} over 0.5 goals: {pred['away_over_0_5_1p_prob']:.1f}%\n")
                f.write(f"      1st Period Total over 1.5 goals: {pred['period_over_1_5_prob']:.1f}%\n")

                f.write(f"\n   MODEL PREDICTIONS:\n")
                for model_name, total in pred['model_predictions'].items():
                    f.write(f"      {model_name:20s}: {total:.2f}\n")

                f.write("\n\n")

            # Summary
            games_with_edge = [p for p in predictions if p['edge'] is not None and abs(p['edge']) >= 0.5]

            f.write("=" * 100 + "\n")
            f.write("SUMMARY\n")
            f.write("=" * 100 + "\n\n")

            if games_with_edge:
                f.write(f"{len(games_with_edge)} games with significant edge (±0.5 goals):\n\n")
                for pred in sorted(games_with_edge, key=lambda x: abs(x['edge']), reverse=True):
                    edge = pred['edge']
                    direction = "OVER" if edge > 0 else "UNDER"
                    f.write(f"   {pred['away_team']} @ {pred['home_team']}\n")
                    f.write(f"      Bet {direction} {pred['market_total']:.1f} (Edge: {edge:+.2f})\n\n")
            else:
                f.write("No games with significant edge (±0.5 goals) today\n")

        print(f"📁 Report saved to: {filename}\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate NHL daily totals predictions report')
    parser.add_argument('--date', help='Date (YYYY-MM-DD)', default=None)

    args = parser.parse_args()

    reporter = NHLDailyTotalsReport()
    reporter.generate_report(args.date)
