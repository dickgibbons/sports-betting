#!/usr/bin/env python3
"""
Team Form Fetcher
Fetches team form and season statistics from API-Sports
"""

import requests
from typing import Dict, Optional, Tuple
from team_stats_cache import TeamStatsCache

API_KEY = "960c628e1c91c4b1f125e1eec52ad862"
API_BASE = "https://v3.football.api-sports.io"


class TeamFormFetcher:
    """Fetch team form and season statistics with caching"""

    def __init__(self, api_key: str = None):
        """Initialize fetcher with API key and cache"""
        self.api_key = api_key or API_KEY
        self.headers = {'x-apisports-key': self.api_key}
        self.cache = TeamStatsCache()

    def fetch_team_form(self, team_id: int, league_id: int, season: int,
                       num_games: int = 5) -> Dict:
        """
        Fetch team form (last N games statistics)

        Args:
            team_id: Team ID
            league_id: League ID
            season: Season year
            num_games: Number of recent games to analyze (default 5)

        Returns:
            Dictionary with form statistics
        """
        # Check cache first
        cached = self.cache.get_team_form(team_id, league_id, season, max_age_hours=24)
        if cached is not None:
            return cached

        # Fetch from API
        try:
            url = f"{API_BASE}/fixtures"
            params = {
                'team': team_id,
                'league': league_id,
                'season': season,
                'last': num_games * 2  # Fetch more to ensure we have enough
            }

            response = requests.get(url, params=params, headers=self.headers, timeout=10)

            if response.status_code != 200:
                print(f"   ⚠️  API error fetching form: {response.status_code}")
                return self._get_default_form()

            data = response.json()
            fixtures = data.get('response', [])

            if not fixtures:
                return self._get_default_form()

            # Analyze last N completed matches
            form_stats = self._analyze_fixtures(fixtures[:num_games], team_id)

            # Cache the results
            self.cache.set_team_form(team_id, league_id, season, form_stats)

            return form_stats

        except Exception as e:
            print(f"   ⚠️  Error fetching team form: {e}")
            return self._get_default_form()

    def _analyze_fixtures(self, fixtures: list, team_id: int) -> Dict:
        """
        Analyze fixtures to extract form statistics

        Args:
            fixtures: List of fixture dictionaries
            team_id: Team ID to analyze

        Returns:
            Dictionary with form statistics
        """
        wins = 0
        draws = 0
        losses = 0
        goals_for = 0
        goals_against = 0
        btts_count = 0
        over_25_count = 0
        clean_sheets = 0
        matches_analyzed = 0

        for fixture in fixtures:
            # Only analyze finished matches
            status = fixture.get('fixture', {}).get('status', {}).get('short', '')
            if status != 'FT':
                continue

            teams = fixture.get('teams', {})
            goals = fixture.get('goals', {})

            home_team = teams.get('home', {})
            away_team = teams.get('away', {})
            home_goals = goals.get('home', 0) or 0
            away_goals = goals.get('away', 0) or 0

            # Determine if team was home or away
            is_home = home_team.get('id') == team_id

            if is_home:
                team_goals = home_goals
                opponent_goals = away_goals
                winner = home_team.get('winner')
            else:
                team_goals = away_goals
                opponent_goals = home_goals
                winner = away_team.get('winner')

            # Update statistics
            goals_for += team_goals
            goals_against += opponent_goals

            if winner is True:
                wins += 1
            elif winner is False:
                losses += 1
            else:
                draws += 1

            # BTTS
            if team_goals > 0 and opponent_goals > 0:
                btts_count += 1

            # Over 2.5
            if (team_goals + opponent_goals) > 2.5:
                over_25_count += 1

            # Clean sheet
            if opponent_goals == 0:
                clean_sheets += 1

            matches_analyzed += 1

        # Handle case where no matches were analyzed
        if matches_analyzed == 0:
            return self._get_default_form()

        # Calculate rates
        btts_rate = btts_count / matches_analyzed if matches_analyzed > 0 else 0
        over_25_rate = over_25_count / matches_analyzed if matches_analyzed > 0 else 0

        # Calculate points (3 for win, 1 for draw)
        points = (wins * 3) + draws

        # Goal differential
        goal_diff = goals_for - goals_against

        return {
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'points': points,
            'goals_for': goals_for,
            'goals_against': goals_against,
            'goal_diff': goal_diff,
            'btts_rate': btts_rate,
            'over_25_rate': over_25_rate,
            'clean_sheets': clean_sheets,
            'matches_analyzed': matches_analyzed
        }

    def fetch_team_season_stats(self, team_id: int, league_id: int, season: int) -> Dict:
        """
        Fetch team season statistics

        Args:
            team_id: Team ID
            league_id: League ID
            season: Season year

        Returns:
            Dictionary with season statistics
        """
        # Check cache first
        cached = self.cache.get_team_season_stats(team_id, league_id, season, max_age_hours=24)
        if cached is not None:
            return cached

        # Fetch from API
        try:
            url = f"{API_BASE}/teams/statistics"
            params = {
                'team': team_id,
                'league': league_id,
                'season': season
            }

            response = requests.get(url, params=params, headers=self.headers, timeout=10)

            if response.status_code != 200:
                print(f"   ⚠️  API error fetching season stats: {response.status_code}")
                return self._get_default_season_stats()

            data = response.json()
            stats = data.get('response', {})

            if not stats:
                return self._get_default_season_stats()

            # Extract key statistics
            season_stats = self._extract_season_stats(stats)

            # Cache the results
            self.cache.set_team_season_stats(team_id, league_id, season, season_stats)

            return season_stats

        except Exception as e:
            print(f"   ⚠️  Error fetching season stats: {e}")
            return self._get_default_season_stats()

    def _extract_season_stats(self, stats: Dict) -> Dict:
        """
        Extract relevant statistics from API response

        Args:
            stats: API response dictionary

        Returns:
            Processed season statistics
        """
        fixtures = stats.get('fixtures', {})
        goals = stats.get('goals', {})

        # Total matches played
        total_played = fixtures.get('played', {}).get('total', 0) or 1  # Avoid division by zero

        # Wins, draws, losses
        total_wins = fixtures.get('wins', {}).get('total', 0) or 0
        total_draws = fixtures.get('draws', {}).get('total', 0) or 0
        total_losses = fixtures.get('loses', {}).get('total', 0) or 0

        # Home/away splits
        home_wins = fixtures.get('wins', {}).get('home', 0) or 0
        home_draws = fixtures.get('draws', {}).get('home', 0) or 0
        home_losses = fixtures.get('loses', {}).get('home', 0) or 0

        away_wins = fixtures.get('wins', {}).get('away', 0) or 0
        away_draws = fixtures.get('draws', {}).get('away', 0) or 0
        away_losses = fixtures.get('loses', {}).get('away', 0) or 0

        # Goals
        goals_for = goals.get('for', {}).get('total', {}).get('total', 0) or 0
        goals_against = goals.get('against', {}).get('total', {}).get('total', 0) or 0

        # Calculate rates
        win_rate = total_wins / total_played if total_played > 0 else 0
        goals_per_game = goals_for / total_played if total_played > 0 else 0
        conceded_per_game = goals_against / total_played if total_played > 0 else 0

        # Clean sheets
        clean_sheet = stats.get('clean_sheet', {})
        total_clean_sheets = clean_sheet.get('total', 0) or 0
        clean_sheet_rate = total_clean_sheets / total_played if total_played > 0 else 0

        return {
            'win_rate': win_rate,
            'goals_per_game': goals_per_game,
            'conceded_per_game': conceded_per_game,
            'clean_sheet_rate': clean_sheet_rate,
            'home_wins': home_wins,
            'home_draws': home_draws,
            'home_losses': home_losses,
            'away_wins': away_wins,
            'away_draws': away_draws,
            'away_losses': away_losses,
            'total_played': total_played
        }

    def fetch_team_features(self, team_id: int, league_id: int, season: int,
                           num_games: int = 5) -> Dict:
        """
        Fetch all team features (form + season stats) in one call

        Args:
            team_id: Team ID
            league_id: League ID
            season: Season year
            num_games: Number of recent games for form (default 5)

        Returns:
            Combined dictionary with form and season features
        """
        form_stats = self.fetch_team_form(team_id, league_id, season, num_games)
        season_stats = self.fetch_team_season_stats(team_id, league_id, season)

        # Combine features with prefixes
        features = {}

        # Form features (last N games)
        features[f'wins_last_{num_games}'] = form_stats['wins']
        features[f'draws_last_{num_games}'] = form_stats['draws']
        features[f'losses_last_{num_games}'] = form_stats['losses']
        features[f'points_last_{num_games}'] = form_stats['points']
        features[f'goals_for_last_{num_games}'] = form_stats['goals_for']
        features[f'goals_against_last_{num_games}'] = form_stats['goals_against']
        features[f'goal_diff_last_{num_games}'] = form_stats['goal_diff']
        features[f'btts_rate_last_{num_games}'] = form_stats['btts_rate']
        features[f'over_25_rate_last_{num_games}'] = form_stats['over_25_rate']
        features[f'clean_sheets_last_{num_games}'] = form_stats['clean_sheets']

        # Season features
        features['season_win_rate'] = season_stats['win_rate']
        features['season_goals_per_game'] = season_stats['goals_per_game']
        features['season_conceded_per_game'] = season_stats['conceded_per_game']
        features['season_clean_sheet_rate'] = season_stats['clean_sheet_rate']
        features['season_home_wins'] = season_stats['home_wins']
        features['season_away_wins'] = season_stats['away_wins']

        return features

    def _get_default_form(self) -> Dict:
        """Return default form statistics when API call fails"""
        return {
            'wins': 0,
            'draws': 0,
            'losses': 0,
            'points': 0,
            'goals_for': 0,
            'goals_against': 0,
            'goal_diff': 0,
            'btts_rate': 0.5,
            'over_25_rate': 0.5,
            'clean_sheets': 0,
            'matches_analyzed': 0
        }

    def _get_default_season_stats(self) -> Dict:
        """Return default season statistics when API call fails"""
        return {
            'win_rate': 0.33,
            'goals_per_game': 1.5,
            'conceded_per_game': 1.5,
            'clean_sheet_rate': 0.25,
            'home_wins': 0,
            'home_draws': 0,
            'home_losses': 0,
            'away_wins': 0,
            'away_draws': 0,
            'away_losses': 0,
            'total_played': 1
        }


if __name__ == "__main__":
    # Test the fetcher
    print("Testing TeamFormFetcher...")

    fetcher = TeamFormFetcher()

    # Test with Manchester City (team 50, EPL league 39, season 2024)
    print("\n📊 Fetching form for Manchester City...")
    form = fetcher.fetch_team_form(50, 39, 2024, num_games=5)
    print(f"Form (last 5): {form}")

    print("\n📊 Fetching season stats for Manchester City...")
    season = fetcher.fetch_team_season_stats(50, 39, 2024)
    print(f"Season stats: {season}")

    print("\n📊 Fetching all features...")
    features = fetcher.fetch_team_features(50, 39, 2024, num_games=5)
    print(f"All features: {features}")

    # Test cache
    print("\n📊 Cache stats:")
    cache_stats = fetcher.cache.get_cache_stats()
    print(f"{cache_stats}")

    print("\n✅ TeamFormFetcher tests complete!")
