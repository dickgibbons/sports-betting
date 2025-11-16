# NBA Betting System Setup

## Overview

Your NBA betting system structure (mirroring the NHL system):

```
/Users/dickgibbons/nba/daily nba/
├── nba_odds_api.py                 ✅ CREATED
├── nba_stats_api.py                ⏳ TO CREATE
├── nba_enhanced_data.py            ⏳ TO CREATE
├── nba_enhanced_trainer.py         ⏳ TO CREATE
├── daily_nba_report.py             ⏳ TO CREATE
├── automated_daily_system.sh       ⏳ TO CREATE
├── models/                          ✅ CREATED
└── logs/                            ✅ CREATED
```

## ✅ What's Already Created

1. **Directory Structure** - `/Users/dickgibbons/nba/daily nba/`
2. **NBA Odds API** - `nba_odds_api.py` (fetches odds from The-Odds-API)

## 🎯 Quick Start (Copy from NHL)

The fastest way to get NBA running is to **adapt your NHL files**:

### Step 1: Copy NHL Files

```bash
cd "/Users/dickgibbons/nba/daily nba"

# Copy NHL files as templates
cp "/Users/dickgibbons/hockey/daily hockey/nhl_enhanced_data.py" ./nba_enhanced_data.py
cp "/Users/dickgibbons/hockey/daily hockey/nhl_enhanced_trainer.py" ./nba_enhanced_trainer.py
cp "/Users/dickgibbons/hockey/daily hockey/daily_nhl_report.py" ./daily_nba_report.py
```

### Step 2: Find/Replace in All Files

Replace these strings in all copied files:

| Find | Replace |
|------|---------|
| `NHL` | `NBA` |
| `nhl` | `nba` |
| `hockey` | `basketball` |
| `Hockey` | `Basketball` |
| `icehockey_nhl` | `basketball_nba` |

### Step 3: Update API Endpoints

**NHL uses:**
- NHL API: `https://api-web.nhle.com/v1/`
- MoneyPuck: Team analytics

**NBA should use:**
- NBA API: `https://api.balldontlie.io/v1/` (free)
- Or: `https://www.balldontlie.io/api/v1/` (stats)
- Odds API: Already set up in `nba_odds_api.py`

### Step 4: Feature Differences

**NHL features:**
- Goals For/Against
- xGoals, Corsi, Fenwick
- Goalie saves
- Shots on goal

**NBA equivalent features:**
- Points For/Against
- Field Goal %
- 3-Point %
- Rebounds, Assists, Turnovers
- Pace, Offensive/Defensive Rating

## 📊 NBA-Specific Markets

### Primary Markets (similar to NHL)

1. **Moneyline** (Winner)
   - Like NHL match outcome

2. **Spread** (Point Spread)
   - Like NHL puckline
   - Typical: -5.5 / +5.5 points

3. **Totals** (Over/Under Points)
   - Like NHL over/under goals
   - Typical: O/U 220.5 points

### NBA-Specific Markets

4. **Player Props**
   - Points Over/Under (e.g., LeBron Over 25.5 points)
   - Rebounds Over/Under
   - Assists Over/Under
   - Similar to NHL player shots/saves

5. **Team Totals**
   - Team Points Over/Under
   - Quarter/Half totals

6. **First to Score X Points**
   - First to 20, first to 10, etc.

## 🔧 Model Features (NBA)

Based on NHL system, here are NBA equivalents:

### Team Statistics

| NHL Feature | NBA Equivalent |
|-------------|----------------|
| Goals For | Points For |
| Goals Against | Points Against |
| xGoals % | Offensive Rating |
| Corsi % | Possession % |
| Shots On Goal | Field Goal Attempts |
| Save % | Defensive Rating |
| Power Play % | Fast Break % |
| Penalty Kill % | Paint Defense % |

### Advanced NBA Metrics

Add these NBA-specific features:
- **Pace** - Possessions per 48 min
- **Effective FG%** - Adjusted for 3-pointers
- **True Shooting %** - Overall shooting efficiency
- **Turnover Rate**
- **Offensive Rebound %**
- **Free Throw Rate**

## 🚀 Quick Test

Test if NBA odds are working:

```bash
cd "/Users/dickgibbons/nba/daily nba"
python3 nba_odds_api.py
```

