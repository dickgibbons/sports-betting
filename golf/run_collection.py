#!/usr/bin/env python
"""
Quick Start Script - Run data collection with config-based API key
Usage: python run_collection.py [current|historical|all]
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from configs.config import DATAGOLF_API_KEY
from scripts.collect_data import PGADataCollector


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "current"
    
    if DATAGOLF_API_KEY == "YOUR_API_KEY_HERE":
        print("Error: Please set your API key in configs/config.py")
        sys.exit(1)
    
    collector = PGADataCollector(
        api_key=DATAGOLF_API_KEY,
        data_dir=os.path.join(project_root, "data", "raw")
    )
    
    if mode == "current":
        print("Collecting current tournament data...")
        collector.collect_all_current("pga")
    elif mode == "historical":
        print("Collecting historical data (this may take a while)...")
        collector.collect_all_historical("pga", years=list(range(2017, 2025)))
    elif mode == "all":
        print("Collecting all data...")
        collector.collect_everything("pga")
    elif mode == "test":
        print("Running quick API test...")
        from scripts.datagolf_client import DataGolfClient
        client = DataGolfClient(DATAGOLF_API_KEY)
        df = client.get_dg_rankings()
        print(f"Success! Top 10 DG Rankings:")
        print(df[['player_name', 'dg_skill_estimate', 'owgr_rank']].head(10).to_string(index=False))
    else:
        print(f"Unknown mode: {mode}")
        print("Usage: python run_collection.py [current|historical|all|test]")
        sys.exit(1)


if __name__ == "__main__":
    main()
