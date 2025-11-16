#!/usr/bin/env python3
"""
Backtesting System for Soccer Betting Strategy

Tests the betting system from August 1st onwards, showing:
- What bets would have been placed
- Exact stake amounts using Kelly Criterion
- Actual results and profit/loss
- Daily and cumulative bankroll progression
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from csv_predictions_generator import CSVPredictionsGenerator
from daily_bankroll_manager import DailyBankrollManager
import random


class BacktestSystem:
    """Backtest the betting strategy with historical data simulation"""
    
    def __init__(self, api_key: str, initial_bankroll: float = 300.0, start_date: str = "2024-08-01"):
        self.api_key = api_key
        self.initial_bankroll = initial_bankroll
        self.current_bankroll = initial_bankroll
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.now()
        
        self.manager = DailyBankrollManager(api_key, initial_bankroll)
        self.backtest_results = []
        self.daily_summaries = []
        
        # Historical match results simulation data
        # In real implementation, this would come from actual historical API data
        self.historical_outcomes = self.generate_historical_data()
        
    def generate_historical_data(self):
        """Generate historical match outcomes for backtesting"""
        
        # Simulate historical matches for each day since August 1st
        historical_data = {}
        current_date = self.start_date
        
        print("📊 Generating historical match data for backtesting...")
        
        while current_date <= self.end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            
            # Generate 3-8 matches per day (realistic for major leagues)
            num_matches = random.randint(3, 8)
            daily_matches = []
            
            leagues = ['Premier League', 'La Liga', 'Bundesliga', 'Serie A', 'Ligue 1', 'MLS', 'Liga MX']
            teams = {
                'Premier League': [
                    ('Manchester City', 'Arsenal'), ('Liverpool', 'Chelsea'), ('Tottenham', 'Manchester United'),
                    ('Newcastle', 'Brighton'), ('Aston Villa', 'West Ham'), ('Crystal Palace', 'Fulham')
                ],
                'La Liga': [
                    ('Real Madrid', 'Barcelona'), ('Atletico Madrid', 'Valencia'), ('Sevilla', 'Real Betis'),
                    ('Villarreal', 'Athletic Bilbao'), ('Real Sociedad', 'Getafe'), ('Osasuna', 'Celta Vigo')
                ],
                'Bundesliga': [
                    ('Bayern Munich', 'Borussia Dortmund'), ('RB Leipzig', 'Bayer Leverkusen'), 
                    ('Eintracht Frankfurt', 'VfB Stuttgart'), ('Borussia Monchengladbach', 'Wolfsburg')
                ],
                'Serie A': [
                    ('Juventus', 'AC Milan'), ('Inter Milan', 'Napoli'), ('AS Roma', 'Lazio'),
                    ('Atalanta', 'Fiorentina'), ('Bologna', 'Torino')
                ],
                'MLS': [
                    ('LA Galaxy', 'LAFC'), ('Inter Miami', 'New York City FC'), ('Seattle Sounders', 'Portland Timbers')
                ],
                'Liga MX': [
                    ('Club America', 'Chivas'), ('Cruz Azul', 'Pumas'), ('Monterrey', 'Tigres')
                ]
            }
            
            for i in range(num_matches):
                league = random.choice(leagues)
                if league in teams:
                    home_team, away_team = random.choice(teams[league])
                    
                    # Generate realistic odds
                    home_odds = round(random.uniform(1.5, 4.5), 2)
                    away_odds = round(random.uniform(1.5, 4.5), 2)
                    draw_odds = round(random.uniform(2.8, 3.8), 2)
                    
                    # Generate other market odds
                    btts_yes_odds = round(random.uniform(1.6, 2.2), 2)
                    btts_no_odds = round(random.uniform(1.7, 2.3), 2)
                    over_25_odds = round(random.uniform(1.4, 2.5), 2)
                    under_25_odds = round(random.uniform(1.5, 2.8), 2)
                    
                    # Simulate actual match outcome based on odds probabilities
                    home_prob = 1 / home_odds
                    draw_prob = 1 / draw_odds  
                    away_prob = 1 / away_odds
                    
                    # Normalize probabilities
                    total_prob = home_prob + draw_prob + away_prob
                    home_prob /= total_prob
                    draw_prob /= total_prob
                    away_prob /= total_prob
                    
                    # Determine actual outcome
                    rand = random.random()
                    if rand < home_prob:
                        actual_result = 'Home Win'
                        home_score = random.choice([1, 2, 2, 3, 3, 4])
                        away_score = random.choice([0, 0, 1, 1, 2])
                    elif rand < home_prob + draw_prob:
                        actual_result = 'Draw'
                        score = random.choice([0, 1, 1, 2, 2])
                        home_score = away_score = score
                    else:
                        actual_result = 'Away Win'
                        away_score = random.choice([1, 2, 2, 3, 3, 4])
                        home_score = random.choice([0, 0, 1, 1, 2])
                    
                    total_goals = home_score + away_score
                    btts_result = home_score > 0 and away_score > 0
                    
                    match_data = {
                        'date': date_str,
                        'time': f"{random.randint(12, 22):02d}:00",
                        'league': league,
                        'home_team': home_team,
                        'away_team': away_team,
                        'home_odds': home_odds,
                        'draw_odds': draw_odds,
                        'away_odds': away_odds,
                        'btts_yes_odds': btts_yes_odds,
                        'btts_no_odds': btts_no_odds,
                        'over_25_odds': over_25_odds,
                        'under_25_odds': under_25_odds,
                        
                        # Actual results
                        'actual_result': actual_result,
                        'home_score': home_score,
                        'away_score': away_score,
                        'total_goals': total_goals,
                        'btts_actual': 'YES' if btts_result else 'NO',
                        'over_25_actual': 'OVER' if total_goals > 2.5 else 'UNDER'
                    }
                    
                    daily_matches.append(match_data)
            
            historical_data[date_str] = daily_matches
            current_date += timedelta(days=1)
        
        return historical_data
    
    def run_backtest(self, max_bets_per_day=5):
        """Run the complete backtest simulation"""
        
        print(f"🎯 Starting Backtest Simulation")
        print(f"=" * 50)
        print(f"📅 Period: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        print(f"💰 Starting Bankroll: ${self.initial_bankroll:.2f}")
        print(f"🎯 Max Bets Per Day: {max_bets_per_day}")
        print(f"📊 Days to Simulate: {(self.end_date - self.start_date).days + 1}")
        print("=" * 50)
        
        # Load models
        if not self.manager.load_models():
            print("⚠️  No models loaded - using basic calculations")
        
        current_date = self.start_date
        total_days = 0
        days_with_bets = 0
        total_bets = 0
        
        while current_date <= self.end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            total_days += 1
            
            if date_str in self.historical_outcomes:
                daily_matches = self.historical_outcomes[date_str]
                
                print(f"\n📅 {date_str} ({current_date.strftime('%A')})")
                print(f"💼 Bankroll: ${self.current_bankroll:.2f}")
                
                # Update manager's bankroll
                self.manager.current_bankroll = self.current_bankroll
                
                # Generate predictions for all matches
                daily_opportunities = []
                for match in daily_matches:
                    # Get predictions
                    prediction = self.manager.csv_generator.predict_betting_markets(match)
                    
                    # Get betting opportunities
                    opportunities = self.manager.evaluate_bet_opportunity(prediction)
                    
                    # Add actual results to opportunities
                    for opp in opportunities:
                        opp['actual_result'] = match['actual_result']
                        opp['home_score'] = match['home_score']
                        opp['away_score'] = match['away_score']
                        opp['btts_actual'] = match['btts_actual']
                        opp['over_25_actual'] = match['over_25_actual']
                        
                    daily_opportunities.extend(opportunities)
                
                if daily_opportunities:
                    # Sort by expected value and select top N
                    daily_opportunities.sort(key=lambda x: x['expected_value'], reverse=True)
                    selected_bets = daily_opportunities[:max_bets_per_day]
                    
                    # Apply daily risk limit
                    max_daily_risk = self.current_bankroll * 0.25
                    final_bets = []
                    daily_stakes = 0
                    
                    for bet in selected_bets:
                        if daily_stakes + bet['bet_size'] <= max_daily_risk:
                            final_bets.append(bet)
                            daily_stakes += bet['bet_size']
                    
                    if final_bets:
                        days_with_bets += 1
                        print(f"🎯 Selected {len(final_bets)} bets (${daily_stakes:.2f} total stakes)")
                        
                        # Process each bet
                        daily_profit = 0
                        daily_bets = []
                        
                        for i, bet in enumerate(final_bets, 1):
                            # Determine if bet won
                            bet_won = self.determine_bet_result(bet)
                            
                            if bet_won:
                                profit = bet['potential_profit']
                                print(f"   ✅ BET {i}: WON ${profit:.2f}")
                            else:
                                profit = -bet['bet_size']
                                print(f"   ❌ BET {i}: LOST ${bet['bet_size']:.2f}")
                            
                            daily_profit += profit
                            total_bets += 1
                            
                            # Record bet details
                            bet_record = {
                                'date': date_str,
                                'match': bet['match'],
                                'league': bet['league'],
                                'market': bet['market'],
                                'odds': bet['odds'],
                                'stake': bet['bet_size'],
                                'prediction': bet['market'],
                                'actual_result': bet['actual_result'],
                                'bet_won': bet_won,
                                'profit_loss': profit,
                                'bankroll_before': self.current_bankroll,
                                'bankroll_after': self.current_bankroll + profit,
                                'edge': bet['edge'],
                                'confidence': bet['confidence'],
                                'expected_value': bet['expected_value']
                            }
                            
                            self.backtest_results.append(bet_record)
                            daily_bets.append(bet_record)
                        
                        # Update bankroll
                        self.current_bankroll += daily_profit
                        
                        print(f"📊 Daily P&L: ${daily_profit:.2f}")
                        print(f"💼 New Bankroll: ${self.current_bankroll:.2f}")
                        
                        # Daily summary
                        daily_summary = {
                            'date': date_str,
                            'starting_bankroll': self.current_bankroll - daily_profit,
                            'num_bets': len(final_bets),
                            'total_stakes': daily_stakes,
                            'daily_profit': daily_profit,
                            'ending_bankroll': self.current_bankroll,
                            'roi': (daily_profit / daily_stakes * 100) if daily_stakes > 0 else 0,
                            'bets_won': sum(1 for bet in daily_bets if bet['bet_won']),
                            'win_rate': (sum(1 for bet in daily_bets if bet['bet_won']) / len(daily_bets)) * 100 if daily_bets else 0
                        }
                        self.daily_summaries.append(daily_summary)
                    else:
                        print("❌ No bets within risk limits")
                else:
                    print("❌ No opportunities found")
            
            current_date += timedelta(days=1)
        
        # Generate final results
        self.generate_backtest_report(total_days, days_with_bets, total_bets)
        return self.backtest_results
    
    def determine_bet_result(self, bet):
        """Determine if a bet won based on actual results"""
        
        market = bet['market']
        actual_result = bet['actual_result']
        
        # 1X2 Markets
        if market == 'Home Win':
            return actual_result == 'Home Win'
        elif market == 'Away Win':
            return actual_result == 'Away Win'
        elif market == 'Draw':
            return actual_result == 'Draw'
        
        # BTTS Markets
        elif market == 'BTTS Yes':
            return bet['btts_actual'] == 'YES'
        elif market == 'BTTS No':
            return bet['btts_actual'] == 'NO'
        
        # Goals Markets
        elif market == 'Over 2.5 Goals':
            return bet['over_25_actual'] == 'OVER'
        elif market == 'Under 2.5 Goals':
            return bet['over_25_actual'] == 'UNDER'
        
        # Default to loss if market not recognized
        return False
    
    def generate_backtest_report(self, total_days, days_with_bets, total_bets):
        """Generate comprehensive backtest report"""
        
        print(f"\n" + "=" * 70)
        print(f"📊 BACKTEST RESULTS SUMMARY")
        print(f"=" * 70)
        
        total_profit = self.current_bankroll - self.initial_bankroll
        total_roi = (total_profit / self.initial_bankroll) * 100
        
        # Overall performance
        print(f"\n💰 FINANCIAL PERFORMANCE:")
        print(f"   Starting Bankroll: ${self.initial_bankroll:.2f}")
        print(f"   Ending Bankroll: ${self.current_bankroll:.2f}")
        print(f"   Total Profit/Loss: ${total_profit:.2f}")
        print(f"   Total ROI: {total_roi:.2f}%")
        
        # Betting statistics
        if self.backtest_results:
            total_stakes = sum(bet['stake'] for bet in self.backtest_results)
            bets_won = sum(1 for bet in self.backtest_results if bet['bet_won'])
            win_rate = (bets_won / len(self.backtest_results)) * 100
            
            print(f"\n📊 BETTING STATISTICS:")
            print(f"   Total Days: {total_days}")
            print(f"   Days with Bets: {days_with_bets}")
            print(f"   Total Bets Placed: {total_bets}")
            print(f"   Average Bets per Day: {total_bets/days_with_bets:.1f}")
            print(f"   Total Amount Staked: ${total_stakes:.2f}")
            print(f"   Bets Won: {bets_won}")
            print(f"   Win Rate: {win_rate:.1f}%")
            print(f"   Average Stake: ${total_stakes/total_bets:.2f}")
            
            # Best and worst days
            if self.daily_summaries:
                best_day = max(self.daily_summaries, key=lambda x: x['daily_profit'])
                worst_day = min(self.daily_summaries, key=lambda x: x['daily_profit'])
                
                print(f"\n📈 BEST & WORST DAYS:")
                print(f"   Best Day: {best_day['date']} (+${best_day['daily_profit']:.2f})")
                print(f"   Worst Day: {worst_day['date']} (${worst_day['daily_profit']:.2f})")
                
                # Profitability streak
                profitable_days = sum(1 for day in self.daily_summaries if day['daily_profit'] > 0)
                profitability_rate = (profitable_days / len(self.daily_summaries)) * 100
                print(f"   Profitable Days: {profitable_days}/{len(self.daily_summaries)} ({profitability_rate:.1f}%)")
        
        # Market performance
        market_performance = {}
        for bet in self.backtest_results:
            market = bet['market']
            if market not in market_performance:
                market_performance[market] = {'bets': 0, 'won': 0, 'profit': 0, 'stakes': 0}
            
            market_performance[market]['bets'] += 1
            market_performance[market]['stakes'] += bet['stake']
            market_performance[market]['profit'] += bet['profit_loss']
            if bet['bet_won']:
                market_performance[market]['won'] += 1
        
        if market_performance:
            print(f"\n🎯 MARKET PERFORMANCE:")
            for market, stats in sorted(market_performance.items(), key=lambda x: x[1]['profit'], reverse=True):
                win_rate = (stats['won'] / stats['bets']) * 100
                roi = (stats['profit'] / stats['stakes']) * 100 if stats['stakes'] > 0 else 0
                print(f"   {market}: {stats['bets']} bets, {win_rate:.1f}% wins, ${stats['profit']:.2f} profit ({roi:.1f}% ROI)")
    
    def save_backtest_results(self):
        """Save detailed backtest results to CSV files"""
        
        if self.backtest_results:
            # Detailed bet-by-bet results
            results_df = pd.DataFrame(self.backtest_results)
            results_filename = f"backtest_detailed_{self.start_date.strftime('%Y%m%d')}_{self.end_date.strftime('%Y%m%d')}.csv"
            results_path = f"./{results_filename}"
            results_df.to_csv(results_path, index=False)
            print(f"\n💾 Detailed results saved to: {results_filename}")
            
            # Daily summaries
            if self.daily_summaries:
                summary_df = pd.DataFrame(self.daily_summaries)
                summary_filename = f"backtest_daily_summary_{self.start_date.strftime('%Y%m%d')}_{self.end_date.strftime('%Y%m%d')}.csv"
                summary_path = f"./{summary_filename}"
                summary_df.to_csv(summary_path, index=False)
                print(f"💾 Daily summaries saved to: {summary_filename}")
                
                return results_path, summary_path
        
        return None, None


def main():
    """Main function to run the backtest"""
    
    API_KEY = "ceb338b9bcb82a452efc114fb2d3cccac67f58be1569e7b5acf1d2195adeae11"
    INITIAL_BANKROLL = 300.0
    START_DATE = "2024-08-01"
    MAX_DAILY_BETS = 5
    
    print("🎯 Soccer Betting Strategy Backtest")
    print("=" * 45)
    print(f"📊 Testing period: {START_DATE} to present")
    print(f"💰 Starting bankroll: ${INITIAL_BANKROLL}")
    print(f"🎯 Maximum bets per day: {MAX_DAILY_BETS}")
    print(f"🧠 Using Kelly Criterion position sizing")
    print(f"⚖️  Maximum daily risk: 25% of bankroll")
    print("=" * 45)
    
    # Initialize and run backtest
    backtester = BacktestSystem(API_KEY, INITIAL_BANKROLL, START_DATE)
    
    # Set random seed for consistent results (remove in production)
    random.seed(42)
    np.random.seed(42)
    
    # Run the backtest
    results = backtester.run_backtest(MAX_DAILY_BETS)
    
    # Save results to files
    detailed_file, summary_file = backtester.save_backtest_results()
    
    print(f"\n🎉 Backtest Complete!")
    print(f"📁 Check your files:")
    if detailed_file:
        print(f"   📊 Detailed Results: {detailed_file.split('/')[-1]}")
    if summary_file:
        print(f"   📈 Daily Summary: {summary_file.split('/')[-1]}")
    
    print(f"\n💡 Use these files to:")
    print(f"   • Analyze bet-by-bet performance")
    print(f"   • Track daily bankroll progression") 
    print(f"   • Identify best performing markets")
    print(f"   • Evaluate risk management effectiveness")


if __name__ == "__main__":
    main()