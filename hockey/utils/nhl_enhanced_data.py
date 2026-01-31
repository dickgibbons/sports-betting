#!/usr/bin/env python3
"""
NHL Enhanced Data Integration
Combines multiple free data sources for better predictions:
- NHL Official API (player/team stats)
- MoneyPuck (advanced analytics - xG, Corsi, Fenwick)
- Puckpedia (injury data)
"""

import requests
import pandas as pd
import json
from typing import Dict, List, Optional
from datetime import datetime
import time

class NHLEnhancedData:
    """Integrate multiple NHL data sources"""

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

        print("🏒 NHL Enhanced Data Integration initialized")

    def get_team_code(self, team_name: str) -> Optional[str]:
        """Convert team name to 3-letter code"""

        if team_name in self.team_map:
            return self.team_map[team_name]

        # Fuzzy match
        for name, code in self.team_map.items():
            if team_name.lower() in name.lower() or name.lower() in team_name.lower():
                return code

        return None

    def get_moneypuck_team_stats(self, season: int = 2024) -> pd.DataFrame:
        """Get advanced team stats from MoneyPuck"""

        cache_key = f"moneypuck_{season}"
        if cache_key in self.moneypuck_cache:
            return self.moneypuck_cache[cache_key]

        url = f"{self.moneypuck_base}/{season}/regular/teams.csv"

        try:
            df = pd.read_csv(url)

            # Filter to team-level, all situations data
            df = df[(df['position'] == 'Team Level') & (df['situation'] == 'all')]

            # Keep key advanced metrics
            key_metrics = [
                'team', 'xGoalsPercentage', 'corsiPercentage', 'fenwickPercentage',
                'xGoalsFor', 'xGoalsAgainst', 'shotsOnGoalFor', 'shotsOnGoalAgainst',
                'goalsFor', 'goalsAgainst', 'games_played',
                'highDangerShotsFor', 'highDangerShotsAgainst',
                'highDangerxGoalsFor', 'highDangerxGoalsAgainst'
            ]

            df = df[key_metrics].copy()

            # Cache it
            self.moneypuck_cache[cache_key] = df

            print(f"   ✅ MoneyPuck: {len(df)} teams with advanced stats")
            return df

        except Exception as e:
            print(f"   ❌ MoneyPuck error: {e}")
            return pd.DataFrame()

    def get_puckpedia_injuries(self) -> Dict[str, List[str]]:
        """
        Get injury data from Puckpedia
        Note: This would require web scraping. For now, return empty dict.
        TODO: Implement BeautifulSoup scraping
        """

        # This would scrape https://puckpedia.com/injuries
        # For now, return placeholder

        print("   ⚠️  Injury data scraping not yet implemented")
        return {}

    def get_enhanced_team_features(self, team_name: str, season: int = 2024) -> Dict:
        """Get comprehensive team features from all sources"""

        team_code = self.get_team_code(team_name)
        if not team_code:
            return {}

        features = {'team_code': team_code}

        # Get MoneyPuck advanced stats
        mp_data = self.get_moneypuck_team_stats(season)

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
        """Build complete feature set for ML model"""

        print(f"   Building features: {home_team} vs {away_team}")

        home_features = self.get_enhanced_team_features(home_team, season)
        away_features = self.get_enhanced_team_features(away_team, season)

        if not home_features or not away_features:
            return None

        # Combine features
        features = {
            # Home team advanced stats
            'home_xGoals_pct': home_features.get('xGoals_pct', 0),
            'home_corsi_pct': home_features.get('corsi_pct', 0),
            'home_fenwick_pct': home_features.get('fenwick_pct', 0),
            'home_xGF_per_game': home_features.get('xGF', 0) / max(home_features.get('games_played', 1), 1),
            'home_xGA_per_game': home_features.get('xGA', 0) / max(home_features.get('games_played', 1), 1),
            'home_GF_per_game': home_features.get('GF', 0) / max(home_features.get('games_played', 1), 1),
            'home_GA_per_game': home_features.get('GA', 0) / max(home_features.get('games_played', 1), 1),
            'home_HD_xGF_per_game': home_features.get('HD_xGF', 0) / max(home_features.get('games_played', 1), 1),

            # Away team advanced stats
            'away_xGoals_pct': away_features.get('xGoals_pct', 0),
            'away_corsi_pct': away_features.get('corsi_pct', 0),
            'away_fenwick_pct': away_features.get('fenwick_pct', 0),
            'away_xGF_per_game': away_features.get('xGF', 0) / max(away_features.get('games_played', 1), 1),
            'away_xGA_per_game': away_features.get('xGA', 0) / max(away_features.get('games_played', 1), 1),
            'away_GF_per_game': away_features.get('GF', 0) / max(away_features.get('games_played', 1), 1),
            'away_GA_per_game': away_features.get('GA', 0) / max(away_features.get('games_played', 1), 1),
            'away_HD_xGF_per_game': away_features.get('HD_xGF', 0) / max(away_features.get('games_played', 1), 1),

            # Differentials (key predictors)
            'xGoals_pct_diff': home_features.get('xGoals_pct', 0) - away_features.get('xGoals_pct', 0),
            'corsi_pct_diff': home_features.get('corsi_pct', 0) - away_features.get('corsi_pct', 0),
            'fenwick_pct_diff': home_features.get('fenwick_pct', 0) - away_features.get('fenwick_pct', 0),
            'xGF_diff': (home_features.get('xGF', 0) - away_features.get('xGF', 0)) / max(home_features.get('games_played', 1), 1),
            'HD_xGF_diff': (home_features.get('HD_xGF', 0) - away_features.get('HD_xGF', 0)) / max(home_features.get('games_played', 1), 1),

            # Betting odds
            'home_odds': home_odds,
            'away_odds': away_odds,
            'home_implied_prob': 1 / home_odds if home_odds > 0 else 0,
            'away_implied_prob': 1 / away_odds if away_odds > 0 else 0,
        }

        return features


def main():
    """Test enhanced data integration"""

    print("🏒 Testing NHL Enhanced Data Integration")
    print("=" * 60)

    data_integrator = NHLEnhancedData()

    # Test MoneyPuck data
    print("\n📊 Testing MoneyPuck Advanced Stats...")
    mp_data = data_integrator.get_moneypuck_team_stats(2024)

    if not mp_data.empty:
        print(f"\nTop 5 teams by xGoals%:")
        top_teams = mp_data.nlargest(5, 'xGoalsPercentage')
        for _, team in top_teams.iterrows():
            print(f"   {team['team']}: {team['xGoalsPercentage']:.3f} xG%, {team['corsiPercentage']:.3f} Corsi%")

    # Test feature building
    print("\n🔨 Testing Feature Building...")
    features = data_integrator.build_enhanced_features(
        "Boston Bruins",
        "Toronto Maple Leafs",
        2.1,
        1.8,
        season=2024
    )

    if features:
        print(f"\n✅ Generated {len(features)} features:")
        for key, value in list(features.items())[:10]:
            print(f"   {key}: {value:.4f}")

    print("\n✅ Enhanced data integration ready!")


if __name__ == "__main__":
    main()
