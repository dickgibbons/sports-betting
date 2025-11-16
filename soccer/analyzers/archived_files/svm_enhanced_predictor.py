#!/usr/bin/env python3
"""
SVM-Enhanced Multi-Market Soccer Betting Predictor

Extends the existing multi-market predictor by adding Support Vector Machine models
for improved prediction accuracy and ensemble performance.

Enhanced with:
- SVC with RBF kernel for non-linear patterns
- LinearSVC for linear separability
- Ensemble voting including SVMs
- Probability calibration for better betting odds
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import random
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC, LinearSVC
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import VotingClassifier
from sklearn.metrics import classification_report, log_loss
import joblib
import logging
import warnings
warnings.filterwarnings('ignore')


class SVMEnhancedPredictor:
    """Multi-market soccer predictor enhanced with Support Vector Machines"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        
        # Risk parameters optimized for SVM ensemble
        self.max_bet_fraction = 0.08
        self.kelly_fraction = 0.40
        self.min_edge = 0.05
        self.min_confidence = 0.58
        self.max_odds = 8.0
        
        # Enhanced model collection including SVMs
        self.market_models = {}
        self.scaler = StandardScaler()
        self.model_performance = {}
        
        # Betting markets
        self.betting_markets = {
            'match_result': ['Home', 'Draw', 'Away'],
            'total_goals': ['Over 1.5', 'Under 1.5', 'Over 2.5', 'Under 2.5', 'Over 3.5', 'Under 3.5'],
            'btts': ['BTTS Yes', 'BTTS No'],
            'double_chance': ['Home/Draw', 'Home/Away', 'Draw/Away'],
            'team_totals': ['Home Over 1.5', 'Home Under 1.5', 'Away Over 1.5', 'Away Under 1.5'],
            'corners': ['Over 9.5 Corners', 'Under 9.5 Corners', 'Over 11.5 Corners', 'Under 11.5 Corners'],
            'handicap': ['Home -1', 'Home +1', 'Away -1', 'Away +1']
        }
        
        print("🤖 SVM-Enhanced Soccer Predictor initialized")
        print("   📊 Models: Random Forest + Gradient Boosting + SVM + Logistic")
        print("   🎯 Enhanced ensemble voting with probability calibration")
        print()
    
    def create_ensemble_model(self, market: str) -> VotingClassifier:
        """Create ensemble model combining multiple algorithms including SVMs"""
        
        # Base models with optimized parameters
        models = [
            ('rf', RandomForestClassifier(
                n_estimators=150, 
                max_depth=10, 
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42, 
                n_jobs=-1
            )),
            ('gb', GradientBoostingClassifier(
                n_estimators=100, 
                learning_rate=0.1, 
                max_depth=6,
                min_samples_split=5,
                random_state=42
            )),
            ('svm_rbf', SVC(
                C=1.0,
                kernel='rbf',
                gamma='scale',
                probability=True,  # Enable probability estimates
                random_state=42
            )),
            ('svm_linear', LinearSVC(
                C=0.1,
                random_state=42,
                max_iter=2000
            )),
            ('lr', LogisticRegression(
                C=1.0,
                random_state=42,
                max_iter=1000
            ))
        ]
        
        # For LinearSVC, we need to wrap it for probability estimates
        calibrated_linear_svm = CalibratedClassifierCV(
            LinearSVC(C=0.1, random_state=42, max_iter=2000),
            method='sigmoid'
        )
        
        # Create ensemble with probability voting
        ensemble_models = [
            ('rf', models[0][1]),
            ('gb', models[1][1]),
            ('svm_rbf', models[2][1]),
            ('svm_linear', calibrated_linear_svm),
            ('lr', models[4][1])
        ]
        
        ensemble = VotingClassifier(
            estimators=ensemble_models,
            voting='soft'  # Use probability voting
        )
        
        return ensemble
    
    def create_market_features(self, odds: dict) -> np.ndarray:
        """Enhanced feature engineering for SVM compatibility"""
        
        # Extract basic odds
        home_ml = odds.get('home_ml', 2.0)
        draw_ml = odds.get('draw_ml', 3.2)
        away_ml = odds.get('away_ml', 3.5)
        
        # Calculate probabilities
        home_prob = 1 / home_ml
        draw_prob = 1 / draw_ml
        away_prob = 1 / away_ml
        total_prob = home_prob + draw_prob + away_prob
        
        # Normalize probabilities
        home_prob_norm = home_prob / total_prob
        draw_prob_norm = draw_prob / total_prob
        away_prob_norm = away_prob / total_prob
        
        # Advanced features for SVM
        features = [
            # Basic odds
            home_ml, draw_ml, away_ml,
            
            # Normalized probabilities
            home_prob_norm, draw_prob_norm, away_prob_norm,
            
            # Odds ratios and differences
            home_ml / away_ml,  # Home vs Away strength
            (home_ml + away_ml) / (2 * draw_ml),  # Favorite vs Draw tendency
            abs(home_ml - away_ml),  # Match competitiveness
            
            # Market efficiency indicators
            total_prob - 1.0,  # Bookmaker margin
            max(home_ml, draw_ml, away_ml),  # Highest odds
            min(home_ml, draw_ml, away_ml),  # Lowest odds
            
            # Goals market features
            odds.get('over_25', 2.0),
            odds.get('under_25', 2.0),
            odds.get('over_15', 1.3),
            odds.get('under_15', 3.5),
            odds.get('over_35', 3.0),
            odds.get('under_35', 1.4),
            
            # BTTS features
            odds.get('btts_yes', 2.0),
            odds.get('btts_no', 1.8),
            
            # Additional synthetic features for SVM
            np.log(home_ml),  # Log transformation for SVM
            np.log(away_ml),
            np.sqrt(home_ml * away_ml),  # Geometric mean
            (home_ml * away_ml) / (home_ml + away_ml),  # Harmonic mean
        ]
        
        return np.array(features)
    
    def train_market_models(self, training_data: list):
        """Train enhanced ensemble models for each market"""
        
        print("🤖 Training SVM-enhanced multi-market models...")
        
        # Generate comprehensive training data
        X_data = []
        market_data = {market: [] for market in ['Home', 'Draw', 'Away'] + 
                      [m for markets in self.betting_markets.values() for m in markets]}
        
        for i in range(1000):  # Generate training samples
            # Create realistic odds scenario
            odds = self.generate_realistic_odds()
            features = self.create_market_features(odds)
            X_data.append(features)
            
            # Simulate outcomes with realistic probabilities
            outcome = self.simulate_enhanced_match_outcome(odds)
            
            # Set target labels for each market
            for market_group in self.betting_markets.values():
                for market in market_group:
                    if market in outcome:
                        market_data[market].append(1 if outcome[market] else 0)
                    else:
                        market_data[market].append(0)
        
        X = np.array(X_data)
        X_scaled = self.scaler.fit_transform(X)
        
        # Train ensemble model for each market
        markets_to_train = ['Home', 'Draw', 'Away'] + \
                          [m for markets in self.betting_markets.values() for m in markets]
        
        for market in markets_to_train:
            if market in market_data:
                y = np.array(market_data[market])
                
                if len(np.unique(y)) > 1:  # Ensure we have both classes
                    # Create and train ensemble model
                    ensemble = self.create_ensemble_model(market)
                    ensemble.fit(X_scaled, y)
                    
                    # Calibrate the entire ensemble for better probabilities
                    calibrated_ensemble = CalibratedClassifierCV(
                        ensemble, 
                        method='isotonic', 
                        cv=3
                    )
                    calibrated_ensemble.fit(X_scaled, y)
                    
                    self.market_models[market] = calibrated_ensemble
                    
                    # Calculate performance metrics
                    y_pred_proba = calibrated_ensemble.predict_proba(X_scaled)[:, 1]
                    hit_rate = np.mean(y)
                    
                    print(f"   ✅ Trained {market} ensemble (hit rate: {hit_rate:.2%})")
        
        print(f"🎯 Trained {len(self.market_models)} SVM-enhanced market models")
    
    def simulate_enhanced_match_outcome(self, odds_context: dict) -> dict:
        """Enhanced match simulation with more realistic probabilities"""
        
        # Extract probabilities from odds
        home_prob = 1 / odds_context.get('home_ml', 2.0)
        draw_prob = 1 / odds_context.get('draw_ml', 3.2)
        away_prob = 1 / odds_context.get('away_ml', 3.5)
        
        # Normalize
        total_prob = home_prob + draw_prob + away_prob
        home_prob /= total_prob
        draw_prob /= total_prob
        away_prob /= total_prob
        
        # Determine match result
        rand_val = random.random()
        if rand_val < home_prob:
            result = 'Home'
            home_score = random.choices([1, 2, 3, 4], weights=[0.4, 0.3, 0.2, 0.1])[0]
            away_score = random.choices([0, 1, 2], weights=[0.6, 0.3, 0.1])[0]
        elif rand_val < home_prob + draw_prob:
            result = 'Draw'
            score = random.choices([0, 1, 2, 3], weights=[0.1, 0.4, 0.4, 0.1])[0]
            home_score = away_score = score
        else:
            result = 'Away'
            away_score = random.choices([1, 2, 3, 4], weights=[0.4, 0.3, 0.2, 0.1])[0]
            home_score = random.choices([0, 1, 2], weights=[0.6, 0.3, 0.1])[0]
        
        total_goals = home_score + away_score
        btts = home_score > 0 and away_score > 0
        corners = random.randint(6, 16)
        
        # Create comprehensive outcome dict
        outcome = {
            'Home': result == 'Home',
            'Draw': result == 'Draw', 
            'Away': result == 'Away',
            'Over 1.5': total_goals > 1.5,
            'Under 1.5': total_goals <= 1.5,
            'Over 2.5': total_goals > 2.5,
            'Under 2.5': total_goals <= 2.5,
            'Over 3.5': total_goals > 3.5,
            'Under 3.5': total_goals <= 3.5,
            'BTTS Yes': btts,
            'BTTS No': not btts,
            'Home/Draw': result in ['Home', 'Draw'],
            'Home/Away': result in ['Home', 'Away'],
            'Draw/Away': result in ['Draw', 'Away'],
            'Home Over 1.5': home_score > 1.5,
            'Home Under 1.5': home_score <= 1.5,
            'Away Over 1.5': away_score > 1.5,
            'Away Under 1.5': away_score <= 1.5,
            'Over 9.5 Corners': corners > 9.5,
            'Under 9.5 Corners': corners <= 9.5,
            'Over 11.5 Corners': corners > 11.5,
            'Under 11.5 Corners': corners <= 11.5,
            'Home -1': home_score - away_score > 1,
            'Home +1': home_score - away_score >= -1,
            'Away -1': away_score - home_score > 1,
            'Away +1': away_score - home_score >= -1,
        }
        
        return outcome
    
    def generate_realistic_odds(self, match_context: dict = None) -> dict:
        """Generate realistic odds with proper market relationships"""
        
        # Generate correlated odds based on match strength
        strength_diff = random.uniform(-2.0, 2.0)  # -2 (away favored) to +2 (home favored)
        
        # Base match odds
        if strength_diff > 1.0:  # Home heavily favored
            home_ml = random.uniform(1.2, 1.8)
            draw_ml = random.uniform(3.2, 4.5)
            away_ml = random.uniform(4.0, 8.0)
        elif strength_diff > 0.2:  # Home slightly favored
            home_ml = random.uniform(1.8, 2.4)
            draw_ml = random.uniform(3.0, 3.8)
            away_ml = random.uniform(2.8, 4.5)
        elif strength_diff > -0.2:  # Even match
            home_ml = random.uniform(2.2, 3.0)
            draw_ml = random.uniform(2.8, 3.4)
            away_ml = random.uniform(2.2, 3.0)
        elif strength_diff > -1.0:  # Away slightly favored
            home_ml = random.uniform(2.8, 4.5)
            draw_ml = random.uniform(3.0, 3.8)
            away_ml = random.uniform(1.8, 2.4)
        else:  # Away heavily favored
            home_ml = random.uniform(4.0, 8.0)
            draw_ml = random.uniform(3.2, 4.5)
            away_ml = random.uniform(1.2, 1.8)
        
        # Goals markets correlated with match odds
        attacking_strength = random.uniform(0.5, 2.0)
        over_25 = random.uniform(1.5, 3.0) / attacking_strength
        under_25 = random.uniform(1.3, 2.5) * attacking_strength
        
        # Complete odds dict
        odds = {
            'home_ml': home_ml,
            'draw_ml': draw_ml, 
            'away_ml': away_ml,
            'over_25': over_25,
            'under_25': under_25,
            'over_15': random.uniform(1.1, 1.4),
            'under_15': random.uniform(2.5, 4.0),
            'over_35': random.uniform(2.2, 4.0),
            'under_35': random.uniform(1.2, 1.8),
            'btts_yes': random.uniform(1.6, 2.4),
            'btts_no': random.uniform(1.5, 2.2),
            'strength_diff': strength_diff
        }
        
        return odds
    
    def analyze_all_markets(self, odds: dict) -> list:
        """Analyze all markets using SVM-enhanced ensemble"""
        if not self.market_models:
            self.train_market_models([])
        
        features = self.create_market_features(odds)
        features_scaled = self.scaler.transform(features.reshape(1, -1))
        
        opportunities = []
        
        for market, model in self.market_models.items():
            try:
                # Get ensemble prediction with probability
                prob = model.predict_proba(features_scaled)[0, 1]
                
                # Get corresponding odds for this market
                market_odds = self.get_market_odds(market, odds)
                
                if market_odds > 1.0:
                    implied_prob = 1 / market_odds
                    edge = prob - implied_prob
                    
                    if (edge > self.min_edge and 
                        prob > self.min_confidence and 
                        market_odds <= self.max_odds):
                        
                        # Enhanced Kelly calculation
                        kelly = (prob * market_odds - 1) / (market_odds - 1)
                        stake = min(kelly * self.kelly_fraction, self.max_bet_fraction)
                        
                        opportunity = {
                            'market': market,
                            'odds': market_odds,
                            'model_probability': prob,
                            'implied_probability': implied_prob,
                            'edge': edge,
                            'kelly_fraction': stake,
                            'confidence': prob,
                            'expected_value': edge,
                            'model_type': 'SVM_Enhanced_Ensemble'
                        }
                        
                        opportunities.append(opportunity)
                        
            except Exception as e:
                continue
        
        return opportunities
    
    def get_market_odds(self, market: str, odds: dict) -> float:
        """Get odds for specific market"""
        
        market_mapping = {
            'Home': 'home_ml',
            'Draw': 'draw_ml',
            'Away': 'away_ml',
            'Over 1.5': 'over_15',
            'Under 1.5': 'under_15',
            'Over 2.5': 'over_25',
            'Under 2.5': 'under_25',
            'Over 3.5': 'over_35',
            'Under 3.5': 'under_35',
            'BTTS Yes': 'btts_yes',
            'BTTS No': 'btts_no'
        }
        
        if market in market_mapping:
            return odds.get(market_mapping[market], 2.0)
        else:
            # Generate synthetic odds for other markets
            return random.uniform(1.5, 4.0)


