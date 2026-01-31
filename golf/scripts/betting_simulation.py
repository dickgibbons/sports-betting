"""
PGA Tour Betting Simulation
Simulates $25 bets on our top 5 predicted players per tournament.
Bet types: Outright Winner, Top 5, Top 10
Uses realistic odds based on predicted rank and field size.
"""

import sys
import os
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Add parent directory for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, script_dir)
sys.path.insert(0, parent_dir)


@dataclass
class Bet:
    """Single bet record"""
    event_id: int
    event_name: str
    event_date: str
    month: str
    player_id: int
    player_name: str
    predicted_rank: int
    actual_finish: int
    bet_type: str  # 'win', 'top5', 'top10'
    odds: float  # American odds
    stake: float
    payout: float
    profit: float
    won: bool


class OddsSimulator:
    """Simulates realistic betting odds based on player predicted rank"""

    def __init__(self, field_size: int = 150):
        self.field_size = field_size

    def get_outright_odds(self, predicted_rank: int, field_size: int = None) -> float:
        """
        Generate realistic outright winner odds based on predicted rank.
        Top players: +800 to +1500
        Mid-tier: +2000 to +5000
        Lower: +6000 to +15000
        """
        if field_size is None:
            field_size = self.field_size

        if predicted_rank == 1:
            return 800  # +800 favorite
        elif predicted_rank == 2:
            return 1000
        elif predicted_rank == 3:
            return 1200
        elif predicted_rank <= 5:
            return 1500 + (predicted_rank - 4) * 200
        elif predicted_rank <= 10:
            return 2000 + (predicted_rank - 5) * 300
        elif predicted_rank <= 20:
            return 3500 + (predicted_rank - 10) * 400
        elif predicted_rank <= 30:
            return 7500 + (predicted_rank - 20) * 500
        else:
            return 12500 + (predicted_rank - 30) * 300

    def get_top5_odds(self, predicted_rank: int) -> float:
        """Top 5 finish odds - lower payouts but higher hit rate"""
        if predicted_rank == 1:
            return 150  # +150
        elif predicted_rank == 2:
            return 175
        elif predicted_rank == 3:
            return 200
        elif predicted_rank <= 5:
            return 250 + (predicted_rank - 4) * 50
        elif predicted_rank <= 10:
            return 400 + (predicted_rank - 5) * 75
        elif predicted_rank <= 20:
            return 800 + (predicted_rank - 10) * 100
        else:
            return 1800 + (predicted_rank - 20) * 150

    def get_top10_odds(self, predicted_rank: int) -> float:
        """Top 10 finish odds - most conservative"""
        if predicted_rank == 1:
            return -150  # -150 (bet $150 to win $100)
        elif predicted_rank == 2:
            return -120
        elif predicted_rank == 3:
            return 100  # Even money
        elif predicted_rank <= 5:
            return 120 + (predicted_rank - 4) * 30
        elif predicted_rank <= 10:
            return 200 + (predicted_rank - 5) * 40
        elif predicted_rank <= 20:
            return 400 + (predicted_rank - 10) * 60
        else:
            return 1000 + (predicted_rank - 20) * 80


def american_odds_to_payout(odds: float, stake: float) -> float:
    """Convert American odds to potential payout (stake + profit)"""
    if odds > 0:
        profit = stake * (odds / 100)
    else:
        profit = stake * (100 / abs(odds))
    return stake + profit


def american_odds_to_profit(odds: float, stake: float) -> float:
    """Convert American odds to profit if win"""
    if odds > 0:
        return stake * (odds / 100)
    else:
        return stake * (100 / abs(odds))


