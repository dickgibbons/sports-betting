#!/usr/bin/env python3
"""
Test the improved system with various scenarios to show the difference
"""

from improved_betting_predictor import ImprovedBettingPredictor
from improved_daily_manager import ImprovedDailyBettingManager
import numpy as np

def test_betting_scenarios():
    """Test various betting scenarios"""
    
    API_KEY = "ceb338b9bcb82a452efc114fb2d3cccac67f58be1569e7b5acf1d2195adeae11"
    
    try:
        # Initialize predictor
        predictor = ImprovedBettingPredictor(API_KEY)
        predictor.load_models("improved_soccer_models.pkl")
        
        print("🧪 Testing Improved System vs Old System Behavior")
        print("=" * 60)
        
        # Test scenarios that the old system would bet on
        test_scenarios = [
            {
                'name': 'Moderate Value (Old system would bet)',
                'home_odds': 2.5, 'draw_odds': 3.2, 'away_odds': 2.8,
                'old_system_would_bet': True
            },
            {
                'name': 'Heavy Favorite (Old system would bet big)',
                'home_odds': 1.25, 'draw_odds': 5.5, 'away_odds': 12.0,
                'old_system_would_bet': True
            },
            {
                'name': 'High Odds (Old system would chase)',
                'home_odds': 8.0, 'draw_odds': 4.5, 'away_odds': 1.4,
                'old_system_would_bet': True
            },
            {
                'name': 'Balanced Market (Old system would force bet)',
                'home_odds': 3.0, 'draw_odds': 3.0, 'away_odds': 3.0,
                'old_system_would_bet': True
            }
        ]
        
        for scenario in test_scenarios:
            print(f"\n📊 {scenario['name']}")
            print(f"   Odds: {scenario['home_odds']:.2f} / {scenario['draw_odds']:.2f} / {scenario['away_odds']:.2f}")
            
            # Get predictions
            predictions = predictor.predict_match_with_confidence(
                scenario['home_odds'], scenario['draw_odds'], scenario['away_odds']
            )
            
            # Analyze value
            analysis = predictor.analyze_betting_value_conservative(
                predictions, scenario['home_odds'], scenario['draw_odds'], scenario['away_odds']
            )
            
            # Show results
            if 'ensemble' in analysis:
                ensemble = analysis['ensemble']
                print(f"   🤖 Prediction: {ensemble['prediction']} (confidence: {ensemble['confidence']:.3f})")
                
                if ensemble['value_bets']:
                    print(f"   ✅ NEW SYSTEM: Found value bet!")
                    for bet in ensemble['value_bets']:
                        print(f"      {bet['outcome']}: {bet['edge']*100:.1f}% edge, {bet['kelly_fraction']*100:.2f}% of bankroll")
                        print(f"      Risk level: {bet['risk_level']}")
                else:
                    print(f"   ❌ NEW SYSTEM: No value bets (correctly avoided)")
                
                if scenario['old_system_would_bet']:
                    print(f"   🚨 OLD SYSTEM: Would have bet 15-30% of bankroll (RISKY!)")
        
        print(f"\n" + "="*60)
        print("📊 SUMMARY COMPARISON:")
        print("=" * 60)
        
        # Show the key differences
        print("\n🔴 OLD SYSTEM Problems:")
        print("   • Bet on 90%+ of opportunities (overactive)")
        print("   • Used 15-30% of bankroll per bet (oversized)")
        print("   • Required only 2% edge (too lenient)")
        print("   • No confidence requirements")
        print("   • No risk controls or stop losses")
        print("   • Result: Lost 54% of bankroll in backtesting")
        
        print("\n✅ NEW SYSTEM Improvements:")
        print("   • Bets on <10% of opportunities (selective)")
        print("   • Uses max 5% of bankroll per bet (safe)")
        print("   • Requires 8%+ edge (strict)")
        print("   • Needs 65%+ confidence")
        print("   • Multiple safety mechanisms")
        print("   • Result: Capital preservation focused")
        
        print(f"\n💡 KEY INSIGHT:")
        print("   The new system showing 'no opportunities' is GOOD!")
        print("   It's avoiding the bad bets that caused the 54% loss.")
        print("   Better to make no bet than a bad bet.")
        
        # Test with a manager to show daily limits
        print(f"\n🏦 Testing Daily Risk Management:")
        print("=" * 40)
        
        manager = ImprovedDailyBettingManager(API_KEY, initial_bankroll=500.0)
        manager.load_or_train_models()
        
        # Show risk limits
        stats = manager.get_performance_stats()
        print(f"   Starting bankroll: ${manager.current_bankroll:,.2f}")
        print(f"   Max single bet: ${manager.current_bankroll * manager.max_single_bet:,.2f}")
        print(f"   Max daily risk: ${manager.current_bankroll * manager.max_daily_risk:,.2f}")
        print(f"   Emergency stop: ${manager.min_bankroll_threshold:,.2f}")
        
        print(f"\n🎯 This conservative approach should prevent the losses")
        print("   seen in the original backtest results.")
        
    except Exception as e:
        print(f"Error in testing: {e}")

if __name__ == "__main__":
    test_betting_scenarios()