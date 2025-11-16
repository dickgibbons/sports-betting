#!/usr/bin/env python3
"""
High Confidence Favorites Report

Generates a separate report for highest confidence Over 1.5 Goals bets
with odds below -400 (1.25 decimal), regardless of value metrics
"""

import pandas as pd
from datetime import datetime
from typing import List, Dict
import json

class HighConfidenceFavoritesReport:
    """Generate report for high-confidence Over 1.5 Goals favorites"""
    
    def __init__(self):
        self.max_decimal_odds = 1.25  # Equivalent to -400 American odds
        self.min_confidence = 70.0    # High confidence threshold
        
        print("🎯 High Confidence Favorites Report Generator Initialized")
        print(f"   📊 Target: Over 1.5 Goals with odds ≤ {self.max_decimal_odds}")
        print(f"   🎪 Minimum Confidence: {self.min_confidence}%")
    
    def generate_favorites_report(self, all_predictions: List[Dict]) -> List[Dict]:
        """Generate high confidence favorites report"""
        
        if not all_predictions:
            print("❌ No predictions available for favorites analysis")
            return []
        
        print(f"🔍 Analyzing {len(all_predictions)} predictions for high-confidence favorites...")
        
        # Filter for Over 1.5 Goals bets with short odds
        favorites = []
        
        for pred in all_predictions:
            bet_description = pred.get('bet_description', '').lower()
            odds = pred.get('odds', 999)
            confidence = pred.get('confidence_pct', 0)
            
            # Check if it's Over 1.5 Goals
            if 'over 1.5' in bet_description and 'goals' in bet_description:
                # Check if odds are short enough (≤ 1.25 = -400)
                if odds <= self.max_decimal_odds:
                    # Check if confidence meets threshold
                    if confidence >= self.min_confidence:
                        
                        # Add additional metrics for favorites
                        pred['american_odds'] = self.decimal_to_american(odds)
                        pred['implied_probability'] = (1 / odds) * 100
                        pred['confidence_edge'] = confidence - pred['implied_probability']
                        
                        favorites.append(pred)
        
        # Sort by confidence (highest first)
        favorites.sort(key=lambda x: x.get('confidence_pct', 0), reverse=True)
        
        print(f"   ✅ Found {len(favorites)} high-confidence Over 1.5 Goals favorites")
        
        if favorites:
            self.save_favorites_report(favorites)
        
        return favorites
    
    def decimal_to_american(self, decimal_odds: float) -> str:
        """Convert decimal odds to American odds format"""
        
        if decimal_odds >= 2.0:
            american = (decimal_odds - 1) * 100
            return f"+{american:.0f}"
        else:
            american = -100 / (decimal_odds - 1)
            return f"{american:.0f}"
    
    def save_favorites_report(self, favorites: List[Dict]):
        """Save the high confidence favorites report"""
        
        if not favorites:
            return
        
        date_str = datetime.now().strftime('%Y%m%d')
        
        # Create detailed report
        report_content = self.create_detailed_report(favorites)
        
        # Save text report
        report_file = f"./soccer/output reports/high_confidence_favorites_{date_str}.txt"
        with open(report_file, 'w') as f:
            f.write(report_content)
        
        # Save CSV data
        csv_file = f"./soccer/output reports/high_confidence_favorites_{date_str}.csv"
        df = pd.DataFrame(favorites)
        
        # Select relevant columns for CSV
        columns = ['date', 'kick_off', 'home_team', 'away_team', 'league', 'bet_description', 
                  'odds', 'american_odds', 'confidence_pct', 'implied_probability', 
                  'confidence_edge', 'edge_pct', 'expected_value', 'quality_score']
        
        # Only include columns that exist
        available_columns = [col for col in columns if col in df.columns]
        df[available_columns].to_csv(csv_file, index=False)
        
        print(f"📊 High confidence favorites report saved:")
        print(f"   📋 Text report: {report_file}")
        print(f"   📊 CSV data: {csv_file}")
    
    def create_detailed_report(self, favorites: List[Dict]) -> str:
        """Create detailed text report for favorites"""
        
        if not favorites:
            return "No high confidence favorites found."
        
        # Calculate summary stats
        total_favorites = len(favorites)
        avg_confidence = sum([f.get('confidence_pct', 0) for f in favorites]) / total_favorites
        avg_odds = sum([f.get('odds', 0) for f in favorites]) / total_favorites
        highest_confidence = max([f.get('confidence_pct', 0) for f in favorites])
        
        # Group by league
        league_counts = {}
        for fav in favorites:
            league = fav.get('league', 'Unknown')
            league_counts[league] = league_counts.get(league, 0) + 1
        
        report_content = f"""
🎯 HIGH CONFIDENCE OVER 1.5 GOALS FAVORITES REPORT
==================================================
📅 Date: {datetime.now().strftime('%A, %B %d, %Y')}
📊 Criteria: Over 1.5 Goals, Odds ≤ {self.max_decimal_odds} (-400), Confidence ≥ {self.min_confidence}%

📈 SUMMARY STATISTICS:
----------------------
🎯 Total High Confidence Favorites: {total_favorites}
🎪 Average Confidence: {avg_confidence:.1f}%
📊 Average Decimal Odds: {avg_odds:.2f}
⭐ Highest Confidence: {highest_confidence:.1f}%

🏆 LEAGUE DISTRIBUTION:
-----------------------"""
        
        for league, count in sorted(league_counts.items(), key=lambda x: x[1], reverse=True):
            report_content += f"\n📊 {league}: {count} match{'es' if count > 1 else ''}"
        
        report_content += f"""

🌟 HIGH CONFIDENCE FAVORITES:
============================="""
        
        for i, fav in enumerate(favorites, 1):
            home_team = fav.get('home_team', 'Unknown')
            away_team = fav.get('away_team', 'Unknown')
            league = fav.get('league', 'Unknown')
            kick_off = fav.get('kick_off', 'TBD')
            odds = fav.get('odds', 0)
            american_odds = fav.get('american_odds', 'N/A')
            confidence = fav.get('confidence_pct', 0)
            implied_prob = fav.get('implied_probability', 0)
            confidence_edge = fav.get('confidence_edge', 0)
            
            report_content += f"""

#{i} - {kick_off} | {league}
   {home_team} vs {away_team}
   🎯 BET: Over 1.5 Goals
   📊 ODDS: {odds:.2f} ({american_odds})
   🎪 CONFIDENCE: {confidence:.1f}%
   📈 IMPLIED PROBABILITY: {implied_prob:.1f}%
   ⚡ CONFIDENCE EDGE: {confidence_edge:+.1f}%"""
            
            # Add value metrics if available
            if 'edge_pct' in fav and fav['edge_pct'] is not None:
                report_content += f"""
   💰 VALUE EDGE: {fav['edge_pct']:.1f}%"""
            
            if 'expected_value' in fav and fav['expected_value'] is not None:
                report_content += f"""
   💵 EXPECTED VALUE: ${fav['expected_value']:+.2f}"""
        
        report_content += f"""

📊 BETTING STRATEGY FOR FAVORITES:
===================================

💡 APPROACH:
• These are low-value, high-probability bets
• Use for accumulator building or safe bankroll growth
• Consider larger position sizes due to high confidence
• Perfect for conservative betting strategies

⚠️ IMPORTANT NOTES:
• Odds below -400 offer limited value but high safety
• High confidence doesn't guarantee wins
• Consider combining multiple favorites for better returns
• Monitor for line movement that might improve value

🎯 CONFIDENCE INTERPRETATION:
• 85%+ Confidence: Extremely likely to hit
• 80-85% Confidence: Very strong probability
• 75-80% Confidence: Strong probability
• 70-75% Confidence: Good probability

📋 Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📊 Total Opportunities: {total_favorites} high-confidence favorites identified
"""
        
        return report_content

