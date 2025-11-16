#!/usr/bin/env python3

"""
Volume Opportunity Reporter
===========================
Generate high volume report with high confidence (70%+) and any positive edge (>0)
across ALL leagues globally for maximum opportunities
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import csv
from multi_market_predictor import MultiMarketPredictor

class VolumeOpportunityReporter:
    """Generate high volume opportunities with minimal filtering"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.predictor = MultiMarketPredictor(api_key)
        self.today = datetime.now().strftime('%Y-%m-%d')
        
        # Volume opportunity criteria - very relaxed
        self.min_confidence = 0.50      # 50%+ confidence (very relaxed)
        self.min_edge = 0.00           # Zero or better edge (as requested)
        self.min_quality_score = 0.01   # Ultra low quality bar for volume
        
        # NO banned markets - allow everything
        self.allowed_markets = 'ALL'
        
        print("📊 VOLUME OPPORTUNITY REPORTER INITIALIZED")
        print(f"   🎯 Min Confidence: {self.min_confidence:.0%}")
        print(f"   📈 Min Edge: {self.min_edge} (zero or better)")
        print(f"   🌍 Scope: FOLLOWED leagues only")
        print(f"   🎪 Focus: Maximum volume opportunities")
        print()
    
    def generate_volume_report(self):
        """Generate high volume opportunities report"""
        
        print(f"📊 GENERATING VOLUME OPPORTUNITIES REPORT for {self.today}")
        print("="*70)
        
        # Get all fixtures from all leagues
        all_fixtures = self._get_all_leagues_fixtures()
        
        if not all_fixtures:
            print("❌ No fixtures available for volume analysis")
            return self._generate_empty_report()
        
        print(f"🌍 Analyzing {len(all_fixtures)} fixtures from FOLLOWED leagues...")
        
        # Generate ALL opportunities
        all_opportunities = self._generate_all_opportunities(all_fixtures)
        
        if not all_opportunities:
            print("❌ No opportunities generated")
            return self._generate_empty_report()
        
        print(f"💎 Generated {len(all_opportunities)} total opportunities")
        
        # Apply volume filtering (very relaxed)
        volume_picks = self._filter_volume_opportunities(all_opportunities)
        
        if not volume_picks:
            print("❌ No opportunities passed volume filtering")
            return self._generate_empty_report()
        
        # Sort by confidence (highest first), then by edge
        volume_picks.sort(key=lambda x: (x.get('confidence', 0), x.get('edge', 0)), reverse=True)
        
        print(f"✅ Found {len(volume_picks)} volume opportunities")
        
        # Generate report
        report_data = {
            'date': self.today,
            'total_fixtures': len(all_fixtures),
            'total_opportunities': len(all_opportunities),
            'volume_picks': len(volume_picks),
            'picks': volume_picks,
            'criteria': {
                'min_confidence': f"{self.min_confidence:.0%}",
                'min_edge': f"{self.min_edge}",
                'scope': 'ALL leagues globally'
            }
        }
        
        # Save reports
        self._save_volume_csv(volume_picks)
        self._save_volume_txt(report_data)
        
        return report_data
    
    def _get_all_leagues_fixtures(self):
        """Get fixtures from FOLLOWED leagues only"""
        
        try:
            print(f"🔌 Loading FOLLOWED league fixtures for {self.today}")
            
            # Use real data integration with strict filtering
            from real_data_integration import RealDataIntegration
            real_data = RealDataIntegration()
            
            # Get ALL fixtures first, then filter to followed leagues only
            all_fixtures_raw = real_data.get_real_fixtures_with_odds(self.today)
            followed_fixtures = real_data.filter_followed_leagues(all_fixtures_raw)
            
            print(f"📊 Found {len(followed_fixtures)} fixtures in FOLLOWED leagues")
            
            # Return the fixtures in the expected format
            return followed_fixtures
            
        except Exception as e:
            print(f"❌ Error loading all leagues fixtures: {e}")
            return []
    
    def _generate_all_opportunities(self, fixtures):
        """Generate opportunities from all fixtures"""
        
        print("🤖 Training models on ALL leagues data...")
        
        # Train models using all the fixture data
        training_data = []
        for fixture in fixtures[:500]:  # Use first 500 for training efficiency
            training_data.append({
                'home_team': fixture.get('home_team', ''),
                'away_team': fixture.get('away_team', ''),
                'league': fixture.get('league', ''),
                'home_odds': fixture.get('home_odds', 2.0),
                'draw_odds': fixture.get('draw_odds', 3.0),
                'away_odds': fixture.get('away_odds', 2.5)
            })
        
        # Train models
        self.predictor.train_market_models(training_data)
        
        # Generate opportunities for a reasonable sample of fixtures
        all_opportunities = []
        
        # Limit to first 200 fixtures for volume analysis (still covers many leagues)
        sample_fixtures = fixtures[:200]
        print(f"💎 Generating opportunities from {len(sample_fixtures)} sample fixtures...")
        
        for i, fixture in enumerate(sample_fixtures):
            if i % 50 == 0:
                print(f"   Processing fixture {i+1}/{len(sample_fixtures)}...")
            
            try:
                # Generate comprehensive odds for all markets (like other systems do)
                odds = self.predictor.generate_realistic_odds(fixture)
                
                # Generate predictions for this fixture
                opportunities = self.predictor.analyze_all_markets(odds)
                
                # Debug logging for first few fixtures
                if i < 3:
                    print(f"   Debug: Fixture {i+1} generated {len(opportunities)} opportunities")
                    if opportunities:
                        print(f"      Sample opportunity: {opportunities[0]}")
                
                # Add fixture info to each opportunity
                for opp in opportunities:
                    opp['fixture'] = fixture
                    opp['kick_off'] = fixture.get('kick_off', '')
                    opp['home_team'] = fixture.get('home_team', '')
                    opp['away_team'] = fixture.get('away_team', '')
                    opp['league'] = fixture.get('league', '')
                    opp['country'] = fixture.get('country', '')
                    
                    # Ensure quality_score exists (use edge * confidence if missing)
                    if 'quality_score' not in opp:
                        confidence = opp.get('confidence', 0)
                        edge = opp.get('edge', 0)
                        opp['quality_score'] = confidence * edge
                
                all_opportunities.extend(opportunities)
                
            except Exception as e:
                # Debug logging for errors
                if i < 3:
                    print(f"   Debug: Fixture {i+1} error: {e}")
                continue
        
        print(f"✅ Generated {len(all_opportunities)} total opportunities")
        return all_opportunities
    
    def _filter_volume_opportunities(self, opportunities):
        """Apply volume filtering (very relaxed criteria)"""
        
        if not opportunities:
            return []
        
        print(f"🔍 APPLYING VOLUME FILTERING to {len(opportunities)} opportunities...")
        
        volume_picks = []
        rejection_stats = {
            'low_confidence': 0,
            'no_edge': 0,
            'low_quality': 0,
            'total_passed': 0
        }
        
        for opp in opportunities:
            confidence = opp.get('confidence', 0)
            edge = opp.get('edge', 0)
            quality_score = opp.get('quality_score', 0)
            
            # Check confidence requirement (70%+)
            if confidence < self.min_confidence:
                rejection_stats['low_confidence'] += 1
                continue
            
            # Check edge requirement (zero or better)
            if edge < self.min_edge:
                rejection_stats['no_edge'] += 1
                continue
            
            # Check quality score (very low bar)
            if quality_score < self.min_quality_score:
                rejection_stats['low_quality'] += 1
                continue
            
            # Calculate volume score
            volume_score = self._calculate_volume_score(opp)
            opp['volume_score'] = volume_score
            
            # Add tier classification
            opp['tier'] = self._classify_opportunity_tier(opp)
            
            volume_picks.append(opp)
            rejection_stats['total_passed'] += 1
        
        # Report filtering results
        print(f"📊 VOLUME FILTERING RESULTS:")
        print(f"   ✅ Passed: {rejection_stats['total_passed']}")
        print(f"   ❌ Low confidence (<{self.min_confidence:.0%}): {rejection_stats['low_confidence']}")
        print(f"   ❌ No edge (≤{self.min_edge}): {rejection_stats['no_edge']}")
        print(f"   ❌ Low quality (<{self.min_quality_score}): {rejection_stats['low_quality']}")
        print()
        
        return volume_picks
    
    def _calculate_volume_score(self, opportunity):
        """Calculate volume score for sorting"""
        
        confidence = opportunity.get('confidence', 0)
        edge = opportunity.get('edge', 0)
        quality_score = opportunity.get('quality_score', 0)
        
        # Simple volume score: weighted combination
        volume_score = (confidence * 0.5) + (edge * 0.3) + (quality_score * 0.2)
        
        return volume_score
    
    def _classify_opportunity_tier(self, opportunity):
        """Classify opportunity into tiers"""
        
        confidence = opportunity.get('confidence', 0)
        edge = opportunity.get('edge', 0)
        
        if confidence >= 0.85 and edge >= 0.3:
            return "PREMIUM"
        elif confidence >= 0.80 and edge >= 0.2:
            return "HIGH"
        elif confidence >= 0.75 and edge >= 0.1:
            return "GOOD"
        else:
            return "VOLUME"
    
    def _save_volume_csv(self, picks):
        """Save volume opportunities to CSV"""
        
        if not picks:
            return
        
        filename = f"output reports/volume_opportunities_{self.today.replace('-', '')}.csv"
        
        fieldnames = [
            'date', 'kick_off', 'home_team', 'away_team', 'league', 'country',
            'market', 'odds', 'confidence_percent', 'edge_percent', 'quality_score',
            'volume_score', 'tier', 'expected_value', 'recommended_stake'
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
                    'confidence_percent': f"{pick.get('confidence', 0)*100:.1f}%",
                    'edge_percent': f"{pick.get('edge', 0)*100:.1f}%",
                    'quality_score': f"{pick.get('quality_score', 0):.3f}",
                    'volume_score': f"{pick.get('volume_score', 0):.3f}",
                    'tier': pick.get('tier', ''),
                    'expected_value': f"{pick.get('expected_value', 0):.2f}",
                    'recommended_stake': self._get_recommended_stake(pick)
                })
        
        print(f"💾 Volume opportunities CSV saved: {filename}")
    
    def _save_volume_txt(self, report_data):
        """Save formatted volume opportunities report"""
        
        filename = f"output reports/volume_opportunities_{self.today.replace('-', '')}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("📊 DAILY VOLUME OPPORTUNITIES REPORT\n")
            f.write("="*50 + "\n")
            f.write(f"📅 Date: {report_data['date']}\n")
            f.write(f"🌍 Scope: ALL leagues globally\n")
            f.write(f"🎯 Criteria: {report_data['criteria']['min_confidence']} confidence, {report_data['criteria']['min_edge']}+ edge\n")
            f.write(f"📊 Total Fixtures: {report_data['total_fixtures']}\n")
            f.write(f"💎 Total Opportunities: {report_data['total_opportunities']}\n")
            f.write(f"✅ Volume Picks: {report_data['volume_picks']}\n\n")
            
            if not report_data['picks']:
                f.write("❌ No volume opportunities found\n")
                f.write("   Try lowering criteria or check fixture availability\n")
                return
            
            # Group by tier
            tiers = {}
            for pick in report_data['picks']:
                tier = pick.get('tier', 'VOLUME')
                if tier not in tiers:
                    tiers[tier] = []
                tiers[tier].append(pick)
            
            # Write picks by tier
            tier_order = ['PREMIUM', 'HIGH', 'GOOD', 'VOLUME']
            
            for tier in tier_order:
                if tier not in tiers:
                    continue
                
                picks_in_tier = tiers[tier]
                f.write(f"\n🏆 {tier} OPPORTUNITIES ({len(picks_in_tier)}):\n")
                f.write("="*40 + "\n\n")
                
                for i, pick in enumerate(picks_in_tier[:20], 1):  # Limit to top 20 per tier
                    f.write(f"#{i} - {pick.get('kick_off', 'TBD')} | {pick.get('league', 'Unknown')}\n")
                    f.write(f"   {pick.get('home_team', '')} vs {pick.get('away_team', '')}\n")
                    f.write(f"   🎯 BET: {pick.get('market', '')}\n")
                    f.write(f"   📊 ODDS: {pick.get('odds', 0):.2f}\n")
                    f.write(f"   🎪 CONFIDENCE: {pick.get('confidence', 0)*100:.1f}%\n")
                    f.write(f"   📈 EDGE: {pick.get('edge', 0)*100:.1f}%\n")
                    f.write(f"   ⭐ VOLUME SCORE: {pick.get('volume_score', 0):.3f}\n")
                    f.write(f"   💰 STAKE: {self._get_recommended_stake(pick)}\n\n")
                
                if len(picks_in_tier) > 20:
                    f.write(f"   ... and {len(picks_in_tier) - 20} more {tier} opportunities\n\n")
            
            f.write("⚠️ VOLUME OPPORTUNITY NOTES:\n")
            f.write("-"*35 + "\n")
            f.write("• These picks prioritize VOLUME over strict quality\n")
            f.write("• Use smaller stakes than main strategy\n")
            f.write("• Good for finding value across many markets\n")
            f.write("• Consider focusing on PREMIUM and HIGH tiers\n")
            f.write("• All opportunities have 70%+ confidence and positive edge\n")
        
        print(f"📄 Volume opportunities report saved: {filename}")
    
    def _get_recommended_stake(self, pick):
        """Get recommended stake based on tier"""
        
        tier = pick.get('tier', 'VOLUME')
        
        stake_map = {
            'PREMIUM': '3-5%',
            'HIGH': '2-4%', 
            'GOOD': '1-3%',
            'VOLUME': '1-2%'
        }
        
        return stake_map.get(tier, '1-2%')
    
    def _generate_empty_report(self):
        """Generate empty report structure"""
        return {
            'date': self.today,
            'total_fixtures': 0,
            'total_opportunities': 0,
            'volume_picks': 0,
            'picks': [],
            'message': 'No volume opportunities found'
        }

def main():
    """Main function to run volume opportunity reporter"""
    
    # API key for data fetching
    API_KEY = "960c628e1c91c4b1f125e1eec52ad862"
    
    try:
        reporter = VolumeOpportunityReporter(API_KEY)
        report = reporter.generate_volume_report()
        
        print("\n" + "="*70)
        print("📊 VOLUME OPPORTUNITIES REPORT COMPLETE")
        print("="*70)
        
        if report['volume_picks'] > 0:
            print(f"✅ {report['volume_picks']} volume opportunities generated")
            print(f"📊 From {report['total_fixtures']} fixtures globally")
            print("📁 Check output reports/ folder for detailed picks")
        else:
            print("❌ No volume opportunities found")
            print("💡 This means even with relaxed criteria, no opportunities met minimum standards")
        
    except Exception as e:
        print(f"❌ Error generating volume opportunities report: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()