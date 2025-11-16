#!/usr/bin/env python3
"""
Soccer Betting Predictor using FootyStats API

This script fetches soccer match data from FootyStats API and uses machine learning
to predict match outcomes for betting purposes.

Author: Claude Code Assistant
Date: 2025-09-04
"""

import requests
# import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import time
from typing import Dict, List, Tuple, Optional
import logging
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, accuracy_score
import joblib
import warnings
warnings.filterwarnings('ignore')

class FootyStatsAPI:
    """Client for FootyStats API interactions"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.football-data-api.com"
        self.session = requests.Session()
        self.rate_limit_delay = 1  # seconds between requests
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make API request with error handling and rate limiting"""
        url = f"{self.base_url}/{endpoint}"
        
        if params is None:
            params = {}
        params['key'] = self.api_key
        
        try:
            time.sleep(self.rate_limit_delay)  # Rate limiting
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            return {}
    
    def get_league_matches(self, league_id: int, season: str = None, page: int = 1) -> List[Dict]:
        """Fetch matches for a specific league"""
        params = {
            'league_id': league_id,
            'page': page
        }
        if season:
            params['season'] = season
            
        data = self.make_request('league-matches', params)
        return data.get('data', [])
    
    def get_team_stats(self, team_id: int, season: str = None) -> Dict:
        """Fetch team statistics"""
        params = {'team_id': team_id}
        if season:
            params['season'] = season
            
        return self.make_request('team-stats', params)
    
    def get_head_to_head(self, team1_id: int, team2_id: int) -> Dict:
        """Fetch head-to-head statistics between two teams"""
        params = {
            'team1_id': team1_id,
            'team2_id': team2_id
        }
        return self.make_request('head-to-head', params)


class DataProcessor:
    """Handles data preprocessing and feature engineering"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.logger = logging.getLogger(__name__)
    
    def process_match_data(self, matches: List[Dict]) -> pd.DataFrame:
        """Process raw match data into features"""
        processed_data = []
        
        for match in matches:
            if not match or 'home_team' not in match or 'away_team' not in match:
                continue
                
            features = self.extract_match_features(match)
            if features:
                processed_data.append(features)
        
        return pd.DataFrame(processed_data)
    
    def extract_match_features(self, match: Dict) -> Dict:
        """Extract relevant features from a single match"""
        try:
            features = {
                # Basic match info
                'match_id': match.get('id'),
                'date': match.get('date'),
                'home_team_id': match.get('home_team', {}).get('id'),
                'away_team_id': match.get('away_team', {}).get('id'),
                
                # Match outcome (target variable)
                'outcome': self.get_match_outcome(match),
                
                # Team form and statistics
                'home_goals_for_avg': match.get('home_team_stats', {}).get('goals_for_avg', 0),
                'home_goals_against_avg': match.get('home_team_stats', {}).get('goals_against_avg', 0),
                'away_goals_for_avg': match.get('away_team_stats', {}).get('goals_for_avg', 0),
                'away_goals_against_avg': match.get('away_team_stats', {}).get('goals_against_avg', 0),
                
                # Form (last 5 games)
                'home_form_points': self.calculate_form_points(match.get('home_team_form', [])),
                'away_form_points': self.calculate_form_points(match.get('away_team_form', [])),
                
                # Head-to-head record
                'h2h_home_wins': match.get('h2h_stats', {}).get('home_wins', 0),
                'h2h_away_wins': match.get('h2h_stats', {}).get('away_wins', 0),
                'h2h_draws': match.get('h2h_stats', {}).get('draws', 0),
                
                # Betting odds (if available)
                'home_odds': match.get('odds', {}).get('home', 2.0),
                'draw_odds': match.get('odds', {}).get('draw', 3.0),
                'away_odds': match.get('odds', {}).get('away', 2.0),
                
                # Additional stats
                'home_position': match.get('home_team_stats', {}).get('league_position', 10),
                'away_position': match.get('away_team_stats', {}).get('league_position', 10),
                'total_goals_over_2_5': match.get('stats', {}).get('over_2_5', 0),
                'both_teams_to_score': match.get('stats', {}).get('btts', 0),
            }
            
            # Calculate derived features
            features.update(self.calculate_derived_features(features))
            
            return features
            
        except Exception as e:
            self.logger.error(f"Error extracting features from match: {e}")
            return {}
    
    def get_match_outcome(self, match: Dict) -> str:
        """Determine match outcome (Home/Draw/Away)"""
        home_score = match.get('home_score')
        away_score = match.get('away_score')
        
        if home_score is None or away_score is None:
            return 'Unknown'
        
        if home_score > away_score:
            return 'Home'
        elif away_score > home_score:
            return 'Away'
        else:
            return 'Draw'
    
    def calculate_form_points(self, form: List[str]) -> int:
        """Calculate form points from recent results (W=3, D=1, L=0)"""
        points_map = {'W': 3, 'D': 1, 'L': 0}
        return sum(points_map.get(result, 0) for result in form[-5:])
    
    def calculate_derived_features(self, features: Dict) -> Dict:
        """Calculate additional derived features"""
        derived = {}
        
        # Goal difference
        derived['home_goal_diff'] = features['home_goals_for_avg'] - features['home_goals_against_avg']
        derived['away_goal_diff'] = features['away_goals_for_avg'] - features['away_goals_against_avg']
        
        # Form difference
        derived['form_diff'] = features['home_form_points'] - features['away_form_points']
        
        # Position difference
        derived['position_diff'] = features['away_position'] - features['home_position']
        
        # Odds-based probabilities
        home_prob = 1 / features['home_odds'] if features['home_odds'] > 0 else 0
        draw_prob = 1 / features['draw_odds'] if features['draw_odds'] > 0 else 0
        away_prob = 1 / features['away_odds'] if features['away_odds'] > 0 else 0
        
        total_prob = home_prob + draw_prob + away_prob
        if total_prob > 0:
            derived['home_implied_prob'] = home_prob / total_prob
            derived['draw_implied_prob'] = draw_prob / total_prob
            derived['away_implied_prob'] = away_prob / total_prob
        else:
            derived['home_implied_prob'] = 0.33
            derived['draw_implied_prob'] = 0.33
            derived['away_implied_prob'] = 0.33
        
        # Strength indicators
        derived['home_attack_strength'] = features['home_goals_for_avg'] / max(features['away_goals_against_avg'], 0.1)
        derived['away_attack_strength'] = features['away_goals_for_avg'] / max(features['home_goals_against_avg'], 0.1)
        
        return derived
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features for machine learning"""
        # Remove non-feature columns
        feature_cols = [col for col in df.columns if col not in ['match_id', 'date', 'outcome', 'home_team_id', 'away_team_id']]
        
        X = df[feature_cols].fillna(0)
        y = df['outcome']
        
        # Remove unknown outcomes
        mask = y != 'Unknown'
        X = X[mask]
        y = y[mask]
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Encode target
        y_encoded = self.label_encoder.fit_transform(y)
        
        return X_scaled, y_encoded, feature_cols


