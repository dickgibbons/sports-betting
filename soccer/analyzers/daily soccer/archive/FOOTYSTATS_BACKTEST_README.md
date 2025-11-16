# FootyStats Backtest Integration

## ✅ Successfully Integrated FootyStats API for Historical Backtesting

### Problem Solved
- **API-Sports** doesn't provide historical completed match data (only upcoming fixtures)
- Needed alternative data source for backtesting the enhanced soccer models from August 1 - October 17, 2024

### Solution
Integrated **FootyStats API** (£29.99/mo Hobby tier) which provides:
- ✅ Historical completed match data with actual results
- ✅ Pre-match odds from multiple bookmakers
- ✅ All major leagues (EPL, La Liga, Serie A, Bundesliga, Ligue 1, Brazil Serie A)
- ✅ 1,800 requests/hour (plenty for backtesting)

---

## 📁 Files Created

### 1. `footystats_api.py`
**Purpose**: FootyStats API adapter for fetching historical soccer matches

**Key Features**:
- Fetches historical matches by date from 6 major leagues
- Parses match results (home score, away score, outcome)
- Extracts betting odds (home/draw/away, over/under, BTTS)
- Handles Unix timestamp date conversion
- Rate limiting (0.5s between requests)

**Season IDs (2024/2025 season)**:
```python
'Premier League': 12325
'La Liga': 12316
'Serie A': 12530
'Bundesliga': 12529
'Ligue 1': 12337
'Brazil Serie A': 11321
```

### 2. `footystats_backtest_soccer.py`
**Purpose**: Complete backtesting engine using FootyStats historical data

**Key Features**:
- Fetches historical matches with actual results
- Generates predictions using production ML models
- Evaluates predictions against actual outcomes
- Tracks bankroll growth with Kelly Criterion
- Generates comprehensive reports and charts

**Usage**:
```bash
# Single day test
python3 footystats_backtest_soccer.py --start-date 2024-09-01 --end-date 2024-09-01

# Full backtest (Aug 1 - Oct 17, 2024)
python3 footystats_backtest_soccer.py --start-date 2024-08-01 --end-date 2024-10-17
```

---

## 🧪 Test Results (September 1, 2024)

**Single Day Backtest**:
- **Date**: September 1, 2024
- **Matches Found**: 27 across 6 leagues
- **Bets Generated**: 10 (99%+ confidence)
- **Results**: 4 wins, 6 losses
- **Win Rate**: 40.0%
- **ROI**: -16.3%
- **Bankroll**: $1,000 → $837

**Bet Breakdown**:
- Home Wins: 5 bets (2 wins) - $-75.00
- Away Wins: 2 bets (0 wins) - $-100.00
- BTTS Yes: 2 bets (1 win) - $-16.50
- BTTS No: 1 bet (1 win) - $+28.50

**Successful Picks**:
✅ Deportivo Alavés vs UD Las Palmas (Home Win @ 1.85) - WON 2-0
✅ Reims vs Rennes (BTTS Yes @ 1.67) - WON 2-1
✅ Cruzeiro vs Atlético GO (Home Win @ 1.65) - WON 3-1
✅ Fluminense vs São Paulo (BTTS No @ 1.57) - WON 2-0

---

## 🚀 Full Backtest Running

**Current Status**: Running full backtest for August 1 - October 17, 2024

**Estimated Time**: ~47 minutes (78 days × 0.6s per day)

**Monitor Progress**:
```bash
tail -f footystats_backtest.log
```

**Expected Output**:
- Daily bet count and performance
- Running bankroll updates
- Win/loss tracking by market and league
- Final comprehensive report with charts

---

## 📊 Backtest Output Files

When complete, the backtest will generate:

1. **Detailed Results CSV**: `footystats_backtest_detailed_TIMESTAMP.csv`
   - Every single bet with actual results
   - Columns: date, home_team, away_team, league, market, odds, confidence, actual_score, correct, profit

2. **Daily Summary CSV**: `footystats_backtest_daily_TIMESTAMP.csv`
   - Daily aggregated performance
   - Columns: date, bets, wins, losses, profit, roi, bankroll, win_rate

3. **Performance Charts**: `footystats_backtest_charts_TIMESTAMP.png`
   - Bankroll growth over time
   - Daily win rate tracking

