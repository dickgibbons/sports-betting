# NHL First Period Trend Reports

## Purpose

Visual trend analysis tool for NHL 1st period betting. Shows goals scored/allowed/total for each team over time, with home/away filtering.

## Status: FIXED ✅

**Date Fixed:** 2025-11-26

**What was fixed:**
1. Updated `nhl_ml_totals_predictor.py` to use correct NHL API endpoint (`landing` instead of `play-by-play`)
2. Changed JSON path from `plays` to `summary/scoring` structure
3. Fixed `generate_1p_trend_reports.py` to use same API structure
4. Added date range handling for system clock issues

**Files Updated:**
- `/Users/dickgibbons/NHL-Machine-Learning-Sports-Betting/nhl_ml_totals_predictor.py` (lines 110-143)
- `/Users/dickgibbons/AI Projects/sports-betting/generate_1p_trend_reports.py` (date handling + API structure)

**Verification:** Reports now show actual first period goals (e.g., CAR: 4 (H), CBJ: 3 (H), SEA: 4 (A))

## How the Reports Will Work (Once Data Fixed)

### Generated Files

After running `/Users/dickgibbons/AI Projects/sports-betting/generate_1p_trend_reports.py`:

1. **nhl_1p_goals_scored_trend.csv** - Goals each team scored in 1P
2. **nhl_1p_goals_allowed_trend.csv** - Goals each team allowed in 1P
3. **nhl_1p_total_goals_trend.csv** - Total goals in each team's 1P
4. **nhl_1p_trends_complete.xlsx** - All three as separate sheets

### Report Format

**Columns:** Date + all NHL teams (32 teams)
**Rows:** Each game date
**Values:**
- "2 (H)" = 2 goals, home game
- "1 (A)" = 1 goal, away game
- "NA" = No game that day

### Example Usage

**Scenario:** Tonight's game is EDM @ LAK

1. **Open Excel file:** `nhl_1p_trends_complete.xlsx`

2. **Analyze Oilers (EDM):**
   - Go to "Goals Scored" sheet
   - Find EDM column
   - Filter to show only away games: "(A)"
   - Look at last 5-10 away games
   - See pattern: 1(A), 2(A), 0(A), 1(A), 2(A)
   - **Trend:** EDM averaging 1.2 goals/1P on road

3. **Analyze Kings (LAK):**
   - Stay on "Goals Scored" sheet (to see what LAK scores at home)
   - Find LAK column
   - Filter to show only home games: "(H)"
   - Look at last 5-10 home games
   - See pattern: 2(H), 1(H), 3(H), 1(H), 2(H)
   - **Trend:** LAK averaging 1.8 goals/1P at home

4. **Check Goals Allowed:**
   - Go to "Goals Allowed" sheet
   - EDM away: How many goals do they allow on road?
   - LAK home: How many do they allow at home?

5. **Check Total Goals:**
   - Go to "Total Goals" sheet
   - EDM away games: Recent 1P totals
   - LAK home games: Recent 1P totals
   - **Look for patterns:** Are EDM road games high or low scoring?

6. **Make Prediction:**
   ```
   EDM road 1P: Scores 1.2, Allows 1.3 = 2.5 total avg
   LAK home 1P: Scores 1.8, Allows 0.9 = 2.7 total avg

   Combined projection: 2.6 total

   Bet: OVER 1.5 (if both teams trending high)
   or UNDER 1.5 (if both trending low)
   ```

### Excel Tips

1. **Enable Filtering:**
   - Data → Filter (adds dropdown arrows to headers)

2. **Freeze Top Row:**
   - View → Freeze Panes → Freeze Top Row
   - Keeps team names visible when scrolling

3. **Highlight Patterns:**
   - Select team column
   - Home → Conditional Formatting
   - Color scale: Red (low) → Green (high)

4. **Filter by Home/Away:**
   - Click dropdown on team column
   - Text Filters → Contains → "(H)" or "(A)"

5. **Create Charts:**
   - Select team column
   - Insert → Line Chart
   - Visual trend of goals over time

### Integration with Daily Workflow

Add to `/Users/dickgibbons/AI Projects/sports-betting/run_nhl_daily.sh`:

```bash
# Generate 1P trend reports
log "Generating First Period Trend Reports..."
python3 generate_1p_trend_reports.py 30  # Last 30 days
```

This will update the reports daily with new games.

## What It Solves

**Before:** Had to manually track each team's 1P performance

**After:**
- See all teams' 1P trends in one place
- Quickly identify hot/cold streaks
- Filter by home/away instantly
- Spot patterns before betting
- Make data-driven 1P predictions

## Next Steps

1. **Fix data source** - Update nhl_ml_totals_predictor.py to properly extract 1P goals
2. **Test with sample data** - Verify reports generate correctly
3. **Integrate into daily workflow** - Add to run_all_daily.sh
4. **Use for analysis** - Start making better 1P predictions!

## Expected Results (When Working)

```
✓ Fetched 290 games
✓ Found 32 teams

Creating Goals Scored report...
✓ Saved: nhl_1p_goals_scored_trend.csv

Creating Goals Allowed report...
✓ Saved: nhl_1p_goals_allowed_trend.csv

Creating Total Goals report...
✓ Saved: nhl_1p_total_goals_trend.csv

✓ Excel file: nhl_1p_trends_complete.xlsx

Report dimensions: 48 dates x 32 teams
```

---

**The concept is solid and will provide powerful visual trend analysis - we just need to fix the data extraction first!**