def main():
    """Test the high confidence favorites report"""
    
    # Sample test data
    test_predictions = [
        {
            'date': '2025-09-10',
            'kick_off': '15:00',
            'home_team': 'Manchester City',
            'away_team': 'Sheffield United',
            'league': 'Premier League',
            'bet_description': 'Over 1.5 Goals',
            'odds': 1.18,
            'confidence_pct': 89.5,
            'edge_pct': 12.3,
            'expected_value': 3.85
        },
        {
            'date': '2025-09-10',
            'kick_off': '17:30',
            'home_team': 'Barcelona',
            'away_team': 'Real Valladolid',
            'league': 'La Liga',
            'bet_description': 'Over 1.5 Goals',
            'odds': 1.22,
            'confidence_pct': 86.2,
            'edge_pct': 4.1,
            'expected_value': 0.95
        },
        {
            'date': '2025-09-10',
            'kick_off': '20:00',
            'home_team': 'Bayern Munich',
            'away_team': 'Augsburg',
            'league': 'Bundesliga',
            'bet_description': 'Over 1.5 Goals',
            'odds': 1.30,  # Too high odds, should be filtered out
            'confidence_pct': 82.1,
            'edge_pct': -2.5,
            'expected_value': -0.45
        }
    ]
    
    generator = HighConfidenceFavoritesReport()
    favorites = generator.generate_favorites_report(test_predictions)
    
    print(f"\n✅ Test complete - found {len(favorites)} qualifying favorites")

if __name__ == "__main__":
    main()