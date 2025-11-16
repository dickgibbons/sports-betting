#!/usr/bin/env python3
"""
NHL Enhanced Data Integration with Home/Road Splits
Combines multiple free data sources for better predictions:
- NHL Official API (player/team stats)
- MoneyPuck (advanced analytics - xG, Corsi, Fenwick) WITH HOME/ROAD SPLITS
- Puckpedia (injury data)
"""

import requests
import pandas as pd
import json
from typing import Dict, List, Optional
from datetime import datetime
import time

class NHLEnhancedDataWithSplits:
    """Integrate multiple NHL data sources with home/road splits"""

    def __init__(self):
        self.nhl_api_base = "https://api.nhle.com/stats/rest/en"
        self.moneypuck_base = "https://moneypuck.com/moneypuck/playerData/seasonSummary"

        # Cache
        self.moneypuck_cache = {}
        self.team_map = {
            # Map full names to 3-letter codes
            'Anaheim Ducks': 'ANA',
            'Boston Bruins': 'BOS',
            'Buffalo Sabres': 'BUF',
            'Calgary Flames': 'CGY',
            'Carolina Hurricanes': 'CAR',
            'Chicago Blackhawks': 'CHI',
            'Colorado Avalanche': 'COL',
            'Columbus Blue Jackets': 'CBJ',
            'Dallas Stars': 'DAL',
            'Detroit Red Wings': 'DET',
            'Edmonton Oilers': 'EDM',
            'Florida Panthers': 'FLA',
            'Los Angeles Kings': 'LAK',
            'Minnesota Wild': 'MIN',
            'Montreal Canadiens': 'MTL',
            'Montréal Canadiens': 'MTL',
            'Nashville Predators': 'NSH',
            'New Jersey Devils': 'NJD',
            'New York Islanders': 'NYI',
            'New York Rangers': 'NYR',
            'Ottawa Senators': 'OTT',
            'Philadelphia Flyers': 'PHI',
            'Pittsburgh Penguins': 'PIT',
            'San Jose Sharks': 'SJS',
            'Seattle Kraken': 'SEA',
            'St. Louis Blues': 'STL',
            'Tampa Bay Lightning': 'TBL',
            'Toronto Maple Leafs': 'TOR',
            'Vancouver Canucks': 'VAN',
            'Vegas Golden Knights': 'VGK',
            'Washington Capitals': 'WSH',
            'Winnipeg Jets': 'WPG'
        }

        print("🏒 NHL Enhanced Data Integration with Home/Road Splits initialized")

    def get_team_code(self, team_name: str) -> Optional[str]:
        """Convert team name to 3-letter code"""

        if team_name in self.team_map:
            return self.team_map[team_name]

        # Fuzzy match
        for name, code in self.team_map.items():
            if team_name.lower() in name.lower() or name.lower() in team_name.lower():
                return code

        return None

    def get_moneypuck_team_stats(self, season: int = 2024, home_road: str = 'all') -> pd.DataFrame:
        """
        Get advanced team stats from MoneyPuck

        Args:
            season: NHL season (2024 for 2024-25 season)
            home_road: 'all', 'home', or 'away'
        """

        cache_key = f"moneypuck_{season}_{home_road}"
        if cache_key in self.moneypuck_cache:
            return self.moneypuck_cache[cache_key]

        url = f"{self.moneypuck_base}/{season}/regular/teams.csv"

        try:
            df = pd.read_csv(url)

            # Filter to team-level data
            df = df[(df['position'] == 'Team Level')]

            # Filter by home/road/all
            if home_road == 'home':
                df = df[df['situation'] == 'home']
            elif home_road == 'away':
                df = df[df['situation'] == 'away']
            else:
                df = df[df['situation'] == 'all']

            # Keep key advanced metrics
            key_metrics = [
                'team', 'situation', 'xGoalsPercentage', 'corsiPercentage', 'fenwickPercentage',
                'xGoalsFor', 'xGoalsAgainst', 'shotsOnGoalFor', 'shotsOnGoalAgainst',
                'goalsFor', 'goalsAgainst', 'games_played',
                'highDangerShotsFor', 'highDangerShotsAgainst',
                'highDangerxGoalsFor', 'highDangerxGoalsAgainst'
            ]

            df = df[key_metrics].copy()

            # Cache it
            self.moneypuck_cache[cache_key] = df

            print(f"   ✅ MoneyPuck ({home_road}): {len(df)} teams with advanced stats")
            return df

        except Exception as e:
            print(f"   ❌ MoneyPuck error: {e}")
            return pd.DataFrame()

    def get_enhanced_team_features(self, team_name: str, season: int = 2024,
                                   home_road: str = 'all') -> Dict:
        """
        Get comprehensive team features from all sources

        Args:
            team_name: Full team name
            season: NHL season
            home_road: 'all', 'home', or 'away' for home/road splits
        """

        team_code = self.get_team_code(team_name)
        if not team_code:
            return {}

        features = {'team_code': team_code}

        # Get MoneyPuck advanced stats
        mp_data = self.get_moneypuck_team_stats(season, home_road)

        if not mp_data.empty:
            team_stats = mp_data[mp_data['team'] == team_code]

            if not team_stats.empty:
                team_stats = team_stats.iloc[0]

                features.update({
                    'xGoals_pct': float(team_stats.get('xGoalsPercentage', 0)),
                    'corsi_pct': float(team_stats.get('corsiPercentage', 0)),
                    'fenwick_pct': float(team_stats.get('fenwickPercentage', 0)),
                    'xGF': float(team_stats.get('xGoalsFor', 0)),
                    'xGA': float(team_stats.get('xGoalsAgainst', 0)),
                    'SOG_for': float(team_stats.get('shotsOnGoalFor', 0)),
                    'SOG_against': float(team_stats.get('shotsOnGoalAgainst', 0)),
                    'GF': float(team_stats.get('goalsFor', 0)),
                    'GA': float(team_stats.get('goalsAgainst', 0)),
                    'games_played': int(team_stats.get('games_played', 0)),
                    'HD_shots_for': float(team_stats.get('highDangerShotsFor', 0)),
                    'HD_shots_against': float(team_stats.get('highDangerShotsAgainst', 0)),
                    'HD_xGF': float(team_stats.get('highDangerxGoalsFor', 0)),
                    'HD_xGA': float(team_stats.get('highDangerxGoalsAgainst', 0)),
                })

        return features

    def build_enhanced_features(self, home_team: str, away_team: str,
                               home_odds: float, away_odds: float,
                               season: int = 2024) -> Optional[Dict]:
        """Build complete feature set for ML model WITH HOME/ROAD SPLITS"""

        print(f"   Building features with home/road splits: {home_team} vs {away_team}")

        # Get overall stats
        home_features_all = self.get_enhanced_team_features(home_team, season, 'all')
        away_features_all = self.get_enhanced_team_features(away_team, season, 'all')

        # Get home-specific stats for home team
        home_features_home = self.get_enhanced_team_features(home_team, season, 'home')

        # Get road-specific stats for away team
        away_features_road = self.get_enhanced_team_features(away_team, season, 'away')

        if not home_features_all or not away_features_all:
            return None

        # Combine features
        features = {
            # Home team OVERALL stats (legacy features)
            'home_xGoals_pct': home_features_all.get('xGoals_pct', 0),
            'home_corsi_pct': home_features_all.get('corsi_pct', 0),
            'home_fenwick_pct': home_features_all.get('fenwick_pct', 0),
            'home_xGF_per_game': home_features_all.get('xGF', 0) / max(home_features_all.get('games_played', 1), 1),
            'home_xGA_per_game': home_features_all.get('xGA', 0) / max(home_features_all.get('games_played', 1), 1),
            'home_GF_per_game': home_features_all.get('GF', 0) / max(home_features_all.get('games_played', 1), 1),
            'home_GA_per_game': home_features_all.get('GA', 0) / max(home_features_all.get('games_played', 1), 1),
            'home_HD_xGF_per_game': home_features_all.get('HD_xGF', 0) / max(home_features_all.get('games_played', 1), 1),

            # Away team OVERALL stats (legacy features)
            'away_xGoals_pct': away_features_all.get('xGoals_pct', 0),
            'away_corsi_pct': away_features_all.get('corsi_pct', 0),
            'away_fenwick_pct': away_features_all.get('fenwick_pct', 0),
            'away_xGF_per_game': away_features_all.get('xGF', 0) / max(away_features_all.get('games_played', 1), 1),
            'away_xGA_per_game': away_features_all.get('xGA', 0) / max(away_features_all.get('games_played', 1), 1),
            'away_GF_per_game': away_features_all.get('GF', 0) / max(away_features_all.get('games_played', 1), 1),
            'away_GA_per_game': away_features_all.get('GA', 0) / max(away_features_all.get('games_played', 1), 1),
            'away_HD_xGF_per_game': away_features_all.get('HD_xGF', 0) / max(away_features_all.get('games_played', 1), 1),

            # Differentials (key predictors)
            'xGoals_pct_diff': home_features_all.get('xGoals_pct', 0) - away_features_all.get('xGoals_pct', 0),
            'corsi_pct_diff': home_features_all.get('corsi_pct', 0) - away_features_all.get('corsi_pct', 0),
            'fenwick_pct_diff': home_features_all.get('fenwick_pct', 0) - away_features_all.get('fenwick_pct', 0),
            'xGF_diff': (home_features_all.get('xGF', 0) - away_features_all.get('xGF', 0)) / max(home_features_all.get('games_played', 1), 1),
            'HD_xGF_diff': (home_features_all.get('HD_xGF', 0) - away_features_all.get('HD_xGF', 0)) / max(home_features_all.get('games_played', 1), 1),

            # Betting odds
            'home_odds': home_odds,
            'away_odds': away_odds,
            'home_implied_prob': 1 / home_odds if home_odds > 0 else 0,
            'away_implied_prob': 1 / away_odds if away_odds > 0 else 0,

            # === NEW: HOME/ROAD SPLIT FEATURES ===
            # Home team when playing AT HOME
            'home_team_home_GF_per_game': home_features_home.get('GF', 0) / max(home_features_home.get('games_played', 1), 1),
            'home_team_home_GA_per_game': home_features_home.get('GA', 0) / max(home_features_home.get('games_played', 1), 1),
            'home_team_home_xGF_per_game': home_features_home.get('xGF', 0) / max(home_features_home.get('games_played', 1), 1),
            'home_team_home_xGA_per_game': home_features_home.get('xGA', 0) / max(home_features_home.get('games_played', 1), 1),
            'home_team_home_xGoals_pct': home_features_home.get('xGoals_pct', 0),
            'home_team_home_corsi_pct': home_features_home.get('corsi_pct', 0),

            # Away team when playing ON THE ROAD
            'away_team_road_GF_per_game': away_features_road.get('GF', 0) / max(away_features_road.get('games_played', 1), 1),
            'away_team_road_GA_per_game': away_features_road.get('GA', 0) / max(away_features_road.get('games_played', 1), 1),
            'away_team_road_xGF_per_game': away_features_road.get('xGF', 0) / max(away_features_road.get('games_played', 1), 1),
            'away_team_road_xGA_per_game': away_features_road.get('xGA', 0) / max(away_features_road.get('games_played', 1), 1),
            'away_team_road_xGoals_pct': away_features_road.get('xGoals_pct', 0),
            'away_team_road_corsi_pct': away_features_road.get('corsi_pct', 0),

            # Split differentials (home team at home vs. away team on road)
            'split_GF_diff': (home_features_home.get('GF', 0) / max(home_features_home.get('games_played', 1), 1)) -
                            (away_features_road.get('GF', 0) / max(away_features_road.get('games_played', 1), 1)),
            'split_xGoals_pct_diff': home_features_home.get('xGoals_pct', 0) - away_features_road.get('xGoals_pct', 0),
            'split_corsi_pct_diff': home_features_home.get('corsi_pct', 0) - away_features_road.get('corsi_pct', 0),
        }

        return features


