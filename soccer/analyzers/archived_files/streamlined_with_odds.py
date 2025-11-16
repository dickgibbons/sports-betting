#!/usr/bin/env python3
"""
Streamlined Generator with Enhanced Odds
Combines existing reports with The Odds API data
"""

import json
import csv
from datetime import datetime
import os
from odds_api_integration import OddsAPIClient

def generate_streamlined_reports_with_odds():
    """Generate streamlined reports enhanced with The Odds API data"""

    date_str = datetime.now().strftime("%Y%m%d")
    date_readable = datetime.now().strftime("%Y-%m-%d")

    print(f"🎯 Generating streamlined reports with enhanced odds for {date_readable}")
    print("=" * 60)

    # Initialize Odds API client
    odds_client = OddsAPIClient("fc8b43bb8508b51b52b52fd1827eaaf4")

    # Ensure output directory exists
    os.makedirs("output reports", exist_ok=True)

    # Load fixtures if available
    fixtures = []
    fixture_file = f"real_fixtures_{date_str}.json"
    if os.path.exists(fixture_file):
        with open(fixture_file, 'r') as f:
            fixtures = json.load(f)
        print(f"📊 Loaded {len(fixtures)} local fixtures")

    # Get enhanced odds from major leagues
    print("💰 Fetching enhanced odds from The Odds API...")
    enhanced_odds = {}

    major_leagues = ['soccer_epl', 'soccer_spain_la_liga', 'soccer_usa_mls']

    for league in major_leagues:
        try:
            # Get just h2h odds to avoid API limits
            odds_data = odds_client.get_odds_for_sport(league, ['h2h'])
            if odds_data:
                enhanced_odds[league] = odds_data
                print(f"   ✅ {league}: {len(odds_data)} matches with odds")
            else:
                print(f"   ⚠️ {league}: No odds data available")
        except Exception as e:
            print(f"   ❌ {league}: Error fetching odds - {e}")

    reports_generated = []

    # 1. Enhanced daily_picks with odds comparison
    filename = f"output reports/daily_picks_{date_str}.csv"
    with open(filename, 'w', newline='') as f:
        fieldnames = ['date', 'time', 'home_team', 'away_team', 'league', 'market',
                     'best_odds', 'avg_odds', 'bookmaker', 'confidence', 'stake_pct',
                     'odds_value', 'bookmaker_count']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        picks_added = 0

        # Add enhanced picks from odds analysis
        for league, matches in enhanced_odds.items():
            for match in matches[:3]:  # Top 3 per league
                odds_analysis = analyze_match_odds(match)
                if odds_analysis['has_value']:
                    writer.writerow({
                        'date': date_readable,
                        'time': match.get('commence_time', 'TBD'),
                        'home_team': match.get('home_team', 'Unknown'),
                        'away_team': match.get('away_team', 'Unknown'),
                        'league': league.replace('soccer_', '').replace('_', ' ').title(),
                        'market': odds_analysis['best_market'],
                        'best_odds': odds_analysis['best_odds'],
                        'avg_odds': odds_analysis['avg_odds'],
                        'bookmaker': odds_analysis['best_bookmaker'],
                        'confidence': f"{odds_analysis['confidence']:.1f}%",
                        'stake_pct': f"{odds_analysis['stake_pct']:.1f}%",
                        'odds_value': f"{odds_analysis['value']:.1f}%",
                        'bookmaker_count': odds_analysis['bookmaker_count']
                    })
                    picks_added += 1

        if picks_added == 0:
            writer.writerow({
                'date': date_readable,
                'time': 'N/A',
                'home_team': 'No value picks today',
                'away_team': 'Conservative approach',
                'league': 'Risk Management',
                'market': 'No opportunities found',
                'best_odds': 'N/A',
                'avg_odds': 'N/A',
                'bookmaker': 'Multiple sources checked',
                'confidence': 'Waiting',
                'stake_pct': '0%',
                'odds_value': 'N/A',
                'bookmaker_count': 'Various'
            })

    reports_generated.append(f"daily_picks_{date_str}.csv")
    print(f"✅ Enhanced daily picks: {picks_added} value opportunities")

    # 2. Daily all games with odds comparison
    filename = f"output reports/daily_all_games_{date_str}.csv"
    with open(filename, 'w', newline='') as f:
        fieldnames = ['date', 'home_team', 'away_team', 'league', 'best_home_odds',
                     'best_draw_odds', 'best_away_odds', 'home_bookmaker', 'draw_bookmaker',
                     'away_bookmaker', 'bookmaker_count', 'arbitrage_opportunity',
                     'analysis', 'recommendation']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        games_processed = 0

        for league, matches in enhanced_odds.items():
            for match in matches[:10]:  # Top 10 per league
                odds_details = extract_detailed_odds(match)
                writer.writerow({
                    'date': date_readable,
                    'home_team': match.get('home_team', 'Team A'),
                    'away_team': match.get('away_team', 'Team B'),
                    'league': league.replace('soccer_', '').replace('_', ' ').title(),
                    'best_home_odds': odds_details['best_home_odds'],
                    'best_draw_odds': odds_details['best_draw_odds'],
                    'best_away_odds': odds_details['best_away_odds'],
                    'home_bookmaker': odds_details['home_bookmaker'],
                    'draw_bookmaker': odds_details['draw_bookmaker'],
                    'away_bookmaker': odds_details['away_bookmaker'],
                    'bookmaker_count': odds_details['bookmaker_count'],
                    'arbitrage_opportunity': odds_details['arbitrage_opportunity'],
                    'analysis': odds_details['analysis'],
                    'recommendation': odds_details['recommendation']
                })
                games_processed += 1

        if games_processed == 0:
            writer.writerow({
                'date': date_readable,
                'home_team': 'No enhanced odds available',
                'away_team': 'System in conservative mode',
                'league': 'Various',
                'best_home_odds': 'N/A',
                'best_draw_odds': 'N/A',
                'best_away_odds': 'N/A',
                'home_bookmaker': 'Multiple',
                'draw_bookmaker': 'Multiple',
                'away_bookmaker': 'Multiple',
                'bookmaker_count': '0',
                'arbitrage_opportunity': 'None',
                'analysis': 'Waiting for odds data',
                'recommendation': 'Monitor'
            })

    reports_generated.append(f"daily_all_games_{date_str}.csv")
    print(f"✅ Enhanced all games: {games_processed} matches analyzed")

    # 3. Enhanced odds summary
    filename = f"output reports/enhanced_odds_summary_{date_str}.csv"
    with open(filename, 'w', newline='') as f:
        fieldnames = ['league', 'matches_found', 'bookmakers_avg', 'arbitrage_opportunities',
                     'value_bets_found', 'best_value_pct', 'status']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for league, matches in enhanced_odds.items():
            summary = calculate_league_summary(matches)
            writer.writerow({
                'league': league.replace('soccer_', '').replace('_', ' ').title(),
                'matches_found': len(matches),
                'bookmakers_avg': summary['avg_bookmakers'],
                'arbitrage_opportunities': summary['arbitrage_count'],
                'value_bets_found': summary['value_bets'],
                'best_value_pct': f"{summary['best_value']:.1f}%",
                'status': summary['status']
            })

    reports_generated.append(f"enhanced_odds_summary_{date_str}.csv")

    print(f"\n✅ Generated {len(reports_generated)} enhanced reports:")
    for report in reports_generated:
        print(f"   • {report}")

    print(f"\n💰 Enhanced with The Odds API:")
    print(f"   • {len(enhanced_odds)} leagues analyzed")
    print(f"   • {sum(len(matches) for matches in enhanced_odds.values())} total matches")
    print(f"   • Multiple bookmaker comparison")
    print(f"   • Arbitrage opportunity detection")

    return reports_generated

