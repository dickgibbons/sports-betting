#!/usr/bin/env python3
"""
Multi-League Soccer Betting Predictor

Focuses on specific leagues for comprehensive betting analysis.
Supports 28+ leagues across multiple continents.
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

class MultiLeaguePredictor:
    """Enhanced predictor focusing on specific leagues"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.football-data-api.com"
        self.session = requests.Session()
        self.rate_limit_delay = 1
        
        # Target leagues with their IDs (updated from UPDATED_supported_leagues_database.csv)
        self.target_leagues = {
            # Europe - Major Leagues
            'Premier League': {'id': 1625, 'country': 'England', 'tier': 1},
            'Championship': {'id': 1626, 'country': 'England', 'tier': 2},
            'FA Trophy': {'id': 1626, 'country': 'England', 'tier': 3},
            'La Liga': {'id': 1729, 'country': 'Spain', 'tier': 1},
            'Bundesliga': {'id': 1854, 'country': 'Germany', 'tier': 1},
            'Serie A': {'id': 2105, 'country': 'Italy', 'tier': 1},
            'Ligue 1': {'id': 1843, 'country': 'France', 'tier': 1},
            'Eredivisie': {'id': 2200, 'country': 'Netherlands', 'tier': 1},
            
            # European Cups
            'UEFA Champions League': {'id': 3000, 'country': 'Europe', 'tier': 0},
            'UEFA Europa League': {'id': 3001, 'country': 'Europe', 'tier': 0},
            'UEFA Europa Conference League': {'id': 3002, 'country': 'Europe', 'tier': 0},
            
            # FIFA Club World Cup
            'FIFA Club World Cup': {'id': 4000, 'country': 'International', 'tier': 0},
            'FIFA Club World Cup Playin': {'id': 4001, 'country': 'International', 'tier': 0},
            
            # World Cup Qualifications
            'WC Qualification Europe': {'id': 4100, 'country': 'International', 'tier': 0},
            'WC Qualification Africa': {'id': 4101, 'country': 'International', 'tier': 0},
            'WC Qualification Asia': {'id': 4102, 'country': 'International', 'tier': 0},
            'WC Qualification South America': {'id': 4103, 'country': 'International', 'tier': 0},
            'WC Qualification CONCACAF': {'id': 4104, 'country': 'International', 'tier': 0},
            'WC Qualification Oceania': {'id': 4105, 'country': 'International', 'tier': 0},
            
            # Americas
            'MLS': {'id': 5000, 'country': 'USA', 'tier': 1},
            'USL League One': {'id': 5002, 'country': 'USA', 'tier': 2},
            'NWSL': {'id': 5003, 'country': 'USA', 'tier': 1},
            'Liga MX': {'id': 5200, 'country': 'Mexico', 'tier': 1},
            'Copa MX': {'id': 5202, 'country': 'Mexico', 'tier': 2},
            'Brazil Serie A': {'id': 5400, 'country': 'Brazil', 'tier': 1},
            'Brazil Serie B': {'id': 5401, 'country': 'Brazil', 'tier': 2},
            'Primera División': {'id': 5500, 'country': 'Argentina', 'tier': 1},
            'Copa Libertadores': {'id': 5300, 'country': 'South America', 'tier': 0},
            
            # Other European Leagues
            'Pro League': {'id': 2400, 'country': 'Belgium', 'tier': 1},
            'Superlig': {'id': 6200, 'country': 'Denmark', 'tier': 1},
            'First League': {'id': 6400, 'country': 'Czech Republic', 'tier': 1},
            'Eliteserien': {'id': 6000, 'country': 'Norway', 'tier': 1},
            'First Division': {'id': 6001, 'country': 'Norway', 'tier': 2},
            'LigaPro': {'id': 2300, 'country': 'Portugal', 'tier': 2},
            'Super League': {'id': 6700, 'country': 'Switzerland', 'tier': 1},
            'Süper Lig': {'id': 6900, 'country': 'Turkey', 'tier': 1},
            
            # CONCACAF
            'CONCACAF Central American Cup': {'id': 7001, 'country': 'International', 'tier': 0},
            'CONCACAF Caribbean Club Championship': {'id': 7002, 'country': 'International', 'tier': 0},
        }
        
        self.models = {}
        self.scaler = StandardScaler()
        self.league_models = {}  # Separate models for each league
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def discover_league_ids(self):
        """Discover available league IDs from the API"""
        print("🔍 Discovering available leagues...")
        print("=" * 50)
        
        # Test various ID ranges to find available leagues
        test_ranges = [
            range(1600, 1700),  # Premier League area
            range(1700, 1800),  # La Liga area
            range(1800, 1900),  # Bundesliga area
            range(2000, 2200),  # Serie A area
            range(2200, 2300),  # Other European leagues
            range(2300, 2500),  # American leagues
        ]
        
        found_leagues = {}
        
        for test_range in test_ranges:
            for league_id in test_range:
                try:
                    url = f"{self.base_url}/league-matches"
                    params = {'key': self.api_key, 'league_id': league_id}
                    
                    time.sleep(self.rate_limit_delay)
                    response = self.session.get(url, params=params)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('data') and len(data.get('data', [])) > 0:
                            # Try to get league name from match data
                            sample_match = data['data'][0]
                            league_name = f"League_{league_id}"  # Default name
                            
                            found_leagues[league_id] = {
                                'name': league_name,
                                'matches': len(data.get('data', [])),
                                'sample_teams': {
                                    'home': sample_match.get('home_name', 'Unknown'),
                                    'away': sample_match.get('away_name', 'Unknown')
                                }
                            }
                            
                            print(f"✅ Found League {league_id}: {found_leagues[league_id]['matches']} matches")
                            print(f"   Sample: {found_leagues[league_id]['sample_teams']['home']} vs {found_leagues[league_id]['sample_teams']['away']}")
                            
                    elif response.status_code == 417:
                        # League not available to user
                        continue
                    else:
                        print(f"❌ League {league_id}: HTTP {response.status_code}")
                        
                except Exception as e:
                    continue
                    
                # Don't overwhelm the API
                if len(found_leagues) > 20:
                    break
            
            if len(found_leagues) > 20:
                break
        
        print(f"\n📊 Summary: Found {len(found_leagues)} available leagues")
        return found_leagues
    
    def get_available_leagues(self):
        """Get leagues that are actually available with your API key"""
        available_leagues = {}
        
        print("🔍 Checking available leagues from your target list...")
        print("=" * 55)
        
        for league_name, league_info in self.target_leagues.items():
            league_id = league_info['id']
            
            if league_id is None:
                print(f"⚠️  {league_name}: ID unknown, skipping")
                continue
                
            try:
                url = f"{self.base_url}/league-matches"
                params = {'key': self.api_key, 'league_id': league_id}
                
                time.sleep(self.rate_limit_delay)
                response = self.session.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    matches = data.get('data', [])
                    
                    if matches:
                        available_leagues[league_name] = {
                            'id': league_id,
                            'matches': len(matches),
                            'country': league_info['country'],
                            'tier': league_info['tier'],
                            'sample_match': {
                                'home': matches[0].get('home_name', 'Unknown'),
                                'away': matches[0].get('away_name', 'Unknown')
                            }
                        }
                        
                        print(f"✅ {league_name} ({league_info['country']}): {len(matches)} matches")
                        print(f"   Sample: {matches[0].get('home_name')} vs {matches[0].get('away_name')}")
                        
                elif response.status_code == 417:
                    print(f"❌ {league_name}: Not available with your API key")
                else:
                    print(f"⚠️  {league_name}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {league_name}: Error - {e}")
        
        print(f"\n📊 Result: {len(available_leagues)} leagues available for analysis")
        return available_leagues
    
    def collect_multi_league_data(self, available_leagues: dict, matches_per_league: int = 200):
        """Collect data from multiple leagues"""
        all_data = []
        league_distribution = {}
        
        print(f"\n📚 Collecting training data from {len(available_leagues)} leagues...")
        print("=" * 60)
        
        for league_name, league_info in available_leagues.items():
            league_id = league_info['id']
            
            print(f"📊 Collecting {league_name} data...")
            
            # Collect data in batches
            collected_matches = []
            page = 1
            
            while len(collected_matches) < matches_per_league and page <= 10:
                try:
                    url = f"{self.base_url}/league-matches"
                    params = {
                        'key': self.api_key,
                        'league_id': league_id,
                        'page': page
                    }
                    
                    time.sleep(self.rate_limit_delay)
                    response = self.session.get(url, params=params)
                    
                    if response.status_code == 200:
                        data = response.json()
                        matches = data.get('data', [])
                        
                        if not matches:
                            break
                            
                        # Add league info to each match
                        for match in matches:
                            match['league_name'] = league_name
                            match['league_country'] = league_info['country']
                            match['league_tier'] = league_info['tier']
                            
                        collected_matches.extend(matches)
                        page += 1
                        
                        print(f"   Page {page-1}: {len(matches)} matches (total: {len(collected_matches)})")
                        
                    else:
                        break
                        
                except Exception as e:
                    print(f"   Error on page {page}: {e}")
                    break
            
            # Process matches for this league
            processed_matches = self.process_league_matches(collected_matches[:matches_per_league])
            all_data.extend(processed_matches)
            
            league_distribution[league_name] = len(processed_matches)
            print(f"✅ {league_name}: {len(processed_matches)} processed matches")
        
        print(f"\n📈 Data Collection Summary:")
        print(f"   Total matches: {len(all_data)}")
        print(f"   Leagues covered: {len(league_distribution)}")
        
        for league, count in sorted(league_distribution.items(), key=lambda x: x[1], reverse=True):
            print(f"   {league}: {count} matches")
        
        return all_data
    
    def process_league_matches(self, matches: list):
        """Process matches with league-specific features"""
        processed = []
        
        for match in matches:
            if not self.is_valid_match(match):
                continue
                
            features = self.extract_match_features(match)
            if features:
                processed.append({
                    'features': features,
                    'outcome': self.get_match_outcome(match),
                    'league': match.get('league_name'),
                    'country': match.get('league_country'),
                    'tier': match.get('league_tier', 1),
                    'match_info': {
                        'home_name': match.get('home_name', 'Unknown'),
                        'away_name': match.get('away_name', 'Unknown'),
                        'date': match.get('date_unix', 0)
                    }
                })
        
        return processed
    
    def is_valid_match(self, match: dict) -> bool:
        """Check if match has required data"""
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
    
    def extract_match_features(self, match: dict) -> list:
        """Extract features with league-specific adjustments"""
        try:
            # Base features
            features = [
                # Odds
                float(match.get('odds_ft_1', 2.0)),
                float(match.get('odds_ft_x', 3.0)),
                float(match.get('odds_ft_2', 2.0)),
                
                # Implied probabilities
                1 / float(match.get('odds_ft_1', 2.0)),
                1 / float(match.get('odds_ft_x', 3.0)),
                1 / float(match.get('odds_ft_2', 2.0)),
                
                # Over/Under odds
                float(match.get('odds_ft_over25', 2.0) if match.get('odds_ft_over25') else 2.0),
                float(match.get('odds_ft_under25', 2.0) if match.get('odds_ft_under25') else 2.0),
                float(match.get('odds_ft_over15', 1.5) if match.get('odds_ft_over15') else 1.5),
                float(match.get('odds_ft_under15', 2.5) if match.get('odds_ft_under15') else 2.5),
                
                # BTTS and other markets
                float(match.get('odds_btts_yes', 2.0) if match.get('odds_btts_yes') else 2.0),
                float(match.get('odds_btts_no', 2.0) if match.get('odds_btts_no') else 2.0),
                
                # Team performance
                float(match.get('home_ppg', 1.0) if match.get('home_ppg') else 1.0),
                float(match.get('away_ppg', 1.0) if match.get('away_ppg') else 1.0),
                
                # Match stats
                float(match.get('totalGoalCount', 0.0)),
                float(match.get('totalCornerCount', 0.0)),
                float(match.get('team_a_possession', 50.0)),
                float(match.get('team_b_possession', 50.0)),
                float(match.get('team_a_shots', 0.0)),
                float(match.get('team_b_shots', 0.0)),
                
                # League-specific features
                float(match.get('league_tier', 1)),  # League tier (1=top, 2=second, etc.)
            ]
            
            # Add derived features
            home_odds = float(match.get('odds_ft_1', 2.0))
            away_odds = float(match.get('odds_ft_2', 2.0))
            draw_odds = float(match.get('odds_ft_x', 3.0))
            
            features.extend([
                home_odds / away_odds,
                abs(home_odds - away_odds),
                min(home_odds, away_odds, draw_odds),
                max(home_odds, away_odds, draw_odds),
            ])
            
            return features
            
        except Exception as e:
            self.logger.error(f"Error extracting features: {e}")
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
    
    def train_multi_league_models(self, processed_data: list):
        """Train models on multi-league data"""
        if not processed_data:
            print("❌ No data available for training")
            return
        
        # Prepare features and labels
        X = np.array([item['features'] for item in processed_data])
        y = np.array([item['outcome'] for item in processed_data])
        
        print(f"\n🤖 Training models on {len(X)} matches...")
        print(f"📊 Features: {X.shape[1]}")
        print(f"🎯 Outcomes - Away: {np.sum(y==0)}, Draw: {np.sum(y==1)}, Home: {np.sum(y==2)}")
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train models
        models = {
            'random_forest': RandomForestClassifier(
                n_estimators=200,
                max_depth=15,
                random_state=42,
                n_jobs=-1,
                class_weight='balanced'
            ),
            'gradient_boosting': GradientBoostingClassifier(
                n_estimators=200,
                max_depth=8,
                learning_rate=0.1,
                random_state=42
            )
        }
        
        print("\n📈 Training Results:")
        print("=" * 30)
        
        for name, model in models.items():
            # Train model
            model.fit(X_train, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test)
            test_accuracy = accuracy_score(y_test, y_pred)
            
            # Cross validation
            cv_scores = cross_val_score(model, X_scaled, y, cv=5)
            
            print(f"\n🤖 {name.upper()}:")
            print(f"   Test Accuracy: {test_accuracy:.3f}")
            print(f"   CV Score: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
            
            self.models[name] = model
        
        # Train league-specific models if we have enough data
        self.train_league_specific_models(processed_data)
    
    def train_league_specific_models(self, processed_data: list):
        """Train separate models for each league"""
        league_data = {}
        
        # Group data by league
        for item in processed_data:
            league = item['league']
            if league not in league_data:
                league_data[league] = []
            league_data[league].append(item)
        
        print(f"\n🎯 Training league-specific models...")
        
        for league, data in league_data.items():
            if len(data) < 50:  # Need minimum data
                print(f"⚠️  {league}: Only {len(data)} matches - using global model")
                continue
            
            try:
                X_league = np.array([item['features'] for item in data])
                y_league = np.array([item['outcome'] for item in data])
                
                # Check if we have all outcome classes
                unique_outcomes = np.unique(y_league)
                if len(unique_outcomes) < 2:
                    print(f"⚠️  {league}: Insufficient outcome variety - using global model")
                    continue
                
                X_league_scaled = self.scaler.transform(X_league)
                
                # Simple Random Forest for league-specific model
                league_model = RandomForestClassifier(
                    n_estimators=100,
                    random_state=42,
                    n_jobs=-1
                )
                
                league_model.fit(X_league_scaled, y_league)
                
                # Quick accuracy check
                accuracy = league_model.score(X_league_scaled, y_league)
                
                self.league_models[league] = league_model
                print(f"✅ {league}: {len(data)} matches, accuracy: {accuracy:.3f}")
                
            except Exception as e:
                print(f"❌ {league}: Training failed - {e}")
    
    def predict_match(self, home_odds: float, draw_odds: float, away_odds: float, 
                     league: str = None, additional_features: dict = None):
        """Make prediction with league-specific enhancements"""
        
        if not self.models:
            return {'error': 'Models not trained'}
        
        # Create feature vector (matching training structure)
        features = [
            # Basic odds
            home_odds, draw_odds, away_odds,
            1/home_odds, 1/draw_odds, 1/away_odds,
            
            # Default market odds
            2.0, 2.0, 1.5, 2.5,  # Over/under
            2.0, 2.0,             # BTTS
            1.0, 1.0,             # PPG
            2.5, 8.0, 50.0, 50.0, 10.0, 10.0,  # Match stats
            1,                    # League tier (default)
        ]
        
        # Add derived features
        features.extend([
            home_odds / away_odds,
            abs(home_odds - away_odds),
            min(home_odds, away_odds, draw_odds),
            max(home_odds, away_odds, draw_odds),
        ])
        
        # Scale features
        feature_array = np.array(features).reshape(1, -1)
        feature_scaled = self.scaler.transform(feature_array)
        
        predictions = {}
        outcome_labels = ['Away Win', 'Draw', 'Home Win']
        
        # Use league-specific model if available
        if league and league in self.league_models:
            league_model = self.league_models[league]
            pred_proba = league_model.predict_proba(feature_scaled)[0]
            predicted_class = league_model.predict(feature_scaled)[0]
            
            predictions['league_specific'] = {
                'prediction': outcome_labels[predicted_class],
                'probabilities': {
                    'away_win': pred_proba[0],
                    'draw': pred_proba[1],
                    'home_win': pred_proba[2]
                },
                'confidence': max(pred_proba),
                'model_type': f'{league} Specialist'
            }
        
        # Global models
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
                'confidence': max(pred_proba),
                'model_type': 'Global'
            }
        
        return predictions
    
    def analyze_value_bets(self, predictions: dict, home_odds: float, 
                          draw_odds: float, away_odds: float, min_edge: float = 0.05):
        """Enhanced value betting analysis"""
        analysis = {}
        
        for model_name, pred_data in predictions.items():
            probs = pred_data['probabilities']
            value_bets = []
            
            # Check each outcome
            outcomes = [
                ('Home Win', home_odds, probs['home_win']),
                ('Draw', draw_odds, probs['draw']),
                ('Away Win', away_odds, probs['away_win'])
            ]
            
            for outcome_name, odds, probability in outcomes:
                implied_prob = 1 / odds
                
                if probability > implied_prob + min_edge:
                    edge = (probability - implied_prob) / implied_prob
                    kelly = self.calculate_kelly(probability, odds)
                    
                    value_bets.append({
                        'outcome': outcome_name,
                        'odds': odds,
                        'model_probability': probability,
                        'implied_probability': implied_prob,
                        'edge': edge,
                        'kelly_fraction': kelly,
                        'confidence_level': self.get_confidence_level(edge, pred_data['confidence'])
                    })
            
            analysis[model_name] = {
                'prediction': pred_data['prediction'],
                'confidence': pred_data['confidence'],
                'model_type': pred_data.get('model_type', 'Unknown'),
                'value_bets': sorted(value_bets, key=lambda x: x['edge'], reverse=True)
            }
        
        return analysis
    
    def calculate_kelly(self, probability: float, odds: float) -> float:
        """Calculate Kelly Criterion"""
        if probability <= 1/odds:
            return 0.0
        
        b = odds - 1
        p = probability
        q = 1 - p
        
        kelly = (b * p - q) / b
        return max(0, min(kelly, 0.25))  # Cap at 25%
    
    def get_confidence_level(self, edge: float, model_confidence: float) -> str:
        """Determine confidence level for betting recommendation"""
        combined_score = (edge * 0.6) + (model_confidence * 0.4)
        
        if combined_score > 0.4:
            return "High"
        elif combined_score > 0.2:
            return "Medium"
        else:
            return "Low"
    
    def save_models(self, filepath: str):
        """Save all models"""
        model_data = {
            'global_models': self.models,
            'league_models': self.league_models,
            'scaler': self.scaler,
            'target_leagues': self.target_leagues
        }
        joblib.dump(model_data, filepath)
        print(f"💾 All models saved to {filepath}")
    
    def load_models(self, filepath: str) -> bool:
        """Load all models"""
        try:
            model_data = joblib.load(filepath)
            self.models = model_data.get('global_models', {})
            self.league_models = model_data.get('league_models', {})
            self.scaler = model_data.get('scaler', StandardScaler())
            print(f"✅ Models loaded from {filepath}")
            return True
        except:
            print(f"⚠️  No saved models found at {filepath}")
            return False


