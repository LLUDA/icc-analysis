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
- This is where you plan your entry

### Step 3: CONTINUATION
- Wait for price to **break through** the level again
- This confirms the original move was valid
- **Enter HERE at the break level**

### Critical Filter: Correction Depth
**Only take trades where correction is ≤ 70% of the original move**

| Correction Depth | Win Rate |
|-----------------|----------|
| 0-50% | **76-100%** |
| 50-70% | **77-85%** |
| 70%+: | **51%** |

Deep corrections (70%+) are typically fakeouts or reversals.

---

## Entry Rules

1. **Entry:** At the break level (where indication happened)
2. **SL:** At the nearest significant structure level beyond the break
3. **TP:** At the next significant structure level in the direction of trade
4. **Min RR:** 2:1 required

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

## Structure Score (Direction-Specific)

### Structure Formation

| Structure | LONG | SHORT |
|-----------|------|--------|
| HH/HL forming | +20 | -20 |
| LH/LL forming | -20 | +20 |
| Partial HH/HL | +10 | -10 |
| Partial LH/LL | -10 | +10 |
| Ranging | 0 | 0 |

### Momentum

| Momentum | LONG | SHORT |
|----------|------|--------|
| Strong up | +10 | -10 |
| Strong down | -10 | +10 |

---

## S/R Zones

Shows significant support and resistance zones near current price.

---

## R:R Interest Level

| R:R | Interest |
|-----|----------|
| ≥7:1 | VERY INTERESTED |
| 4-6:1 | INTERESTED |
| 2-3:1 | HAPPY TO TAKE |
| <2:1 | NOT INTERESTED |

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

S/R ZONES (relevant to direction):
  - [zone]

TRADE SETUP (if provided):
  Direction: LONG/SHORT
  Entry: X
  SL: X
  TP: X
  R:R: X:1 - INTEREST

  >>> REVISED PROBABILITY: XX%
```

---

## Usage

```bash
python icc_analysis.py <SYMBOL> [ENTRY] [SL] [TP]

Examples:
python icc_analysis.py GBPUSD
python icc_analysis.py BTC-USD 66000 65500 68000
python icc_analysis.py US30
```

---

## Symbols

| Trading Pair | Yahoo Symbol |
|-------------|-------------|
| GBPUSD | GBPUSD=X |
| USDJPY | USDJPY=X |
| EURJPY | EURJPY=X |
| XAUUSD | GC=F (Gold Futures) |
| US30 | ^DJI (Dow Jones) |
| BTCUSD | BTC-USD |

---

## Files

- `icc_analysis.py` - Main analysis script
- `FRAMEWORK.md` - This documentation
