# Sport-Specific Daily Picks System

Individual picks files for each sport to develop sport-specific strategies.

---

## 📋 Overview

Each sport now generates its own dedicated picks file daily at 5:00 AM with:
- Sport-specific betting opportunities
- Confidence ratings (ELITE, HIGH, MEDIUM, LOW)
- Expected edge percentages
- True EV calculations (when odds available)
- Betting angles that triggered each pick
- Recommended bet sizing

This allows you to:
- **Analyze each sport independently**
- **Develop sport-specific strategies**
- **Track what works for NHL vs NBA vs NCAA vs Soccer**
- **Make informed decisions per sport**

---

## 📁 Generated Files

### Daily Location: `/Users/dickgibbons/AI Projects/sports-betting/reports/YYYY-MM-DD/`

Each day at 5:00 AM, the following files are automatically generated:

```
reports/2025-11-18/
├── nhl_picks_2025-11-18.txt         # 🏒 NHL picks
├── nba_picks_2025-11-18.txt         # 🏀 NBA picks
├── ncaa_picks_2025-11-18.txt        # 🏀 NCAA picks
├── soccer_picks_2025-11-18.txt      # ⚽ Soccer picks
├── nhl_first_period_trends_*.txt    # NHL 1P analysis
├── nhl_first_period_trends_*.csv    # NHL 1P data
└── report_2025-11-18.txt            # Unified cross-sport
```

---

## 🏒 NHL Picks File Format

**Example: `nhl_picks_2025-11-18.txt`**

```
🏒 NHL BETTING PICKS - 2025-11-18
================================================================================

📊 SUMMARY
────────────────────────────────────────────────────────────────────────────────
Total Picks: 6
🔥 ELITE: 1 picks
✅ HIGH: 3 picks
💡 MEDIUM: 2 picks

🔥🔥🔥 #1 CBJ @ WPG
   BET: WPG ML
   Expected Edge: +30.0%
   Confidence: ELITE
   Angles (3):
     • CBJ on HOME → ROAD B2B (80% win rate historical)
     • CBJ playing 3rd game in 4 nights (heavy fatigue)
     • WPG has 2 days rest vs CBJ 0 days
   💰 Recommended: 2-3% of bankroll

✅✅ #2 SEA @ DET
   BET: SEA ML
   Expected Edge: +10.0%
   Confidence: HIGH
   Angles (1):
     • DET playing 3rd game in 4 nights (heavy fatigue)
   💰 Recommended: 1-2% of bankroll
```

---

## 🏀 NBA Picks File Format

**Example: `nba_picks_2025-11-18.txt`**

```
🏀 NBA BETTING PICKS - 2025-11-18
================================================================================

📊 SUMMARY
────────────────────────────────────────────────────────────────────────────────
Total Picks: 2
✅ HIGH: 1 picks
💡 MEDIUM: 1 picks

✅✅ #1 Detroit Pistons @ Atlanta Hawks
   BET: Atlanta Hawks ML
   ODDS: -104 | True EV: +21.6%
   Confidence: HIGH
   Angles (1):
     • Detroit Pistons on HOME → ROAD B2B (80% win rate historical)
   💰 Recommended: 1-2% of bankroll

💡 #2 Golden State Warriors @ Orlando Magic
   BET: Orlando Magic ML
   ODDS: +136 | True EV: +35.2%
   Confidence: MEDIUM
   Angles (1):
     • Golden State Warriors on 5th game of road trip
   💰 Recommended: 0.5-1% of bankroll
```

---

## 🎯 Confidence Levels Explained

| Level | Edge Required | Angle Count | Bet Sizing | When to Bet |
|-------|---------------|-------------|------------|-------------|
| **🔥 ELITE** | 15%+ edge AND 2+ angles | 2+ | 2-3% of bankroll | High confidence opportunities |
| **✅ HIGH** | 10%+ edge OR 2+ angles | 1-2 | 1-2% of bankroll | Strong opportunities |
| **💡 MEDIUM** | 7-10% edge | 1 | 0.5-1% of bankroll | Moderate opportunities |
| **⚪ LOW** | <7% edge | 1 | Optional/Skip | Weak opportunities |

