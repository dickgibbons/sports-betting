# Soccer Totals Strategy Report
**Date:** November 30, 2025
**Analysis Period:** 2022-2024 (3 Seasons)
**Sample Size:** 11,461 matches across 12 leagues

---

## Executive Summary

Multi-season backtest analysis identified **4 statistically significant profitable angles** in soccer totals markets. The best opportunities are concentrated in high-scoring European leagues, particularly the Bundesliga, Eliteserien, and Eredivisie.

### Key Findings

| Strategy | Hit Rate | Edge | ROI | Sample | Confidence |
|----------|----------|------|-----|--------|------------|
| **Bundesliga Over 2.5** | 61.1% | +8.5% | +16.1% | 923 | HIGH |
| **Eliteserien Over 2.5** | 60.1% | +7.5% | +14.3% | 725 | HIGH |
| **Eredivisie Over 2.5** | 59.6% | +6.9% | +13.2% | 957 | HIGH |
| **Premier League Over 2.5** | 58.0% | +5.4% | +10.2% | 1,140 | HIGH |

---

## Methodology

### Data Source
- **API:** Football API (api-sports.io)
- **Seasons:** 2022-23, 2023-24, 2024-25
- **Leagues:** 12 major European leagues
- **Status:** Finished matches only

### Edge Calculation
```
Edge = (Historical Hit Rate - Implied Probability) × 100
Implied Probability = 1 / Typical Odds
ROI = (Hit Rate × Decimal Odds - 1) × 100
```

### Typical Market Odds Used
| Market | Odds | Implied Probability |
|--------|------|---------------------|
| Over 2.5 | 1.90 | 52.6% |
| Over 3.5 | 2.75 | 36.4% |
| Under 2.5 | 1.95 | 51.3% |
| H1 Over 1.5 | 2.50 | 40.0% |

---

## Detailed Analysis

### 1. Bundesliga Over 2.5 Goals

**The Best Angle**

| Metric | Value |
|--------|-------|
| Hit Rate | 61.1% |
| Sample Size | 923 matches |
| Edge vs Market | +8.5% |
| Expected ROI | +16.1% |
| Confidence | HIGH |

**Season-by-Season Consistency:**
| Season | Hit Rate | Consistent? |
|--------|----------|-------------|
| 2022-23 | 60.7% | Yes |
| 2023-24 | 62.5% | Yes |
| 2024-25 | 60.1% | Yes |

**Why It Works:**
- Bundesliga has the highest average goals per game (~3.1) among top 5 leagues
- Open, attacking style of play
- Less defensive focus than Serie A or La Liga
- Consistent across all 3 seasons

**Recommended Stake:** 1.5-2 units (High confidence)

---

### 2. Eliteserien (Norway) Over 2.5 Goals

**Strong Second Option**

| Metric | Value |
|--------|-------|
| Hit Rate | 60.1% |
| Sample Size | 725 matches |
| Edge vs Market | +7.5% |
| Expected ROI | +14.3% |
| Confidence | HIGH |

**Why It Works:**
- Norwegian league is consistently high-scoring
- Less market attention means better odds available
- Smaller pool of teams leads to predictable patterns

**Recommended Stake:** 1-1.5 units (High confidence)

---

### 3. Eredivisie (Netherlands) Over 2.5 Goals

**Third Best Option**

| Metric | Value |
|--------|-------|
| Hit Rate | 59.6% |
| Sample Size | 957 matches |
| Edge vs Market | +6.9% |
| Expected ROI | +13.2% |
| Confidence | HIGH |

**Why It Works:**
- Dutch football favors attacking play
- Young, developing players = more mistakes and goals
- Ajax, PSV historically score heavily

**Recommended Stake:** 1-1.5 units (High confidence)

---

### 4. Premier League Over 2.5 Goals

**Most Liquid Market**

| Metric | Value |
|--------|-------|
| Hit Rate | 58.0% |
| Sample Size | 1,140 matches |
| Edge vs Market | +5.4% |
| Expected ROI | +10.2% |
| Confidence | HIGH |

**Why It Works:**
- Highest-scoring top 5 league after Bundesliga
- Fast pace, end-to-end football
- Best odds availability (most liquid market)

**Recommended Stake:** 1 unit (High confidence, lower edge)

