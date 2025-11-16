#!/usr/bin/env python3

"""
Balanced Betting Strategy - Generate Daily Picks
===============================================
A more balanced approach that generates actual picks while avoiding the worst performers.
Based on backtest analysis but less restrictive to ensure daily opportunities.
"""

import pandas as pd
from typing import List, Dict
import numpy as np

class BalancedBettingStrategy:
    """Balanced strategy that generates picks while avoiding worst performers"""
    
    def __init__(self):
        
        # WORST PERFORMERS TO AVOID (from backtest data)
        self.banned_markets = {
            'Under 2.5 Goals'     # -76.0% ROI, 20.0% win rate - TERRIBLE  
        }
        
        # DE-PRIORITIZE but don't ban completely
        self.low_priority_markets = {
            'Draw'               # -56.6% ROI, 26.7% win rate - Poor but not banned
        }
        
        # BALANCED CONFIDENCE RANGE - not too restrictive
        self.confidence_range = (0.52, 0.88)  # Wider range for more opportunities
        
        # RELAXED EDGE REQUIREMENTS - need to generate picks
        self.min_edge = 0.02             # Very low to allow opportunities (2%)
        
        # QUALITY SCORE THRESHOLD - disabled to generate picks  
        self.min_quality_score = 0.0     # Disabled to ensure picks are generated
        
        # PROBLEMATIC LEAGUES TO DEPRIORITIZE (not ban)
        self.low_priority_leagues = {
            'MLS',               # -$177 loss in backtest
            'Serie A'            # -$121 loss in backtest
        }
        
        print("⚖️ BALANCED BETTING STRATEGY LOADED")
        print(f"❌ Banned Markets: {', '.join(self.banned_markets) if self.banned_markets else 'None'}")
        print(f"⚠️ Low Priority Markets: {', '.join(self.low_priority_markets)}")
        print(f"🎯 Confidence Range: {self.confidence_range[0]:.0%}-{self.confidence_range[1]:.0%}")
        print(f"📈 Min Edge: {self.min_edge:.1%}")
        print(f"⭐ Min Quality: {self.min_quality_score}")
        print()
    
    def apply_balanced_filtering(self, opportunities: List[Dict]) -> List[Dict]:
        """Apply balanced filtering that generates picks while avoiding worst performers"""
        
        if not opportunities:
            return []
        
        print(f"⚖️ APPLYING BALANCED FILTERS to {len(opportunities)} opportunities...")
        
        filtered_opportunities = []
        rejection_reasons = {
            'banned_market': 0,
            'confidence_out_of_range': 0, 
            'low_edge': 0,
            'low_quality': 0
        }
        
        for opp in opportunities:
            # Extract values
            market = opp.get('market', '').strip()
            confidence = opp.get('confidence', 0)
            edge = opp.get('edge', 0)
            league = opp.get('league', '').strip()
            quality_score = opp.get('quality_score', 0)
            
            # 1. ONLY BAN THE WORST MARKET
            if market in self.banned_markets:
                rejection_reasons['banned_market'] += 1
                continue
            
            # 2. CONFIDENCE RANGE - wider than improved strategy
            if not (self.confidence_range[0] <= confidence <= self.confidence_range[1]):
                rejection_reasons['confidence_out_of_range'] += 1
                continue
            
            # 3. EDGE REQUIREMENT - much more relaxed
            if edge < self.min_edge:
                rejection_reasons['low_edge'] += 1
                continue
            
            # 4. QUALITY SCORE - relaxed threshold
            if quality_score < self.min_quality_score:
                rejection_reasons['low_quality'] += 1
                continue
            
            # 5. APPLY SCORING ADJUSTMENTS for prioritization
            adjusted_opp = opp.copy()
            
            # Penalize low priority markets and leagues (but don't exclude)
            priority_penalty = 0
            if market in self.low_priority_markets:
                priority_penalty += 0.1
            if league in self.low_priority_leagues:
                priority_penalty += 0.05
                
            # Create balanced score combining multiple factors
            balanced_score = (
                confidence * 0.4 +        # 40% weight on confidence
                edge * 0.3 +              # 30% weight on edge
                quality_score * 0.2 +     # 20% weight on quality
                (1.0 - priority_penalty) * 0.1  # 10% adjustment for market/league priority
            )
            
            adjusted_opp['balanced_score'] = balanced_score
            filtered_opportunities.append(adjusted_opp)
        
        # Sort by balanced score (highest first)
        filtered_opportunities.sort(key=lambda x: x.get('balanced_score', 0), reverse=True)
        
        print(f"📊 BALANCED FILTERING RESULTS:")
        print(f"   ✅ Passed: {len(filtered_opportunities)} opportunities")
        print(f"   ❌ Rejected: {sum(rejection_reasons.values())} opportunities")
        print()
        
        if rejection_reasons and sum(rejection_reasons.values()) > 0:
            print(f"📋 REJECTION BREAKDOWN:")
            for reason, count in rejection_reasons.items():
                if count > 0:
                    reason_display = reason.replace('_', ' ').title()
                    print(f"   • {reason_display}: {count}")
            print()
        
        # Show top opportunities
        if filtered_opportunities:
            print(f"🏆 TOP BALANCED OPPORTUNITIES:")
            for i, opp in enumerate(filtered_opportunities[:5]):
                market = opp.get('market', 'Unknown')
                home = opp.get('home_team', 'Unknown')
                away = opp.get('away_team', 'Unknown')
                conf = opp.get('confidence', 0) * 100
                edge = opp.get('edge', 0) * 100
                score = opp.get('balanced_score', 0)
                print(f"   #{i+1}: {market} | {home} vs {away} | {conf:.1f}% conf, {edge:.1f}% edge, {score:.3f} score")
            print()
        
        return filtered_opportunities

def main():
    """Test the balanced strategy"""
    strategy = BalancedBettingStrategy()
    print("✅ Balanced strategy initialized and ready to generate daily picks!")

if __name__ == "__main__":
    main()