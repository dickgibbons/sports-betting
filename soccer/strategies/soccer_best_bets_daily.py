#!/usr/bin/env python3
"""
Soccer Best Bets Daily - High Confidence Picks Only

Similar to Euro Hockey system:
- Strict confidence thresholds (75%+ for winners, 70%+ for totals)
- Bankroll management with Kelly Criterion
- Top leagues worldwide
- Reports saved to reports/YYYYMMDD/
"""

import os
import sys
import json
import requests
import numpy as np
import pandas as pd
import joblib
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Add utils directory to path
utils_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils')
strategies_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, utils_dir)
sys.path.insert(0, strategies_dir)

from team_form_fetcher import TeamFormFetcher

# ProphitBet Ensemble Integration
try:
    from prophitbet_ensemble import ProphitBetEnsemble
    PROPHITBET_AVAILABLE = True
except ImportError:
    PROPHITBET_AVAILABLE = False
    print("Note: ProphitBet ensemble not available. Run 'python prophitbet_ensemble.py --train' to enable.")

# Minimum confidence thresholds (CALIBRATED - post-isotonic calibration adjustment)
# After calibration, predictions are realistic (65-83% range)
# Volume control via top-N selection (not threshold filtering)
MIN_CONFIDENCE = 0.60  # 60% for match winners (calibrated threshold)
MIN_TOTALS_CONFIDENCE = 0.65  # 65% for over/under (calibrated threshold)
MIN_BTTS_CONFIDENCE = 0.60  # 60% for BTTS (calibrated threshold)
MIN_CORNERS_CONFIDENCE = 0.70  # 70% for corners (calibrated threshold)
MIN_TEAM_TOTALS_CONFIDENCE = 0.65  # 65% for team totals O/U 1.5 (using borrowed calibration)

# TOP-N SELECTION (Volume Control)
# Weekdays: 5-7 bets | Weekends (Fri-Sun): 10-15 bets
WEEKDAY_MAX_BETS = 7
WEEKEND_MAX_BETS = 15

# OPTIMIZED CONFIGURATION (Based on 600-match backtest analysis - Nov 2025)
# ============================================================================
# PROFITABLE MARKETS (positive edge):
#   Over 1.5: +5.5% edge at 1.33 odds (80.7% hit rate)
#   Away Win: +4.9% edge at 3.50 odds (33.5% hit rate)
#   Over 2.5: +3.4% edge at 1.90 odds (56.0% hit rate)
# LOSING MARKETS (negative edge - AVOID):
#   BTTS No: -5.1% edge (only 43.7% hit rate globally)
#   Under 2.5: -7.3% edge
#   Home Win: -4.5% edge
# ============================================================================
# MATCH OUTCOME MARKETS (separate controls for each)
ENABLE_HOME_WIN = False        # DISABLED - -4.5% edge (43.2% hit rate)
ENABLE_DRAW = False            # DISABLED - -6.1% edge (23.3% hit rate)
ENABLE_AWAY_WIN = True         # ENABLE - +4.9% edge at 3.50 odds (33.5% hit rate)
ENABLE_MATCH_WINNERS = True    # Master switch for any match outcome bets

# TOTALS MARKETS
ENABLE_TOTALS = True           # ENABLE - Over 2.5 has +3.4% edge, Over 1.5 has +5.5%
ENABLE_OVER_35 = True          # ENABLE - Bundesliga Over 3.5 has +15.6% edge!

# BTTS MARKETS
ENABLE_BTTS_YES = True         # ENABLE - +0.7% edge globally, +6.9% in Ligue 1/Süper Lig
ENABLE_BTTS_NO = False         # DISABLED - -5.1% edge globally (except La Liga whitelist)

# OTHER MARKETS
ENABLE_TEAM_TOTALS = False     # DISABLED - No clear edge
ENABLE_CORNERS = False         # DISABLED - No models trained
ENABLE_H1_TOTALS = True        # ENABLED - Now with ProphitBet ensemble boost

# PROPHITBET ENSEMBLE INTEGRATION
# When enabled, predictions are combined with ProphitBet's XGBoost models
ENABLE_PROPHITBET_ENSEMBLE = True  # Enable ensemble combination
PROPHITBET_WEIGHT = 0.30           # Weight for ProphitBet predictions (0-1)
                                   # 0.30 = 30% ProphitBet, 70% existing models

# LEAGUE-SPECIFIC VALUE BETTING (Based on backtest)
# These combinations have proven positive edge:
LEAGUE_OVER25_WHITELIST = ['Bundesliga', 'MLS', 'Süper Lig', 'Ligue 1', 'Primeira Liga', 'Belgium Pro League']
LEAGUE_OVER35_WHITELIST = ['Bundesliga', 'Super League', 'Belgium Pro League']  # +15.6% edge in Bundesliga!
LEAGUE_HOME_WIN_WHITELIST = ['MLS', 'Super League', 'Ligue 1']  # +12.4% edge in MLS
LEAGUE_BTTS_YES_WHITELIST = ['Ligue 1', 'Süper Lig', 'Brazil Serie A']  # +6.9% edge
LEAGUE_BTTS_NO_WHITELIST = ['La Liga']  # ONLY league where BTTS No is profitable (+7.2% edge)
LEAGUE_UNDER25_WHITELIST = ['Premier League']  # +4.7% edge

# Global blacklist for markets that lose everywhere
LEAGUE_BLACKLIST = []  # No leagues blacklisted - use whitelists instead

# Kelly Criterion parameters
KELLY_FRACTION = 0.25  # Conservative quarter-Kelly
MAX_BET_SIZE = 0.05  # Maximum 5% of bankroll

# API Configuration - API-Sports (same as hockey system)
API_KEY = "960c628e1c91c4b1f125e1eec52ad862"
API_BASE = "https://v3.football.api-sports.io"


