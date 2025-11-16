#!/usr/bin/env python3
"""
Test NHL Predictions with Team Totals and Back-to-Back Tracking
"""

import pickle
import pandas as pd
import numpy as np
from datetime import datetime
from nhl_trainer_with_totals_b2b import NHLTrainerWithTotalsB2B

def load_models(filepath='nhl_models_with_totals_b2b.pkl'):
    """Load trained models"""
    with open(filepath, 'rb') as f:
        data = pickle.load(f)

    return data['models'], data['scaler'], data['feature_names']

def test_predictions():
    """Test predictions for today's games"""

    print("="*100)
    print("🏒 NHL PREDICTIONS TEST - Team Totals & Back-to-Back Tracking")
    print("="*100)

    # Load models
    print("\n📦 Loading models...")
    try:
        models, scaler, feature_names = load_models()
        print(f"   ✅ Loaded {len(models)} models")
        print(f"   ✅ Features: {len(feature_names)}")
    except Exception as e:
        print(f"   ❌ Error loading models: {e}")
        return

    # Initialize trainer to get data functions
    trainer = NHLTrainerWithTotalsB2B()

    # Test with a sample game (you can modify this to fetch today's games)
    print("\n🎯 Testing Predictions...")
    print("-"*100)

    # Example: Boston @ Toronto
    home_team = "Toronto Maple Leafs"
    away_team = "Boston Bruins"
    game_date = datetime.now().strftime('%Y-%m-%d')

    print(f"\n🏒 Game: {away_team} @ {home_team}")
    print(f"📅 Date: {game_date}")

    # Build features
    features_dict = trainer.data_integrator.build_enhanced_features(
        home_team,
        away_team,
        2.0,  # Default odds
        2.0,
        season=2024
    )

    if not features_dict:
        print("   ❌ Could not build features")
        return

    # Add back-to-back features
    home_days_rest = trainer.get_days_since_last_game(home_team, game_date, 2024)
    away_days_rest = trainer.get_days_since_last_game(away_team, game_date, 2024)

    features_dict['home_days_rest'] = home_days_rest
    features_dict['away_days_rest'] = away_days_rest
    features_dict['home_b2b'] = 1 if home_days_rest == 0 else 0
    features_dict['away_b2b'] = 1 if away_days_rest == 0 else 0
    features_dict['rest_differential'] = home_days_rest - away_days_rest

    print(f"\n📊 Back-to-Back Analysis:")
    print(f"   {home_team}: {home_days_rest} days rest {'⚠️ (B2B!)' if home_days_rest == 0 else ''}")
    print(f"   {away_team}: {away_days_rest} days rest {'⚠️ (B2B!)' if away_days_rest == 0 else ''}")
    print(f"   Rest Advantage: {abs(home_days_rest - away_days_rest)} days ({'Home' if home_days_rest > away_days_rest else 'Away' if away_days_rest > home_days_rest else 'Even'})")

    # Convert to array
    X = np.array([list(features_dict.values())])
    X_scaled = scaler.transform(X)

    # Make predictions
    print(f"\n🎯 PREDICTIONS:")
    print("-"*100)

    # Game Winner
    rf_win_prob = models['rf_winner'].predict_proba(X_scaled)[0][1]
    gb_win_prob = models['gb_winner'].predict_proba(X_scaled)[0][1]
    avg_win_prob = (rf_win_prob + gb_win_prob) / 2

    winner = home_team if avg_win_prob > 0.5 else away_team
    win_conf = max(avg_win_prob, 1 - avg_win_prob) * 100

    print(f"\n🏆 GAME WINNER:")
    print(f"   Predicted Winner: {winner}")
    print(f"   Confidence: {win_conf:.1f}%")
    print(f"   {home_team} Win Probability: {avg_win_prob*100:.1f}%")
    print(f"   {away_team} Win Probability: {(1-avg_win_prob)*100:.1f}%")

    # Home Team Totals
    print(f"\n🏠 {home_team} TEAM TOTALS:")

    # Home O/U 2.5
    rf_h25_prob = models['rf_home_over_2_5'].predict_proba(X_scaled)[0][1]
    gb_h25_prob = models['gb_home_over_2_5'].predict_proba(X_scaled)[0][1]
    avg_h25_prob = (rf_h25_prob + gb_h25_prob) / 2

    print(f"   Over 2.5 Goals: {avg_h25_prob*100:.1f}% ({'OVER' if avg_h25_prob > 0.5 else 'UNDER'})")

    # Home O/U 3.5
    rf_h35_prob = models['rf_home_over_3_5'].predict_proba(X_scaled)[0][1]
    gb_h35_prob = models['gb_home_over_3_5'].predict_proba(X_scaled)[0][1]
    avg_h35_prob = (rf_h35_prob + gb_h35_prob) / 2

    print(f"   Over 3.5 Goals: {avg_h35_prob*100:.1f}% ({'OVER' if avg_h35_prob > 0.5 else 'UNDER'})")

    # Away Team Totals
    print(f"\n✈️  {away_team} TEAM TOTALS:")

    # Away O/U 2.5
    rf_a25_prob = models['rf_away_over_2_5'].predict_proba(X_scaled)[0][1]
    gb_a25_prob = models['gb_away_over_2_5'].predict_proba(X_scaled)[0][1]
    avg_a25_prob = (rf_a25_prob + gb_a25_prob) / 2

    print(f"   Over 2.5 Goals: {avg_a25_prob*100:.1f}% ({'OVER' if avg_a25_prob > 0.5 else 'UNDER'})")

    # Away O/U 3.5
    rf_a35_prob = models['rf_away_over_3_5'].predict_proba(X_scaled)[0][1]
    gb_a35_prob = models['gb_away_over_3_5'].predict_proba(X_scaled)[0][1]
    avg_a35_prob = (rf_a35_prob + gb_a35_prob) / 2

    print(f"   Over 3.5 Goals: {avg_a35_prob*100:.1f}% ({'OVER' if avg_a35_prob > 0.5 else 'UNDER'})")

    # Expected Score Estimate
    home_expected = 2.5 if avg_h25_prob > 0.5 else (3.5 if avg_h35_prob > 0.5 else 2.0)
    away_expected = 2.5 if avg_a25_prob > 0.5 else (3.5 if avg_a35_prob > 0.5 else 2.0)

    print(f"\n📊 ESTIMATED SCORE:")
    print(f"   {home_team}: ~{home_expected:.1f} goals")
    print(f"   {away_team}: ~{away_expected:.1f} goals")
    print(f"   Expected Total: ~{home_expected + away_expected:.1f} goals")

    print(f"\n{'='*100}")
    print("✅ Test Complete!")
    print("="*100)

if __name__ == "__main__":
    test_predictions()
