#!/usr/bin/env python3
"""
Generate Individual Sport-Specific Picks Files
Creates separate daily picks files for each sport with confidence ratings
"""

import sys
import os
from datetime import datetime

# Add core to path
sys.path.insert(0, '/Users/dickgibbons/sports-betting/core')

from nhl_betting_angles_analyzer import NHLBettingAnglesAnalyzer
from nba_betting_angles_analyzer_v2 import NBABettingAnglesAnalyzer
from ncaa_betting_angles_analyzer import NCAABettingAnglesAnalyzer
from soccer_betting_angles_analyzer_v2 import SoccerBettingAnglesAnalyzer
import requests


class SportPicksGenerator:
    """Generate daily picks for individual sports"""

    def __init__(self, date_str=None):
        self.date = date_str or datetime.now().strftime('%Y-%m-%d')
        self.output_dir = f"/Users/dickgibbons/sports-betting/reports/{self.date}"
        os.makedirs(self.output_dir, exist_ok=True)

        # Odds API
        self.odds_api_key = '518c226b561ad7586ec8c5dd1144e3fb'
        self.max_favorite_odds = -250
        self.min_value_threshold = 0.05

    def _fetch_odds(self, sport_key):
        """Fetch odds from The-Odds-API"""
        try:
            url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
            params = {
                'apiKey': self.odds_api_key,
                'regions': 'us',
                'markets': 'h2h',
                'oddsFormat': 'american'
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"   ⚠️  Could not fetch odds for {sport_key}: {e}")
        return []

    def _get_team_odds(self, sport_key, home_team, away_team):
        """Get odds for a specific game"""
        odds_data = self._fetch_odds(sport_key)

        for game in odds_data:
            game_home = game.get('home_team', '')
            game_away = game.get('away_team', '')

            if (home_team in game_home or game_home in home_team) and \
               (away_team in game_away or game_away in away_team):

                bookmakers = game.get('bookmakers', [])
                if bookmakers:
                    markets = bookmakers[0].get('markets', [])
                    if markets and markets[0].get('key') == 'h2h':
                        outcomes = markets[0].get('outcomes', [])

                        odds_dict = {}
                        for outcome in outcomes:
                            team_name = outcome.get('name', '')
                            price = outcome.get('price', 0)

                            if home_team in team_name:
                                odds_dict['home'] = price
                            elif away_team in team_name:
                                odds_dict['away'] = price

                        return odds_dict
        return None

    def _calculate_true_ev(self, odds, win_prob):
        """Calculate true expected value"""
        if odds > 0:
            profit_per_dollar = odds / 100
            return (win_prob * profit_per_dollar) - ((1 - win_prob) * 1)
        else:
            profit_per_dollar = 100 / abs(odds)
            return (win_prob * profit_per_dollar) - ((1 - win_prob) * 1)

    def generate_nhl_picks(self):
        """Generate NHL-specific picks file"""
        print(f"🏒 Generating NHL picks for {self.date}...")

        analyzer = NHLBettingAnglesAnalyzer()
        games = analyzer.get_games_for_date(self.date)

        if not games:
            print("   ⚠️  No NHL games scheduled")
            return

        analyzer._build_schedule_context(self.date)
        picks = []

        for game in games:
            home_team_obj = game.get('homeTeam', {})
            away_team_obj = game.get('awayTeam', {})
            home_team = home_team_obj.get('abbrev', '')
            away_team = away_team_obj.get('abbrev', '')

            if not home_team or not away_team:
                continue

            # Analyze betting angles
            angles = []
            total_edge = 0

            # Back-to-back
            b2b = analyzer._analyze_back_to_back(home_team, away_team, self.date)
            if b2b:
                angles.append(b2b)
                total_edge += 12.0

            # 3-in-4 nights
            heavy = analyzer._analyze_three_in_four(home_team, away_team, self.date)
            if heavy:
                angles.append(heavy)
                total_edge += 10.0

            # Rest advantage
            rest = analyzer._analyze_rest_advantage(home_team, away_team, self.date)
            if rest:
                angles.append(rest)
                total_edge += 8.0

            # Road trip fatigue
            road = analyzer._analyze_road_trip_fatigue(home_team, away_team, self.date)
            if road:
                angles.append(road)
                total_edge += 7.4

            if angles:
                # Determine bet direction
                bet_home = sum(1 for a in angles if 'home' in a['bet'].lower() or home_team in a['bet'])
                bet_away = len(angles) - bet_home

                if bet_home > bet_away:
                    bet_team = home_team
                    bet_side = 'home'
                else:
                    bet_team = away_team
                    bet_side = 'away'

                # Get odds
                game_odds = self._get_team_odds('icehockey_nhl', home_team, away_team)

                if game_odds:
                    odds = game_odds.get(bet_side, 0)

                    # EV filtering
                    if odds < self.max_favorite_odds:
                        continue

                    estimated_win_prob = 0.50 + (total_edge / 100)
                    true_ev = self._calculate_true_ev(odds, estimated_win_prob)

                    if true_ev < self.min_value_threshold:
                        continue

                    picks.append({
                        'game': f"{away_team} @ {home_team}",
                        'bet': f"{bet_team} ML",
                        'odds': odds,
                        'edge': total_edge,
                        'true_ev': true_ev * 100,
                        'confidence': self._get_confidence(total_edge, len(angles)),
                        'angles': angles
                    })
                else:
                    # No odds, use angle-only
                    picks.append({
                        'game': f"{away_team} @ {home_team}",
                        'bet': f"{bet_team} ML",
                        'odds': None,
                        'edge': total_edge,
                        'true_ev': total_edge,
                        'confidence': self._get_confidence(total_edge, len(angles)),
                        'angles': angles
                    })

        # Write picks file
        self._write_picks_file('NHL', picks, '🏒')

    def generate_nba_picks(self):
        """Generate NBA-specific picks file"""
        print(f"🏀 Generating NBA picks for {self.date}...")

        analyzer = NBABettingAnglesAnalyzer()
        games = analyzer.get_games_for_date(self.date)

        if not games:
            print("   ⚠️  No NBA games scheduled")
            return

        analyzer._build_schedule_context(self.date)
        picks = []

        for game in games:
            home_team = game.get('home_team', '')
            away_team = game.get('away_team', '')

            if not home_team or not away_team:
                continue

            angles = []
            total_edge = 0

            # Back-to-back
            b2b = analyzer._analyze_back_to_back(home_team, away_team, self.date)
            if b2b:
                angles.append(b2b)
                total_edge += 12.0

            # Heavy schedule
            heavy = analyzer._analyze_heavy_schedule(home_team, away_team, self.date)
            if heavy:
                angles.append(heavy)
                total_edge += 10.0

            # Rest advantage
            rest = analyzer._analyze_rest_advantage(home_team, away_team, self.date)
            if rest:
                angles.append(rest)
                total_edge += 8.0

            # Road trip
            road = analyzer._analyze_road_trip_fatigue(home_team, away_team, self.date)
            if road:
                angles.append(road)
                edge_val = 11.7 if '5th' in str(road.get('road_games', 0)) else 7.3
                total_edge += edge_val

            if angles:
                bet_home = sum(1 for a in angles if 'home' in a['bet'].lower() or home_team in a['bet'])
                bet_away = len(angles) - bet_home

                if bet_home > bet_away:
                    bet_team = home_team
                    bet_side = 'home'
                else:
                    bet_team = away_team
                    bet_side = 'away'

                game_odds = self._get_team_odds('basketball_nba', home_team, away_team)

                if game_odds:
                    odds = game_odds.get(bet_side, 0)

                    if odds < self.max_favorite_odds:
                        continue

                    estimated_win_prob = 0.50 + (total_edge / 100)
                    true_ev = self._calculate_true_ev(odds, estimated_win_prob)

                    if true_ev < self.min_value_threshold:
                        continue

                    picks.append({
                        'game': f"{away_team} @ {home_team}",
                        'bet': f"{bet_team} ML",
                        'odds': odds,
                        'edge': total_edge,
                        'true_ev': true_ev * 100,
                        'confidence': self._get_confidence(total_edge, len(angles)),
                        'angles': angles
                    })

        self._write_picks_file('NBA', picks, '🏀')

    def generate_ncaa_picks(self):
        """Generate NCAA-specific picks file"""
        print(f"🏀 Generating NCAA picks for {self.date}...")

        analyzer = NCAABettingAnglesAnalyzer()
        opportunities = analyzer.analyze_schedule_for_date(self.date)

        if not opportunities:
            print("   ⚠️  No NCAA games with angles found")
            return

        picks = []
        for game in opportunities:
            home_team = game.get('home_team', '')
            away_team = game.get('away_team', '')
            angles = game.get('angles', [])

            if not angles:
                continue

            total_edge = sum(float(a.get('edge', '+0%').replace('+', '').replace('%', '').split('-')[0])
                           for a in angles if a.get('edge'))

            # Fetch odds for EV filtering
            game_odds = self._get_team_odds('basketball_ncaab', home_team, away_team)

            if game_odds:
                bet_home = sum(1 for a in angles if 'home' in a.get('bet', '').lower() or home_team in a.get('bet', ''))
                bet_side = 'home' if bet_home > len(angles) / 2 else 'away'
                bet_team = home_team if bet_side == 'home' else away_team

                odds = game_odds.get(bet_side, 0)

                if odds < self.max_favorite_odds:
                    continue

                estimated_win_prob = 0.50 + (total_edge / 100)
                true_ev = self._calculate_true_ev(odds, estimated_win_prob)

                if true_ev < self.min_value_threshold:
                    continue

                picks.append({
                    'game': f"{away_team} @ {home_team}",
                    'bet': f"{bet_team} ML",
                    'odds': odds,
                    'edge': total_edge,
                    'true_ev': true_ev * 100,
                    'confidence': self._get_confidence(total_edge, len(angles)),
                    'angles': angles
                })

        self._write_picks_file('NCAA', picks, '🏀')

    def generate_soccer_picks(self):
        """Generate Soccer-specific picks file"""
        print(f"⚽ Generating Soccer picks for {self.date}...")

        analyzer = SoccerBettingAnglesAnalyzer()
        matches = analyzer.get_all_matches(self.date)

        if not matches:
            print("   ⚠️  No soccer matches scheduled")
            return

        picks = []
        for match in matches:
            home_team = match.get('home_team', '')
            away_team = match.get('away_team', '')
            league = match.get('league', '')

            if not home_team or not away_team:
                continue

            angles = []
            total_edge = 0

            # Table position
            table = analyzer._analyze_table_position(home_team, away_team, league)
            if table:
                angles.append(table)
                edge_val = 8.5 if table.get('confidence') == 'HIGH' else 5.0
                total_edge += edge_val

            # Home/away splits
            splits = analyzer._analyze_home_away_splits(home_team, away_team)
            if splits:
                angles.append(splits)
                if 'weak_away' in splits.get('type', ''):
                    total_edge += 7.5
                elif 'home_fortress' in splits.get('type', ''):
                    total_edge += 6.5

            if angles and total_edge >= 4.0:
                bet_text = angles[0]['bet']

                # Try to get odds
                game_odds = self._get_team_odds('soccer', home_team, away_team)

                if game_odds:
                    if home_team in bet_text or 'home' in bet_text.lower():
                        bet_side = 'home'
                    elif away_team in bet_text or 'away' in bet_text.lower():
                        bet_side = 'away'
                    else:
                        bet_side = None

                    if bet_side:
                        odds = game_odds.get(bet_side, 0)

                        if odds < self.max_favorite_odds:
                            continue

                        estimated_win_prob = 0.35 + (total_edge / 100)
                        true_ev = self._calculate_true_ev(odds, estimated_win_prob)

                        if true_ev < self.min_value_threshold:
                            continue

                        picks.append({
                            'game': f"{away_team} @ {home_team}",
                            'league': league,
                            'bet': bet_text,
                            'odds': odds,
                            'edge': total_edge,
                            'true_ev': true_ev * 100,
                            'confidence': self._get_confidence(total_edge, len(angles)),
                            'angles': angles
                        })

        self._write_picks_file('SOCCER', picks, '⚽')

    def _get_confidence(self, edge, angle_count):
        """Calculate confidence level"""
        if edge >= 15 and angle_count >= 2:
            return 'ELITE'
        elif edge >= 10 or angle_count >= 2:
            return 'HIGH'
        elif edge >= 7:
            return 'MEDIUM'
        else:
            return 'LOW'

    def _write_picks_file(self, sport, picks, emoji):
        """Write picks to sport-specific file"""
        if not picks:
            print(f"   ℹ️  No qualifying picks found for {sport}")
            return

        # Sort by confidence and edge
        confidence_order = {'ELITE': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        picks.sort(key=lambda x: (confidence_order.get(x['confidence'], 4), -x['edge']))

        filename = f"{self.output_dir}/{sport.lower()}_picks_{self.date}.txt"

        with open(filename, 'w') as f:
            f.write(f"{emoji} {sport} BETTING PICKS - {self.date}\n")
            f.write("=" * 80 + "\n\n")

            # Summary
            by_confidence = {}
            for pick in picks:
                conf = pick['confidence']
                by_confidence[conf] = by_confidence.get(conf, 0) + 1

            f.write(f"📊 SUMMARY\n")
            f.write(f"{'─' * 80}\n")
            f.write(f"Total Picks: {len(picks)}\n")
            for conf in ['ELITE', 'HIGH', 'MEDIUM', 'LOW']:
                if conf in by_confidence:
                    marker = {'ELITE': '🔥', 'HIGH': '✅', 'MEDIUM': '💡', 'LOW': '⚪'}[conf]
                    f.write(f"{marker} {conf}: {by_confidence[conf]} picks\n")
            f.write("\n")

            # Individual picks
            for i, pick in enumerate(picks, 1):
                conf_marker = {'ELITE': '🔥🔥🔥', 'HIGH': '✅✅', 'MEDIUM': '💡', 'LOW': '⚪'}[pick['confidence']]

                f.write(f"{conf_marker} #{i} {pick['game']}\n")
                f.write(f"   BET: {pick['bet']}\n")

                if pick['odds']:
                    f.write(f"   ODDS: {pick['odds']:+d} | True EV: +{pick['true_ev']:.1f}%\n")
                else:
                    f.write(f"   Expected Edge: +{pick['edge']:.1f}%\n")

                f.write(f"   Confidence: {pick['confidence']}\n")

                if 'league' in pick:
                    f.write(f"   League: {pick['league']}\n")

                f.write(f"   Angles ({len(pick['angles'])}):\n")
                for angle in pick['angles']:
                    f.write(f"     • {angle.get('reason', angle.get('type', 'Unknown'))}\n")

                # Bet sizing recommendation
                stake_rec = {'ELITE': '2-3% of bankroll', 'HIGH': '1-2% of bankroll',
                           'MEDIUM': '0.5-1% of bankroll', 'LOW': 'Optional/skip'}
                f.write(f"   💰 Recommended: {stake_rec[pick['confidence']]}\n")
                f.write("\n")

            f.write("=" * 80 + "\n")
            f.write(f"📁 Full analysis saved to: {filename}\n")

        print(f"   ✅ {sport} picks saved: {len(picks)} picks")
        print(f"      File: {filename}")


def main():
    """Generate all sport-specific picks files"""
    import argparse

    parser = argparse.ArgumentParser(description='Generate sport-specific daily picks')
    parser.add_argument('--date', help='Date (YYYY-MM-DD)', default=None)
    parser.add_argument('--sport', help='Specific sport (NHL, NBA, NCAA, SOCCER, ALL)',
                       default='ALL')

    args = parser.parse_args()

    print("\n" + "=" * 80)
    print("GENERATING SPORT-SPECIFIC DAILY PICKS")
    print("=" * 80)
    print()

    generator = SportPicksGenerator(args.date)

    if args.sport in ['NHL', 'ALL']:
        generator.generate_nhl_picks()

    if args.sport in ['NBA', 'ALL']:
        generator.generate_nba_picks()

    if args.sport in ['NCAA', 'ALL']:
        generator.generate_ncaa_picks()

    if args.sport in ['SOCCER', 'ALL']:
        generator.generate_soccer_picks()

    print()
    print("=" * 80)
    print(f"✅ Sport-specific picks saved to: {generator.output_dir}/")
    print("=" * 80)


if __name__ == '__main__':
    main()