class BettingSimulator:
    """Simulates betting on PGA Tour events"""

    def __init__(
        self,
        historical_sg: pd.DataFrame,
        skill_weights: pd.DataFrame,
        stake_per_bet: float = 25.0
    ):
        self.historical_sg = historical_sg.copy()
        self.skill_weights = skill_weights
        self.stake = stake_per_bet
        self.odds_sim = OddsSimulator()

        # Prepare data
        self.historical_sg['year'] = self.historical_sg['year'].astype(int)

        # Parse finish positions
        def parse_finish(fin):
            if pd.isna(fin) or fin in ['CUT', 'WD', 'DQ', 'MDF']:
                return None
            return int(str(fin).replace('T', ''))

        self.historical_sg['finish_pos'] = self.historical_sg['fin_text'].apply(parse_finish)

        # Event dates mapping (approximate - would use actual dates in production)
        self.event_dates_2024 = {
            16: ('2024-01-04', 'January'),   # The Sentry
            6: ('2024-01-11', 'January'),    # Sony Open
            4: ('2024-01-25', 'January'),    # Farmers Insurance
            5: ('2024-02-01', 'February'),   # Pebble Beach
            3: ('2024-02-08', 'February'),   # WM Phoenix Open
            9: ('2024-03-07', 'March'),      # Arnold Palmer Invitational
            11: ('2024-03-14', 'March'),     # THE PLAYERS
            475: ('2024-03-21', 'March'),    # Valspar
            12: ('2024-04-11', 'April'),     # RBC Heritage (after Masters)
            14: ('2024-04-11', 'April'),     # Masters
            33: ('2024-05-16', 'May'),       # PGA Championship
            21: ('2024-05-23', 'May'),       # Charles Schwab
            23: ('2024-06-06', 'June'),      # Memorial
            26: ('2024-06-13', 'June'),      # US Open
            34: ('2024-06-20', 'June'),      # Travelers
            100: ('2024-07-18', 'July'),     # The Open
            27: ('2024-08-15', 'August'),    # FedEx St. Jude
            13: ('2024-08-08', 'August'),    # Wyndham
            60: ('2024-08-29', 'August'),    # Tour Championship
            493: ('2024-11-21', 'November'), # RSM Classic
        }

    def get_player_trailing_skills(
        self,
        player_id: int,
        before_year: int,
        n_events: int = 20
    ) -> Optional[Dict[str, float]]:
        """Get player's trailing SG averages"""
        mask = (
            (self.historical_sg['dg_id'] == player_id) &
            (self.historical_sg['year'] < before_year) &
            (self.historical_sg['rounds_played'] >= 2)
        )
        player_events = self.historical_sg[mask].sort_values('year', ascending=False)

        if len(player_events) < 3:
            return None

        recent = player_events.head(n_events)
        weights = np.exp(-np.arange(len(recent)) * 0.1)
        weights = weights / weights.sum()

        return {
            'sg_ott_avg': np.average(recent['sg_ott_avg'], weights=weights),
            'sg_app_avg': np.average(recent['sg_app_avg'], weights=weights),
            'sg_arg_avg': np.average(recent['sg_arg_avg'], weights=weights),
            'sg_putt_avg': np.average(recent['sg_putt_avg'], weights=weights),
        }

    def predict_tournament(
        self,
        event_id: int,
        year: int,
        field_player_ids: List[int]
    ) -> pd.DataFrame:
        """Generate predictions for a tournament"""
        weights_row = self.skill_weights[self.skill_weights['event_id'] == event_id]

        if len(weights_row) == 0:
            weights = {'sg_ott': 0.216, 'sg_app': 0.291, 'sg_arg': 0.197, 'sg_putt': 0.297}
        else:
            row = weights_row.iloc[0]
            weights = {
                'sg_ott': row['sg_ott_pct'],
                'sg_app': row['sg_app_pct'],
                'sg_arg': row['sg_arg_pct'],
                'sg_putt': row['sg_putt_pct']
            }

        predictions = []
        for player_id in field_player_ids:
            skills = self.get_player_trailing_skills(player_id, year)
            if skills is None:
                continue

            score = (
                skills['sg_ott_avg'] * weights['sg_ott'] +
                skills['sg_app_avg'] * weights['sg_app'] +
                skills['sg_arg_avg'] * weights['sg_arg'] +
                skills['sg_putt_avg'] * weights['sg_putt']
            )

            predictions.append({
                'dg_id': player_id,
                'predicted_score': score,
            })

        df = pd.DataFrame(predictions)
        df = df.sort_values('predicted_score', ascending=False)
        df['predicted_rank'] = range(1, len(df) + 1)

        return df

    def simulate_event(
        self,
        event_id: int,
        year: int = 2024,
        n_picks: int = 5
    ) -> List[Bet]:
        """Simulate betting on a single event"""

        # Get actual results
        mask = (
            (self.historical_sg['event_id'] == event_id) &
            (self.historical_sg['year'] == year)
        )
        actual_results = self.historical_sg[mask].copy()

        if len(actual_results) < 30:
            return []

        actual_results = actual_results.dropna(subset=['finish_pos'])

        if len(actual_results) < 20:
            return []

        # Get predictions
        field_ids = actual_results['dg_id'].tolist()
        predictions = self.predict_tournament(event_id, year, field_ids)

        if len(predictions) < n_picks:
            return []

        # Merge with actual results
        merged = predictions.merge(
            actual_results[['dg_id', 'finish_pos', 'player_name']],
            on='dg_id'
        )

        # Get event info
        event_name = actual_results['event_name'].iloc[0] if 'event_name' in actual_results.columns else f"Event {event_id}"
        event_date, month = self.event_dates_2024.get(event_id, ('2024-01-01', 'January'))
        field_size = len(actual_results)

        # Create bets on top N picks
        bets = []
        top_picks = merged.nsmallest(n_picks, 'predicted_rank')

        for _, row in top_picks.iterrows():
            pred_rank = int(row['predicted_rank'])
            actual_finish = int(row['finish_pos'])

            # Outright Winner Bet
            win_odds = self.odds_sim.get_outright_odds(pred_rank, field_size)
            won_outright = actual_finish == 1
            win_profit = american_odds_to_profit(win_odds, self.stake) if won_outright else -self.stake

            bets.append(Bet(
                event_id=event_id,
                event_name=event_name,
                event_date=event_date,
                month=month,
                player_id=int(row['dg_id']),
                player_name=row['player_name'],
                predicted_rank=pred_rank,
                actual_finish=actual_finish,
                bet_type='win',
                odds=win_odds,
                stake=self.stake,
                payout=self.stake + win_profit if won_outright else 0,
                profit=win_profit,
                won=won_outright
            ))

            # Top 5 Bet
            top5_odds = self.odds_sim.get_top5_odds(pred_rank)
            won_top5 = actual_finish <= 5
            top5_profit = american_odds_to_profit(top5_odds, self.stake) if won_top5 else -self.stake

            bets.append(Bet(
                event_id=event_id,
                event_name=event_name,
                event_date=event_date,
                month=month,
                player_id=int(row['dg_id']),
                player_name=row['player_name'],
                predicted_rank=pred_rank,
                actual_finish=actual_finish,
                bet_type='top5',
                odds=top5_odds,
                stake=self.stake,
                payout=self.stake + top5_profit if won_top5 else 0,
                profit=top5_profit,
                won=won_top5
            ))

            # Top 10 Bet
            top10_odds = self.odds_sim.get_top10_odds(pred_rank)
            won_top10 = actual_finish <= 10
            top10_profit = american_odds_to_profit(top10_odds, self.stake) if won_top10 else -self.stake

            bets.append(Bet(
                event_id=event_id,
                event_name=event_name,
                event_date=event_date,
                month=month,
                player_id=int(row['dg_id']),
                player_name=row['player_name'],
                predicted_rank=pred_rank,
                actual_finish=actual_finish,
                bet_type='top10',
                odds=top10_odds,
                stake=self.stake,
                payout=self.stake + top10_profit if won_top10 else 0,
                profit=top10_profit,
                won=won_top10
            ))

        return bets

    def run_season_simulation(self, year: int = 2024) -> Tuple[List[Bet], pd.DataFrame]:
        """Run simulation for an entire season"""
        all_bets = []

        # Events to simulate (in approximate order)
        events = [16, 6, 4, 5, 3, 9, 11, 475, 14, 12, 33, 21, 23, 26, 34, 100, 13, 27, 60, 493]

        for event_id in events:
            event_bets = self.simulate_event(event_id, year)
            if event_bets:
                all_bets.extend(event_bets)

        # Convert to DataFrame
        bets_df = pd.DataFrame([
            {
                'event_id': b.event_id,
                'event_name': b.event_name,
                'event_date': b.event_date,
                'month': b.month,
                'player_id': b.player_id,
                'player_name': b.player_name,
                'predicted_rank': b.predicted_rank,
                'actual_finish': b.actual_finish,
                'bet_type': b.bet_type,
                'odds': b.odds,
                'stake': b.stake,
                'payout': b.payout,
                'profit': b.profit,
                'won': b.won
            }
            for b in all_bets
        ])

        return all_bets, bets_df


