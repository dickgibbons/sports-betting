#!/usr/bin/env python3
"""
NHL Historical Backtest with Bet Type Tracking
Backtests predictions against historical results and tracks performance by bet type
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pickle
import sys
import os
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import seaborn as sns

# Import existing NHL data and prediction modules
from nhl_enhanced_data import NHLEnhancedData
from bet_recommendations_enhanced import NHLBetRecommendationsGenerator

class NHLHistoricalBacktest:
    """Backtest NHL predictions with bet type performance tracking"""

    def __init__(self, start_date: str, end_date: str):
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d')
        self.data = NHLEnhancedData()
        self.generator = NHLBet RecommendationsGenerator(min_edge=0.10, min_confidence=0.62)

        self.bankroll = 1000.0
        self.initial_bankroll = 1000.0
        self.kelly_fraction = 0.25  # Quarter Kelly
        self.max_bet_pct = 0.05  # Max 5% of bankroll per bet

        # Track all bets
        self.all_bets = []
        self.daily_summary = []

    def run_backtest(self):
        """Run complete backtest"""

        print("🏒 NHL HISTORICAL BACKTEST")
        print("=" * 70)
        print(f"📅 Period: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        print(f"💰 Starting Bankroll: ${self.initial_bankroll:.2f}")
        print("=" * 70)
        print()

        current_date = self.start_date

        while current_date <= self.end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            self._backtest_date(date_str)
            current_date += timedelta(days=1)

        self._generate_reports()

    def _backtest_date(self, date_str: str):
        """Backtest a single date"""

        print(f"\n📅 Backtesting {date_str}...")

        # Get historical games for this date
        games = self._get_historical_games(date_str)

        if not games:
            print(f"   ⚠️  No games found for {date_str}")
            return

        print(f"   Found {len(games)} games")

        # Generate predictions for each game
        date_bets = []

        for game in games:
            try:
                predictions = self._generate_predictions(game)

                # Evaluate each prediction against actual result
                for pred in predictions:
                    actual_result = self._get_actual_result(game, pred['bet_type'])
                    is_correct = self._evaluate_bet(pred, actual_result, game)

                    # Calculate bet size using Kelly Criterion
                    bet_size = self._calculate_bet_size(pred['confidence'], pred['odds'])

                    # Calculate profit/loss
                    if is_correct:
                        profit = bet_size * (pred['odds'] - 1)
                    else:
                        profit = -bet_size

                    self.bankroll += profit

                    # Record bet
                    bet_record = {
                        'date': date_str,
                        'home_team': game['home_team'],
                        'away_team': game['away_team'],
                        'bet_type': pred['bet_type'],
                        'pick': pred['pick'],
                        'odds': pred['odds'],
                        'confidence': pred['confidence'],
                        'edge': pred['edge'],
                        'stake': bet_size,
                        'actual_home_score': game['home_score'],
                        'actual_away_score': game['away_score'],
                        'correct': is_correct,
                        'profit': profit,
                        'bankroll': self.bankroll
                    }

                    date_bets.append(bet_record)
                    self.all_bets.append(bet_record)

            except Exception as e:
                print(f"   Error processing game {game['home_team']} vs {game['away_team']}: {e}")
                continue

        # Daily summary
        if date_bets:
            wins = sum(1 for bet in date_bets if bet['correct'])
            losses = len(date_bets) - wins
            win_rate = wins / len(date_bets) if date_bets else 0
            daily_profit = sum(bet['profit'] for bet in date_bets)
            daily_roi = (daily_profit / sum(bet['stake'] for bet in date_bets)) if date_bets else 0

            self.daily_summary.append({
                'date': date_str,
                'bets': len(date_bets),
                'wins': wins,
                'losses': losses,
                'win_rate': win_rate,
                'profit': daily_profit,
                'roi': daily_roi,
                'bankroll': self.bankroll
            })

            print(f"   📊 Bets: {len(date_bets)} | Wins: {wins} | Losses: {losses}")
            print(f"   Win Rate: {win_rate*100:.1f}% | P/L: ${daily_profit:+.2f} | Bankroll: ${self.bankroll:.2f}")

    def _get_historical_games(self, date_str: str) -> List[Dict]:
        """Fetch historical NHL games and scores"""
        # This would fetch from NHL API or stored data
        # For now, returning empty - you'll need to implement NHL API calls
        # or load from a historical database

        # Placeholder - implement NHL API historical data fetch
        return []

    def _generate_predictions(self, game: Dict) -> List[Dict]:
        """Generate predictions for a game"""

        predictions = []

        # Use existing bet generator (simplified)
        # You'd call your existing prediction models here

        # Moneyline predictions
        home_win_prob = 0.55  # Placeholder - use your models
        away_win_prob = 0.45

        if home_win_prob > 0.58:
            predictions.append({
                'bet_type': 'Moneyline',
                'pick': game['home_team'],
                'odds': 1.90,
                'confidence': home_win_prob,
                'edge': (home_win_prob * 1.90 - 1)
            })

        # Team totals predictions
        home_goals_pred = 3.2  # Placeholder
        away_goals_pred = 2.8

        if home_goals_pred > 2.7:
            predictions.append({
                'bet_type': 'Team Total O/U 2.5',
                'pick': f"{game['home_team']} Over 2.5",
                'odds': 1.90,
                'confidence': 0.75,
                'edge': 0.15
            })

        # Game totals
        game_total_pred = home_goals_pred + away_goals_pred

        if game_total_pred > 6.2:
            predictions.append({
                'bet_type': 'Game Total O/U 6.5',
                'pick': 'Over 6.5',
                'odds': 1.90,
                'confidence': 0.72,
                'edge': 0.12
            })

        # P1 totals
        p1_goals_pred = 1.9  # Placeholder

        if p1_goals_pred > 1.7:
            predictions.append({
                'bet_type': 'P1 Game Total O/U 1.5',
                'pick': 'Over 1.5',
                'odds': 1.90,
                'confidence': 0.68,
                'edge': 0.10
            })

        return predictions

    def _get_actual_result(self, game: Dict, bet_type: str) -> Dict:
        """Get actual result for bet evaluation"""

        return {
            'home_score': game['home_score'],
            'away_score': game['away_score'],
            'p1_home_score': game.get('p1_home_score', 0),
            'p1_away_score': game.get('p1_away_score', 0)
        }

    def _evaluate_bet(self, prediction: Dict, actual: Dict, game: Dict) -> bool:
        """Evaluate if prediction was correct"""

        bet_type = prediction['bet_type']
        pick = prediction['pick']

        home_score = actual['home_score']
        away_score = actual['away_score']

        # Moneyline
        if bet_type == 'Moneyline':
            if pick == game['home_team']:
                return home_score > away_score
            else:
                return away_score > home_score

        # Team totals
        elif 'Team Total O/U 2.5' in bet_type:
            if 'Over' in pick:
                if game['home_team'] in pick:
                    return home_score > 2.5
                else:
                    return away_score > 2.5
            else:
                if game['home_team'] in pick:
                    return home_score < 2.5
                else:
                    return away_score < 2.5

        # Game totals
        elif 'Game Total O/U' in bet_type:
            total = home_score + away_score
            if 'Over' in pick:
                threshold = float(bet_type.split('O/U')[1].strip())
                return total > threshold
            else:
                threshold = float(bet_type.split('O/U')[1].strip())
                return total < threshold

        # P1 totals
        elif 'P1 Game Total' in bet_type:
            p1_total = actual['p1_home_score'] + actual['p1_away_score']
            if 'Over 1.5' in pick:
                return p1_total > 1.5
            else:
                return p1_total < 1.5

        return False

    def _calculate_bet_size(self, confidence: float, odds: float) -> float:
        """Calculate bet size using Kelly Criterion"""

        # Kelly = (confidence * odds - 1) / (odds - 1)
        kelly = (confidence * odds - 1) / (odds - 1)

        # Apply fraction and limits
        bet_fraction = kelly * self.kelly_fraction
        bet_fraction = max(0, min(bet_fraction, self.max_bet_pct))

        return self.bankroll * bet_fraction

    def _generate_reports(self):
        """Generate comprehensive backtest reports"""

        print("\n" + "=" * 70)
        print("📊 BACKTEST RESULTS")
        print("=" * 70)

        # Overall performance
        total_bets = len(self.all_bets)
        wins = sum(1 for bet in self.all_bets if bet['correct'])
        losses = total_bets - wins
        win_rate = wins / total_bets if total_bets > 0 else 0

        total_profit = self.bankroll - self.initial_bankroll
        roi = (total_profit / self.initial_bankroll) * 100

        print(f"\n💰 FINANCIAL PERFORMANCE:")
        print(f"   Starting Bankroll: ${self.initial_bankroll:.2f}")
        print(f"   Ending Bankroll: ${self.bankroll:.2f}")
        print(f"   Total Profit/Loss: ${total_profit:+.2f}")
        print(f"   ROI: {roi:+.1f}%")

        print(f"\n📊 BETTING STATISTICS:")
        print(f"   Total Bets: {total_bets}")
        print(f"   Wins: {wins} | Losses: {losses}")
        print(f"   Win Rate: {win_rate*100:.1f}%")

        # Performance by bet type
        print(f"\n📊 PERFORMANCE BY BET TYPE:")

        df_bets = pd.DataFrame(self.all_bets)

        for bet_type in df_bets['bet_type'].unique():
            type_bets = df_bets[df_bets['bet_type'] == bet_type]
            type_wins = type_bets['correct'].sum()
            type_total = len(type_bets)
            type_win_rate = type_wins / type_total if type_total > 0 else 0
            type_profit = type_bets['profit'].sum()
            type_roi = (type_profit / type_bets['stake'].sum()) * 100 if type_total > 0 else 0

            print(f"   {bet_type}: {type_total} bets | {type_win_rate*100:.1f}% win rate | ${type_profit:+.2f} | ROI: {type_roi:+.1f}%")

        # Save CSVs
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Detailed bets
        df_bets.to_csv(f'nhl_backtest_detailed_{timestamp}.csv', index=False)
        print(f"\n✅ Detailed results saved to: nhl_backtest_detailed_{timestamp}.csv")

        # Daily summary
        df_daily = pd.DataFrame(self.daily_summary)
        df_daily.to_csv(f'nhl_backtest_daily_{timestamp}.csv', index=False)
        print(f"✅ Daily summary saved to: nhl_backtest_daily_{timestamp}.csv")

        # Generate charts
        self._generate_charts(df_bets, df_daily, timestamp)

    def _generate_charts(self, df_bets, df_daily, timestamp):
        """Generate performance charts"""

        fig, axes = plt.subplots(2, 2, figsize=(15, 10))

        # Bankroll growth
        axes[0, 0].plot(df_daily.index, df_daily['bankroll'])
        axes[0, 0].set_title('Bankroll Growth Over Time')
        axes[0, 0].set_xlabel('Days')
        axes[0, 0].set_ylabel('Bankroll ($)')
        axes[0, 0].grid(True)

        # Win rate by bet type
        win_rates = df_bets.groupby('bet_type')['correct'].mean()
        win_rates.plot(kind='bar', ax=axes[0, 1])
        axes[0, 1].set_title('Win Rate by Bet Type')
        axes[0, 1].set_ylabel('Win Rate')
        axes[0, 1].set_ylim([0, 1])
        axes[0, 1].axhline(y=0.5, color='r', linestyle='--', label='Break-even')
        axes[0, 1].legend()

        # ROI by bet type
        roi_by_type = df_bets.groupby('bet_type').apply(
            lambda x: (x['profit'].sum() / x['stake'].sum()) * 100
        )
        roi_by_type.plot(kind='bar', ax=axes[1, 0])
        axes[1, 0].set_title('ROI by Bet Type')
        axes[1, 0].set_ylabel('ROI (%)')
        axes[1, 0].axhline(y=0, color='r', linestyle='--')

        # Daily win rate
        axes[1, 1].plot(df_daily.index, df_daily['win_rate'])
        axes[1, 1].set_title('Daily Win Rate')
        axes[1, 1].set_xlabel('Days')
        axes[1, 1].set_ylabel('Win Rate')
        axes[1, 1].set_ylim([0, 1])
        axes[1, 1].axhline(y=0.5, color='r', linestyle='--')
        axes[1, 1].grid(True)

        plt.tight_layout()
        plt.savefig(f'nhl_backtest_charts_{timestamp}.png', dpi=150)
        print(f"✅ Charts saved to: nhl_backtest_charts_{timestamp}.png")


def main():
    """Run backtest"""

    if len(sys.argv) < 3:
        print("Usage: python3 nhl_historical_backtest.py START_DATE END_DATE")
        print("Example: python3 nhl_historical_backtest.py 2025-10-01 2025-10-19")
        sys.exit(1)

    start_date = sys.argv[1]
    end_date = sys.argv[2]

    backtest = NHLHistoricalBacktest(start_date, end_date)
    backtest.run_backtest()


if __name__ == '__main__':
    main()
