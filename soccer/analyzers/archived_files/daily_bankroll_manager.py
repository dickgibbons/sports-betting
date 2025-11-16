#!/usr/bin/env python3
"""
Daily Bankroll Management System for Soccer Betting

Uses a $300 bankroll to make intelligent daily betting recommendations
with proper risk management and Kelly Criterion position sizing.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from csv_predictions_generator import CSVPredictionsGenerator
from multi_league_predictor import MultiLeaguePredictor


class DailyBankrollManager:
    """Manage daily betting recommendations with bankroll management"""
    
    def __init__(self, api_key: str, initial_bankroll: float = 300.0):
        self.api_key = api_key
        self.initial_bankroll = initial_bankroll
        self.current_bankroll = initial_bankroll
        self.min_bet = 5.0  # Minimum bet size
        self.max_bet_percentage = 0.15  # Max 15% of bankroll per bet
        self.max_daily_risk = 0.25  # Max 25% of bankroll per day
        self.min_edge = 0.05  # Minimum 5% edge required
        self.min_confidence = 0.6  # Minimum confidence required
        
        self.csv_generator = CSVPredictionsGenerator(api_key)
        self.daily_bets = []
        self.betting_history = []
        
    def load_models(self):
        """Load prediction models"""
        return self.csv_generator.load_models()
    
    def calculate_kelly_bet_size(self, probability: float, odds: float, 
                                confidence: float = 1.0) -> float:
        """Calculate optimal bet size using Kelly Criterion"""
        
        if probability <= 1/odds:  # No edge
            return 0.0
        
        # Kelly formula: f = (bp - q) / b
        b = odds - 1  # Net odds received
        p = probability  # Win probability
        q = 1 - p  # Lose probability
        
        kelly_fraction = (b * p - q) / b
        
        # Apply confidence adjustment
        adjusted_kelly = kelly_fraction * confidence
        
        # Conservative caps
        max_kelly = min(adjusted_kelly, 0.10)  # Cap at 10% of bankroll
        
        return max(0.0, max_kelly)
    
    def evaluate_bet_opportunity(self, prediction_row):
        """Evaluate if a betting opportunity meets our criteria"""
        
        opportunities = []
        
        # Check 1X2 markets
        markets_to_check = [
            {
                'name': 'Home Win',
                'probability': prediction_row['home_win_prob'],
                'odds': prediction_row['home_odds'],
                'value': prediction_row['home_value'],
                'confidence': prediction_row['winner_confidence']
            },
            {
                'name': 'Draw',
                'probability': prediction_row['draw_prob'],
                'odds': prediction_row['draw_odds'],
                'value': prediction_row['draw_value'],
                'confidence': prediction_row['winner_confidence']
            },
            {
                'name': 'Away Win',
                'probability': prediction_row['away_win_prob'],
                'odds': prediction_row['away_odds'],
                'value': prediction_row['away_value'],
                'confidence': prediction_row['winner_confidence']
            },
            {
                'name': 'BTTS Yes',
                'probability': prediction_row['btts_yes_prob'],
                'odds': prediction_row.get('btts_yes_odds', 1.9),
                'value': prediction_row['btts_yes_value'],
                'confidence': prediction_row['btts_confidence']
            },
            {
                'name': 'BTTS No',
                'probability': prediction_row['btts_no_prob'],
                'odds': prediction_row.get('btts_no_odds', 1.9),
                'value': prediction_row['btts_no_value'],
                'confidence': prediction_row['btts_confidence']
            },
            {
                'name': 'Over 2.5 Goals',
                'probability': prediction_row['over_2_5_prob'],
                'odds': prediction_row.get('over_25_odds', 1.8),
                'value': prediction_row['over_25_value'],
                'confidence': 0.7  # Lower confidence for goals markets
            },
            {
                'name': 'Under 2.5 Goals',
                'probability': prediction_row['under_2_5_prob'],
                'odds': prediction_row.get('under_25_odds', 2.0),
                'value': prediction_row['under_25_value'],
                'confidence': 0.7
            }
        ]
        
        for market in markets_to_check:
            # Check if opportunity meets our criteria
            if (market['value'] > self.min_edge and 
                market['confidence'] > self.min_confidence and
                market['odds'] > 1.2):  # Avoid very low odds
                
                kelly_fraction = self.calculate_kelly_bet_size(
                    market['probability'], 
                    market['odds'],
                    market['confidence']
                )
                
                if kelly_fraction > 0:
                    bet_size = kelly_fraction * self.current_bankroll
                    
                    # Apply minimum and maximum bet constraints
                    bet_size = max(self.min_bet, bet_size)
                    bet_size = min(bet_size, self.current_bankroll * self.max_bet_percentage)
                    
                    # Calculate potential profit and ROI
                    potential_profit = bet_size * (market['odds'] - 1)
                    expected_value = (market['probability'] * potential_profit) - ((1 - market['probability']) * bet_size)
                    roi = (expected_value / bet_size) * 100
                    
                    opportunity = {
                        'match': f"{prediction_row['home_team']} vs {prediction_row['away_team']}",
                        'league': prediction_row['league'],
                        'market': market['name'],
                        'odds': market['odds'],
                        'probability': market['probability'],
                        'confidence': market['confidence'],
                        'edge': market['value'],
                        'kelly_fraction': kelly_fraction,
                        'bet_size': bet_size,
                        'potential_profit': potential_profit,
                        'expected_value': expected_value,
                        'roi': roi,
                        'risk_rating': self.calculate_risk_rating(market),
                        'match_time': prediction_row.get('time', '15:00'),
                        'date': prediction_row.get('date', datetime.now().strftime('%Y-%m-%d'))
                    }
                    
                    opportunities.append(opportunity)
        
        return opportunities
    
    def calculate_risk_rating(self, market):
        """Calculate risk rating for a bet"""
        
        # Base risk factors
        edge = market['value']
        confidence = market['confidence']
        odds = market['odds']
        
        # Higher edge and confidence = lower risk
        risk_score = 1.0
        
        if edge > 0.15:  # Very high edge
            risk_score -= 0.3
        elif edge > 0.10:  # High edge
            risk_score -= 0.2
        elif edge > 0.05:  # Moderate edge
            risk_score -= 0.1
        
        if confidence > 0.8:  # Very confident
            risk_score -= 0.2
        elif confidence > 0.7:  # Confident
            risk_score -= 0.1
        
        # Very high or very low odds increase risk
        if odds < 1.5 or odds > 4.0:
            risk_score += 0.1
        
        # Market type risk adjustment
        if 'BTTS' in market['name']:
            risk_score += 0.05  # BTTS slightly more volatile
        elif 'Goals' in market['name']:
            risk_score += 0.1   # Goals markets more volatile
        
        risk_score = max(0.1, min(1.0, risk_score))
        
        if risk_score < 0.4:
            return "Low"
        elif risk_score < 0.7:
            return "Medium"
        else:
            return "High"
    
    def generate_daily_betting_plan(self, matches_data=None, target_date=None):
        """Generate daily betting recommendations"""
        
        if target_date is None:
            target_date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"💰 Daily Bankroll Management System")
        print(f"=" * 45)
        print(f"📅 Date: {target_date}")
        print(f"💵 Current Bankroll: ${self.current_bankroll:.2f}")
        print(f"🎯 Maximum Daily Risk: ${self.current_bankroll * self.max_daily_risk:.2f} ({self.max_daily_risk*100:.0f}%)")
        print(f"📊 Minimum Edge Required: {self.min_edge*100:.0f}%")
        print(f"⭐ Minimum Confidence: {self.min_confidence*100:.0f}%")
        print("=" * 45)
        
        # Generate predictions if not provided
        if matches_data is None:
            matches_data = self.csv_generator.generate_sample_matches()
        
        # Load models
        if not self.load_models():
            print("⚠️  No models loaded - using basic calculations")
        
        # Generate predictions for all matches
        all_predictions = []
        for match in matches_data:
            prediction = self.csv_generator.predict_betting_markets(match)
            all_predictions.append(prediction)
        
        # Convert to DataFrame for easier processing
        predictions_df = pd.DataFrame(all_predictions)
        
        # Find all betting opportunities
        all_opportunities = []
        for _, row in predictions_df.iterrows():
            opportunities = self.evaluate_bet_opportunity(row)
            all_opportunities.extend(opportunities)
        
        # Sort by expected value and risk (Low risk first)
        all_opportunities.sort(key=lambda x: (x['expected_value'], x['risk_rating'] == 'Low'), reverse=True)
        
        # Select bets within daily risk limit
        daily_bets = []
        total_daily_risk = 0.0
        max_daily_risk = self.current_bankroll * self.max_daily_risk
        
        print(f"🔍 Found {len(all_opportunities)} potential betting opportunities")
        print(f"📋 Evaluating bets within daily risk limit...")
        print()
        
        for i, opp in enumerate(all_opportunities):
            if total_daily_risk + opp['bet_size'] <= max_daily_risk:
                daily_bets.append(opp)
                total_daily_risk += opp['bet_size']
                
                print(f"✅ BET {len(daily_bets)}: {opp['match']} - {opp['market']}")
                print(f"   💰 Stake: ${opp['bet_size']:.2f} ({opp['kelly_fraction']*100:.1f}% of bankroll)")
                print(f"   📊 Odds: {opp['odds']:.2f} | Edge: {opp['edge']*100:.1f}% | Confidence: {opp['confidence']*100:.0f}%")
                print(f"   🏆 Potential Profit: ${opp['potential_profit']:.2f} | Expected Value: ${opp['expected_value']:.2f}")
                print(f"   📈 ROI: {opp['roi']:.1f}% | Risk: {opp['risk_rating']}")
                print(f"   ⏰ {opp['league']} - {opp['match_time']}")
                print()
                
                # Stop if we've used enough of daily budget or have enough bets
                if len(daily_bets) >= 8:  # Max 8 bets per day
                    break
            else:
                if len(daily_bets) == 0:
                    print(f"⚠️  Bet #{i+1} exceeds daily risk limit")
        
        # Summary
        total_stake = sum(bet['bet_size'] for bet in daily_bets)
        total_potential_profit = sum(bet['potential_profit'] for bet in daily_bets)
        total_expected_value = sum(bet['expected_value'] for bet in daily_bets)
        
        print(f"=" * 60)
        print(f"📊 DAILY BETTING SUMMARY")
        print(f"=" * 60)
        print(f"🎯 Recommended Bets: {len(daily_bets)}")
        print(f"💰 Total Stakes: ${total_stake:.2f} ({total_stake/self.current_bankroll*100:.1f}% of bankroll)")
        print(f"🏆 Max Potential Profit: ${total_potential_profit:.2f}")
        print(f"📈 Total Expected Value: ${total_expected_value:.2f}")
        print(f"💹 Expected ROI: {(total_expected_value/total_stake)*100:.1f}%" if total_stake > 0 else "💹 Expected ROI: 0%")
        print(f"⚖️  Risk Level: {total_stake/self.current_bankroll*100:.1f}% of bankroll at risk")
        
        # Risk breakdown
        risk_breakdown = {}
        for bet in daily_bets:
            risk = bet['risk_rating']
            risk_breakdown[risk] = risk_breakdown.get(risk, 0) + 1
        
        if risk_breakdown:
            print(f"\n🎯 Risk Distribution:")
            for risk, count in risk_breakdown.items():
                print(f"   {risk} Risk: {count} bets")
        
        # Market breakdown
        market_breakdown = {}
        for bet in daily_bets:
            market = bet['market']
            market_breakdown[market] = market_breakdown.get(market, 0) + 1
        
        if market_breakdown:
            print(f"\n📊 Market Distribution:")
            for market, count in sorted(market_breakdown.items(), key=lambda x: x[1], reverse=True):
                print(f"   {market}: {count} bets")
        
        self.daily_bets = daily_bets
        
        # Generate betting slip
        if daily_bets:
            self.generate_betting_slip(daily_bets, target_date)
        else:
            print(f"\n❌ No suitable betting opportunities found for {target_date}")
            print(f"💡 Suggestions:")
            print(f"   • Lower minimum edge requirement (currently {self.min_edge*100:.0f}%)")
            print(f"   • Lower minimum confidence (currently {self.min_confidence*100:.0f}%)")
            print(f"   • Wait for better opportunities tomorrow")
        
        return daily_bets
    
    def generate_betting_slip(self, bets, date):
        """Generate a formatted betting slip"""
        
        print(f"\n" + "=" * 70)
        print(f"🎫 DAILY BETTING SLIP - {date}")
        print(f"=" * 70)
        
        total_stake = 0
        
        for i, bet in enumerate(bets, 1):
            print(f"\nBET #{i}")
            print(f"🏆 {bet['match']} ({bet['league']})")
            print(f"🎯 Market: {bet['market']} @ {bet['odds']:.2f}")
            print(f"💰 Stake: ${bet['bet_size']:.2f}")
            print(f"📊 Win Probability: {bet['probability']*100:.1f}%")
            print(f"🏅 Potential Return: ${bet['bet_size'] + bet['potential_profit']:.2f}")
            print(f"⭐ Confidence: {bet['confidence']*100:.0f}% | Edge: {bet['edge']*100:.1f}%")
            
            total_stake += bet['bet_size']
        
        print(f"\n" + "=" * 70)
        print(f"💵 TOTAL STAKES: ${total_stake:.2f}")
        print(f"💼 REMAINING BANKROLL: ${self.current_bankroll - total_stake:.2f}")
        print(f"📊 BANKROLL USAGE: {total_stake/self.current_bankroll*100:.1f}%")
        print(f"=" * 70)
        
        print(f"\n⚠️  IMPORTANT REMINDERS:")
        print(f"• Only bet what you can afford to lose")
        print(f"• Check for team news and injuries before placing bets")
        print(f"• Verify odds with your bookmaker before betting")
        print(f"• Consider in-play changes that may affect outcomes")
        print(f"• This is for educational purposes - bet responsibly")
        
        # Save betting slip to CSV
        self.save_betting_slip(bets, date)
    
    def save_betting_slip(self, bets, date):
        """Save betting slip to CSV"""
        
        slip_data = []
        for bet in bets:
            slip_data.append({
                'date': date,
                'match': bet['match'],
                'league': bet['league'],
                'market': bet['market'],
                'odds': bet['odds'],
                'stake': bet['bet_size'],
                'potential_profit': bet['potential_profit'],
                'probability': bet['probability'],
                'confidence': bet['confidence'],
                'edge': bet['edge'],
                'risk_rating': bet['risk_rating'],
                'expected_value': bet['expected_value'],
                'roi': bet['roi']
            })
        
        if slip_data:
            df = pd.DataFrame(slip_data)
            filename = f"daily_betting_slip_{date.replace('-', '')}.csv"
            filepath = f"./{filename}"
            df.to_csv(filepath, index=False)
            print(f"\n💾 Betting slip saved to: {filename}")
    
    def simulate_bet_results(self, bets, win_rate_adjustment=0.0):
        """Simulate bet results for testing (optional)"""
        
        results = []
        total_staked = 0
        total_returned = 0
        
        for bet in bets:
            total_staked += bet['bet_size']
            
            # Simulate outcome based on probability (with optional adjustment)
            adjusted_prob = min(0.95, bet['probability'] + win_rate_adjustment)
            won = np.random.random() < adjusted_prob
            
            if won:
                payout = bet['bet_size'] * bet['odds']
                profit = payout - bet['bet_size']
                total_returned += payout
            else:
                payout = 0
                profit = -bet['bet_size']
            
            results.append({
                'match': bet['match'],
                'market': bet['market'],
                'stake': bet['bet_size'],
                'won': won,
                'payout': payout,
                'profit': profit
            })
        
        net_profit = total_returned - total_staked
        roi = (net_profit / total_staked) * 100 if total_staked > 0 else 0
        
        return {
            'results': results,
            'total_staked': total_staked,
            'total_returned': total_returned,
            'net_profit': net_profit,
            'roi': roi,
            'win_rate': sum(1 for r in results if r['won']) / len(results) if results else 0
        }


def main():
    """Main function to run daily bankroll management"""
    
    API_KEY = "ceb338b9bcb82a452efc114fb2d3cccac67f58be1569e7b5acf1d2195adeae11"
    BANKROLL = 300.0
    
    # Initialize bankroll manager
    manager = DailyBankrollManager(API_KEY, BANKROLL)
    
    # Generate today's betting plan
    today = datetime.now().strftime('%Y-%m-%d')
    daily_bets = manager.generate_daily_betting_plan(target_date=today)
    
    # Optional: Show simulation results
    if daily_bets:
        print(f"\n🎲 SIMULATION (Educational Purpose Only)")
        print(f"=" * 40)
        
        # Simulate with normal win rates
        sim_results = manager.simulate_bet_results(daily_bets)
        print(f"📊 Simulation Results:")
        print(f"   Bets Won: {len([r for r in sim_results['results'] if r['won']])}/{len(daily_bets)}")
        print(f"   Win Rate: {sim_results['win_rate']*100:.1f}%")
        print(f"   Total Staked: ${sim_results['total_staked']:.2f}")
        print(f"   Total Returned: ${sim_results['total_returned']:.2f}")
        print(f"   Net Profit: ${sim_results['net_profit']:.2f}")
        print(f"   ROI: {sim_results['roi']:.1f}%")
        print(f"   New Bankroll: ${BANKROLL + sim_results['net_profit']:.2f}")


if __name__ == "__main__":
    main()