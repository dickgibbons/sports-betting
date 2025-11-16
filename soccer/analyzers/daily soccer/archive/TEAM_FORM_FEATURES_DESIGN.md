# Team Form Features - Design Document

## API-Sports Data Available

### 1. `/teams/statistics` Endpoint
**Parameters**: team_id, league_id, season

**Available Data**:
- `form`: String of recent results (e.g., "WWWWDDWWWLL") - W=Win, D=Draw, L=Loss
- `fixtures.played`: Total/home/away matches played
- `fixtures.wins`: Total/home/away wins
- `fixtures.draws`: Total/home/away draws
- `fixtures.loses`: Total/home/away losses
- `goals.for.total`: Goals scored (home/away/total)
- `goals.for.average`: Avg goals scored per game (home/away/total)
- `goals.against.total`: Goals conceded (home/away/total)
- `goals.against.average`: Avg goals conceded per game
- `clean_sheet`: Clean sheets (home/away/total)
- `failed_to_score`: Times failed to score (home/away/total)
- `biggest.wins.home/away`: Largest victory margins
- `biggest.loses.home/away`: Largest defeat margins
- `biggest.streak.wins/draws/loses`: Longest streaks

### 2. `/fixtures` Endpoint with `last=N` parameter
**Parameters**: team_id, league_id, season, last=10

**Available Data** (per match):
- Match date, venue, status
- Home/away teams
- Goals scored by each team
- Halftime score, fulltime score
- Winner indicator

**Use Case**: Calculate rolling form over last 5-10 games

### 3. `/fixtures/headtohead` Endpoint
**Parameters**: h2h=teamA-teamB, last=N

**Available Data**:
- Historical matchups between two specific teams
- Goals scored by each team
- Winner history
- BTTS history

---

## Proposed Features to Add

### Category 1: Recent Form (Last 5-10 Games) ⭐ **HIGHEST PRIORITY**

#### For Home Team:
1. `home_wins_last_5`: Wins in last 5 games
2. `home_draws_last_5`: Draws in last 5 games
3. `home_losses_last_5`: Losses in last 5 games
4. `home_points_last_5`: Points earned (3 per win, 1 per draw)
5. `home_goals_for_last_5`: Total goals scored in last 5
6. `home_goals_against_last_5`: Total goals conceded in last 5
7. `home_goal_diff_last_5`: Goal differential (+/-)
8. `home_btts_rate_last_5`: % of games with both teams scoring
9. `home_over_25_rate_last_5`: % of games with >2.5 goals
10. `home_clean_sheets_last_5`: Clean sheets in last 5

#### For Away Team:
11. `away_wins_last_5`: Wins in last 5 games
12. `away_draws_last_5`: Draws in last 5 games
13. `away_losses_last_5`: Losses in last 5 games
14. `away_points_last_5`: Points earned
15. `away_goals_for_last_5`: Total goals scored in last 5
16. `away_goals_against_last_5`: Total goals conceded in last 5
17. `away_goal_diff_last_5`: Goal differential
18. `away_btts_rate_last_5`: % games with BTTS
19. `away_over_25_rate_last_5`: % games with >2.5 goals
20. `away_clean_sheets_last_5`: Clean sheets in last 5

**Total**: 20 form features

### Category 2: Season-Long Statistics (Context)

#### For Home Team:
21. `home_season_win_rate`: Overall win %
22. `home_season_goals_per_game`: Avg goals scored per game
23. `home_season_conceded_per_game`: Avg goals conceded per game
24. `home_home_record_wins`: Wins at home this season
25. `home_home_record_draws`: Draws at home
26. `home_home_record_losses`: Losses at home

#### For Away Team:
27. `away_season_win_rate`: Overall win %
28. `away_season_goals_per_game`: Avg goals scored per game
29. `away_season_conceded_per_game`: Avg goals conceded per game
30. `away_away_record_wins`: Wins away this season
31. `away_away_record_draws`: Draws away
32. `away_away_record_losses`: Losses away

**Total**: 12 season features

### Category 3: Head-to-Head History (Optional - Phase 2.5)

33. `h2h_home_wins_last_5`: Home team wins in last 5 H2H
34. `h2h_away_wins_last_5`: Away team wins in last 5 H2H
35. `h2h_draws_last_5`: Draws in last 5 H2H
36. `h2h_btts_rate`: % of H2H with both teams scoring
37. `h2h_avg_goals`: Avg total goals in H2H matches
38. `h2h_over_25_rate`: % of H2H with >2.5 goals

