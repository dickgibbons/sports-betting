# NHL Betting System - Performance Analysis & Recommendations
**Date**: October 19, 2025
**Status**: Analysis and improvement strategy

---

## 📊 Current System Overview

### What We're Betting
Based on today's report (Oct 19, 2025), our NHL system generates:
- **Moneyline bets** (team to win)
- **Team Totals Over 2.5** (individual team scores 3+ goals)
- **Team Totals Under 2.5** (individual team scores 2 or fewer goals)
- **Team Totals Over 3.5** (individual team scores 4+ goals)
- **Team Totals Under 3.5** (individual team scores 3 or fewer goals)

**Example from Oct 19:**
- 23 total recommended bets
- Mix of moneylines (6 bets) and team totals (17 bets)
- Confidence range: 63-87%
- Edge range: +10% to +35%

---

## 🚨 Key Problem: Lack of Historical Tracking

### Current Gaps
1. **No bet type performance tracking** - We don't know which bet types are profitable
2. **No cumulative results** - Unlike soccer (which tracks by Home Win, BTTS Yes, etc.), NHL has no historical performance data
3. **No backtest validation** - Last backtest showed 0 bets placed (thresholds too high)

### Soccer System Success Example
The FootyStats soccer backtest (Aug 1 - Oct 17, 2024) showed:

**Performance by Market:**
- **BTTS Yes**: 32 bets | 72.0% win rate | **+$196.95 profit** ✅
- **Premier League**: 18 bets | 61.0% win rate | +$7.49 profit ✅
- **Ligue 1**: 7 bets | 71.0% win rate | +$39.19 profit ✅

**Losing Markets:**
- **Home Win**: 48 bets | 42.0% win rate | -$421.61 loss ❌
- **BTTS No**: 66 bets | 50.0% win rate | -$379.38 loss ❌
- **Bundesliga**: 9 bets | 22.0% win rate | -$224.44 loss ❌

**Insight**: If they had **only bet BTTS Yes**, they would have made +$196 instead of losing -$674!

---

## ✅ Recommended Solution: Implement Performance Tracking System

### 1. Create NHL Backtest with Actual Historical Data

**What to build:**
```python
nhl_backtest_with_tracking.py
```

**Features:**
- Fetch NHL historical game results (2024-2025 season)
- Generate predictions using enhanced models for each game
- Track actual outcomes vs predictions
- **Break down performance by bet type:**
  - Moneyline (Home/Away)
  - Team Totals Over 2.5
  - Team Totals Under 2.5
  - Team Totals Over 3.5
  - Team Totals Under 3.5
  - Game Totals Over 5.5, 6.5 (if we add these)

