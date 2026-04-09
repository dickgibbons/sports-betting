#!/usr/bin/env python3
"""
Generate Individual Sport-Specific Picks Files
Creates separate daily picks files for each sport with confidence ratings
"""

import sys
import os
from datetime import datetime

# Add paths
sys.path.insert(0, '/Users/dickgibbons/AI Projects/sports-betting/core')
sys.path.insert(0, '/Users/dickgibbons/AI Projects/sports-betting/hockey/analysis')
sys.path.insert(0, '/Users/dickgibbons/AI Projects/sports-betting/nba/analysis')
sys.path.insert(0, '/Users/dickgibbons/AI Projects/sports-betting/ncaa/analyzers')
sys.path.insert(0, '/Users/dickgibbons/AI Projects/sports-betting/soccer/analysis')

from nhl_betting_angles_analyzer import NHLBettingAnglesAnalyzer
from nba_betting_angles_analyzer_v2 import NBABettingAnglesAnalyzer
from ncaa_betting_angles_analyzer import NCAABettingAnglesAnalyzer
from soccer_betting_angles_analyzer_v2 import SoccerBettingAnglesAnalyzer
import requests


class SportPicksGenerator:
    """Generate daily picks for individual sports"""

    def __init__(self, date_str=None):
        self.date = date_str or datetime.now().strftime('%Y-%m-%d')
        self.output_dir = f"/Users/dickgibbons/AI Projects/sports-betting/reports/{self.date}"
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
        """Generate NCAA-specific picks file - EXPANDED to analyze all games"""
        print(f"🏀 Generating NCAA picks for {self.date}...")

        # Fetch ALL games with odds from The Odds API
        odds_data = self._fetch_odds_with_spreads('basketball_ncaab')

        if not odds_data:
            print("   ⚠️  No NCAA games found from odds API")
            return

        print(f"   📊 Analyzing {len(odds_data)} NCAA games...")

        # Also get ESPN-based angles for games that have them
        analyzer = NCAABettingAnglesAnalyzer()
        espn_opportunities = analyzer.analyze_schedule_for_date(self.date)

        picks = []

        for game_odds in odds_data:
            home_team = game_odds.get('home_team', '')
            away_team = game_odds.get('away_team', '')

            # Get moneyline odds
            home_ml = game_odds.get('home_ml')
            away_ml = game_odds.get('away_ml')

            # Get spread odds
            home_spread = game_odds.get('home_spread')
            home_spread_odds = game_odds.get('home_spread_odds')
            away_spread = game_odds.get('away_spread')
            away_spread_odds = game_odds.get('away_spread_odds')

            # Look for ESPN-based angles (elite venue, fatigue, etc.)
            espn_angles = []
            espn_edge = 0

            for opp in espn_opportunities:
                opp_home = opp.get('home_team', '')
                opp_away = opp.get('away_team', '')

                home_match = (home_team.lower() in opp_home.lower() or opp_home.lower() in home_team.lower())
                away_match = (away_team.lower() in opp_away.lower() or opp_away.lower() in away_team.lower())

                if home_match and away_match:
                    espn_angles = opp.get('angles', [])
                    espn_edge = sum(float(a.get('edge', '+0%').replace('+', '').replace('%', '').split('-')[0])
                                   for a in espn_angles if a.get('edge'))
                    break

            # NEW: Add odds-based angles (analyze all games, not just ESPN subset)
            odds_angles = self._analyze_ncaa_odds_angles(home_team, away_team, home_ml, away_ml,
                                                         home_spread, away_spread)

            # Combine all angles
            all_angles = espn_angles + odds_angles
            total_edge = espn_edge + sum(a.get('edge_value', 0) for a in odds_angles)

            if not all_angles:
                continue  # Skip games with no angles at all

            # Evaluate MONEYLINE bets
            if home_ml and away_ml:
                # Check home ML
                if home_ml >= self.max_favorite_odds:  # Not too heavy a favorite
                    estimated_home_prob = 0.50 + (total_edge / 100)
                    home_ml_ev = self._calculate_true_ev(home_ml, estimated_home_prob)

                    if home_ml_ev >= self.min_value_threshold:
                        picks.append({
                            'game': f"{away_team} @ {home_team}",
                            'bet': f"{home_team} ML",
                            'bet_type': 'ML',
                            'odds': home_ml,
                            'edge': total_edge,
                            'true_ev': home_ml_ev * 100,
                            'confidence': self._get_confidence(total_edge, len(all_angles)),
                            'angles': all_angles
                        })

                # Check away ML
                if away_ml >= self.max_favorite_odds:
                    estimated_away_prob = 0.50 - (total_edge / 100) if espn_edge > 0 else 0.50 + (total_edge / 100)
                    away_ml_ev = self._calculate_true_ev(away_ml, estimated_away_prob)

                    if away_ml_ev >= self.min_value_threshold:
                        picks.append({
                            'game': f"{away_team} @ {home_team}",
                            'bet': f"{away_team} ML",
                            'bet_type': 'ML',
                            'odds': away_ml,
                            'edge': total_edge if total_edge < 0 else 0,  # Away gets reverse edge
                            'true_ev': away_ml_ev * 100,
                            'confidence': self._get_confidence(abs(total_edge), len(all_angles)),
                            'angles': all_angles
                        })

            # Evaluate SPREAD bets (important for heavy favorites)
            if home_spread_odds and away_spread_odds:
                # Home spread
                estimated_spread_prob = 0.50 + (total_edge / 200)  # Spreads need less edge adjustment
                home_spread_ev = self._calculate_true_ev(home_spread_odds, estimated_spread_prob)

                if home_spread_ev >= self.min_value_threshold:
                    picks.append({
                        'game': f"{away_team} @ {home_team}",
                        'bet': f"{home_team} {home_spread:+.1f}",
                        'bet_type': 'SPREAD',
                        'odds': home_spread_odds,
                        'edge': total_edge,
                        'true_ev': home_spread_ev * 100,
                        'confidence': self._get_confidence(total_edge, len(all_angles)),
                        'angles': all_angles
                    })

                # Away spread
                estimated_spread_prob = 0.50 - (total_edge / 200) if espn_edge > 0 else 0.50 + (total_edge / 200)
                away_spread_ev = self._calculate_true_ev(away_spread_odds, estimated_spread_prob)

                if away_spread_ev >= self.min_value_threshold:
                    picks.append({
                        'game': f"{away_team} @ {home_team}",
                        'bet': f"{away_team} {away_spread:+.1f}",
                        'bet_type': 'SPREAD',
                        'odds': away_spread_odds,
                        'edge': abs(total_edge),
                        'true_ev': away_spread_ev * 100,
                        'confidence': self._get_confidence(abs(total_edge), len(all_angles)),
                        'angles': all_angles
                    })

        self._write_picks_file('NCAA', picks, '🏀')

    def _analyze_ncaa_odds_angles(self, home_team, away_team, home_ml, away_ml, home_spread, away_spread):
        """Analyze odds-based angles for NCAA games (power conference, underdog value, etc.)"""
        angles = []

        # Power 5 conferences
        power_5 = ['Duke', 'North Carolina', 'Kentucky', 'Kansas', 'UCLA', 'Arizona', 'UConn',
                   'Michigan', 'Illinois', 'Auburn', 'Alabama', 'Notre Dame', 'Virginia Tech',
                   'Penn State', 'Maryland', 'Michigan State', 'Creighton', 'TCU', 'Temple']

        # Check for mid-major underdog value
        if away_ml and away_ml > 0:  # Away is underdog
            is_power_5_home = any(p5 in home_team for p5 in power_5)
            is_away_mid_major = not any(p5 in away_team for p5 in power_5)

            # Good underdog value (reasonable line)
            if away_ml >= 120 and away_ml <= 300:
                if not is_power_5_home:  # Both mid-majors or home is weak
                    angles.append({
                        'type': 'UNDERDOG_VALUE',
                        'reason': f'{away_team} underdog value at +{away_ml}',
                        'edge_value': 5.0
                    })
                elif is_away_mid_major and away_ml >= 200:
                    angles.append({
                        'type': 'UNDERDOG_VALUE',
                        'reason': f'{away_team} live dog against power conference at +{away_ml}',
                        'edge_value': 4.0
                    })

        # Check for competitive spread (close game expected)
        if home_spread and abs(home_spread) <= 5.5:
            angles.append({
                'type': 'COMPETITIVE_GAME',
                'reason': f'Close spread ({home_spread:+.1f}) suggests competitive game',
                'edge_value': 3.0
            })

        # Check for big spread with value (fade the favorite on spread)
        if home_spread and home_spread <= -15 and home_ml and home_ml < -1000:
            angles.append({
                'type': 'BIG_FAVORITE',
                'reason': f'Large spread ({home_spread:+.1f}) creates underdog spread value',
                'edge_value': 4.0
            })

        return angles

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

    def generate_ncaa_ev_report(self):
        """Generate comprehensive NCAA EV report showing all games ranked by EV"""
        print(f"📊 Generating NCAA EV Report for {self.date}...")

        analyzer = NCAABettingAnglesAnalyzer()
        opportunities = analyzer.analyze_schedule_for_date(self.date)

        if not opportunities:
            print("   ⚠️  No NCAA games found")
            return

        all_games = []

        for game in opportunities:
            home_team = game.get('home_team', '')
            away_team = game.get('away_team', '')
            angles = game.get('angles', [])

            total_edge = sum(float(a.get('edge', '+0%').replace('+', '').replace('%', '').split('-')[0])
                           for a in angles if a.get('edge'))

            # Fetch odds
            game_odds = self._get_team_odds('basketball_ncaab', home_team, away_team)

            home_odds = game_odds.get('home', 0) if game_odds else None
            away_odds = game_odds.get('away', 0) if game_odds else None

            # Determine bet side
            bet_home = sum(1 for a in angles if 'home' in a.get('bet', '').lower() or home_team in a.get('bet', ''))
            bet_side = 'home' if bet_home > len(angles) / 2 else 'away'
            bet_team = home_team if bet_side == 'home' else away_team
            odds = home_odds if bet_side == 'home' else away_odds

            # Calculate EV
            true_ev = None
            estimated_win_prob = 0.50 + (total_edge / 100)
            if odds:
                true_ev = self._calculate_true_ev(odds, estimated_win_prob)

            all_games.append({
                'game': f"{away_team} @ {home_team}",
                'bet_team': bet_team,
                'odds': odds,
                'edge': total_edge,
                'true_ev': true_ev * 100 if true_ev is not None else None,
                'angles': angles,
                'home_odds': home_odds,
                'away_odds': away_odds
            })

        # Sort by EV descending (None values go to bottom)
        all_games.sort(key=lambda x: x['true_ev'] if x['true_ev'] is not None else -999, reverse=True)

        # Write report
        filename = f"{self.output_dir}/ncaa_ev_report_{self.date}.txt"
        with open(filename, 'w') as f:
            f.write(f"🏀 NCAA BASKETBALL - COMPREHENSIVE EV REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Date: {self.date}\n")
            f.write(f"Total Games Analyzed: {len(all_games)}\n")
            f.write("=" * 80 + "\n\n")
            f.write("📊 ALL GAMES RANKED BY EXPECTED VALUE (EV)\n")
            f.write("=" * 80 + "\n\n")

            for idx, game in enumerate(all_games, 1):
                f.write(f"#{idx} {game['game']}\n")
                f.write("-" * 80 + "\n")
                f.write(f"   RECOMMENDED BET: {game['bet_team']} ML\n")

                if game['odds']:
                    f.write(f"   ODDS: {game['odds']:+d}\n")
                else:
                    f.write(f"   ODDS: Not Available\n")

                if game['true_ev'] is not None:
                    f.write(f"   TRUE EV: {game['true_ev']:+.1f}%\n")

                    # Visual indicator
                    if game['true_ev'] >= 5:
                        f.write(f"   STATUS: ✅ QUALIFIES (EV >= 5%)\n")
                    else:
                        f.write(f"   STATUS: ❌ FILTERED (EV < 5%)\n")

                    if game['odds'] and game['odds'] < -250:
                        f.write(f"   WARNING: ⚠️  Heavy favorite (worse than -250)\n")
                else:
                    f.write(f"   TRUE EV: Cannot Calculate (no odds)\n")
                    f.write(f"   STATUS: ❌ NO ODDS AVAILABLE\n")

                f.write(f"   ANGLE EDGE: +{game['edge']:.1f}%\n")

                # Show both sides' odds
                if game['home_odds'] or game['away_odds']:
                    f.write(f"\n   Market Odds:\n")
                    if game['home_odds']:
                        home_name = game['game'].split(' @ ')[1]
                        f.write(f"     • {home_name}: {game['home_odds']:+d}\n")
                    if game['away_odds']:
                        away_name = game['game'].split(' @ ')[0]
                        f.write(f"     • {away_name}: {game['away_odds']:+d}\n")

                # Angles
                if game['angles']:
                    f.write(f"\n   Betting Angles ({len(game['angles'])}):\n")
                    for angle in game['angles']:
                        f.write(f"     • {angle.get('reason', angle.get('type', 'Unknown'))}\n")

                f.write("\n")

            f.write("=" * 80 + "\n")
            f.write("📋 LEGEND\n")
            f.write("  ✅ QUALIFIES: EV >= 5% and odds better than -250\n")
            f.write("  ❌ FILTERED: Does not meet minimum EV threshold or too heavy favorite\n")
            f.write("  TRUE EV: Expected value based on real odds and estimated win probability\n")
            f.write("  ANGLE EDGE: Edge from betting angles (doesn't account for market odds)\n")
            f.write("=" * 80 + "\n")

        print(f"   ✅ NCAA EV Report saved: {len(all_games)} games")
        print(f"      File: {filename}")

    def generate_soccer_ev_report(self):
        """Generate comprehensive Soccer EV report showing all matches ranked by EV"""
        print(f"📊 Generating Soccer EV Report for {self.date}...")

        analyzer = SoccerBettingAnglesAnalyzer()
        matches = analyzer.get_all_matches(self.date)

        if not matches:
            print("   ⚠️  No soccer matches scheduled")
            return

        all_matches = []

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

            # Get odds
            game_odds = self._get_team_odds('soccer', home_team, away_team)
            home_odds = game_odds.get('home', 0) if game_odds else None
            away_odds = game_odds.get('away', 0) if game_odds else None

            # Determine bet side
            if angles:
                bet_text = angles[0]['bet']
                if home_team in bet_text or 'home' in bet_text.lower():
                    bet_side = 'home'
                    bet_team = home_team
                    odds = home_odds
                elif away_team in bet_text or 'away' in bet_text.lower():
                    bet_side = 'away'
                    bet_team = away_team
                    odds = away_odds
                else:
                    bet_side = None
                    bet_team = bet_text
                    odds = None
            else:
                bet_side = 'home'
                bet_team = home_team
                odds = home_odds

            # Calculate EV
            true_ev = None
            estimated_win_prob = 0.35 + (total_edge / 100)
            if odds:
                true_ev = self._calculate_true_ev(odds, estimated_win_prob)

            all_matches.append({
                'game': f"{away_team} @ {home_team}",
                'league': league,
                'bet_team': bet_team,
                'odds': odds,
                'edge': total_edge,
                'true_ev': true_ev * 100 if true_ev is not None else None,
                'angles': angles,
                'home_odds': home_odds,
                'away_odds': away_odds
            })

        # Sort by EV descending
        all_matches.sort(key=lambda x: x['true_ev'] if x['true_ev'] is not None else -999, reverse=True)

        # Write report
        filename = f"{self.output_dir}/soccer_ev_report_{self.date}.txt"
        with open(filename, 'w') as f:
            f.write(f"⚽ SOCCER - COMPREHENSIVE EV REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Date: {self.date}\n")
            f.write(f"Total Matches Analyzed: {len(all_matches)}\n")
            f.write("=" * 80 + "\n\n")
            f.write("📊 ALL MATCHES RANKED BY EXPECTED VALUE (EV)\n")
            f.write("=" * 80 + "\n\n")

            for idx, match in enumerate(all_matches, 1):
                f.write(f"#{idx} {match['game']}\n")
                f.write(f"   League: {match['league']}\n")
                f.write("-" * 80 + "\n")
                f.write(f"   RECOMMENDED BET: {match['bet_team']}\n")

                if match['odds']:
                    f.write(f"   ODDS: {match['odds']:+d}\n")
                else:
                    f.write(f"   ODDS: Not Available\n")

                if match['true_ev'] is not None:
                    f.write(f"   TRUE EV: {match['true_ev']:+.1f}%\n")

                    # Visual indicator
                    if match['true_ev'] >= 5 and (not match['odds'] or match['odds'] >= -250):
                        f.write(f"   STATUS: ✅ QUALIFIES (EV >= 5%, odds OK)\n")
                    elif match['true_ev'] < 5:
                        f.write(f"   STATUS: ❌ FILTERED (EV < 5%)\n")
                    elif match['odds'] and match['odds'] < -250:
                        f.write(f"   STATUS: ❌ FILTERED (Heavy favorite worse than -250)\n")
                else:
                    f.write(f"   TRUE EV: Cannot Calculate (no odds)\n")
                    f.write(f"   STATUS: ❌ NO ODDS AVAILABLE\n")

                f.write(f"   ANGLE EDGE: +{match['edge']:.1f}%\n")

                # Show market odds
                if match['home_odds'] or match['away_odds']:
                    f.write(f"\n   Market Odds:\n")
                    if match['home_odds']:
                        home_name = match['game'].split(' @ ')[1]
                        f.write(f"     • {home_name}: {match['home_odds']:+d}\n")
                    if match['away_odds']:
                        away_name = match['game'].split(' @ ')[0]
                        f.write(f"     • {away_name}: {match['away_odds']:+d}\n")

                # Angles
                if match['angles']:
                    f.write(f"\n   Betting Angles ({len(match['angles'])}):\n")
                    for angle in match['angles']:
                        reason = angle.get('reason', angle.get('type', 'Unknown'))
                        f.write(f"     • {reason}\n")

                f.write("\n")

            f.write("=" * 80 + "\n")
            f.write("📋 LEGEND\n")
            f.write("  ✅ QUALIFIES: EV >= 5% and odds better than -250\n")
            f.write("  ❌ FILTERED: Does not meet minimum EV threshold or too heavy favorite\n")
            f.write("  TRUE EV: Expected value based on real odds and estimated win probability\n")
            f.write("  ANGLE EDGE: Edge from betting angles (doesn't account for market odds)\n")
            f.write("=" * 80 + "\n")

        print(f"   ✅ Soccer EV Report saved: {len(all_matches)} matches")
        print(f"      File: {filename}")

    def generate_ncaa_comprehensive_csv(self):
        """Generate comprehensive CSV showing ALL NCAA games with spread and ML EV"""
        print(f"📊 Generating NCAA Comprehensive CSV for {self.date}...")

        # Fetch all odds with spread market from The Odds API (primary source)
        odds_data = self._fetch_odds_with_spreads('basketball_ncaab')

        if not odds_data:
            print("   ⚠️  No NCAA games found from odds API")
            return

        # Get betting angles from analyzer
        analyzer = NCAABettingAnglesAnalyzer()
        opportunities = analyzer.analyze_schedule_for_date(self.date)

        csv_data = []

        for game_odds in odds_data:
            home_team = game_odds.get('home_team', '')
            away_team = game_odds.get('away_team', '')

            # Get moneyline odds
            home_ml = game_odds.get('home_ml')
            away_ml = game_odds.get('away_ml')

            # Get spread odds
            home_spread = game_odds.get('home_spread')
            home_spread_odds = game_odds.get('home_spread_odds')
            away_spread = game_odds.get('away_spread')
            away_spread_odds = game_odds.get('away_spread_odds')

            # Try to find betting angles for this game
            angles_for_game = []
            angle_edge = 0

            for opp in opportunities:
                opp_home = opp.get('home_team', '')
                opp_away = opp.get('away_team', '')

                # Fuzzy match team names
                home_match = (home_team.lower() in opp_home.lower() or opp_home.lower() in home_team.lower())
                away_match = (away_team.lower() in opp_away.lower() or opp_away.lower() in away_team.lower())

                if home_match and away_match:
                    angles_for_game = opp.get('angles', [])
                    angle_edge = sum(float(a.get('edge', '+0%').replace('+', '').replace('%', '').split('-')[0])
                                   for a in angles_for_game if a.get('edge'))
                    break

            # Calculate EV for home ML
            home_ml_ev = None
            if home_ml:
                estimated_home_prob = 0.50 + (angle_edge / 100) if angles_for_game else 0.50
                home_ml_ev = self._calculate_true_ev(home_ml, estimated_home_prob) * 100

            # Calculate EV for away ML
            away_ml_ev = None
            if away_ml:
                estimated_away_prob = 0.50 - (angle_edge / 100) if angles_for_game else 0.50
                away_ml_ev = self._calculate_true_ev(away_ml, estimated_away_prob) * 100

            # Calculate EV for home spread
            home_spread_ev = None
            if home_spread_odds:
                # Spreads typically have ~50% win probability (that's the point of a spread)
                # But adjust slightly based on angles
                estimated_spread_prob = 0.50 + (angle_edge / 200) if angles_for_game else 0.50
                home_spread_ev = self._calculate_true_ev(home_spread_odds, estimated_spread_prob) * 100

            # Calculate EV for away spread
            away_spread_ev = None
            if away_spread_odds:
                estimated_spread_prob = 0.50 - (angle_edge / 200) if angles_for_game else 0.50
                away_spread_ev = self._calculate_true_ev(away_spread_odds, estimated_spread_prob) * 100

            # Angles description
            angles_desc = '; '.join([a.get('reason', a.get('type', '')) for a in angles_for_game]) if angles_for_game else 'None'

            csv_data.append({
                'Game': f"{away_team} @ {home_team}",
                'Home Team': home_team,
                'Away Team': away_team,
                'Home ML': home_ml if home_ml else '',
                'Away ML': away_ml if away_ml else '',
                'Home ML EV%': f"{home_ml_ev:.2f}" if home_ml_ev is not None else '',
                'Away ML EV%': f"{away_ml_ev:.2f}" if away_ml_ev is not None else '',
                'Home Spread': home_spread if home_spread else '',
                'Home Spread Odds': home_spread_odds if home_spread_odds else '',
                'Away Spread': away_spread if away_spread else '',
                'Away Spread Odds': away_spread_odds if away_spread_odds else '',
                'Home Spread EV%': f"{home_spread_ev:.2f}" if home_spread_ev is not None else '',
                'Away Spread EV%': f"{away_spread_ev:.2f}" if away_spread_ev is not None else '',
                'Angle Edge%': f"{angle_edge:.1f}" if angle_edge > 0 else '',
                'Betting Angles': angles_desc
            })

        # Write CSV
        import csv
        filename = f"{self.output_dir}/ncaa_comprehensive_{self.date}.csv"

        if csv_data:
            with open(filename, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=csv_data[0].keys())
                writer.writeheader()
                writer.writerows(csv_data)

            print(f"   ✅ NCAA Comprehensive CSV saved: {len(csv_data)} games")
            print(f"      File: {filename}")
        else:
            print("   ⚠️  No data to write")

    def _fetch_odds_with_spreads(self, sport_key):
        """Fetch odds including spread markets from The-Odds-API"""
        try:
            url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
            params = {
                'apiKey': self.odds_api_key,
                'regions': 'us',
                'markets': 'h2h,spreads',  # Both moneyline and spreads
                'oddsFormat': 'american'
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                games_data = response.json()

                processed_games = []
                for game in games_data:
                    home_team = game.get('home_team', '')
                    away_team = game.get('away_team', '')

                    game_info = {
                        'home_team': home_team,
                        'away_team': away_team,
                        'home_ml': None,
                        'away_ml': None,
                        'home_spread': None,
                        'home_spread_odds': None,
                        'away_spread': None,
                        'away_spread_odds': None
                    }

                    bookmakers = game.get('bookmakers', [])
                    if bookmakers:
                        # Use first bookmaker (typically DraftKings or FanDuel)
                        markets = bookmakers[0].get('markets', [])

                        for market in markets:
                            market_key = market.get('key')
                            outcomes = market.get('outcomes', [])

                            if market_key == 'h2h':  # Moneyline
                                for outcome in outcomes:
                                    if outcome.get('name') == home_team:
                                        game_info['home_ml'] = outcome.get('price')
                                    elif outcome.get('name') == away_team:
                                        game_info['away_ml'] = outcome.get('price')

                            elif market_key == 'spreads':  # Spreads
                                for outcome in outcomes:
                                    if outcome.get('name') == home_team:
                                        game_info['home_spread'] = outcome.get('point')
                                        game_info['home_spread_odds'] = outcome.get('price')
                                    elif outcome.get('name') == away_team:
                                        game_info['away_spread'] = outcome.get('point')
                                        game_info['away_spread_odds'] = outcome.get('price')

                    processed_games.append(game_info)

                return processed_games
        except Exception as e:
            print(f"   ⚠️  Could not fetch odds with spreads for {sport_key}: {e}")
        return []


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
        generator.generate_ncaa_ev_report()
        generator.generate_ncaa_comprehensive_csv()

    if args.sport in ['SOCCER', 'ALL']:
        generator.generate_soccer_picks()
        generator.generate_soccer_ev_report()

    print()
    print("=" * 80)
    print(f"✅ Sport-specific picks saved to: {generator.output_dir}/")
    print("=" * 80)


if __name__ == '__main__':
    main()
