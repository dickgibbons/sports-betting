#!/usr/bin/env python3
"""
API Fixture Tester
Tests multiple soccer/football APIs to see what match data is available
Creates comprehensive report showing matches per day for each API endpoint
"""

import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import os
from typing import Dict, List, Optional

class APIFixtureTester:
    """Test multiple APIs for soccer fixture data availability"""

    def __init__(self):
        self.apis = self.configure_apis()
        self.test_dates = self.generate_test_dates()

        print("🧪 API FIXTURE TESTER")
        print("📊 Testing multiple soccer APIs for fixture availability")
        print("🎯 Goal: Find working APIs with real match data")

    def configure_apis(self) -> List[Dict]:
        """Configure all APIs to test"""

        return [
            {
                'name': 'API-Sports (RapidAPI)',
                'base_url': 'https://v3.football.api-sports.io/fixtures',
                'headers': {
                    'X-RapidAPI-Key': 'demo',
                    'X-RapidAPI-Host': 'v3.football.api-sports.io'
                },
                'params_template': {'date': '{date}'},
                'rate_limit': 100,  # per day for free
                'notes': 'Popular API, good coverage'
            },
            {
                'name': 'Football-Data.org',
                'base_url': 'https://api.football-data.org/v4/matches',
                'headers': {'X-Auth-Token': 'demo'},
                'params_template': {'dateFrom': '{date}', 'dateTo': '{date}'},
                'rate_limit': 10,  # per minute for free
                'notes': 'Official UEFA data partner'
            },
            {
                'name': 'FootyStats',
                'base_url': 'https://api.footystats.org/league-fixtures',
                'headers': {},
                'params_template': {'key': 'test', 'date': '{date}'},
                'rate_limit': 500,  # per day for free
                'notes': 'Good for statistics'
            },
            {
                'name': 'TheSportsDB',
                'base_url': 'https://www.thesportsdb.com/api/v1/json/3/eventsday.php',
                'headers': {},
                'params_template': {'d': '{date}', 's': 'Soccer'},
                'rate_limit': 1000,  # per hour for free
                'notes': 'Free community API'
            },
            {
                'name': 'OpenLigaDB (German)',
                'base_url': 'https://api.openligadb.de/getmatchdata/bl1/2025',
                'headers': {},
                'params_template': {},
                'rate_limit': 'Unlimited',
                'notes': 'Free German football data'
            },
            {
                'name': 'Premier League Official',
                'base_url': 'https://footballapi.pulselive.com/football/fixtures',
                'headers': {
                    'Accept': 'application/json',
                    'User-Agent': 'Mozilla/5.0'
                },
                'params_template': {'comps': '1', 'teams': '', 'page': '0', 'pageSize': '40', 'sort': 'desc'},
                'rate_limit': 'Unknown',
                'notes': 'Official PL data (may be restricted)'
            }
        ]

    def generate_test_dates(self) -> List[str]:
        """Generate list of dates to test (today +/- 7 days)"""

        dates = []
        today = datetime.now()

        # Test 7 days before to 7 days after today
        for i in range(-7, 8):
            test_date = today + timedelta(days=i)
            dates.append(test_date.strftime('%Y-%m-%d'))

        return dates

    def test_api_endpoint(self, api: Dict, date: str) -> Dict:
        """Test a specific API endpoint for a specific date"""

        result = {
            'api_name': api['name'],
            'date': date,
            'status': 'unknown',
            'matches_found': 0,
            'response_time': 0,
            'error_message': '',
            'sample_matches': [],
            'leagues_found': set()
        }

        try:
            start_time = datetime.now()

            # Build URL and parameters
            url = api['base_url']
            params = {}

            for key, template in api['params_template'].items():
                if '{date}' in template:
                    params[key] = template.format(date=date)
                else:
                    params[key] = template

            # Make request
            response = requests.get(
                url,
                headers=api['headers'],
                params=params,
                timeout=15
            )

            end_time = datetime.now()
            result['response_time'] = (end_time - start_time).total_seconds()

            if response.status_code == 200:
                result['status'] = 'success'
                data = response.json()

                # Parse response based on API type
                matches = self.parse_api_response(api['name'], data)
                result['matches_found'] = len(matches)
                result['sample_matches'] = matches[:3]  # First 3 matches as sample

                # Extract unique leagues
                for match in matches:
                    if 'league' in match:
                        result['leagues_found'].add(match['league'])

            elif response.status_code == 401:
                result['status'] = 'unauthorized'
                result['error_message'] = 'API key required or invalid'
            elif response.status_code == 403:
                result['status'] = 'forbidden'
                result['error_message'] = 'Access denied'
            elif response.status_code == 429:
                result['status'] = 'rate_limited'
                result['error_message'] = 'Rate limit exceeded'
            else:
                result['status'] = 'error'
                result['error_message'] = f'HTTP {response.status_code}'

        except requests.exceptions.Timeout:
            result['status'] = 'timeout'
            result['error_message'] = 'Request timeout (>15s)'
        except requests.exceptions.ConnectionError:
            result['status'] = 'connection_error'
            result['error_message'] = 'Unable to connect'
        except Exception as e:
            result['status'] = 'exception'
            result['error_message'] = str(e)

        return result

    def parse_api_response(self, api_name: str, data: dict) -> List[Dict]:
        """Parse API response based on API type"""

        matches = []

        try:
            if api_name == 'API-Sports (RapidAPI)':
                if 'response' in data:
                    for fixture in data['response']:
                        teams = fixture.get('teams', {})
                        match = {
                            'home_team': teams.get('home', {}).get('name', 'Unknown'),
                            'away_team': teams.get('away', {}).get('name', 'Unknown'),
                            'league': fixture.get('league', {}).get('name', 'Unknown'),
                            'date': fixture.get('fixture', {}).get('date', ''),
                            'status': fixture.get('fixture', {}).get('status', {}).get('long', 'Unknown')
                        }
                        matches.append(match)

            elif api_name == 'Football-Data.org':
                if 'matches' in data:
                    for match_data in data['matches']:
                        match = {
                            'home_team': match_data.get('homeTeam', {}).get('name', 'Unknown'),
                            'away_team': match_data.get('awayTeam', {}).get('name', 'Unknown'),
                            'league': match_data.get('competition', {}).get('name', 'Unknown'),
                            'date': match_data.get('utcDate', ''),
                            'status': match_data.get('status', 'Unknown')
                        }
                        matches.append(match)

            elif api_name == 'FootyStats':
                if 'data' in data:
                    for fixture in data['data']:
                        match = {
                            'home_team': fixture.get('home_name', 'Unknown'),
                            'away_team': fixture.get('away_name', 'Unknown'),
                            'league': fixture.get('league_name', 'Unknown'),
                            'date': fixture.get('date_unix', ''),
                            'status': fixture.get('status', 'Unknown')
                        }
                        matches.append(match)

            elif api_name == 'TheSportsDB':
                if 'events' in data and data['events']:
                    for event in data['events']:
                        match = {
                            'home_team': event.get('strHomeTeam', 'Unknown'),
                            'away_team': event.get('strAwayTeam', 'Unknown'),
                            'league': event.get('strLeague', 'Unknown'),
                            'date': event.get('dateEvent', ''),
                            'status': event.get('strStatus', 'Unknown')
                        }
                        matches.append(match)

            elif api_name == 'OpenLigaDB (German)':
                if isinstance(data, list):
                    for match_data in data:
                        match = {
                            'home_team': match_data.get('team1', {}).get('teamName', 'Unknown'),
                            'away_team': match_data.get('team2', {}).get('teamName', 'Unknown'),
                            'league': 'Bundesliga',
                            'date': match_data.get('matchDateTime', ''),
                            'status': 'Scheduled'
                        }
                        matches.append(match)

            elif api_name == 'Premier League Official':
                if 'content' in data:
                    for fixture in data['content']:
                        teams = fixture.get('teams', [])
                        home_team = next((t['team']['name'] for t in teams if t['score']['home'] is not None), 'Unknown')
                        away_team = next((t['team']['name'] for t in teams if t['score']['away'] is not None), 'Unknown')

                        match = {
                            'home_team': home_team,
                            'away_team': away_team,
                            'league': 'Premier League',
                            'date': fixture.get('kickoff', {}).get('millis', ''),
                            'status': fixture.get('status', 'Unknown')
                        }
                        matches.append(match)

        except Exception as e:
            print(f"⚠️ Error parsing {api_name} response: {e}")

        return matches

    def run_comprehensive_test(self) -> Dict:
        """Run comprehensive test across all APIs and dates"""

        print(f"🧪 Testing {len(self.apis)} APIs across {len(self.test_dates)} dates...")
        print(f"📅 Date range: {self.test_dates[0]} to {self.test_dates[-1]}")

        all_results = []
        api_summaries = {}

        for api in self.apis:
            print(f"\n🔍 Testing {api['name']}...")
            api_results = []

            for date in self.test_dates:
                print(f"  📅 {date}...", end='')
                result = self.test_api_endpoint(api, date)
                api_results.append(result)
                all_results.append(result)

                if result['matches_found'] > 0:
                    print(f" ✅ {result['matches_found']} matches")
                else:
                    print(f" ❌ {result['status']}")

            # Summarize API performance
            successful_days = len([r for r in api_results if r['status'] == 'success'])
            total_matches = sum([r['matches_found'] for r in api_results])
            avg_response_time = sum([r['response_time'] for r in api_results]) / len(api_results)

            api_summaries[api['name']] = {
                'successful_days': successful_days,
                'total_days_tested': len(self.test_dates),
                'total_matches_found': total_matches,
                'avg_response_time': avg_response_time,
                'success_rate': successful_days / len(self.test_dates),
                'unique_leagues': set()
            }

            # Collect unique leagues
            for result in api_results:
                api_summaries[api['name']]['unique_leagues'].update(result['leagues_found'])

        return {
            'test_timestamp': datetime.now().isoformat(),
            'apis_tested': len(self.apis),
            'dates_tested': len(self.test_dates),
            'date_range': {
                'start': self.test_dates[0],
                'end': self.test_dates[-1]
            },
            'detailed_results': all_results,
            'api_summaries': api_summaries
        }

    def generate_report(self, results: Dict) -> str:
        """Generate comprehensive API testing report"""

        report = f"""
🧪 COMPREHENSIVE API FIXTURE TESTING REPORT
{'='*80}
📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🎯 APIs Tested: {results['apis_tested']}
📊 Date Range: {results['date_range']['start']} to {results['date_range']['end']}
⏱️ Total Days Tested: {results['dates_tested']}

"""

        # API Performance Summary
        report += "📈 API PERFORMANCE SUMMARY:\n"
        report += "="*50 + "\n"

        sorted_apis = sorted(
            results['api_summaries'].items(),
            key=lambda x: (x[1]['success_rate'], x[1]['total_matches_found']),
            reverse=True
        )

        for api_name, summary in sorted_apis:
            success_rate = summary['success_rate'] * 100
            leagues = len(summary['unique_leagues'])

            report += f"""
🏆 {api_name}
   Success Rate: {success_rate:.1f}% ({summary['successful_days']}/{summary['total_days_tested']} days)
   Matches Found: {summary['total_matches_found']} total
   Avg Response: {summary['avg_response_time']:.2f} seconds
   Leagues Covered: {leagues} different leagues
   Status: {'✅ WORKING' if success_rate > 50 else '❌ ISSUES' if success_rate > 0 else '🔴 FAILED'}
"""

        # Best Performing APIs
        working_apis = [(api, summary) for api, summary in sorted_apis if summary['success_rate'] > 0.5]

        if working_apis:
            report += f"""
🌟 RECOMMENDED APIS FOR PRODUCTION:
{'='*45}
"""
            for api_name, summary in working_apis[:3]:
                report += f"""
✅ {api_name}
   - {summary['success_rate']*100:.1f}% uptime
   - {summary['total_matches_found']} matches found
   - {len(summary['unique_leagues'])} leagues
   - Avg response: {summary['avg_response_time']:.2f}s
"""

        else:
            report += """
⚠️ NO FULLY WORKING APIS FOUND
All tested APIs have issues or limitations
Consider:
  • Getting proper API keys
  • Using premium endpoints
  • Web scraping alternatives
"""

        # Daily Match Availability
        report += f"""
📅 DAILY MATCH AVAILABILITY:
{'='*35}
"""

        # Group results by date
        date_matches = {}
        for result in results['detailed_results']:
            date = result['date']
            if date not in date_matches:
                date_matches[date] = 0
            date_matches[date] += result['matches_found']

        for date in sorted(date_matches.keys()):
            total_matches = date_matches[date]
            day_name = datetime.strptime(date, '%Y-%m-%d').strftime('%A')

            if total_matches > 0:
                report += f"📊 {date} ({day_name}): {total_matches} matches found\n"
            else:
                report += f"❌ {date} ({day_name}): No matches\n"

        # API-Specific Issues
        report += f"""
🔧 COMMON API ISSUES FOUND:
{'='*30}
"""

        issue_counts = {}
        for result in results['detailed_results']:
            if result['status'] != 'success':
                issue = result['error_message'] or result['status']
                issue_counts[issue] = issue_counts.get(issue, 0) + 1

        for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
            report += f"❌ {issue}: {count} occurrences\n"

        # Recommendations
        report += f"""
💡 RECOMMENDATIONS:
{'='*20}
"""

        if working_apis:
            best_api = working_apis[0][0]
            report += f"🎯 Primary API: Use {best_api} as main data source\n"

            if len(working_apis) > 1:
                backup_api = working_apis[1][0]
                report += f"🔄 Backup API: Use {backup_api} as fallback\n"

        report += """
📋 Next Steps:
  1. Obtain proper API keys for best performing APIs
  2. Implement error handling and fallback logic
  3. Add caching to reduce API calls
  4. Consider rate limiting to stay within quotas
  5. Monitor API performance over time

⚠️ IMPORTANT NOTES:
  • Demo/test keys have severe limitations
  • Production use requires paid API plans
  • Some APIs may require application approval
  • Response times vary significantly
"""

        return report

    def save_results(self, results: Dict, report: str):
        """Save test results and report"""

        os.makedirs("output reports", exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Save JSON results
        json_file = f"output reports/api_test_results_{timestamp}.json"

        # Convert sets to lists for JSON serialization
        json_results = results.copy()
        for api_name, summary in json_results['api_summaries'].items():
            summary['unique_leagues'] = list(summary['unique_leagues'])

        with open(json_file, 'w') as f:
            json.dump(json_results, f, indent=2)

        # Save text report
        report_file = f"output reports/api_test_report_{timestamp}.txt"
        with open(report_file, 'w') as f:
            f.write(report)

        # Create CSV summary
        csv_data = []
        for result in results['detailed_results']:
            csv_data.append({
                'API': result['api_name'],
                'Date': result['date'],
                'Status': result['status'],
                'Matches_Found': result['matches_found'],
                'Response_Time': result['response_time'],
                'Error': result['error_message'],
                'Leagues': len(result['leagues_found'])
            })

        df = pd.DataFrame(csv_data)
        csv_file = f"output reports/api_test_data_{timestamp}.csv"
        df.to_csv(csv_file, index=False)

        print(f"\n📁 Results saved to:")
        print(f"   • {json_file}")
        print(f"   • {report_file}")
        print(f"   • {csv_file}")

def main():
    """Run comprehensive API testing"""

    tester = APIFixtureTester()
    results = tester.run_comprehensive_test()
    report = tester.generate_report(results)

    print(report)
    tester.save_results(results, report)

if __name__ == "__main__":
    main()