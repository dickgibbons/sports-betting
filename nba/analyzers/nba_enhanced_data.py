#!/usr/bin/env python3
"""
NBA Enhanced Data Integration
Combines multiple free data sources for better predictions:
- NBA Official API (player/team stats)
- BallDontLie API (free NBA stats)
- ESPN API (backup stats)
"""

import requests
import pandas as pd
import json
from typing import Dict, List, Optional
from datetime import datetime
import time

class NBAEnhancedData:
    """Integrate multiple NBA data sources"""

    def __init__(self):
        self.balldontlie_base = "https://api.balldontlie.io/v1"
        self.nba_stats_base = "https://stats.nba.com/stats"

        # Cache
        self.stats_cache = {}
        self.team_map = {
            # Map full names to 3-letter codes
            'Atlanta Hawks': 'ATL',
            'Boston Celtics': 'BOS',
            'Brooklyn Nets': 'BKN',
            'Charlotte Hornets': 'CHA',
            'Chicago Bulls': 'CHI',
            'Cleveland Cavaliers': 'CLE',
            'Dallas Mavericks': 'DAL',
            'Denver Nuggets': 'DEN',
            'Detroit Pistons': 'DET',
            'Golden State Warriors': 'GSW',
            'Houston Rockets': 'HOU',
            'Indiana Pacers': 'IND',
            'Los Angeles Clippers': 'LAC',
            'Los Angeles Lakers': 'LAL',
            'Memphis Grizzlies': 'MEM',
            'Miami Heat': 'MIA',
            'Milwaukee Bucks': 'MIL',
            'Minnesota Timberwolves': 'MIN',
            'New Orleans Pelicans': 'NOP',
            'New York Knicks': 'NYK',
            'Oklahoma City Thunder': 'OKC',
            'Orlando Magic': 'ORL',
            'Philadelphia 76ers': 'PHI',
            'Phoenix Suns': 'PHX',
            'Portland Trail Blazers': 'POR',
            'Sacramento Kings': 'SAC',
            'San Antonio Spurs': 'SAS',
            'Toronto Raptors': 'TOR',
            'Utah Jazz': 'UTA',
            'Washington Wizards': 'WAS'
        }

        print("🏀 NBA Enhanced Data Integration initialized")

    def get_team_code(self, team_name: str) -> Optional[str]:
        """Convert team name to 3-letter code"""

        if team_name in self.team_map:
            return self.team_map[team_name]

        # Fuzzy match
        for name, code in self.team_map.items():
            if team_name.lower() in name.lower() or name.lower() in team_name.lower():
                return code

        return None

    def get_nba_team_stats(self, season: int = 2024) -> pd.DataFrame:
        """Get NBA team stats from NBA.com Official Stats API"""

        cache_key = f"nba_stats_{season}"
        if cache_key in self.stats_cache:
            return self.stats_cache[cache_key]

        # NBA.com stats endpoints require headers
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://stats.nba.com/',
            'x-nba-stats-origin': 'stats',
            'x-nba-stats-token': 'true'
        }

        # Convert season format (2024 -> 2024-25)
        season_str = f"{season}-{str(season + 1)[-2:]}"

        url = f"{self.nba_stats_base}/leaguedashteamstats"
        params = {
            'Season': season_str,
            'SeasonType': 'Regular Season',
            'LeagueID': '00',
            'PerMode': 'PerGame',
            'MeasureType': 'Base'
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code != 200:
                print(f"   ⚠️  NBA Stats API returned status {response.status_code}")
                return pd.DataFrame()

            data = response.json()
            result_sets = data.get('resultSets', [])

            if not result_sets:
                return pd.DataFrame()

            # Get headers and data
            headers_list = result_sets[0].get('headers', [])
            rows = result_sets[0].get('rowSet', [])

            # Convert to DataFrame
            df = pd.DataFrame(rows, columns=headers_list)

            # Keep key metrics
            key_metrics = [
                'TEAM_ABBREVIATION', 'TEAM_NAME', 'GP', 'W', 'L',
                'PTS', 'FGM', 'FGA', 'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT',
                'FTM', 'FTA', 'FT_PCT', 'OREB', 'DREB', 'REB', 'AST', 'TOV', 'STL', 'BLK'
            ]

            df = df[key_metrics].copy()

            # Rename to match our format
            df.rename(columns={
                'TEAM_ABBREVIATION': 'team',
                'TEAM_NAME': 'team_name',
                'GP': 'games_played',
                'W': 'wins',
                'L': 'losses',
                'PTS': 'pointsFor',
                'FG_PCT': 'fgPct',
                'FG3_PCT': 'fg3Pct',
                'FT_PCT': 'ftPct',
                'REB': 'rebounds',
                'AST': 'assists',
                'TOV': 'turnovers',
                'STL': 'steals',
                'BLK': 'blocks',
                'FGA': 'fga',
                'FTA': 'fta',
                'OREB': 'offReb',
                'DREB': 'defReb'
            }, inplace=True)

            # Calculate advanced metrics
            # Pace = possessions per game (estimate)
            df['pace'] = (df['fga'] - df['offReb'] + df['turnovers'] + 0.4 * df['fta'])

            # Offensive Rating = Points per 100 possessions
            df['offRating'] = (df['pointsFor'] / df['pace']) * 100

            # We'll need opponent stats for defensive rating - estimate for now
            df['pointsAgainst'] = 110.0  # Will be updated with actual data
            df['defRating'] = 110.0  # Will be updated with actual data

            # Calculate effective FG% (accounts for 3-pointers being worth more)
            df['efgPct'] = (df['FGM'] + 0.5 * df['FG3M']) / df['fga']

            # True Shooting % = PTS / (2 * (FGA + 0.44 * FTA))
            df['tsPct'] = df['pointsFor'] / (2 * (df['fga'] + 0.44 * df['fta']))

            # Cache it
            self.stats_cache[cache_key] = df

            print(f"   ✅ NBA Stats: {len(df)} teams with statistics")
            return df

        except Exception as e:
            print(f"   ❌ NBA Stats error: {e}")
            return pd.DataFrame()

    def get_enhanced_team_features(self, team_name: str, season: int = 2024) -> Dict:
        """Get comprehensive team features from all sources"""

        team_code = self.get_team_code(team_name)
        if not team_code:
            return {}

        features = {'team_code': team_code}

        # Get NBA Official stats
        nba_data = self.get_nba_team_stats(season)

        if not nba_data.empty:
            team_stats = nba_data[nba_data['team'] == team_code]

            if not team_stats.empty:
                team_stats = team_stats.iloc[0]

                features.update({
                    'pointsFor_per_game': float(team_stats.get('pointsFor', 0)),
                    'pointsAgainst_per_game': float(team_stats.get('pointsAgainst', 110)),
                    'fgPct': float(team_stats.get('fgPct', 0.45)),
                    'fg3Pct': float(team_stats.get('fg3Pct', 0.35)),
                    'ftPct': float(team_stats.get('ftPct', 0.75)),
                    'rebounds_per_game': float(team_stats.get('rebounds', 0)),
                    'assists_per_game': float(team_stats.get('assists', 0)),
                    'turnovers_per_game': float(team_stats.get('turnovers', 0)),
                    'steals_per_game': float(team_stats.get('steals', 0)),
                    'blocks_per_game': float(team_stats.get('blocks', 0)),
                    'pace': float(team_stats.get('pace', 100)),
                    'offRating': float(team_stats.get('offRating', 110)),
                    'defRating': float(team_stats.get('defRating', 110)),
                    'games_played': int(team_stats.get('games_played', 0)),
                    'wins': int(team_stats.get('wins', 0)),
                    'losses': int(team_stats.get('losses', 0)),
                    'efgPct': float(team_stats.get('efgPct', 0.50)),
                    'tsPct': float(team_stats.get('tsPct', 0.55)),
                })

                # Win percentage
                gp = features['games_played']
                if gp > 0:
                    features['win_pct'] = features['wins'] / gp
                else:
                    features['win_pct'] = 0.5

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
            # Home team stats
            'home_pointsFor_per_game': home_features.get('pointsFor_per_game', 0),
            'home_pointsAgainst_per_game': home_features.get('pointsAgainst_per_game', 0),
            'home_fgPct': home_features.get('fgPct', 0),
            'home_fg3Pct': home_features.get('fg3Pct', 0),
            'home_ftPct': home_features.get('ftPct', 0),
            'home_rebounds_per_game': home_features.get('rebounds_per_game', 0),
            'home_assists_per_game': home_features.get('assists_per_game', 0),
            'home_turnovers_per_game': home_features.get('turnovers_per_game', 0),
            'home_pace': home_features.get('pace', 0),
            'home_offRating': home_features.get('offRating', 0),
            'home_defRating': home_features.get('defRating', 0),
            'home_win_pct': home_features.get('win_pct', 0),
            'home_efgPct': home_features.get('efgPct', 0),
            'home_tsPct': home_features.get('tsPct', 0),

            # Away team stats
            'away_pointsFor_per_game': away_features.get('pointsFor_per_game', 0),
            'away_pointsAgainst_per_game': away_features.get('pointsAgainst_per_game', 0),
            'away_fgPct': away_features.get('fgPct', 0),
            'away_fg3Pct': away_features.get('fg3Pct', 0),
            'away_ftPct': away_features.get('ftPct', 0),
            'away_rebounds_per_game': away_features.get('rebounds_per_game', 0),
            'away_assists_per_game': away_features.get('assists_per_game', 0),
            'away_turnovers_per_game': away_features.get('turnovers_per_game', 0),
            'away_pace': away_features.get('pace', 0),
            'away_offRating': away_features.get('offRating', 0),
            'away_defRating': away_features.get('defRating', 0),
            'away_win_pct': away_features.get('win_pct', 0),
            'away_efgPct': away_features.get('efgPct', 0),
            'away_tsPct': away_features.get('tsPct', 0),

            # Differentials (key predictors)
            'pointsFor_diff': home_features.get('pointsFor_per_game', 0) - away_features.get('pointsFor_per_game', 0),
            'offRating_diff': home_features.get('offRating', 0) - away_features.get('offRating', 0),
            'defRating_diff': home_features.get('defRating', 0) - away_features.get('defRating', 0),
            'pace_diff': home_features.get('pace', 0) - away_features.get('pace', 0),
            'win_pct_diff': home_features.get('win_pct', 0) - away_features.get('win_pct', 0),
            'efgPct_diff': home_features.get('efgPct', 0) - away_features.get('efgPct', 0),
            'tsPct_diff': home_features.get('tsPct', 0) - away_features.get('tsPct', 0),

            # Betting odds
            'home_odds': home_odds,
            'away_odds': away_odds,
            'home_implied_prob': 1 / home_odds if home_odds > 0 else 0,
            'away_implied_prob': 1 / away_odds if away_odds > 0 else 0,
        }

        return features


def main():
    """Test enhanced data integration"""

    print("🏀 Testing NBA Enhanced Data Integration")
    print("=" * 60)

    data_integrator = NBAEnhancedData()

    # Test NBA Official Stats
    print("\n📊 Testing NBA Official Stats...")
    nba_data = data_integrator.get_nba_team_stats(2024)

    if not nba_data.empty:
        print(f"\nTop 5 teams by Points Per Game:")
        top_teams = nba_data.nlargest(5, 'pointsFor')
        for _, team in top_teams.iterrows():
            print(f"   {team['team']}: {team['pointsFor']:.1f} PPG, {team['fgPct']:.3f} FG%")

    # Test feature building
    print("\n🔨 Testing Feature Building...")
    features = data_integrator.build_enhanced_features(
        "Los Angeles Lakers",
        "Golden State Warriors",
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