def analyze_match_odds(match):
    """Analyze a match for value betting opportunities"""

    analysis = {
        'has_value': False,
        'best_market': 'H2H',
        'best_odds': 0,
        'avg_odds': 0,
        'best_bookmaker': 'Unknown',
        'confidence': 0,
        'stake_pct': 0,
        'value': 0,
        'bookmaker_count': 0
    }

    bookmakers = match.get('bookmakers', [])
    analysis['bookmaker_count'] = len(bookmakers)

    if not bookmakers:
        return analysis

    # Collect all h2h odds
    home_odds = []
    draw_odds = []
    away_odds = []

    for bookmaker in bookmakers:
        for market in bookmaker.get('markets', []):
            if market.get('key') == 'h2h':
                for outcome in market.get('outcomes', []):
                    name = outcome.get('name', '').lower()
                    price = outcome.get('price', 0)
                    bookie = bookmaker.get('title', 'Unknown')

                    if any(x in name for x in [match.get('home_team', '').lower()]):
                        home_odds.append({'bookmaker': bookie, 'odds': price})
                    elif 'draw' in name:
                        draw_odds.append({'bookmaker': bookie, 'odds': price})
                    else:
                        away_odds.append({'bookmaker': bookie, 'odds': price})

    # Find best value
    best_value = 0
    best_outcome = None

    for outcome_name, odds_list in [('Home', home_odds), ('Draw', draw_odds), ('Away', away_odds)]:
        if len(odds_list) >= 2:  # Need at least 2 bookmakers for comparison
            best = max(odds_list, key=lambda x: x['odds'])
            avg = sum(x['odds'] for x in odds_list) / len(odds_list)
            value = (best['odds'] - avg) / avg * 100

            if value > best_value:
                best_value = value
                best_outcome = {
                    'market': outcome_name,
                    'best_odds': best['odds'],
                    'avg_odds': round(avg, 3),
                    'bookmaker': best['bookmaker'],
                    'value': value
                }

    if best_outcome and best_value > 3:  # 3% value threshold
        analysis.update({
            'has_value': True,
            'best_market': best_outcome['market'],
            'best_odds': best_outcome['best_odds'],
            'avg_odds': best_outcome['avg_odds'],
            'best_bookmaker': best_outcome['bookmaker'],
            'confidence': min(70 + best_value * 2, 95),  # Conservative confidence
            'stake_pct': min(best_value / 2, 5),  # Max 5% stake
            'value': best_value
        })

    return analysis

