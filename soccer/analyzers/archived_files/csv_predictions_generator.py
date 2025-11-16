#!/usr/bin/env python3
"""
CSV Predictions Generator for Soccer Betting

Generates comprehensive predictions for multiple betting markets:
- BTTS (Both Teams to Score)
- Over/Under Goals (1.5, 2.5, 3.5)
- Match Winner (1X2)
- Corners Over/Under
- And more betting markets

Outputs results to CSV files for easy analysis and tracking.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import csv
import os
from multi_league_predictor import MultiLeaguePredictor
from enhanced_soccer_predictor import BettingPredictor


class CSVPredictionsGenerator:
    """Generate comprehensive betting predictions and export to CSV"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.multi_league_predictor = MultiLeaguePredictor(api_key)
        self.basic_predictor = BettingPredictor(api_key)
        self.predictions = []
        
    def load_models(self):
        """Load existing models"""
        multi_loaded = self.multi_league_predictor.load_models("multi_league_models.pkl")
        basic_loaded = self.basic_predictor.load_models("soccer_prediction_models.pkl")
        
        return multi_loaded or basic_loaded
    
    def predict_betting_markets(self, match_data):
        """Generate predictions for all betting markets"""
        
        # Basic match info
        home_odds = match_data.get('home_odds', 2.0)
        draw_odds = match_data.get('draw_odds', 3.0)
        away_odds = match_data.get('away_odds', 2.0)
        league = match_data.get('league', 'Unknown')
        
        # Get base predictions from multi-league predictor
        base_predictions = self.multi_league_predictor.predict_match(
            home_odds, draw_odds, away_odds, league=league
        )
        
        # Initialize prediction record
        prediction_record = {
            'date': match_data.get('date', datetime.now().strftime('%Y-%m-%d')),
            'time': match_data.get('time', '15:00'),
            'league': league,
            'home_team': match_data.get('home_team', 'Home Team'),
            'away_team': match_data.get('away_team', 'Away Team'),
            'home_odds': home_odds,
            'draw_odds': draw_odds,
            'away_odds': away_odds,
        }
        
        # Get the best prediction from available models
        best_model = self.get_best_model_prediction(base_predictions)
        
        if best_model:
            probs = best_model['probabilities']
            
            # 1X2 Predictions
            prediction_record.update({
                'winner_prediction': best_model['prediction'],
                'winner_confidence': best_model['confidence'],
                'home_win_prob': probs['home_win'],
                'draw_prob': probs['draw'],
                'away_win_prob': probs['away_win'],
            })
            
            # BTTS Predictions
            btts_prob = self.calculate_btts_probability(match_data, probs)
            prediction_record.update({
                'btts_yes_prob': btts_prob,
                'btts_no_prob': 1 - btts_prob,
                'btts_prediction': 'YES' if btts_prob > 0.5 else 'NO',
                'btts_confidence': abs(btts_prob - 0.5) * 2,  # Scale to 0-1
            })
            
            # Over/Under Goals Predictions
            goals_predictions = self.calculate_goals_predictions(match_data, probs)
            prediction_record.update(goals_predictions)
            
            # Corners Predictions
            corners_predictions = self.calculate_corners_predictions(match_data, probs)
            prediction_record.update(corners_predictions)
            
            # Cards Predictions
            cards_predictions = self.calculate_cards_predictions(match_data, probs)
            prediction_record.update(cards_predictions)
            
            # Additional Markets
            additional_predictions = self.calculate_additional_markets(match_data, probs)
            prediction_record.update(additional_predictions)
            
            # Value Betting Analysis
            value_analysis = self.analyze_market_values(match_data, prediction_record)
            prediction_record.update(value_analysis)
        
        return prediction_record
    
    def get_best_model_prediction(self, predictions):
        """Get the best prediction from available models"""
        if not predictions:
            return None
        
        # Prefer league-specific models
        if 'league_specific' in predictions:
            return predictions['league_specific']
        
        # Fall back to global models, prefer gradient boosting
        if 'gradient_boosting' in predictions:
            return predictions['gradient_boosting']
        
        if 'random_forest' in predictions:
            return predictions['random_forest']
        
        # Return any available prediction
        return list(predictions.values())[0]
    
    def calculate_btts_probability(self, match_data, win_probs):
        """Calculate Both Teams to Score probability"""
        
        # Get odds-based probability if available
        btts_yes_odds = match_data.get('btts_yes_odds')
        if btts_yes_odds and btts_yes_odds > 0:
            market_btts_prob = 1 / btts_yes_odds
        else:
            market_btts_prob = 0.5
        
        # Calculate based on match dynamics
        home_win_prob = win_probs['home_win']
        away_win_prob = win_probs['away_win']
        draw_prob = win_probs['draw']
        
        # BTTS more likely in competitive matches
        competitiveness = 1 - abs(home_win_prob - away_win_prob)
        
        # Base BTTS probability adjusted by competitiveness and league factors
        base_btts = 0.52  # Historical average
        league_factor = self.get_league_btts_factor(match_data.get('league'))
        
        btts_prob = base_btts + (competitiveness * 0.15) + league_factor
        
        # Blend with market probability
        if btts_yes_odds:
            btts_prob = (btts_prob * 0.7) + (market_btts_prob * 0.3)
        
        return max(0.1, min(0.9, btts_prob))
    
    def get_league_btts_factor(self, league):
        """Get league-specific BTTS adjustment factor"""
        league_factors = {
            'Premier League': 0.05,
            'La Liga': 0.02,
            'Bundesliga': 0.08,
            'Serie A': -0.03,
            'Ligue 1': 0.01,
            'MLS': 0.12,
            'Liga MX': 0.08,
            'Brazil Serie A': 0.06,
            'FIFA Club World Cup': 0.08,
            'FIFA Club World Cup Playin': 0.10,
            # World Cup Qualifications
            'WC Qualification Europe': 0.03,
            'WC Qualification Africa': 0.08,
            'WC Qualification Asia': 0.05,
            'WC Qualification South America': 0.12,
            'WC Qualification CONCACAF': 0.10,
            'WC Qualification Oceania': 0.15,
            # English Lower Tier
            'FA Trophy': 0.12,
        }
        return league_factors.get(league, 0.0)
    
    def calculate_goals_predictions(self, match_data, win_probs):
        """Calculate Over/Under goals predictions"""
        
        # Estimate total goals based on team strengths and match dynamics
        home_strength = 1.0 + (win_probs['home_win'] - 0.33) * 2
        away_strength = 1.0 + (win_probs['away_win'] - 0.33) * 2
        
        # Expected goals calculation
        expected_goals = (home_strength + away_strength) * 1.2
        
        # Adjust for league characteristics
        league_goal_factor = self.get_league_goals_factor(match_data.get('league'))
        expected_goals *= league_goal_factor
        
        # Calculate probabilities using Poisson distribution approximation
        def goals_probability(threshold, expected):
            # Simplified probability calculation
            if expected <= 0:
                return 0.1
            
            # Use exponential decay for over probabilities
            over_prob = np.exp(-(threshold - expected) / expected) if threshold > expected else 0.8
            return max(0.05, min(0.95, over_prob))
        
        return {
            'expected_goals': expected_goals,
            'over_0_5_prob': goals_probability(0.5, expected_goals),
            'over_1_5_prob': goals_probability(1.5, expected_goals),
            'over_2_5_prob': goals_probability(2.5, expected_goals),
            'over_3_5_prob': goals_probability(3.5, expected_goals),
            'over_4_5_prob': goals_probability(4.5, expected_goals),
            'under_0_5_prob': 1 - goals_probability(0.5, expected_goals),
            'under_1_5_prob': 1 - goals_probability(1.5, expected_goals),
            'under_2_5_prob': 1 - goals_probability(2.5, expected_goals),
            'under_3_5_prob': 1 - goals_probability(3.5, expected_goals),
            'under_4_5_prob': 1 - goals_probability(4.5, expected_goals),
            'goals_prediction_0_5': 'OVER' if goals_probability(0.5, expected_goals) > 0.5 else 'UNDER',
            'goals_prediction_1_5': 'OVER' if goals_probability(1.5, expected_goals) > 0.5 else 'UNDER',
            'goals_prediction_2_5': 'OVER' if goals_probability(2.5, expected_goals) > 0.5 else 'UNDER',
            'goals_prediction_3_5': 'OVER' if goals_probability(3.5, expected_goals) > 0.5 else 'UNDER',
        }
    
    def get_league_goals_factor(self, league):
        """Get league-specific goals adjustment factor"""
        league_factors = {
            'Premier League': 1.05,
            'La Liga': 0.98,
            'Bundesliga': 1.12,
            'Serie A': 0.92,
            'Ligue 1': 1.02,
            'MLS': 1.08,
            'Liga MX': 1.15,
            'Brazil Serie A': 1.06,
            'Championship': 1.03,
            'FIFA Club World Cup': 1.10,
            'FIFA Club World Cup Playin': 1.15,
            # World Cup Qualifications
            'WC Qualification Europe': 1.02,
            'WC Qualification Africa': 1.08,
            'WC Qualification Asia': 0.98,
            'WC Qualification South America': 1.15,
            'WC Qualification CONCACAF': 1.12,
            'WC Qualification Oceania': 1.20,
            # English Lower Tier
            'FA Trophy': 1.05,
        }
        return league_factors.get(league, 1.0)
    
    def calculate_corners_predictions(self, match_data, win_probs):
        """Calculate corners over/under predictions"""
        
        # Base corners expectation
        base_corners = 10.5
        
        # Adjust based on match competitiveness
        competitiveness = 1 - abs(win_probs['home_win'] - win_probs['away_win'])
        expected_corners = base_corners + (competitiveness * 2)
        
        # League adjustment
        league_corner_factor = self.get_league_corners_factor(match_data.get('league'))
        expected_corners *= league_corner_factor
        
        def corners_probability(threshold, expected):
            # Probability calculation for corners
            if expected <= 0:
                return 0.1
            over_prob = 0.5 + (expected - threshold) / (expected * 2)
            return max(0.05, min(0.95, over_prob))
        
        return {
            'expected_corners': expected_corners,
            'corners_over_8_5_prob': corners_probability(8.5, expected_corners),
            'corners_over_9_5_prob': corners_probability(9.5, expected_corners),
            'corners_over_10_5_prob': corners_probability(10.5, expected_corners),
            'corners_over_11_5_prob': corners_probability(11.5, expected_corners),
            'corners_over_12_5_prob': corners_probability(12.5, expected_corners),
            'corners_under_8_5_prob': 1 - corners_probability(8.5, expected_corners),
            'corners_under_9_5_prob': 1 - corners_probability(9.5, expected_corners),
            'corners_under_10_5_prob': 1 - corners_probability(10.5, expected_corners),
            'corners_under_11_5_prob': 1 - corners_probability(11.5, expected_corners),
            'corners_under_12_5_prob': 1 - corners_probability(12.5, expected_corners),
            'corners_prediction_10_5': 'OVER' if corners_probability(10.5, expected_corners) > 0.5 else 'UNDER',
            'corners_prediction_9_5': 'OVER' if corners_probability(9.5, expected_corners) > 0.5 else 'UNDER',
        }
    
    def get_league_corners_factor(self, league):
        """Get league-specific corners adjustment factor"""
        league_factors = {
            'Premier League': 1.08,
            'La Liga': 0.95,
            'Bundesliga': 1.02,
            'Serie A': 0.88,
            'Ligue 1': 0.98,
            'MLS': 1.05,
            'Liga MX': 1.12,
            'FIFA Club World Cup': 1.05,
            'FIFA Club World Cup Playin': 1.08,
            # World Cup Qualifications
            'WC Qualification Europe': 0.98,
            'WC Qualification Africa': 1.02,
            'WC Qualification Asia': 0.95,
            'WC Qualification South America': 1.08,
            'WC Qualification CONCACAF': 1.05,
            'WC Qualification Oceania': 1.10,
            # English Lower Tier
            'FA Trophy': 1.08,
        }
        return league_factors.get(league, 1.0)
    
    def calculate_cards_predictions(self, match_data, win_probs):
        """Calculate cards over/under predictions"""
        
        # Base cards expectation
        base_cards = 4.2
        
        # More cards in competitive matches
        competitiveness = 1 - abs(win_probs['home_win'] - win_probs['away_win'])
        expected_cards = base_cards + (competitiveness * 1.5)
        
        # League adjustment
        league_cards_factor = self.get_league_cards_factor(match_data.get('league'))
        expected_cards *= league_cards_factor
        
        def cards_probability(threshold, expected):
            if expected <= 0:
                return 0.1
            over_prob = 0.5 + (expected - threshold) / (expected * 2.5)
            return max(0.05, min(0.95, over_prob))
        
        return {
            'expected_cards': expected_cards,
            'cards_over_3_5_prob': cards_probability(3.5, expected_cards),
            'cards_over_4_5_prob': cards_probability(4.5, expected_cards),
            'cards_over_5_5_prob': cards_probability(5.5, expected_cards),
            'cards_under_3_5_prob': 1 - cards_probability(3.5, expected_cards),
            'cards_under_4_5_prob': 1 - cards_probability(4.5, expected_cards),
            'cards_under_5_5_prob': 1 - cards_probability(5.5, expected_cards),
            'cards_prediction_4_5': 'OVER' if cards_probability(4.5, expected_cards) > 0.5 else 'UNDER',
        }
    
    def get_league_cards_factor(self, league):
        """Get league-specific cards adjustment factor"""
        league_factors = {
            'Premier League': 1.15,
            'La Liga': 1.25,
            'Bundesliga': 0.95,
            'Serie A': 1.35,
            'Ligue 1': 1.10,
            'Liga MX': 1.20,
            'FIFA Club World Cup': 1.08,
            'FIFA Club World Cup Playin': 1.12,
            # World Cup Qualifications
            'WC Qualification Europe': 1.05,
            'WC Qualification Africa': 1.15,
            'WC Qualification Asia': 1.10,
            'WC Qualification South America': 1.25,
            'WC Qualification CONCACAF': 1.18,
            'WC Qualification Oceania': 1.12,
            # English Lower Tier
            'FA Trophy': 1.08,
        }
        return league_factors.get(league, 1.0)
    
    def calculate_additional_markets(self, match_data, win_probs):
        """Calculate additional betting markets"""
        
        home_win_prob = win_probs['home_win']
        away_win_prob = win_probs['away_win']
        draw_prob = win_probs['draw']
        
        return {
            # Double Chance
            'double_chance_1X_prob': home_win_prob + draw_prob,
            'double_chance_12_prob': home_win_prob + away_win_prob,
            'double_chance_X2_prob': draw_prob + away_win_prob,
            'double_chance_1X_pred': 'YES' if (home_win_prob + draw_prob) > 0.5 else 'NO',
            'double_chance_12_pred': 'YES' if (home_win_prob + away_win_prob) > 0.5 else 'NO',
            'double_chance_X2_pred': 'YES' if (draw_prob + away_win_prob) > 0.5 else 'NO',
            
            # Half Time Result (simplified)
            'ht_home_prob': home_win_prob * 0.7,  # Less decisive at half time
            'ht_draw_prob': 0.4 + (draw_prob * 0.3),  # More draws at half time
            'ht_away_prob': away_win_prob * 0.7,
            'ht_prediction': 'X',  # Default to draw as most common HT result
            
            # Clean Sheet
            'home_clean_sheet_prob': 0.3 + (home_win_prob * 0.4),
            'away_clean_sheet_prob': 0.3 + (away_win_prob * 0.4),
            'home_clean_sheet_pred': 'YES' if (0.3 + home_win_prob * 0.4) > 0.5 else 'NO',
            'away_clean_sheet_pred': 'YES' if (0.3 + away_win_prob * 0.4) > 0.5 else 'NO',
        }
    
    def analyze_market_values(self, match_data, predictions):
        """Analyze value opportunities across markets"""
        
        value_bets = []
        
        # Check 1X2 value
        home_odds = match_data.get('home_odds', 2.0)
        draw_odds = match_data.get('draw_odds', 3.0)
        away_odds = match_data.get('away_odds', 2.0)
        
        home_implied = 1 / home_odds
        draw_implied = 1 / draw_odds
        away_implied = 1 / away_odds
        
        home_value = predictions['home_win_prob'] - home_implied
        draw_value = predictions['draw_prob'] - draw_implied
        away_value = predictions['away_win_prob'] - away_implied
        
        # Check BTTS value
        btts_yes_odds = match_data.get('btts_yes_odds', 2.0)
        btts_no_odds = match_data.get('btts_no_odds', 1.8)
        
        btts_yes_implied = 1 / btts_yes_odds
        btts_no_implied = 1 / btts_no_odds
        
        btts_yes_value = predictions['btts_yes_prob'] - btts_yes_implied
        btts_no_value = predictions['btts_no_prob'] - btts_no_implied
        
        # Check O/U 2.5 goals value
        over_25_odds = match_data.get('over_25_odds', 2.0)
        under_25_odds = match_data.get('under_25_odds', 1.8)
        
        over_25_implied = 1 / over_25_odds
        under_25_implied = 1 / under_25_odds
        
        over_25_value = predictions['over_2_5_prob'] - over_25_implied
        under_25_value = predictions['under_2_5_prob'] - under_25_implied
        
        return {
            'home_value': home_value,
            'draw_value': draw_value,
            'away_value': away_value,
            'btts_yes_value': btts_yes_value,
            'btts_no_value': btts_no_value,
            'over_25_value': over_25_value,
            'under_25_value': under_25_value,
            'best_value_bet': self.get_best_value_bet([
                ('Home Win', home_value),
                ('Draw', draw_value),
                ('Away Win', away_value),
                ('BTTS Yes', btts_yes_value),
                ('BTTS No', btts_no_value),
                ('Over 2.5', over_25_value),
                ('Under 2.5', under_25_value),
            ]),
            'has_value_bet': max(home_value, draw_value, away_value, btts_yes_value, 
                               btts_no_value, over_25_value, under_25_value) > 0.05
        }
    
    def get_best_value_bet(self, value_bets):
        """Get the bet with highest value"""
        best_bet = max(value_bets, key=lambda x: x[1])
        return best_bet[0] if best_bet[1] > 0.05 else 'None'
    
    def generate_sample_matches(self):
        """Generate sample matches for demonstration"""
        sample_matches = [
            {
                'date': '2024-09-05',
                'time': '15:00',
                'league': 'Premier League',
                'home_team': 'Manchester City',
                'away_team': 'Arsenal',
                'home_odds': 1.85,
                'draw_odds': 3.6,
                'away_odds': 4.2,
                'btts_yes_odds': 1.9,
                'btts_no_odds': 1.9,
                'over_25_odds': 1.7,
                'under_25_odds': 2.1,
            },
            {
                'date': '2024-09-05',
                'time': '17:30',
                'league': 'La Liga',
                'home_team': 'Real Madrid',
                'away_team': 'Barcelona',
                'home_odds': 2.1,
                'draw_odds': 3.3,
                'away_odds': 3.4,
                'btts_yes_odds': 1.8,
                'btts_no_odds': 2.0,
                'over_25_odds': 1.6,
                'under_25_odds': 2.3,
            },
            {
                'date': '2024-09-05',
                'time': '20:00',
                'league': 'Bundesliga',
                'home_team': 'Bayern Munich',
                'away_team': 'Borussia Dortmund',
                'home_odds': 1.9,
                'draw_odds': 3.5,
                'away_odds': 4.0,
                'btts_yes_odds': 1.7,
                'btts_no_odds': 2.1,
                'over_25_odds': 1.5,
                'under_25_odds': 2.5,
            },
            {
                'date': '2024-09-06',
                'time': '16:00',
                'league': 'Serie A',
                'home_team': 'Juventus',
                'away_team': 'AC Milan',
                'home_odds': 2.2,
                'draw_odds': 3.2,
                'away_odds': 3.3,
                'btts_yes_odds': 2.0,
                'btts_no_odds': 1.8,
                'over_25_odds': 1.9,
                'under_25_odds': 1.9,
            },
            {
                'date': '2024-09-06',
                'time': '21:00',
                'league': 'MLS',
                'home_team': 'LA Galaxy',
                'away_team': 'LAFC',
                'home_odds': 2.4,
                'draw_odds': 3.1,
                'away_odds': 2.9,
                'btts_yes_odds': 1.6,
                'btts_no_odds': 2.3,
                'over_25_odds': 1.4,
                'under_25_odds': 2.8,
            },
        ]
        
        return sample_matches
    
    def generate_csv_predictions(self, matches=None, filename=None):
        """Generate predictions for matches and save to CSV"""
        
        if matches is None:
            matches = self.generate_sample_matches()
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"output reports/soccer_predictions_{timestamp}.csv"
        
        print(f"🎯 Generating predictions for {len(matches)} matches...")
        print("=" * 50)
        
        # Load models
        if not self.load_models():
            print("⚠️  No models loaded - using basic calculations")
        
        # Generate predictions for all matches
        for i, match in enumerate(matches, 1):
            print(f"📊 Processing match {i}/{len(matches)}: {match['home_team']} vs {match['away_team']}")
            prediction = self.predict_betting_markets(match)
            self.predictions.append(prediction)
        
        # Create DataFrame
        df = pd.DataFrame(self.predictions)
        
        # Save to CSV
        output_path = f"./{filename}"
        df.to_csv(output_path, index=False, float_format='%.4f')
        
        print(f"\n✅ Predictions saved to: {filename}")
        print(f"📊 Total predictions: {len(self.predictions)}")
        print(f"📋 Markets covered: Winner, BTTS, O/U Goals, Corners, Cards, Value Bets")
        
        # Show summary
        self.show_predictions_summary(df)
        
        return output_path, df
    
    def show_predictions_summary(self, df):
        """Show summary of predictions"""
        print(f"\n📈 Predictions Summary:")
        print("=" * 25)
        
        # Winner predictions
        winner_counts = df['winner_prediction'].value_counts()
        print(f"\n🏆 Winner Predictions:")
        for outcome, count in winner_counts.items():
            print(f"   {outcome}: {count} matches ({count/len(df)*100:.1f}%)")
        
        # BTTS predictions
        btts_counts = df['btts_prediction'].value_counts()
        print(f"\n⚽ BTTS Predictions:")
        for outcome, count in btts_counts.items():
            print(f"   {outcome}: {count} matches ({count/len(df)*100:.1f}%)")
        
        # Goals predictions
        goals_25_counts = df['goals_prediction_2_5'].value_counts()
        print(f"\n🥅 Over/Under 2.5 Goals:")
        for outcome, count in goals_25_counts.items():
            print(f"   {outcome}: {count} matches ({count/len(df)*100:.1f}%)")
        
        # Value bets
        value_bets = df[df['has_value_bet'] == True]
        print(f"\n💰 Value Opportunities: {len(value_bets)} matches ({len(value_bets)/len(df)*100:.1f}%)")
        
        if len(value_bets) > 0:
            best_values = value_bets['best_value_bet'].value_counts()
            print("   Top value markets:")
            for market, count in best_values.head(3).items():
                print(f"      {market}: {count} opportunities")
        
        # Average statistics
        print(f"\n📊 Average Statistics:")
        print(f"   Expected Goals: {df['expected_goals'].mean():.2f}")
        print(f"   Expected Corners: {df['expected_corners'].mean():.2f}")
        print(f"   Expected Cards: {df['expected_cards'].mean():.2f}")
        print(f"   Average Confidence: {df['winner_confidence'].mean():.3f}")


