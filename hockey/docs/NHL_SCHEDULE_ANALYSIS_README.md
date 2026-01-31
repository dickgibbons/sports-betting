# NHL Schedule Situation Analysis

## Overview

This tool analyzes NHL team performance in compressed schedule situations, specifically:
- **Back-to-back games** (games on consecutive nights)
- **Three games in four nights**

It provides detailed **home/road splits** to identify betting opportunities.

## Key Findings (2024-25 Season So Far)

### 🔥 **Major Betting Edge Discovered**

**Back-to-Back Games (Game 2 Performance):**

| Situation | Win Rate | Sample Size | Edge |
|-----------|----------|-------------|------|
| **Game 2 at HOME** | **75.0%** | 8 games | **STRONG** |
| Game 2 on ROAD | 38.5% | 26 games | FADE |
| **Overall Game 2** | 47.1% | 34 games | - |

### 💎 **Key Insight:**
**Teams playing at home in the 2nd game of a back-to-back have a +36.5 percentage point advantage!**

This is a **massive edge** compared to the typical 50-60% home win rate.

### 🎯 **Best Travel Patterns (Game 2 Win Rates)**

1. **ROAD → HOME**: 100.0% (4/4 games) ⭐⭐⭐
2. HOME → HOME: 50.0% (2/4 games)
3. ROAD → ROAD: 42.9% (6/14 games)
4. HOME → ROAD: 33.3% (4/12 games) ⚠️

### 📊 **Three Games in Four Nights**

- Average wins: 1.50 per 3-game stretch
- Most common: 1 win (46.4%)
- Best case: 3 wins (10.7%)
- Worst case: 0 wins (7.1%)

## Betting Strategy

### ✅ **Recommended Bets**

**1. ROAD → HOME Pattern (100% win rate)**
- When a team plays on the road, then returns home the next night
- **Bet ON the home team** (the one returning home)
- Sample: 4 games, 4 wins (small sample but perfect record)

**2. Game 2 at HOME (75% win rate)**
- Any back-to-back where Game 2 is at home
- **Bet ON the home team**
- Sample: 8 games, 6 wins

### ⚠️ **Bets to Avoid**

**1. HOME → ROAD Pattern (33.3% win rate)**
- When a team plays at home, then travels for the next night
- **Consider betting AGAINST** the road team
- Sample: 12 games, only 4 wins

**2. Game 2 on ROAD (38.5% win rate)**
- Any back-to-back where Game 2 is on the road
- **Avoid betting on road teams** in this spot
- Sample: 26 games, 10 wins

## Usage

### Run Analysis for Current Season

```bash
cd "/Users/dickgibbons/hockey/daily hockey"

# Current season (October 2024 - present)
python3 nhl_schedule_analyzer.py --start-date 2024-10-01 --end-date 2024-10-24

# Full season (once complete)
python3 nhl_schedule_analyzer.py --start-date 2024-10-01 --end-date 2025-04-30
```

### Run Analysis for Previous Season

```bash
# 2023-24 season
python3 nhl_schedule_analyzer.py --start-date 2023-10-01 --end-date 2024-04-30

# 2022-23 season
python3 nhl_schedule_analyzer.py --start-date 2022-10-01 --end-date 2023-04-30
```

### Output Files

The analyzer creates two CSV files:

1. **`nhl_back_to_back_analysis.csv`**
   - Every back-to-back situation found
   - Game 1 and Game 2 details
   - Home/road for each game
   - Win/loss results
   - Scores

2. **`nhl_three_in_four_analysis.csv`**
   - Every three-in-four situation found
   - All three games details
   - Total wins in the stretch

## How It Works

### Data Source
- Uses official **NHL API** (api-web.nhle.com)
- Fetches completed games for specified date range
- Processes all 32 NHL teams

### Back-to-Back Detection
1. Sorts each team's schedule chronologically
2. Finds games on consecutive days
3. Tracks both games' location (home/road)
4. Records outcomes

### Three-in-Four Detection
1. Looks for 3 games within a 4-day span
2. Tracks all three games
3. Calculates total wins

### Analysis
- Calculates win rates for different situations
- Splits by home/road
- Identifies travel patterns
- Generates betting insights

## Interpreting Results

### Win Rate Thresholds

| Win Rate | Interpretation | Betting Action |
|----------|----------------|----------------|
| >60% | Strong edge | **BET ON** |
| 55-60% | Moderate edge | Consider betting on |
| 45-55% | No clear edge | Avoid or use other factors |
| 40-45% | Moderate fade | Consider betting against |
| <40% | Strong fade | **BET AGAINST** |

### Sample Size Guidelines