Should show:
```
🏀 Testing NBA Odds API

✅ Found X upcoming NBA games

Lakers @ Warriors
  Moneyline: 2.10 / 1.80
  Spread: +3.5 @ 1.91 / -3.5 @ 1.91
  Total: O/U 225.5 (1.91/1.91)
```

## 📅 NBA Season Schedule

**2024-25 Season:**
- **Preseason:** October 4-18, 2024
- **Regular Season:** October 22, 2024 - April 13, 2025
- **Playoffs:** April 2025
- **Finals:** June 2025

**Games per day:**
- Typical: 5-15 games per night
- More games than NHL (30 teams × 82 games = 2,460 total)

## 💡 NBA vs NHL Differences

| Aspect | NHL | NBA |
|--------|-----|-----|
| Games/season | 82 | 82 |
| Teams | 32 | 30 |
| Scoring | Low (6-7 total goals) | High (210-230 total points) |
| Key stat | Save % | FG % |
| Variance | Higher | Lower |
| B2B Impact | Significant | Very significant |
| Home advantage | ~55% | ~58-60% |

## 🎯 Recommended Markets for NBA

Based on NHL experience:

1. ✅ **Spreads** (Most reliable, like NHL)
   - Lower variance than moneyline
   - Better odds than totals

2. ✅ **Team Totals** (Good for strong/weak teams)
   - Lakers Team Total Over
   - Pistons Team Total Under

3. ✅ **Player Props** (High volume, good data)
   - Points, Rebounds, Assists
   - Similar to NHL player shots/saves

4. ⚠️ **Totals** (Moderate)
   - More predictable than NHL
   - Pace matters a lot

5. ❌ **Moneyline** (Avoid heavy favorites)
   - Like NHL, favorites often overpriced

## 📈 Back-to-Back Analysis for NBA

NBA back-to-backs are even more important than NHL:

**Key findings from NBA research:**
- **ROAD → ROAD** (2nd night): Win rate drops ~8-10%
- **Home after road**: Better rest, win rate +3-5%
- **Fatigue factor**: Bigger impact than NHL (more running)

**Recommended:**
- **Bet AGAINST teams on 2nd night of road B2B**
- **Bet ON home teams facing B2B opponents**
- **Avoid betting ON B2B teams** (unless big underdogs)

## 📁 Next Steps

1. **Copy and adapt NHL files** (30 minutes)
2. **Test NBA odds API** (5 minutes)
3. **Find NBA stats API** (research balldontlie.io or NBA official API)
4. **Train initial models** (1 hour)
5. **Run first predictions** (5 minutes)
6. **Backtest** (optional, several hours)

## 🔗 Useful APIs

### Free NBA APIs

1. **balldontlie.io** - Free NBA stats API
   - `https://www.balldontlie.io/home.html`
   - Team stats, player stats, game scores
   - No API key required (for basic use)

2. **NBA Official API** - Stats.nba.com endpoints
   - More comprehensive
   - Unofficial but widely used
   - No API key

3. **The-Odds-API** - Already integrated
   - Your existing key works for NBA too
   - `basketball_nba` sport

### Paid Options (if needed)

- **SportsData.io** - $10/month
- **API-Sports** - NBA package available
- **RapidAPI** - Various NBA data providers

## 🎬 Sample Workflow

```bash
# 1. Get today's games
python3 nba_odds_api.py

# 2. Fetch team stats (once you create the file)
python3 nba_stats_api.py

# 3. Train models (once you create the file)
python3 nba_enhanced_trainer.py

# 4. Generate predictions (once you create the file)
python3 daily_nba_report.py

# 5. Review predictions
cat nba_daily_report_$(date +%Y-%m-%d).csv
```

## 🤖 Automation (Future)

Once system is working, add to cron (like NHL):

```bash
# Run at 4 PM daily (before NBA games start at 7 PM)
0 16 * * * cd /Users/dickgibbons/nba/daily\ nba && ./automated_daily_system.sh
```

## 📞 Support

For questions, reference your NHL system:
- `/Users/dickgibbons/hockey/daily hockey/`
- All the same principles apply!

---

**Created:** October 25, 2024
**Status:** Directory created, odds API ready
**Next:** Copy NHL files and adapt for NBA