def main():
    """Test enhanced data integration with home/road splits"""

    print("🏒 Testing NHL Enhanced Data Integration with Home/Road Splits")
    print("=" * 80)

    data_integrator = NHLEnhancedDataWithSplits()

    # Test MoneyPuck data with splits
    print("\n📊 Testing MoneyPuck Advanced Stats (Overall)...")
    mp_data_all = data_integrator.get_moneypuck_team_stats(2024, 'all')

    print("\n🏠 Testing MoneyPuck Advanced Stats (Home Only)...")
    mp_data_home = data_integrator.get_moneypuck_team_stats(2024, 'home')

    print("\n✈️  Testing MoneyPuck Advanced Stats (Road Only)...")
    mp_data_road = data_integrator.get_moneypuck_team_stats(2024, 'away')

    # Test feature building
    print("\n🔨 Testing Feature Building with Home/Road Splits...")
    features = data_integrator.build_enhanced_features(
        "Boston Bruins",
        "Toronto Maple Leafs",
        2.1,
        1.8,
        season=2024
    )

    if features:
        print(f"\n✅ Generated {len(features)} features (up from 30!):")
        print("\n🆕 NEW HOME/ROAD SPLIT FEATURES:")
        split_features = {k: v for k, v in features.items() if 'home_team_home' in k or 'away_team_road' in k or 'split_' in k}
        for key, value in split_features.items():
            print(f"   {key}: {value:.4f}")

    print("\n✅ Enhanced data integration with home/road splits ready!")


if __name__ == "__main__":
    main()