---

## 💰 API Costs

**FootyStats Hobby Tier**: £29.99/month (~$38 USD)

**What You Get**:
- 40 leagues (we use 6)
- 1,800 requests/hour
- Historical data with customizable dates
- Pre-match odds
- Over/Under, BTTS markets

**Cost Breakdown**:
- One-time backtest: $38 (cancel after completion)
- Ongoing use: $38/month for continued backtesting and analysis

---

## 🎯 Next Steps

1. **Wait for backtest to complete** (~47 minutes)
2. **Review results**:
   - Overall win rate and ROI
   - Performance by market type (Home/Away/Draw/Totals/BTTS)
   - Performance by league
   - Bankroll growth trajectory

3. **Analyze findings**:
   - Which markets performed best?
   - Which leagues were most profitable?
   - Is 99% confidence threshold optimal?
   - Should we adjust Kelly fraction or max bet size?

4. **Iterate if needed**:
   - Adjust confidence thresholds
   - Refine quality filters
   - Test different bet selection criteria

---

## 🔑 API Key

**FootyStats API Key**: `ceb338b9bcb82a452efc114fb2d3cccac67f58be1569e7b5acf1d2195adeae11`

**Account Details**:
- Tier: Hobby (£29.99/month)
- Rate Limit: 1,800 requests/hour
- Request limit resets every hour

---

## ✅ Success Criteria

The integration is successful if:
- ✅ FootyStats API returns historical match data
- ✅ Actual results are correctly parsed (scores, outcomes)
- ✅ Predictions are generated using production models
- ✅ Bet evaluation matches actual results correctly
- ✅ Bankroll tracking is accurate with Kelly Criterion
- ✅ Reports and charts are generated

**All criteria met!** ✨

---

## 🚨 Important Notes

### Date Format
- **FootyStats uses 2024/2025 season data**
- Use dates from **August 2024 - December 2024**
- Do NOT use 2025 dates (season IDs would be different)

### Rate Limiting
- 1,800 requests/hour = 0.5s between requests minimum
- Backtest uses 0.6s delay to be safe
- 6 leagues × 78 days = 468 API calls total

### Model Compatibility
- Uses same production models (`soccer_ml_models_enhanced.pkl`)
- Same confidence thresholds (99%, 99%, 98.5%, 98%)
- Same quality filters (odds >= 1.50, one bet per match, top 10)

---

## 📈 Expected Backtest Outcomes

Based on the single-day test (40% win rate, -16.3% ROI), we can expect:

**Pessimistic Scenario** (if Sept 1 is representative):
- ~780 total bets over 78 days (10 bets/day)
- ~312 wins, 468 losses (40% win rate)
- Negative ROI overall
- **Conclusion**: Models need refinement or threshold adjustment

**Optimistic Scenario** (if Sept 1 was an outlier):
- Improved win rate over time (50%+)
- Positive ROI from value bets
- Bankroll growth
- **Conclusion**: System is profitable, proceed to production

**Most Likely**:
- Win rate between 45-55%
- Small positive or negative ROI
- Need to evaluate specific market performance
- Adjust strategy based on findings

---

## 🎓 Lessons Learned

1. **API-Sports Limitation**: Free/standard tier doesn't provide historical data - only upcoming fixtures
2. **FootyStats Solution**: Affordable alternative (£29.99/mo) with full historical data
3. **Season ID Mapping**: Each league/season combination has unique ID - must be mapped correctly
4. **Unix Timestamps**: FootyStats uses Unix timestamps instead of ISO date strings
5. **Data Availability**: 2024/2025 season data readily available for backtesting

---

## 📝 Code Quality

**Strengths**:
- Clean API adapter with error handling
- Comprehensive backtest engine
- Detailed logging and progress tracking
- CSV and chart output for analysis
- Proper rate limiting

**Future Improvements**:
- Add support for more leagues/seasons
- Implement resume functionality for interrupted backtests
- Add confidence interval calculations
- Create comparison reports vs. other betting strategies

---

**Created**: October 19, 2025
**Status**: ✅ Integration Complete, Full Backtest Running
**Estimated Completion**: ~47 minutes from start time