class BettingPredictor:
    """Main class for soccer betting predictions"""
    
    def __init__(self, api_key: str):
        self.api = FootyStatsAPI(api_key)
        self.processor = DataProcessor()
        self.models = {}
        self.feature_cols = []
        self.logger = logging.getLogger(__name__)
        
    def collect_training_data(self, league_ids: List[int], seasons: List[str] = None) -> pd.DataFrame:
        """Collect training data from multiple leagues and seasons"""
        all_matches = []
        
        for league_id in league_ids:
            self.logger.info(f"Collecting data for league {league_id}")
            
            if seasons:
                for season in seasons:
                    matches = self.api.get_league_matches(league_id, season)
                    all_matches.extend(matches)
            else:
                matches = self.api.get_league_matches(league_id)
                all_matches.extend(matches)
        
        self.logger.info(f"Collected {len(all_matches)} matches")
        return self.processor.process_match_data(all_matches)
    
    def train_models(self, df: pd.DataFrame):
        """Train multiple models for prediction"""
        X, y, feature_cols = self.processor.prepare_features(df)
        self.feature_cols = feature_cols
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        
        # Random Forest
        rf_model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        rf_model.fit(X_train, y_train)
        
        # Gradient Boosting
        gb_model = GradientBoostingClassifier(n_estimators=100, random_state=42)
        gb_model.fit(X_train, y_train)
        
        self.models = {
            'random_forest': rf_model,
            'gradient_boosting': gb_model
        }
        
        # Evaluate models
        for name, model in self.models.items():
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            self.logger.info(f"{name} accuracy: {accuracy:.3f}")
    
    def predict_match(self, home_team_id: int, away_team_id: int, match_data: Dict = None) -> Dict:
        """Predict outcome for a specific match"""
        if not self.models:
            raise ValueError("Models not trained. Call train_models() first.")
        
        # If match_data not provided, create basic structure
        if match_data is None:
            match_data = {
                'home_team': {'id': home_team_id},
                'away_team': {'id': away_team_id},
                'home_team_stats': {},
                'away_team_stats': {},
                'odds': {'home': 2.0, 'draw': 3.0, 'away': 2.0}
            }
        
        # Extract features
        features = self.processor.extract_match_features(match_data)
        if not features:
            return {'error': 'Could not extract features'}
        
        # Create DataFrame
        feature_df = pd.DataFrame([features])
        X = feature_df[self.feature_cols].fillna(0)
        X_scaled = self.processor.scaler.transform(X)
        
        predictions = {}
        
        for name, model in self.models.items():
            # Get prediction and probabilities
            pred_class = model.predict(X_scaled)[0]
            pred_proba = model.predict_proba(X_scaled)[0]
            
            # Convert back to labels
            pred_label = self.processor.label_encoder.inverse_transform([pred_class])[0]
            
            class_labels = self.processor.label_encoder.classes_
            proba_dict = {label: prob for label, prob in zip(class_labels, pred_proba)}
            
            predictions[name] = {
                'prediction': pred_label,
                'probabilities': proba_dict,
                'confidence': max(pred_proba)
            }
        
        return predictions
    
    def analyze_betting_value(self, predictions: Dict, odds: Dict) -> Dict:
        """Analyze betting value based on predictions and odds"""
        analysis = {}
        
        for model_name, pred_data in predictions.items():
            if 'probabilities' not in pred_data:
                continue
                
            probs = pred_data['probabilities']
            value_bets = []
            
            # Check each outcome for value
            outcome_mapping = {'Home': 'home', 'Draw': 'draw', 'Away': 'away'}
            
            for outcome, prob in probs.items():
                odds_key = outcome_mapping.get(outcome)
                if odds_key and odds_key in odds:
                    implied_prob = 1 / odds[odds_key]
                    if prob > implied_prob:  # We think it's more likely than bookmaker
                        value = (prob - implied_prob) / implied_prob
                        value_bets.append({
                            'outcome': outcome,
                            'our_probability': prob,
                            'implied_probability': implied_prob,
                            'odds': odds[odds_key],
                            'value': value
                        })
            
            analysis[model_name] = {
                'prediction': pred_data['prediction'],
                'confidence': pred_data['confidence'],
                'value_bets': sorted(value_bets, key=lambda x: x['value'], reverse=True)
            }
        
        return analysis
    
    def save_models(self, filepath: str):
        """Save trained models and processors"""
        model_data = {
            'models': self.models,
            'scaler': self.processor.scaler,
            'label_encoder': self.processor.label_encoder,
            'feature_cols': self.feature_cols
        }
        joblib.dump(model_data, filepath)
        self.logger.info(f"Models saved to {filepath}")
    
    def load_models(self, filepath: str):
        """Load trained models and processors"""
        model_data = joblib.load(filepath)
        self.models = model_data['models']
        self.processor.scaler = model_data['scaler']
        self.processor.label_encoder = model_data['label_encoder']
        self.feature_cols = model_data['feature_cols']
        self.logger.info(f"Models loaded from {filepath}")


