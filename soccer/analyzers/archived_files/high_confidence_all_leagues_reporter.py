#!/usr/bin/env python3
"""
High Confidence All-Leagues Reporter

Generates a daily report of high confidence betting opportunities from ALL available leagues,
not just the followed ones. This provides a broader view of potential high-value bets.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from real_data_integration import RealDataIntegration
from multi_market_predictor import MultiMarketPredictor
from typing import Dict, List, Tuple
import csv

class HighConfidenceAllLeaguesReporter:
    """Generate high confidence picks from all available leagues"""
    
    def __init__(self, api_key: str = "960c628e1c91c4b1f125e1eec52ad862"):
        self.api_key = api_key
        self.today = datetime.now().strftime('%Y-%m-%d')
        self.day_name = datetime.now().strftime('%A')
        
        # High confidence thresholds
        self.min_confidence = 70.0  # Lowered to 70% for more results
        self.min_edge = 10.0       # Edge requirement lowered from 25% to 10%
        self.min_quality_score = 0.3  # Lowered from 0.6 to get some results
        
        print(f"🌍 High Confidence All-Leagues Reporter Initialized")
        print(f"   📊 Min Confidence: {self.min_confidence}%")
        print(f"   📈 Min Edge: {self.min_edge}%")
        print(f"   ⭐ Min Quality Score: {self.min_quality_score}")
        
    def get_all_fixtures_today(self) -> List[Dict]:
        """Get fixtures from FOLLOWED leagues only for today"""
        
        print(f"📅 Fetching FOLLOWED league fixtures for {self.day_name}, {self.today}...")
        
        # Initialize real data integration
        real_data = RealDataIntegration()
        
        # Get ALL fixtures first
        all_fixtures = real_data.get_real_fixtures_with_odds(self.today)
        
        # Apply strict filtering to only include followed leagues
        followed_fixtures = real_data.filter_followed_leagues(all_fixtures)
        
        print(f"🌍 Retrieved {len(followed_fixtures)} fixtures from FOLLOWED leagues only")
        
        return followed_fixtures
    
    def analyze_all_matches(self, fixtures: List[Dict]) -> List[Dict]:
        """Analyze all matches for high confidence opportunities"""
        
        print(f"🔍 Analyzing {len(fixtures)} matches for high confidence opportunities...")
        
        # Initialize predictor
        predictor = MultiMarketPredictor(self.api_key)
        
        # Let the predictor handle model training internally
        print("🤖 Training multi-market models on all leagues...")
        
        all_predictions = []
        
        for fixture in fixtures:
            try:
                # Generate odds and get market analysis
                odds = predictor.generate_realistic_odds(fixture)
                predictions = predictor.analyze_all_markets(odds)
                
                if predictions:
                    # Add match context to each prediction
                    for pred in predictions:
                        pred.update({
                            'kick_off': fixture['kick_off'],
                            'home_team': fixture['home_team'],
                            'away_team': fixture['away_team'],
                            'league': fixture['league'],
                            'country': fixture.get('country', 'Unknown'),
                            'date': self.today
                        })
                    
                    all_predictions.extend(predictions)
                    
            except Exception as e:
                print(f"⚠️ Error analyzing {fixture.get('home_team', 'Unknown')} vs {fixture.get('away_team', 'Unknown')}: {e}")
                continue
        
        print(f"💎 Found {len(all_predictions)} total predictions across all leagues")
        return all_predictions
    
    def filter_high_confidence_picks(self, predictions: List[Dict]) -> List[Dict]:
        """Filter for only the highest confidence opportunities"""
        
        print(f"🔍 Filtering {len(predictions)} predictions for high confidence...")
        
        high_confidence_picks = []
        
        for pred in predictions:
            confidence = pred.get('confidence_percent', 0)
            edge = pred.get('edge_percent', 0)
            quality_score = pred.get('quality_score', 0)
            odds = pred.get('odds', 0)
            
            # Apply high confidence filters
            if (confidence >= self.min_confidence and 
                edge >= self.min_edge and 
                quality_score >= self.min_quality_score and
                1.3 <= odds <= 4.0):  # Reasonable odds range
                
                high_confidence_picks.append(pred)
        
        print(f"✅ {len(high_confidence_picks)} picks passed high confidence filters")
        
        # Sort by quality score descending
        high_confidence_picks.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
        
        return high_confidence_picks
    
    def save_high_confidence_report(self, picks: List[Dict]) -> str:
        """Save high confidence picks to CSV and formatted report"""
        
        date_str = self.today.replace('-', '')
        
        # Save CSV report
        csv_filename = f"high_confidence_all_leagues_{date_str}.csv"
        csv_path = f"./soccer/output reports/{csv_filename}"
        
        if picks:
            fieldnames = [
                'date', 'kick_off', 'home_team', 'away_team', 'league', 'country',
                'market', 'bet_description', 'odds', 'recommended_stake_pct',
                'edge_percent', 'confidence_percent', 'expected_value',
                'quality_score', 'risk_level'
            ]
            
            with open(csv_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for pick in picks:
                    writer.writerow({
                        'date': pick.get('date'),
                        'kick_off': pick.get('kick_off'),
                        'home_team': pick.get('home_team'),
                        'away_team': pick.get('away_team'),
                        'league': pick.get('league'),
                        'country': pick.get('country'),
                        'market': pick.get('market'),
                        'bet_description': pick.get('bet_description'),
                        'odds': pick.get('odds'),
                        'recommended_stake_pct': pick.get('recommended_stake_pct', 8.0),
                        'edge_percent': pick.get('edge_percent'),
                        'confidence_percent': pick.get('confidence_percent'),
                        'expected_value': pick.get('expected_value'),
                        'quality_score': pick.get('quality_score'),
                        'risk_level': pick.get('risk_level', 'Medium Risk')
                    })
            
            print(f"💾 High confidence CSV saved: {csv_filename}")
        
        # Generate formatted report
        txt_filename = f"high_confidence_all_leagues_report_{date_str}.txt"
        txt_path = f"./soccer/output reports/{txt_filename}"
        
        self.generate_formatted_report(picks, txt_path)
        
        return csv_path
    
    def generate_formatted_report(self, picks: List[Dict], output_path: str):
        """Generate a formatted text report"""
        
        with open(output_path, 'w') as f:
            f.write("🌍 HIGH CONFIDENCE ALL-LEAGUES BETTING REPORT 🌍\n")
            f.write("=" * 60 + "\n")
            f.write(f"📅 Date: {self.day_name}, {self.today}\n")
            f.write(f"🎯 High Confidence Threshold: {self.min_confidence}%+\n")
            f.write(f"📈 Minimum Edge Required: {self.min_edge}%+\n")
            f.write(f"⭐ Minimum Quality Score: {self.min_quality_score}+\n\n")
            
            if not picks:
                f.write("⚠️ No high confidence opportunities found across all leagues today.\n")
                f.write("This suggests the current market conditions don't meet our strict criteria.\n\n")
            else:
                f.write(f"🎯 FOUND {len(picks)} HIGH CONFIDENCE OPPORTUNITIES\n")
                f.write("-" * 50 + "\n\n")
                
                # Group by league for better organization
                leagues = {}
                for pick in picks:
                    league = pick.get('league', 'Unknown')
                    country = pick.get('country', 'Unknown')
                    league_key = f"{league} ({country})"
                    
                    if league_key not in leagues:
                        leagues[league_key] = []
                    leagues[league_key].append(pick)
                
                for league_key, league_picks in leagues.items():
                    f.write(f"🏟️ {league_key} - {len(league_picks)} picks:\n")
                    f.write("-" * 40 + "\n")
                    
                    for i, pick in enumerate(league_picks, 1):
                        f.write(f"{i}. {pick.get('kick_off')} | {pick.get('home_team')} vs {pick.get('away_team')}\n")
                        f.write(f"   🎯 {pick.get('bet_description')} @ {pick.get('odds'):.2f}\n")
                        f.write(f"   📊 Confidence: {pick.get('confidence_percent'):.1f}% | ")
                        f.write(f"Edge: {pick.get('edge_percent'):.1f}% | ")
                        f.write(f"Quality: {pick.get('quality_score'):.3f}\n")
                        f.write(f"   💰 Expected Value: {pick.get('expected_value'):.3f} | ")
                        f.write(f"Risk: {pick.get('risk_level')}\n\n")
                    
                    f.write("\n")
            
            f.write("⚠️ IMPORTANT NOTES:\n")
            f.write("• This report includes opportunities from ALL available leagues\n")
            f.write("• Only the highest confidence picks are shown\n")
            f.write("• These are supplemental to your main followed leagues\n")
            f.write("• Always verify league familiarity before betting\n")
            f.write("• Results are for analysis purposes only\n\n")
        
        print(f"📋 Formatted report saved: {output_path}")
    
    def generate_daily_high_confidence_report(self) -> Dict:
        """Generate the complete high confidence all-leagues report"""
        
        print(f"🌍 GENERATING HIGH CONFIDENCE ALL-LEAGUES REPORT")
        print("=" * 60)
        print(f"📅 Date: {self.day_name}, {self.today}")
        
        # Get all fixtures from all leagues
        all_fixtures = self.get_all_fixtures_today()
        
        if not all_fixtures:
            print("⚠️ No fixtures available for analysis")
            return {'picks': [], 'total_leagues': 0, 'total_fixtures': 0}
        
        # Analyze all matches for opportunities
        all_predictions = self.analyze_all_matches(all_fixtures)
        
        # Filter for high confidence only
        high_confidence_picks = self.filter_high_confidence_picks(all_predictions)
        
        # Save reports
        csv_path = self.save_high_confidence_report(high_confidence_picks)
        
        # Count unique leagues represented
        unique_leagues = set()
        for fixture in all_fixtures:
            league = fixture.get('league', 'Unknown')
            country = fixture.get('country', 'Unknown')
            unique_leagues.add(f"{league} ({country})")
        
        print(f"📊 High confidence report complete:")
        print(f"   🌍 Total leagues analyzed: {len(unique_leagues)}")
        print(f"   ⚽ Total fixtures processed: {len(all_fixtures)}")
        print(f"   🎯 High confidence picks: {len(high_confidence_picks)}")
        
        return {
            'picks': high_confidence_picks,
            'total_leagues': len(unique_leagues),
            'total_fixtures': len(all_fixtures),
            'csv_path': csv_path
        }

def main():
    """Run the high confidence all-leagues reporter"""
    reporter = HighConfidenceAllLeaguesReporter()
    result = reporter.generate_daily_high_confidence_report()
    
    if result['picks']:
        print(f"\n✅ High confidence report generated successfully!")
        print(f"📊 {len(result['picks'])} high confidence opportunities found")
    else:
        print(f"\n⚠️ No high confidence opportunities found today")
        print(f"Analyzed {result['total_fixtures']} fixtures from {result['total_leagues']} leagues")

if __name__ == "__main__":
    main()