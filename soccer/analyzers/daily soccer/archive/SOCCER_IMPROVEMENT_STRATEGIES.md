# Soccer Betting System - Improvement Strategies for Underperforming Markets

## Executive Summary

Based on backtest results (Aug 1 - Oct 17, 2024), our soccer betting system shows significant performance disparity across different bet types:

**Current Performance:**
- **BTTS Yes**: 72% WR, +$197 profit ✅ (ONLY profitable market)
- **Match Winners (Home/Away/Draw)**: 42-45% WR, -$492 total loss ❌
- **BTTS No**: 50% WR, -$379 loss ❌
- **Over/Under 2.5**: Not yet backtested
- **Corners**: Not yet backtested
- **H1 Totals**: Not yet backtested (newly added)

**Break-even Requirements:**
- At 1.90 odds: Need 52.6% win rate
- At 2.00 odds: Need 50.0% win rate
- At 2.50 odds: Need 40.0% win rate

**Conclusion**: Match winners (42-45% WR at 2.0-2.3 odds) are significantly below break-even. System needs fundamental improvements, not just confidence threshold adjustments.

---

## 1. Match Winner Problems (Home/Away/Draw)

### Current Performance
```
Home Win: 48 bets | 20 wins | 42% WR | -$422 loss
Away Win: 11 bets | 5 wins  | 45% WR | -$37 loss
Draw:     4 bets  | 1 win   | 25% WR | -$33 loss
Total:    63 bets | 26 wins | 41% WR | -$492 loss
```

### Root Cause Analysis

#### Why Match Winners Fail:
1. **Soccer is inherently unpredictable** - low-scoring sport where single events (ref calls, injuries, red cards) can swing outcomes
2. **Odds already price in value** - bookmakers extremely sharp on match winner markets
3. **Model relies only on odds** - no team form, injuries, or tactical data
4. **Three-way market complexity** - Draw option makes prediction harder than binary markets
5. **Small sample edges don't overcome variance** - need 55%+ WR to be profitable at typical odds

### Improvement Strategies

#### Strategy 1: Add Team Form Features ⭐ **HIGHEST PRIORITY**
**What**: Incorporate last 5-10 games performance for each team
**Why**: Current model only uses pre-match odds, missing critical form indicators
**How**:
```python
# Add features to training data
features = {
    'home_last_5_wins': count_wins(home_team, last_5_games),
    'home_last_5_goals_for': avg_goals_scored(home_team, last_5_games),
    'home_last_5_goals_against': avg_goals_conceded(home_team, last_5_games),
    'away_last_5_wins': count_wins(away_team, last_5_games),
    'away_last_5_goals_for': avg_goals_scored(away_team, last_5_games),
    'away_last_5_goals_against': avg_goals_conceded(away_team, last_5_games),
    'home_points_last_5': points(home_team, last_5_games),
    'away_points_last_5': points(away_team, last_5_games)
}
```
**Expected Impact**: +5-10% win rate improvement
**Implementation Effort**: Medium (need historical results API)

#### Strategy 2: Train League-Specific Models
**What**: Separate models for each major league (EPL, La Liga, Serie A, etc.)
**Why**: Different leagues have different characteristics:
- Bundesliga: High-scoring, home advantage strong
- Serie A: Low-scoring, tactical, draws common
- La Liga: Top teams dominate
**How**:
```python
models_by_league = {
    'Premier League': train_model(epl_data),
    'La Liga': train_model(laliga_data),
    'Serie A': train_model(seria_data),
    # etc.
}
```
**Expected Impact**: +3-7% win rate improvement
**Implementation Effort**: Low (just retrain existing pipeline per league)

#### Strategy 3: Add Head-to-Head History
**What**: Include historical matchup data between specific teams
**Why**: Some teams consistently perform well/poorly against specific opponents
**How**:
```python
features = {
    'h2h_home_wins_last_10': count_h2h_wins(home_team, away_team, last_10),
    'h2h_avg_home_goals': avg_h2h_goals(home_team, away_team, last_10),
    'h2h_avg_away_goals': avg_h2h_goals(away_team, home_team, last_10),
    'h2h_btts_pct': btts_percentage(home_team, away_team, last_10)
}
```
**Expected Impact**: +2-5% win rate improvement
**Implementation Effort**: Medium

#### Strategy 4: Add Expected Goals (xG) Data
**What**: Use xG metrics from providers like FBref, Understat
**Why**: xG is better predictor of future performance than actual goals
**How**:
```python
features = {
    'home_xg_for_per_game': team_stats['home_xg_for'] / games_played,
    'home_xg_against_per_game': team_stats['home_xg_against'] / games_played,
    'away_xg_for_per_game': team_stats['away_xg_for'] / games_played,
    'away_xg_against_per_game': team_stats['away_xg_against'] / games_played
}
```
**Expected Impact**: +3-8% win rate improvement
**Implementation Effort**: High (need xG data source - paid API or web scraping)