def main():
    """Main function to generate CSV predictions"""
    
    API_KEY = "ceb338b9bcb82a452efc114fb2d3cccac67f58be1569e7b5acf1d2195adeae11"
    
    print("📊 CSV Soccer Predictions Generator")
    print("=" * 45)
    print("Generating comprehensive predictions for:")
    print("• Match Winner (1X2)")
    print("• Both Teams to Score (BTTS)")
    print("• Over/Under Goals (0.5, 1.5, 2.5, 3.5, 4.5)")
    print("• Over/Under Corners")
    print("• Over/Under Cards")
    print("• Double Chance markets")
    print("• Value betting opportunities")
    print("=" * 45)
    
    # Initialize generator
    generator = CSVPredictionsGenerator(API_KEY)
    
    # Generate predictions with sample data
    output_file, predictions_df = generator.generate_csv_predictions()
    
    print(f"\n🎉 Complete! Your predictions are ready.")
    print(f"📁 File location: {output_file}")
    print(f"📊 You can now analyze {len(predictions_df)} matches across multiple betting markets")
    
    print(f"\n💡 Next Steps:")
    print("• Open the CSV file in Excel or Google Sheets")
    print("• Filter by league, date, or value opportunities")
    print("• Compare predictions with actual odds from bookmakers")
    print("• Track your betting performance over time")
    
    print(f"\n⚠️  Important:")
    print("• These predictions are for educational purposes")
    print("• Always do your own research before betting")
    print("• Only bet what you can afford to lose")
    print("• Consider team news, injuries, and other factors")


if __name__ == "__main__":
    main()