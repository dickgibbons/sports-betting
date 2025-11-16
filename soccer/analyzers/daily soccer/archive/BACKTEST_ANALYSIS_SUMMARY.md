# Backtest Analysis Summary - Form-Enhanced Models (Phase 2)

## Executive Summary

Phase 2 form-enhanced models (45 features: 13 odds + 32 team form) have been successfully implemented and backtested on historical 2024 data. Initial results reveal critical calibration issues that need to be addressed.

## Test Backtest Results (August 15-20, 2024)

### Overall Performance
- **Period**: 6 days (Aug 15-20, 2024)
- **Total Bets**: 687
- **Win Rate**: 43.5% (299W-388L)
- **ROI**: -248.2%
- **Final Bankroll**: -$1,482 (started with $1,000)
- **Confidence Threshold**: 60% (relaxed for testing)

### Performance by Market

| Market | Bets | Wins | Win Rate | Profit/Loss | Avg Confidence |
|--------|------|------|----------|-------------|----------------|
| **BTTS No** | 13 | 11 | **84.6%** ✅ | **+$286.38** | 60.4% |
| Home Win | 337 | 147 | 43.6% ❌ | -$2,259.76 | 95.6% |
| Under 2.5 | 337 | 141 | 41.8% ❌ | -$508.74 | 94.7% |

### Performance by League (Top 10)

| League | Bets | Wins | Win Rate | Profit/Loss |
|--------|------|------|----------|-------------|
| UEFA Europa League | 15 | 11 | 73.3% | +$309.32 |
| UEFA Europa Conference League | 37 | 22 | 59.5% | +$274.92 |
| First League | 16 | 10 | 62.5% | +$271.50 |
| Premier League | 21 | 12 | 57.1% | +$187.12 |
| Brazil Serie A | 20 | 7 | 35.0% | +$508.71 (variance) |
| Eredivisie | 18 | 8 | 44.4% | +$355.91 |

## Key Findings

### 1. **Severe Model Overconfidence**

The match winner and totals predictions show extreme overconfidence:
- **Home Win**: 95.6% average confidence → 43.6% actual win rate
- **Under 2.5**: 94.7% average confidence → 41.8% actual win rate

**This represents a ~50 percentage point calibration error**, indicating the models are predicting outcomes with far more certainty than warranted.

### 2. **BTTS No Predictions Are Highly Accurate**

Despite only 60% average confidence (barely above threshold), BTTS No predictions achieved:
- 84.6% win rate (11/13 bets)
- +$286 profit in just 6 days
- **This is the system's strongest signal**

### 3. **UEFA Competition Strength**

European competitions showed significantly better performance:
- UEFA Europa League: 73.3% WR
- UEFA Europa Conference League: 59.5% WR
- These competitions may have more predictable patterns

### 4. **Volume Issue**

With relaxed 60% threshold:
- 687 bets in 6 days = ~115 bets/day
- This is far too many for selective betting
- Production 99% threshold would dramatically reduce volume (likely to near zero based on calibration issues)

## Technical Implementation Status

### ✅ Completed

1. **Historical Backtest Infrastructure**
   - `backtest_historical_2024.py`: Fetches completed matches (status='FT')
   - `backtest_historical_2024_relaxed.py`: Relaxed thresholds for model evaluation
   - Successfully integrated with form-enhanced models

2. **Form Feature Integration**
   - Team form fetcher working correctly
   - 45-feature vectors being generated
   - Caching system operational

3. **Result Validation**
   - Predictions evaluated against actual match outcomes
   - Detailed CSV outputs generated
   - Performance tracked by market and league

### ⏳ In Progress

- **Full Historical Backtest** (August 15 - October 17, 2024)
  - Status: Running in background (PID: 56979)
  - Expected duration: 2-3 hours
  - Will provide ~64 days of comprehensive data

## Critical Issues Identified

### Issue 1: Model Calibration

**Problem**: Models are severely overconfident, particularly for match winners and totals.

**Evidence**:
- 95.6% predicted confidence → 43.6% actual accuracy (Home Win)
- 94.7% predicted confidence → 41.8% actual accuracy (Under 2.5)

**Possible Causes**:
1. Training data mismatch (synthetic odds vs. real odds)
2. Feature scaling issues
3. Model overfitting to training set
4. Class imbalance not properly handled

**Recommended Solutions**:
1. Retrain models with proper probability calibration (Platt scaling, isotonic regression)
2. Use cross-validation with actual historical odds data
3. Implement temperature scaling on model outputs
4. Consider ensemble calibration techniques