#### Strategy 5: Filter by League Performance
**What**: Only bet on match winners in leagues where model performs well
**Why**: Backtest may show model works in certain leagues but not others
**How**:
```python
# Analyze backtest by league
league_performance = {
    'Ligue 1': {'wr': 0.71, 'roi': 0.18},  # Good - enable
    'Bundesliga': {'wr': 0.22, 'roi': -0.55},  # Bad - disable
    # etc.
}

# Only predict if league is profitable
if league in PROFITABLE_LEAGUES and model_confidence >= threshold:
    make_prediction()
```
**Expected Impact**: +5-15% win rate by avoiding bad leagues
**Implementation Effort**: Very Low (just filter existing backtest results)

#### Strategy 6: Ensemble with Alternative Data
**What**: Combine our model with expert picks, betting market movements, weather data
**Why**: Wisdom of crowds + model = better predictions
**How**:
```python
final_probability = (
    0.50 * our_model_prob +
    0.25 * expert_consensus_prob +
    0.15 * betting_market_prob +
    0.10 * weather_adjusted_prob
)
```
**Expected Impact**: +5-10% win rate improvement
**Implementation Effort**: High (need multiple data sources)

---

## 2. BTTS No Problems

### Current Performance
```
BTTS No: 66 bets | 33 wins | 50% WR | -$379 loss
```

### Root Cause Analysis

#### Why BTTS No Fails:
1. **At 50% WR, we're break-even at 2.00 odds** - but average odds are likely lower
2. **Modern soccer is high-scoring** - BTTS No is harder to hit than BTTS Yes
3. **Defensive errors common** - one mistake ruins BTTS No bet
4. **Model may be too aggressive** - predicting No when should be neutral

### Improvement Strategies

#### Strategy 1: Increase Confidence Threshold for BTTS No
**What**: Require 99.5%+ confidence instead of 98.5% for BTTS No
**Why**: 50% WR suggests we're not selective enough
**How**:
```python
MIN_BTTS_NO_CONFIDENCE = 0.995  # Stricter than BTTS Yes
MIN_BTTS_YES_CONFIDENCE = 0.985  # Keep current
```
**Expected Impact**: Reduce volume by 50%, improve WR to 58-62%
**Implementation Effort**: Very Low (one line change)

#### Strategy 2: Filter by League Scoring Trends
**What**: Only bet BTTS No in low-scoring leagues
**Why**: Serie A, Ligue 1, La Liga have lower BTTS rates than EPL, Bundesliga
**How**:
```python
LOW_SCORING_LEAGUES = ['Serie A', 'Ligue 1', 'La Liga']
if league in LOW_SCORING_LEAGUES and btts_no_prob >= threshold:
    make_prediction()
```
**Expected Impact**: +5-8% win rate by avoiding high-scoring leagues
**Implementation Effort**: Very Low

#### Strategy 3: Consider Team Defensive Stats
**What**: Add clean sheet frequency, goals conceded per game
**Why**: Teams with strong defenses more likely to keep BTTS No
**How**:
```python
features = {
    'home_clean_sheets_last_10': count_clean_sheets(home_team, 10),
    'away_clean_sheets_last_10': count_clean_sheets(away_team, 10),
    'home_goals_conceded_per_game': avg_goals_conceded(home_team),
    'away_goals_conceded_per_game': avg_goals_conceded(away_team)
}
```
**Expected Impact**: +3-7% win rate improvement
**Implementation Effort**: Medium

---

## 3. Over/Under 2.5 Goals

### Current Status
**Not yet backtested** - currently DISABLED

### Why O/U 2.5 Might Underperform:
1. **Similar issues to match winners** - odds already efficient
2. **Lacks scoring context** - doesn't consider team attacking/defensive strength
3. **Middle outcome common** - exactly 2 goals is frustrating for bettors

### Improvement Strategies Before Enabling

#### Strategy 1: Add Expected Goals Data
Same as match winners - xG is strongest predictor of total goals

#### Strategy 2: Add Team Scoring Trends
```python
features = {
    'home_goals_per_game_last_10': avg_goals_scored(home_team, 10),
    'away_goals_per_game_last_10': avg_goals_scored(away_team, 10),
    'home_goals_against_per_game': avg_goals_conceded(home_team, 10),
    'away_goals_against_per_game': avg_goals_conceded(away_team, 10),
    'home_over_2_5_rate_last_10': pct_over_25(home_team, 10),
    'away_over_2_5_rate_last_10': pct_over_25(away_team, 10)
}
```

#### Strategy 3: Consider Game State Factors
```python
features = {
    'league_avg_goals_per_game': league_stats['avg_goals'],
    'expected_importance': derby_or_cup_match,  # High stakes = defensive
    'weather_impact': temperature_effect_on_goals
}
```

---

## 4. First Half (H1) Totals

### Current Status
**Newly added** - not yet backtested

### Why H1 Might Succeed:
1. **Less efficient market** - bookmakers focus on FT markets
2. **Predictable patterns** - first 15 mins often scoreless, then picks up
3. **Ensemble models already trained** - `rf_first_half_over_0_5`, `gb_first_half_over_0_5`