**Output Reports:**
- Daily summary CSV (date, bets, wins, losses, profit, ROI, bankroll)
- Detailed bet CSV (every single bet with result and profit)
- **Performance by bet type** (win rate, ROI, total profit per market)
- **Performance by team** (which teams we're most accurate on)
- Bankroll growth charts

---

### 2. Add Game Totals Markets

**Current Gap**: We only bet team totals, not game totals

**Recommendation**: Add these bet types:
- **Game Total Over 5.5** (both teams combine for 6+ goals)
- **Game Total Under 5.5** (both teams combine for 5 or fewer goals)
- **Game Total Over 6.5** (both teams combine for 7+ goals)
- **Game Total Under 6.5** (both teams combine for 6 or fewer goals)

**Why?**
- NHL averages ~6 goals per game
- Game totals are popular, liquid markets
- Diversifies bet types (currently 74% of bets are team totals)
- May perform better than team-specific predictions

**Implementation:**
```python
# In bet_recommendations_enhanced.py, add:
game_total = home_score_pred + away_score_pred

if game_total > 6.5 and model_confidence > 0.78:
    bets.append({
        'type': 'Game Total Over 6.5',
        'pick': 'Over 6.5',
        'confidence': model_confidence,
        'edge': calculate_edge(odds, model_confidence)
    })
```

---

### 3. Add First Period (P1) Totals Markets ⭐ NEW

**High-Value Opportunity**: First period betting is fast, exciting, and less predictable for casual bettors

**Recommendation**: Add these P1 bet types:
- **P1 Game Total Over 1.5** (2+ goals scored in first period by both teams)
- **P1 Game Total Under 1.5** (0-1 goals scored in first period)
- **P1 Team Total Over 0.5** (specific team scores in first period)
- **P1 Team Total Over 1.5** (specific team scores 2+ in first period)

**Why P1 Totals?**
- **Fast results** - settled in 20 minutes (vs 2.5 hours for full game)
- **High variance** - books often misprice P1 totals
- **Fresh data** - no goalie pulled, no empty nets, no desperation plays
- **Team tendencies** - some teams consistently start fast/slow
- **Less correlation** with full game (can hedge strategies)

**NHL P1 Averages** (2023-24 season):
- Average P1 goals per game: **1.8 goals**
- P1 Over 1.5 hits: ~52% of games
- Teams that score in P1 win: 62% of the time

**Implementation Strategy:**
```python
# Feature engineering for P1 predictions:
features = {
    'home_p1_goals_per_game': 0.95,  # Historical P1 scoring rate
    'away_p1_goals_per_game': 0.85,
    'home_p1_goals_allowed': 0.75,
    'away_p1_goals_allowed': 0.90,
    'home_corsi_for_p1': 52.3,       # Shot attempts in P1
    'away_corsi_for_p1': 49.8,
    'home_starting_goalie_p1_sv_pct': 0.915,  # Goalie P1 save %
    'away_starting_goalie_p1_sv_pct': 0.902,
}

# Predict P1 goals
p1_game_total_pred = predict_p1_game_total(features)

if p1_game_total_pred > 1.7 and confidence > 0.80:
    bets.append({
        'type': 'P1 Game Total Over 1.5',
        'pick': 'Over 1.5',
        'confidence': confidence,
        'expected_goals': p1_game_total_pred
    })
```

**Data Requirements:**
- **MoneyPuck** - P1 Corsi%, P1 xG%, P1 scoring rates (FREE)
- **NHL API** - P1 historical scores by team (FREE)
- **Hockey-Reference** - P1 goalie stats (FREE)

---

### 4. Integrate Goalie Information ⭐ CRITICAL

**Current State**: You already have goalie models (`nhl_goalie_models.pkl`, `nhl_goalie_trainer.py`)

**Problem**: Goalie information may not be fully integrated into game predictions

**Why Goalies Matter**:
- **Elite goalies** can shift game totals by 0.5-1.0 goals
- **Backup goalies** often have 10-15% worse save percentage
- **Goalie matchups** are critical for totals betting
- **Fresh goalies** vs tired goalies (games in last 3 days)

**Key Goalie Metrics to Track:**
1. **Save Percentage (Sv%)** - Current season vs career
2. **Goals Saved Above Expected (GSAx)** - Advanced stat showing goalie quality
3. **Home vs Road splits** - Some goalies much better at home
4. **Rest days** - Goalies on 0-1 days rest perform worse
5. **Recent form** - Last 5 games Sv% vs season average
6. **P1 Performance** - Some goalies start slow/strong

**Integration Strategy:**
```python
# In nhl_enhanced_data.py or bet_recommendations_enhanced.py:

def get_starting_goalies(game_date):
    """Fetch confirmed starting goalies for today's games"""
    # Sources: Daily Faceoff, LeftWingLock, NHL.com
    return {
        'COL vs BOS': {
            'home_goalie': 'Alexandar Georgiev',
            'away_goalie': 'Linus Ullmark'
        },
        ...
    }

def adjust_prediction_for_goalie(base_prediction, goalie_stats):
    """Adjust goal predictions based on goalie quality"""

    # Elite goalie (GSAx > +10): reduce goals by 0.3
    if goalie_stats['gsax'] > 10:
        adjustment = -0.3
    # Backup goalie (Sv% < .900): increase goals by 0.4
    elif goalie_stats['sv_pct'] < 0.900:
        adjustment = +0.4
    # Average goalie
    else:
        adjustment = 0.0

    # Add rest penalty
    if goalie_stats['rest_days'] == 0:  # Back-to-back
        adjustment += 0.2  # More goals expected

    return base_prediction + adjustment

# Example usage:
home_goals_base = 3.2
away_goals_base = 2.8

# Get starting goalies
goalies = get_starting_goalies(game_date)
home_goalie_stats = get_goalie_stats(goalies['home_goalie'])
away_goalie_stats = get_goalie_stats(goalies['away_goalie'])

# Adjust for goalie quality
home_goals_adjusted = adjust_prediction_for_goalie(home_goals_base, away_goalie_stats)  # Home scores against away goalie
away_goals_adjusted = adjust_prediction_for_goalie(away_goals_base, home_goalie_stats)

# Final predictions account for goalie quality
game_total = home_goals_adjusted + away_goals_adjusted  # e.g., 5.7 goals
```

**Goalie Data Sources:**
1. **Daily Faceoff** (https://www.dailyfaceoff.com/starting-goalies/) - Confirmed starters
2. **LeftWingLock** (https://leftwinglock.com/starting-goalies/) - Real-time goalie confirmations
3. **MoneyPuck** - GSAx, Sv%, quality metrics
4. **NHL API** - Game logs, recent performance

**Implementation Priority:**
1. ✅ **Phase 1**: Fetch confirmed starting goalies daily (automate)
2. ✅ **Phase 2**: Load goalie stats from existing `nhl_goalie_models.pkl`
3. ✅ **Phase 3**: Adjust game/team total predictions based on goalie quality
4. ✅ **Phase 4**: Add goalie-specific confidence boosts/penalties
5. ✅ **Phase 5**: Track goalie prediction accuracy separately

---

### 3. Implement Daily Cumulative Tracking

**Goal**: Track actual bet results over time (like soccer and euro hockey)

**New File**:
```python
nhl_bet_tracker.py
```

**Features:**
- Scrape or manually input actual game results
- Compare against recommended bets from that day's CSV
- Calculate which bets won/lost
- Update cumulative performance file

**Cumulative CSV Structure:**
```csv
date,total_bets,wins,losses,win_rate,roi,bankroll,moneyline_win_rate,team_totals_win_rate,game_totals_win_rate
2025-10-19,23,15,8,65.2%,+12.3%,$1123,58.3%,68.0%,N/A
2025-10-20,18,12,6,66.7%,+14.1%,$1281,62.5%,64.3%,75.0%
...
```

---

## 🎯 Specific Action Plan

### Phase 1: Integrate Goalie Data & Add P1 Totals (Week 1)
**Priority**: HIGH - Immediate impact on prediction accuracy

1. **Goalie Integration**:
   - Create `nhl_goalie_fetcher.py` - scrapes Daily Faceoff for confirmed starters
   - Update `bet_recommendations_enhanced.py` to load goalie stats
   - Adjust goal predictions based on goalie quality (GSAx, Sv%, rest days)
   - Add goalie names to output reports

2. **First Period Totals**:
   - Collect P1 historical data (MoneyPuck, NHL API)
   - Train P1-specific models (game total, team totals)
   - Add P1 predictions to daily reports
   - Test P1 O/U 1.5 on historical data (52% expected hit rate)

3. **AWS Training Setup**:
   - Upload P1 historical data to AWS S3
   - Create `aws_train_p1_models.sh` training script
   - Train P1 models on AWS EC2 (faster, more data)
   - Download trained P1 models to local

**Deliverables**:
- ✅ Goalie-adjusted predictions in daily reports
- ✅ P1 totals (O/U 1.5) in bet recommendations
- ✅ P1 models trained on AWS with 2+ years of data

---

### Phase 2: Add Game Totals & Backtest System (Week 2)
**Priority**: HIGH - Fill major gap in bet types

1. **Game Totals Implementation**:
   - Add full-game O/U 5.5 and 6.5 predictions
   - Combine home/away predictions for game totals
   - Adjust for goalie matchup (elite vs backup)
   - Add game totals to daily CSV reports

2. **Build Backtest Framework**:
   - Create `nhl_historical_backtest.py`
   - Fetch historical NHL scores (NHL API, MoneyPuck)
   - Fetch historical odds (API-Sports or OddsJam)
   - Run predictions on past games (Oct 1-19, 2025)

3. **Performance Tracking by Bet Type**:
   - Track moneyline win rate + ROI
   - Track team totals win rate + ROI (by O/U threshold)
   - Track game totals win rate + ROI
   - Track P1 totals win rate + ROI

4. **AWS Retraining**:
   - If backtest shows <48% win rate on any market, retrain on AWS
   - Add goalie features to models if not already included
   - Add P1 features if building from scratch
   - Test different hyperparameters (tree depth, estimators)

**Deliverables**:
- ✅ Game totals O/U 5.5, 6.5 in daily reports
- ✅ Backtest results showing performance by bet type
- ✅ CSV: `nhl_backtest_by_bet_type_20251019.csv`

---

### Phase 3: Implement Live Tracking (Week 3)
**Priority**: MEDIUM - Validates real-world performance

1. **Daily Bet Tracker**:
   - Create `nhl_bet_tracker.py`
   - Scrape NHL.com or NHL API for final scores
   - Match actual results against bet recommendations
   - Calculate daily win/loss and bankroll

2. **Cumulative Performance File**:
   - Create `nhl_cumulative_performance.csv`
   - Append daily results (wins, losses, ROI by bet type)
   - Track goalie prediction accuracy
   - Track P1 prediction accuracy

3. **Automated Reporting**:
   - Generate weekly summary emails/alerts
   - Flag underperforming bet types (<45% win rate)
   - Highlight top-performing markets (>58% win rate)

**Deliverables**:
- ✅ Daily automated result tracking
- ✅ Cumulative performance CSV updated nightly
- ✅ Weekly summary reports

---

### Phase 4: Optimize & Filter by Performance (Week 4)
**Priority**: HIGH - Maximize profitability

1. **Review Performance Data** (after 3-4 weeks of tracking):
   - Calculate win rate by bet type (moneyline, totals, P1)
   - Calculate ROI by bet type
   - Identify losing markets (<48% win rate or negative ROI)
   - Identify high-performing markets (>55% win rate, >10% ROI)

2. **Filter Bet Selection**:
   - **Eliminate unprofitable bet types** (e.g., if moneylines show 42% win rate)
   - **Increase confidence thresholds** for marginal markets
   - **Decrease confidence thresholds** for proven winners
   - **Adjust Kelly fractions** (increase for high-ROI markets)

3. **AWS Retraining with Filters**:
   - If game totals underperform: retrain with goalie + P1 features
   - If P1 totals underperform: add team pace/Corsi features
   - If team totals underperform: add home/road splits
   - Upload new training data to AWS, retrain all models

4. **A/B Testing**:
   - Run parallel systems (filtered vs unfiltered)
   - Compare bankroll growth over 2 weeks
   - Commit to better-performing system

**Deliverables**:
- ✅ Filtered bet recommendations (only profitable markets)
- ✅ Retrained models on AWS with enhanced features
- ✅ Documented performance improvements (+10-30% ROI expected)

---

## 📈 Expected Outcomes

### Scenario 1: All Bet Types Profitable
- Continue current strategy
- Optimize confidence thresholds per market
- Consider adding more games (lower confidence threshold for best-performing markets)

### Scenario 2: Some Bet Types Unprofitable (Most Likely)
Example findings after tracking:
- **Moneylines**: 52% win rate, +8% ROI ✅
- **Team O/U 2.5**: 48% win rate, -5% ROI ❌
- **Team O/U 3.5**: 65% win rate, +22% ROI ✅✅
- **Game Totals**: 58% win rate, +12% ROI ✅

**Action**: Stop betting Team O/U 2.5, focus on Team O/U 3.5 and Game Totals

### Scenario 3: Major Overhaul Needed
If most bet types show <48% win rate:
- Review model features (may be missing key stats)
- Increase confidence thresholds (currently 62% min)
- Consider Back-to-Back (B2B) filters more heavily
- Analyze home/road splits more carefully

---

## 🔧 Technical Implementation Notes

### Data Sources Needed
1. **NHL API** (free) - game results, scores
2. **MoneyPuck** (already using) - advanced stats
3. **Odds data** - for actual betting lines (may need API-Sports or similar)

### Files to Create
```
/Users/dickgibbons/hockey/daily hockey/
├── nhl_historical_backtest.py          # NEW: Backtest with results tracking
├── nhl_bet_tracker.py                  # NEW: Daily results tracker
├── nhl_cumulative_performance.csv      # NEW: Historical performance log
└── reports/
    └── backtest_by_bet_type_YYYYMMDD.csv  # NEW: Performance breakdown
```

### Integration with Existing System
- **Keep**: Enhanced models, feature engineering, confidence scoring
- **Add**: Game totals predictions, bet type tracking
- **Modify**: Bet selection logic (filter by historical bet type performance)

---

## 🎓 Key Lessons from Soccer System

### What Worked in Soccer
1. **Tracking by market type** revealed BTTS Yes was highly profitable
2. **Tracking by league** showed Ligue 1 outperformed Bundesliga
3. **Selective betting** - could have avoided -$674 loss by filtering bad markets

### Apply to NHL
1. Track by **bet type** (moneyline, team totals, game totals)
2. Track by **team** (some teams may be more predictable)
3. Track by **situation** (home/away, B2B games, division rivals)
4. **Filter aggressively** - only bet markets with proven ROI

---

## 💡 Quick Win Recommendations (This Week)

### Immediate Actions
1. ✅ **Run today's picks** (Oct 19) and manually track results tomorrow
2. ✅ **Start Google Sheet** tracking:
   - Date | Game | Bet Type | Confidence | Result | Win/Loss | Profit
3. ✅ **Count bet types** from last 5 days of reports
4. ✅ **Set calendar reminder** to review performance every Friday

### Week 1 Goal
- **Collect 7 days of actual results** (Oct 19-26)
- **Calculate basic win rates** by bet type
- **Identify obvious winners/losers** before building full backtest

---

## 📊 Success Metrics

### After 2 Weeks
- [ ] Win rate by bet type calculated
- [ ] At least one bet type shows 55%+ win rate
- [ ] Positive ROI overall (+5% minimum)

### After 1 Month
- [ ] Backtest system fully automated
- [ ] Filtered out unprofitable bet types
- [ ] Bankroll showing steady growth
- [ ] Confidence intervals established per market

### After 2 Months
- [ ] 60%+ win rate on best-performing bet types
- [ ] +15%+ ROI on filtered bets
- [ ] Can confidently recommend 5-10 daily bets
- [ ] System rivals Euro hockey success (91%+ confidence picks)

---

## 🚀 Next Steps

1. **User Decision**: Which phase to start with?
   - **Option A**: Quick manual tracking (start today)
   - **Option B**: Build full backtest first (1 week development)
   - **Option C**: Add game totals first, then backtest

2. **Resource Assessment**:
   - Do we have historical NHL odds data?
   - Can we access NHL API for game results?
   - How much manual work is acceptable?

3. **Timeline**:
   - When do you want recommendations implemented?
   - Can we run parallel tracking while building backtest?

---

**Created**: October 19, 2025
**Status**: Ready for implementation
**Estimated Impact**: +20-30% ROI improvement by filtering unprofitable bet types
