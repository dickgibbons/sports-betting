#!/usr/bin/env python3
"""
Quick Performance Dashboard - Show betting performance by sport
"""

import sys
sys.path.insert(0, '/Users/dickgibbons/AI Projects/sports-betting/core')

from bet_tracker import BetTracker

def main():
    """Display performance dashboard"""
    tracker = BetTracker()
    tracker.display_dashboard()

if __name__ == '__main__':
    main()
