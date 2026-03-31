# ICC Trading Analysis Framework

## Overview
Top-down analysis showing only the favorable action with probability of success.

---

## ICC Method (Indication → Correction → Continuation)

### Step 1: INDICATION
- Identify swing high/low on 1H timeframe
- Wait for price to **break** this structure level
- This shows market intent

### Step 2: CORRECTION  
- Wait for price to **pull back** to the broken level
- Measure correction depth as % of original move
- **Critical filter:** Only continue if correction ≤ 80% of original move

### Step 3: CONTINUATION
- Wait for price to **break through** the level again
- This confirms the original move was valid
- **Enter HERE at the break level**

### Entry Rules

1. **Entry:** At the break level (where indication happened)
2. **SL:** At the nearest significant structure level beyond the break
3. **TP:** At the next significant structure level in the direction of trade
4. **Min RR:** 1.5:1 required (can go lower for high conviction setups)

---

## HYBRID APPROACH

### Two Filter Modes Based on Pair Quality

#### **Tier 1: High-Quality Pairs** (EURUSD, AUDUSD, GBPUSD)
**Looser Filters:**
- ✅ Either 4H OR 1H trend aligned
- ✅ Correction ≤ 80%
- ✅ RR ≥ 1.5
- **Expected WR:** 75-92%

#### **Tier 2: Medium-Quality Pairs** (GBPJPY, USDJPY)
**Moderate Filters:**
- ✅ Either 4H OR 1H trend aligned  
- ✅ Correction ≤ 70%
- ✅ RR ≥ 2.0
- **Expected WR:** 60-75%

#### **Tier 3: Avoid These Pairs**
**GBPCAD, USDCAD, NZDUSD, EURGBP**
- Only trade with strictest filters or avoid entirely
- Historical WR below 50%

---

## Critical Filters (Tested & Validated)

### 1. Correction Depth
**Most important filter discovered:**

| Correction Depth | Win Rate | Action |
|-----------------|----------|--------|
| 0-50% | 76-100% | ✅ Excellent |
| 50-80% | 72-85% | ✅ Good |
| 80%+ | ~50% | ❌ Avoid |

### 2. Trend Alignment
**Either 4H OR 1H trend works** - doesn't need both:
- Adding 1H trend increases setups by 40%
- Only slightly reduces WR

### 3. Minimum RR
**Lower RR (≥1.5) actually IMPROVES WR:**
- RR ≥ 2.0: ~76% WR
- RR ≥ 1.5: ~78% WR + 40% more setups

---

## Probability of Success Formula

```
Base: 50%
+ Structure alignment (up to 40%)
+ R:R bonus (up to 10%)
= Final probability (capped at 95%)
```

### Structure Contribution
| Aligned Score | Contribution |
|---------------|--------------|
| 90+ (exceptional) | +40% |
| 60-89 | +25-35% |
| 30-59 | +15-25% |
| 1-29 | +5-15% |
| 0 or negative | Not favorable |

### R:R Bonus
| R:R | Bonus |
|-----|-------|
| ≥7:1 | +10% |
| 4-6:1 | +7% |
| 2-3:1 | +3% |
| <2:1 | -5% |

---

## Backtest Results (6 Months, 5 Pairs)

### Final Optimized Strategy

| Pair | Setups | Win Rate | Avg RR |
|------|--------|----------|--------|
| EURUSD | 12 | **92%** | 2.18:1 |
| AUDUSD | 11 | **82%** | 4.55:1 |
| GBPUSD | 11 | **73%** | 3.37:1 |
| GBPJPY | 5 | 60% | 2.36:1 |
| USDJPY | 2 | 50% | 2.38:1 |

### Total: 41 setups | **78% WR** | 3.17:1 RR | 2.25R EV

---

## Daily + 4H + 1H Analysis Checklist

```
DAILY:
  □ Trend direction
  □ Key S/R levels
  □ Major structure breaks

4H:
  □ Trend confirmation
  □ Swing highs/lows
  □ SL/TP zones

1H:
  □ Wait for indication (break of structure)
  □ Wait for correction (measure depth)
  □ Wait for continuation (break of level)
  □ Enter at break level
```

---

## Output Format

```
>>> ACTION: LONG/SHORT
>>> PROBABILITY OF SUCCESS: XX%

STRUCTURE BREAKDOWN:
  DAILY: [structure]
    [point] (+/-X)
  4H: [structure]
    [point] (+/-X)
  1H: [structure]
    [point] (+/-X)

CORRECTION ANALYSIS:
  Original move: X pips
  Correction: X pips (XX% depth)
  [PASS/FAIL] - Must be ≤ 80%

TRADE SETUP:
  Direction: LONG/SHORT
  Entry: X
  SL: X
  TP: X
  R:R: X:1 - INTEREST

  >>> REVISED PROBABILITY: XX%
```

---

## Symbols

| Trading Pair | Yahoo Symbol |
|-------------|-------------|
| EURUSD | EURUSD=X |
| AUDUSD | AUDUSD=X |
| GBPUSD | GBPUSD=X |
| GBPJPY | GBPJPY=X |
| USDJPY | USDJPY=X |
| XAUUSD | GC=F (Gold Futures) |

---

## Files

- `icc_final_optimized.py` - Final validated backtest with hybrid filters
- `icc_smart.py` - Smart selective strategy with pair-specific filters
- `icc_deep_research.py` - Analysis of various filter combinations
