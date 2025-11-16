#!/usr/bin/env python3
"""
Multi-Market Soccer Betting Predictor

Covers all major betting markets:
- Match Result (ML): Home/Draw/Away
- Totals: Over/Under 2.5, 1.5, 3.5 goals
- Team Totals: Team Over/Under goals
- BTTS: Both Teams to Score Yes/No
- Corners: Over/Under corner kicks
- Asian Handicap: Spread betting
- Double Chance: Multiple outcome coverage
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import random
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC, LinearSVC
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.calibration import CalibratedClassifierCV
import joblib
import logging


class MultiMarketPredictor:
    """Comprehensive multi-market soccer betting predictor"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        
        # Adjusted risk parameters - more realistic for actual betting
        self.max_bet_fraction = 0.08  # Max 8% per bet (increased from 5%)
        self.kelly_fraction = 0.40  # Use 40% Kelly (increased from 25%)
        self.min_edge = 0.05  # Minimum 5% edge (reduced from 8%)
        self.min_confidence = 0.58  # Require 58% confidence (reduced from 65%)
        self.max_odds = 8.0  # Allow higher odds for value (increased from 6.0)
        
        # Market-specific models
        self.market_models = {}
        self.scaler = StandardScaler()
        
        # All betting markets we support
        self.betting_markets = {
            'match_result': ['Home', 'Draw', 'Away'],
            'total_goals': ['Over 1.5', 'Under 1.5', 'Over 2.5', 'Under 2.5', 'Over 3.5', 'Under 3.5'],
            'btts': ['BTTS Yes', 'BTTS No'],
            'double_chance': ['Home/Draw', 'Home/Away', 'Draw/Away'],
            'team_totals': ['Home Over 1.5', 'Home Under 1.5', 'Away Over 1.5', 'Away Under 1.5'],
            'corners': ['Over 9.5 Corners', 'Under 9.5 Corners', 'Over 11.5 Corners', 'Under 11.5 Corners'],
            'asian_handicap': ['Home -1', 'Home +1', 'Away -1', 'Away +1']
        }
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def generate_realistic_odds(self, match_context: dict = None) -> dict:
        """Generate realistic odds for all markets based on match context"""
        
        # Base match strength differential (affects all markets)
        strength_diff = random.uniform(-0.8, 0.8)  # -0.8 = away much stronger, +0.8 = home much stronger
        
        # Match Result odds
        if strength_diff > 0.4:  # Home favored
            home_odds = random.uniform(1.4, 1.9)
            away_odds = random.uniform(3.2, 5.5)
            draw_odds = random.uniform(3.0, 4.2)
        elif strength_diff < -0.4:  # Away favored
            home_odds = random.uniform(3.2, 5.5)
            away_odds = random.uniform(1.4, 1.9)
            draw_odds = random.uniform(3.0, 4.2)
        else:  # Balanced match
            home_odds = random.uniform(2.1, 2.9)
            away_odds = random.uniform(2.1, 2.9)
            draw_odds = random.uniform(2.8, 3.6)
        
        # Expected goals (affects totals markets)
        expected_goals = random.uniform(2.1, 3.2)
        
        # Total Goals odds
        over_15_odds = random.uniform(1.15, 1.35) if expected_goals > 2.5 else random.uniform(1.8, 2.4)
        under_15_odds = random.uniform(2.8, 4.5) if expected_goals > 2.5 else random.uniform(1.4, 1.7)
        
        over_25_odds = random.uniform(1.5, 1.9) if expected_goals > 2.5 else random.uniform(2.1, 2.8)
        under_25_odds = random.uniform(1.8, 2.3) if expected_goals > 2.5 else random.uniform(1.5, 1.8)
        
        over_35_odds = random.uniform(2.2, 3.5) if expected_goals > 3.0 else random.uniform(3.8, 6.2)
        under_35_odds = random.uniform(1.3, 1.6) if expected_goals > 3.0 else random.uniform(1.2, 1.4)
        
        # BTTS odds (affected by both teams' attacking strength)
        btts_probability = random.uniform(0.45, 0.65)
        btts_yes_odds = round(1 / btts_probability, 2)
        btts_no_odds = round(1 / (1 - btts_probability), 2)
        
        # Team totals (affected by individual team strength)
        home_attacking = random.uniform(0.7, 2.1)
        away_attacking = random.uniform(0.7, 2.1)
        
        home_over_15_odds = random.uniform(1.6, 2.4) if home_attacking > 1.3 else random.uniform(2.8, 4.2)
        home_under_15_odds = random.uniform(1.4, 1.8) if home_attacking > 1.3 else random.uniform(1.3, 1.6)
        away_over_15_odds = random.uniform(1.6, 2.4) if away_attacking > 1.3 else random.uniform(2.8, 4.2)
        away_under_15_odds = random.uniform(1.4, 1.8) if away_attacking > 1.3 else random.uniform(1.3, 1.6)
        
        # Double Chance odds
        home_draw_odds = round(1 / ((1/home_odds) + (1/draw_odds)), 2)
        home_away_odds = round(1 / ((1/home_odds) + (1/away_odds)), 2)
        draw_away_odds = round(1 / ((1/draw_odds) + (1/away_odds)), 2)
        
        # Corners (typically 8-14 per match)
        expected_corners = random.uniform(8.5, 13.5)
        over_95_corners_odds = random.uniform(1.7, 2.2) if expected_corners > 10 else random.uniform(2.4, 3.1)
        under_95_corners_odds = random.uniform(1.6, 2.0) if expected_corners > 10 else random.uniform(1.4, 1.7)
        over_115_corners_odds = random.uniform(2.1, 2.8) if expected_corners > 11 else random.uniform(3.2, 4.5)
        under_115_corners_odds = random.uniform(1.4, 1.7) if expected_corners > 11 else random.uniform(1.3, 1.5)
        
        # Asian Handicap
        home_minus1_odds = random.uniform(2.8, 4.2) if strength_diff > 0.3 else random.uniform(4.5, 7.0)
        home_plus1_odds = random.uniform(1.3, 1.6) if strength_diff > 0 else random.uniform(1.1, 1.4)
        away_minus1_odds = random.uniform(2.8, 4.2) if strength_diff < -0.3 else random.uniform(4.5, 7.0)
        away_plus1_odds = random.uniform(1.3, 1.6) if strength_diff < 0 else random.uniform(1.1, 1.4)
        
        return {
            # Match Result
            'home_ml': home_odds,
            'draw_ml': draw_odds,
            'away_ml': away_odds,
            
            # Total Goals
            'over_15': over_15_odds,
            'under_15': under_15_odds,
            'over_25': over_25_odds,
            'under_25': under_25_odds,
            'over_35': over_35_odds,
            'under_35': under_35_odds,
            
            # BTTS
            'btts_yes': btts_yes_odds,
            'btts_no': btts_no_odds,
            
            # Double Chance
            'home_draw': home_draw_odds,
            'home_away': home_away_odds,
            'draw_away': draw_away_odds,
            
            # Team Totals
            'home_over_15': home_over_15_odds,
            'home_under_15': home_under_15_odds,
            'away_over_15': away_over_15_odds,
            'away_under_15': away_under_15_odds,
            
            # Corners
            'over_95_corners': over_95_corners_odds,
            'under_95_corners': under_95_corners_odds,
            'over_115_corners': over_115_corners_odds,
            'under_115_corners': under_115_corners_odds,
            
            # Asian Handicap
            'home_minus1': home_minus1_odds,
            'home_plus1': home_plus1_odds,
            'away_minus1': away_minus1_odds,
            'away_plus1': away_plus1_odds,
            
            # Context for outcome simulation
            'strength_diff': strength_diff,
            'expected_goals': expected_goals,
            'btts_probability': btts_probability,
            'expected_corners': expected_corners
        }
    
    def simulate_match_outcome(self, odds_context: dict) -> dict:
        """Simulate realistic match outcome based on odds context"""
        strength_diff = odds_context['strength_diff']
        expected_goals = odds_context['expected_goals']
        btts_prob = odds_context['btts_probability']
        expected_corners = odds_context['expected_corners']
        
        # Simulate goals based on Poisson distribution around expected goals
        total_goals = max(0, int(np.random.poisson(expected_goals)))
        
        # Distribute goals between teams based on strength difference
        if strength_diff > 0.2:  # Home stronger
            home_goals = max(0, int(np.random.poisson(expected_goals * 0.6)))
            away_goals = max(0, total_goals - home_goals)
        elif strength_diff < -0.2:  # Away stronger
            away_goals = max(0, int(np.random.poisson(expected_goals * 0.6)))
            home_goals = max(0, total_goals - away_goals)
        else:  # Balanced
            home_goals = max(0, int(np.random.poisson(expected_goals * 0.5)))
            away_goals = max(0, total_goals - home_goals)
        
        # Ensure realistic score distribution
        if total_goals == 0:
            home_goals = away_goals = 0
        elif total_goals == 1:
            if random.random() < 0.5 + strength_diff/2:
                home_goals, away_goals = 1, 0
            else:
                home_goals, away_goals = 0, 1
        
        total_goals = home_goals + away_goals
        
        # Match result
        if home_goals > away_goals:
            match_result = 'Home'
        elif away_goals > home_goals:
            match_result = 'Away'
        else:
            match_result = 'Draw'
        
        # BTTS
        btts_result = 'BTTS Yes' if (home_goals > 0 and away_goals > 0) else 'BTTS No'
        
        # Corners
        actual_corners = max(4, int(np.random.poisson(expected_corners)))
        
        return {
            'home_goals': home_goals,
            'away_goals': away_goals,
            'total_goals': total_goals,
            'match_result': match_result,
            'btts_result': btts_result,
            'actual_corners': actual_corners
        }
    
    def create_market_features(self, odds: dict) -> np.ndarray:
        """Create features for market prediction from odds"""
        features = [
            # Match result probabilities
            1/odds['home_ml'], 1/odds['draw_ml'], 1/odds['away_ml'],
            
            # Total goals market analysis
            1/odds['over_25'], 1/odds['under_25'],
            1/odds['over_15'], 1/odds['under_15'],
            1/odds['over_35'], 1/odds['under_35'],
            
            # BTTS probabilities
            1/odds['btts_yes'], 1/odds['btts_no'],
            
            # Team strength indicators
            1/odds['home_over_15'], 1/odds['home_under_15'],
            1/odds['away_over_15'], 1/odds['away_under_15'],
            
            # Market efficiency indicators
            odds['home_ml'] / odds['away_ml'],  # Home/Away odds ratio
            min(odds['home_ml'], odds['away_ml']),  # Favorite odds
            max(odds['home_ml'], odds['away_ml']),  # Underdog odds
            
            # Totals market consistency
            odds['over_25'] * odds['under_25'],  # Should be close to overround
            
            # Corner market
            1/odds['over_95_corners'], 1/odds['under_95_corners'],
            
            # Double chance efficiency
            1/odds['home_draw'], 1/odds['draw_away'],
        ]
        
        return np.array(features)
    
    def train_market_models(self, training_data: list):
        """Train separate models for each betting market"""
        print("🤖 Training multi-market models...")
        
        # Generate training data for all markets
        all_features = []
        market_outcomes = {market: [] for market_list in self.betting_markets.values() for market in market_list}
        
        for match_data in training_data:
            odds = self.generate_realistic_odds()
            outcome = self.simulate_match_outcome(odds)
            
            features = self.create_market_features(odds)
            all_features.append(features)
            
            # Record outcomes for each market
            # Match Result
            market_outcomes['Home'].append(1 if outcome['match_result'] == 'Home' else 0)
            market_outcomes['Draw'].append(1 if outcome['match_result'] == 'Draw' else 0)
            market_outcomes['Away'].append(1 if outcome['match_result'] == 'Away' else 0)
            
            # Total Goals
            market_outcomes['Over 1.5'].append(1 if outcome['total_goals'] > 1.5 else 0)
            market_outcomes['Under 1.5'].append(1 if outcome['total_goals'] <= 1.5 else 0)
            market_outcomes['Over 2.5'].append(1 if outcome['total_goals'] > 2.5 else 0)
            market_outcomes['Under 2.5'].append(1 if outcome['total_goals'] <= 2.5 else 0)
            market_outcomes['Over 3.5'].append(1 if outcome['total_goals'] > 3.5 else 0)
            market_outcomes['Under 3.5'].append(1 if outcome['total_goals'] <= 3.5 else 0)
            
            # BTTS
            market_outcomes['BTTS Yes'].append(1 if outcome['btts_result'] == 'BTTS Yes' else 0)
            market_outcomes['BTTS No'].append(1 if outcome['btts_result'] == 'BTTS No' else 0)
            
            # Team Totals
            market_outcomes['Home Over 1.5'].append(1 if outcome['home_goals'] > 1.5 else 0)
            market_outcomes['Home Under 1.5'].append(1 if outcome['home_goals'] <= 1.5 else 0)
            market_outcomes['Away Over 1.5'].append(1 if outcome['away_goals'] > 1.5 else 0)
            market_outcomes['Away Under 1.5'].append(1 if outcome['away_goals'] <= 1.5 else 0)
            
            # Double Chance
            market_outcomes['Home/Draw'].append(1 if outcome['match_result'] in ['Home', 'Draw'] else 0)
            market_outcomes['Home/Away'].append(1 if outcome['match_result'] in ['Home', 'Away'] else 0)
            market_outcomes['Draw/Away'].append(1 if outcome['match_result'] in ['Draw', 'Away'] else 0)
            
            # Corners
            market_outcomes['Over 9.5 Corners'].append(1 if outcome['actual_corners'] > 9.5 else 0)
            market_outcomes['Under 9.5 Corners'].append(1 if outcome['actual_corners'] <= 9.5 else 0)
            market_outcomes['Over 11.5 Corners'].append(1 if outcome['actual_corners'] > 11.5 else 0)
            market_outcomes['Under 11.5 Corners'].append(1 if outcome['actual_corners'] <= 11.5 else 0)
            
            # Asian Handicap (simplified)
            market_outcomes['Home -1'].append(1 if outcome['home_goals'] - outcome['away_goals'] > 1 else 0)
            market_outcomes['Home +1'].append(1 if outcome['home_goals'] - outcome['away_goals'] > -1 else 0)
            market_outcomes['Away -1'].append(1 if outcome['away_goals'] - outcome['home_goals'] > 1 else 0)
            market_outcomes['Away +1'].append(1 if outcome['away_goals'] - outcome['home_goals'] > -1 else 0)
        
        X = np.array(all_features)
        X_scaled = self.scaler.fit_transform(X)
        
        # Train models for markets with reasonable hit rates
        for market, outcomes in market_outcomes.items():
            hit_rate = np.mean(outcomes)
            if 0.15 < hit_rate < 0.85:  # Only train models for markets with reasonable variability
                y = np.array(outcomes)
                
                # Create SVM-enhanced ensemble for this market
                ensemble = VotingClassifier([
                    ('rf', RandomForestClassifier(n_estimators=100, random_state=42, max_depth=8)),
                    ('gb', GradientBoostingClassifier(n_estimators=80, learning_rate=0.1, max_depth=6, random_state=42)),
                    ('svm_rbf', SVC(C=1.0, kernel='rbf', probability=True, random_state=42)),
                    ('svm_linear', CalibratedClassifierCV(LinearSVC(C=0.1, random_state=42, max_iter=2000), method='sigmoid')),
                    ('lr', LogisticRegression(C=1.0, random_state=42, max_iter=1000))
                ], voting='soft')
                
                # Calibrate the entire ensemble
                calibrated_ensemble = CalibratedClassifierCV(ensemble, method='isotonic', cv=3)
                calibrated_ensemble.fit(X_scaled, y)
                
                self.market_models[market] = calibrated_ensemble
                print(f"   ✅ Trained {market} SVM-enhanced ensemble (hit rate: {hit_rate:.2%})")
        
        print(f"🎯 Trained {len(self.market_models)} market models")
    
    def analyze_all_markets(self, odds: dict) -> list:
        """Analyze all betting markets for value opportunities"""
        if not self.market_models:
            self.train_market_models(range(1000))  # Train with 1000 synthetic matches
        
        features = self.create_market_features(odds)
        X_scaled = self.scaler.transform([features])
        
        opportunities = []
        
        # Market-specific odds mapping
        market_odds_map = {
            'Home': odds['home_ml'],
            'Draw': odds['draw_ml'], 
            'Away': odds['away_ml'],
            'Over 1.5': odds['over_15'],
            'Under 1.5': odds['under_15'],
            'Over 2.5': odds['over_25'],
            'Under 2.5': odds['under_25'],
            'Over 3.5': odds['over_35'],
            'Under 3.5': odds['under_35'],
            'BTTS Yes': odds['btts_yes'],
            'BTTS No': odds['btts_no'],
            'Home/Draw': odds['home_draw'],
            'Home/Away': odds['home_away'],
            'Draw/Away': odds['draw_away'],
            'Home Over 1.5': odds['home_over_15'],
            'Home Under 1.5': odds['home_under_15'],
            'Away Over 1.5': odds['away_over_15'],
            'Away Under 1.5': odds['away_under_15'],
            'Over 9.5 Corners': odds['over_95_corners'],
            'Under 9.5 Corners': odds['under_95_corners'],
            'Over 11.5 Corners': odds['over_115_corners'],
            'Under 11.5 Corners': odds['under_115_corners'],
            'Home -1': odds['home_minus1'],
            'Home +1': odds['home_plus1'],
            'Away -1': odds['away_minus1'],
            'Away +1': odds['away_plus1']
        }
        
        for market, model in self.market_models.items():
            if market in market_odds_map:
                # Get model prediction
                prob = model.predict_proba(X_scaled)[0][1]  # Probability of market hitting
                market_odds = market_odds_map[market]
                implied_prob = 1 / market_odds
                
                # Calculate edge
                edge = (prob - implied_prob) / implied_prob
                
                # Check if this meets our criteria
                if (edge > self.min_edge and 
                    prob > self.min_confidence and 
                    market_odds <= self.max_odds):
                    
                    # Calculate Kelly fraction
                    kelly_full = (prob * market_odds - 1) / (market_odds - 1)
                    kelly_adjusted = max(0, min(kelly_full * self.kelly_fraction, self.max_bet_fraction))
                    
                    if kelly_adjusted > 0.01:  # Minimum 1% bet
                        opportunities.append({
                            'market': market,
                            'odds': market_odds,
                            'model_probability': prob,
                            'implied_probability': implied_prob,
                            'edge': edge,
                            'kelly_fraction': kelly_adjusted,
                            'confidence': prob,
                            'expected_value': prob * (market_odds - 1) - (1 - prob)
                        })
        
        # Sort by expected value and return top opportunities
        opportunities.sort(key=lambda x: x['expected_value'], reverse=True)
        return opportunities[:5]  # Max 5 bets per match
    
    def save_models(self, filepath: str):
        """Save all market models"""
        model_data = {
            'market_models': self.market_models,
            'scaler': self.scaler,
            'risk_params': {
                'max_bet_fraction': self.max_bet_fraction,
                'kelly_fraction': self.kelly_fraction,
                'min_edge': self.min_edge,
                'min_confidence': self.min_confidence,
                'max_odds': self.max_odds
            }
        }
        joblib.dump(model_data, filepath)
        print(f"💾 Multi-market models saved to {filepath}")


