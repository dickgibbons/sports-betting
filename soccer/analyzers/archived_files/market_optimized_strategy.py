#!/usr/bin/env python3
"""
Market-Optimized Selection Strategy

Based on comprehensive bet type performance analysis, this strategy:
1. Focuses heavily on profitable bet types
2. Eliminates or restricts poor-performing markets
3. Applies market-specific thresholds based on actual performance data
"""

import pandas as pd
from datetime import datetime
from typing import List, Dict
import numpy as np

class MarketOptimizedStrategy:
    """Market-optimized bet selection based on historical performance data"""
    
    def __init__(self):
        # Market performance data from analysis
        self.market_performance = {
            # TOP TIER - Highly profitable markets
            'Over 2.5 Goals': {
                'tier': 'ELITE',
                'historical_win_rate': 77.3,
                'historical_roi': 60.3,
                'min_edge': 25.0,
                'min_confidence': 65.0,
                'max_daily': 3,
                'position_multiplier': 1.5,  # 50% larger positions
                'priority': 1
            },
            'Away Team Under 1.5 Goals': {
                'tier': 'ELITE', 
                'historical_win_rate': 83.3,
                'historical_roi': 91.3,
                'min_edge': 20.0,
                'min_confidence': 65.0,
                'max_daily': 2,
                'position_multiplier': 1.5,
                'priority': 1
            },
            
            # SECOND TIER - Modestly profitable
            'Under 2.5 Goals': {
                'tier': 'GOOD',
                'historical_win_rate': 54.5,
                'historical_roi': 5.1,
                'min_edge': 20.0,
                'min_confidence': 70.0,
                'max_daily': 2,
                'position_multiplier': 1.0,
                'priority': 2
            },
            'Both Teams to Score - No': {
                'tier': 'GOOD',
                'historical_win_rate': 57.1,
                'historical_roi': 4.8,
                'min_edge': 25.0,
                'min_confidence': 72.0,
                'max_daily': 2,
                'position_multiplier': 1.0,
                'priority': 2
            },
            'Over 9.5 Total Corners': {
                'tier': 'GOOD',
                'historical_win_rate': 50.0,
                'historical_roi': 16.0,
                'min_edge': 22.0,
                'min_confidence': 70.0,
                'max_daily': 1,
                'position_multiplier': 1.0,
                'priority': 2
            },
            
            # RESTRICTED TIER - Poor performers, very high standards
            'Home Team Under 1.5 Goals': {
                'tier': 'RESTRICTED',
                'historical_win_rate': 50.0,
                'historical_roi': -12.6,
                'min_edge': 35.0,  # Much higher threshold
                'min_confidence': 78.0,
                'max_daily': 1,
                'position_multiplier': 0.7,  # Smaller positions
                'priority': 4
            },
            'Both Teams to Score - Yes': {
                'tier': 'RESTRICTED',
                'historical_win_rate': 33.3,
                'historical_roi': -32.9,
                'min_edge': 40.0,  # Very high threshold
                'min_confidence': 80.0,
                'max_daily': 1,
                'position_multiplier': 0.5,
                'priority': 5
            },
            
            # BANNED - Avoid completely
            'Over 1.5 Goals': {
                'tier': 'BANNED',
                'historical_win_rate': 48.5,
                'historical_roi': -35.6,
                'reason': 'Consistently unprofitable with -8.89 avg per bet'
            }
        }
        
        # Default settings for markets not in our analysis
        self.default_market_settings = {
            'tier': 'UNKNOWN',
            'min_edge': 30.0,
            'min_confidence': 75.0,
            'max_daily': 1,
            'position_multiplier': 0.8,
            'priority': 3
        }
        
        print("🎯 Market-Optimized Strategy Initialized")
        print(f"   🏆 Elite Markets: {len([m for m, s in self.market_performance.items() if s['tier'] == 'ELITE'])}")
        print(f"   ✅ Good Markets: {len([m for m, s in self.market_performance.items() if s['tier'] == 'GOOD'])}")
        print(f"   ⚠️ Restricted Markets: {len([m for m, s in self.market_performance.items() if s['tier'] == 'RESTRICTED'])}")
        print(f"   🚫 Banned Markets: {len([m for m, s in self.market_performance.items() if s['tier'] == 'BANNED'])}")
    
    def filter_market_optimized_picks(self, predictions: List[Dict]) -> List[Dict]:
        """Apply market-optimized filtering"""
        
        if not predictions:
            return []
        
        print(f"🎯 Filtering {len(predictions)} predictions with market optimization...")
        
        # First pass: Apply market-specific filters
        market_filtered = []
        daily_counts = {}
        
        for pred in predictions:
            market = self.normalize_market_name(pred.get('bet_description', ''))
            date = pred.get('date', datetime.now().strftime('%Y-%m-%d'))
            
            # Get market settings
            settings = self.market_performance.get(market, self.default_market_settings)
            
            # Skip banned markets entirely
            if settings['tier'] == 'BANNED':
                continue
            
            # Apply market-specific thresholds
            edge = pred.get('edge_pct', 0)
            confidence = pred.get('confidence_pct', 0)
            
            if edge < settings['min_edge'] or confidence < settings['min_confidence']:
                continue
            
            # Apply daily limits per market
            market_date_key = f"{market}_{date}"
            current_count = daily_counts.get(market_date_key, 0)
            
            if current_count >= settings['max_daily']:
                continue
            
            # Add market optimization data
            pred['market_tier'] = settings['tier']
            pred['market_priority'] = settings['priority']
            pred['position_multiplier'] = settings['position_multiplier']
            pred['historical_win_rate'] = settings.get('historical_win_rate', 50.0)
            pred['historical_roi'] = settings.get('historical_roi', 0.0)
            
            # Calculate optimized position size
            base_position = self.calculate_base_position_size(pred)
            optimized_position = base_position * settings['position_multiplier']
            pred['optimized_position_size'] = min(optimized_position, 4.0)  # Cap at 4%
            
            market_filtered.append(pred)
            daily_counts[market_date_key] = current_count + 1
        
        # Sort by priority and quality
        market_filtered.sort(key=lambda x: (
            x['market_priority'],                    # Priority (1 = best)
            -x.get('edge_pct', 0),                  # Higher edge first
            -x.get('optimized_position_size', 0)     # Larger positions first
        ))
        
        # Apply overall daily limits (focused approach)
        final_picks = self.apply_daily_limits(market_filtered)
        
        print(f"   ✅ {len(final_picks)} picks passed market optimization")
        
        # Show market distribution
        if final_picks:
            market_counts = {}
            for pick in final_picks:
                tier = pick['market_tier']
                market_counts[tier] = market_counts.get(tier, 0) + 1
            
            print(f"   📊 Market distribution: {dict(market_counts)}")
        
        return final_picks
    
    def normalize_market_name(self, bet_description: str) -> str:
        """Normalize bet description to match our market categories"""
        
        desc_lower = bet_description.lower()
        
        # Exact matches first
        for market in self.market_performance.keys():
            if market.lower() in desc_lower:
                return market
        
        # Pattern matching for variations
        if 'over 2.5' in desc_lower and 'goals' in desc_lower:
            return 'Over 2.5 Goals'
        elif 'under 2.5' in desc_lower and 'goals' in desc_lower:
            return 'Under 2.5 Goals'
        elif 'over 1.5' in desc_lower and 'goals' in desc_lower:
            return 'Over 1.5 Goals'
        elif 'under 1.5' in desc_lower and 'goals' in desc_lower:
            if 'away' in desc_lower or 'away team' in desc_lower:
                return 'Away Team Under 1.5 Goals'
            elif 'home' in desc_lower or 'home team' in desc_lower:
                return 'Home Team Under 1.5 Goals'
        elif 'both teams to score' in desc_lower:
            if 'yes' in desc_lower:
                return 'Both Teams to Score - Yes'
            elif 'no' in desc_lower:
                return 'Both Teams to Score - No'
        elif 'over 9.5' in desc_lower and 'corners' in desc_lower:
            return 'Over 9.5 Total Corners'
        
        return bet_description  # Return original if no match
    
    def calculate_base_position_size(self, prediction: Dict) -> float:
        """Calculate base position size before market multiplier"""
        
        edge = prediction.get('edge_pct', 0)
        confidence = prediction.get('confidence_pct', 0)
        
        # Base position sizing logic
        if edge >= 40 and confidence >= 75:
            return 3.0  # Elite opportunities
        elif edge >= 30 and confidence >= 70:
            return 2.5  # Premium opportunities
        elif edge >= 25 and confidence >= 65:
            return 2.0  # Good opportunities
        elif edge >= 20 and confidence >= 60:
            return 1.5  # Standard opportunities
        else:
            return 1.0  # Minimum
    
    def apply_daily_limits(self, picks: List[Dict]) -> List[Dict]:
        """Apply intelligent daily limits focused on best opportunities"""
        
        # Group by date
        daily_groups = {}
        for pick in picks:
            date = pick.get('date', datetime.now().strftime('%Y-%m-%d'))
            if date not in daily_groups:
                daily_groups[date] = []
            daily_groups[date].append(pick)
        
        final_picks = []
        
        for date, date_picks in daily_groups.items():
            # Prioritize elite markets
            elite_picks = [p for p in date_picks if p['market_tier'] == 'ELITE']
            good_picks = [p for p in date_picks if p['market_tier'] == 'GOOD']
            other_picks = [p for p in date_picks if p['market_tier'] not in ['ELITE', 'GOOD']]
            
            # Daily allocation strategy
            daily_selection = []
            
            # Take up to 4 elite picks per day
            daily_selection.extend(elite_picks[:4])
            
            # Add up to 3 good picks if we have room
            remaining_slots = max(0, 6 - len(daily_selection))
            daily_selection.extend(good_picks[:remaining_slots])
            
            # Add 1 other pick only if we have lots of room and it's exceptional
            if len(daily_selection) <= 3:
                exceptional_others = [p for p in other_picks if p.get('edge_pct', 0) >= 35]
                if exceptional_others:
                    daily_selection.extend(exceptional_others[:1])
            
            final_picks.extend(daily_selection)
        
        return final_picks
    
    def generate_strategy_report(self, original_picks: List[Dict], optimized_picks: List[Dict]):
        """Generate report showing market optimization impact"""
        
        print(f"\n📊 MARKET OPTIMIZATION STRATEGY REPORT")
        print("=" * 60)
        
        print(f"Original picks: {len(original_picks)}")
        print(f"Market-optimized picks: {len(optimized_picks)}")
        print(f"Optimization rate: {((len(original_picks) - len(optimized_picks)) / len(original_picks) * 100):.1f}% filtered")
        
        if not optimized_picks:
            return
        
        # Market tier breakdown
        tier_counts = {}
        tier_historical_performance = {}
        
        for pick in optimized_picks:
            tier = pick['market_tier']
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            
            if tier not in tier_historical_performance:
                tier_historical_performance[tier] = {
                    'avg_historical_win_rate': 0,
                    'avg_historical_roi': 0,
                    'count': 0
                }
            
            tier_historical_performance[tier]['avg_historical_win_rate'] += pick.get('historical_win_rate', 0)
            tier_historical_performance[tier]['avg_historical_roi'] += pick.get('historical_roi', 0)
            tier_historical_performance[tier]['count'] += 1
        
        print(f"\n🏆 MARKET TIER DISTRIBUTION:")
        for tier, count in sorted(tier_counts.items()):
            if tier_historical_performance[tier]['count'] > 0:
                avg_win_rate = tier_historical_performance[tier]['avg_historical_win_rate'] / tier_historical_performance[tier]['count']
                avg_roi = tier_historical_performance[tier]['avg_historical_roi'] / tier_historical_performance[tier]['count']
                print(f"   {tier}: {count} picks (Historical: {avg_win_rate:.1f}% win rate, {avg_roi:+.1f}% ROI)")
        
        # Market-specific breakdown
        market_counts = {}
        for pick in optimized_picks:
            market = self.normalize_market_name(pick.get('bet_description', ''))
            market_counts[market] = market_counts.get(market, 0) + 1
        
        print(f"\n📈 SELECTED MARKETS:")
        for market, count in sorted(market_counts.items(), key=lambda x: x[1], reverse=True):
            if market in self.market_performance:
                settings = self.market_performance[market]
                print(f"   {market}: {count} picks ({settings['tier']} tier)")
        
        print(f"\n💡 STRATEGY ADVANTAGES:")
        print(f"   • Focus on proven profitable markets (Over 2.5 Goals, Away U1.5)")
        print(f"   • Eliminated worst performer (Over 1.5 Goals: -35.6% ROI)")
        print(f"   • Higher thresholds for poor-performing markets")
        print(f"   • Position sizing based on market track record")

def main():
    """Test market-optimized strategy"""
    
    # Sample predictions for testing
    sample_predictions = [
        {
            'date': '2025-09-10',
            'bet_description': 'Over 2.5 Goals',
            'edge_pct': 28.5,
            'confidence_pct': 72.3,
            'odds': 2.2
        },
        {
            'date': '2025-09-10', 
            'bet_description': 'Away Team Under 1.5 Goals',
            'edge_pct': 25.2,
            'confidence_pct': 68.9,
            'odds': 2.8
        },
        {
            'date': '2025-09-10',
            'bet_description': 'Over 1.5 Goals',  # This should be banned
            'edge_pct': 35.0,
            'confidence_pct': 75.0,
            'odds': 1.35
        },
        {
            'date': '2025-09-10',
            'bet_description': 'Both Teams to Score - Yes',  # This should need very high thresholds
            'edge_pct': 35.0,  # Below 40% threshold
            'confidence_pct': 75.0,
            'odds': 2.0
        }
    ]
    
    strategy = MarketOptimizedStrategy()
    optimized = strategy.filter_market_optimized_picks(sample_predictions)
    strategy.generate_strategy_report(sample_predictions, optimized)

if __name__ == "__main__":
    main()