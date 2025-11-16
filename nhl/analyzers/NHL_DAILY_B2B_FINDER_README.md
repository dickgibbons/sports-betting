# NHL Daily Back-to-Back Finder

## Overview

This tool automatically identifies **today's NHL games** where teams are playing back-to-back, with special focus on the **best betting opportunities**.

## Quick Start

```bash
cd "/Users/dickgibbons/hockey/daily hockey"

# Check today's games
python3 nhl_daily_b2b_finder.py

# Check a specific date
python3 nhl_daily_b2b_finder.py --date 2024-11-15
```

## What It Does

The tool analyzes today's NHL schedule and identifies:

1. **🔥 STRONG BETS** - ROAD → ROAD Pattern
   - Away team played on road yesterday, playing on road again tonight
   - **Bet ON the home team**
   - Expected win rate: **57.6%**
   - Edge: **+7.6%** (profitable at -110 odds!)

2. **✅ GOOD BETS** - HOME → ROAD Pattern
   - Away team played at home yesterday, traveling for tonight's game
   - **Bet ON the home team**
   - Expected win rate: **56.7%**
   - Edge: **+6.7%** (profitable at -110 odds!)

3. **📊 MONITOR** - Other B2B Situations
   - ROAD → HOME (home team coming back home)
   - HOME → HOME (home team playing consecutive home games)
   - These have modest edges - use as tiebreakers

## Today's Opportunities (October 25, 2024)

### ✅ GOOD BETS (2 games):

1. **Buffalo @ Toronto** (9:00 PM)
   - Buffalo: HOME → ROAD pattern
   - **BET: ON Toronto**
   - Expected win rate: 56.7%
   - Toronto also in ROAD → HOME pattern (bonus!)

2. **Columbus @ Pittsburgh** (11:00 PM)
   - Columbus: HOME → ROAD pattern
   - **BET: ON Pittsburgh**
   - Expected win rate: 56.7%

### 📊 MONITOR (1 game):

3. **Ottawa @ Washington** (11:00 PM)
   - Washington: ROAD → HOME pattern
   - Consider ON Washington (49.2% win rate)
   - Smaller edge, use with other factors

## Betting Strategy

### When to Bet

**Always Bet:**
- **ROAD → ROAD** situations (57.6% edge)
- **HOME → ROAD** situations (56.7% edge)
- Both are **profitable at standard -110 odds**

**Consider Betting:**
- **ROAD → HOME** when home team is undervalued (+110 or better)
- Combine with other factors (team strength, goalie matchups)

### Recommended Stakes

Based on Kelly Criterion with conservative sizing:

**ROAD → ROAD (57.6% win rate):**
- At -110 odds: **4-5% of bankroll**
- Very strong edge

**HOME → ROAD (56.7% win rate):**
- At -110 odds: **3-4% of bankroll**
- Strong edge

**Other patterns:**
- 1-2% of bankroll (if betting at all)
- Use as tiebreakers only

## Example Output

```
🔥 BEST BETTING OPPORTUNITIES - ROAD → ROAD Pattern
────────────────────────────────────────────────────
Historical win rate when betting ON home team: 57.6%
Expected edge: +7.6% (profitable at -110 odds)
────────────────────────────────────────────────────

1. Team A @ Team B
   Time: 07:00 PM
   ⚠️  Team A: ROAD → ROAD
      Yesterday: vs Team C
   💰 BET: ON Team B (Strong edge: 57.6% win rate)
   ✅ Profitable at standard -110 odds
```

## Daily Workflow

### Morning Routine (10 AM):

```bash
cd "/Users/dickgibbons/hockey/daily hockey"
python3 nhl_daily_b2b_finder.py
```

1. Check for ROAD → ROAD situations (STRONG BETS)
2. Check for HOME → ROAD situations (GOOD BETS)
3. Note game times and teams
4. Check odds and place bets accordingly

### Pre-Game (1-2 hours before):

