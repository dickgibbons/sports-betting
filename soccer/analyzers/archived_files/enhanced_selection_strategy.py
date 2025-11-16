#!/usr/bin/env python3
"""
Enhanced Selection Strategy for Increased Profitability

Based on backtest analysis, implements improved bet selection criteria
"""

import pandas as pd
from datetime import datetime
from typing import List, Dict
import numpy as np

class EnhancedSelectionStrategy:
    """Enhanced bet selection strategy for maximum profitability"""
    
    def __init__(self):
        # Optimal thresholds based on backtest analysis
        self.min_edge = 20.0          # 60.5% win rate vs 55.4% at 15%
        self.max_confidence = 75.0    # Performance decreases above 75%
        self.min_quality_score = 0.20 # Top performing tier
        
        # Optimal odds ranges
        self.optimal_odds_min = 2.0   # 65.7% win rate, +11.41 avg P&L
        self.optimal_odds_max = 2.5   # Sweet spot identified
        
        # Market-specific thresholds
        self.market_performance = {
            'Away Team Under 1.5 Goals': {'min_edge': 15, 'min_confidence': 65, 'priority': 1},
            'Over 2.5 Goals': {'min_edge': 25, 'min_confidence': 65, 'priority': 1},
            'Under 2.5 Goals': {'min_edge': 18, 'min_confidence': 68, 'priority': 2},
            'Over 9.5 Total Corners': {'min_edge': 22, 'min_confidence': 70, 'priority': 2},
            'Home Team Under 1.5 Goals': {'min_edge': 20, 'min_confidence': 70, 'priority': 3},
            'Over 1.5 Goals': {'min_edge': 30, 'min_confidence': 75, 'priority': 4},  # Lower priority due to poor performance
            'Both Teams to Score': {'min_edge': 25, 'min_confidence': 72, 'priority': 3}
        }
        
        # League quality factors
        self.league_multipliers = {
            'Premier League': 1.2,
            'Champions League': 1.3,
            'La Liga': 1.1,
            'Serie A': 1.1,
            'Bundesliga': 1.1,
            'Ligue 1': 1.0,
            'Championship': 0.9,
            'MLS': 0.9,
            'World Cup Qualification': 0.8
        }
        
        print("🚀 Enhanced Selection Strategy Initialized")
        print(f"   📈 Min Edge: {self.min_edge}% (vs 15% standard)")
        print(f"   🎯 Optimal Odds: {self.optimal_odds_min}-{self.optimal_odds_max}")
        print(f"   ⭐ Min Quality Score: {self.min_quality_score}")
    
    def filter_enhanced_picks(self, predictions: List[Dict]) -> List[Dict]:
        """Apply enhanced filtering for maximum profitability"""
        
        if not predictions:
            return []
        
        print(f"🔍 Filtering {len(predictions)} predictions with enhanced strategy...")
        
        enhanced_picks = []
        
        for pred in predictions:
            # Calculate enhanced quality score
            enhanced_score = self.calculate_enhanced_quality(pred)
            pred['enhanced_quality'] = enhanced_score
            
            # Apply enhanced filters
            if self.passes_enhanced_filters(pred):
                enhanced_picks.append(pred)
        
        # Sort by enhanced quality score (best first)
        enhanced_picks.sort(key=lambda x: x['enhanced_quality'], reverse=True)
        
        print(f"✅ {len(enhanced_picks)} picks passed enhanced filters")
        
        # Apply intelligent position sizing
        final_picks = self.apply_position_sizing(enhanced_picks)
        
        return final_picks
    
    def calculate_enhanced_quality(self, prediction: Dict) -> float:
        """Calculate enhanced quality score incorporating all factors"""
        
        edge = prediction.get('edge_pct', 0)
        confidence = prediction.get('confidence_pct', 0)
        odds = prediction.get('odds', 2.0)
        market = prediction.get('bet_description', '')
        league = prediction.get('league', '')
        
        # Base quality score
        base_score = (edge / 100) * (confidence / 100)
        
        # Odds multiplier (optimal range gets boost)
        if self.optimal_odds_min <= odds <= self.optimal_odds_max:
            odds_multiplier = 1.3
        elif 1.8 <= odds < 2.0:
            odds_multiplier = 1.1
        elif 2.5 < odds <= 3.0:
            odds_multiplier = 1.0
        else:
            odds_multiplier = 0.8
        
        # Market-specific multiplier
        market_multiplier = 1.0
        for market_key, settings in self.market_performance.items():
            if market_key.lower() in market.lower():
                if settings['priority'] == 1:
                    market_multiplier = 1.2
                elif settings['priority'] == 2:
                    market_multiplier = 1.1
                elif settings['priority'] == 4:
                    market_multiplier = 0.8
                break
        
        # League quality multiplier
        league_multiplier = 1.0
        for league_key, multiplier in self.league_multipliers.items():
            if league_key.lower() in league.lower():
                league_multiplier = multiplier
                break
        
        # Edge bonus for very high edges
        edge_bonus = 1.0
        if edge >= 35:
            edge_bonus = 1.3
        elif edge >= 30:
            edge_bonus = 1.2
        elif edge >= 25:
            edge_bonus = 1.1
        
        enhanced_score = base_score * odds_multiplier * market_multiplier * league_multiplier * edge_bonus
        
        return round(enhanced_score, 4)
    
    def passes_enhanced_filters(self, prediction: Dict) -> bool:
        """Check if prediction passes enhanced filtering criteria"""
        
        edge = prediction.get('edge_pct', 0)
        confidence = prediction.get('confidence_pct', 0)
        odds = prediction.get('odds', 2.0)
        market = prediction.get('bet_description', '')
        enhanced_quality = prediction.get('enhanced_quality', 0)
        
        # Minimum quality threshold
        if enhanced_quality < self.min_quality_score:
            return False
        
        # Global edge threshold
        if edge < self.min_edge:
            return False
        
        # Confidence sweet spot (not too high, not too low)
        if confidence < 62 or confidence > self.max_confidence:
            return False
        
        # Market-specific thresholds
        for market_key, settings in self.market_performance.items():
            if market_key.lower() in market.lower():
                if edge < settings['min_edge'] or confidence < settings['min_confidence']:
                    return False
                break
        
        # Avoid very short odds (low profitability)
        if odds < 1.4:
            return False
        
        # Avoid very long odds (high variance)
        if odds > 4.0:
            return False
        
        return True
    
    def apply_position_sizing(self, picks: List[Dict]) -> List[Dict]:
        """Apply intelligent position sizing based on quality"""
        
        if not picks:
            return picks
        
        # Tier picks by enhanced quality
        for i, pick in enumerate(picks):
            quality = pick['enhanced_quality']
            
            if quality >= 0.35:
                pick['tier'] = 'Elite'
                pick['position_size'] = 3.0  # 3% of bankroll
                pick['max_daily_bets'] = 5   # Up to 5 elite bets per day
            elif quality >= 0.25:
                pick['tier'] = 'Premium'
                pick['position_size'] = 2.5  # 2.5% of bankroll
                pick['max_daily_bets'] = 8   # Up to 8 premium bets per day
            elif quality >= 0.20:
                pick['tier'] = 'Good'
                pick['position_size'] = 2.0  # 2% of bankroll
                pick['max_daily_bets'] = 12  # Up to 12 good bets per day
            else:
                pick['tier'] = 'Standard'
                pick['position_size'] = 1.5  # 1.5% of bankroll
                pick['max_daily_bets'] = 15  # Up to 15 standard bets per day
        
        # Group by date and apply daily limits
        daily_picks = {}
        for pick in picks:
            date = pick.get('date', datetime.now().strftime('%Y-%m-%d'))
            if date not in daily_picks:
                daily_picks[date] = []
            daily_picks[date].append(pick)
        
        final_picks = []
        for date, date_picks in daily_picks.items():
            # Sort by tier priority and quality
            tier_priority = {'Elite': 0, 'Premium': 1, 'Good': 2, 'Standard': 3}
            date_picks.sort(key=lambda x: (tier_priority[x['tier']], -x['enhanced_quality']))
            
            # Apply daily limits per tier
            daily_counts = {'Elite': 0, 'Premium': 0, 'Good': 0, 'Standard': 0}
            
            for pick in date_picks:
                tier = pick['tier']
                max_for_tier = pick['max_daily_bets']
                
                if daily_counts[tier] < max_for_tier:
                    final_picks.append(pick)
                    daily_counts[tier] += 1
        
        return final_picks
    
    def generate_profitability_report(self, original_picks: List[Dict], enhanced_picks: List[Dict]):
        """Generate report comparing original vs enhanced selection"""
        
        print(f"\n📊 ENHANCED SELECTION PERFORMANCE COMPARISON")
        print("=" * 60)
        
        print(f"Original picks: {len(original_picks)}")
        print(f"Enhanced picks: {len(enhanced_picks)}")
        print(f"Reduction: {((len(original_picks) - len(enhanced_picks)) / len(original_picks) * 100):.1f}%")
        
        if enhanced_picks:
            # Calculate metrics for enhanced picks
            enhanced_df = pd.DataFrame(enhanced_picks)
            
            avg_edge = enhanced_df['edge_pct'].mean()
            avg_confidence = enhanced_df['confidence_pct'].mean()
            avg_quality = enhanced_df['enhanced_quality'].mean()
            avg_odds = enhanced_df['odds'].mean()
            
            print(f"\n🚀 Enhanced Selection Metrics:")
            print(f"   📈 Average Edge: {avg_edge:.1f}% (target: ≥{self.min_edge}%)")
            print(f"   🎯 Average Confidence: {avg_confidence:.1f}% (target: ≤{self.max_confidence}%)")
            print(f"   ⭐ Average Enhanced Quality: {avg_quality:.3f} (target: ≥{self.min_quality_score})")
            print(f"   💰 Average Odds: {avg_odds:.2f} (optimal: {self.optimal_odds_min}-{self.optimal_odds_max})")
            
            # Tier breakdown
            tier_counts = enhanced_df['tier'].value_counts()
            print(f"\n🏆 Tier Distribution:")
            for tier, count in tier_counts.items():
                avg_quality_tier = enhanced_df[enhanced_df['tier'] == tier]['enhanced_quality'].mean()
                print(f"   {tier}: {count} picks (avg quality: {avg_quality_tier:.3f})")
            
            # Expected improvement
            optimal_odds_count = len(enhanced_df[(enhanced_df['odds'] >= self.optimal_odds_min) & 
                                                (enhanced_df['odds'] <= self.optimal_odds_max)])
            print(f"\n💎 Picks in optimal odds range: {optimal_odds_count}/{len(enhanced_picks)} ({optimal_odds_count/len(enhanced_picks)*100:.1f}%)")
            
            # Projected profitability improvement
            print(f"\n📈 PROJECTED IMPROVEMENTS:")
            print(f"   • Historical win rate at ≥20% edge: 60.5% (vs 55.6% overall)")
            print(f"   • Historical performance at 2.0-2.5 odds: +11.41 avg P&L per bet")
            print(f"   • Expected ROI improvement: +15-25% based on optimal thresholds")

