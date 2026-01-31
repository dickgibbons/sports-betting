"""
Data Collection Script for PGA Tour Prediction Model
Pulls historical and current data from DataGolf API
"""

import os
import sys
import pandas as pd
from datetime import datetime
import time
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.datagolf_client import DataGolfClient


class PGADataCollector:
    """Collects and organizes PGA Tour data for modeling"""
    
    def __init__(self, api_key: str, data_dir: str = "data/raw"):
        self.client = DataGolfClient(api_key)
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
    def save_data(self, df: pd.DataFrame, filename: str):
        """Save dataframe to CSV"""
        filepath = os.path.join(self.data_dir, filename)
        df.to_csv(filepath, index=False)
        print(f"Saved: {filepath} ({len(df)} rows)")
        return filepath
    
    # ==================== COLLECT CORE DATA ====================
    
    def collect_player_list(self) -> pd.DataFrame:
        """Collect master player list"""
        print("Collecting player list...")
        df = self.client.get_player_list()
        self.save_data(df, "players.csv")
        return df
    
    def collect_rankings(self) -> pd.DataFrame:
        """Collect current DataGolf rankings"""
        print("Collecting DG rankings...")
        df = self.client.get_dg_rankings()
        df['snapshot_date'] = datetime.now().strftime('%Y-%m-%d')
        self.save_data(df, "dg_rankings.csv")
        return df
    
    def collect_skill_ratings(self) -> pd.DataFrame:
        """Collect player skill ratings"""
        print("Collecting skill ratings...")
        df = self.client.get_player_skill_ratings(display="value")
        df['snapshot_date'] = datetime.now().strftime('%Y-%m-%d')
        self.save_data(df, "skill_ratings.csv")
        return df
    
    def collect_skill_decompositions(self) -> pd.DataFrame:
        """Collect skill decompositions by category"""
        print("Collecting skill decompositions...")
        df = self.client.get_player_skill_decompositions()
        df['snapshot_date'] = datetime.now().strftime('%Y-%m-%d')
        self.save_data(df, "skill_decompositions.csv")
        return df
    
    def collect_approach_skill(self) -> pd.DataFrame:
        """Collect detailed approach skill by yardage"""
        print("Collecting approach skill data...")
        df = self.client.get_detailed_approach_skill(period="l24")
        df['snapshot_date'] = datetime.now().strftime('%Y-%m-%d')
        self.save_data(df, "approach_skill.csv")
        return df
    
    def collect_schedule(self, tour: str = "pga", season: int = 2025) -> pd.DataFrame:
        """Collect tournament schedule"""
        print(f"Collecting {tour.upper()} schedule for {season}...")
        df = self.client.get_tour_schedule(tour=tour, season=season)
        self.save_data(df, f"schedule_{tour}_{season}.csv")
        return df
    
    # ==================== COLLECT HISTORICAL DATA ====================
    
    def collect_historical_events_list(self) -> pd.DataFrame:
        """Get list of all available historical events"""
        print("Collecting historical events list...")
        df = self.client.get_historical_events_list()
        self.save_data(df, "historical_events.csv")
        return df
    
    def collect_historical_rounds(
        self, 
        tour: str = "pga",
        years: list = None,
        delay: float = 1.0
    ) -> pd.DataFrame:
        """
        Collect historical round-level data for multiple years
        
        Args:
            tour: Tour code
            years: List of years to collect
            delay: Seconds between API calls
        """
        if years is None:
            years = list(range(2017, 2025))
        
        all_rounds = []
        
        for year in years:
            print(f"Collecting {tour.upper()} rounds for {year}...")
            try:
                df = self.client.get_historical_round_scoring(tour=tour, year=year)
                df['year'] = year
                all_rounds.append(df)
                time.sleep(delay)  # Rate limiting
            except Exception as e:
                print(f"  Error for {year}: {e}")
                continue
        
        if all_rounds:
            combined = pd.concat(all_rounds, ignore_index=True)
            self.save_data(combined, f"historical_rounds_{tour}.csv")
            return combined
        return pd.DataFrame()
    
    def collect_prediction_archive(
        self,
        years: list = None,
        delay: float = 1.0
    ) -> pd.DataFrame:
        """
        Collect historical pre-tournament predictions
        Useful for backtesting model against DataGolf
        """
        if years is None:
            years = list(range(2020, 2025))
        
        # First get events list to know event IDs
        events_df = self.collect_historical_events_list()
        
        all_preds = []
        
        for year in years:
            year_events = events_df[events_df['calendar_year'] == year]
            print(f"Collecting predictions for {year} ({len(year_events)} events)...")
            
            for _, event in year_events.iterrows():
                try:
                    df = self.client.get_pre_tournament_archive(
                        event_id=event.get('event_id'),
                        year=year
                    )
                    if not df.empty:
                        df['event_id'] = event.get('event_id')
                        df['event_name'] = event.get('event_name', '')
                        df['year'] = year
                        all_preds.append(df)
                    time.sleep(delay)
                except Exception as e:
                    print(f"  Error for {event.get('event_name', 'Unknown')}: {e}")
                    continue
        
        if all_preds:
            combined = pd.concat(all_preds, ignore_index=True)
            self.save_data(combined, "prediction_archive.csv")
            return combined
        return pd.DataFrame()
    
    # ==================== COLLECT CURRENT TOURNAMENT ====================
    
    def collect_current_field(self, tour: str = "pga") -> pd.DataFrame:
        """Collect current tournament field"""
        print(f"Collecting current {tour.upper()} field...")
        df = self.client.get_field_updates(tour=tour)
        df['snapshot_date'] = datetime.now().strftime('%Y-%m-%d')
        self.save_data(df, f"current_field_{tour}.csv")
        return df
    
    def collect_current_predictions(self, tour: str = "pga") -> pd.DataFrame:
        """Collect predictions for upcoming tournament"""
        print(f"Collecting predictions for upcoming {tour.upper()} event...")
        df = self.client.get_pre_tournament_predictions(tour=tour)
        df['snapshot_date'] = datetime.now().strftime('%Y-%m-%d')
        self.save_data(df, f"current_predictions_{tour}.csv")
        return df
    
    def collect_current_odds(self, tour: str = "pga") -> dict:
        """Collect current betting odds for all markets"""
        print(f"Collecting betting odds for {tour.upper()}...")
        
        odds_data = {}
        markets = ['win', 'top_5', 'top_10', 'top_20', 'make_cut']
        
        for market in markets:
            try:
                df = self.client.get_outright_odds(tour=tour, market=market)
                df['market'] = market
                df['snapshot_date'] = datetime.now().strftime('%Y-%m-%d')
                odds_data[market] = df
                time.sleep(0.5)
            except Exception as e:
                print(f"  Error for {market}: {e}")
        
        # Combine all odds
        if odds_data:
            combined = pd.concat(odds_data.values(), ignore_index=True)
            self.save_data(combined, f"current_odds_{tour}.csv")
        
        return odds_data
    
    # ==================== FULL COLLECTION ====================
    
    def collect_all_current(self, tour: str = "pga"):
        """Collect all current/snapshot data"""
        print("=" * 50)
        print("COLLECTING CURRENT DATA")
        print("=" * 50)

        self.collect_player_list()
        self.collect_rankings()

        # These endpoints may require premium API access
        try:
            self.collect_skill_ratings()
        except Exception as e:
            print(f"  Skipping skill_ratings (may require premium): {e}")

        try:
            self.collect_skill_decompositions()
        except Exception as e:
            print(f"  Skipping skill_decompositions (may require premium): {e}")

        try:
            self.collect_approach_skill()
        except Exception as e:
            print(f"  Skipping approach_skill (may require premium): {e}")

        try:
            self.collect_schedule(tour=tour, season=2025)
        except Exception as e:
            print(f"  Skipping schedule: {e}")

        try:
            self.collect_current_field(tour=tour)
        except Exception as e:
            print(f"  Skipping current_field: {e}")

        try:
            self.collect_current_predictions(tour=tour)
        except Exception as e:
            print(f"  Skipping current_predictions: {e}")

        try:
            self.collect_current_odds(tour=tour)
        except Exception as e:
            print(f"  Skipping current_odds: {e}")

        print("\nCurrent data collection complete!")
    
    def collect_all_historical(self, tour: str = "pga", years: list = None):
        """Collect all historical data"""
        print("=" * 50)
        print("COLLECTING HISTORICAL DATA")
        print("=" * 50)
        
        if years is None:
            years = list(range(2017, 2025))
        
        self.collect_historical_events_list()
        self.collect_historical_rounds(tour=tour, years=years)
        
        # Prediction archive takes longer - optional
        # self.collect_prediction_archive(years=years)
        
        print("\nHistorical data collection complete!")
    
    def collect_everything(self, tour: str = "pga"):
        """Full data collection"""
        self.collect_all_current(tour)
        self.collect_all_historical(tour)
        print("\n" + "=" * 50)
        print("ALL DATA COLLECTION COMPLETE")
        print("=" * 50)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Collect PGA Tour data from DataGolf')
    parser.add_argument('--api-key', required=True, help='DataGolf API key')
    parser.add_argument('--mode', choices=['current', 'historical', 'all'], 
                        default='current', help='Collection mode')
    parser.add_argument('--tour', default='pga', help='Tour (pga, euro, kft)')
    parser.add_argument('--data-dir', default='data/raw', help='Output directory')
    
    args = parser.parse_args()
    
    collector = PGADataCollector(args.api_key, args.data_dir)
    
    if args.mode == 'current':
        collector.collect_all_current(args.tour)
    elif args.mode == 'historical':
        collector.collect_all_historical(args.tour)
    else:
        collector.collect_everything(args.tour)


if __name__ == "__main__":
    main()
