#!/usr/bin/env python3
"""
Quick Bet Results Updater
Simple script to update bet results quickly
"""

from bet_tracker import BetTracker
import sys


def main():
    tracker = BetTracker()

    # Show pending bets
    tracker.list_pending_bets()

    if len(sys.argv) > 1:
        # Command line mode: python3 update_results.py BET_ID WIN/LOSS
        bet_id = sys.argv[1]
        result = sys.argv[2].upper() if len(sys.argv) > 2 else None

        if result and result in ['WIN', 'LOSS', 'PUSH']:
            tracker.update_result(bet_id, result)
        else:
            print("❌ Usage: python3 update_results.py BET_ID WIN/LOSS/PUSH")

    else:
        # Interactive mode
        while True:
            bet_id = input("\nEnter bet ID (or 'done' to finish, 'show' to see dashboard): ").strip()

            if bet_id.lower() == 'done':
                break
            elif bet_id.lower() == 'show':
                tracker.display_dashboard()
                continue

            result = input("Result (WIN/LOSS/PUSH): ").strip().upper()

            if result in ['WIN', 'LOSS', 'PUSH']:
                tracker.update_result(bet_id, result)
            else:
                print("❌ Invalid result. Use WIN, LOSS, or PUSH")

        # Show updated dashboard
        print("\n")
        tracker.display_dashboard()


if __name__ == "__main__":
    main()