1. Verify starting goalies (make sure it's not a backup)
2. Check injury reports
3. Confirm odds are still favorable
4. Place bets

## Integration with Other Systems

### Combine with:

1. **Team strength** - Check standings
2. **Goalie matchups** - Starter vs backup?
3. **Recent form** - Hot streak vs cold streak?
4. **Odds value** - Is home team underpriced?

### Example Combined Analysis:

```
Game: Columbus @ Pittsburgh
- Columbus: HOME → ROAD (bet ON Pittsburgh)
- Pittsburgh: 6-2-1 (strong team)
- Columbus: 3-5-1 (weak team)
- Pittsburgh starting their #1 goalie
- Odds: Pittsburgh -130 (acceptable for this edge)

Decision: ✅ BET ON Pittsburgh (4% of bankroll)
```

## Historical Performance

Based on 3-season analysis (768 back-to-backs):

| Pattern | Sample | Home Team Win% | Edge | Profitable at -110? |
|---------|--------|----------------|------|---------------------|
| **ROAD → ROAD** | 361 | **57.6%** | **+7.6%** | ✅ **YES** |
| **HOME → ROAD** | 164 | **56.7%** | **+6.7%** | ✅ **YES** |
| ROAD → HOME | 168 | 49.2% | -0.8% | ❌ No |
| HOME → HOME | 75 | 48.0% | -2.0% | ❌ No |

**Key Insight:** Only ROAD → ROAD and HOME → ROAD patterns are profitable at standard -110 odds.

## Expected ROI

At standard -110 odds ($110 to win $100):

**ROAD → ROAD Pattern:**
- Win: 57.6% × $100 = $57.60
- Loss: 42.4% × $110 = -$46.64
- **Expected profit: +$10.96 per bet (~10% ROI)**

**HOME → ROAD Pattern:**
- Win: 56.7% × $100 = $56.70
- Loss: 43.3% × $110 = -$47.63
- **Expected profit: +$9.07 per bet (~8% ROI)**

## Tracking Your Bets

Create a simple spreadsheet:

| Date | Game | Pattern | Bet | Odds | Stake | Result | Profit |
|------|------|---------|-----|------|-------|--------|--------|
| 10/25 | CBJ @ PIT | HOME → ROAD | PIT | -110 | $110 | W | +$100 |
| 10/25 | BUF @ TOR | HOME → ROAD | TOR | -110 | $110 | L | -$110 |

Track your actual results to verify the edge holds!

## Troubleshooting

### "No games scheduled for today"
- It's an off-day (NHL doesn't play every day)
- Check again during the season (Oct-Apr)

### "No back-to-back situations today"
- Good! All teams are well-rested
- Check back tomorrow

### API Errors
- NHL API may be temporarily down
- Try again in a few minutes
- The tool uses official NHL API (very reliable)

## Advanced Usage

### Check Multiple Days Ahead

```bash
# Tomorrow
python3 nhl_daily_b2b_finder.py --date $(date -v +1d +%Y-%m-%d)

# Specific date
python3 nhl_daily_b2b_finder.py --date 2024-11-15
```

### Weekly Planning

Run for the next 7 days to plan your week:

```bash
for i in {0..6}; do
    date=$(date -v +${i}d +%Y-%m-%d)
    echo "=== $date ==="
    python3 nhl_daily_b2b_finder.py --date $date
    echo ""
done
```

## Important Notes

1. **Starting goalies matter** - If backup plays, edge may be reduced
2. **Check injury reports** - Key players out affects everything
3. **Odds vary** - Shop around for best lines
4. **Don't over-bet** - Even 57% winners lose 43% of the time
5. **Track results** - Verify the edge in your actual betting

## Questions?

**Q: Can I bet on every ROAD → ROAD situation blindly?**
A: Technically yes (57.6% > 52.4% breakeven), but combining with other factors improves results.

**Q: What if the away team is much stronger?**
A: The edge still exists, but may be priced into the odds. Look for value where the home team is underpriced.

**Q: How often do these situations occur?**
A: About 1-3 ROAD → ROAD or HOME → ROAD situations per week during the season.

**Q: Does this work in playoffs?**
A: Unknown - playoffs have different scheduling. This analysis is regular season only.

## Files Created

- `nhl_daily_b2b_finder.py` - The finder tool
- `NHL_DAILY_B2B_FINDER_README.md` - This file
- `NHL_B2B_COMPREHENSIVE_ANALYSIS.md` - Full 3-season analysis

---

**Created:** October 24, 2024
**Last Updated:** October 24, 2024
**Season:** 2024-25 NHL Regular Season