def main():
    """Example usage of the betting predictor"""
    
    # Configuration
    API_KEY = "ceb338b9bcb82a452efc114fb2d3cccac67f58be1569e7b5acf1d2195adeae11"
    MODEL_PATH = "soccer_betting_models.pkl"
    
    # Major league IDs (these are examples - check FootyStats for actual IDs)
    LEAGUE_IDS = [
        1625,  # Premier League (example)
        1729,  # La Liga (example) 
        1854,  # Bundesliga (example)
        # Add more league IDs as needed
    ]
    
    try:
        # Initialize predictor
        predictor = BettingPredictor(API_KEY)
        
        print("🏈 Soccer Betting Predictor")
        print("=" * 40)
        
        # Check if we have saved models
        try:
            predictor.load_models(MODEL_PATH)
            print("✅ Loaded existing models")
        except:
            print("📚 Training new models...")
            
            # Collect training data
            training_data = predictor.collect_training_data(LEAGUE_IDS)
            
            if len(training_data) > 0:
                print(f"📊 Collected {len(training_data)} matches for training")
                
                # Train models
                predictor.train_models(training_data)
                
                # Save models
                predictor.save_models(MODEL_PATH)
                print("✅ Models trained and saved")
            else:
                print("❌ No training data collected. Check API key and league IDs.")
                return
        
        # Example prediction
        print("\n🔮 Making sample prediction...")
        
        sample_odds = {
            'home': 2.1,
            'draw': 3.2,
            'away': 3.5
        }
        
        # Make prediction (using dummy data for example)
        sample_match = {
            'home_team': {'id': 1},
            'away_team': {'id': 2},
            'home_team_stats': {'goals_for_avg': 1.8, 'goals_against_avg': 1.2},
            'away_team_stats': {'goals_for_avg': 1.5, 'goals_against_avg': 1.4},
            'odds': sample_odds
        }
        
        predictions = predictor.predict_match(1, 2, sample_match)
        
        print("\n📈 Prediction Results:")
        for model_name, pred_data in predictions.items():
            print(f"\n{model_name.upper()}:")
            print(f"  Prediction: {pred_data['prediction']}")
            print(f"  Confidence: {pred_data['confidence']:.3f}")
            print("  Probabilities:")
            for outcome, prob in pred_data['probabilities'].items():
                print(f"    {outcome}: {prob:.3f}")
        
        # Analyze betting value
        print("\n💰 Betting Value Analysis:")
        value_analysis = predictor.analyze_betting_value(predictions, sample_odds)
        
        for model_name, analysis in value_analysis.items():
            print(f"\n{model_name.upper()}:")
            if analysis['value_bets']:
                print("  Value bets found:")
                for bet in analysis['value_bets']:
                    print(f"    {bet['outcome']}: {bet['value']:.2%} value at odds {bet['odds']}")
            else:
                print("  No value bets identified")
        
        print("\n✨ Analysis complete!")
        print("\n⚠️  Remember: Gambling involves risk. Only bet what you can afford to lose.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logging.error(f"Main execution error: {e}", exc_info=True)


if __name__ == "__main__":
    main()