def extract_detailed_odds(match):
    """Extract detailed odds information for a match"""

    details = {
        'best_home_odds': 'N/A',
        'best_draw_odds': 'N/A',
        'best_away_odds': 'N/A',
        'home_bookmaker': 'N/A',
        'draw_bookmaker': 'N/A',
        'away_bookmaker': 'N/A',
        'bookmaker_count': 0,
        'arbitrage_opportunity': 'No',
        'analysis': 'Insufficient data',
        'recommendation': 'Monitor'
    }

    bookmakers = match.get('bookmakers', [])
    details['bookmaker_count'] = len(bookmakers)

    if not bookmakers:
        return details

    # Extract best odds for each outcome
    home_odds = []
    draw_odds = []
    away_odds = []

    for bookmaker in bookmakers:
        for market in bookmaker.get('markets', []):
            if market.get('key') == 'h2h':
                for outcome in market.get('outcomes', []):
                    name = outcome.get('name', '').lower()
                    price = outcome.get('price', 0)
                    bookie = bookmaker.get('title', 'Unknown')

                    if any(x in name for x in [match.get('home_team', '').lower()]):
                        home_odds.append({'bookmaker': bookie, 'odds': price})
                    elif 'draw' in name:
                        draw_odds.append({'bookmaker': bookie, 'odds': price})
                    else:
                        away_odds.append({'bookmaker': bookie, 'odds': price})

    # Find best odds
    if home_odds:
        best_home = max(home_odds, key=lambda x: x['odds'])
        details['best_home_odds'] = best_home['odds']
        details['home_bookmaker'] = best_home['bookmaker']

    if draw_odds:
        best_draw = max(draw_odds, key=lambda x: x['odds'])
        details['best_draw_odds'] = best_draw['odds']
        details['draw_bookmaker'] = best_draw['bookmaker']

    if away_odds:
        best_away = max(away_odds, key=lambda x: x['odds'])
        details['best_away_odds'] = best_away['odds']
        details['away_bookmaker'] = best_away['bookmaker']

    # Check for arbitrage
    if all(isinstance(details[k], (int, float)) for k in ['best_home_odds', 'best_away_odds']):
        home_prob = 1 / details['best_home_odds']
        away_prob = 1 / details['best_away_odds']
        draw_prob = 1 / details['best_draw_odds'] if isinstance(details['best_draw_odds'], (int, float)) else 0

        total_prob = home_prob + away_prob + draw_prob

        if total_prob < 1:
            details['arbitrage_opportunity'] = f"Yes ({(1-total_prob)*100:.1f}%)"
            details['analysis'] = "Arbitrage opportunity detected"
            details['recommendation'] = "Consider arbitrage"
        else:
            details['analysis'] = f"{len(bookmakers)} bookmakers compared"
            details['recommendation'] = "Monitor for value"

    return details

def calculate_league_summary(matches):
    """Calculate summary statistics for a league"""

    summary = {
        'avg_bookmakers': 0,
        'arbitrage_count': 0,
        'value_bets': 0,
        'best_value': 0,
        'status': 'No data'
    }

    if not matches:
        return summary

    total_bookmakers = 0
    arbitrage_found = 0
    value_found = 0
    max_value = 0

    for match in matches:
        # Count bookmakers
        bookmaker_count = len(match.get('bookmakers', []))
        total_bookmakers += bookmaker_count

        # Check for value
        analysis = analyze_match_odds(match)
        if analysis['has_value']:
            value_found += 1
            max_value = max(max_value, analysis['value'])

        # Check arbitrage
        details = extract_detailed_odds(match)
        if 'Yes' in details['arbitrage_opportunity']:
            arbitrage_found += 1

    summary.update({
        'avg_bookmakers': round(total_bookmakers / len(matches), 1) if matches else 0,
        'arbitrage_count': arbitrage_found,
        'value_bets': value_found,
        'best_value': max_value,
        'status': 'Active' if matches else 'No data'
    })

    return summary

if __name__ == "__main__":
    generate_streamlined_reports_with_odds()