---

## 🔄 Automation Schedule

**Runs daily at 5:00 AM automatically via cron:**

```bash
0 5 * * * cd /Users/dickgibbons/AI Projects/sports-betting && ./run_all_daily.sh
```

### What Happens at 5:00 AM:
1. ✅ Generate NHL picks → `nhl_picks_YYYY-MM-DD.txt`
2. ✅ Generate NBA picks → `nba_picks_YYYY-MM-DD.txt`
3. ✅ Generate NCAA picks → `ncaa_picks_YYYY-MM-DD.txt`
4. ✅ Generate Soccer picks → `soccer_picks_YYYY-MM-DD.txt`
5. ✅ Generate NHL first period trends
6. ✅ Generate unified cross-sport report
7. ✅ Update cumulative performance trackers

All files saved to: `/Users/dickgibbons/AI Projects/sports-betting/reports/YYYY-MM-DD/`

---

## 🚀 Manual Execution

### Generate All Sport Picks (Without Full Reports)
```bash
cd /Users/dickgibbons/AI Projects/sports-betting/core
python3 generate_sport_picks.py
```

### Generate Specific Sport Only
```bash
# NHL only
python3 generate_sport_picks.py --sport NHL

# NBA only
python3 generate_sport_picks.py --sport NBA

# NCAA only
python3 generate_sport_picks.py --sport NCAA

# Soccer only
python3 generate_sport_picks.py --sport SOCCER
```

### Generate for Specific Date
```bash
python3 generate_sport_picks.py --date 2025-11-17
```

### Run Complete Daily System (All Reports + Trackers)
```bash
cd /Users/dickgibbons/AI Projects/sports-betting
./run_all_daily.sh
```

---

## 📊 Using With Performance Trackers

### Step 1: Review Daily Sport-Specific Picks
```bash
# Morning - Check today's picks
cat /Users/dickgibbons/AI Projects/sports-betting/reports/2025-11-18/nhl_picks_2025-11-18.txt
cat /Users/dickgibbons/AI Projects/sports-betting/reports/2025-11-18/nba_picks_2025-11-18.txt
```

### Step 2: Place Bets Based on Confidence
- **ELITE picks**: 2-3% of bankroll
- **HIGH picks**: 1-2% of bankroll
- **MEDIUM picks**: 0.5-1% of bankroll (optional)
- **LOW picks**: Skip or very small amounts

### Step 3: Track Results
Results are automatically tracked in:
- `/Users/dickgibbons/AI Projects/sports-betting/data/bet_history.json`

### Step 4: Analyze Performance By Sport
```bash
# View cumulative performance by sport
python3 view_performance_by_sport.py

# Or open CSV files in Excel
open performance_reports/nhl_cumulative_performance.csv
open performance_reports/nba_cumulative_performance.csv
```

---

## 🎯 Sport-Specific Strategy Development

### NHL Strategy (54.5% Win Rate - Profitable)
**What's Working:**
- Back-to-back situations (especially HOME → ROAD)
- 3-in-4 nights fatigue
- Road trip fatigue (4th+ game)
- Rest advantages

**Focus Areas:**
- Continue betting on fatigue angles
- Prioritize ELITE and HIGH confidence picks
- Track goalie matchups separately

### NBA Strategy (33.3% Win Rate - Needs Work)
**What's NOT Working:**
- Too many losses despite good angles
- Need better EV filtering (now implemented)

**Action Items:**
- Focus only on ELITE picks until strategy improves
- Track home vs away performance separately
- Review which specific angles work best

### NCAA Strategy (Insufficient Data)
**Current Status:**
- Only 6 bets tracked (all pending)
- Need more data before developing strategy

**Next Steps:**
- Continue logging picks
- Build sample size (20+ bets minimum)
- Analyze elite venue home court advantage

### Soccer Strategy (Insufficient Data)
**Current Status:**
- 19 bets tracked (all pending)
- Need more data

**Next Steps:**
- Track BTTS vs Totals vs Moneyline separately
- Build league-specific insights
- Analyze home fortress patterns

---

## 📈 EV Filtering

