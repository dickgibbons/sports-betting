"""
DataGolf API Client
Wrapper for interacting with DataGolf.com API endpoints
"""

import requests
import pandas as pd
from typing import Optional, List, Dict, Any
import time


class DataGolfClient:
    """Client for interacting with DataGolf API"""
    
    def __init__(self, api_key: str, base_url: str = "https://feeds.datagolf.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[Any, Any]:
        """Make API request with error handling"""
        if params is None:
            params = {}
        params['key'] = self.api_key
        params['file_format'] = 'json'
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}")
            raise
    
    # ==================== GENERAL ENDPOINTS ====================
    
    def get_player_list(self) -> pd.DataFrame:
        """Get list of all players with IDs"""
        data = self._make_request("get-player-list")
        return pd.DataFrame(data)
    
    def get_tour_schedule(self, tour: str = "pga", season: Optional[int] = None) -> pd.DataFrame:
        """
        Get tournament schedule
        
        Args:
            tour: 'pga', 'euro', 'kft', 'liv'
            season: Year (e.g., 2025)
        """
        params = {'tour': tour}
        if season:
            params['season'] = season
        data = self._make_request("get-schedule", params)
        return pd.DataFrame(data['schedule'])
    
    def get_field_updates(self, tour: str = "pga") -> pd.DataFrame:
        """Get current field updates, withdrawals, tee times"""
        params = {'tour': tour}
        data = self._make_request("field-updates", params)
        return pd.DataFrame(data.get('field', []))
    
    # ==================== RANKINGS & SKILL ====================
    
    def get_dg_rankings(self) -> pd.DataFrame:
        """Get DataGolf player rankings"""
        data = self._make_request("preds/get-dg-rankings")
        return pd.DataFrame(data['rankings'])
    
    def get_player_skill_decompositions(self, tour: str = "pga") -> pd.DataFrame:
        """Get skill decomposition by category for each player"""
        params = {'tour': tour}
        data = self._make_request("preds/skill-decompositions", params)
        return pd.DataFrame(data['players'])
    
    def get_player_skill_ratings(self, display: str = "value") -> pd.DataFrame:
        """
        Get player skill ratings
        
        Args:
            display: 'value' or 'rank'
        """
        params = {'display': display}
        data = self._make_request("preds/player-skill-ratings", params)
        return pd.DataFrame(data['players'])
    
    def get_detailed_approach_skill(self, period: str = "l24") -> pd.DataFrame:
        """
        Get detailed approach skill by yardage bucket
        
        Args:
            period: 'l24' (last 24 rounds), 'l12', 'ytd', etc.
        """
        params = {'period': period}
        data = self._make_request("preds/approach-skill", params)
        return pd.DataFrame(data['players'])
    
    # ==================== PREDICTIONS ====================
    
    def get_pre_tournament_predictions(
        self, 
        tour: str = "pga",
        add_position: Optional[str] = None,
        odds_format: str = "decimal"
    ) -> pd.DataFrame:
        """
        Get pre-tournament win/top 5/10/20 predictions
        
        Args:
            tour: 'pga', 'euro', 'kft', 'opp', 'alt'
            add_position: Additional positions like '17,23,30'
            odds_format: 'decimal', 'american', 'percent', 'fraction'
        """
        params = {
            'tour': tour,
            'odds_format': odds_format
        }
        if add_position:
            params['add_position'] = add_position
        
        data = self._make_request("preds/pre-tournament", params)
        df = pd.DataFrame(data['baseline_history_fit'])
        
        # Also capture baseline-only predictions if available
        if 'baseline' in data:
            df_baseline = pd.DataFrame(data['baseline'])
            df_baseline = df_baseline.add_suffix('_baseline')
            # Merge on player name
        
        return df
    
    def get_pre_tournament_archive(
        self,
        event_id: Optional[int] = None,
        year: Optional[int] = None,
        odds_format: str = "decimal"
    ) -> pd.DataFrame:
        """Get historical pre-tournament predictions"""
        params = {'odds_format': odds_format}
        if event_id:
            params['event_id'] = event_id
        if year:
            params['year'] = year
        
        data = self._make_request("preds/pre-tournament-archive", params)
        return pd.DataFrame(data.get('baseline_history_fit', []))
    
    # ==================== LIVE PREDICTIONS ====================
    
    def get_live_predictions(self, tour: str = "pga", odds_format: str = "decimal") -> Dict:
        """Get live in-play predictions during tournament"""
        params = {'tour': tour, 'odds_format': odds_format}
        return self._make_request("preds/in-play", params)
    
    def get_live_tournament_stats(
        self,
        stats: str = "sg_ott,sg_app,sg_arg,sg_putt,sg_total",
        round_num: str = "event_avg",
        display: str = "value"
    ) -> pd.DataFrame:
        """
        Get live strokes-gained stats during tournament
        
        Args:
            stats: Comma-separated list of stats
            round_num: 'event_avg', '1', '2', '3', '4'
            display: 'value' or 'rank'
        """
        params = {
            'stats': stats,
            'round': round_num,
            'display': display
        }
        data = self._make_request("preds/live-tournament-stats", params)
        return pd.DataFrame(data.get('live_stats', []))
    
    # ==================== HISTORICAL RAW DATA ====================
    
    def get_historical_events_list(self) -> pd.DataFrame:
        """Get list of all historical events available"""
        data = self._make_request("historical-raw-data/event-list")
        # Handle both list response and dict with 'events' key
        if isinstance(data, list):
            return pd.DataFrame(data)
        return pd.DataFrame(data.get('events', data))
    
    def get_historical_round_scoring(
        self,
        tour: str = "pga",
        event_id: Optional[str] = None,
        year: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Get historical round-level scoring and strokes gained

        Args:
            tour: Tour code
            event_id: Event ID from events list
            year: Calendar year

        Returns:
            DataFrame with flattened round-level data including SG metrics
        """
        params = {'tour': tour}
        if event_id:
            params['event_id'] = event_id
        if year:
            params['year'] = year

        data = self._make_request("historical-raw-data/rounds", params)

        # Handle nested structure: scores -> [player] -> round_1, round_2, etc.
        if 'scores' not in data:
            return pd.DataFrame()

        rows = []
        event_info = {
            'event_id': data.get('event_id'),
            'event_name': data.get('event_name'),
            'event_completed': data.get('event_completed')
        }

        for player in data['scores']:
            player_info = {
                'dg_id': player.get('dg_id'),
                'player_name': player.get('player_name'),
                'fin_text': player.get('fin_text')
            }

            # Extract each round's data
            for round_num in range(1, 5):
                round_key = f'round_{round_num}'
                if round_key in player:
                    round_data = player[round_key]
                    row = {**event_info, **player_info, 'round_num': round_num}
                    row.update(round_data)
                    rows.append(row)

        return pd.DataFrame(rows)

    def get_historical_event_summary(
        self,
        tour: str = "pga",
        event_id: Optional[str] = None,
        year: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Get tournament-level summary with aggregated SG stats per player

        Returns:
            DataFrame with one row per player per tournament
        """
        params = {'tour': tour}
        if event_id:
            params['event_id'] = event_id
        if year:
            params['year'] = year

        data = self._make_request("historical-raw-data/rounds", params)

        if 'scores' not in data:
            return pd.DataFrame()

        rows = []
        event_info = {
            'event_id': data.get('event_id'),
            'event_name': data.get('event_name'),
            'event_completed': data.get('event_completed')
        }

        for player in data['scores']:
            row = {**event_info}
            row['dg_id'] = player.get('dg_id')
            row['player_name'] = player.get('player_name')
            row['fin_text'] = player.get('fin_text')

            # Aggregate stats across rounds
            rounds_played = 0
            sg_totals = {'sg_ott': 0, 'sg_app': 0, 'sg_arg': 0, 'sg_putt': 0, 'sg_total': 0, 'sg_t2g': 0}
            total_score = 0
            total_par = 0

            for round_num in range(1, 5):
                round_key = f'round_{round_num}'
                if round_key in player and player[round_key]:
                    rd = player[round_key]
                    rounds_played += 1
                    total_score += rd.get('score', 0)
                    total_par += rd.get('course_par', 72)

                    for sg_key in sg_totals:
                        if sg_key in rd and rd[sg_key] is not None:
                            sg_totals[sg_key] += rd[sg_key]

            row['rounds_played'] = rounds_played
            row['total_score'] = total_score
            row['total_par'] = total_par
            row['score_vs_par'] = total_score - total_par

            # Store totals and per-round averages
            for sg_key, total in sg_totals.items():
                row[f'{sg_key}_total'] = total
                row[f'{sg_key}_avg'] = total / rounds_played if rounds_played > 0 else 0

            rows.append(row)

        return pd.DataFrame(rows)
    
    # ==================== BETTING TOOLS ====================
    
    def get_outright_odds(
        self,
        tour: str = "pga",
        market: str = "win",
        odds_format: str = "decimal"
    ) -> pd.DataFrame:
        """
        Get outright betting odds from multiple books
        
        Args:
            market: 'win', 'top_5', 'top_10', 'top_20', 'mc', 'make_cut', 'frl'
        """
        params = {
            'tour': tour,
            'market': market,
            'odds_format': odds_format
        }
        data = self._make_request("betting-tools/outrights", params)
        return pd.DataFrame(data.get('outrights', []))
    
    def get_matchup_odds(
        self,
        tour: str = "pga",
        market: str = "tournament_matchups",
        odds_format: str = "decimal"
    ) -> pd.DataFrame:
        """
        Get head-to-head matchup odds
        
        Args:
            market: 'tournament_matchups', 'round_matchups', '3_balls'
        """
        params = {
            'tour': tour,
            'market': market,
            'odds_format': odds_format
        }
        data = self._make_request("betting-tools/matchups", params)
        return pd.DataFrame(data.get('matchups', []))


def create_client(api_key: str) -> DataGolfClient:
    """Factory function to create DataGolf client"""
    return DataGolfClient(api_key)