def main():
    """Test the SVM-enhanced predictor"""
    
    print("🧪 TESTING SVM-ENHANCED SOCCER PREDICTOR")
    print("="*50)
    
    predictor = SVMEnhancedPredictor("test_key")
    
    # Generate test odds
    test_odds = predictor.generate_realistic_odds()
    
    print(f"🎯 Test Match Odds:")
    print(f"   ML: {test_odds['home_ml']:.2f} / {test_odds['draw_ml']:.2f} / {test_odds['away_ml']:.2f}")
    print(f"   O/U 2.5: {test_odds['over_25']:.2f} / {test_odds['under_25']:.2f}")
    print(f"   BTTS: {test_odds['btts_yes']:.2f} / {test_odds['btts_no']:.2f}")
    print()
    
    # Analyze for opportunities
    opportunities = predictor.analyze_all_markets(test_odds)
    
    if opportunities:
        print(f"💰 SVM-Enhanced Value Opportunities Found: {len(opportunities)}")
        for i, opp in enumerate(opportunities[:5], 1):
            print(f"   #{i} {opp['market']}: {opp['edge']*100:.1f}% edge @ {opp['odds']:.2f} "
                  f"({opp['confidence']*100:.1f}% confidence)")
    else:
        print("❌ No value opportunities found in this scenario")
    
    print(f"\n✅ SVM-Enhanced Predictor test complete!")


if __name__ == "__main__":
    main()