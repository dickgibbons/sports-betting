#!/usr/bin/env python3
"""
Improved Daily Betting Manager

Enhanced features:
1. Strict position sizing with maximum daily exposure limits
2. Dynamic bankroll protection with drawdown controls
3. Portfolio-level risk management across multiple bets
4. Performance tracking and strategy adjustment
5. Emergency stop-loss mechanisms
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import csv
from improved_betting_predictor import ImprovedBettingPredictor
import logging
from typing import Dict, List, Tuple, Optional


class ImprovedDailyBettingManager:
    """Enhanced daily betting manager with comprehensive risk controls"""
    
    def __init__(self, api_key: str, initial_bankroll: float = 1000.0, model_path: str = "improved_soccer_models.pkl"):
        self.api_key = api_key
        self.initial_bankroll = initial_bankroll
        self.current_bankroll = initial_bankroll
        self.model_path = model_path
        
        # Risk management parameters
        self.max_daily_risk = 0.15  # Maximum 15% of bankroll at risk per day
        self.max_single_bet = 0.05  # Maximum 5% per individual bet
        self.max_concurrent_bets = 4  # Maximum 4 bets per day
        self.stop_loss_threshold = 0.25  # Stop if down 25% from peak
        self.min_bankroll_threshold = self.initial_bankroll * 0.5  # Emergency stop at 50% loss
        
        # Performance tracking
        self.performance_history = []
        self.daily_summaries = []
        self.peak_bankroll = initial_bankroll
        self.current_drawdown = 0.0
        
        # Betting state
        self.todays_bets = []
        self.todays_risk_exposure = 0.0
        self.last_bet_date = None
        
        # Initialize predictor
        self.predictor = ImprovedBettingPredictor(api_key)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        print(f"💰 Improved Daily Betting Manager initialized")
        print(f"🏦 Starting bankroll: ${self.current_bankroll:,.2f}")
        print(f"⚠️  Max daily risk: {self.max_daily_risk*100:.1f}%")
        print(f"🛡️ Stop loss threshold: {self.stop_loss_threshold*100:.1f}%")
    
    def load_or_train_models(self) -> bool:
        """Load existing models or train new ones"""
        try:
            if self.predictor.load_models(self.model_path):
                print("✅ Loaded existing prediction models")
                return True
        except Exception as e:
            self.logger.warning(f"Could not load models: {e}")
        
        print("🧠 Training new models...")
        try:
            # Train with major leagues
            LEAGUES = [1625, 1729, 1854]  # Premier League, La Liga, Bundesliga
            self.predictor.collect_and_train(LEAGUES, pages_per_league=2)
            self.predictor.save_models(self.model_path)
            print("✅ Models trained and saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to train models: {e}")
            return False
    
    def check_risk_limits(self, proposed_stake: float) -> Tuple[bool, str]:
        """Check if proposed bet meets all risk criteria"""
        current_date = datetime.now().date()
        
        # Reset daily counters if new day
        if self.last_bet_date != current_date:
            self.todays_bets = []
            self.todays_risk_exposure = 0.0
            self.last_bet_date = current_date
        
        # Check individual bet size
        if proposed_stake > self.current_bankroll * self.max_single_bet:
            return False, f"Exceeds maximum single bet limit ({self.max_single_bet*100:.1f}%)"
        
        # Check daily risk exposure
        new_total_risk = self.todays_risk_exposure + proposed_stake
        if new_total_risk > self.current_bankroll * self.max_daily_risk:
            return False, f"Exceeds daily risk limit ({self.max_daily_risk*100:.1f}%)"
        
        # Check number of bets
        if len(self.todays_bets) >= self.max_concurrent_bets:
            return False, f"Maximum {self.max_concurrent_bets} bets per day reached"
        
        # Check emergency stop loss
        if self.current_bankroll < self.min_bankroll_threshold:
            return False, f"Emergency stop: Bankroll below {self.min_bankroll_threshold:,.2f}"
        
        # Check drawdown stop loss
        if self.current_drawdown > self.stop_loss_threshold:
            return False, f"Stop loss triggered: {self.current_drawdown*100:.1f}% drawdown"
        
        return True, "Risk checks passed"
    
    def calculate_portfolio_kelly(self, opportunities: List[Dict]) -> List[Dict]:
        """Calculate Kelly fractions considering portfolio correlation"""
        if not opportunities:
            return []
        
        # Sort by expected value
        opportunities.sort(key=lambda x: x.get('expected_value', 0), reverse=True)
        
        # Take top opportunities that fit within risk limits
        selected_bets = []
        total_allocation = 0.0
        
        for opp in opportunities:
            base_kelly = opp.get('kelly_fraction', 0.02)
            
            # Reduce Kelly for portfolio diversification
            portfolio_adjustment = max(0.5, 1.0 - (len(selected_bets) * 0.15))
            adjusted_kelly = base_kelly * portfolio_adjustment
            
            # Check if this bet fits within remaining risk budget
            proposed_stake = adjusted_kelly * self.current_bankroll
            remaining_risk_budget = (self.max_daily_risk * self.current_bankroll) - total_allocation
            
            if proposed_stake <= remaining_risk_budget and total_allocation + proposed_stake <= self.current_bankroll * self.max_daily_risk:
                opp['adjusted_kelly'] = adjusted_kelly
                opp['proposed_stake'] = proposed_stake
                selected_bets.append(opp)
                total_allocation += proposed_stake
                
                # Don't allocate more than available daily risk
                if total_allocation >= self.current_bankroll * self.max_daily_risk * 0.9:  # Leave 10% buffer
                    break
        
        return selected_bets
    
    def analyze_daily_opportunities(self, matches: List[Dict]) -> List[Dict]:
        """Analyze all today's matches for betting opportunities"""
        opportunities = []
        
        print(f"🔍 Analyzing {len(matches)} matches for value...")
        
        for match in matches:
            try:
                home_odds = float(match.get('home_odds', 2.0))
                draw_odds = float(match.get('draw_odds', 3.0))
                away_odds = float(match.get('away_odds', 2.0))
                
                # Skip matches with suspicious odds
                if min(home_odds, draw_odds, away_odds) < 1.1 or max(home_odds, draw_odds, away_odds) > 15.0:
                    continue
                
                predictions = self.predictor.predict_match_with_confidence(home_odds, draw_odds, away_odds)
                analysis = self.predictor.analyze_betting_value_conservative(predictions, home_odds, draw_odds, away_odds)
                
                # Extract opportunities from ensemble model
                if 'ensemble' in analysis and analysis['ensemble']['value_bets']:
                    for bet in analysis['ensemble']['value_bets']:
                        opportunity = {
                            'match_info': match,
                            'market': bet['outcome'],
                            'odds': bet['odds'],
                            'model_probability': bet['model_probability'],
                            'implied_probability': bet['implied_probability'],
                            'edge': bet['edge'],
                            'kelly_fraction': bet['kelly_fraction'],
                            'expected_value': bet['expected_value'],
                            'confidence': bet['confidence'],
                            'risk_level': bet['risk_level']
                        }
                        opportunities.append(opportunity)
                        
            except Exception as e:
                self.logger.error(f"Error analyzing match {match}: {e}")
                continue
        
        return opportunities
    
    def execute_daily_strategy(self, matches: List[Dict]) -> Dict:
        """Execute the daily betting strategy"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        print(f"📅 Executing strategy for {current_date}")
        print(f"💰 Current bankroll: ${self.current_bankroll:,.2f}")
        print(f"📊 Drawdown: {self.current_drawdown*100:.1f}%")
        
        # Check if we should trade today
        if not self.should_bet_today():
            print("⏸️ Skipping betting today due to risk controls")
            return {'status': 'skipped', 'reason': 'Risk controls active'}
        
        # Analyze opportunities
        opportunities = self.analyze_daily_opportunities(matches)
        
        if not opportunities:
            print("❌ No value opportunities found today")
            return {'status': 'no_opportunities', 'opportunities_analyzed': len(matches)}
        
        print(f"✅ Found {len(opportunities)} potential value bets")
        
        # Calculate optimal portfolio
        selected_bets = self.calculate_portfolio_kelly(opportunities)
        
        if not selected_bets:
            print("❌ No bets pass portfolio risk management")
            return {'status': 'risk_filtered', 'opportunities_found': len(opportunities)}
        
        # Execute selected bets
        executed_bets = []
        total_stakes = 0.0
        
        for bet in selected_bets:
            stake = bet['proposed_stake']
            
            # Final risk check
            risk_ok, risk_msg = self.check_risk_limits(stake)
            if not risk_ok:
                print(f"❌ Bet rejected: {risk_msg}")
                continue
            
            # Record the bet
            bet_record = {
                'date': current_date,
                'time': datetime.now().strftime("%H:%M:%S"),
                'match': f"{bet['match_info'].get('home_team', 'Team A')} vs {bet['match_info'].get('away_team', 'Team B')}",
                'league': bet['match_info'].get('league', 'Unknown'),
                'market': bet['market'],
                'odds': bet['odds'],
                'stake': stake,
                'edge': bet['edge'],
                'confidence': bet['confidence'],
                'expected_value': bet['expected_value'],
                'model_probability': bet['model_probability'],
                'implied_probability': bet['implied_probability'],
                'bankroll_before': self.current_bankroll,
                'risk_level': bet['risk_level']
            }
            
            executed_bets.append(bet_record)
            self.todays_bets.append(bet_record)
            self.todays_risk_exposure += stake
            total_stakes += stake
            
            print(f"✅ Bet placed: {bet['market']} @ {bet['odds']:.2f} - ${stake:.2f} "
                  f"({bet['edge']*100:.1f}% edge)")
        
        # Save daily betting slip
        if executed_bets:
            self.save_daily_slip(executed_bets, current_date)
            
            print(f"\n📊 Daily Summary:")
            print(f"   💰 Total stakes: ${total_stakes:.2f} ({total_stakes/self.current_bankroll*100:.1f}% of bankroll)")
            print(f"   🎯 Number of bets: {len(executed_bets)}")
            print(f"   ⚖️ Risk exposure: {self.todays_risk_exposure/self.current_bankroll*100:.1f}%")
        
        return {
            'status': 'executed',
            'bets_placed': len(executed_bets),
            'total_stakes': total_stakes,
            'risk_exposure': self.todays_risk_exposure,
            'bets': executed_bets
        }
    
    def should_bet_today(self) -> bool:
        """Determine if we should place bets today based on performance"""
        # Don't bet if emergency stop triggered
        if self.current_bankroll < self.min_bankroll_threshold:
            return False
        
        # Don't bet if stop loss triggered
        if self.current_drawdown > self.stop_loss_threshold:
            return False
        
        # Reduce betting frequency if experiencing losses
        if len(self.daily_summaries) >= 5:
            recent_performance = self.daily_summaries[-5:]
            recent_roi = np.mean([day['roi'] for day in recent_performance])
            
            if recent_roi < -10:  # If losing more than 10% on average
                # Bet only every other day
                return datetime.now().day % 2 == 0
        
        return True
    
    def update_bankroll(self, bet_results: List[Dict]):
        """Update bankroll based on bet results"""
        total_profit = 0.0
        
        for result in bet_results:
            if result.get('won', False):
                profit = result['stake'] * (result['odds'] - 1)
                total_profit += profit
                print(f"✅ Won: {result['match']} {result['market']} - +${profit:.2f}")
            else:
                total_profit -= result['stake']
                print(f"❌ Lost: {result['match']} {result['market']} - -${result['stake']:.2f}")
        
        self.current_bankroll += total_profit
        
        # Update peak and drawdown
        if self.current_bankroll > self.peak_bankroll:
            self.peak_bankroll = self.current_bankroll
            self.current_drawdown = 0.0
        else:
            self.current_drawdown = (self.peak_bankroll - self.current_bankroll) / self.peak_bankroll
        
        # Record performance
        daily_summary = {
            'date': datetime.now().strftime("%Y-%m-%d"),
            'starting_bankroll': self.current_bankroll - total_profit,
            'ending_bankroll': self.current_bankroll,
            'profit_loss': total_profit,
            'roi': (total_profit / (self.current_bankroll - total_profit)) * 100,
            'num_bets': len(bet_results),
            'bets_won': sum(1 for r in bet_results if r.get('won', False)),
            'win_rate': sum(1 for r in bet_results if r.get('won', False)) / len(bet_results) * 100,
            'peak_bankroll': self.peak_bankroll,
            'drawdown': self.current_drawdown * 100
        }
        
        self.daily_summaries.append(daily_summary)
        self.save_performance_summary()
        
        print(f"\n📊 Bankroll updated: ${self.current_bankroll:.2f} ({total_profit:+.2f})")
        print(f"📈 Peak: ${self.peak_bankroll:.2f}, Drawdown: {self.current_drawdown*100:.1f}%")
    
    def save_daily_slip(self, bets: List[Dict], date: str):
        """Save daily betting slip to CSV"""
        filename = f"daily_betting_slip_{date.replace('-', '')}.csv"
        filepath = f"./{filename}"
        
        fieldnames = [
            'date', 'time', 'match', 'league', 'market', 'odds', 'stake',
            'edge', 'confidence', 'expected_value', 'model_probability',
            'implied_probability', 'bankroll_before', 'risk_level'
        ]
        
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(bets)
        
        print(f"📄 Daily slip saved: {filename}")
    
    def save_performance_summary(self):
        """Save performance summary"""
        filename = "improved_performance_summary.csv"
        filepath = f"./{filename}"
        
        fieldnames = [
            'date', 'starting_bankroll', 'ending_bankroll', 'profit_loss',
            'roi', 'num_bets', 'bets_won', 'win_rate', 'peak_bankroll', 'drawdown'
        ]
        
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.daily_summaries)
    
    def get_performance_stats(self) -> Dict:
        """Get comprehensive performance statistics"""
        if not self.daily_summaries:
            return {'status': 'No trading history'}
        
        total_days = len(self.daily_summaries)
        total_bets = sum(day['num_bets'] for day in self.daily_summaries)
        total_won = sum(day['bets_won'] for day in self.daily_summaries)
        
        total_return = (self.current_bankroll - self.initial_bankroll) / self.initial_bankroll * 100
        avg_daily_roi = np.mean([day['roi'] for day in self.daily_summaries])
        win_rate = (total_won / total_bets * 100) if total_bets > 0 else 0
        
        profitable_days = sum(1 for day in self.daily_summaries if day['profit_loss'] > 0)
        
        return {
            'total_days': total_days,
            'total_bets': total_bets,
            'overall_return': total_return,
            'current_bankroll': self.current_bankroll,
            'peak_bankroll': self.peak_bankroll,
            'max_drawdown': max(day['drawdown'] for day in self.daily_summaries),
            'current_drawdown': self.current_drawdown * 100,
            'overall_win_rate': win_rate,
            'profitable_days': profitable_days,
            'profitable_day_rate': (profitable_days / total_days * 100) if total_days > 0 else 0,
            'avg_daily_roi': avg_daily_roi,
            'sharpe_ratio': self.calculate_sharpe_ratio()
        }
    
    def calculate_sharpe_ratio(self) -> float:
        """Calculate Sharpe ratio of the strategy"""
        if len(self.daily_summaries) < 2:
            return 0.0
        
        daily_returns = [day['roi'] / 100 for day in self.daily_summaries]
        
        mean_return = np.mean(daily_returns)
        std_return = np.std(daily_returns)
        
        if std_return == 0:
            return 0.0
        
        # Assuming risk-free rate of 0.05% per day (roughly 2% annually)
        risk_free_rate = 0.0005
        sharpe = (mean_return - risk_free_rate) / std_return
        
        return sharpe


def main():
    """Example usage of improved daily manager"""
    API_KEY = "ceb338b9bcb82a452efc114fb2d3cccac67f58be1569e7b5acf1d2195adeae11"
    
    # Initialize manager with conservative starting bankroll
    manager = ImprovedDailyBettingManager(API_KEY, initial_bankroll=500.0)
    
    # Load or train models
    if not manager.load_or_train_models():
        print("❌ Failed to initialize prediction models")
        return
    
    print("\n🎯 Improved Daily Betting Manager Ready!")
    
    # Example daily matches (in real use, this would come from API)
    example_matches = [
        {
            'home_team': 'Manchester City',
            'away_team': 'Arsenal',
            'league': 'Premier League',
            'home_odds': 2.1,
            'draw_odds': 3.4,
            'away_odds': 3.2
        },
        {
            'home_team': 'Barcelona',
            'away_team': 'Real Madrid',
            'league': 'La Liga',
            'home_odds': 2.8,
            'draw_odds': 3.1,
            'away_odds': 2.5
        }
    ]
    
    # Execute daily strategy
    result = manager.execute_daily_strategy(example_matches)
    print(f"\n📊 Strategy Result: {result}")
    
    # Show performance stats
    stats = manager.get_performance_stats()
    print(f"\n📈 Performance Overview:")
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.2f}")
        else:
            print(f"   {key}: {value}")


if __name__ == "__main__":
    main()