#!/usr/bin/env python3
"""
Rebuild the top 8 tracker with historical data but fix data quality issues
"""

import pandas as pd
import os
import glob
from datetime import datetime
import random

def rebuild_comprehensive_top8_tracker():
    """Rebuild tracker with all historical data but fix obvious errors"""
    
    print("🔧 REBUILDING COMPREHENSIVE TOP 8 TRACKER")
    print("=" * 50)
    
    # Restore the backed up tracker first
    if os.path.exists("output reports/top8_daily_tracker_backup.csv"):
        print("📦 Found backup tracker, using as base...")
        base_tracker = pd.read_csv("output reports/top8_daily_tracker_backup.csv")
        print(f"   📊 Backup contains {len(base_tracker)} records")
        
        # Fix obvious data quality issues
        print("🧹 Fixing data quality issues...")
        
        # Fix impossible fixtures
        impossible_fixtures = [
            ("Barcelona", "Girona", "2025-09-07"),  # This specific combination on this date
        ]
        
        for home, away, bad_date in impossible_fixtures:
            mask = ~((base_tracker['home_team'] == home) & 
                    (base_tracker['away_team'] == away) & 
                    (base_tracker['date'] == bad_date))
            before_count = len(base_tracker)
            base_tracker = base_tracker[mask]
            after_count = len(base_tracker)
            if before_count != after_count:
                print(f"   ❌ Removed {before_count - after_count} impossible fixture: {home} vs {away} on {bad_date}")
        
        # Fix extreme outliers
        original_count = len(base_tracker)
        
        # Cap unrealistic odds
        base_tracker = base_tracker[base_tracker['odds'] <= 15.0]
        
        # Cap unrealistic edges
        if 'edge_percent' in base_tracker.columns:
            base_tracker = base_tracker[base_tracker['edge_percent'] <= 200.0]
        
        # Cap unrealistic confidence
        if 'confidence_percent' in base_tracker.columns:
            base_tracker = base_tracker[base_tracker['confidence_percent'] <= 95.0]
        
        cleaned_count = len(base_tracker)
        if original_count != cleaned_count:
            print(f"   🧹 Removed {original_count - cleaned_count} outlier records")
        
        # Recalculate running totals to ensure consistency
        print("🔢 Recalculating running totals...")
        base_tracker = base_tracker.sort_values(['date', 'kick_off']).reset_index(drop=True)
        
        running_total = 0
        running_bankroll = 1000
        cumulative_wins = 0
        
        for idx in range(len(base_tracker)):
            # Recalculate P&L if outcome is known
            if base_tracker.loc[idx, 'outcome_description'] in ['WIN', 'LOSS']:
                bet_amount = base_tracker.loc[idx, 'bet_amount']
                odds = base_tracker.loc[idx, 'odds']
                
                if base_tracker.loc[idx, 'outcome_description'] == 'WIN':
                    pnl = (bet_amount * odds) - bet_amount
                    cumulative_wins += 1
                else:
                    pnl = -bet_amount
                
                running_total += pnl
                running_bankroll += pnl
                
                # Update the record
                base_tracker.loc[idx, 'actual_pnl'] = round(pnl, 2)
                base_tracker.loc[idx, 'running_total'] = round(running_total, 2)
                base_tracker.loc[idx, 'running_bankroll'] = round(running_bankroll, 2)
                base_tracker.loc[idx, 'cumulative_wins'] = cumulative_wins
                base_tracker.loc[idx, 'cumulative_picks'] = idx + 1
                base_tracker.loc[idx, 'win_rate'] = round((cumulative_wins / (idx + 1)) * 100, 1)
        
        print(f"✅ Recalculated running totals")
        print(f"📊 Final stats: {cumulative_wins} wins out of {len(base_tracker)} picks")
        
    else:
        print("⚠️ No backup found, creating fresh tracker...")
        base_tracker = pd.DataFrame()
    
    # Add new verified picks from September 13th
    print("➕ Adding today's verified picks...")
    today_file = "output reports/daily_picks_20250913.csv"
    if os.path.exists(today_file):
        today_picks = pd.read_csv(today_file)
        
        # Get top picks
        if 'quality_score' in today_picks.columns:
            top_today = today_picks.nlargest(4, 'quality_score')
        else:
            top_today = today_picks.head(4)
        
        # Add these as pending picks
        for idx, pick in top_today.iterrows():
            current_picks = len(base_tracker)
            current_bankroll = base_tracker['running_bankroll'].iloc[-1] if len(base_tracker) > 0 else 1000
            
            bet_amount = current_bankroll * 0.08
            potential_win = bet_amount * pick.get('odds', 1.0)
            
            new_record = {
                'date': '2025-09-13',
                'kick_off': pick.get('kick_off', ''),
                'home_team': pick.get('home_team', ''),
                'away_team': pick.get('away_team', ''),
                'league': pick.get('league', ''),
                'market': pick.get('market', ''),
                'bet_description': pick.get('bet_description', ''),
                'odds': pick.get('odds', 0),
                'recommended_stake_pct': pick.get('recommended_stake_pct', 8.0),
                'edge_percent': pick.get('edge_percent', 0),
                'confidence_percent': pick.get('confidence_percent', 0),
                'expected_value': pick.get('expected_value', 0),
                'quality_score': pick.get('quality_score', 0),
                'risk_level': pick.get('risk_level', 'Medium Risk'),
                'country': pick.get('country', ''),
                'bet_amount': round(bet_amount, 2),
                'potential_win': round(potential_win, 2),
                'simulated_outcome': False,  # Will be updated when results are known
                'actual_pnl': 0,
                'running_total': base_tracker['running_total'].iloc[-1] if len(base_tracker) > 0 else 0,
                'running_bankroll': round(current_bankroll, 2),
                'cumulative_wins': base_tracker['cumulative_wins'].iloc[-1] if len(base_tracker) > 0 else 0,
                'cumulative_picks': current_picks + 1,
                'win_rate': base_tracker['win_rate'].iloc[-1] if len(base_tracker) > 0 else 0,
                'outcome_description': 'PENDING'
            }
            
            base_tracker = pd.concat([base_tracker, pd.DataFrame([new_record])], ignore_index=True)
        
        print(f"   ✅ Added {len(top_today)} picks from today")
    
    # Save the rebuilt tracker
    output_file = "output reports/top8_daily_tracker.csv"
    base_tracker.to_csv(output_file, index=False)
    
    print(f"\n✅ COMPREHENSIVE TRACKER REBUILT")
    print(f"📊 Total records: {len(base_tracker)}")
    print(f"💾 Saved to: {output_file}")
    
    # Show summary stats
    if len(base_tracker) > 0:
        completed_picks = base_tracker[base_tracker['outcome_description'].isin(['WIN', 'LOSS'])]
        pending_picks = base_tracker[base_tracker['outcome_description'] == 'PENDING']
        
        print(f"\n📈 SUMMARY:")
        print(f"   Completed bets: {len(completed_picks)}")
        print(f"   Pending bets: {len(pending_picks)}")
        if len(completed_picks) > 0:
            wins = len(completed_picks[completed_picks['outcome_description'] == 'WIN'])
            win_rate = (wins / len(completed_picks)) * 100
            print(f"   Historical win rate: {win_rate:.1f}%")
            print(f"   Final P&L: ${completed_picks['running_total'].iloc[-1]:.2f}")

if __name__ == "__main__":
    rebuild_comprehensive_top8_tracker()