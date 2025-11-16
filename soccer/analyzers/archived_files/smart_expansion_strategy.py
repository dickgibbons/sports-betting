#!/usr/bin/env python3

"""
Smart Expansion Strategy - Quality Over Quantity
===============================================
Instead of expanding to 30 leagues, focus on expanding opportunities 
within the 1 profitable league we identified: La Liga (+38.7% ROI)
"""

class SmartExpansionStrategy:
    """Focus expansion on profitable opportunities rather than more leagues"""
    
    def __init__(self):
        
        # Based on backtest analysis - only profitable league
        self.profitable_leagues = {
            'La Liga': {
                'roi': 38.7,
                'total_bets': 82,
                'win_rate': 39.0,
                'status': 'HIGHLY_PROFITABLE'
            }
        }
        
        # Near-breakeven leagues (consider with caution)
        self.marginal_leagues = {
            'Premier League': {
                'roi': -5.3,
                'total_bets': 20, 
                'win_rate': 65.0,
                'status': 'SMALL_SAMPLE_HIGH_WR'
            }
        }
        
        # Avoid these entirely
        self.losing_leagues = {
            'MLS': {'roi': -53.6, 'reason': 'Massive losses'},
            'Serie A': {'roi': -29.7, 'reason': 'Consistent losses'}, 
            'Liga MX': {'roi': -26.1, 'reason': 'Poor performance'},
            'Bundesliga': {'roi': -16.4, 'reason': 'High volume losses'}
        }
    
    def get_smart_expansion_plan(self):
        """Return expansion plan focused on quality over quantity"""
        
        return {
            'approach': 'QUALITY_OVER_QUANTITY',
            'strategy': [
                {
                    'phase': 1,
                    'action': 'MAXIMIZE_LA_LIGA',
                    'description': 'Increase La Liga coverage - more matches, markets, analysis',
                    'expected_impact': 'Higher volume in only profitable league (+38.7% ROI)'
                },
                {
                    'phase': 2, 
                    'action': 'CAUTIOUS_PREMIER_LEAGUE',
                    'description': 'Careful expansion in Premier League with strict filtering',
                    'expected_impact': 'Test if 65% win rate scales (small sample: 20 bets)'
                },
                {
                    'phase': 3,
                    'action': 'MARKET_EXPANSION', 
                    'description': 'Expand profitable markets (Home Win +70.8% ROI) within current leagues',
                    'expected_impact': 'More opportunities in proven profitable patterns'
                },
                {
                    'phase': 4,
                    'action': 'SEASONAL_OPTIMIZATION',
                    'description': 'Focus on peak months (avoid Dec: -84.7% ROI)',
                    'expected_impact': 'Better timing reduces losses'
                }
            ],
            'avoid_completely': list(self.losing_leagues.keys()),
            'expected_roi_improvement': '+15-25% by focusing resources on proven winners'
        }
    
    def compare_strategies(self):
        """Compare 30-league expansion vs smart focused expansion"""
        
        print("📊 STRATEGY COMPARISON:")
        print("="*50)
        
        print("\n🌍 30-LEAGUE EXPANSION:")
        print("• Pros: More opportunities, diversification")
        print("• Cons: 83% of current leagues are unprofitable")
        print("• Risk: High - spreading into unproven markets")
        print("• Expected ROI: Likely negative (most leagues losing)")
        
        print("\n🎯 SMART FOCUSED EXPANSION:")  
        print("• Focus: La Liga (+38.7% ROI) + selective Premier League")
        print("• Strategy: Deepen profitable markets vs broaden losing ones")
        print("• Risk: Low - proven profitable patterns")
        print("• Expected ROI: +20-30% by maximizing winners")
        
        print("\n✅ RECOMMENDATION: SMART FOCUSED EXPANSION")
        print("Reason: Only 1 of 6 current leagues profitable - fix quality before adding quantity")

def simulate_expansion_impact():
    """Simulate impact of different expansion strategies"""
    
    # Current backtest results
    current_total_profit = -299.99  # From backtest
    current_total_bets = 463
    
    # La Liga performance 
    la_liga_profit = 164.10
    la_liga_bets = 82
    la_liga_roi = 38.7
    
    print("\n🧮 EXPANSION IMPACT SIMULATION:")
    print("="*40)
    
    # Scenario 1: 30-league expansion (assume average of current performance)
    current_avg_roi = (current_total_profit / (current_total_bets * 25)) * 100  # Assuming $25 avg stake
    
    expanded_volume_30_leagues = current_total_bets * 3  # 3x more leagues
    projected_30_league_loss = (expanded_volume_30_leagues * 25) * (current_avg_roi / 100)
    
    print(f"📈 30-League Expansion:")
    print(f"   • Volume: {expanded_volume_30_leagues:,} bets (~3x current)")
    print(f"   • Expected ROI: {current_avg_roi:.1f}% (same as current)")
    print(f"   • Projected P&L: ${projected_30_league_loss:+,.2f}")
    print(f"   • Risk: HIGH - unproven leagues")
    
    # Scenario 2: Smart expansion (focus on La Liga type performance)  
    smart_volume = current_total_bets * 1.5  # 50% more volume
    smart_roi = 15  # Conservative estimate focusing on profitable patterns
    projected_smart_profit = (smart_volume * 25) * (smart_roi / 100)
    
    print(f"\n🎯 Smart Focused Expansion:")
    print(f"   • Volume: {smart_volume:,} bets (+50% in profitable leagues)")
    print(f"   • Expected ROI: +{smart_roi}% (focus on La Liga patterns)")
    print(f"   • Projected P&L: ${projected_smart_profit:+,.2f}")
    print(f"   • Risk: LOW - proven profitable patterns")
    
    improvement = projected_smart_profit - projected_30_league_loss
    print(f"\n💰 SMART STRATEGY ADVANTAGE: ${improvement:+,.2f}")

if __name__ == "__main__":
    strategy = SmartExpansionStrategy()
    
    plan = strategy.get_smart_expansion_plan()
    print(f"🚀 {plan['approach']} EXPANSION PLAN")
    print("="*45)
    
    for phase_info in plan['strategy']:
        print(f"\n📋 PHASE {phase_info['phase']}: {phase_info['action']}")
        print(f"   🎯 Action: {phase_info['description']}")
        print(f"   📈 Impact: {phase_info['expected_impact']}")
    
    print(f"\n❌ AVOID: {', '.join(plan['avoid_completely'])}")
    print(f"🎯 Expected: {plan['expected_roi_improvement']}")
    
    strategy.compare_strategies()
    simulate_expansion_impact()