All picks are filtered for Expected Value:
- **Max Favorite:** -250 (won't recommend worse than -250)
- **Min EV:** 5% (minimum 5% expected value required)

**Filtered Out Examples:**
- ❌ Gonzaga -10000 (need to bet $10,000 to win $100)
- ❌ Any pick with true EV < 5%
- ❌ Heavy chalk favorites without value

**Only Positive EV Bets Recommended**

---

## 🛠️ Cron Job Management

### View Current Cron Schedule
```bash
crontab -l
```

### Edit Cron Schedule
```bash
crontab -e
```

### Change Time (Example: 6:00 AM instead of 5:00 AM)
```bash
crontab -e
# Change: 0 5 * * * to 0 6 * * *
```

### Remove Automation
```bash
crontab -l | grep -v 'sports-betting' | crontab -
```

### Reinstall 5:00 AM Automation
```bash
cd /Users/dickgibbons/AI Projects/sports-betting
./setup_5am_cron.sh
```

---

## 📋 Daily Workflow

### Morning (After 5:00 AM)
1. Check email/notifications (if configured)
2. Review sport-specific picks files
3. Open cumulative performance trackers
4. Decide which sports/picks to bet based on recent performance

### During Day
1. Place bets on selected picks
2. Note any odds changes

### Evening (After Games)
1. Update bet results (auto-updates available for NHL/NBA)
2. Review performance trackers
3. Adjust strategy based on results

### Weekly
1. Review weekly performance by sport
2. Identify which angles are working
3. Adjust bet sizing/selection criteria
4. Review cumulative CSV trackers in Excel

---

## 📊 Example Daily Routine

```bash
# Morning - Check all picks
cd /Users/dickgibbons/AI Projects/sports-betting/reports/2025-11-18

# Read NHL picks
cat nhl_picks_2025-11-18.txt

# Read NBA picks
cat nba_picks_2025-11-18.txt

# Check current performance
cd /Users/dickgibbons/AI Projects/sports-betting
python3 view_performance_by_sport.py

# Decision: Based on NHL's 54.5% win rate, bet on ELITE NHL picks
# Skip NBA picks today since only 33.3% win rate

# Evening - Update results
cd core
python3 auto_update_results.py

# Weekly - Analyze in Excel
open ../performance_reports/nhl_cumulative_performance.csv
```

---

## 🎯 Key Benefits

### 1. **Sport-Specific Focus**
Each sport has unique characteristics:
- NHL: Fatigue matters more (shorter benches)
- NBA: More possessions, different variance
- NCAA: Home court advantage stronger
- Soccer: Draw possibility, different markets

### 2. **Independent Analysis**
Track what works for each sport separately without cross-contamination

### 3. **Better Bankroll Management**
Allocate more to profitable sports (NHL), less to struggling sports (NBA)

### 4. **Strategy Evolution**
Develop specialized strategies per sport based on data

### 5. **Clear Daily Workflow**
Simple, automated system that delivers picks every morning

---

## 📁 File Locations Summary

```
/Users/dickgibbons/AI Projects/sports-betting/
├── reports/
│   └── YYYY-MM-DD/
│       ├── nhl_picks_YYYY-MM-DD.txt         ← Daily NHL picks
│       ├── nba_picks_YYYY-MM-DD.txt         ← Daily NBA picks
│       ├── ncaa_picks_YYYY-MM-DD.txt        ← Daily NCAA picks
│       ├── soccer_picks_YYYY-MM-DD.txt      ← Daily Soccer picks
│       └── report_YYYY-MM-DD.txt            ← Unified report
│
├── performance_reports/
│   ├── nhl_cumulative_performance.csv       ← NHL bet history
│   ├── nba_cumulative_performance.csv       ← NBA bet history
│   ├── ncaa_cumulative_performance.csv      ← NCAA bet history
│   └── soccer_cumulative_performance.csv    ← Soccer bet history
│
├── core/
│   └── generate_sport_picks.py              ← Picks generator
│
├── run_all_daily.sh                         ← Daily automation
└── setup_5am_cron.sh                        ← Cron installer
```

---

**Last Updated:** November 18, 2025
**Automation Status:** ✅ Active (runs daily at 5:00 AM)
