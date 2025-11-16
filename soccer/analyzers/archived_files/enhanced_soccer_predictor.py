#!/usr/bin/env python3
"""
Enhanced Soccer Betting Predictor using FootyStats API

This script uses real match data from FootyStats API to build predictive models
for soccer betting outcomes. Includes proper feature engineering and betting analysis.
"""

import requests
import json
import numpy as np
import time
import logging
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score
import joblib

class FootyStatsAPI:
    """Enhanced client for FootyStats API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.football-data-api.com"
        self.session = requests.Session()
        self.rate_limit_delay = 1
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def make_request(self, endpoint: str, params: dict = None) -> dict:
        """Make API request with error handling"""
        url = f"{self.base_url}/{endpoint}"
        
        if params is None:
            params = {}
        params['key'] = self.api_key
        
        try:
            time.sleep(self.rate_limit_delay)
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"API Error {response.status_code}: {response.text}")
                return {'error': f"HTTP {response.status_code}"}
                
        except Exception as e:
            self.logger.error(f"Request exception: {e}")
            return {'error': str(e)}
    
    def get_league_matches(self, league_id: int, season: str = None, page: int = 1) -> list:
        """Fetch matches for a specific league"""
        params = {'league_id': league_id, 'page': page}
        if season:
            params['season'] = season
            
        data = self.make_request('league-matches', params)
        return data.get('data', [])

class SoccerDataProcessor:
    """Process and engineer features from soccer match data"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.logger = logging.getLogger(__name__)
        
    def extract_features(self, matches: list) -> tuple:
        """Extract features and labels from match data"""
        features = []
        labels = []
        match_info = []
        
        for match in matches:
            if not self.is_valid_match(match):
                continue
                
            feature_vector = self.create_feature_vector(match)
            if feature_vector is None:
                continue
                
            features.append(feature_vector)
            labels.append(self.get_match_outcome(match))
            match_info.append({
                'id': match.get('id'),
                'home_name': match.get('home_name', 'Unknown'),
                'away_name': match.get('away_name', 'Unknown'),
                'date_unix': match.get('date_unix', 0)
            })
        
        return np.array(features), np.array(labels), match_info
    
    def is_valid_match(self, match: dict) -> bool:
        """Check if match has minimum required data"""
        # Check if we have the basic match result and odds data
        return (
            match.get('homeGoalCount') is not None and
            match.get('awayGoalCount') is not None and
            match.get('odds_ft_1') is not None and
            match.get('odds_ft_x') is not None and
            match.get('odds_ft_2') is not None and
            float(match.get('odds_ft_1', 0)) > 0 and
            float(match.get('odds_ft_x', 0)) > 0 and
            float(match.get('odds_ft_2', 0)) > 0
        )
    
    def create_feature_vector(self, match: dict) -> list:
        """Create feature vector from match data"""
        try:
            features = [
                # Basic odds
                float(match.get('odds_ft_1', 2.0)),      # Home win odds
                float(match.get('odds_ft_x', 3.0)),      # Draw odds  
                float(match.get('odds_ft_2', 2.0)),      # Away win odds
                
                # Implied probabilities from odds
                1 / float(match.get('odds_ft_1', 2.0)),  # Home win probability
                1 / float(match.get('odds_ft_x', 3.0)),  # Draw probability
                1 / float(match.get('odds_ft_2', 2.0)),  # Away win probability
                
                # Over/Under odds (handle both int and float types)
                float(match.get('odds_ft_over25', 2.0) if match.get('odds_ft_over25') else 2.0),
                float(match.get('odds_ft_under25', 2.0) if match.get('odds_ft_under25') else 2.0),
                float(match.get('odds_ft_over15', 1.5) if match.get('odds_ft_over15') else 1.5),
                float(match.get('odds_ft_under15', 2.5) if match.get('odds_ft_under15') else 2.5),
                
                # Both Teams to Score
                float(match.get('odds_btts_yes', 2.0) if match.get('odds_btts_yes') else 2.0),
                float(match.get('odds_btts_no', 2.0) if match.get('odds_btts_no') else 2.0),
                
                # Corner odds (many are 0, so use defaults)
                float(match.get('odds_corners_over_105', 2.0) if match.get('odds_corners_over_105') else 2.0),
                float(match.get('odds_corners_under_105', 2.0) if match.get('odds_corners_under_105') else 2.0),
                
                # Team performance indicators
                float(match.get('home_ppg', 1.0) if match.get('home_ppg') else 1.0),
                float(match.get('away_ppg', 1.0) if match.get('away_ppg') else 1.0),
                float(match.get('pre_match_home_ppg', 0.0)),
                float(match.get('pre_match_away_ppg', 0.0)),
                
                # xG data - actual vs predicted
                float(match.get('team_a_xg', 1.0) if match.get('team_a_xg') else 1.0),
                float(match.get('team_b_xg', 1.0) if match.get('team_b_xg') else 1.0),
                float(match.get('team_a_xg_prematch', 0.0)),
                float(match.get('team_b_xg_prematch', 0.0)),
                
                # Match stats
                float(match.get('totalGoalCount', 0.0)),
                float(match.get('totalCornerCount', 0.0)),
                float(match.get('team_a_possession', 50.0)),
                float(match.get('team_b_possession', 50.0)),
                
                # Shots data
                float(match.get('team_a_shots', 0.0)),
                float(match.get('team_b_shots', 0.0)),
                float(match.get('team_a_shotsOnTarget', 0.0)),
                float(match.get('team_b_shotsOnTarget', 0.0)),
            ]
            
            # Calculate derived features
            home_odds = float(match.get('odds_ft_1', 2.0))
            away_odds = float(match.get('odds_ft_2', 2.0))
            draw_odds = float(match.get('odds_ft_x', 3.0))
            
            # Odds ratios and differences
            features.extend([
                home_odds / away_odds,           # Home vs Away odds ratio
                (home_odds + away_odds) / 2,     # Average outcome odds
                abs(home_odds - away_odds),      # Odds difference
                min(home_odds, away_odds, draw_odds),  # Favorite odds
                max(home_odds, away_odds, draw_odds),  # Underdog odds
            ])
            
            # PPG differences
            home_ppg = float(match.get('home_ppg', 1.0))
            away_ppg = float(match.get('away_ppg', 1.0))
            features.append(home_ppg - away_ppg)     # PPG difference
            
            return features
            
        except (ValueError, TypeError, ZeroDivisionError) as e:
            self.logger.error(f"Error creating feature vector: {e}")
            return None
    
    def get_match_outcome(self, match: dict) -> int:
        """Get match outcome: 0=Away, 1=Draw, 2=Home"""
        home_goals = int(match.get('homeGoalCount', 0))
        away_goals = int(match.get('awayGoalCount', 0))
        
        if home_goals > away_goals:
            return 2  # Home win
        elif away_goals > home_goals:
            return 0  # Away win
        else:
            return 1  # Draw