**Total**: 6 H2H features

---

## Implementation Plan

### Phase 2.1: Form Features (Week 1-2)

**Step 1**: Create `TeamStatsCache` class
- Cache team statistics to avoid repeated API calls
- Store in memory with TTL (time-to-live)
- Persist to disk for historical data

**Step 2**: Implement `fetch_team_form()` function
- Call `/fixtures` endpoint with `last=10`
- Calculate last 5 games statistics:
  - Wins/draws/losses
  - Goals for/against
  - BTTS rate, Over 2.5 rate
  - Clean sheets

**Step 3**: Implement `fetch_team_season_stats()` function
- Call `/teams/statistics` endpoint
- Extract season-long averages:
  - Win rate
  - Goals per game
  - Conceded per game
  - Home/away splits

**Step 4**: Update `extract_features()` in `soccer_best_bets_daily.py`
- Add team form features to existing odds features
- Maintain backwards compatibility with existing models

**Step 5**: Update training pipeline
- Modify `train_soccer_models.py` to:
  - Fetch team form data for historical matches
  - Add form features to training data
  - Retrain models with expanded feature set

**Step 6**: Backtest with new features
- Run backtest on Aug 1 - Oct 17, 2024 data
- Compare performance vs. odds-only model
- Expected improvement: +5-10% win rate

### Phase 2.2: H2H Features (Week 3-4)

**Step 1**: Implement `fetch_h2h_history()` function
- Call `/fixtures/headtohead` endpoint
- Calculate H2H statistics

**Step 2**: Add H2H features to model
- Integrate with existing form + season features
- Retrain and validate

---

## Data Flow Architecture

```
Match Data (from API)
  ├─> Home Team ID
  │   ├─> fetch_team_form(team_id, league_id, season) -> Last 5 games stats
  │   └─> fetch_team_season_stats(team_id, league_id, season) -> Season averages
  │
  ├─> Away Team ID
  │   ├─> fetch_team_form(team_id, league_id, season) -> Last 5 games stats
  │   └─> fetch_team_season_stats(team_id, league_id, season) -> Season averages
  │
  ├─> Odds Data (existing)
  │   └─> Home odds, draw odds, away odds, BTTS odds, totals odds
  │
  └─> Combined Feature Vector (38 features)
      ├─> 20 form features (last 5 games)
      ├─> 12 season features (full season)
      └─> 6 existing odds features
```

---

## API Rate Limiting Considerations

**Current API Plan**: Likely free tier or basic tier
- **Requests per day**: Typically 100-500 for free tier
- **Requests per minute**: Typically 10-30

**Our Usage**:
- Per match prediction: 2 API calls (home team stats + away team stats)
- For 50 matches/day: 100 API calls
- With caching: ~10-20 API calls (only for new teams)

**Caching Strategy**:
1. Cache team stats for 24 hours (stats don't change mid-season rapidly)
2. Store in local SQLite database
3. Refresh cache only when:
   - Match date is after last cached date
   - No cached data exists for team

---

## Expected Performance Improvement

### Current System (Odds Only):
- BTTS Yes: 72% WR, +$197 profit (with league filtering)
- Match Winners: 42-45% WR, -$492 loss

### With Form Features (Estimated):
- BTTS Yes: **77-82% WR**, +$300-400 profit
- Match Winners: **52-58% WR**, break-even to +$50-100

### Reasoning:
- Team form captures recent momentum (hot/cold streaks)
- Goals for/against trends predict BTTS better than odds alone
- Home/away splits improve match outcome predictions
- Academic research shows form features add 5-15% to model accuracy

---

## Testing & Validation Protocol

1. **Backtest on Aug 1 - Oct 17, 2024**:
   - Fetch historical team stats for each match date
   - Generate predictions with form features
   - Compare win rate vs. odds-only model

2. **Forward Test for 2-3 weeks**:
   - Deploy to live system
   - Monitor win rate daily
   - Track API call usage

3. **A/B Test** (Optional):
   - Run odds-only model in parallel
   - Compare results side-by-side
   - Switch to form model if >5% improvement

---

## Next Steps

1. ✅ **DONE**: API exploration and data validation
2. **NOW**: Implement `TeamStatsCache` class
3. **NEXT**: Implement `fetch_team_form()` function
4. **THEN**: Update `extract_features()` to include form data
5. **FINALLY**: Retrain models and backtest

---

**Document Version**: 1.0
**Created**: October 19, 2025
**Target Completion**: 2-3 weeks (by Nov 10, 2025)
