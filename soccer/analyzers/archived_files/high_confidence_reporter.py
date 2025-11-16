#!/usr/bin/env python3

"""
High Confidence Reporter
========================
Generates daily high confidence picks where we prioritize probability of success
over edge. Focus on picks with very high confidence (85%+) and odds of -400 or better (1.25+).

These are "safer" bets for conservative bankroll building or parlay construction.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import csv
from multi_market_predictor import MultiMarketPredictor

class HighConfidenceReporter:
    """Generate high confidence, low odds betting picks"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.predictor = MultiMarketPredictor(api_key)
        self.today = datetime.now().strftime('%Y-%m-%d')
        
        # High confidence criteria
        self.min_confidence = 0.85      # 85%+ confidence required
        self.max_odds = 5.0             # Odds of -400 = 1.25 (but using 5.0 as max for flexibility)
        self.min_odds = 1.10            # Don't want odds too low (1.10 = -1000)
        
        # Preferred markets for high confidence picks
        self.preferred_markets = {
            'Over 0.5 Goals': 'Very safe - at least 1 goal',
            'Over 1.5 Goals': 'Safe - at least 2 goals', 
            'BTTS No': 'Conservative - one team doesn\'t score',
            'Under 4.5 Goals': 'Very safe - not a basketball score',
            'Under 5.5 Goals': 'Extremely safe - reasonable goal total',
            'Double Chance': 'Two outcomes covered'
        }
        
        print("🎯 HIGH CONFIDENCE REPORTER INITIALIZED")
        print(f"   📊 Min Confidence: {self.min_confidence:.0%}")
        print(f"   💰 Odds Range: {self.min_odds:.2f} - {self.max_odds:.2f}")
        print(f"   🎪 Target: High probability, conservative picks")
        print()
    
    def generate_high_confidence_report(self, opportunities=None):
        """Generate high confidence picks report"""
        
        print(f"🎯 GENERATING HIGH CONFIDENCE REPORT for {self.today}")
        print("="*60)
        
        if opportunities is None:
            # If no opportunities provided, generate from today's fixtures
            opportunities = self._get_todays_opportunities()
        
        if not opportunities:
            print("❌ No opportunities available for high confidence analysis")
            return self._generate_empty_report()
        
        print(f"🔍 Analyzing {len(opportunities)} opportunities for high confidence picks...")
        
        # Filter for high confidence picks
        high_confidence_picks = self._filter_high_confidence_picks(opportunities)
        
        if not high_confidence_picks:
            print("❌ No high confidence picks meet criteria today")
            return self._generate_empty_report()
        
        # Sort by confidence (highest first)
        high_confidence_picks.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        print(f"✅ Found {len(high_confidence_picks)} high confidence picks")
        
        # Generate report
        report_data = {
            'date': self.today,
            'total_analyzed': len(opportunities),
            'high_confidence_picks': len(high_confidence_picks),
            'picks': high_confidence_picks,
            'criteria': {
                'min_confidence': f"{self.min_confidence:.0%}",
                'odds_range': f"{self.min_odds:.2f} - {self.max_odds:.2f}",
                'focus': 'Probability over edge'
            }
        }
        
        # Save reports
        self._save_high_confidence_csv(high_confidence_picks)
        self._save_high_confidence_txt(report_data)
        
        return report_data
    
    def _filter_high_confidence_picks(self, opportunities):
        """Filter opportunities for high confidence picks"""
        
        high_confidence_picks = []
        rejection_stats = {
            'low_confidence': 0,
            'odds_too_high': 0,
            'odds_too_low': 0,
            'total_passed': 0
        }
        
        for opp in opportunities:
            confidence = opp.get('confidence', 0)
            odds = opp.get('odds', 0)
            market = opp.get('market', '')
            
            # Check confidence requirement
            if confidence < self.min_confidence:
                rejection_stats['low_confidence'] += 1
                continue
            
            # Check odds range
            if odds > self.max_odds:
                rejection_stats['odds_too_high'] += 1
                continue
                
            if odds < self.min_odds:
                rejection_stats['odds_too_low'] += 1
                continue
            
            # Calculate safety score (different from edge-based scoring)
            safety_score = self._calculate_safety_score(opp)
            opp['safety_score'] = safety_score
            
            # Convert odds to American format for display
            american_odds = self._decimal_to_american_odds(odds)
            opp['american_odds'] = american_odds
            
            # Add market safety rating
            opp['market_safety'] = self._get_market_safety_rating(market)
            
            high_confidence_picks.append(opp)
            rejection_stats['total_passed'] += 1
        
        # Report filtering results
        print(f"📊 HIGH CONFIDENCE FILTERING RESULTS:")
        print(f"   ✅ Passed: {rejection_stats['total_passed']}")
        print(f"   ❌ Low confidence (<{self.min_confidence:.0%}): {rejection_stats['low_confidence']}")
        print(f"   ❌ Odds too high (>{self.max_odds:.2f}): {rejection_stats['odds_too_high']}")
        print(f"   ❌ Odds too low (<{self.min_odds:.2f}): {rejection_stats['odds_too_low']}")
        print()
        
        return high_confidence_picks
    
    def _calculate_safety_score(self, opportunity):
        """Calculate safety score based on confidence and market type"""
        
        confidence = opportunity.get('confidence', 0)
        market = opportunity.get('market', '')
        odds = opportunity.get('odds', 1.0)
        
        # Base safety from confidence
        base_safety = confidence
        
        # Market safety multiplier
        market_multipliers = {
            'Under 5.5 Goals': 1.3,     # Very safe
            'Under 4.5 Goals': 1.25,    # Very safe  
            'Over 0.5 Goals': 1.2,      # Safe
            'Over 1.5 Goals': 1.1,      # Moderately safe
            'Double Chance': 1.15,      # Two outcomes
            'BTTS No': 1.05,           # Conservative
        }
        
        market_bonus = market_multipliers.get(market, 1.0)
        
        # Odds consistency bonus (closer to implied probability = safer)
        implied_prob = 1 / odds
        confidence_odds_alignment = 1 - abs(confidence - implied_prob)
        alignment_bonus = 1 + (confidence_odds_alignment * 0.1)
        
        safety_score = base_safety * market_bonus * alignment_bonus
        
        return min(safety_score, 1.0)  # Cap at 1.0
    
    def _decimal_to_american_odds(self, decimal_odds):
        """Convert decimal odds to American odds format"""
        if decimal_odds >= 2.0:
            return int((decimal_odds - 1) * 100)
        else:
            return int(-100 / (decimal_odds - 1))
    
    def _get_market_safety_rating(self, market):
        """Get safety rating for market type"""
        
        safety_ratings = {
            'Under 5.5 Goals': 'VERY_SAFE',
            'Under 4.5 Goals': 'VERY_SAFE',
            'Over 0.5 Goals': 'SAFE',
            'Over 1.5 Goals': 'MODERATELY_SAFE',
            'Double Chance': 'SAFE',
            'BTTS No': 'MODERATELY_SAFE',
            'Under 3.5 Goals': 'MODERATELY_SAFE',
            'Over 2.5 Goals': 'MODERATE_RISK',
            'BTTS Yes': 'MODERATE_RISK'
        }
        
        return safety_ratings.get(market, 'UNKNOWN')
    
    def _get_todays_opportunities(self):
        """Get today's opportunities from fixtures"""
        
        # Import real data integration
        from real_data_integration import RealDataIntegration
        
        try:
            integrator = RealDataIntegration()
            fixtures = integrator.update_daily_system_with_real_data(self.today)
            
            if not fixtures:
                return []
            
            # Analyze fixtures for opportunities
            opportunities = []
            for fixture in fixtures:
                fixture_opportunities = self.predictor.analyze_match(fixture)
                opportunities.extend(fixture_opportunities)
            
            return opportunities
            
        except Exception as e:
            print(f"❌ Error getting today's opportunities: {e}")
            return []
    
    def _save_high_confidence_csv(self, picks):
        """Save high confidence picks to CSV"""
        
        if not picks:
            return
        
        filename = f"output reports/high_confidence_picks_{self.today.replace('-', '')}.csv"
        
        fieldnames = [
            'date', 'kick_off', 'home_team', 'away_team', 'league', 'country',
            'market', 'odds', 'american_odds', 'confidence_percent', 'safety_score',
            'market_safety', 'recommended_stake', 'reasoning'
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for pick in picks:
                writer.writerow({
                    'date': self.today,
                    'kick_off': pick.get('kick_off', ''),
                    'home_team': pick.get('home_team', ''),
                    'away_team': pick.get('away_team', ''),
                    'league': pick.get('league', ''),
                    'country': pick.get('country', ''),
                    'market': pick.get('market', ''),
                    'odds': f"{pick.get('odds', 0):.2f}",
                    'american_odds': pick.get('american_odds', 0),
                    'confidence_percent': f"{pick.get('confidence', 0)*100:.1f}%",
                    'safety_score': f"{pick.get('safety_score', 0):.3f}",
                    'market_safety': pick.get('market_safety', ''),
                    'recommended_stake': '2-5%',  # Conservative staking for these
                    'reasoning': self._get_pick_reasoning(pick)
                })
        
        print(f"💾 High confidence CSV saved: {filename}")
    
    def _save_high_confidence_txt(self, report_data):
        """Save formatted high confidence report"""
        
        filename = f"output reports/high_confidence_report_{self.today.replace('-', '')}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("🎯 DAILY HIGH CONFIDENCE PICKS REPORT\n")
            f.write("="*50 + "\n")
            f.write(f"📅 Date: {report_data['date']}\n")
            f.write(f"🎪 Focus: High Probability Bets (85%+ Confidence)\n")
            f.write(f"💰 Odds Range: {report_data['criteria']['odds_range']}\n")
            f.write(f"📊 Total Analyzed: {report_data['total_analyzed']}\n")
            f.write(f"✅ High Confidence Picks: {report_data['high_confidence_picks']}\n\n")
            
            if not report_data['picks']:
                f.write("❌ No high confidence picks found today\n")
                f.write("   Try again tomorrow or lower confidence threshold\n")
                return
            
            f.write("🌟 TODAY'S HIGH CONFIDENCE PICKS:\n")
            f.write("="*40 + "\n\n")
            
            for i, pick in enumerate(report_data['picks'], 1):
                f.write(f"#{i} - {pick.get('kick_off', 'TBD')} | {pick.get('league', 'Unknown')}\n")
                f.write(f"   {pick.get('home_team', '')} vs {pick.get('away_team', '')}\n")
                f.write(f"   🎯 BET: {pick.get('market', '')}\n")
                f.write(f"   📊 ODDS: {pick.get('odds', 0):.2f} ({pick.get('american_odds', 0):+d})\n")
                f.write(f"   🎪 CONFIDENCE: {pick.get('confidence', 0)*100:.1f}%\n")
                f.write(f"   🛡️ SAFETY SCORE: {pick.get('safety_score', 0):.3f}\n")
                f.write(f"   📈 MARKET SAFETY: {pick.get('market_safety', 'Unknown')}\n")
                f.write(f"   💰 SUGGESTED STAKE: 2-5% of bankroll\n")
                f.write(f"   📝 REASONING: {self._get_pick_reasoning(pick)}\n\n")
            
            f.write("⚠️ HIGH CONFIDENCE BETTING NOTES:\n")
            f.write("-"*35 + "\n")
            f.write("• These picks prioritize WIN RATE over profit margins\n")
            f.write("• Use conservative staking (2-5% of bankroll)\n")
            f.write("• Good for parlay building or confidence building\n")
            f.write("• Lower expected value but higher hit rate\n")
            f.write("• Consider combining with main betting strategy\n")
        
        print(f"📄 High confidence report saved: {filename}")
    
    def _get_pick_reasoning(self, pick):
        """Generate reasoning text for pick"""
        
        confidence = pick.get('confidence', 0) * 100
        market = pick.get('market', '')
        odds = pick.get('odds', 0)
        
        reasoning_templates = {
            'Under 5.5 Goals': f"Extremely safe bet - {confidence:.0f}% confident total stays under 6 goals",
            'Under 4.5 Goals': f"Very safe bet - {confidence:.0f}% confident total stays under 5 goals",
            'Over 0.5 Goals': f"Safe bet - {confidence:.0f}% confident at least 1 goal scored",
            'Over 1.5 Goals': f"Moderately safe - {confidence:.0f}% confident at least 2 goals scored",
            'Double Chance': f"Two outcomes covered - {confidence:.0f}% confidence in prediction",
            'BTTS No': f"Conservative pick - {confidence:.0f}% confident one team blanked"
        }
        
        return reasoning_templates.get(market, f"{confidence:.0f}% confidence in {market} outcome")
    
    def _generate_empty_report(self):
        """Generate empty report structure"""
        return {
            'date': self.today,
            'total_analyzed': 0,
            'high_confidence_picks': 0,
            'picks': [],
            'message': 'No high confidence picks found today'
        }

def main():
    """Main function to run high confidence reporter"""
    
    # API key for data fetching
    API_KEY = "960c628e1c91c4b1f125e1eec52ad862"
    
    try:
        reporter = HighConfidenceReporter(API_KEY)
        report = reporter.generate_high_confidence_report()
        
        print("\n" + "="*60)
        print("🎯 HIGH CONFIDENCE REPORT COMPLETE")
        print("="*60)
        
        if report['high_confidence_picks'] > 0:
            print(f"✅ {report['high_confidence_picks']} high confidence picks generated")
            print("📊 Check output reports/ folder for detailed picks")
        else:
            print("❌ No high confidence picks found today")
            print("💡 Try again tomorrow or adjust criteria")
        
    except Exception as e:
        print(f"❌ Error generating high confidence report: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()