def main():
    """Run betting simulation"""
    print("=" * 80)
    print("PGA TOUR 2024 SEASON BETTING SIMULATION")
    print("$25 per bet | 5 players per event | Win/Top5/Top10 markets")
    print("=" * 80)

    # Load data
    print("\nLoading data...")
    skill_weights = pd.read_csv("/Users/dickgibbons/sports-betting/PGA_Bets/data/processed/course_skill_weights.csv")
    historical_sg = pd.read_csv("/Users/dickgibbons/sports-betting/PGA_Bets/data/raw/historical_sg_data.csv")

    print(f"  Loaded {len(skill_weights)} course profiles")
    print(f"  Loaded {len(historical_sg)} player-tournament records")

    # Run simulation
    simulator = BettingSimulator(historical_sg, skill_weights, stake_per_bet=25.0)
    all_bets, bets_df = simulator.run_season_simulation(2024)

    print(f"\n  Total bets placed: {len(bets_df)}")

    # Overall Summary
    print("\n" + "=" * 80)
    print("OVERALL SEASON SUMMARY")
    print("=" * 80)

    total_stake = bets_df['stake'].sum()
    total_profit = bets_df['profit'].sum()
    total_roi = (total_profit / total_stake) * 100

    print(f"\nTotal Wagered:  ${total_stake:,.2f}")
    print(f"Total Profit:   ${total_profit:,.2f}")
    print(f"ROI:            {total_roi:+.1f}%")

    # By Bet Type
    print("\n" + "-" * 60)
    print("BY BET TYPE:")
    print("-" * 60)

    for bet_type in ['win', 'top5', 'top10']:
        type_df = bets_df[bets_df['bet_type'] == bet_type]
        stake = type_df['stake'].sum()
        profit = type_df['profit'].sum()
        wins = type_df['won'].sum()
        total = len(type_df)
        roi = (profit / stake) * 100 if stake > 0 else 0

        print(f"\n{bet_type.upper()} BETS:")
        print(f"  Bets: {total} | Wins: {wins} ({wins/total*100:.1f}%)")
        print(f"  Wagered: ${stake:,.2f} | Profit: ${profit:,.2f} | ROI: {roi:+.1f}%")

    # Monthly Breakdown
    print("\n" + "=" * 80)
    print("MONTH-BY-MONTH PROFITABILITY")
    print("=" * 80)

    months_order = ['January', 'February', 'March', 'April', 'May', 'June',
                    'July', 'August', 'September', 'October', 'November']

    monthly_results = []
    cumulative_profit = 0

    print(f"\n{'Month':<12} {'Events':>7} {'Bets':>6} {'Stake':>10} {'Profit':>12} {'ROI':>8} {'Cumulative':>12}")
    print("-" * 80)

    for month in months_order:
        month_df = bets_df[bets_df['month'] == month]
        if len(month_df) == 0:
            continue

        stake = month_df['stake'].sum()
        profit = month_df['profit'].sum()
        n_events = month_df['event_id'].nunique()
        n_bets = len(month_df)
        roi = (profit / stake) * 100 if stake > 0 else 0
        cumulative_profit += profit

        monthly_results.append({
            'month': month,
            'n_events': n_events,
            'n_bets': n_bets,
            'stake': stake,
            'profit': profit,
            'roi': roi,
            'cumulative': cumulative_profit
        })

        print(f"{month:<12} {n_events:>7} {n_bets:>6} ${stake:>8,.0f} ${profit:>+10,.2f} {roi:>+7.1f}% ${cumulative_profit:>+10,.2f}")

    # Save monthly results
    monthly_df = pd.DataFrame(monthly_results)
    monthly_df.to_csv("/Users/dickgibbons/sports-betting/PGA_Bets/data/processed/monthly_betting_results.csv", index=False)

    # Best and Worst Events
    print("\n" + "=" * 80)
    print("BEST & WORST EVENTS")
    print("=" * 80)

    event_summary = bets_df.groupby(['event_id', 'event_name', 'month']).agg({
        'stake': 'sum',
        'profit': 'sum',
        'won': 'sum'
    }).reset_index()
    event_summary['roi'] = (event_summary['profit'] / event_summary['stake']) * 100

    print("\nBEST EVENTS:")
    best = event_summary.nlargest(5, 'profit')
    for _, row in best.iterrows():
        print(f"  {row['event_name'][:35]:<35} | Profit: ${row['profit']:>+8,.2f} | ROI: {row['roi']:>+6.1f}%")

    print("\nWORST EVENTS:")
    worst = event_summary.nsmallest(5, 'profit')
    for _, row in worst.iterrows():
        print(f"  {row['event_name'][:35]:<35} | Profit: ${row['profit']:>+8,.2f} | ROI: {row['roi']:>+6.1f}%")

    # Big Winners
    print("\n" + "=" * 80)
    print("BIG WINNERS (Outright Win Hits)")
    print("=" * 80)

    winners = bets_df[(bets_df['bet_type'] == 'win') & (bets_df['won'] == True)]
    if len(winners) > 0:
        for _, row in winners.iterrows():
            print(f"  {row['player_name']:<25} @ {row['event_name'][:25]:<25} | +{row['odds']} odds | Profit: ${row['profit']:,.2f}")
    else:
        print("  No outright winner bets hit")

    # Best ROI by Bet Type + Month
    print("\n" + "=" * 80)
    print("PROFITABILITY BY BET TYPE & MONTH")
    print("=" * 80)

    pivot = bets_df.pivot_table(
        values='profit',
        index='month',
        columns='bet_type',
        aggfunc='sum'
    ).reindex(months_order)

    print(f"\n{'Month':<12} {'Win':>12} {'Top 5':>12} {'Top 10':>12}")
    print("-" * 50)

    for month in months_order:
        if month in pivot.index:
            row = pivot.loc[month]
            win = row.get('win', 0)
            top5 = row.get('top5', 0)
            top10 = row.get('top10', 0)
            print(f"{month:<12} ${win:>+10,.2f} ${top5:>+10,.2f} ${top10:>+10,.2f}")

    # Save all bets
    bets_df.to_csv("/Users/dickgibbons/sports-betting/PGA_Bets/data/processed/all_simulated_bets.csv", index=False)
    print(f"\n\nSaved detailed bet records to /Users/dickgibbons/sports-betting/PGA_Bets/data/processed/all_simulated_bets.csv")
    print(f"Saved monthly summary to /Users/dickgibbons/sports-betting/PGA_Bets/data/processed/monthly_betting_results.csv")

    # Final Analysis
    print("\n" + "=" * 80)
    print("STRATEGY RECOMMENDATIONS")
    print("=" * 80)

    # Which bet type is most profitable?
    for bet_type in ['win', 'top5', 'top10']:
        type_df = bets_df[bets_df['bet_type'] == bet_type]
        roi = (type_df['profit'].sum() / type_df['stake'].sum()) * 100
        if roi > 0:
            print(f"  ✓ {bet_type.upper()} bets: {roi:+.1f}% ROI - PROFITABLE")
        else:
            print(f"  ✗ {bet_type.upper()} bets: {roi:+.1f}% ROI - NOT PROFITABLE")


if __name__ == "__main__":
    main()