### Strategies to Maximize H1 Performance

#### Strategy 1: Lower Confidence Threshold for H1
**What**: Try 97-98% instead of 99% for H1 bets
**Why**: Less efficient market may not need ultra-strict threshold
**How**:
```python
MIN_H1_CONFIDENCE = 0.975  # Slightly looser than FT markets
```

#### Strategy 2: Focus on H1 Over 0.5
**What**: Only bet H1 Over 0.5, not Under
**Why**: Over 0.5 has better odds value (typically 1.65-1.80 vs 2.00-2.20 for Under)

#### Strategy 3: Add First Half Specific Features
```python
features = {
    'home_h1_goals_per_game': avg_h1_goals(home_team),
    'away_h1_goals_per_game': avg_h1_goals(away_team),
    'home_h1_over_05_rate': pct_h1_over_05(home_team),
    'away_h1_over_05_rate': pct_h1_over_05(away_team),
    'early_kickoff_factor': is_early_kickoff(match_time)  # Early games often slower start
}
```

---

## 5. Recommended Implementation Priority

### Phase 1: Quick Wins (1-2 weeks)
1. ✅ **DONE**: Filter to BTTS Yes only (already most profitable)
2. **Filter match winners by league** - analyze backtest, disable bad leagues
3. **Increase BTTS No threshold to 99.5%** - if we re-enable it
4. **Test H1 totals at 97.5% threshold** - see if volume increases with good WR

### Phase 2: Feature Engineering (4-6 weeks)
1. **Add team form features (last 5-10 games)** - biggest expected impact
2. **Train league-specific models** - customize for each league's characteristics
3. **Add head-to-head history** - capture rivalry/matchup effects

### Phase 3: Advanced Data (8-12 weeks)
1. **Integrate expected goals (xG) data** - best predictor of future goals
2. **Add weather data** - temperature, rain, wind affect scoring
3. **Add lineup data** - missing key players impact outcomes

---

## 6. Testing & Validation Protocol

For each improvement:
1. **Backtest on historical data** (Aug 1 - Oct 17, 2024 minimum)
2. **Calculate key metrics**:
   - Win rate by market
   - ROI by market
   - ROI by league
   - Sharpe ratio (risk-adjusted returns)
3. **Forward test** for 2-4 weeks before full deployment
4. **Set stop-loss** - disable if cumulative ROI falls below -10%

---

## 7. Data Sources Needed

### Currently Using:
- ✅ API-Sports odds data (Bet365)
- ✅ API-Sports fixture results

### Recommended Additions:
- **Team Stats**: API-Sports `/teams/statistics` endpoint (form, goals, clean sheets)
- **Head-to-Head**: API-Sports `/fixtures/headtohead` endpoint
- **Expected Goals**: Understat API (free but unofficial) or FBref (scraping)
- **Lineups**: API-Sports `/fixtures/lineups` endpoint (key player availability)
- **Weather**: OpenWeather API (free tier available)

---

## 8. Estimated ROI Improvements

Based on typical improvements from adding features:

| Improvement | Est. WR Gain | Est. ROI Gain |
|---|---|---|
| Team form features | +5-10% | +15-25% |
| League-specific models | +3-7% | +10-20% |
| Expected goals data | +3-8% | +10-25% |
| Head-to-head history | +2-5% | +5-15% |
| League filtering | +5-15% | +15-40% |
| **Combined Effect** | **+15-30%** | **+50-100%** |

**Realistic Outcome**:
- Match winners: 42% WR → 57-62% WR (break-even at 52.6%)
- BTTS No: 50% WR → 58-65% WR
- System-wide: -67% ROI → +10-30% ROI

---

## 9. Next Steps

1. **Immediate**: Keep BTTS Yes only, monitor performance
2. **This week**: Analyze backtest results by league, create league whitelist
3. **Next 2 weeks**: Add team form features to model training
4. **Next month**: Retrain models with new features, backtest, deploy if positive
5. **Ongoing**: Track live performance, iterate on features

---

## Appendix: Break-Even Analysis

### Win Rate Required by Odds:

| Odds | Implied Prob | Break-Even WR | Profit Margin Needed |
|---|---|---|---|
| 1.50 | 66.7% | 66.7% | 0% |
| 1.70 | 58.8% | 58.8% | 0% |
| 1.90 | 52.6% | 52.6% | 0% |
| 2.00 | 50.0% | 50.0% | 0% |
| 2.20 | 45.5% | 45.5% | 0% |
| 2.50 | 40.0% | 40.0% | 0% |

**Key Insight**: At average odds of 2.00-2.30 for match winners, we need 50-52% WR minimum. Current 42-45% WR is 8-10 percentage points below break-even.

---

**Document Version**: 1.0
**Created**: October 19, 2025
**Last Updated**: October 19, 2025
**Author**: Soccer Betting System Analysis