| Games | Reliability | Notes |
|-------|-------------|-------|
| 30+ | High | Strong confidence |
| 15-29 | Medium | Moderate confidence |
| 8-14 | Low | Use cautiously |
| <8 | Very Low | Monitor for trends |

## Advanced Analysis

### Combine with Other Factors

The schedule situation is one factor. For stronger bets, combine with:

1. **Team strength** (standings, recent form)
2. **Goalie matchups** (especially if fatigued backup plays Game 2)
3. **Opponent quality** (playing weak team on B2B is better)
4. **Odds value** (is the market underpricing the home advantage?)

### Sample Betting Approach

```
Scenario: Team X is playing at home tonight, Game 2 of a back-to-back
         after playing on the road last night (ROAD → HOME pattern)

Base edge: 100% historical win rate (4/4)
Check:
  ✓ Team X is above .500 (good team)
  ✓ Opponent is below .500 (weak opponent)
  ✓ Team X's starting goalie is playing (well-rested)
  ✓ Odds are +100 or better (good value)

Action: BET ON Team X moneyline
Confidence: HIGH
```

## Historical Validation

### 2024-25 Season (Oct 1-24, 2024)

**Back-to-Back Stats:**
- Total situations: 34
- Game 2 home win rate: 75.0%
- Game 2 road win rate: 38.5%
- **Home advantage: +36.5 points**

**Recommended next step:**
Run analysis on 2023-24 and 2022-23 seasons to validate these findings across larger sample sizes.

## Example Commands

### Quick Current Season Check
```bash
python3 nhl_schedule_analyzer.py --start-date 2024-10-01 --end-date $(date +%Y-%m-%d)
```

### Multi-Season Analysis
```bash
# Run for last 3 seasons
for year in 2022 2023 2024; do
    python3 nhl_schedule_analyzer.py --start-date ${year}-10-01 --end-date $((year+1))-04-30
    mv nhl_back_to_back_analysis.csv nhl_b2b_${year}_${year+1}.csv
    mv nhl_three_in_four_analysis.csv nhl_3in4_${year}_${year+1}.csv
done
```

## Integration with Betting System

### Daily Workflow

1. **Check today's schedule** for back-to-back games
2. **Identify patterns** (especially ROAD → HOME or Game 2 at HOME)
3. **Apply filters** (team quality, matchups, odds)
4. **Place bets** on high-confidence situations

### Find Today's Back-to-Backs

```bash
# Get today's games from NHL API
curl "https://api-web.nhle.com/v1/schedule/$(date +%Y-%m-%d)" | jq '.gameWeek[].games[] | {home: .homeTeam.abbrev, away: .awayTeam.abbrev}'

# Check each team's previous game (manual or script)
# Look for teams that played yesterday
```

## Troubleshooting

### No Data Found

If the analyzer finds no games:
- Check date range (NHL season is Oct-Apr)
- Verify internet connection (needs NHL API access)
- Ensure dates are in YYYY-MM-DD format

### API Errors

If you get API errors:
- NHL API may be temporarily down
- Try again in a few minutes
- Check https://api-web.nhle.com/v1/schedule/2024-10-01 directly

## Future Enhancements

Potential additions:
- Real-time game fetcher (identifies today's B2B situations)
- Goalie fatigue analysis (does backup play Game 2?)
- Travel distance analysis (does distance matter?)
- Rest days analysis (coming off 2+ days rest vs B2B)
- Integration with odds API (auto-calculate value)

## Data Retention

The analyzer fetches data fresh each time. To build a historical database:

```bash
# Save results with date stamp
python3 nhl_schedule_analyzer.py --start-date 2024-10-01 --end-date 2024-10-24
mv nhl_back_to_back_analysis.csv nhl_b2b_$(date +%Y%m%d).csv
```

## Credits

- Data source: NHL Official API
- Analysis: Custom Python script
- Created: October 24, 2024

## Key Takeaways

1. **🔥 Home teams in Game 2 of back-to-backs win 75% of the time** (vs 38.5% for road teams)
2. **⭐ ROAD → HOME pattern is perfect (4-0)** - strong betting signal
3. **⚠️ Avoid betting on teams going HOME → ROAD** (33% win rate)
4. **📊 Sample sizes are small but edges are large** - validate with more data
5. **💰 This represents a potential betting edge** worth exploiting

## Recommended Action

✅ **Use this analyzer weekly** to find back-to-back situations
✅ **Focus on ROAD → HOME and Game 2 at HOME** patterns
✅ **Validate with larger historical datasets** (run for 2-3 prior seasons)
✅ **Track your bets** to measure actual edge in practice
✅ **Combine with other factors** (team strength, matchups, odds value)

---

**Last Updated:** October 24, 2024
**Season Analyzed:** 2024-25 (Oct 1-24)
**Next Update:** Run monthly to update statistics