def main():
    """Main execution for multi-league predictor"""
    
    API_KEY = "ceb338b9bcb82a452efc114fb2d3cccac67f58be1569e7b5acf1d2195adeae11"
    MODEL_PATH = "./multi_league_models.pkl"
    
    print("🌍 Multi-League Soccer Betting Predictor")
    print("=" * 50)
    print("Targeting 28+ leagues across multiple continents")
    print("=" * 50)
    
    predictor = MultiLeaguePredictor(API_KEY)
    
    # Discover available leagues
    available_leagues = predictor.get_available_leagues()
    
    if not available_leagues:
        print("\n❌ No target leagues available with your API key")
        print("🔍 Let's discover what leagues are available...")
        found_leagues = predictor.discover_league_ids()
        
        if found_leagues:
            print("\n📋 Available leagues found:")
            for league_id, info in found_leagues.items():
                print(f"   ID {league_id}: {info['matches']} matches")
                print(f"      Sample: {info['sample_teams']['home']} vs {info['sample_teams']['away']}")
        
        return
    
    # Try loading existing models
    if not predictor.load_models(MODEL_PATH):
        print("\n🤖 Training new multi-league models...")
        
        # Collect training data
        training_data = predictor.collect_multi_league_data(available_leagues, matches_per_league=150)
        
        if training_data:
            # Train models
            predictor.train_multi_league_models(training_data)
            
            # Save models
            predictor.save_models(MODEL_PATH)
        else:
            print("❌ No training data collected")
            return
    
    # Example predictions
    print(f"\n🔮 Example Multi-League Predictions")
    print("=" * 45)
    
    test_matches = [
        {
            'name': 'Manchester City vs Liverpool',
            'league': 'Premier League',
            'home_odds': 2.1, 'draw_odds': 3.4, 'away_odds': 3.2
        },
        {
            'name': 'Real Madrid vs Barcelona',
            'league': 'La Liga',
            'home_odds': 2.3, 'draw_odds': 3.1, 'away_odds': 3.0
        },
        {
            'name': 'Bayern Munich vs Dortmund',
            'league': 'Bundesliga',
            'home_odds': 1.9, 'draw_odds': 3.5, 'away_odds': 4.1
        }
    ]
    
    for match in test_matches:
        print(f"\n🏆 {match['name']} ({match['league']})")
        print(f"📊 Odds: {match['home_odds']} / {match['draw_odds']} / {match['away_odds']}")
        
        # Get predictions
        predictions = predictor.predict_match(
            match['home_odds'], match['draw_odds'], match['away_odds'], 
            league=match['league']
        )
        
        # Analyze value
        value_analysis = predictor.analyze_value_bets(
            predictions, match['home_odds'], match['draw_odds'], match['away_odds']
        )
        
        # Show results
        for model_name, analysis in value_analysis.items():
            print(f"\n   🤖 {model_name.upper()} ({analysis['model_type']}):")
            print(f"      Prediction: {analysis['prediction']} (Confidence: {analysis['confidence']:.3f})")
            
            if analysis['value_bets']:
                print(f"      💰 Value Opportunities:")
                for bet in analysis['value_bets']:
                    print(f"         {bet['outcome']}: {bet['edge']:.1%} edge, Kelly: {bet['kelly_fraction']:.1%}")
                    print(f"            Confidence: {bet['confidence_level']}")
            else:
                print(f"      ❌ No value opportunities")
    
    print(f"\n" + "=" * 60)
    print("✅ Multi-league analysis complete!")
    print(f"📊 Leagues analyzed: {len(available_leagues)}")
    print(f"🤖 Models trained: Global + League-specific")
    print(f"💾 Models saved for future use")

if __name__ == "__main__":
    main()