def main():
    """Test the multi-market predictor"""
    
    predictor = MultiMarketPredictor("test_api_key")
    
    print("🎯 Multi-Market Soccer Betting Predictor")
    print("=" * 50)
    
    # Test with sample matches
    for i in range(5):
        print(f"\n🏆 Match {i+1}:")
        
        # Generate realistic odds for this match
        odds = predictor.generate_realistic_odds()
        
        print(f"   ML: {odds['home_ml']:.2f} / {odds['draw_ml']:.2f} / {odds['away_ml']:.2f}")
        print(f"   O/U 2.5: {odds['over_25']:.2f} / {odds['under_25']:.2f}")
        print(f"   BTTS: {odds['btts_yes']:.2f} / {odds['btts_no']:.2f}")
        
        # Analyze for opportunities
        opportunities = predictor.analyze_all_markets(odds)
        
        if opportunities:
            print(f"   💰 Value opportunities found:")
            for opp in opportunities:
                print(f"      {opp['market']}: {opp['edge']*100:.1f}% edge @ {opp['odds']:.2f} "
                      f"({opp['kelly_fraction']*100:.1f}% Kelly)")
        else:
            print("   ❌ No value opportunities")
    
    # Save models
    predictor.save_models("./multi_market_models.pkl")
    
    print(f"\n✅ Multi-market system ready!")
    print(f"📊 Covers {len(predictor.market_models)} different betting markets")


if __name__ == "__main__":
    main()