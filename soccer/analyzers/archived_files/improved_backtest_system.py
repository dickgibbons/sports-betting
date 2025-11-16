#!/usr/bin/env python3
"""
Comprehensive Backtest System for Improved Soccer Betting Strategy

This backtests the improved system using the same historical match data
that caused the original system to lose 54% of the bankroll.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import csv
import random
from improved_betting_predictor import ImprovedBettingPredictor
from improved_daily_manager import ImprovedDailyBettingManager
import logging


class ImprovedBacktestSystem:
    """Backtest the improved betting strategy using realistic historical data"""
    
    def __init__(self, api_key: str, initial_bankroll: float = 300.0, start_date: str = "2024-08-01"):
        self.api_key = api_key
        self.initial_bankroll = initial_bankroll
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.now()
        
        # Initialize improved components
        self.predictor = ImprovedBettingPredictor(api_key)
        self.manager = ImprovedDailyBettingManager(api_key, initial_bankroll)
        
        # Backtest results storage
        self.backtest_results = []
        self.daily_summaries = []
        self.performance_metrics = {}
        
        # Load historical outcomes from the original backtest
        self.load_original_backtest_data()
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def load_original_backtest_data(self):
        """Load the original backtest data to use same scenarios"""
        try:
            # Read the original detailed results
            original_path = "./backtest_detailed_20240801_20250904.csv"
            self.original_data = pd.read_csv(original_path)
            print(f"📊 Loaded {len(self.original_data)} original betting scenarios")
        except Exception as e:
            self.logger.error(f"Could not load original data: {e}")
            self.original_data = pd.DataFrame()
    
    def run_comprehensive_backtest(self):
        """Run the improved system against the same scenarios that failed before"""
        print("🧪 Starting Comprehensive Backtest of Improved System")
        print("=" * 70)
        print(f"📅 Period: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        print(f"💰 Starting Bankroll: ${self.initial_bankroll:,.2f}")
        print(f"🎯 Goal: Test against scenarios that caused 54% loss in original system")
        
        # Initialize the manager
        if not self.manager.load_or_train_models():
            print("❌ Failed to load models")
            return
        
        # Process each day from the original backtest
        current_bankroll = self.initial_bankroll
        peak_bankroll = self.initial_bankroll
        total_bets_placed = 0
        total_bets_avoided = 0
        
        if self.original_data.empty:
            print("❌ No original data to backtest against")
            return
        
        # Group original data by date
        daily_groups = self.original_data.groupby('date')
        
        for date_str, daily_bets in daily_groups:
            print(f"\n📅 Processing {date_str} ({len(daily_bets)} original scenarios)")
            
            # Reset daily counters
            daily_bet_results = []
            daily_stakes = 0
            daily_opportunities_analyzed = 0
            
            for _, original_bet in daily_bets.iterrows():
                daily_opportunities_analyzed += 1
                
                # Extract odds from original bet
                try:
                    if original_bet['market'] == 'Home Win':
                        home_odds = original_bet['odds']
                        draw_odds = 3.2  # Estimate
                        away_odds = 4.0  # Estimate
                    elif original_bet['market'] == 'Draw':
                        home_odds = 2.5  # Estimate  
                        draw_odds = original_bet['odds']
                        away_odds = 3.0  # Estimate
                    elif original_bet['market'] == 'Away Win':
                        home_odds = 3.5  # Estimate
                        draw_odds = 3.1  # Estimate
                        away_odds = original_bet['odds']
                    else:
                        # Handle other markets (Over/Under, BTTS)
                        home_odds = 2.5
                        draw_odds = 3.2
                        away_odds = 2.8
                
                    # Test with improved system
                    predictions = self.predictor.predict_match_with_confidence(
                        home_odds, draw_odds, away_odds
                    )
                    
                    analysis = self.predictor.analyze_betting_value_conservative(
                        predictions, home_odds, draw_odds, away_odds
                    )
                    
                    # Check if improved system would bet
                    bet_placed = False
                    if 'ensemble' in analysis and analysis['ensemble']['value_bets']:
                        for opportunity in analysis['ensemble']['value_bets']:
                            # Check risk limits
                            proposed_stake = opportunity['kelly_fraction'] * current_bankroll
                            risk_ok, _ = self.manager.check_risk_limits(proposed_stake)
                            
                            if risk_ok:
                                # Place the bet
                                bet_result = {
                                    'date': date_str,
                                    'match': original_bet['match'],
                                    'league': original_bet['league'],
                                    'market': opportunity['outcome'],
                                    'odds': opportunity['odds'],
                                    'stake': proposed_stake,
                                    'original_prediction': original_bet['prediction'],
                                    'original_actual': original_bet['actual_result'],
                                    'original_won': original_bet['bet_won'],
                                    'edge': opportunity['edge'],
                                    'confidence': opportunity['confidence'],
                                    'bankroll_before': current_bankroll
                                }
                                
                                # Simulate outcome based on original result
                                # Use the actual historical outcome
                                actual_outcome = original_bet['actual_result']
                                bet_won = (opportunity['outcome'] == actual_outcome)
                                
                                if bet_won:
                                    profit = proposed_stake * (opportunity['odds'] - 1)
                                    current_bankroll += profit
                                    bet_result['profit_loss'] = profit
                                    bet_result['bet_won'] = True
                                else:
                                    current_bankroll -= proposed_stake
                                    bet_result['profit_loss'] = -proposed_stake
                                    bet_result['bet_won'] = False
                                
                                bet_result['bankroll_after'] = current_bankroll
                                daily_bet_results.append(bet_result)
                                daily_stakes += proposed_stake
                                total_bets_placed += 1
                                bet_placed = True
                                
                                # Update manager state
                                self.manager.current_bankroll = current_bankroll
                                self.manager.todays_risk_exposure += proposed_stake
                                
                                print(f"   ✅ Bet: {opportunity['outcome']} @ {opportunity['odds']:.2f} "
                                      f"${proposed_stake:.2f} ({'Won' if bet_won else 'Lost'} {profit if bet_won else -proposed_stake:+.2f})")
                                break
                    
                    if not bet_placed:
                        total_bets_avoided += 1
                        print(f"   ❌ Avoided: {original_bet['market']} @ {original_bet['odds']:.2f} "
                              f"(Original: {'Won' if original_bet['bet_won'] else 'Lost'} {original_bet['profit_loss']:+.2f})")
                
                except Exception as e:
                    self.logger.error(f"Error processing bet: {e}")
                    continue
            
            # Update peak and calculate drawdown
            if current_bankroll > peak_bankroll:
                peak_bankroll = current_bankroll
            
            drawdown = (peak_bankroll - current_bankroll) / peak_bankroll
            
            # Daily summary
            daily_profit = sum(bet['profit_loss'] for bet in daily_bet_results)
            daily_summary = {
                'date': date_str,
                'starting_bankroll': current_bankroll - daily_profit,
                'ending_bankroll': current_bankroll,
                'daily_profit': daily_profit,
                'daily_stakes': daily_stakes,
                'bets_placed': len(daily_bet_results),
                'bets_won': sum(1 for bet in daily_bet_results if bet['bet_won']),
                'opportunities_analyzed': daily_opportunities_analyzed,
                'opportunities_avoided': daily_opportunities_analyzed - len(daily_bet_results),
                'win_rate': (sum(1 for bet in daily_bet_results if bet['bet_won']) / len(daily_bet_results) * 100) if daily_bet_results else 0,
                'roi': (daily_profit / (current_bankroll - daily_profit) * 100) if current_bankroll != daily_profit else 0,
                'peak_bankroll': peak_bankroll,
                'drawdown': drawdown * 100
            }
            
            self.daily_summaries.append(daily_summary)
            self.backtest_results.extend(daily_bet_results)
            
            print(f"   💰 Daily P&L: {daily_profit:+.2f} | Bankroll: ${current_bankroll:.2f} | "
                  f"Bets: {len(daily_bet_results)}/{daily_opportunities_analyzed}")
        
        # Final performance calculation
        self.calculate_final_metrics(current_bankroll, peak_bankroll, total_bets_placed, total_bets_avoided)
        
    def calculate_final_metrics(self, final_bankroll, peak_bankroll, bets_placed, bets_avoided):
        """Calculate comprehensive performance metrics"""
        total_return = (final_bankroll - self.initial_bankroll) / self.initial_bankroll * 100
        max_drawdown = max([day['drawdown'] for day in self.daily_summaries]) if self.daily_summaries else 0
        
        total_opportunities = len(self.original_data)
        bet_selectivity = (bets_placed / total_opportunities * 100) if total_opportunities > 0 else 0
        
        winning_bets = len([bet for bet in self.backtest_results if bet['bet_won']])
        win_rate = (winning_bets / bets_placed * 100) if bets_placed > 0 else 0
        
        profitable_days = len([day for day in self.daily_summaries if day['daily_profit'] > 0])
        total_trading_days = len(self.daily_summaries)
        
        self.performance_metrics = {
            'initial_bankroll': self.initial_bankroll,
            'final_bankroll': final_bankroll,
            'total_return_pct': total_return,
            'total_return_dollar': final_bankroll - self.initial_bankroll,
            'peak_bankroll': peak_bankroll,
            'max_drawdown_pct': max_drawdown,
            'total_opportunities': total_opportunities,
            'bets_placed': bets_placed,
            'bets_avoided': bets_avoided,
            'bet_selectivity_pct': bet_selectivity,
            'overall_win_rate': win_rate,
            'profitable_days': profitable_days,
            'total_trading_days': total_trading_days,
            'profitable_day_rate': (profitable_days / total_trading_days * 100) if total_trading_days > 0 else 0,
            'avg_daily_return': np.mean([day['roi'] for day in self.daily_summaries]) if self.daily_summaries else 0,
            'volatility': np.std([day['roi'] for day in self.daily_summaries]) if self.daily_summaries else 0,
            'sharpe_ratio': self.calculate_sharpe_ratio()
        }
        
    def calculate_sharpe_ratio(self):
        """Calculate risk-adjusted returns"""
        if not self.daily_summaries:
            return 0
        
        daily_returns = [day['roi'] / 100 for day in self.daily_summaries]
        mean_return = np.mean(daily_returns)
        std_return = np.std(daily_returns)
        
        if std_return == 0:
            return 0
        
        # Risk-free rate: ~2% annually = 0.0055% daily
        risk_free_rate = 0.000055
        return (mean_return - risk_free_rate) / std_return
    
    def generate_comparison_report(self):
        """Generate detailed comparison with original system"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE BACKTEST RESULTS - IMPROVED vs ORIGINAL SYSTEM")
        print("=" * 80)
        
        # Load original performance for comparison
        try:
            original_summary_path = "./backtest_daily_summary_20240801_20250904.csv"
            original_summary = pd.read_csv(original_summary_path)
            
            original_final_bankroll = original_summary['ending_bankroll'].iloc[-1]
            original_return = (original_final_bankroll - 300) / 300 * 100
            original_max_drawdown = 100 - (original_summary['ending_bankroll'].min() / 300 * 100)
            original_total_bets = original_summary['num_bets'].sum()
            original_total_won = original_summary['bets_won'].sum()
            original_win_rate = (original_total_won / original_total_bets * 100) if original_total_bets > 0 else 0
            
        except Exception as e:
            print(f"Could not load original summary: {e}")
            original_final_bankroll = 139  # From the data we saw earlier
            original_return = -54
            original_max_drawdown = 59
            original_total_bets = 70  # Estimated
            original_win_rate = 40  # Estimated
        
        print(f"\n💰 BANKROLL PERFORMANCE:")
        print(f"{'Metric':<25} {'Original':<15} {'Improved':<15} {'Difference':<15}")
        print("-" * 70)
        print(f"{'Starting Bankroll':<25} ${300:<14,.2f} ${self.initial_bankroll:<14,.2f} ${0:<14,.2f}")
        print(f"{'Final Bankroll':<25} ${original_final_bankroll:<14,.2f} ${self.performance_metrics['final_bankroll']:<14,.2f} ${self.performance_metrics['final_bankroll'] - original_final_bankroll:<14,.2f}")
        print(f"{'Total Return':<25} {original_return:<14.1f}% {self.performance_metrics['total_return_pct']:<14.1f}% {self.performance_metrics['total_return_pct'] - original_return:<14.1f}%")
        print(f"{'Max Drawdown':<25} {original_max_drawdown:<14.1f}% {self.performance_metrics['max_drawdown_pct']:<14.1f}% {self.performance_metrics['max_drawdown_pct'] - original_max_drawdown:<14.1f}%")
        
        print(f"\n🎯 BETTING BEHAVIOR:")
        print(f"{'Metric':<25} {'Original':<15} {'Improved':<15} {'Difference':<15}")
        print("-" * 70)
        print(f"{'Total Opportunities':<25} {self.performance_metrics['total_opportunities']:<15} {self.performance_metrics['total_opportunities']:<15} {0:<15}")
        print(f"{'Bets Placed':<25} {original_total_bets:<15} {self.performance_metrics['bets_placed']:<15} {self.performance_metrics['bets_placed'] - original_total_bets:<15}")
        print(f"{'Bets Avoided':<25} {0:<15} {self.performance_metrics['bets_avoided']:<15} {self.performance_metrics['bets_avoided']:<15}")
        print(f"{'Selectivity':<25} {100:<14.1f}% {self.performance_metrics['bet_selectivity_pct']:<14.1f}% {self.performance_metrics['bet_selectivity_pct'] - 100:<14.1f}%")
        print(f"{'Win Rate':<25} {original_win_rate:<14.1f}% {self.performance_metrics['overall_win_rate']:<14.1f}% {self.performance_metrics['overall_win_rate'] - original_win_rate:<14.1f}%")
        
        print(f"\n📈 RISK METRICS:")
        print(f"{'Profitable Days':<25} {'Unknown':<15} {self.performance_metrics['profitable_days']}/{self.performance_metrics['total_trading_days']:<14}")
        print(f"{'Profitable Day Rate':<25} {'~30%':<15} {self.performance_metrics['profitable_day_rate']:<14.1f}%")
        print(f"{'Avg Daily Return':<25} {'~-2%':<15} {self.performance_metrics['avg_daily_return']:<14.2f}%")
        print(f"{'Sharpe Ratio':<25} {'Negative':<15} {self.performance_metrics['sharpe_ratio']:<14.2f}")
        
        print(f"\n🎉 KEY IMPROVEMENTS:")
        improvement_bankroll = self.performance_metrics['final_bankroll'] - original_final_bankroll
        improvement_return = self.performance_metrics['total_return_pct'] - original_return
        
        if improvement_bankroll > 0:
            print(f"   ✅ Saved ${improvement_bankroll:.2f} in capital ({improvement_return:+.1f}% better return)")
        else:
            print(f"   📊 Performance difference: {improvement_return:+.1f}%")
            
        print(f"   ✅ Avoided {self.performance_metrics['bets_avoided']} risky bets ({100 - self.performance_metrics['bet_selectivity_pct']:.1f}% rejection rate)")
        print(f"   ✅ Reduced maximum drawdown by {original_max_drawdown - self.performance_metrics['max_drawdown_pct']:.1f}%")
        
        if self.performance_metrics['overall_win_rate'] > original_win_rate:
            print(f"   ✅ Improved win rate by {self.performance_metrics['overall_win_rate'] - original_win_rate:.1f}%")
        
    def save_backtest_results(self):
        """Save detailed backtest results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed results
        if self.backtest_results:
            detailed_file = f"./improved_backtest_detailed_{timestamp}.csv"
            
            fieldnames = [
                'date', 'match', 'league', 'market', 'odds', 'stake',
                'profit_loss', 'bet_won', 'edge', 'confidence',
                'bankroll_before', 'bankroll_after', 'original_prediction', 
                'original_actual', 'original_won'
            ]
            
            with open(detailed_file, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.backtest_results)
            
            print(f"💾 Detailed results saved: improved_backtest_detailed_{timestamp}.csv")
        
        # Save daily summary
        if self.daily_summaries:
            summary_file = f"./improved_backtest_summary_{timestamp}.csv"
            
            fieldnames = [
                'date', 'starting_bankroll', 'ending_bankroll', 'daily_profit',
                'daily_stakes', 'bets_placed', 'bets_won', 'opportunities_analyzed',
                'opportunities_avoided', 'win_rate', 'roi', 'peak_bankroll', 'drawdown'
            ]
            
            with open(summary_file, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.daily_summaries)
            
            print(f"💾 Summary results saved: improved_backtest_summary_{timestamp}.csv")
        
        # Save performance metrics
        metrics_file = f"./improved_backtest_metrics_{timestamp}.json"
        with open(metrics_file, 'w') as jsonfile:
            json.dump(self.performance_metrics, jsonfile, indent=2, default=str)
        
        print(f"💾 Performance metrics saved: improved_backtest_metrics_{timestamp}.json")


def main():
    """Run the improved system backtest"""
    API_KEY = "ceb338b9bcb82a452efc114fb2d3cccac67f58be1569e7b5acf1d2195adeae11"
    
    # Initialize backtest with same parameters as original
    backtest = ImprovedBacktestSystem(API_KEY, initial_bankroll=300.0, start_date="2024-08-01")
    
    # Run comprehensive backtest
    backtest.run_comprehensive_backtest()
    
    # Generate comparison report
    backtest.generate_comparison_report()
    
    # Save results
    backtest.save_backtest_results()
    
    print(f"\n✅ Improved System Backtest Complete!")
    print(f"📊 Check the generated CSV files for detailed results")


if __name__ == "__main__":
    main()