---

## First Half Analysis

### H1 Over 1.5 Goals

First half over markets showed less edge overall, but Bundesliga stood out:

| League | H1 O1.5 Rate | Edge | Sample |
|--------|--------------|------|--------|
| Bundesliga | 44.4% | +4.4% | 923 |
| Eredivisie | 42.8% | +2.8% | 957 |
| Eliteserien | 41.2% | +1.2% | 725 |

**Recommendation:** Only bet Bundesliga H1 Over 1.5 when combined with other angles (e.g., strong attacking teams, high xG expected)

---

## Markets to AVOID

### Under Markets (No Edge Found)

| Market | Hit Rate | Edge | Status |
|--------|----------|------|--------|
| Under 2.5 (overall) | 47.2% | -4.1% | AVOID |
| Under 3.5 (overall) | 60.8% | -8.5% | AVOID |
| La Liga Under 2.5 | 49.1% | -2.2% | AVOID |

Under markets are priced efficiently - no value found.

### BTTS Markets (Minimal Edge)

| Market | Hit Rate | Edge | Status |
|--------|----------|------|--------|
| BTTS Yes (overall) | 55.2% | -1.9% | AVOID |
| BTTS No (overall) | 44.8% | -3.9% | AVOID |

BTTS markets are tight - not worth pursuing.

---

## Implementation Strategy

### Daily Selection Process

1. **Check Today's Fixtures:**
   - Filter for Bundesliga, Eliteserien, Eredivisie, Premier League matches

2. **Verify Odds:**
   - Only bet if Over 2.5 odds are 1.85 or higher
   - Sweet spot: 1.90-2.00

3. **Avoid:**
   - Matches with elite defensive goalkeepers on both sides
   - Extreme weather conditions
   - End-of-season dead rubbers (lower intensity)

4. **Stake Sizing:**
   - Bundesliga: 2 units
   - Eliteserien/Eredivisie: 1.5 units
   - Premier League: 1 unit

### Expected Monthly Performance

Assuming 30-40 qualifying bets per month:

| Scenario | Bets | Win Rate | ROI | Monthly Profit |
|----------|------|----------|-----|----------------|
| Conservative | 30 | 58% | +10% | +$300 (at $100/unit) |
| Expected | 35 | 59% | +12% | +$420 |
| Optimistic | 40 | 61% | +15% | +$600 |

---

## Risk Management

### Kelly Criterion Application

For Bundesliga Over 2.5:
```
Kelly % = (bp - q) / b
Where:
  b = 0.90 (decimal odds - 1)
  p = 0.611 (win probability)
  q = 0.389 (loss probability)

Kelly % = (0.90 × 0.611 - 0.389) / 0.90
        = (0.55 - 0.389) / 0.90
        = 17.9%
```

**Recommended:** Use 25% Kelly (4.5% of bankroll per bet) for safety.

### Stop-Loss Rules

- Daily: Stop after 3 consecutive losses
- Weekly: Review if win rate drops below 50%
- Monthly: Reassess if ROI goes negative

---

## Files Created

1. **Analysis Script:** `/Users/dickgibbons/sports-betting/soccer/analyzers/multi_season_totals_backtest.py`
2. **Cached Data:** `/Users/dickgibbons/sports-betting/soccer/analyzers/cache/multi_season_data.json` (11,461 matches)
3. **This Report:** `/Users/dickgibbons/sports-betting/reports/2025-11-30/SOCCER_TOTALS_STRATEGY_REPORT.md`

---

## Conclusion

The analysis confirms that **Over 2.5 goals in high-scoring European leagues** offers a consistent, statistically significant edge. The Bundesliga stands out as the best opportunity with 61.1% hit rate and +16.1% ROI over 3 seasons.

**Priority Order:**
1. Bundesliga Over 2.5 (Best edge, high sample)
2. Eliteserien Over 2.5 (Second best, good sample)
3. Eredivisie Over 2.5 (Solid third option)
4. Premier League Over 2.5 (Most liquid, smaller edge)

**First Half Markets:** Only pursue Bundesliga H1 Over 1.5 as a secondary play.

**Avoid:** All Under markets and BTTS markets - no edge found.

---

*Report generated from 11,461 matches across 3 seasons (2022-2024)*
