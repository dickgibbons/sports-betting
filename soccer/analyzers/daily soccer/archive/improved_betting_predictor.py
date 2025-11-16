#!/usr/bin/env python3
"""
Improved Soccer Betting Predictor

Key improvements:
1. Conservative Kelly Criterion with fractional betting
2. Enhanced risk management and position sizing
3. Better feature engineering with momentum indicators
4. Multi-model ensemble with confidence weighting
5. Strict value threshold requirements
6. Dynamic bankroll protection
"""

import requests
import json
import numpy as np
import pandas as pd
import time
import logging
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.metrics import classification_report, accuracy_score, log_loss
from sklearn.calibration import CalibratedClassifierCV
import joblib
import warnings
warnings.filterwarnings('ignore')


class ImprovedFootyStatsAPI:
    """Enhanced API client with better error handling and rate limiting"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.football-data-api.com"
        self.session = requests.Session()
        self.rate_limit_delay = 1.5  # More conservative rate limiting
        self.request_count = 0
        self.max_requests_per_hour = 100
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def make_request(self, endpoint: str, params: dict = None, retries: int = 3) -> dict:
        """Make API request with enhanced error handling and retries"""
        url = f"{self.base_url}/{endpoint}"
        
        if params is None:
            params = {}
        params['key'] = self.api_key
        
        for attempt in range(retries):
            try:
                # Rate limiting
                if self.request_count >= self.max_requests_per_hour:
                    self.logger.warning("Rate limit reached, waiting...")
                    time.sleep(3600)  # Wait 1 hour
                    self.request_count = 0
                
                time.sleep(self.rate_limit_delay)
                response = self.session.get(url, params=params, timeout=30)
                self.request_count += 1
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Rate limited
                    self.logger.warning(f"Rate limited, waiting before retry {attempt + 1}")
                    time.sleep(60)  # Wait 1 minute
                else:
                    self.logger.error(f"API Error {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.logger.error(f"Request exception (attempt {attempt + 1}): {e}")
                if attempt < retries - 1:
                    time.sleep(5 * (attempt + 1))  # Exponential backoff
        
        return {'error': 'Failed after retries'}
    
    def get_league_matches(self, league_id: int, season: str = None, pages: int = 1) -> list:
        """Fetch matches with pagination support"""
        all_matches = []
        
        for page in range(1, pages + 1):
            params = {'league_id': league_id, 'page': page}
            if season:
                params['season'] = season
                
            data = self.make_request('league-matches', params)
            matches = data.get('data', [])
            
            if not matches:
                break
                
            all_matches.extend(matches)
            
            # Check if we have more pages
            if len(matches) < 50:  # Typical page size
                break
        
        return all_matches


class AdvancedFeatureEngineer:
    """Advanced feature engineering for soccer betting predictions"""
    
    def __init__(self):
        self.scaler = RobustScaler()  # More robust to outliers
        self.logger = logging.getLogger(__name__)
        
    def extract_enhanced_features(self, matches: list) -> tuple:
        """Extract comprehensive features from match data"""
        features = []
        labels = []
        match_info = []
        
        # Sort matches by date for time-based features
        valid_matches = [m for m in matches if self.is_valid_match(m)]
        valid_matches.sort(key=lambda x: x.get('date_unix', 0))
        
        for i, match in enumerate(valid_matches):
            try:
                feature_vector = self.create_comprehensive_features(match, i, valid_matches)
                if feature_vector is None:
                    continue
                    
                features.append(feature_vector)
                labels.append(self.get_match_outcome(match))
                match_info.append({
                    'id': match.get('id'),
                    'home_name': match.get('home_name', 'Unknown'),
                    'away_name': match.get('away_name', 'Unknown'),
                    'date_unix': match.get('date_unix', 0),
                    'odds': {
                        'home': match.get('odds_ft_1', 2.0),
                        'draw': match.get('odds_ft_x', 3.0),
                        'away': match.get('odds_ft_2', 2.0)
                    }
                })
            except Exception as e:
                self.logger.error(f"Error processing match {match.get('id')}: {e}")
                continue
        
        return np.array(features), np.array(labels), match_info
    
    def is_valid_match(self, match: dict) -> bool:
        """Enhanced validation for match data"""
        return (
            match.get('homeGoalCount') is not None and
            match.get('awayGoalCount') is not None and
            match.get('odds_ft_1') is not None and
            match.get('odds_ft_x') is not None and
            match.get('odds_ft_2') is not None and
            float(match.get('odds_ft_1', 0)) > 1.01 and
            float(match.get('odds_ft_x', 0)) > 1.01 and
            float(match.get('odds_ft_2', 0)) > 1.01
        )
    
    def create_comprehensive_features(self, match: dict, match_index: int, all_matches: list) -> list:
        """Create comprehensive feature set"""
        try:
            # Basic odds features
            home_odds = float(match.get('odds_ft_1', 2.0))
            draw_odds = float(match.get('odds_ft_x', 3.0))
            away_odds = float(match.get('odds_ft_2', 2.0))
            
            # Implied probabilities
            total_prob = (1/home_odds) + (1/draw_odds) + (1/away_odds)
            home_prob = (1/home_odds) / total_prob
            draw_prob = (1/draw_odds) / total_prob
            away_prob = (1/away_odds) / total_prob
            
            # Market efficiency indicators
            overround = total_prob - 1.0
            favorite_odds = min(home_odds, away_odds)
            underdog_odds = max(home_odds, away_odds)
            odds_ratio = underdog_odds / favorite_odds
            
            # Additional market odds (if available)
            btts_yes = float(match.get('btts_yes', 1.8))
            btts_no = float(match.get('btts_no', 1.8))
            over_25 = float(match.get('over_25', 1.8))
            under_25 = float(match.get('under_25', 1.8))
            
            # Goal expectancy from market
            btts_prob = 1 / btts_yes if btts_yes > 1.01 else 0.5
            over_25_prob = 1 / over_25 if over_25 > 1.01 else 0.5
            
            # Time-based features
            date_unix = match.get('date_unix', 0)
            if date_unix > 0:
                match_date = datetime.fromtimestamp(date_unix)
                day_of_week = match_date.weekday()  # 0 = Monday
                is_weekend = 1 if day_of_week >= 5 else 0
                month = match_date.month
            else:
                day_of_week = 0
                is_weekend = 0
                month = 1
            
            # Historical performance indicators (if we have enough data)
            home_form, away_form = self.calculate_team_form(match, match_index, all_matches)
            
            # League competitiveness (based on odds distribution)
            league_competitiveness = self.estimate_league_strength(match, all_matches)
            
            # Feature vector
            features = [
                # Basic market features
                home_odds, draw_odds, away_odds,
                home_prob, draw_prob, away_prob,
                
                # Market efficiency
                overround, odds_ratio, favorite_odds, underdog_odds,
                
                # Goals market
                btts_yes, btts_no, over_25, under_25,
                btts_prob, over_25_prob,
                
                # Derived probabilities
                home_prob - (1/3),  # Deviation from equal probability
                draw_prob - (1/3),
                away_prob - (1/3),
                
                # Market pressure indicators
                home_prob * home_odds - 1,  # Expected value for home bet
                draw_prob * draw_odds - 1,  # Expected value for draw bet
                away_prob * away_odds - 1,  # Expected value for away bet
                
                # Time features
                day_of_week / 6.0,  # Normalized
                is_weekend,
                month / 12.0,  # Normalized
                
                # Form features
                home_form['points_per_game'],
                away_form['points_per_game'],
                home_form['goals_for_avg'],
                home_form['goals_against_avg'],
                away_form['goals_for_avg'], 
                away_form['goals_against_avg'],
                
                # Form momentum
                home_form['points_per_game'] - away_form['points_per_game'],
                home_form['goals_for_avg'] - away_form['goals_against_avg'],
                away_form['goals_for_avg'] - home_form['goals_against_avg'],
                
                # League context
                league_competitiveness,
                
                # Risk indicators
                1 if favorite_odds < 1.5 else 0,  # Heavy favorite flag
                1 if min(home_odds, draw_odds, away_odds) < 1.3 else 0,  # Very short odds flag
                1 if max(home_odds, draw_odds, away_odds) > 8.0 else 0,  # Long shot flag
            ]
            
            # Ensure all features are numeric and finite
            features = [float(f) if isinstance(f, (int, float)) and np.isfinite(f) else 0.0 for f in features]
            
            return features
            
        except Exception as e:
            self.logger.error(f"Error creating features: {e}")
            return None
    
    def calculate_team_form(self, current_match: dict, match_index: int, all_matches: list) -> tuple:
        """Calculate recent form for both teams"""
        home_team = current_match.get('home_name', '')
        away_team = current_match.get('away_name', '')
        current_date = current_match.get('date_unix', 0)
        
        # Look for recent matches of both teams
        lookback_days = 30  # Look at last 30 days
        cutoff_date = current_date - (lookback_days * 24 * 3600)
        
        home_matches = []
        away_matches = []
        
        # Find recent matches for both teams (before current match)
        for i in range(max(0, match_index - 50), match_index):  # Look at up to 50 previous matches
            match = all_matches[i]
            match_date = match.get('date_unix', 0)
            
            if match_date < cutoff_date:
                continue
                
            if match.get('home_name') == home_team or match.get('away_name') == home_team:
                home_matches.append(match)
            if match.get('home_name') == away_team or match.get('away_name') == away_team:
                away_matches.append(match)
        
        home_form = self.analyze_team_form(home_team, home_matches[-5:])  # Last 5 matches
        away_form = self.analyze_team_form(away_team, away_matches[-5:])  # Last 5 matches
        
        return home_form, away_form
    
    def analyze_team_form(self, team_name: str, matches: list) -> dict:
        """Analyze form from recent matches"""
        if not matches:
            return {
                'points_per_game': 1.0,  # Neutral assumption
                'goals_for_avg': 1.5,
                'goals_against_avg': 1.5,
                'matches_played': 0
            }
        
        total_points = 0
        total_goals_for = 0
        total_goals_against = 0
        
        for match in matches:
            home_goals = match.get('homeGoalCount', 0)
            away_goals = match.get('awayGoalCount', 0)
            
            if match.get('home_name') == team_name:
                # Team played at home
                total_goals_for += home_goals
                total_goals_against += away_goals
                if home_goals > away_goals:
                    total_points += 3
                elif home_goals == away_goals:
                    total_points += 1
            elif match.get('away_name') == team_name:
                # Team played away
                total_goals_for += away_goals
                total_goals_against += home_goals
                if away_goals > home_goals:
                    total_points += 3
                elif away_goals == home_goals:
                    total_points += 1
        
        num_matches = len(matches)
        return {
            'points_per_game': total_points / num_matches,
            'goals_for_avg': total_goals_for / num_matches,
            'goals_against_avg': total_goals_against / num_matches,
            'matches_played': num_matches
        }
    
    def estimate_league_strength(self, match: dict, all_matches: list) -> float:
        """Estimate league competitiveness based on odds patterns"""
        # Simple measure: average of minimum odds across recent matches
        # More competitive leagues tend to have higher minimum odds
        recent_matches = all_matches[-20:] if len(all_matches) >= 20 else all_matches
        
        min_odds_list = []
        for m in recent_matches:
            try:
                odds = [float(m.get('odds_ft_1', 2)), float(m.get('odds_ft_x', 3)), float(m.get('odds_ft_2', 2))]
                min_odds_list.append(min(odds))
            except:
                continue
        
        if min_odds_list:
            return np.mean(min_odds_list)
        return 1.8  # Default value
    
    def get_match_outcome(self, match: dict) -> int:
        """Get match outcome as numeric label"""
        home_goals = match.get('homeGoalCount', 0)
        away_goals = match.get('awayGoalCount', 0)
        
        if home_goals > away_goals:
            return 2  # Home win
        elif away_goals > home_goals:
            return 0  # Away win
        else:
            return 1  # Draw


class ImprovedBettingPredictor:
    """Enhanced betting predictor with risk management"""
    
    def __init__(self, api_key: str):
        self.api = ImprovedFootyStatsAPI(api_key)
        self.feature_engineer = AdvancedFeatureEngineer()
        
        # Ensemble of calibrated models
        self.base_models = {
            'random_forest': RandomForestClassifier(
                n_estimators=200, max_depth=15, min_samples_split=10,
                min_samples_leaf=5, random_state=42, n_jobs=-1
            ),
            'gradient_boosting': GradientBoostingClassifier(
                n_estimators=150, learning_rate=0.1, max_depth=8,
                min_samples_split=10, random_state=42
            ),
            'logistic': LogisticRegression(
                random_state=42, max_iter=1000, C=1.0
            )
        }
        
        self.calibrated_models = {}
        self.ensemble_model = None
        self.feature_names = []
        
        # Risk management parameters
        self.max_bet_fraction = 0.05  # Never bet more than 5% of bankroll
        self.kelly_fraction = 0.25  # Use quarter Kelly
        self.min_edge = 0.08  # Require at least 8% edge
        self.min_confidence = 0.65  # Require 65% confidence
        self.max_odds = 6.0  # Don't bet on odds higher than 6.0
        
        self.logger = logging.getLogger(__name__)
        
    def collect_and_train(self, league_ids: list, seasons: list = None, pages_per_league: int = 3):
        """Collect data and train models"""
        print("📊 Collecting training data...")
        
        all_features = []
        all_labels = []
        all_match_info = []
        
        for league_id in league_ids:
            print(f"   📈 Processing league {league_id}...")
            
            if seasons:
                for season in seasons:
                    matches = self.api.get_league_matches(league_id, season, pages_per_league)
                    if matches:
                        features, labels, match_info = self.feature_engineer.extract_enhanced_features(matches)
                        if len(features) > 0:
                            all_features.extend(features)
                            all_labels.extend(labels)
                            all_match_info.extend(match_info)
            else:
                matches = self.api.get_league_matches(league_id, pages=pages_per_league)
                if matches:
                    features, labels, match_info = self.feature_engineer.extract_enhanced_features(matches)
                    if len(features) > 0:
                        all_features.extend(features)
                        all_labels.extend(labels)
                        all_match_info.extend(match_info)
        
        if not all_features:
            raise ValueError("No training data collected!")
        
        X = np.array(all_features)
        y = np.array(all_labels)
        
        print(f"📊 Training data: {len(X)} matches with {X.shape[1]} features")
        print(f"🎯 Label distribution - Home: {np.sum(y==2)}, Draw: {np.sum(y==1)}, Away: {np.sum(y==0)}")
        
        # Scale features
        X_scaled = self.feature_engineer.scaler.fit_transform(X)
        
        # Train and calibrate individual models
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print("🤖 Training and calibrating models...")
        for name, model in self.base_models.items():
            print(f"   Training {name}...")
            
            # Train base model
            model.fit(X_train, y_train)
            
            # Calibrate probabilities
            calibrated_model = CalibratedClassifierCV(model, method='isotonic', cv=3)
            calibrated_model.fit(X_train, y_train)
            
            self.calibrated_models[name] = calibrated_model
            
            # Evaluate
            y_pred = calibrated_model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            print(f"     {name} accuracy: {accuracy:.3f}")
        
        # Create ensemble
        ensemble_estimators = [(name, model) for name, model in self.calibrated_models.items()]
        self.ensemble_model = VotingClassifier(
            estimators=ensemble_estimators,
            voting='soft'  # Use predicted probabilities
        )
        self.ensemble_model.fit(X_train, y_train)
        
        # Evaluate ensemble
        y_pred_ensemble = self.ensemble_model.predict(X_test)
        ensemble_accuracy = accuracy_score(y_test, y_pred_ensemble)
        print(f"🎯 Ensemble accuracy: {ensemble_accuracy:.3f}")
        
        # Store feature names for later reference
        self.feature_names = [f"feature_{i}" for i in range(X.shape[1])]
        
        return X_test, y_test  # Return test set for further analysis
    
    def predict_match_with_confidence(self, home_odds: float, draw_odds: float, away_odds: float) -> dict:
        """Make prediction with confidence and risk assessment"""
        if not self.ensemble_model:
            raise ValueError("Models not trained!")
        
        # Create synthetic match data from odds
        synthetic_match = self.create_synthetic_match(home_odds, draw_odds, away_odds)
        
        # Extract features
        features = self.feature_engineer.create_comprehensive_features(
            synthetic_match, 0, [synthetic_match]
        )
        
        if features is None:
            return {'error': 'Could not extract features'}
        
        # Scale features
        X = np.array([features])
        X_scaled = self.feature_engineer.scaler.transform(X)
        
        # Get predictions from all models
        predictions = {}
        
        for name, model in self.calibrated_models.items():
            pred_proba = model.predict_proba(X_scaled)[0]
            pred_class = np.argmax(pred_proba)
            confidence = np.max(pred_proba)
            
            predictions[name] = {
                'probabilities': {'away': pred_proba[0], 'draw': pred_proba[1], 'home': pred_proba[2]},
                'prediction': ['Away', 'Draw', 'Home'][pred_class],
                'confidence': confidence
            }
        
        # Ensemble prediction
        ensemble_proba = self.ensemble_model.predict_proba(X_scaled)[0]
        ensemble_class = np.argmax(ensemble_proba)
        ensemble_confidence = np.max(ensemble_proba)
        
        predictions['ensemble'] = {
            'probabilities': {'away': ensemble_proba[0], 'draw': ensemble_proba[1], 'home': ensemble_proba[2]},
            'prediction': ['Away', 'Draw', 'Home'][ensemble_class],
            'confidence': ensemble_confidence
        }
        
        return predictions
    
    def create_synthetic_match(self, home_odds: float, draw_odds: float, away_odds: float) -> dict:
        """Create synthetic match data for prediction"""
        return {
            'odds_ft_1': home_odds,
            'odds_ft_x': draw_odds,
            'odds_ft_2': away_odds,
            'btts_yes': 1.8,  # Default values
            'btts_no': 1.8,
            'over_25': 1.8,
            'under_25': 1.8,
            'date_unix': int(datetime.now().timestamp()),
            'home_name': 'Team A',
            'away_name': 'Team B'
        }
    
    def analyze_betting_value_conservative(self, predictions: dict, home_odds: float, 
                                         draw_odds: float, away_odds: float) -> dict:
        """Conservative value analysis with strict risk management"""
        market_odds = {'home': home_odds, 'draw': draw_odds, 'away': away_odds}
        
        analysis = {}
        
        for model_name, pred_data in predictions.items():
            if 'probabilities' not in pred_data:
                continue
            
            model_probs = pred_data['probabilities']
            confidence = pred_data['confidence']
            
            value_bets = []
            
            for outcome in ['home', 'draw', 'away']:
                model_prob = model_probs[outcome]
                odds = market_odds[outcome]
                
                if odds > self.max_odds:  # Skip very long odds
                    continue
                
                # Market implied probability
                implied_prob = 1 / odds
                
                # Calculate edge
                edge = (model_prob - implied_prob) / implied_prob
                
                # Strict requirements for value betting
                if (edge > self.min_edge and 
                    confidence > self.min_confidence and 
                    model_prob > implied_prob * 1.15):  # Must be 15% better than market
                    
                    # Conservative Kelly fraction
                    kelly_full = (model_prob * odds - 1) / (odds - 1)
                    kelly_conservative = max(0, min(kelly_full * self.kelly_fraction, self.max_bet_fraction))
                    
                    # Additional risk adjustment
                    risk_multiplier = min(1.0, confidence / self.min_confidence)  # Reduce bet size for lower confidence
                    kelly_final = kelly_conservative * risk_multiplier
                    
                    if kelly_final > 0.01:  # Minimum 1% bet
                        expected_value = model_prob * (odds - 1) - (1 - model_prob)
                        
                        value_bets.append({
                            'outcome': outcome.title(),
                            'odds': odds,
                            'model_probability': model_prob,
                            'implied_probability': implied_prob,
                            'edge': edge,
                            'kelly_fraction': kelly_final,
                            'expected_value': expected_value,
                            'confidence': confidence,
                            'risk_level': 'Low' if kelly_final < 0.02 else 'Medium' if kelly_final < 0.04 else 'High'
                        })
            
            # Sort by expected value
            value_bets.sort(key=lambda x: x['expected_value'], reverse=True)
            
            analysis[model_name] = {
                'prediction': pred_data['prediction'],
                'confidence': confidence,
                'value_bets': value_bets[:2]  # Maximum 2 bets per model
            }
        
        return analysis
    
    def save_models(self, filepath: str):
        """Save all models and components"""
        model_data = {
            'calibrated_models': self.calibrated_models,
            'ensemble_model': self.ensemble_model,
            'scaler': self.feature_engineer.scaler,
            'feature_names': self.feature_names,
            'risk_params': {
                'max_bet_fraction': self.max_bet_fraction,
                'kelly_fraction': self.kelly_fraction,
                'min_edge': self.min_edge,
                'min_confidence': self.min_confidence,
                'max_odds': self.max_odds
            }
        }
        joblib.dump(model_data, filepath)
        print(f"💾 Enhanced models saved to {filepath}")
    
    def load_models(self, filepath: str):
        """Load all models and components"""
        try:
            model_data = joblib.load(filepath)
            self.calibrated_models = model_data['calibrated_models']
            self.ensemble_model = model_data['ensemble_model']
            self.feature_engineer.scaler = model_data['scaler']
            self.feature_names = model_data['feature_names']
            
            # Load risk parameters
            risk_params = model_data.get('risk_params', {})
            for param, value in risk_params.items():
                if hasattr(self, param):
                    setattr(self, param, value)
            
            print(f"✅ Enhanced models loaded from {filepath}")
            return True
        except Exception as e:
            print(f"❌ Failed to load models: {e}")
            return False


def main():
    """Example usage with improved predictor"""
    
    API_KEY = "ceb338b9bcb82a452efc114fb2d3cccac67f58be1569e7b5acf1d2195adeae11"
    MODEL_PATH = "improved_soccer_models.pkl"
    
    # Target leagues (verified IDs)
    LEAGUES = [1625, 1729, 1854]  # Premier League, La Liga, Bundesliga
    
    try:
        predictor = ImprovedBettingPredictor(API_KEY)
        
        print("⚽ Improved Soccer Betting Predictor")
        print("=" * 50)
        
        # Try to load existing models
        if not predictor.load_models(MODEL_PATH):
            print("🧠 Training new enhanced models...")
            
            # Collect and train
            X_test, y_test = predictor.collect_and_train(LEAGUES, pages_per_league=2)
            
            # Save models
            predictor.save_models(MODEL_PATH)
        
        print("\n🔮 Testing improved prediction system...")
        
        # Test cases with various scenarios
        test_cases = [
            {'name': 'Close Match', 'home': 2.2, 'draw': 3.1, 'away': 3.4},
            {'name': 'Heavy Favorite', 'home': 1.3, 'draw': 4.5, 'away': 8.0},
            {'name': 'Balanced Odds', 'home': 2.8, 'draw': 3.0, 'away': 2.9},
            {'name': 'Away Favorite', 'home': 4.2, 'draw': 3.5, 'away': 1.8}
        ]
        
        for test in test_cases:
            print(f"\n📊 {test['name']}: {test['home']:.1f} / {test['draw']:.1f} / {test['away']:.1f}")
            
            predictions = predictor.predict_match_with_confidence(
                test['home'], test['draw'], test['away']
            )
            
            analysis = predictor.analyze_betting_value_conservative(
                predictions, test['home'], test['draw'], test['away']
            )
            
            # Show ensemble results
            if 'ensemble' in analysis:
                ensemble = analysis['ensemble']
                print(f"   🤖 Prediction: {ensemble['prediction']} (conf: {ensemble['confidence']:.3f})")
                
                if ensemble['value_bets']:
                    print("   💰 Value opportunities:")
                    for bet in ensemble['value_bets']:
                        print(f"      {bet['outcome']}: {bet['edge']:.1%} edge, "
                              f"{bet['kelly_fraction']:.1%} stake ({bet['risk_level']} risk)")
                else:
                    print("   ❌ No value bets meet criteria")
        
        print("\n✅ Improved prediction system ready!")
        print("\n🔒 Enhanced Safety Features:")
        print("   • Maximum 5% of bankroll per bet")
        print("   • Minimum 8% edge required")
        print("   • Confidence threshold of 65%")
        print("   • No bets on odds above 6.0")
        print("   • Calibrated probability models")
        print("   • Conservative Kelly Criterion")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logging.error(f"Main execution error: {e}", exc_info=True)


if __name__ == "__main__":
    main()