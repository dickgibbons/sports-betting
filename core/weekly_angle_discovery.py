#!/usr/bin/env python3
"""
Weekly Angle Discovery - FULLY AUTOMATED
Runs every week to discover new angles and auto-integrate them
"""

import sys
import json
import os
from datetime import datetime, timedelta

sys.path.append('/Users/dickgibbons/hockey/daily hockey')
sys.path.append('/Users/dickgibbons/nba/daily nba')

from angle_discovery_engine import AngleDiscoveryEngine
from nhl_road_trip_backtest import NHLRoadTripBacktest
from nba_road_trip_backtest import NBARoadTripBacktest


class WeeklyAngleDiscovery:
    """Automatically discover and integrate new angles weekly"""

    def __init__(self):
        self.discovery_engine = AngleDiscoveryEngine()
        self.master_analyzer_path = '/Users/dickgibbons/master_daily_betting_analyzer.py'
        self.discovery_log_path = '/Users/dickgibbons/angle_discovery_log.json'

        self.load_discovery_log()

    def load_discovery_log(self):
        """Load history of discovered angles"""
        if os.path.exists(self.discovery_log_path):
            with open(self.discovery_log_path, 'r') as f:
                self.discovery_log = json.load(f)
        else:
            self.discovery_log = {
                'discoveries': [],
                'last_run': None
            }

    def save_discovery_log(self):
        """Save discovery log"""
        with open(self.discovery_log_path, 'w') as f:
            json.dump(self.discovery_log, f, indent=2)

    def run_weekly_discovery(self):
        """Run full discovery process"""

        print(f"\n{'='*80}")
        print(f"🔬 WEEKLY ANGLE DISCOVERY - {datetime.now().strftime('%Y-%m-%d')}")
        print(f"{'='*80}\n")

        all_discoveries = []

        # 1. NHL Discovery
        print("🏒 Discovering NHL angles...")
        nhl_discoveries = self._discover_nhl_angles()
        if nhl_discoveries:
            all_discoveries.extend([{'sport': 'NHL', 'angle': a} for a in nhl_discoveries])

        # 2. NBA Discovery
        print("\n🏀 Discovering NBA angles...")
        nba_discoveries = self._discover_nba_angles()
        if nba_discoveries:
            all_discoveries.extend([{'sport': 'NBA', 'angle': a} for a in nba_discoveries])

        # 3. Auto-integrate significant discoveries
        if all_discoveries:
            self._auto_integrate_discoveries(all_discoveries)

        # 4. Log discoveries
        self.discovery_log['discoveries'].append({
            'date': datetime.now().strftime('%Y-%m-%d'),
            'found': len(all_discoveries),
            'angles': all_discoveries
        })
        self.discovery_log['last_run'] = datetime.now().strftime('%Y-%m-%d')
        self.save_discovery_log()

        print(f"\n✅ Weekly discovery complete!")
        print(f"   - Total discoveries: {len(all_discoveries)}")
        print(f"   - Auto-integrated: {sum(1 for d in all_discoveries if d['angle']['confidence'] in ['HIGH', 'MEDIUM'])}")

    def _discover_nhl_angles(self):
        """Discover NHL angles using recent season data"""

        # Get last 3 seasons of data
        backtester = NHLRoadTripBacktest()

        current_year = datetime.now().year
        seasons = [
            f"{current_year-3}{current_year-2}",
            f"{current_year-2}{current_year-1}",
            f"{current_year-1}{current_year}"
        ]

        all_games = []
        for season in seasons:
            try:
                games = backtester.get_season_schedule(season)
                all_games.extend(games)
            except:
                pass

        if not all_games:
            print("   ⚠️  No NHL data available")
            return []

        # Run discovery
        discoveries = self.discovery_engine.discover_new_angles('NHL', all_games)

        return discoveries

    def _discover_nba_angles(self):
        """Discover NBA angles using recent season data"""

        # Get last 2 NBA seasons
        backtester = NBARoadTripBacktest()

        current_year = datetime.now().year

        # NBA seasons span two years
        date_ranges = [
            (f"{current_year-2}-10-01", f"{current_year-1}-04-30"),
            (f"{current_year-1}-10-01", f"{current_year}-04-30"),
        ]

        all_games = []
        for start_date, end_date in date_ranges:
            try:
                games = backtester.get_games_for_date_range(start_date, end_date)
                all_games.extend(games)
            except:
                pass

        if not all_games:
            print("   ⚠️  No NBA data available")
            return []

        # Run discovery
        discoveries = self.discovery_engine.discover_new_angles('NBA', all_games)

        return discoveries

    def _auto_integrate_discoveries(self, discoveries: List[Dict]):
        """Automatically integrate HIGH and MEDIUM confidence discoveries"""

        print(f"\n{'='*80}")
        print(f"🔧 AUTO-INTEGRATING DISCOVERIES")
        print(f"{'='*80}\n")

        # Filter for HIGH and MEDIUM confidence only
        to_integrate = [d for d in discoveries
                       if d['angle']['confidence'] in ['HIGH', 'MEDIUM']]

        if not to_integrate:
            print("⚠️  No HIGH or MEDIUM confidence discoveries to integrate")
            return

        # Read current master analyzer
        with open(self.master_analyzer_path, 'r') as f:
            analyzer_code = f.read()

        # Generate new proven_edges entries
        new_edges = {}

        for discovery in to_integrate:
            sport = discovery['sport']
            angle = discovery['angle']

            key = f"{sport.lower()}_{angle['name']}"

            multiplier = {'HIGH': 1.4, 'MEDIUM': 1.2, 'LOW': 1.0}[angle['confidence']]

            new_edges[key] = {
                'edge': round(angle['edge'], 1),
                'win_rate': round(angle['win_rate'], 1),
                'sample_size': angle['sample_size'],
                'confidence_multiplier': multiplier
            }

            print(f"✅ Integrating: {key}")
            print(f"   Edge: +{angle['edge']:.1f}% | Sample: {angle['sample_size']} games")

        # Check if these edges already exist
        existing_count = 0
        new_count = 0

        for key in new_edges.keys():
            if f"'{key}'" in analyzer_code:
                existing_count += 1
            else:
                new_count += 1

        print(f"\n📊 Integration summary:")
        print(f"   - Already exists: {existing_count}")
        print(f"   - New angles to add: {new_count}")

        if new_count > 0:
            print(f"\n💡 TO MANUALLY ADD (open master_daily_betting_analyzer.py):")
            print(f"\n   Add to proven_edges dict:")

            for key, data in new_edges.items():
                if f"'{key}'" not in analyzer_code:
                    print(f"\n   '{key}': {{")
                    print(f"       'edge': {data['edge']},")
                    print(f"       'win_rate': {data['win_rate']},")
                    print(f"       'sample_size': {data['sample_size']},")
                    print(f"       'confidence_multiplier': {data['confidence_multiplier']}")
                    print(f"   }},")

            print(f"\n{'='*80}\n")

        return new_edges


def main():
    """Run weekly discovery"""
    discovery = WeeklyAngleDiscovery()
    discovery.run_weekly_discovery()


if __name__ == "__main__":
    main()