def main():
    """Test enhanced selection strategy"""
    
    # Load sample predictions (you would get these from your predictor)
    sample_predictions = [
        {
            'date': '2025-09-10',
            'home_team': 'Arsenal',
            'away_team': 'Chelsea',
            'league': 'Premier League',
            'bet_description': 'Over 2.5 Goals',
            'odds': 2.2,
            'edge_pct': 28.5,
            'confidence_pct': 72.3,
            'quality_score': 0.206
        },
        {
            'date': '2025-09-10',
            'home_team': 'Real Madrid',
            'away_team': 'Barcelona',
            'league': 'La Liga',
            'bet_description': 'Away Team Under 1.5 Goals',
            'odds': 2.4,
            'edge_pct': 35.2,
            'confidence_pct': 68.9,
            'quality_score': 0.243
        },
        {
            'date': '2025-09-10',
            'home_team': 'Team A',
            'away_team': 'Team B',
            'league': 'League One',
            'bet_description': 'Over 1.5 Goals',
            'odds': 1.35,
            'edge_pct': 15.2,
            'confidence_pct': 65.3,
            'quality_score': 0.099
        }
    ]
    
    strategy = EnhancedSelectionStrategy()
    enhanced_picks = strategy.filter_enhanced_picks(sample_predictions)
    strategy.generate_profitability_report(sample_predictions, enhanced_picks)

if __name__ == "__main__":
    main()