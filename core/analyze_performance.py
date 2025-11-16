#!/usr/bin/env python3
import json
from collections import defaultdict

with open("/Users/dickgibbons/sports-betting/data/bet_history.json", "r") as f:
    bets = json.load(f)

# Count wins/losses
wins = len([b for b in bets if b.get("result") == "WIN"])
losses = len([b for b in bets if b.get("result") == "LOSS"])
pending = len([b for b in bets if b.get("result") not in ["WIN", "LOSS"]])
total_bets = len(bets)

# Calculate profit/loss
total_profit = sum(b.get("profit", 0) for b in bets if b.get("result") in ["WIN", "LOSS"])

# Bankroll
starting_bankroll = 10000
current_bankroll = starting_bankroll + total_profit

# Win rate
win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0

# ROI
roi = (total_profit / starting_bankroll * 100) if starting_bankroll > 0 else 0

# By sport
sport_stats = defaultdict(lambda: {"wins": 0, "losses": 0, "profit": 0})
for bet in bets:
    if bet.get("result") in ["WIN", "LOSS"]:
        sport = bet.get("sport", "Unknown")
        if bet["result"] == "WIN":
            sport_stats[sport]["wins"] += 1
        else:
            sport_stats[sport]["losses"] += 1
        sport_stats[sport]["profit"] += bet.get("profit", 0)

# By confidence level
conf_stats = defaultdict(lambda: {"wins": 0, "losses": 0, "profit": 0})
for bet in bets:
    if bet.get("result") in ["WIN", "LOSS"]:
        conf = bet.get("confidence", "Unknown")
        if bet["result"] == "WIN":
            conf_stats[conf]["wins"] += 1
        else:
            conf_stats[conf]["losses"] += 1
        conf_stats[conf]["profit"] += bet.get("profit", 0)

print("="*80)
print("SPORTS BETTING SYSTEM - PERFORMANCE SUMMARY")
print("="*80)
print(f"\nBANKROLL")
print(f"  Starting: ${starting_bankroll:,.2f}")
print(f"  Current:  ${current_bankroll:,.2f}")
print(f"  Profit:   ${total_profit:+,.2f}")
print(f"  ROI:      {roi:+.2f}%")

print(f"\nOVERALL RECORD")
print(f"  Wins:     {wins}")
print(f"  Losses:   {losses}")
print(f"  Pending:  {pending}")
print(f"  Total:    {total_bets}")
print(f"  Win Rate: {win_rate:.1f}%")

print(f"\nBY SPORT")
for sport in ["NHL", "NBA", "SOCCER"]:
    if sport in sport_stats:
        stats = sport_stats[sport]
        total = stats["wins"] + stats["losses"]
        wr = (stats["wins"] / total * 100) if total > 0 else 0
        w = stats["wins"]
        l = stats["losses"]
        p = stats["profit"]
        print(f"  {sport}:")
        print(f"    Record: {w}-{l} ({wr:.1f}%)")
        print(f"    Profit: ${p:+,.2f}")

print(f"\nBY CONFIDENCE LEVEL")
for conf in ["ELITE", "HIGH", "MEDIUM", "LOW"]:
    if conf in conf_stats:
        stats = conf_stats[conf]
        total = stats["wins"] + stats["losses"]
        wr = (stats["wins"] / total * 100) if total > 0 else 0
        w = stats["wins"]
        l = stats["losses"]
        p = stats["profit"]
        print(f"  {conf}:")
        print(f"    Record: {w}-{l} ({wr:.1f}%)")
        print(f"    Profit: ${p:+,.2f}")

# Recent performance (last 10 bets)
recent = [b for b in bets if b.get("result") in ["WIN", "LOSS"]][-10:]
recent_wins = len([b for b in recent if b["result"] == "WIN"])
recent_losses = len([b for b in recent if b["result"] == "LOSS"])
recent_profit = sum(b.get("profit", 0) for b in recent)

print(f"\nLAST 10 SETTLED BETS")
print(f"  Record: {recent_wins}-{recent_losses}")
print(f"  Profit: ${recent_profit:+,.2f}")

print("\n" + "="*80)
