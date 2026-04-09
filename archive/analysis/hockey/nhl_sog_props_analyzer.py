#!/usr/bin/env python3
"""
NHL Shots on Goal (SOG) Props Analyzer

Identifies profitable player prop bets for shots on goal.
Key factors:
- Player's SOG/game average and recent form
- Time on ice (TOI) and power play time
- Opponent's shots allowed per game
- Position-specific matchups

Sources:
- Core Sports Betting: NHL Player Shots on Goal Prop Betting Strategy
- Covers: Hockey Prop Bets Tips
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import json


class NHLSOGPropsAnalyzer:
    """Analyze player shot props for NHL games"""

    def __init__(self):
        self.nhl_api = "https://api-web.nhle.com/v1"
        self.player_cache = {}
        self.team_defense_cache = {}
        print("NHL SOG Props Analyzer initialized")

    def get_todays_games(self, date: str = None) -> List[Dict]:
        """Get today's NHL schedule"""
        date = date or datetime.now().strftime("%Y-%m-%d")
        url = f"{self.nhl_api}/schedule/{date}"

        try:
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                return []

            data = response.json()
            games = []

            for day in data.get("gameWeek", []):
                if day.get("date") == date:
                    for game in day.get("games", []):
                        games.append({
                            "game_id": game.get("id"),
                            "date": date,
                            "home_team": game.get("homeTeam", {}).get("abbrev", ""),
                            "away_team": game.get("awayTeam", {}).get("abbrev", ""),
                        })
            return games
        except Exception as e:
            print(f"Error fetching schedule: {e}")
            return []

    def get_team_stats(self, season: str = "20242025") -> Dict:
        """Get team stats for shots allowed analysis"""
        url = f"{self.nhl_api}/standings/now"

        try:
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                return {}

            data = response.json()
            team_stats = {}

            for team in data.get("standings", []):
                abbrev = team.get("teamAbbrev", {}).get("default", "")
                gp = team.get("gamesPlayed", 0)
                goals_against = team.get("goalAgainst", 0)

                if gp > 0:
                    team_stats[abbrev] = {
                        "games_played": gp,
                        "goals_against": goals_against,
                        "ga_per_game": goals_against / gp
                    }

            return team_stats
        except Exception as e:
            print(f"Error fetching team stats: {e}")
            return {}

    def get_player_stats(self, team_abbrev: str, season: str = "20242025") -> List[Dict]:
        """Get player stats for a team - focusing on top shooters"""
        # Use club stats endpoint
        url = f"{self.nhl_api}/club-stats/{team_abbrev}/{season}/2"  # 2 = regular season

        try:
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                return []

            data = response.json()
            players = []

            # Get skaters
            for player in data.get("skaters", []):
                games = player.get("gamesPlayed", 0)
                if games < 5:  # Need sample size
                    continue

                shots = player.get("shots", 0)
                toi = player.get("avgToi", "00:00")

                # Parse TOI
                try:
                    mins, secs = toi.split(":")
                    toi_minutes = int(mins) + int(secs) / 60
                except:
                    toi_minutes = 0

                sog_per_game = shots / games if games > 0 else 0

                players.append({
                    "player_id": player.get("playerId"),
                    "name": f"{player.get('firstName', {}).get('default', '')} {player.get('lastName', {}).get('default', '')}",
                    "position": player.get("positionCode", ""),
                    "team": team_abbrev,
                    "games_played": games,
                    "shots": shots,
                    "sog_per_game": round(sog_per_game, 2),
                    "avg_toi": round(toi_minutes, 1),
                    "goals": player.get("goals", 0),
                    "pp_goals": player.get("powerPlayGoals", 0),
                })

            # Sort by shots per game
            players.sort(key=lambda x: x["sog_per_game"], reverse=True)

            return players[:20]  # Top 20 shooters

        except Exception as e:
            print(f"Error fetching player stats for {team_abbrev}: {e}")
            return []

    def get_team_shots_allowed(self) -> Dict:
        """Get shots allowed per game for each team (defensive weakness indicator)"""
        # This data would ideally come from NHL API team stats
        # Using estimated values based on general NHL averages
        # Teams average about 30 shots/game, so we'll calculate relative to that

        url = f"{self.nhl_api}/standings/now"
        try:
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                return {}

            data = response.json()
            shots_allowed = {}

            # Get goals against as proxy for defensive quality
            for team in data.get("standings", []):
                abbrev = team.get("teamAbbrev", {}).get("default", "")
                gp = team.get("gamesPlayed", 0)
                ga = team.get("goalAgainst", 0)

                if gp > 0:
                    # Higher GA/game = worse defense = more shots likely allowed
                    ga_per_game = ga / gp
                    # Estimate shots allowed (roughly 10x goals against, adjusted)
                    # League average is about 30 shots allowed
                    estimated_shots = 28 + (ga_per_game - 2.8) * 3

                    shots_allowed[abbrev] = {
                        "estimated_shots_allowed": round(estimated_shots, 1),
                        "defensive_rating": "WEAK" if ga_per_game > 3.2 else ("STRONG" if ga_per_game < 2.5 else "AVERAGE"),
                        "ga_per_game": round(ga_per_game, 2)
                    }

            return shots_allowed
        except Exception as e:
            print(f"Error: {e}")
            return {}

    def analyze_matchup(self, shooter: Dict, opponent: Dict) -> Dict:
        """Analyze a shooter vs opponent matchup"""
        analysis = {
            "player": shooter["name"],
            "team": shooter["team"],
            "opponent": opponent.get("team", ""),
            "sog_avg": shooter["sog_per_game"],
            "toi": shooter["avg_toi"],
            "games": shooter["games_played"],
            "opp_defense": opponent.get("defensive_rating", "AVERAGE"),
            "opp_ga_per_game": opponent.get("ga_per_game", 2.8),
            "signals": []
        }

        signals = []

        # High volume shooter vs weak defense
        if shooter["sog_per_game"] >= 3.0 and opponent.get("defensive_rating") == "WEAK":
            signals.append({
                "type": "HIGH_VOLUME_VS_WEAK_D",
                "bet": f"{shooter['name']} OVER {shooter['sog_per_game'] - 0.5:.1f} SOG",
                "reasoning": f"Averaging {shooter['sog_per_game']} SOG vs weak defense ({opponent.get('ga_per_game', 0):.2f} GA/G)",
                "confidence": "HIGH"
            })

        # Elite shooter (4+ SOG/game)
        elif shooter["sog_per_game"] >= 4.0:
            signals.append({
                "type": "ELITE_SHOOTER",
                "bet": f"{shooter['name']} OVER 3.5 SOG",
                "reasoning": f"Elite shooter averaging {shooter['sog_per_game']} SOG/game",
                "confidence": "HIGH"
            })

        # Good volume with high TOI
        elif shooter["sog_per_game"] >= 3.0 and shooter["avg_toi"] >= 18:
            signals.append({
                "type": "VOLUME_PLUS_TOI",
                "bet": f"{shooter['name']} OVER 2.5 SOG",
                "reasoning": f"{shooter['sog_per_game']} SOG/G with {shooter['avg_toi']} min TOI",
                "confidence": "MEDIUM"
            })

        # Defender with good shot volume vs weak D
        if shooter["position"] in ["D", "LD", "RD"] and shooter["sog_per_game"] >= 2.5:
            if opponent.get("defensive_rating") == "WEAK":
                signals.append({
                    "type": "DMAN_VS_WEAK_D",
                    "bet": f"{shooter['name']} OVER 2.5 SOG",
                    "reasoning": f"D-man averaging {shooter['sog_per_game']} SOG vs weak defense",
                    "confidence": "MEDIUM"
                })

        analysis["signals"] = signals
        return analysis

    def analyze_today(self, date: str = None) -> Dict:
        """Analyze all games for SOG prop opportunities"""
        date = date or datetime.now().strftime("%Y-%m-%d")
        games = self.get_todays_games(date)

        if not games:
            return {"date": date, "games": [], "best_bets": []}

        # Get team defensive stats
        team_defense = self.get_team_shots_allowed()

        all_analysis = {
            "date": date,
            "games": [],
            "best_bets": []
        }

        for game in games:
            home = game["home_team"]
            away = game["away_team"]

            game_analysis = {
                "matchup": f"{away} @ {home}",
                "players": []
            }

            # Analyze away team shooters vs home defense
            away_players = self.get_player_stats(away)
            home_defense = team_defense.get(home, {"defensive_rating": "AVERAGE", "ga_per_game": 2.8, "team": home})
            home_defense["team"] = home

            for player in away_players[:10]:  # Top 10 shooters
                analysis = self.analyze_matchup(player, home_defense)
                if analysis["signals"]:
                    game_analysis["players"].append(analysis)
                    for signal in analysis["signals"]:
                        if signal["confidence"] == "HIGH":
                            all_analysis["best_bets"].append({
                                "matchup": game_analysis["matchup"],
                                "player": analysis["player"],
                                "bet": signal["bet"],
                                "type": signal["type"],
                                "reasoning": signal["reasoning"]
                            })

            # Analyze home team shooters vs away defense
            home_players = self.get_player_stats(home)
            away_defense = team_defense.get(away, {"defensive_rating": "AVERAGE", "ga_per_game": 2.8, "team": away})
            away_defense["team"] = away

            for player in home_players[:10]:
                analysis = self.analyze_matchup(player, away_defense)
                if analysis["signals"]:
                    game_analysis["players"].append(analysis)
                    for signal in analysis["signals"]:
                        if signal["confidence"] == "HIGH":
                            all_analysis["best_bets"].append({
                                "matchup": game_analysis["matchup"],
                                "player": analysis["player"],
                                "bet": signal["bet"],
                                "type": signal["type"],
                                "reasoning": signal["reasoning"]
                            })

            if game_analysis["players"]:
                all_analysis["games"].append(game_analysis)

        return all_analysis

    def generate_report(self, date: str = None) -> str:
        """Generate formatted SOG props report"""
        analysis = self.analyze_today(date)

        lines = []
        lines.append("=" * 80)
        lines.append(f"NHL SHOTS ON GOAL PROPS REPORT - {analysis['date']}")
        lines.append("=" * 80)
        lines.append("")
        lines.append("Strategy: Target high-volume shooters vs weak defenses")
        lines.append("Key factors: SOG/game, TOI, opponent defensive quality")
        lines.append("")

        if analysis["best_bets"]:
            lines.append("⭐ BEST BETS (HIGH CONFIDENCE)")
            lines.append("-" * 40)
            for i, bet in enumerate(analysis["best_bets"], 1):
                lines.append(f"{i}. {bet['player']} ({bet['matchup']})")
                lines.append(f"   BET: {bet['bet']}")
                lines.append(f"   WHY: {bet['reasoning']}")
                lines.append("")
        else:
            lines.append("No high-confidence SOG props identified today.")
            lines.append("")

        lines.append("-" * 80)
        lines.append("📊 ALL PLAYER ANALYSIS")
        lines.append("-" * 80)

        for game in analysis["games"]:
            lines.append(f"\n🏒 {game['matchup']}")
            lines.append("-" * 40)

            for player_analysis in game["players"]:
                lines.append(f"  {player_analysis['player']} ({player_analysis['team']})")
                lines.append(f"    SOG/G: {player_analysis['sog_avg']} | TOI: {player_analysis['toi']} min")
                lines.append(f"    vs {player_analysis['opponent']} ({player_analysis['opp_defense']} defense)")

                for signal in player_analysis["signals"]:
                    lines.append(f"    📌 [{signal['confidence']}] {signal['bet']}")

        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)

    def save_report(self, date: str = None):
        """Generate and save report"""
        date = date or datetime.now().strftime("%Y-%m-%d")
        report = self.generate_report(date)
        print(report)

        from pathlib import Path
        daily_dir = Path(f"/Users/dickgibbons/AI Projects/sports-betting/Daily Reports/{date}")
        daily_dir.mkdir(parents=True, exist_ok=True)

        report_path = daily_dir / f"nhl_sog_props_{date}.txt"
        with open(report_path, "w") as f:
            f.write(report)

        analysis = self.analyze_today(date)
        json_path = daily_dir / f"nhl_sog_props_{date}.json"
        with open(json_path, "w") as f:
            json.dump(analysis, f, indent=2)

        print(f"\n✅ Reports saved:")
        print(f"   {report_path}")
        print(f"   {json_path}")

        return analysis


def main():
    import argparse
    parser = argparse.ArgumentParser(description="NHL SOG Props Analyzer")
    parser.add_argument("--date", type=str, help="Date to analyze (YYYY-MM-DD)")
    args = parser.parse_args()

    analyzer = NHLSOGPropsAnalyzer()
    analyzer.save_report(args.date)


if __name__ == "__main__":
    main()