### Issue 2: Feature Effectiveness

**Question**: Are team form features actually improving predictions, or are they being drowned out by odds features?

**Evidence**:
- Models trained on 45 features show 86-94% accuracy on test set
- But real-world performance is dramatically worse (43-44% WR)
- This suggests potential overfitting or poor generalization

**Next Steps**:
1. Analyze feature importance from trained models
2. Compare form-enhanced model vs. odds-only model on same backtest data
3. Test ablation: remove form features and see if performance changes

### Issue 3: Production Deployment Risk

**Problem**: With 99% confidence threshold in production, system likely generates ZERO bets.

**Evidence**:
- Backtest with 99% threshold found 0 bets (as seen in initial strict backtest)
- Relaxed 60% threshold needed to generate any predictions
- Calibration error means even high-confidence predictions are unreliable

**Recommendation**: **DO NOT deploy to production without recalibration**

## Comparison to Baseline

### Previous System (Odds-Only, Enhanced Models)
From earlier backtest (Aug 1 - Oct 17, 2024):
- **BTTS Yes**: 72% WR, +$197 profit ✅
- **Match Winners**: 42% WR, -$492 loss ❌
- **System ROI**: -67%
- **Total**: 161 bets over 77 days

### Current System (Form-Enhanced, Relaxed)
From test (Aug 15-20, 2024):
- **BTTS No**: 84.6% WR, +$286 profit ✅
- **Home Win**: 43.6% WR, -$2,260 loss ❌
- **System ROI**: -248%
- **Total**: 687 bets over 6 days

### Key Differences
1. **Volume**: Form-enhanced system generates 10x more predictions (at 60% threshold)
2. **BTTS**: Both systems show BTTS as strongest market
   - Old: BTTS Yes (72% WR)
   - New: BTTS No (84.6% WR)
3. **Match Winners**: Both systems struggle (~42-44% WR)
4. **Calibration**: New system shows severe overconfidence issues

## Next Steps

### Immediate (Before Production)

1. **Complete Full Backtest**
   - Wait for Aug 15 - Oct 17, 2024 backtest to finish
   - Analyze ~64 days of comprehensive data
   - Compare results to baseline system

2. **Model Recalibration**
   - Implement Platt scaling or isotonic regression
   - Retrain with proper cross-validation
   - Target: Predicted confidence = Actual win rate (±5%)

3. **Threshold Optimization**
   - Find optimal confidence thresholds for each market
   - Balance volume vs. accuracy
   - Target: 5-10 high-quality bets per day

### Medium Term

4. **Feature Analysis**
   - Compare form-enhanced vs. odds-only models
   - Identify which form features add value
   - Remove noisy features

5. **League Specialization**
   - Focus on profitable leagues (UEFA competitions, Premier League)
   - Blacklist consistently unprofitable leagues
   - Consider league-specific models

6. **Market Focus**
   - Double down on BTTS predictions (strongest signal)
   - Consider dropping match winner predictions
   - Explore H1 totals as alternative

### Long Term

7. **Alternative Approaches**
   - Ensemble multiple model types (not just RF + GB)
   - Try neural networks with better calibration
   - Explore gradient boosting with proper loss functions

8. **Live Data Testing**
   - Paper trading for 2-4 weeks
   - Monitor calibration on new data
   - Adjust thresholds based on live performance

## Conclusion

Phase 2 form-enhanced models successfully integrate team form features and generate predictions, but suffer from severe calibration issues that make them unsuitable for production deployment. The test backtest reveals:

✅ **Strengths**:
- BTTS No predictions are highly accurate (84.6% WR)
- UEFA competitions show strong performance
- Infrastructure is solid and scalable

❌ **Critical Issues**:
- Severe model overconfidence (~50 point calibration error)
- Match winner predictions underperforming badly
- At production thresholds (99%), system generates zero bets

**Recommendation**: **Recalibrate models before production deployment**. Focus on BTTS market where signals are strongest, and consider dropping match winner predictions entirely.

The full historical backtest (currently running) will provide more comprehensive data to validate these findings across 64 days of matches.

---

**Document Created**: October 19, 2025
**Backtest Period**: August 15-20, 2024 (test) | August 15 - October 17, 2024 (full - in progress)
**Models**: Form-Enhanced (45 features: 13 odds + 32 team form)
**Status**: Phase 2 implementation complete | Calibration issues identified | Full backtest in progress