class BettingPredictor:
    """Main betting predictor with machine learning models"""
    
    def __init__(self, api_key: str):
        self.api = FootyStatsAPI(api_key)
        self.processor = SoccerDataProcessor()
        self.models = {}
        self.scaler = StandardScaler()
        self.feature_names = []
        self.logger = logging.getLogger(__name__)
        
    def collect_training_data(self, league_id: int = 1625, pages: int = 5) -> tuple:
        """Collect training data from Premier League"""
        all_matches = []
        
        for page in range(1, pages + 1):
            self.logger.info(f"Collecting page {page}/{pages}")
            matches = self.api.get_league_matches(league_id, page=page)
            
            if not matches:
                break
                
            all_matches.extend(matches)
            
        self.logger.info(f"Collected {len(all_matches)} total matches")
        return self.processor.extract_features(all_matches)
    
    def train_models(self, X: np.ndarray, y: np.ndarray):
        """Train multiple prediction models"""
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train Random Forest
        rf_model = RandomForestClassifier(
            n_estimators=100, 
            random_state=42, 
            n_jobs=-1,
            class_weight='balanced'
        )
        rf_model.fit(X_train, y_train)
        
        # Train Gradient Boosting
        gb_model = GradientBoostingClassifier(
            n_estimators=100, 
            random_state=42
        )
        gb_model.fit(X_train, y_train)
        
        self.models = {
            'random_forest': rf_model,
            'gradient_boosting': gb_model
        }
        
        # Evaluate models
        self.logger.info("\nModel Performance:")
        for name, model in self.models.items():
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            cv_scores = cross_val_score(model, X_scaled, y, cv=5)
            
            self.logger.info(f"{name.upper()}:")
            self.logger.info(f"  Test Accuracy: {accuracy:.3f}")
            self.logger.info(f"  CV Score: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
    
    def predict_match_outcome(self, home_odds: float, draw_odds: float, away_odds: float, 
                            additional_features: dict = None) -> dict:
        """Predict outcome for upcoming match based on odds and additional features"""
        
        if not self.models:
            return {'error': 'Models not trained'}
        
        # Create feature vector matching training data structure (36 features)
        features = [
            # Basic odds (3 features)
            home_odds, draw_odds, away_odds,
            
            # Implied probabilities (3 features)  
            1/home_odds, 1/draw_odds, 1/away_odds,
            
            # Over/Under odds (4 features)
            2.0, 2.0, 1.5, 2.5,  # Default over/under 2.5 and 1.5
            
            # BTTS odds (2 features)
            2.0, 2.0,
            
            # Corner odds (2 features) 
            2.0, 2.0,
            
            # PPG data (4 features)
            1.0, 1.0, 0.0, 0.0,   # home_ppg, away_ppg, pre_match values
            
            # xG data (4 features)
            1.0, 1.0, 0.0, 0.0,   # team_a_xg, team_b_xg, prematch values
            
            # Match stats (6 features)
            2.5,      # totalGoalCount (default)
            8.0,      # totalCornerCount (default)  
            50.0,     # team_a_possession
            50.0,     # team_b_possession
            10.0,     # team_a_shots
            10.0,     # team_b_shots
            
            # Shots on target (2 features)
            5.0, 5.0, # team_a_shotsOnTarget, team_b_shotsOnTarget
        ]
        
        # Add derived features (6 features)
        features.extend([
            home_odds / away_odds,                    # Odds ratio
            (home_odds + away_odds) / 2,              # Average odds
            abs(home_odds - away_odds),               # Odds difference
            min(home_odds, away_odds, draw_odds),     # Favorite odds
            max(home_odds, away_odds, draw_odds),     # Underdog odds
            0.0                                       # PPG difference
        ])
        
        # Override with additional features if provided
        if additional_features:
            # This would be expanded based on available additional data
            pass
        
        # Scale features
        feature_array = np.array(features).reshape(1, -1)
        feature_scaled = self.scaler.transform(feature_array)
        
        predictions = {}
        outcome_labels = ['Away Win', 'Draw', 'Home Win']
        
        for name, model in self.models.items():
            pred_proba = model.predict_proba(feature_scaled)[0]
            predicted_class = model.predict(feature_scaled)[0]
            
            predictions[name] = {
                'prediction': outcome_labels[predicted_class],
                'probabilities': {
                    'away_win': pred_proba[0],
                    'draw': pred_proba[1], 
                    'home_win': pred_proba[2]
                },
                'confidence': max(pred_proba)
            }
        
        return predictions
    
    def analyze_betting_value(self, predictions: dict, home_odds: float, 
                            draw_odds: float, away_odds: float, min_value: float = 0.05) -> dict:
        """Analyze betting value opportunities"""
        
        analysis = {}
        
        for model_name, pred_data in predictions.items():
            probs = pred_data['probabilities']
            
            value_bets = []
            
            # Check home win value
            if probs['home_win'] > (1/home_odds + min_value):
                value = (probs['home_win'] - 1/home_odds) / (1/home_odds)
                value_bets.append({
                    'outcome': 'Home Win',
                    'odds': home_odds,
                    'model_probability': probs['home_win'],
                    'implied_probability': 1/home_odds,
                    'value': value,
                    'kelly_fraction': self.calculate_kelly(probs['home_win'], home_odds)
                })
            
            # Check draw value  
            if probs['draw'] > (1/draw_odds + min_value):
                value = (probs['draw'] - 1/draw_odds) / (1/draw_odds)
                value_bets.append({
                    'outcome': 'Draw',
                    'odds': draw_odds,
                    'model_probability': probs['draw'],
                    'implied_probability': 1/draw_odds,
                    'value': value,
                    'kelly_fraction': self.calculate_kelly(probs['draw'], draw_odds)
                })
            
            # Check away win value
            if probs['away_win'] > (1/away_odds + min_value):
                value = (probs['away_win'] - 1/away_odds) / (1/away_odds)
                value_bets.append({
                    'outcome': 'Away Win',
                    'odds': away_odds,
                    'model_probability': probs['away_win'],
                    'implied_probability': 1/away_odds,
                    'value': value,
                    'kelly_fraction': self.calculate_kelly(probs['away_win'], away_odds)
                })
            
            analysis[model_name] = {
                'prediction': pred_data['prediction'],
                'confidence': pred_data['confidence'],
                'value_bets': sorted(value_bets, key=lambda x: x['value'], reverse=True)
            }
        
        return analysis
    
    def calculate_kelly(self, probability: float, odds: float) -> float:
        """Calculate Kelly Criterion fraction for bet sizing"""
        if probability <= 1/odds:
            return 0.0
        
        b = odds - 1  # Net odds received
        p = probability  # Probability of winning
        q = 1 - p  # Probability of losing
        
        kelly = (b * p - q) / b
        return max(0, min(kelly, 0.25))  # Cap at 25% of bankroll
    
    def save_models(self, filepath: str):
        """Save trained models"""
        model_data = {
            'models': self.models,
            'scaler': self.scaler
        }
        joblib.dump(model_data, filepath)
        self.logger.info(f"Models saved to {filepath}")
    
    def load_models(self, filepath: str):
        """Load trained models"""
        try:
            model_data = joblib.load(filepath)
            self.models = model_data['models']
            self.scaler = model_data['scaler']
            self.logger.info(f"Models loaded from {filepath}")
            return True
        except:
            self.logger.info("No saved models found, will train new models")
            return False

def main():
    """Main execution function"""
    
    API_KEY = "ceb338b9bcb82a452efc114fb2d3cccac67f58be1569e7b5acf1d2195adeae11"
    MODEL_PATH = "soccer_prediction_models.pkl"
    
    print("⚽ Enhanced Soccer Betting Predictor")
    print("=" * 50)
    
    predictor = BettingPredictor(API_KEY)
    
    # Try to load existing models
    if not predictor.load_models(MODEL_PATH):
        print("\n📚 Training new models with Premier League data...")
        
        # Collect and prepare training data
        X, y, match_info = predictor.collect_training_data(league_id=1625, pages=3)
        
        print(f"📊 Training data: {len(X)} matches with {len(X[0])} features")
        print(f"🎯 Outcomes - Away: {np.sum(y==0)}, Draw: {np.sum(y==1)}, Home: {np.sum(y==2)}")
        
        # Train models
        predictor.train_models(X, y)
        
        # Save models
        predictor.save_models(MODEL_PATH)
        
    print("\n🔮 Making Sample Predictions")
    print("=" * 30)
    
    # Example match predictions
    test_matches = [
        {
            'name': 'Manchester City vs Arsenal',
            'home_odds': 1.8, 'draw_odds': 3.5, 'away_odds': 4.2
        },
        {
            'name': 'Liverpool vs Chelsea', 
            'home_odds': 2.1, 'draw_odds': 3.2, 'away_odds': 3.4
        },
        {
            'name': 'Brighton vs Everton',
            'home_odds': 2.3, 'draw_odds': 3.1, 'away_odds': 3.2
        }
    ]
    
    for match in test_matches:
        print(f"\n🏆 {match['name']}")
        print(f"📊 Odds - Home: {match['home_odds']}, Draw: {match['draw_odds']}, Away: {match['away_odds']}")
        
        # Get predictions
        predictions = predictor.predict_match_outcome(
            match['home_odds'], match['draw_odds'], match['away_odds']
        )
        
        # Analyze value
        value_analysis = predictor.analyze_betting_value(
            predictions, match['home_odds'], match['draw_odds'], match['away_odds']
        )
        
        # Display results
        for model_name, analysis in value_analysis.items():
            print(f"\n   {model_name.upper()}")
            print(f"   Prediction: {analysis['prediction']} (Confidence: {analysis['confidence']:.3f})")
            
            if analysis['value_bets']:
                print(f"   💰 Value Opportunities:")
                for bet in analysis['value_bets']:
                    print(f"      {bet['outcome']}: {bet['value']:.1%} value, "
                          f"Kelly: {bet['kelly_fraction']:.1%} of bankroll")
            else:
                print(f"   ❌ No value bets identified")
    
    print("\n" + "=" * 50)
    print("✅ Analysis Complete!")
    print("\n⚠️  Important Disclaimers:")
    print("• Past performance doesn't guarantee future results")
    print("• Always bet responsibly and within your means")
    print("• Consider team news, injuries, and other factors")
    print("• Use proper bankroll management strategies")
    print("• This is for educational purposes only")

if __name__ == "__main__":
    main()