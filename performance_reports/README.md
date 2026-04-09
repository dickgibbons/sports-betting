# Performance Reports by Sport

This directory contains cumulative performance tracking for every bet across all sports.

## 📊 CSV Files

Each CSV tracks every bet made with the following columns:

| Column | Description |
|--------|-------------|
| **Date** | Date of the game |
| **Game** | Teams playing |
| **Bet** | Recommended bet (e.g., "Lakers ML") |
| **Bet Type** | Type of bet (Moneyline, Totals, Spread, etc.) |
| **Odds** | Betting odds (e.g., -125, +180) |
| **Confidence** | Bet confidence (ELITE, HIGH, MEDIUM, LOW) |
| **Expected Edge** | Predicted edge percentage |
| **Result** | WIN, LOSS, PUSH, or PENDING |
| **$25 Profit/Loss** | Hypothetical profit/loss if betting $25 |
| **Running Total** | Cumulative profit/loss across all bets |
| **Type Running Total** | Cumulative profit/loss for this bet type |
| **Angles** | Betting angles that triggered the recommendation |

---

## 📁 Available Reports

### 🏒 NHL - `nhl_cumulative_performance.csv`
- **Record:** 18-15-0 (54.5% win rate)
- **Running Total:** -$375.00 (@ $25/bet)
- **ROI:** -45.5%
- **Total Bets:** 42 (9 pending)

### 🏀 NBA - `nba_cumulative_performance.csv`
- **Record:** 15-30-0 (33.3% win rate)
- **Running Total:** -$253.01 (@ $25/bet)
- **ROI:** -22.5%
- **Total Bets:** 51 (6 pending)

**Breakdown by Bet Type:**
- ML: 0-5 (0.0%) | -$125.00
- Moneyline: 15-25 (37.5%) | -$128.01

### 🏀 NCAA - `ncaa_cumulative_performance.csv`
- **Total Bets:** 6 (all pending)

### ⚽ Soccer - `soccer_cumulative_performance.csv`
- **Total Bets:** 19 (all pending)

---

## 🚀 Quick Access Commands

### View Performance Dashboard
```bash
cd /Users/dickgibbons/AI Projects/sports-betting
python3 view_performance_by_sport.py
```

### Regenerate All Performance Reports
```bash
cd /Users/dickgibbons/AI Projects/sports-betting
python3 generate_performance_trackers.py
```

---

## 📈 How to Use These Reports

### In Excel/Google Sheets:
1. Open any CSV file
2. **Filter by Bet Type** to see Moneyline vs Totals vs Spread performance
3. **Sort by Date** to see chronological progression
4. **Filter by Confidence** to see which confidence levels perform best
5. **Look at Running Total** to track cumulative profit/loss

### Key Insights You Can Find:

**Profitability Analysis:**
- Which sports are profitable?
- Which bet types (ML, Totals, Spread) make money?
- Which confidence levels (ELITE, HIGH, MEDIUM, LOW) perform best?

**Pattern Recognition:**
- Which betting angles work most consistently?
- Are back-to-back situations profitable?
- Do road trip fatigue angles pay off?
- Is 3-in-4 nights a reliable indicator?

**Bet Sizing Optimization:**
- Should you bet more on certain confidence levels?
- Should you skip LOW confidence bets entirely?
- Which bet types deserve bigger stakes?

---

## 💡 Example Analysis Queries

### "Which bet types are profitable in NBA?"
Open `nba_cumulative_performance.csv`, look at "Type Running Total" column:
- Moneyline: -$128.01 ❌
- ML: -$125.00 ❌

### "What's my win rate on ELITE confidence bets?"
Filter by "Confidence" = ELITE across all sports CSVs

### "Which betting angles have the best record?"
Look at the "Angles" column for winning bets

### "Should I bet on heavy favorites?"
Filter by "Odds" < -200 and check win rate

---

## 🔄 Automatic Updates

These reports are automatically regenerated when you:
1. Run daily reports: `./run_all_daily.sh`
2. Update bet results manually via `python3 core/bet_tracker.py`
3. Auto-update results via `python3 core/auto_update_results.py`

To manually regenerate:
```bash
python3 generate_performance_trackers.py
```

---

## 📊 Current Performance Summary

**Overall (All Sports):**
- Total Settled Bets: 78
- Win Rate: 42.3%
- Total P/L (@ $25/bet): -$628.01

**Best Performing:**
- 🏒 **NHL** - 54.5% win rate (profitable sport)

**Needs Improvement:**
- 🏀 **NBA** - 33.3% win rate (losing money)
- Need better EV filtering and bet selection

---

## 🎯 Action Items Based on Data

1. **Focus on NHL** - Only consistently profitable sport
2. **Improve NBA selection** - Too many losses, review angle effectiveness
3. **Track NCAA/Soccer** - Need more data before drawing conclusions
4. **Review ELITE bets** - Underperforming despite high confidence
5. **Consider reducing bet sizes** on experimental angles

---

**Last Generated:** November 18, 2025
