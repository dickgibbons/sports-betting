#!/usr/bin/env python3
"""
Daily Betting Report - THE ONE REPORT YOU NEED EVERY MORNING
Combines ALL betting signals (angles, ML models, totals, BTTS) across all sports
Outputs top 5-10 bets regardless of sport or bet type
"""

import sys
import os
import requests
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

# Add analyzers directory to path
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'analyzers'))

# Import angle analyzers
from nhl_betting_angles_analyzer import NHLBettingAnglesAnalyzer
from nba_betting_angles_analyzer_v2 import NBABettingAnglesAnalyzer
from soccer_betting_angles_analyzer_v2 import SoccerBettingAnglesAnalyzer
from ncaa_betting_angles_analyzer import NCAABettingAnglesAnalyzer

# Import bet tracker
from bet_tracker import BetTracker


class DailyBettingReport:
    """ONE unified report with best bets across all sports and bet types"""

    def __init__(self, track_bets: bool = True, include_soccer: bool = True, include_ncaa: bool = True):
        self.date = datetime.now().strftime('%Y-%m-%d')
        self.all_bets = []  # Every possible bet opportunity
        self.include_soccer = include_soccer
        self.include_ncaa = include_ncaa

        # Initialize analyzers
        self.nhl_analyzer = NHLBettingAnglesAnalyzer()
        self.nba_analyzer = NBABettingAnglesAnalyzer()

        if include_soccer:
            self.soccer_analyzer = SoccerBettingAnglesAnalyzer()

        if include_ncaa:
            self.ncaa_analyzer = NCAABettingAnglesAnalyzer()

        # Bet tracker
        self.track_bets = track_bets
        if track_bets:
            self.bet_tracker = BetTracker()

        # Odds API
        self.odds_api_key = '518c226b561ad7586ec8c5dd1144e3fb'
        self.odds_cache = {}  # Cache odds for performance

        # Filtering thresholds
        self.max_favorite_odds = -350  # Don't recommend favorites worse than -350
        self.min_value_threshold = 0.03  # Minimum 3% true expected value

        print("🎯 Daily Betting Report initialized")

    def generate_daily_report(self):
        """Generate THE daily report"""

        print(f"\n{'='*80}")
        print(f"📊 DAILY BETTING REPORT - {self.date}")
        print(f"{'='*80}\n")

        # 1. Collect ALL betting opportunities from all sources
        print("🔄 Analyzing all betting opportunities...")

        # NHL opportunities
        nhl_bets = self._collect_nhl_bets()
        self.all_bets.extend(nhl_bets)
        print(f"   ✅ NHL: {len(nhl_bets)} opportunities")

        # NBA opportunities
        nba_bets = self._collect_nba_bets()
        self.all_bets.extend(nba_bets)
        print(f"   ✅ NBA: {len(nba_bets)} opportunities")

        # Soccer opportunities (if enabled)
        if self.include_soccer:
            soccer_bets = self._collect_soccer_bets()
            self.all_bets.extend(soccer_bets)
            print(f"   ✅ Soccer: {len(soccer_bets)} opportunities")

        # NCAA opportunities (if enabled)
        if self.include_ncaa:
            ncaa_bets = self._collect_ncaa_bets()
            self.all_bets.extend(ncaa_bets)
            print(f"   ✅ NCAA: {len(ncaa_bets)} opportunities")

        print(f"\n   📊 Total opportunities analyzed: {len(self.all_bets)}\n")

        # 2. Rank ALL bets by expected value
        ranked_bets = self._rank_all_bets()

        # 3. Display top 5-10 bets
        self._display_top_bets(ranked_bets)

        # 4. Log bets to tracker
        if self.track_bets:
            self._log_bets_to_tracker(ranked_bets[:10])

        return ranked_bets[:10]

    def _fetch_odds(self, sport_key: str) -> Dict:
        """Fetch odds from The-Odds-API"""
        if sport_key in self.odds_cache:
            return self.odds_cache[sport_key]

        try:
            url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
            params = {
                'apiKey': self.odds_api_key,
                'regions': 'us',
                'markets': 'h2h',
                'oddsFormat': 'american'
            }

            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 200:
                self.odds_cache[sport_key] = response.json()
                return self.odds_cache[sport_key]

        except Exception as e:
            print(f"   ⚠️  Could not fetch odds for {sport_key}: {e}")

        return []

    def _get_team_odds(self, sport_key: str, home_team: str, away_team: str) -> Optional[Dict]:
        """Get odds for a specific game"""
        odds_data = self._fetch_odds(sport_key)

        for game in odds_data:
            game_home = game.get('home_team', '')
            game_away = game.get('away_team', '')

            # Match teams (fuzzy matching for abbreviations)
            if (home_team in game_home or game_home in home_team) and \
               (away_team in game_away or game_away in away_team):

                # Get best odds from available bookmakers
                bookmakers = game.get('bookmakers', [])
                if bookmakers:
                    markets = bookmakers[0].get('markets', [])
                    if markets and markets[0].get('key') == 'h2h':
                        outcomes = markets[0].get('outcomes', [])

                        odds_dict = {}
                        for outcome in outcomes:
                            team_name = outcome.get('name', '')
                            price = outcome.get('price', 0)

                            if 'home' in team_name.lower() or home_team in team_name:
                                odds_dict['home'] = price
                            elif 'away' in team_name.lower() or away_team in team_name:
                                odds_dict['away'] = price

                        return odds_dict

        return None

    def _calculate_true_ev(self, odds: int, win_prob: float) -> float:
        """Calculate true expected value given odds and win probability"""
        if odds > 0:  # Underdog
            profit_per_dollar = odds / 100
            return (win_prob * profit_per_dollar) - ((1 - win_prob) * 1)
        else:  # Favorite
            profit_per_dollar = 100 / abs(odds)
            return (win_prob * profit_per_dollar) - ((1 - win_prob) * 1)

    def _collect_nhl_bets(self) -> List[Dict]:
        """Collect all NHL betting opportunities"""
        bets = []

        # Fetch NHL odds
        print("   📊 Fetching NHL odds...")

        # Get today's games
        games = self.nhl_analyzer.get_games_for_date(self.date)

        if not games:
            return bets

        # Build schedule context
        self.nhl_analyzer._build_schedule_context(self.date)

        # Analyze each game for ALL bet types
        for game in games:
            # NHL API returns nested team objects
            home_team_obj = game.get('homeTeam', {})
            away_team_obj = game.get('awayTeam', {})

            home_team = home_team_obj.get('abbrev', '')
            away_team = away_team_obj.get('abbrev', '')

            if not home_team or not away_team:
                continue

            # Moneyline bets from angles
            ml_bets = self._analyze_nhl_moneyline(home_team, away_team)
            bets.extend(ml_bets)

            # Totals bets (would integrate with ML model predictions)
            # total_bets = self._analyze_nhl_totals(home_team, away_team)
            # bets.extend(total_bets)

        return bets

    def _analyze_nhl_moneyline(self, home_team: str, away_team: str) -> List[Dict]:
        """Analyze NHL moneyline using angles"""
        bets = []

        # Check all angles
        angles_found = []
        total_edge = 0

        # Back-to-back (HOME→ROAD only, 80% win rate)
        b2b = self.nhl_analyzer._analyze_back_to_back(home_team, away_team, self.date)
        if b2b:
            angles_found.append(b2b)
            total_edge += 12.0  # HOME→ROAD B2B: 80% win rate historical

        # 3-in-4 nights
        heavy = self.nhl_analyzer._analyze_three_in_four(home_team, away_team, self.date)
        if heavy:
            angles_found.append(heavy)
            total_edge += 6.5

        # Rest advantage
        rest = self.nhl_analyzer._analyze_rest_advantage(home_team, away_team, self.date)
        if rest:
            angles_found.append(rest)
            total_edge += 5.0

        # Road trip fatigue (4th+ game only, based on backtest)
        road_trip = self.nhl_analyzer._analyze_road_trip_fatigue(home_team, away_team, self.date)
        if road_trip:
            angles_found.append(road_trip)
            total_edge += 7.4  # Backtest-proven edge for 4th+ road game

        # If any angles found, create bet recommendation
        if angles_found:
            # Determine which team to bet (most angles point to one side)
            bet_home = sum(1 for a in angles_found if 'home' in a['bet'].lower() or home_team in a['bet'])
            bet_away = len(angles_found) - bet_home

            if bet_home > bet_away:
                bet_team = home_team
                bet_side = 'home'
                bet_type = f"{home_team} ML"
            else:
                bet_team = away_team if bet_away > 0 else home_team
                bet_side = 'away' if bet_away > 0 else 'home'
                bet_type = f"{away_team if bet_away > 0 else home_team} ML"

            # Fetch odds
            game_odds = self._get_team_odds('icehockey_nhl', home_team, away_team)

            if game_odds:
                odds = game_odds.get(bet_side, 0)

                # Filter out heavy favorites
                if odds < self.max_favorite_odds:
                    return bets  # Skip this bet

                # Calculate true EV
                estimated_win_prob = 0.50 + (total_edge / 100)  # Edge above 50%
                true_ev = self._calculate_true_ev(odds, estimated_win_prob)

                # Filter by minimum EV
                if true_ev < self.min_value_threshold:
                    return bets  # Skip low value bets

                bets.append({
                    'sport': 'NHL',
                    'game': f"{away_team} @ {home_team}",
                    'bet_type': 'Moneyline',
                    'bet': bet_type,
                    'odds': odds,
                    'expected_edge': total_edge,
                    'true_ev': true_ev * 100,  # Convert to percentage
                    'angles': angles_found,
                    'angle_count': len(angles_found),
                    'confidence': self._calculate_confidence(total_edge, len(angles_found))
                })
            else:
                # No odds available, use edge-only ranking
                bets.append({
                    'sport': 'NHL',
                    'game': f"{away_team} @ {home_team}",
                    'bet_type': 'Moneyline',
                    'bet': bet_type,
                    'odds': None,
                    'expected_edge': total_edge,
                    'true_ev': total_edge,  # Fallback to angle edge
                    'angles': angles_found,
                    'angle_count': len(angles_found),
                    'confidence': self._calculate_confidence(total_edge, len(angles_found))
                })

        return bets

    def _collect_nba_bets(self) -> List[Dict]:
        """Collect all NBA betting opportunities"""
        bets = []

        # Get today's games
        games = self.nba_analyzer.get_games_for_date(self.date)

        if not games:
            return bets

        # Build schedule context
        self.nba_analyzer._build_schedule_context(self.date)

        # Analyze each game
        for game in games:
            home_team = game.get('home_team', '')
            away_team = game.get('away_team', '')

            if not home_team or not away_team:
                continue

            # Moneyline bets from angles
            ml_bets = self._analyze_nba_moneyline(home_team, away_team)
            bets.extend(ml_bets)

        return bets

    def _analyze_nba_moneyline(self, home_team: str, away_team: str) -> List[Dict]:
        """Analyze NBA moneyline using angles"""
        bets = []

        angles_found = []
        total_edge = 0

        # Back-to-back (HOME→ROAD only, 80% win rate)
        b2b = self.nba_analyzer._analyze_back_to_back(home_team, away_team, self.date)
        if b2b:
            angles_found.append(b2b)
            total_edge += 12.0  # HOME→ROAD B2B: 80% win rate historical

        # Heavy schedule
        heavy = self.nba_analyzer._analyze_heavy_schedule(home_team, away_team, self.date)
        if heavy:
            angles_found.append(heavy)
            total_edge += 10.0

        # Rest advantage
        rest = self.nba_analyzer._analyze_rest_advantage(home_team, away_team, self.date)
        if rest:
            angles_found.append(rest)
            total_edge += 8.0

        # Road trip (4th+ game only, based on backtest)
        road_trip = self.nba_analyzer._analyze_road_trip_fatigue(home_team, away_team, self.date)
        if road_trip:
            angles_found.append(road_trip)
            # 5th+ games have even bigger edge (61.7% home win rate)
            edge = 11.7 if '5th' in str(road_trip.get('road_games', 0)) else 7.3
            total_edge += edge

        # Altitude (Denver)
        altitude = self.nba_analyzer._analyze_altitude_advantage(home_team, away_team, self.date)
        if altitude:
            angles_found.append(altitude)
            total_edge += 5.5

        if angles_found:
            # Determine bet direction
            bet_home = sum(1 for a in angles_found if 'home' in a['bet'].lower() or home_team in a['bet'])
            bet_away = len(angles_found) - bet_home

            if bet_home > bet_away:
                bet_team = home_team
                bet_side = 'home'
                bet_type = f"{home_team} ML"
            else:
                bet_team = away_team if bet_away > 0 else home_team
                bet_side = 'away' if bet_away > 0 else 'home'
                bet_type = f"{away_team if bet_away > 0 else home_team} ML"

            # Fetch odds
            game_odds = self._get_team_odds('basketball_nba', home_team, away_team)

            if game_odds:
                odds = game_odds.get(bet_side, 0)

                # Filter out heavy favorites
                if odds < self.max_favorite_odds:
                    return bets  # Skip this bet

                # Calculate true EV
                estimated_win_prob = 0.50 + (total_edge / 100)
                true_ev = self._calculate_true_ev(odds, estimated_win_prob)

                # Filter by minimum EV
                if true_ev < self.min_value_threshold:
                    return bets

                bets.append({
                    'sport': 'NBA',
                    'game': f"{away_team} @ {home_team}",
                    'bet_type': 'Moneyline',
                    'bet': bet_type,
                    'odds': odds,
                    'expected_edge': total_edge,
                    'true_ev': true_ev * 100,
                    'angles': angles_found,
                    'angle_count': len(angles_found),
                    'confidence': self._calculate_confidence(total_edge, len(angles_found))
                })
            else:
                # No odds available, use edge-only ranking
                bets.append({
                    'sport': 'NBA',
                    'game': f"{away_team} @ {home_team}",
                    'bet_type': 'Moneyline',
                    'bet': bet_type,
                    'odds': None,
                    'expected_edge': total_edge,
                    'true_ev': total_edge,
                    'angles': angles_found,
                    'angle_count': len(angles_found),
                    'confidence': self._calculate_confidence(total_edge, len(angles_found))
                })

        return bets

    def _collect_soccer_bets(self) -> List[Dict]:
        """Collect all soccer betting opportunities"""
        bets = []

        # Get all matches for today
        matches = self.soccer_analyzer.get_all_matches(self.date)

        if not matches:
            return bets

        # Collect soccer bets with MEDIUM or HIGH confidence angles
        for match in matches:
            home_team = match.get('home_team', '')
            away_team = match.get('away_team', '')
            league = match.get('league', '')

            if not home_team or not away_team:
                continue

            angles_found = []
            total_edge = 0

            # Check for table position angles (HIGH and MEDIUM confidence)
            table = self.soccer_analyzer._analyze_table_position(home_team, away_team, league)
            if table:
                angles_found.append(table)
                # HIGH confidence gets 8.5%, MEDIUM gets 5%
                edge_value = 8.5 if table.get('confidence') == 'HIGH' else 5.0
                total_edge += edge_value

            # Check for home/away splits
            splits = self.soccer_analyzer._analyze_home_away_splits(home_team, away_team)
            if splits:
                angles_found.append(splits)
                # Different edge values based on type
                if 'weak_away' in splits.get('type', ''):
                    total_edge += 7.5
                elif 'home_fortress' in splits.get('type', ''):
                    total_edge += 6.5

            # Include if ANY angles found (minimum 4% edge to avoid noise)
            if angles_found and total_edge >= 4.0:
                # Determine confidence based on total edge
                if total_edge >= 10:
                    confidence = 'HIGH'
                elif total_edge >= 6:
                    confidence = 'MEDIUM'
                else:
                    confidence = 'LOW'

                bets.append({
                    'sport': 'SOCCER',
                    'game': f"{away_team} @ {home_team}",
                    'league': league,
                    'bet_type': 'Various',
                    'bet': angles_found[0]['bet'],
                    'expected_edge': total_edge,
                    'angles': angles_found,
                    'angle_count': len(angles_found),
                    'confidence': confidence
                })

        return bets

    def _collect_ncaa_bets(self) -> List[Dict]:
        """Collect all NCAA basketball betting opportunities"""
        bets = []

        # Get today's NCAA opportunities
        opportunities = self.ncaa_analyzer.analyze_schedule_for_date(self.date)

        if not opportunities:
            return bets

        # Convert NCAA opportunities to bet format
        # NCAA angles are typically spread-based, not ML-based
        for game in opportunities:
            home_team = game.get('home_team', '')
            away_team = game.get('away_team', '')
            angles = game.get('angles', [])

            if not angles:
                continue

            # Calculate total edge from all angles
            total_edge = 0
            for angle in angles:
                # Parse edge from angle (e.g., "+15%" -> 15.0)
                edge_str = angle.get('edge', '+0%')
                try:
                    # Handle ranges like "+10-15%" or single values like "+15%"
                    if '-' in edge_str and '%' in edge_str:
                        # Take the midpoint of the range
                        parts = edge_str.replace('+', '').replace('%', '').split('-')
                        edge_value = (float(parts[0]) + float(parts[1])) / 2
                    else:
                        edge_value = float(edge_str.replace('+', '').replace('%', ''))
                    total_edge += edge_value
                except:
                    # Default edge if parsing fails
                    if angle.get('confidence') == 'HIGH':
                        edge_value = 12.0
                    elif angle.get('confidence') == 'MEDIUM-HIGH':
                        edge_value = 9.0
                    else:
                        edge_value = 6.0
                    total_edge += edge_value

            # Determine which team to bet based on angles
            bet_text = angles[0].get('bet', '')

            # NCAA angles are mainly for spread betting
            # Don't apply aggressive EV filtering like moneyline bets
            bets.append({
                'sport': 'NCAA',
                'game': f"{away_team} @ {home_team}",
                'bet_type': 'Spread',
                'bet': bet_text,
                'odds': None,  # Spread odds not fetched (typically -110)
                'expected_edge': total_edge,
                'true_ev': total_edge,  # Use angle edge directly for spreads
                'angles': angles,
                'angle_count': len(angles),
                'confidence': self._calculate_confidence(total_edge, len(angles))
            })

        return bets

    def _calculate_confidence(self, total_edge: float, angle_count: int) -> str:
        """Calculate confidence level"""
        if total_edge >= 15 and angle_count >= 2:
            return 'ELITE'
        elif total_edge >= 10 or angle_count >= 2:
            return 'HIGH'
        elif total_edge >= 7:
            return 'MEDIUM'
        else:
            return 'LOW'

    def _rank_all_bets(self) -> List[Dict]:
        """Rank all bets by expected value"""
        # Sort by expected edge (descending)
        ranked = sorted(self.all_bets, key=lambda x: x['expected_edge'], reverse=True)

        # Add rank
        for i, bet in enumerate(ranked, 1):
            bet['rank'] = i

        return ranked

    def _display_top_bets(self, ranked_bets: List[Dict]):
        """Display top 5-10 bets in clean format"""

        top_bets = ranked_bets[:10]

        print(f"\n{'='*80}")
        print(f"🏆 TOP 10 BETS TODAY - {self.date}")
        print(f"{'='*80}\n")

        # Group by confidence
        elite = [b for b in top_bets if b['confidence'] == 'ELITE']
        high = [b for b in top_bets if b['confidence'] == 'HIGH']
        medium = [b for b in top_bets if b['confidence'] == 'MEDIUM']

        print(f"📊 BREAKDOWN:")
        print(f"   🔥 ELITE: {len(elite)} bets")
        print(f"   ✅ HIGH: {len(high)} bets")
        print(f"   💡 MEDIUM: {len(medium)} bets\n")

        print(f"{'─'*80}\n")

        # Display each bet
        for bet in top_bets:
            rank = bet['rank']
            sport = bet['sport']
            game = bet['game']
            bet_type = bet['bet_type']
            bet_text = bet['bet']
            edge = bet['expected_edge']
            angles = bet['angle_count']
            confidence = bet['confidence']

            # Icon
            sport_icon = {'NHL': '🏒', 'NBA': '🏀', 'NCAA': '🏀', 'SOCCER': '⚽'}.get(sport, '🎯')
            conf_marker = {'ELITE': '🔥🔥🔥', 'HIGH': '✅', 'MEDIUM': '💡', 'LOW': '⚪'}.get(confidence, '')

            odds = bet.get('odds')
            true_ev = bet.get('true_ev', edge)

            print(f"{conf_marker} #{rank} {sport_icon} {sport}: {game}")
            print(f"   BET: {bet_text}")

            # Show odds if available
            if odds:
                odds_display = f"{odds:+d}" if odds else "N/A"
                print(f"   ODDS: {odds_display} | True EV: +{true_ev:.1f}% | Angles: {angles}")
            else:
                print(f"   Expected Edge: +{edge:.1f}% | Angles: {angles} | Confidence: {confidence}")

            # Show reasons (top 2 angles)
            for i, angle in enumerate(bet['angles'][:2], 1):
                reason = angle.get('reason', '')
                print(f"   {i}. {reason}")

            # Bet size recommendation
            if confidence == 'ELITE':
                print(f"   💰 RECOMMENDED: Bet 2-3% of bankroll")
            elif confidence == 'HIGH':
                print(f"   💰 RECOMMENDED: Bet 1-2% of bankroll")
            elif confidence == 'MEDIUM':
                print(f"   💰 RECOMMENDED: Bet 0.5-1% of bankroll")

            print()

        # Summary
        print(f"{'='*80}")
        print(f"💰 BANKROLL ALLOCATION GUIDE")
        print(f"{'='*80}")
        print(f"\n🔥 ELITE ({len(elite)} bets): Bet 2-3% each")
        print(f"   → Total allocation: {len(elite) * 2.5:.0f}% of bankroll\n")

        print(f"✅ HIGH ({len(high)} bets): Bet 1-2% each")
        print(f"   → Total allocation: {len(high) * 1.5:.0f}% of bankroll\n")

        print(f"💡 MEDIUM ({len(medium)} bets): Bet 0.5-1% each (optional)")
        print(f"   → Total allocation: {len(medium) * 0.75:.0f}% of bankroll\n")

        total_allocation = (len(elite) * 2.5) + (len(high) * 1.5) + (len(medium) * 0.75)
        print(f"📊 TOTAL RECOMMENDED ALLOCATION: {total_allocation:.0f}% of bankroll")

        if total_allocation > 20:
            print(f"⚠️  WARNING: High allocation today. Consider reducing bet sizes.")

        print(f"{'='*80}\n")

    def save_report(self, ranked_bets: List[Dict]):
        """Save report to file"""
        report_file = f"/Users/dickgibbons/sports-betting/reports/report_{self.date}.txt"

        os.makedirs("/Users/dickgibbons/sports-betting/reports", exist_ok=True)

        with open(report_file, 'w') as f:
            f.write(f"DAILY BETTING REPORT - {self.date}\n")
            f.write(f"{'='*80}\n\n")

            for i, bet in enumerate(ranked_bets[:10], 1):
                f.write(f"#{i} {bet['sport']}: {bet['game']}\n")
                f.write(f"BET: {bet['bet']}\n")
                f.write(f"Edge: +{bet['expected_edge']:.1f}% | Confidence: {bet['confidence']}\n")
                f.write(f"\n")

        print(f"📄 Report saved to: {report_file}")

    def _log_bets_to_tracker(self, bets: List[Dict]):
        """Log all recommended bets to the bet tracker"""

        print(f"\n{'='*80}")
        print(f"📝 LOGGING BETS TO TRACKER")
        print(f"{'='*80}\n")

        for bet in bets:
            # Add date to bet record
            bet['date'] = self.date

            bet_id = self.bet_tracker.log_bet(bet)
            print(f"✅ Logged: {bet_id} - {bet['bet']}")

        print(f"\n💡 To update results later, run: python3 bet_tracker.py")
        print(f"{'='*80}\n")