class SoccerBestBetsGenerator:
    """Generate high-confidence soccer betting recommendations"""

    def __init__(self, model_path: str = None):
        """Initialize with trained models"""
        if model_path is None:
            # Try form-enhanced models first, then standard enhanced, then fallback
            # Models are in soccer/models/ (parent directory)
            models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models')
            form_path = os.path.join(models_dir, 'soccer_ml_models_with_form.pkl')
            enhanced_path = os.path.join(models_dir, 'soccer_ml_models_enhanced.pkl')
            standard_path = os.path.join(models_dir, 'soccer_ml_models.pkl')

            if os.path.exists(form_path):
                model_path = form_path
                print("🚀 Using FORM-ENHANCED models (Phase 2)")
            elif os.path.exists(enhanced_path):
                model_path = enhanced_path
                print("🚀 Using ENHANCED models")
            else:
                model_path = standard_path
                print("⚠️  Using standard models")

        self.model_path = model_path
        self.models = None
        self.scaler = None
        self.feature_names = []

        # Load league database
        self.leagues = self.load_league_database()

        # Initialize team form fetcher for Phase 2 features
        self.form_fetcher = TeamFormFetcher(api_key=API_KEY)

        # Load models
        self.load_models()

        # Load calibration parameters
        self.calibration_params = self.load_calibration()

        # Initialize ProphitBet ensemble (if available and enabled)
        self.prophitbet_ensemble = None
        if ENABLE_PROPHITBET_ENSEMBLE and PROPHITBET_AVAILABLE:
            try:
                self.prophitbet_ensemble = ProphitBetEnsemble()
                if self.prophitbet_ensemble.load_models():
                    print(f"🔮 ProphitBet ensemble ENABLED (weight: {PROPHITBET_WEIGHT:.0%})")
                else:
                    print("⚠️  ProphitBet ensemble models not found. Run 'python prophitbet_ensemble.py --train'")
                    self.prophitbet_ensemble = None
            except Exception as e:
                print(f"⚠️  ProphitBet ensemble initialization failed: {e}")
                self.prophitbet_ensemble = None

    def load_calibration(self) -> dict:
        """Load calibration parameters for probability adjustments"""
        models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models')
        calibration_path = os.path.join(models_dir, 'calibration_params.pkl')

        if os.path.exists(calibration_path):
            try:
                calibration_data = joblib.load(calibration_path)
                print(f"✅ Calibration parameters loaded from {calibration_path}")
                print(f"   Calibration method: Isotonic Regression")
                return calibration_data
            except Exception as e:
                print(f"⚠️  Could not load calibration parameters: {e}")
                return None
        else:
            print(f"⚠️  Calibration file not found: {calibration_path}")
            print(f"   Using uncalibrated model predictions")
            return None

    def load_league_database(self) -> pd.DataFrame:
        """Load supported leagues database"""
        league_db_path = os.path.join(
            os.path.dirname(__file__),
            'output reports/Older/UPDATED_supported_leagues_database.csv'
        )

        if os.path.exists(league_db_path):
            df = pd.read_csv(league_db_path)
            # Filter to active leagues only
            return df[df['status'] == 'Active']
        else:
            print(f"⚠️  League database not found: {league_db_path}")
            # Use default top leagues
            return self.get_default_leagues()

    def get_default_leagues(self) -> pd.DataFrame:
        """Default top leagues if database not found"""
        default_leagues = {
            'league_name': ['Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1',
                          'Champions League', 'Europa League', 'MLS', 'Eredivisie', 'Primeira Liga'],
            'league_id': [39, 140, 135, 78, 61, 16, 3, 5000, 88, 94],
            'country': ['England', 'Spain', 'Italy', 'Germany', 'France',
                       'Europe', 'Europe', 'USA', 'Netherlands', 'Portugal'],
            'tier': [1, 1, 1, 1, 1, 0, 0, 1, 1, 1]
        }
        return pd.DataFrame(default_leagues)

    def load_models(self) -> bool:
        """Load trained ML models"""
        try:
            if not os.path.exists(self.model_path):
                print(f"❌ Model file not found: {self.model_path}")
                return False

            model_data = joblib.load(self.model_path)

            # Handle different model formats
            if isinstance(model_data, dict):
                # Expected format: {'models': {'match_outcome': model, 'over_2_5': model, 'btts': model, ...}}
                self.models = model_data.get('models', {})
                self.scaler = model_data.get('scaler')
                self.feature_names = model_data.get('feature_names', []) or model_data.get('feature_cols', [])

                if self.models:
                    print(f"✅ Models loaded from {self.model_path}")
                    print(f"   Available models: {list(self.models.keys())}")
                    return True
                else:
                    print(f"❌ No models found in model data")
                    return False
            else:
                self.models = model_data
                print(f"✅ Models loaded from {self.model_path}")
                return True

        except Exception as e:
            print(f"❌ Error loading models: {e}")
            import traceback
            traceback.print_exc()
            return False

    def fetch_upcoming_matches(self, date_str: str) -> List[Dict]:
        """Fetch upcoming matches from API-Sports for given date"""
        print(f"📊 Fetching matches for {date_str}...")

        all_matches = []
        today = datetime.now()

        # Get top tier leagues - include tier 2 for lower divisions (Boxing Day, etc.)
        top_leagues = self.leagues[self.leagues['tier'] <= 2]

        headers = {
            'x-apisports-key': API_KEY
        }

        for _, league in top_leagues.iterrows():
            league_id = league['league_id']

            try:
                # Determine season based on date
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                # Soccer seasons typically start in August
                # If month >= 8, use current year; otherwise use previous year
                if date_obj.month >= 8:
                    season = date_obj.year
                else:
                    season = date_obj.year - 1

                url = f"{API_BASE}/fixtures"
                params = {
                    'league': league_id,
                    'date': date_str,
                    'season': season
                }

                response = requests.get(url, params=params, headers=headers, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    fixtures = data.get('response', [])

                    future_matches = 0
                    for fixture in fixtures:
                        # Only include matches that haven't been played yet
                        fixture_data = fixture.get('fixture', {})
                        status = fixture_data.get('status', {}).get('short', '')

                        # Only future matches (NS = Not Started, TBD = To Be Defined)
                        if status in ['NS', 'TBD']:
                            fixture_id = fixture_data.get('id')

                            # Fetch odds for this fixture
                            odds_data = self.fetch_odds_for_fixture(fixture_id, headers)

                            # Convert API-Sports format to our format
                            match = {
                                'id': fixture_id,
                                'date': fixture_data.get('date'),
                                'home_name': fixture.get('teams', {}).get('home', {}).get('name', 'Unknown'),
                                'away_name': fixture.get('teams', {}).get('away', {}).get('name', 'Unknown'),
                                'home_team_id': fixture.get('teams', {}).get('home', {}).get('id'),  # For team form features
                                'away_team_id': fixture.get('teams', {}).get('away', {}).get('id'),  # For team form features
                                'league_name': league['league_name'],
                                'league_id': league_id,  # For team form features
                                'league_country': league['country'],
                                'league_tier': league['tier'],
                                'season': season,  # For team form features
                            }

                            # Add odds data
                            match.update(odds_data)

                            all_matches.append(match)
                            future_matches += 1

                    if future_matches > 0:
                        print(f"   ✅ {league['league_name']}: {future_matches} upcoming matches")

            except Exception as e:
                print(f"   ⚠️  Error fetching {league['league_name']}: {e}")
                continue

        print(f"📊 Total upcoming matches found: {len(all_matches)}")
        return all_matches

    def fetch_odds_for_fixture(self, fixture_id: int, headers: dict) -> dict:
        """Fetch odds for a specific fixture from API-Sports"""
        try:
            url = f"{API_BASE}/odds"
            params = {
                'fixture': fixture_id,
                'bookmaker': 2  # Bet365 (most reliable)
            }

            response = requests.get(url, params=params, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                odds_response = data.get('response', [])

                if odds_response and len(odds_response) > 0:
                    bookmaker_data = odds_response[0].get('bookmakers', [])

                    if bookmaker_data:
                        bets = bookmaker_data[0].get('bets', [])

                        # Initialize defaults
                        odds = {
                            'odds_ft_1': 2.0,
                            'odds_ft_x': 3.2,
                            'odds_ft_2': 3.5,
                            'over_25': 1.8,
                            'under_25': 1.9,
                            'btts_yes': 1.85,
                            'btts_no': 1.85,
                            'over_8_5_corners': 1.8,
                            'under_8_5_corners': 1.9,
                            'over_10_5_corners': 1.9,
                            'under_10_5_corners': 1.8
                        }

                        # Parse bets
                        for bet in bets:
                            bet_name = bet.get('name', '')
                            values = bet.get('values', [])

                            # Match Winner (Home/Draw/Away)
                            if bet_name == 'Match Winner':
                                for value in values:
                                    val_name = value.get('value', '')
                                    odd = float(value.get('odd', 0))
                                    if val_name == 'Home' and odd > 1.01:
                                        odds['odds_ft_1'] = odd
                                    elif val_name == 'Draw' and odd > 1.01:
                                        odds['odds_ft_x'] = odd
                                    elif val_name == 'Away' and odd > 1.01:
                                        odds['odds_ft_2'] = odd

                            # Over/Under 2.5 Goals
                            elif bet_name == 'Goals Over/Under' or bet_name == 'Over/Under':
                                for value in values:
                                    val_name = value.get('value', '')
                                    odd = float(value.get('odd', 0))
                                    if 'Over 2.5' in val_name and odd > 1.01:
                                        odds['over_25'] = odd
                                    elif 'Under 2.5' in val_name and odd > 1.01:
                                        odds['under_25'] = odd

                            # Both Teams Score
                            elif bet_name == 'Both Teams Score' or bet_name == 'BTTS':
                                for value in values:
                                    val_name = value.get('value', '')
                                    odd = float(value.get('odd', 0))
                                    if val_name == 'Yes' and odd > 1.01:
                                        odds['btts_yes'] = odd
                                    elif val_name == 'No' and odd > 1.01:
                                        odds['btts_no'] = odd

                            # Corners (if available)
                            elif 'Corner' in bet_name:
                                for value in values:
                                    val_name = value.get('value', '')
                                    odd = float(value.get('odd', 0))
                                    if 'Over 8.5' in val_name and odd > 1.01:
                                        odds['over_8_5_corners'] = odd
                                    elif 'Under 8.5' in val_name and odd > 1.01:
                                        odds['under_8_5_corners'] = odd
                                    elif 'Over 10.5' in val_name and odd > 1.01:
                                        odds['over_10_5_corners'] = odd
                                    elif 'Under 10.5' in val_name and odd > 1.01:
                                        odds['under_10_5_corners'] = odd

                        return odds

        except Exception as e:
            # If odds fetch fails, return defaults
            pass

        # Return default odds if API call fails
        return {
            'odds_ft_1': 2.0,
            'odds_ft_x': 3.2,
            'odds_ft_2': 3.5,
            'over_25': 1.8,
            'under_25': 1.9,
            'btts_yes': 1.85,
            'btts_no': 1.85,
            'over_8_5_corners': 1.8,
            'under_8_5_corners': 1.9,
            'over_10_5_corners': 1.9,
            'under_10_5_corners': 1.8
        }

    def create_features_from_odds(self, odds_data: dict) -> np.ndarray:
        """Create feature vector from odds for enhanced models"""
        home_odds = odds_data.get('home_odds', 2.0)
        draw_odds = odds_data.get('draw_odds', 3.2)
        away_odds = odds_data.get('away_odds', 3.5)
        over_25 = odds_data.get('over_25', 1.8)
        under_25 = odds_data.get('under_25', 1.9)
        btts_yes = odds_data.get('btts_yes', 1.8)
        btts_no = odds_data.get('btts_no', 1.9)

        # Implied probabilities
        home_prob = 1 / home_odds if home_odds > 0 else 0
        draw_prob = 1 / draw_odds if draw_odds > 0 else 0
        away_prob = 1 / away_odds if away_odds > 0 else 0

        # Normalize
        total_prob = home_prob + draw_prob + away_prob
        home_prob_norm = home_prob / total_prob if total_prob > 0 else 0
        draw_prob_norm = draw_prob / total_prob if total_prob > 0 else 0
        away_prob_norm = away_prob / total_prob if total_prob > 0 else 0

        expected_total = 2.5

        features = [
            home_odds, draw_odds, away_odds, over_25, under_25,
            btts_yes, btts_no, home_prob_norm, draw_prob_norm, away_prob_norm,
            expected_total, home_odds - away_odds,
            1 / (home_odds * away_odds) if (home_odds * away_odds) > 0 else 0
        ]

        return np.array([features])

    def create_features_with_form(self, odds_data: dict, home_form: dict, away_form: dict) -> np.ndarray:
        """Create 45-feature vector (13 odds + 32 form features)"""
        # First 13 odds features
        odds_features = self.create_features_from_odds(odds_data)[0]  # Extract from array

        # Home team form features (16)
        home_form_list = [
            home_form.get('wins_last_5', 0),
            home_form.get('draws_last_5', 0),
            home_form.get('losses_last_5', 0),
            home_form.get('points_last_5', 0),
            home_form.get('goals_for_last_5', 0),
            home_form.get('goals_against_last_5', 0),
            home_form.get('goal_diff_last_5', 0),
            home_form.get('btts_rate_last_5', 0.5),
            home_form.get('over_25_rate_last_5', 0.5),
            home_form.get('clean_sheets_last_5', 0),
            home_form.get('season_win_rate', 0.33),
            home_form.get('season_goals_per_game', 1.5),
            home_form.get('season_conceded_per_game', 1.5),
            home_form.get('season_clean_sheet_rate', 0.25),
            home_form.get('season_home_wins', 0),
            home_form.get('season_away_wins', 0),
        ]

        # Away team form features (16)
        away_form_list = [
            away_form.get('wins_last_5', 0),
            away_form.get('draws_last_5', 0),
            away_form.get('losses_last_5', 0),
            away_form.get('points_last_5', 0),
            away_form.get('goals_for_last_5', 0),
            away_form.get('goals_against_last_5', 0),
            away_form.get('goal_diff_last_5', 0),
            away_form.get('btts_rate_last_5', 0.5),
            away_form.get('over_25_rate_last_5', 0.5),
            away_form.get('clean_sheets_last_5', 0),
            away_form.get('season_win_rate', 0.33),
            away_form.get('season_goals_per_game', 1.5),
            away_form.get('season_conceded_per_game', 1.5),
            away_form.get('season_clean_sheet_rate', 0.25),
            away_form.get('season_home_wins', 0),
            away_form.get('season_away_wins', 0),
        ]

        # Combine all 45 features
        combined = list(odds_features) + home_form_list + away_form_list
        return np.array([combined])

    def extract_features(self, match: Dict) -> Optional[Dict]:
        """Extract features from match data matching existing model format"""
        try:
            # Get odds
            home_odds = float(match.get('odds_ft_1', 0))
            draw_odds = float(match.get('odds_ft_x', 0))
            away_odds = float(match.get('odds_ft_2', 0))

            # Validate odds
            if home_odds < 1.01 or draw_odds < 1.01 or away_odds < 1.01:
                return None

            # Totals market
            over_25 = float(match.get('over_25', 0))
            under_25 = float(match.get('under_25', 0))
            btts_yes = float(match.get('btts_yes', 0))
            btts_no = float(match.get('btts_no', 0))

            # Corners market (if available)
            over_85_corners = float(match.get('over_8_5_corners', 0))
            under_85_corners = float(match.get('under_8_5_corners', 0))
            over_105_corners = float(match.get('over_10_5_corners', 0))
            under_105_corners = float(match.get('under_10_5_corners', 0))

            # Validate totals odds
            if over_25 < 1.01:
                over_25 = 1.8  # Default
            if under_25 < 1.01:
                under_25 = 1.8
            if btts_yes < 1.01:
                btts_yes = 1.8
            if btts_no < 1.01:
                btts_no = 1.8

            # Validate corners odds (defaults if not available)
            if over_85_corners < 1.01:
                over_85_corners = 1.8
            if under_85_corners < 1.01:
                under_85_corners = 1.8
            if over_105_corners < 1.01:
                over_105_corners = 1.9
            if under_105_corners < 1.01:
                under_105_corners = 1.9

            # Match existing model's 6-feature format
            # Based on typical soccer models: home_odds, draw_odds, away_odds, over_25, btts_yes, avg_goals_estimate
            avg_goals_estimate = 2.5  # Default estimate
            avg_corners_estimate = 10.0  # Default corners estimate

            features = {
                'match_outcome': [home_odds, draw_odds, away_odds, over_25, btts_yes, avg_goals_estimate],
                'over_2_5': [home_odds, draw_odds, away_odds, over_25, under_25, btts_yes],
                'btts': [home_odds, draw_odds, away_odds, btts_yes, btts_no, over_25],
                'over_8_5_corners': [home_odds, draw_odds, away_odds, over_85_corners, under_85_corners, avg_corners_estimate],
                'over_10_5_corners': [home_odds, draw_odds, away_odds, over_105_corners, under_105_corners, avg_corners_estimate],
                'odds_data': {
                    'home_odds': home_odds,
                    'draw_odds': draw_odds,
                    'away_odds': away_odds,
                    'over_25': over_25,
                    'under_25': under_25,
                    'btts_yes': btts_yes,
                    'btts_no': btts_no,
                    'over_85_corners': over_85_corners,
                    'under_85_corners': under_85_corners,
                    'over_105_corners': over_105_corners,
                    'under_105_corners': under_105_corners
                }
            }

            # PHASE 2: Add team form features (if available)
            # Note: Current models don't use these yet - they'll be used after retraining
            if 'home_team_id' in match and 'away_team_id' in match and 'league_id' in match and 'season' in match:
                try:
                    # Fetch home team form features
                    home_form = self.form_fetcher.fetch_team_features(
                        match['home_team_id'],
                        match['league_id'],
                        match['season'],
                        num_games=5
                    )

                    # Fetch away team form features
                    away_form = self.form_fetcher.fetch_team_features(
                        match['away_team_id'],
                        match['league_id'],
                        match['season'],
                        num_games=5
                    )

                    # Store form data for future use (when models are retrained)
                    features['home_form'] = home_form
                    features['away_form'] = away_form

                except Exception as e:
                    # If form fetch fails, continue without form features
                    # This ensures backwards compatibility with existing models
                    print(f"   ⚠️  Could not fetch team form (will use odds only): {e}")
                    features['home_form'] = None
                    features['away_form'] = None

            return features

        except Exception as e:
            print(f"   ⚠️  Feature extraction error: {e}")
            return None

    def _get_prophitbet_predictions(self, odds: Dict) -> Optional[Dict]:
        """Get predictions from ProphitBet ensemble if available."""
        if self.prophitbet_ensemble is None:
            return None

        try:
            odds_data = {
                'home_odds': odds.get('home_odds', 2.0),
                'draw_odds': odds.get('draw_odds', 3.2),
                'away_odds': odds.get('away_odds', 3.5),
                'over_25': odds.get('over_25', 1.8),
                'under_25': odds.get('under_25', 1.9),
                'btts_yes': odds.get('btts_yes', 1.85),
                'btts_no': odds.get('btts_no', 1.85)
            }
            return self.prophitbet_ensemble.predict_from_odds(odds_data)
        except Exception as e:
            # Silently fail - don't disrupt main predictions
            return None

    def _combine_with_prophitbet(self, base_prob: float, pb_prob: float, weight: float = PROPHITBET_WEIGHT) -> float:
        """Combine base model probability with ProphitBet prediction."""
        if pb_prob is None or pb_prob == 0:
            return base_prob
        return (1 - weight) * base_prob + weight * pb_prob

    def predict_match(self, match: Dict) -> Optional[Dict]:
        """Predict match outcome with confidence"""
        if self.models is None:
            return None

        # LEAGUE BLACKLIST - Skip matches in consistently unprofitable leagues
        league_name = match.get('league_name', '')
        if league_name in LEAGUE_BLACKLIST:
            return None  # Skip this league completely

        feature_dict = self.extract_features(match)
        if feature_dict is None:
            return None

        try:
            odds = feature_dict['odds_data']
            predictions = []

            # Get ProphitBet ensemble predictions (if available)
            pb_preds = self._get_prophitbet_predictions(odds)

            # Check if form features are available
            has_form_features = (feature_dict.get('home_form') is not None and
                               feature_dict.get('away_form') is not None)

            # Create feature vector (with or without form)
            if has_form_features:
                # Use 45-feature vector (13 odds + 32 form)
                match_features = self.create_features_with_form(
                    odds,
                    feature_dict['home_form'],
                    feature_dict['away_form']
                )
            else:
                # Use 13-feature vector (odds only)
                match_features = self.create_features_from_odds(odds)

            # Scale features
            if self.scaler is not None:
                match_features_scaled = self.scaler.transform(match_features)
            else:
                match_features_scaled = match_features

            # Match Outcome (Home/Draw/Away)
            # Handle both old format ('match_outcome') and new format ('rf_match_outcome', 'gb_match_outcome')
            if 'match_outcome' in self.models:
                match_probs = self.models['match_outcome'].predict_proba(match_features_scaled)[0]
            elif 'rf_match_outcome' in self.models and 'gb_match_outcome' in self.models:
                # Enhanced models - ensemble RF and GB
                rf_probs = self.models['rf_match_outcome'].predict_proba(match_features_scaled)[0]
                gb_probs = self.models['gb_match_outcome'].predict_proba(match_features_scaled)[0]
                match_probs = (rf_probs + gb_probs) / 2  # Ensemble average
            else:
                match_probs = None

            if match_probs is not None:

                # Probabilities for [Away, Draw, Home] or similar
                # Need to check model output format
                if len(match_probs) == 3:
                    # Assume [Away, Draw, Home]
                    away_prob = match_probs[0]
                    draw_prob = match_probs[1]
                    home_prob = match_probs[2]

                    # Apply calibration
                    home_prob = self.apply_calibration(home_prob, 'Home Win')
                    # Note: Currently only have calibration for Home Win, Under 2.5, and BTTS No
                    # Draw and Away predictions will use uncalibrated probabilities

                    # Combine with ProphitBet ensemble predictions (if available)
                    if pb_preds and 'match_outcome' in pb_preds:
                        pb_mo = pb_preds['match_outcome']
                        home_prob = self._combine_with_prophitbet(home_prob, pb_mo.get('home_prob', 0))
                        draw_prob = self._combine_with_prophitbet(draw_prob, pb_mo.get('draw_prob', 0))
                        away_prob = self._combine_with_prophitbet(away_prob, pb_mo.get('away_prob', 0))

                    # Home win
                    if ENABLE_HOME_WIN and home_prob >= MIN_CONFIDENCE:
                        kelly = self.calculate_kelly(home_prob, odds['home_odds'])
                        if kelly > 0:
                            predictions.append({
                                'market': 'Home Win',
                                'selection': match.get('home_name', 'Home'),
                                'odds': odds['home_odds'],
                                'confidence': home_prob,
                                'kelly_stake': kelly,
                                'market_type': 'winner'
                            })

                    # Draw
                    if ENABLE_DRAW and draw_prob >= MIN_CONFIDENCE:
                        kelly = self.calculate_kelly(draw_prob, odds['draw_odds'])
                        if kelly > 0:
                            predictions.append({
                                'market': 'Draw',
                                'selection': 'Draw',
                                'odds': odds['draw_odds'],
                                'confidence': draw_prob,
                                'kelly_stake': kelly,
                                'market_type': 'winner'
                            })

                    # Away win
                    if ENABLE_AWAY_WIN and away_prob >= MIN_CONFIDENCE:
                        kelly = self.calculate_kelly(away_prob, odds['away_odds'])
                        if kelly > 0:
                            predictions.append({
                                'market': 'Away Win',
                                'selection': match.get('away_name', 'Away'),
                                'odds': odds['away_odds'],
                                'confidence': away_prob,
                                'kelly_stake': kelly,
                                'market_type': 'winner'
                            })

            # Over/Under 2.5
            if 'over_2_5' in self.models:
                ou_probs = self.models['over_2_5'].predict_proba(match_features_scaled)[0]
            elif 'rf_over_2_5' in self.models and 'gb_over_2_5' in self.models:
                # Enhanced models - use same feature vector as match_outcome
                rf_probs = self.models['rf_over_2_5'].predict_proba(match_features_scaled)[0]
                gb_probs = self.models['gb_over_2_5'].predict_proba(match_features_scaled)[0]
                ou_probs = (rf_probs + gb_probs) / 2
            else:
                ou_probs = None

            if ou_probs is not None:

                # Assume [Under, Over]
                if len(ou_probs) == 2:
                    under_prob = ou_probs[0]
                    over_prob = ou_probs[1]

                    # Apply calibration
                    under_prob = self.apply_calibration(under_prob, 'Under 2.5')

                    # Combine with ProphitBet ensemble predictions (if available)
                    if pb_preds and 'over_2_5' in pb_preds:
                        pb_ou = pb_preds['over_2_5']
                        over_prob = self._combine_with_prophitbet(over_prob, pb_ou.get('over_prob', 0))
                        under_prob = self._combine_with_prophitbet(under_prob, pb_ou.get('under_prob', 0))

                    if ENABLE_TOTALS and over_prob >= MIN_TOTALS_CONFIDENCE:
                        kelly = self.calculate_kelly(over_prob, odds['over_25'])
                        if kelly > 0:
                            predictions.append({
                                'market': 'Over 2.5',
                                'selection': 'Over 2.5 Goals',
                                'odds': odds['over_25'],
                                'confidence': over_prob,
                                'kelly_stake': kelly,
                                'market_type': 'totals'
                            })

                    if ENABLE_TOTALS and under_prob >= MIN_TOTALS_CONFIDENCE:
                        kelly = self.calculate_kelly(under_prob, odds['under_25'])
                        if kelly > 0:
                            predictions.append({
                                'market': 'Under 2.5',
                                'selection': 'Under 2.5 Goals',
                                'odds': odds['under_25'],
                                'confidence': under_prob,
                                'kelly_stake': kelly,
                                'market_type': 'totals'
                            })

            # BTTS (Both Teams To Score)
            if 'btts' in self.models:
                btts_probs = self.models['btts'].predict_proba(match_features_scaled)[0]
            elif 'rf_btts' in self.models and 'gb_btts' in self.models:
                # Enhanced models - use same feature vector as match_outcome
                rf_probs = self.models['rf_btts'].predict_proba(match_features_scaled)[0]
                gb_probs = self.models['gb_btts'].predict_proba(match_features_scaled)[0]
                btts_probs = (rf_probs + gb_probs) / 2
            else:
                btts_probs = None

            if btts_probs is not None:

                # Assume [No, Yes]
                if len(btts_probs) == 2:
                    btts_no_prob = btts_probs[0]
                    btts_yes_prob = btts_probs[1]

                    # Apply calibration
                    btts_no_prob = self.apply_calibration(btts_no_prob, 'BTTS No')

                    # Combine with ProphitBet ensemble predictions (if available)
                    if pb_preds and 'btts' in pb_preds:
                        pb_btts = pb_preds['btts']
                        btts_yes_prob = self._combine_with_prophitbet(btts_yes_prob, pb_btts.get('yes_prob', 0))
                        btts_no_prob = self._combine_with_prophitbet(btts_no_prob, pb_btts.get('no_prob', 0))

                    if ENABLE_BTTS_YES and btts_yes_prob >= MIN_BTTS_CONFIDENCE:
                        # BTTS Yes whitelist - only bet if whitelist empty or league in whitelist
                        if not LEAGUE_BTTS_YES_WHITELIST or league_name in LEAGUE_BTTS_YES_WHITELIST:
                            kelly = self.calculate_kelly(btts_yes_prob, odds['btts_yes'])
                            if kelly > 0:
                                predictions.append({
                                    'market': 'BTTS Yes',
                                    'selection': 'Both Teams Score',
                                    'odds': odds['btts_yes'],
                                    'confidence': btts_yes_prob,
                                    'kelly_stake': kelly,
                                    'market_type': 'btts'
                                })

                    if ENABLE_BTTS_NO and btts_no_prob >= MIN_BTTS_CONFIDENCE:
                        kelly = self.calculate_kelly(btts_no_prob, odds['btts_no'])
                        if kelly > 0:
                            predictions.append({
                                'market': 'BTTS No',
                                'selection': 'Not Both Teams Score',
                                'odds': odds['btts_no'],
                                'confidence': btts_no_prob,
                                'kelly_stake': kelly,
                                'market_type': 'btts'
                            })

            # Team Totals - Home Team O/U 1.5
            if ENABLE_TEAM_TOTALS and 'rf_home_over_1_5' in self.models and 'gb_home_over_1_5' in self.models:
                rf_home_probs = self.models['rf_home_over_1_5'].predict_proba(match_features_scaled)[0]
                gb_home_probs = self.models['gb_home_over_1_5'].predict_proba(match_features_scaled)[0]
                home_total_probs = (rf_home_probs + gb_home_probs) / 2

                if len(home_total_probs) == 2:
                    home_under_15_prob = home_total_probs[0]
                    home_over_15_prob = home_total_probs[1]

                    # Apply "Home Win" calibration to home team totals (borrowed)
                    home_over_15_prob = self.apply_calibration(home_over_15_prob, 'Home Win')
                    home_under_15_prob = self.apply_calibration(home_under_15_prob, 'Home Win')

                    # Default odds for team totals O/U 1.5 (typical range 1.6-2.2)
                    home_over_15_odds = 1.80
                    home_under_15_odds = 1.90

                    if home_over_15_prob >= MIN_TEAM_TOTALS_CONFIDENCE:
                        kelly = self.calculate_kelly(home_over_15_prob, home_over_15_odds)
                        if kelly > 0:
                            predictions.append({
                                'market': f'{match.get("home_name", "Home")} Over 1.5',
                                'selection': f'{match.get("home_name", "Home")} Over 1.5 Goals',
                                'odds': home_over_15_odds,
                                'confidence': home_over_15_prob,
                                'kelly_stake': kelly,
                                'market_type': 'team_totals'
                            })

                    if home_under_15_prob >= MIN_TEAM_TOTALS_CONFIDENCE:
                        kelly = self.calculate_kelly(home_under_15_prob, home_under_15_odds)
                        if kelly > 0:
                            predictions.append({
                                'market': f'{match.get("home_name", "Home")} Under 1.5',
                                'selection': f'{match.get("home_name", "Home")} Under 1.5 Goals',
                                'odds': home_under_15_odds,
                                'confidence': home_under_15_prob,
                                'kelly_stake': kelly,
                                'market_type': 'team_totals'
                            })

            # Team Totals - Away Team O/U 1.5
            if ENABLE_TEAM_TOTALS and 'rf_away_over_1_5' in self.models and 'gb_away_over_1_5' in self.models:
                rf_away_probs = self.models['rf_away_over_1_5'].predict_proba(match_features_scaled)[0]
                gb_away_probs = self.models['gb_away_over_1_5'].predict_proba(match_features_scaled)[0]
                away_total_probs = (rf_away_probs + gb_away_probs) / 2

                if len(away_total_probs) == 2:
                    away_under_15_prob = away_total_probs[0]
                    away_over_15_prob = away_total_probs[1]

                    # Apply "Home Win" calibration to away team totals (borrowed - conservative)
                    away_over_15_prob = self.apply_calibration(away_over_15_prob, 'Home Win')
                    away_under_15_prob = self.apply_calibration(away_under_15_prob, 'Home Win')

                    # Default odds for team totals O/U 1.5
                    away_over_15_odds = 1.80
                    away_under_15_odds = 1.90

                    if away_over_15_prob >= MIN_TEAM_TOTALS_CONFIDENCE:
                        kelly = self.calculate_kelly(away_over_15_prob, away_over_15_odds)
                        if kelly > 0:
                            predictions.append({
                                'market': f'{match.get("away_name", "Away")} Over 1.5',
                                'selection': f'{match.get("away_name", "Away")} Over 1.5 Goals',
                                'odds': away_over_15_odds,
                                'confidence': away_over_15_prob,
                                'kelly_stake': kelly,
                                'market_type': 'team_totals'
                            })

                    if away_under_15_prob >= MIN_TEAM_TOTALS_CONFIDENCE:
                        kelly = self.calculate_kelly(away_under_15_prob, away_under_15_odds)
                        if kelly > 0:
                            predictions.append({
                                'market': f'{match.get("away_name", "Away")} Under 1.5',
                                'selection': f'{match.get("away_name", "Away")} Under 1.5 Goals',
                                'odds': away_under_15_odds,
                                'confidence': away_under_15_prob,
                                'kelly_stake': kelly,
                                'market_type': 'team_totals'
                            })

            # Corners Over 8.5
            if 'over_8_5_corners' in self.models:
                corners_85_features = np.array([feature_dict['over_8_5_corners']])
                corners_85_probs = self.models['over_8_5_corners'].predict_proba(corners_85_features)[0]

                # Assume [Under, Over]
                if len(corners_85_probs) == 2:
                    under_85_prob = corners_85_probs[0]
                    over_85_prob = corners_85_probs[1]

                    if ENABLE_CORNERS and over_85_prob >= MIN_CORNERS_CONFIDENCE:
                        kelly = self.calculate_kelly(over_85_prob, odds['over_85_corners'])
                        if kelly > 0:
                            predictions.append({
                                'market': 'Over 8.5 Corners',
                                'selection': 'Over 8.5 Corners',
                                'odds': odds['over_85_corners'],
                                'confidence': over_85_prob,
                                'kelly_stake': kelly,
                                'market_type': 'corners'
                            })

                    if ENABLE_CORNERS and under_85_prob >= MIN_CORNERS_CONFIDENCE:
                        kelly = self.calculate_kelly(under_85_prob, odds['under_85_corners'])
                        if kelly > 0:
                            predictions.append({
                                'market': 'Under 8.5 Corners',
                                'selection': 'Under 8.5 Corners',
                                'odds': odds['under_85_corners'],
                                'confidence': under_85_prob,
                                'kelly_stake': kelly,
                                'market_type': 'corners'
                            })

            # Corners Over 10.5
            if 'over_10_5_corners' in self.models:
                corners_105_features = np.array([feature_dict['over_10_5_corners']])
                corners_105_probs = self.models['over_10_5_corners'].predict_proba(corners_105_features)[0]

                # Assume [Under, Over]
                if len(corners_105_probs) == 2:
                    under_105_prob = corners_105_probs[0]
                    over_105_prob = corners_105_probs[1]

                    if ENABLE_CORNERS and over_105_prob >= MIN_CORNERS_CONFIDENCE:
                        kelly = self.calculate_kelly(over_105_prob, odds['over_105_corners'])
                        if kelly > 0:
                            predictions.append({
                                'market': 'Over 10.5 Corners',
                                'selection': 'Over 10.5 Corners',
                                'odds': odds['over_105_corners'],
                                'confidence': over_105_prob,
                                'kelly_stake': kelly,
                                'market_type': 'corners'
                            })

                    if ENABLE_CORNERS and under_105_prob >= MIN_CORNERS_CONFIDENCE:
                        kelly = self.calculate_kelly(under_105_prob, odds['under_105_corners'])
                        if kelly > 0:
                            predictions.append({
                                'market': 'Under 10.5 Corners',
                                'selection': 'Under 10.5 Corners',
                                'odds': odds['under_105_corners'],
                                'confidence': under_105_prob,
                                'kelly_stake': kelly,
                                'market_type': 'corners'
                            })

            # First Half (H1) Predictions - use trained models if available
            # Soccer stats: ~45% of goals in H1, avg 1.2 goals per H1

            # H1 Game Total O/U 0.5 (will there be at least 1 goal in H1?)
            if ENABLE_H1_TOTALS and 'rf_h1_over_0_5' in self.models and 'gb_h1_over_0_5' in self.models:
                # Use the already-scaled features from main prediction
                rf_h1_05_probs = self.models['rf_h1_over_0_5'].predict_proba(match_features_scaled)[0]
                gb_h1_05_probs = self.models['gb_h1_over_0_5'].predict_proba(match_features_scaled)[0]
                h1_05_probs = (rf_h1_05_probs + gb_h1_05_probs) / 2

                if len(h1_05_probs) == 2:
                    h1_under_05_prob = h1_05_probs[0]
                    h1_over_05_prob = h1_05_probs[1]

                    # Combine with ProphitBet ensemble predictions (if available)
                    if pb_preds and 'h1_over_0_5' in pb_preds:
                        pb_h1 = pb_preds['h1_over_0_5']
                        h1_over_05_prob = self._combine_with_prophitbet(h1_over_05_prob, pb_h1.get('over_prob', 0))
                        h1_under_05_prob = self._combine_with_prophitbet(h1_under_05_prob, pb_h1.get('under_prob', 0))

                    if h1_over_05_prob >= MIN_TOTALS_CONFIDENCE:
                        h1_05_odds = 1.75
                        kelly = self.calculate_kelly(h1_over_05_prob, h1_05_odds)
                        if kelly > 0:
                            predictions.append({
                                'market': 'H1 Over 0.5',
                                'selection': 'H1 Over 0.5 Goals',
                                'odds': h1_05_odds,
                                'confidence': h1_over_05_prob,
                                'kelly_stake': kelly,
                                'market_type': 'h1_totals'
                            })

                    if h1_under_05_prob >= MIN_TOTALS_CONFIDENCE:
                        h1_under_05_odds = 2.00
                        kelly = self.calculate_kelly(h1_under_05_prob, h1_under_05_odds)
                        if kelly > 0:
                            predictions.append({
                                'market': 'H1 Under 0.5',
                                'selection': 'H1 Under 0.5 Goals',
                                'odds': h1_under_05_odds,
                                'confidence': h1_under_05_prob,
                                'kelly_stake': kelly,
                                'market_type': 'h1_totals'
                            })

            # H1 Game Total O/U 1.5 (will there be 2+ goals in H1?)
            if ENABLE_H1_TOTALS and 'rf_h1_over_1_5' in self.models and 'gb_h1_over_1_5' in self.models:
                # Use the already-scaled features from main prediction
                rf_h1_15_probs = self.models['rf_h1_over_1_5'].predict_proba(match_features_scaled)[0]
                gb_h1_15_probs = self.models['gb_h1_over_1_5'].predict_proba(match_features_scaled)[0]
                h1_15_probs = (rf_h1_15_probs + gb_h1_15_probs) / 2

                if len(h1_15_probs) == 2:
                    h1_under_15_prob = h1_15_probs[0]
                    h1_over_15_prob = h1_15_probs[1]

                    # Combine with ProphitBet ensemble predictions (if available)
                    if pb_preds and 'h1_over_1_5' in pb_preds:
                        pb_h1 = pb_preds['h1_over_1_5']
                        h1_over_15_prob = self._combine_with_prophitbet(h1_over_15_prob, pb_h1.get('over_prob', 0))
                        h1_under_15_prob = self._combine_with_prophitbet(h1_under_15_prob, pb_h1.get('under_prob', 0))

                    if h1_over_15_prob >= MIN_TOTALS_CONFIDENCE:
                        h1_15_odds = 1.85
                        kelly = self.calculate_kelly(h1_over_15_prob, h1_15_odds)
                        if kelly > 0:
                            predictions.append({
                                'market': 'H1 Over 1.5',
                                'selection': 'H1 Over 1.5 Goals',
                                'odds': h1_15_odds,
                                'confidence': h1_over_15_prob,
                                'kelly_stake': kelly,
                                'market_type': 'h1_totals'
                            })

                    if h1_under_15_prob >= MIN_TOTALS_CONFIDENCE:
                        h1_under_15_odds = 1.90
                        kelly = self.calculate_kelly(h1_under_15_prob, h1_under_15_odds)
                        if kelly > 0:
                            predictions.append({
                                'market': 'H1 Under 1.5',
                                'selection': 'H1 Under 1.5 Goals',
                                'odds': h1_under_15_odds,
                                'confidence': h1_under_15_prob,
                                'kelly_stake': kelly,
                                'market_type': 'h1_totals'
                            })

            if predictions:
                return {
                    'match': match,
                    'predictions': predictions
                }

            return None

        except Exception as e:
            print(f"   ⚠️  Prediction error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def apply_calibration(self, probability: float, market: str, method: str = 'isotonic') -> float:
        """
        Apply calibration to model probability using saved calibration parameters

        Args:
            probability: Raw model probability (0-1)
            market: Market type ('Home Win', 'Under 2.5', 'BTTS No', etc.)
            method: 'isotonic' or 'platt' (default: isotonic)

        Returns:
            Calibrated probability (0-1)
        """
        if self.calibration_params is None:
            return probability  # No calibration available, return raw probability

        try:
            if method == 'isotonic':
                if market in self.calibration_params.get('isotonic', {}):
                    iso_model = self.calibration_params['isotonic'][market]
                    calibrated = iso_model.predict([probability])[0]
                    return float(calibrated)
            elif method == 'platt':
                if market in self.calibration_params.get('platt_scaling', {}):
                    params = self.calibration_params['platt_scaling'][market]
                    a = params['a']
                    b = params['b']

                    # Clip probability to avoid log(0) or log(1)
                    prob_clipped = np.clip(probability, 0.001, 0.999)
                    logit = np.log(prob_clipped / (1 - prob_clipped))
                    calibrated = 1 / (1 + np.exp(a * logit + b))
                    return float(calibrated)

            # If no calibration found for this market, return original
            return probability

        except Exception as e:
            print(f"⚠️  Calibration error for {market}: {e}")
            return probability

    def calculate_kelly(self, win_prob: float, odds: float) -> float:
        """Calculate Kelly Criterion stake (conservative)"""
        if odds <= 1.0 or win_prob <= 0:
            return 0.0

        # Kelly formula: (bp - q) / b
        # b = odds - 1 (net odds)
        # p = win probability
        # q = 1 - p (lose probability)

        b = odds - 1
        p = win_prob
        q = 1 - p

        kelly_full = (b * p - q) / b

        # Apply conservative fraction
        kelly_conservative = kelly_full * KELLY_FRACTION

        # Cap at maximum
        kelly_final = min(kelly_conservative, MAX_BET_SIZE)

        # Only recommend if >= 1% of bankroll
        if kelly_final >= 0.01:
            return round(kelly_final, 4)

        return 0.0

    def generate_daily_report(self, date_str: str) -> pd.DataFrame:
        """Generate best bets report for given date"""
        print(f"\n{'='*80}")
        print(f"⚽ SOCCER BEST BETS - {date_str}")
        print(f"{'='*80}\n")

        # Fetch matches
        matches = self.fetch_upcoming_matches(date_str)

        if not matches:
            print("⚠️  No matches found for this date")
            return pd.DataFrame()

        # Generate predictions
        all_bets = []

        for match in matches:
            result = self.predict_match(match)

            if result and result['predictions']:
                match_data = result['match']

                # Parse date/time
                match_timestamp = match_data.get('date')
                if match_timestamp:
                    try:
                        dt = datetime.fromisoformat(match_timestamp.replace('Z', '+00:00'))
                        game_date = dt.strftime('%Y-%m-%d')
                        game_time = dt.strftime('%H:%M')
                    except:
                        game_date = date_str
                        game_time = 'TBD'
                else:
                    game_date = date_str
                    game_time = 'TBD'

                for pred in result['predictions']:
                    all_bets.append({
                        'country': match_data.get('league_country', ''),
                        'league': match_data.get('league_name', ''),
                        'date': game_date,
                        'time': game_time,
                        'home_team': match_data.get('home_name', 'Unknown'),
                        'away_team': match_data.get('away_name', 'Unknown'),
                        'market': pred['market'],
                        'selection': pred['selection'],
                        'odds': pred['odds'],
                        'confidence': pred['confidence'],
                        'kelly_stake': pred['kelly_stake'],
                        'expected_value': (pred['confidence'] * pred['odds']) - 1
                    })

        if not all_bets:
            print("⚠️  No high-confidence bets found")
            return pd.DataFrame()

        # Create DataFrame
        df = pd.DataFrame(all_bets)

        # QUALITY FILTERS - Weekday: 5-7 bets | Weekend: 10-15 bets
        # Determine if today is weekend (Friday-Sunday)
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        is_weekend = date_obj.weekday() >= 4  # Friday=4, Saturday=5, Sunday=6
        max_bets = WEEKEND_MAX_BETS if is_weekend else WEEKDAY_MAX_BETS

        day_name = date_obj.strftime('%A')
        print(f"\n📅 {day_name} ({'Weekend' if is_weekend else 'Weekday'}) - Target: {max_bets} bets max")

        # 1. Filter out low odds (< 1.50) - not enough value
        df = df[df['odds'] >= 1.50].copy()
        print(f"📊 After odds filter (>=1.50): {len(df)} bets")

        # 2. Keep only BEST bet per match (highest EV)
        df['match_key'] = df['home_team'] + ' vs ' + df['away_team']
        df = df.sort_values('expected_value', ascending=False).groupby('match_key').first().reset_index()
        print(f"📊 After one-bet-per-match filter: {len(df)} bets")

        # 3. Take top N by expected value (weekday vs weekend)
        df = df.sort_values('expected_value', ascending=False).head(max_bets)
        df = df.drop(columns=['match_key'])  # Remove helper column
        print(f"📊 Final selection (top {max_bets} by EV): {len(df)} bets")

        print(f"\n✅ Found {len(df)} best betting opportunities")
        print(f"📊 Average confidence: {df['confidence'].mean():.1%}")
        print(f"📊 Average odds: {df['odds'].mean():.2f}")
        print(f"💰 Total recommended stake: {df['kelly_stake'].sum():.1%} of bankroll")

        return df

    def save_reports(self, df: pd.DataFrame, date_str: str):
        """Save reports to reports/YYYYMMDD/ directory"""
        if df.empty:
            print("\n⚠️  No data to save")
            return

        # Create reports directory
        date_folder = date_str.replace('-', '')  # 2025-10-16 -> 20251016
        reports_dir = os.path.join('reports', date_folder)
        os.makedirs(reports_dir, exist_ok=True)

        # Main best bets file
        best_bets_file = os.path.join(reports_dir, f'soccer_best_bets_{date_str}.csv')
        df.to_csv(best_bets_file, index=False)
        print(f"\n✅ Best bets saved: {best_bets_file}")

        # Top 5 best bets
        top5_df = df.head(5).copy()
        top5_file = os.path.join(reports_dir, f'soccer_top5_best_bets_{date_str}.csv')
        top5_df.to_csv(top5_file, index=False)
        print(f"✅ Top 5 saved: {top5_file}")

        # Cumulative summary - append to historical data
        # First, try to load existing cumulative data from previous reports
        cumulative_df = None

        # Look for the most recent cumulative file in parent reports directory
        reports_parent = os.path.join('reports')
        if os.path.exists(reports_parent):
            # Get all date folders sorted (most recent first)
            date_folders = sorted([d for d in os.listdir(reports_parent)
                                 if os.path.isdir(os.path.join(reports_parent, d)) and d.isdigit()],
                                reverse=True)

            # Look for existing cumulative file (skip current date folder)
            for folder in date_folders:
                if folder == date_folder:  # Skip current date
                    continue

                potential_file = os.path.join(reports_parent, folder,
                                            f'soccer_cumulative_summary_{folder[:4]}-{folder[4:6]}-{folder[6:]}.csv')
                if os.path.exists(potential_file):
                    try:
                        cumulative_df = pd.read_csv(potential_file)
                        print(f"📊 Loaded previous cumulative data from {folder}")
                        break
                    except Exception as e:
                        print(f"⚠️  Could not load {potential_file}: {e}")
                        continue

        # Create today's summary row
        summary_data = {
            'date': [date_str],
            'total_bets': [len(df)],
            'avg_confidence': [df['confidence'].mean()],
            'avg_odds': [df['odds'].mean()],
            'total_stake_pct': [df['kelly_stake'].sum()],
            'top_league': [df['league'].value_counts().index[0] if not df.empty else 'N/A'],
            'match_winners': [len(df[df['market'].str.contains('Win|Draw') & ~df['market'].str.contains('H1')])],
            'totals_bets': [len(df[df['market'].str.contains('Over|Under') & ~df['market'].str.contains('Corner') & ~df['market'].str.contains('H1')])],
            'btts_bets': [len(df[df['market'].str.contains('BTTS')])],
            'corners_bets': [len(df[df['market'].str.contains('Corner')])],
            'h1_totals_bets': [len(df[df['market'].str.contains('H1')])]
        }
        today_summary = pd.DataFrame(summary_data)

        # Append to cumulative data
        if cumulative_df is not None:
            summary_df = pd.concat([cumulative_df, today_summary], ignore_index=True)
            print(f"✅ Appended to cumulative history ({len(cumulative_df)} previous days)")
        else:
            summary_df = today_summary
            print(f"📊 Starting new cumulative history")

        # Save cumulative file
        summary_file = os.path.join(reports_dir, f'soccer_cumulative_summary_{date_str}.csv')
        summary_df.to_csv(summary_file, index=False)
        print(f"✅ Cumulative summary saved: {summary_file} ({len(summary_df)} total days)")

        # Print summary
        print(f"\n{'='*80}")
        print(f"📊 DAILY SUMMARY")
        print(f"{'='*80}")
        print(f"Total Best Bets: {len(df)}")
        print(f"Average Confidence: {df['confidence'].mean():.1%}")
        print(f"Average Odds: {df['odds'].mean():.2f}")
        print(f"Total Recommended Stake: {df['kelly_stake'].sum():.1%} of bankroll")
        print(f"\nBet Types:")
        print(f"  Match Winners: {len(df[df['market'].str.contains('Win|Draw') & ~df['market'].str.contains('H1')])}")
        print(f"  Over/Under Goals: {len(df[df['market'].str.contains('Over|Under') & ~df['market'].str.contains('Corner') & ~df['market'].str.contains('H1')])}")
        print(f"  BTTS: {len(df[df['market'].str.contains('BTTS')])}")
        print(f"  Corners: {len(df[df['market'].str.contains('Corner')])}")
        print(f"  H1 Totals: {len(df[df['market'].str.contains('H1')])}")
        print(f"\nTop 5 Best Bets:")
        print(f"{'='*80}")

        for idx, row in top5_df.iterrows():
            print(f"{row['home_team']} vs {row['away_team']}")
            print(f"  {row['league']} ({row['country']}) - {row['date']} {row['time']}")
            print(f"  Market: {row['market']} @ {row['odds']:.2f}")
            print(f"  Confidence: {row['confidence']:.1%} | Stake: {row['kelly_stake']:.1%} | EV: {row['expected_value']:.1%}")
            print()


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='Generate soccer best bets report')
    parser.add_argument('date', nargs='?',
                       help='Date in YYYY-MM-DD format (default: tomorrow)')
    args = parser.parse_args()

    # Default to tomorrow
    if args.date:
        date_str = args.date
    else:
        tomorrow = datetime.now() + timedelta(days=1)
        date_str = tomorrow.strftime('%Y-%m-%d')

    print(f"\n⚽ SOCCER BEST BETS GENERATOR")
    print(f"{'='*80}\n")
    print(f"Date: {date_str}")
    print(f"Thresholds: Winners {MIN_CONFIDENCE:.0%} | Totals {MIN_TOTALS_CONFIDENCE:.0%} | BTTS {MIN_BTTS_CONFIDENCE:.0%} | Corners {MIN_CORNERS_CONFIDENCE:.0%}")
    print(f"Kelly Fraction: {KELLY_FRACTION:.0%} (conservative)")
    print(f"Max Bet Size: {MAX_BET_SIZE:.0%} of bankroll\n")

    try:
        generator = SoccerBestBetsGenerator()
        df = generator.generate_daily_report(date_str)

        if not df.empty:
            generator.save_reports(df, date_str)
        else:
            print("\n⚠️  No high-confidence opportunities today")
            print("💡 This is normal - we only bet when we have a real edge!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
