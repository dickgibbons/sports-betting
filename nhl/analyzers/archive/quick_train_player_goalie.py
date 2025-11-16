#!/usr/bin/env python3
"""
Quick Initial Training for Player/Goalie Models
Creates initial models using simplified synthetic data based on season averages
These will be improved through continuous learning from actual game results
"""

import pandas as pd
import numpy as np
import pickle
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from datetime import datetime

print("🏒 QUICK PLAYER & GOALIE MODEL TRAINER")
print("=" * 80)
print("Creating initial models using league averages...")
print("These will improve through continuous learning from actual games")
print("")

# ============================================================================
# PLAYER SHOTS MODELS
# ============================================================================
print("📊 Training Player Shots Models...")

# Create synthetic training data based on typical NHL player stats
np.random.seed(42)
n_samples = 1000

# Positions
positions = np.random.choice(['C', 'LW', 'RW', 'D'], n_samples, p=[0.25, 0.25, 0.25, 0.25])

player_data = []
for i in range(n_samples):
    pos = positions[i]

    # Typical shots per game by position
    if pos in ['C', 'LW', 'RW']:
        base_shots = np.random.normal(2.5, 1.0)
    else:  # Defense
        base_shots = np.random.normal(1.5, 0.7)

    avg_shots = max(0.5, base_shots)
    toi = np.random.normal(17, 3) if pos in ['C', 'LW', 'RW'] else np.random.normal(19, 3)

    # Home ice advantage
    is_home = np.random.choice([0, 1])
    home_boost = 0.1 if is_home else 0

    # Actual shots with some variance
    actual_shots = max(0, np.random.poisson(avg_shots * (1 + home_boost)))

    player_data.append({
        'position_C': 1 if pos == 'C' else 0,
        'position_LW': 1 if pos == 'LW' else 0,
        'position_RW': 1 if pos == 'RW' else 0,
        'position_D': 1 if pos == 'D' else 0,
        'avg_shots_per_game': avg_shots,
        'season_shooting_pct': np.random.normal(10, 3),
        'season_points_per_game': avg_shots * 0.4,  # Rough correlation
        'toi_minutes': toi,
        'is_home': is_home,
        'opp_team_strength': np.random.normal(0.5, 0.1),
        'actual_shots': actual_shots
    })

df_players = pd.DataFrame(player_data)

# Train player models
player_feature_names = [
    'position_C', 'position_LW', 'position_RW', 'position_D',
    'avg_shots_per_game', 'season_shooting_pct', 'season_points_per_game',
    'toi_minutes', 'is_home', 'opp_team_strength'
]

X_player = df_players[player_feature_names]
y_player = df_players['actual_shots']

player_scaler = StandardScaler()
X_player_scaled = player_scaler.fit_transform(X_player)

rf_player = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
rf_player.fit(X_player_scaled, y_player)

gb_player = GradientBoostingRegressor(n_estimators=100, random_state=42)
gb_player.fit(X_player_scaled, y_player)

player_models = {
    'random_forest': rf_player,
    'gradient_boosting': gb_player
}

player_model_data = {
    'models': player_models,
    'scaler': player_scaler,
    'feature_names': player_feature_names,
    'trained_date': datetime.now().isoformat(),
    'training_type': 'initial_synthetic'
}

with open('nhl_player_models.pkl', 'wb') as f:
    pickle.dump(player_model_data, f)

print(f"   ✅ Player models trained and saved")
print(f"   📊 Random Forest score: {rf_player.score(X_player_scaled, y_player):.3f}")
print(f"   📊 Gradient Boosting score: {gb_player.score(X_player_scaled, y_player):.3f}")

# ============================================================================
# GOALIE SAVES MODELS
# ============================================================================
print("\n🥅 Training Goalie Saves Models...")

goalie_data = []
for i in range(500):  # Fewer samples for goalies
    # Typical saves per game
    avg_saves = np.random.normal(28, 5)
    save_pct = np.random.normal(0.910, 0.020)
    gaa = np.random.normal(2.8, 0.5)
    games_played = np.random.randint(10, 60)
    is_starter = np.random.choice([0, 1], p=[0.3, 0.7])

    # Opponent shots
    opp_shots = np.random.normal(30, 5)

    # Home ice advantage
    is_home = np.random.choice([0, 1])

    # Actual saves based on save percentage and shots
    expected_saves = opp_shots * save_pct
    actual_saves = max(0, np.random.normal(expected_saves, 2))

    goalie_data.append({
        'avg_saves_per_game': avg_saves,
        'season_save_pct': save_pct,
        'season_gaa': gaa,
        'games_played': games_played,
        'is_starter': is_starter,
        'opp_shots_total': opp_shots,
        'opp_shooting_strength': opp_shots / 30.0,
        'is_home': is_home,
        'actual_saves': actual_saves
    })

df_goalies = pd.DataFrame(goalie_data)

# Train goalie models
goalie_feature_names = [
    'avg_saves_per_game', 'season_save_pct', 'season_gaa',
    'games_played', 'is_starter',
    'opp_shots_total', 'opp_shooting_strength',
    'is_home'
]

X_goalie = df_goalies[goalie_feature_names]
y_goalie = df_goalies['actual_saves']

goalie_scaler = StandardScaler()
X_goalie_scaled = goalie_scaler.fit_transform(X_goalie)

rf_goalie = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
rf_goalie.fit(X_goalie_scaled, y_goalie)

gb_goalie = GradientBoostingRegressor(n_estimators=100, random_state=42)
gb_goalie.fit(X_goalie_scaled, y_goalie)

goalie_models = {
    'random_forest': rf_goalie,
    'gradient_boosting': gb_goalie
}

goalie_model_data = {
    'models': goalie_models,
    'scaler': goalie_scaler,
    'feature_names': goalie_feature_names,
    'trained_date': datetime.now().isoformat(),
    'training_type': 'initial_synthetic'
}

with open('nhl_goalie_models.pkl', 'wb') as f:
    pickle.dump(goalie_model_data, f)

print(f"   ✅ Goalie models trained and saved")
print(f"   📊 Random Forest score: {rf_goalie.score(X_goalie_scaled, y_goalie):.3f}")
print(f"   📊 Gradient Boosting score: {gb_goalie.score(X_goalie_scaled, y_goalie):.3f}")

print("\n" + "=" * 80)
print("✅ Initial models created successfully!")
print("")
print("📝 Note: These models use synthetic data based on NHL averages.")
print("   They will improve through continuous learning as actual game")
print("   results are processed by the daily automation system.")
print("")
print("🎯 Ready to generate predictions!")