def main():
    # First, auto-update results from previous days
    print("\n🔄 Checking for completed games from previous days...")
    try:
        from auto_update_results import AutoResultsUpdater
        updater = AutoResultsUpdater()
        updater.update_all_pending_bets()
    except Exception as e:
        print(f"   ⚠️  Could not auto-update results: {e}")

    # Second, learn from performance and adjust angle weights
    print("\n🧠 Learning from bet performance...")
    try:
        from angle_performance_learner import AnglePerformanceLearner
        learner = AnglePerformanceLearner()
        learner.analyze_and_adjust()
    except Exception as e:
        print(f"   ⚠️  Could not run performance learning: {e}")

    # Generate today's report
    report = DailyBettingReport()
    top_bets = report.generate_daily_report()
    report.save_report(top_bets)

    # Show cumulative performance summary
    print("\n" + "="*80)
    print("📊 CUMULATIVE PERFORMANCE SUMMARY")
    print("="*80)

    try:
        summary = report.bet_tracker.get_performance_summary()

        if 'error' not in summary:
            print(f"\n💰 OVERALL STATS:")
            print(f"   Record: {summary['wins']}-{summary['losses']}-{summary['pushes']}")
            print(f"   Win Rate: {summary['win_rate']:.1f}%")
            print(f"   Bankroll: ${summary['current_bankroll']:,.2f} (started ${report.bet_tracker.starting_bankroll:,.2f})")
            print(f"   Total Profit: ${summary['total_profit']:+,.2f}")
            print(f"   ROI: {summary['roi']:.1f}%")
            print(f"   Pending Bets: {summary['pending_bets']}")
        else:
            print(f"\n   No settled bets yet - keep betting!")

    except Exception as e:
        print(f"   ⚠️  Could not generate summary: {e}")

    print("\n" + "="*80)

    print("\n✅ Daily report complete!")
    print(f"   Run this every morning: python3 daily_betting_report.py")
    print(f"\n💡 For detailed performance breakdown, run: python3 bet_tracker.py")


if __name__ == "__main__":
    main()
