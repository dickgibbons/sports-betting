#!/usr/bin/env python3
"""
Validate and clean fixture data by removing impossible matches
"""

import pandas as pd
import os
from datetime import datetime

def validate_fixture_data():
    """Remove obviously incorrect fixture data"""
    
    print("🔍 VALIDATING AND CLEANING FIXTURE DATA")
    print("=" * 50)
    
    # Known impossible fixtures for early September 2025
    impossible_fixtures = [
        ("Barcelona", "Girona"),  # Would not play during this period
        # Add other known impossible fixtures here
    ]
    
    # Find all daily picks files
    import glob
    picks_files = glob.glob("output reports/daily_picks_*.csv")
    picks_files.extend(glob.glob("output reports/Older/daily_picks_*.csv"))
    
    print(f"📋 Checking {len(picks_files)} daily picks files")
    
    for picks_file in picks_files:
        try:
            print(f"\n📅 Checking: {picks_file}")
            
            df = pd.read_csv(picks_file)
            if df.empty:
                continue
                
            original_count = len(df)
            
            # Remove impossible fixtures
            for home_team, away_team in impossible_fixtures:
                mask = ~((df['home_team'] == home_team) & (df['away_team'] == away_team))
                df = df[mask]
            
            # Remove fixtures with very high impossible odds (likely errors)
            df = df[df['odds'] <= 20.0]  # Remove odds over 20.0 as likely errors
            
            # Remove fixtures with impossible edge percentages
            if 'edge_percent' in df.columns:
                df = df[df['edge_percent'] <= 300.0]  # Cap edge at 300%
            
            cleaned_count = len(df)
            removed_count = original_count - cleaned_count
            
            if removed_count > 0:
                print(f"   🧹 Removed {removed_count} suspect fixtures")
                # Save cleaned file
                df.to_csv(picks_file, index=False)
                print(f"   ✅ Cleaned file saved")
            else:
                print(f"   ✅ No issues found")
                
        except Exception as e:
            print(f"   ❌ Error processing {picks_file}: {e}")
    
    print(f"\n✅ VALIDATION COMPLETE")

def create_realistic_top8_tracker():
    """Create a top 8 tracker with only realistic data"""
    
    print("\n🏆 CREATING REALISTIC TOP 8 TRACKER")
    print("=" * 50)
    
    # Use only verified recent dates with realistic fixtures
    verified_files = {
        "output reports/daily_picks_20250913.csv": "2025-09-13",  # Today's actual picks
        # Add other verified files here as they're confirmed
    }
    
    columns = [
        'date', 'kick_off', 'home_team', 'away_team', 'league', 'market', 
        'bet_description', 'odds', 'recommended_stake_pct', 'edge_percent', 
        'confidence_percent', 'expected_value', 'quality_score', 'risk_level',
        'country', 'bet_amount', 'potential_win', 'actual_pnl', 'running_total', 
        'running_bankroll', 'cumulative_wins', 'cumulative_picks', 'win_rate', 
        'outcome_description'
    ]
    
    realistic_tracker = pd.DataFrame(columns=columns)
    
    running_total = 0
    running_bankroll = 1000
    cumulative_wins = 0
    cumulative_picks = 0
    
    print(f"📋 Processing {len(verified_files)} verified files")
    
    for file_path, date_str in verified_files.items():
        if not os.path.exists(file_path):
            print(f"   ⚠️ File not found: {file_path}")
            continue
            
        print(f"📅 Processing verified file: {file_path}")
        
        try:
            daily_picks = pd.read_csv(file_path)
            
            if daily_picks.empty:
                print(f"   ⚠️ No picks in file")
                continue
            
            # Get top picks by quality score
            if 'quality_score' in daily_picks.columns:
                top_picks = daily_picks.nlargest(min(8, len(daily_picks)), 'quality_score')
            else:
                top_picks = daily_picks.head(min(8, len(daily_picks)))
            
            print(f"   ✅ Selected {len(top_picks)} top picks")
            
            # Process each pick with pending status (since these are future/current bets)
            for idx, pick in top_picks.iterrows():
                cumulative_picks += 1
                
                bet_amount = running_bankroll * 0.08
                potential_win = bet_amount * pick.get('odds', 1.0)
                
                # For current/future bets, mark as pending
                actual_pnl = 0  # Will be updated when results are known
                outcome = "PENDING"
                
                win_rate = (cumulative_wins / cumulative_picks) * 100 if cumulative_picks > 0 else 0
                
                record = {
                    'date': date_str,
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
                    'actual_pnl': actual_pnl,
                    'running_total': round(running_total, 2),
                    'running_bankroll': round(running_bankroll, 2),
                    'cumulative_wins': cumulative_wins,
                    'cumulative_picks': cumulative_picks,
                    'win_rate': round(win_rate, 1),
                    'outcome_description': outcome
                }
                
                realistic_tracker = pd.concat([realistic_tracker, pd.DataFrame([record])], ignore_index=True)
        
        except Exception as e:
            print(f"   ❌ Error processing {file_path}: {e}")
    
    # Save realistic tracker
    output_file = "output reports/top8_daily_tracker_realistic.csv"
    realistic_tracker.to_csv(output_file, index=False)
    
    print(f"\n✅ REALISTIC TRACKER CREATED")
    print(f"📊 Total verified picks: {cumulative_picks}")
    print(f"💾 Saved to: {output_file}")
    
    # Replace the main tracker with realistic one
    backup_file = "output reports/top8_daily_tracker_old.csv"
    if os.path.exists("output reports/top8_daily_tracker.csv"):
        os.rename("output reports/top8_daily_tracker.csv", backup_file)
        print(f"📦 Old tracker backed up to: {backup_file}")
    
    os.rename(output_file, "output reports/top8_daily_tracker.csv")
    print(f"🔄 Realistic tracker is now active")

if __name__ == "__main__":
    validate_fixture_data()
    create_realistic_top8_tracker()