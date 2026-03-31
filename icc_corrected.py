#!/usr/bin/env python3
"""
ICC METHOD CORRECTED - Entry on Continuation Break
===================================================
Correct logic:
1. INDICATION - Swing high/low breaks
2. CORRECTION - Price pulls back to broken level
3. CONTINUATION - Price breaks THROUGH the level again
4. ENTRY - At the break level, on continuation confirmation
"""

import yfinance as yf
from datetime import timedelta


class ICCCorrected:
    """ICC Method with correct entry logic - enter on continuation break"""

    def __init__(self):
        self.pairs = ["GBPUSD=X", "EURUSD=X", "GBPJPY=X", "EURJPY=X", "USDJPY=X"]

    def get_swings(self, data, is_high=True, lookback=5):
        """Find swing highs/lows"""
        swings = []
        for i in range(lookback, len(data) - lookback):
            if is_high:
                if data[i] == max(data[i - lookback : i + lookback + 1]):
                    swings.append((i, data[i]))
            else:
                if data[i] == min(data[i - lookback : i + lookback + 1]):
                    swings.append((i, data[i]))
        return swings

    def get_trend_4h(self, highs, lows, idx):
        """Get trend from 4H swings"""
        if idx < 10:
            return "RANGE"

        recent_h = [h for i, h in self.get_swings(highs[:idx], True)][-4:]
        recent_l = [l for i, l in self.get_swings(lows[:idx], False)][-4:]

        if len(recent_h) < 4 or len(recent_l) < 4:
            return "RANGE"

        # UPTREND: Higher highs AND higher lows
        if recent_h[-1] > recent_h[0] and recent_l[-1] > recent_l[0]:
            return "UPTREND"
        # DOWNTREND: Lower highs AND lower lows
        elif recent_h[-1] < recent_h[0] and recent_l[-1] < recent_l[0]:
            return "DOWNTREND"
        return "RANGE"

    def check_continuation_pattern(
        self, data, highs, lows, correction_start, direction
    ):
        """
        Check for continuation intention pattern on 15M
        SHORT: Want lower highs (supply coming in) during correction
        LONG: Want higher lows (demand coming in) during correction
        """
        lookback = 15
        data_start = max(0, correction_start - lookback)

        if direction == "SHORT":
            # Find swing highs in correction
            swing_highs = []
            for i in range(data_start, min(correction_start + 5, len(data))):
                if highs[i] == max(highs[max(0, i - 2) : min(len(highs), i + 3)]):
                    swing_highs.append((i, highs[i]))

            if len(swing_highs) >= 2:
                # Check for lower highs (supply coming in)
                lh_count = sum(
                    1
                    for i in range(1, len(swing_highs))
                    if swing_highs[i][1] < swing_highs[i - 1][1]
                )
                return lh_count >= 1
        else:  # LONG
            # Find swing lows in correction
            swing_lows = []
            for i in range(data_start, min(correction_start + 5, len(data))):
                if lows[i] == min(lows[max(0, i - 2) : min(len(lows), i + 3)]):
                    swing_lows.append((i, lows[i]))

            if len(swing_lows) >= 2:
                # Check for higher lows (demand coming in)
                hl_count = sum(
                    1
                    for i in range(1, len(swing_lows))
                    if swing_lows[i][1] > swing_lows[i - 1][1]
                )
                return hl_count >= 1

        return True  # Default to pass if can't determine

    def run_backtest(self):
        """Run corrected ICC backtest"""
        print("=" * 70)
        print("  ICC CORRECTED BACKTEST")
        print("  Entry on CONTINUATION BREAK (not during correction)")
        print("=" * 70)

        all_setups = []

        for pair in self.pairs:
            print(f"\n{'=' * 60}")
            print(f"  {pair}")
            print(f"{'=' * 60}")

            try:
                # Load data
                df_4h = yf.Ticker(pair).history(period="2y", interval="4h")
                df_1h = yf.Ticker(pair).history(period="730d", interval="1h")
                df_15m = yf.Ticker(pair).history(period="90d", interval="15m")

                if len(df_15m) < 1000:
                    print("  Not enough 15M data, skipping...")
                    continue

                # Extract data
                highs_4h = df_4h["High"].values
                lows_4h = df_4h["Low"].values
                h4_timestamps = df_4h.index.tolist()

                highs_1h = df_1h["High"].values
                lows_1h = df_1h["Low"].values
                closes_1h = df_1h["Close"].values
                timestamps_1h = df_1h.index

                highs_15m = df_15m["High"].values
                lows_15m = df_15m["Low"].values
                closes_15m = df_15m["Close"].values
                h15_timestamps = df_15m.index.tolist()

                # Find 1H swings
                swings_low_1h = self.get_swings(lows_1h, False)
                swings_high_1h = self.get_swings(highs_1h, True)

                setups = []
                debug_info = {
                    "total_indication": 0,
                    "correction_waited": 0,
                    "continuation_found": 0,
                    "entered": 0,
                }

                # ============================================
                # SHORTS - Swing lows breaking = potential shorts
                # ============================================
                for idx, level in swings_low_1h[10:-20]:
                    ts_1h = timestamps_1h[idx]
                    debug_info["total_indication"] += 1

                    # Find 4H index
                    idx_4h = None
                    for j, ts in enumerate(h4_timestamps):
                        if abs((ts - ts_1h).total_seconds()) < 3600 * 3:
                            idx_4h = j
                            break
                    if idx_4h is None or idx_4h < 5:
                        continue

                    # Check 4H trend (trade with trend for shorts = downtrend)
                    trend = self.get_trend_4h(highs_4h, lows_4h, idx_4h)
                    if trend != "DOWNTREND":
                        continue

                    # STEP 1: Check if swing low BREAKS (Indication)
                    break_idx = None
                    for j in range(idx, min(idx + 20, len(lows_1h))):
                        if lows_1h[j] < level:
                            break_idx = j
                            break
                    if break_idx is None:
                        continue

                    # STEP 2: Wait for CORRECTION back to level
                    correction_idx = None
                    for j in range(break_idx, min(break_idx + 50, len(closes_1h))):
                        if highs_1h[j] >= level:
                            correction_idx = j
                            break
                    if correction_idx is None:
                        continue

                    debug_info["correction_waited"] += 1

                    # STEP 3: Find SL on 4H (swing high above level)
                    sl = None
                    for j in range(idx_4h, max(0, idx_4h - 15), -1):
                        if highs_4h[j] > level:
                            sl = highs_4h[j]
                            break
                    if sl is None or sl - level < 0.0001:
                        continue

                    # STEP 4: Find TP on 4H (next swing low below)
                    tp = None
                    for j in range(idx_4h, min(idx_4h + 40, len(lows_4h))):
                        if lows_4h[j] < level * 0.998:
                            tp = lows_4h[j]
                            break
                    if tp is None:
                        continue

                    # Check RR
                    risk = sl - level
                    reward = level - tp
                    if risk <= 0 or reward <= 0:
                        continue
                    rr = reward / risk
                    if rr < 2.0:
                        continue

                    # STEP 5: Find CONTINUATION BREAK on 15M
                    # Look for price to break THROUGH level again after correction
                    continuation_found = False
                    entry_price = 0
                    entry_idx_15m = None

                    # Start looking from when correction started on 1H
                    correction_ts = timestamps_1h[correction_idx]

                    for j, ts in enumerate(h15_timestamps):
                        if ts < correction_ts:
                            continue
                        if ts > correction_ts + timedelta(hours=30):
                            break

                        # Continuation break: price closes/touches below level
                        if closes_15m[j] < level:
                            continuation_found = True
                            entry_price = level  # Enter at the break level
                            entry_idx_15m = j
                            break

                    if not continuation_found:
                        continue

                    debug_info["continuation_found"] += 1

                    # STEP 6: Check trade outcome on 15M
                    outcome = None
                    for j in range(
                        entry_idx_15m, min(entry_idx_15m + 300, len(closes_15m))
                    ):
                        # TP hit first = WIN
                        if lows_15m[j] <= tp:
                            outcome = "WIN"
                            break
                        # SL hit first = LOSS
                        if highs_15m[j] >= sl:
                            outcome = "LOSS"
                            break

                    if outcome:
                        setups.append({"rr": rr, "outcome": outcome})
                        debug_info["entered"] += 1

                # ============================================
                # LONGS - Swing highs breaking = potential longs
                # ============================================
                for idx, level in swings_high_1h[10:-20]:
                    ts_1h = timestamps_1h[idx]

                    # Find 4H index
                    idx_4h = None
                    for j, ts in enumerate(h4_timestamps):
                        if abs((ts - ts_1h).total_seconds()) < 3600 * 3:
                            idx_4h = j
                            break
                    if idx_4h is None or idx_4h < 5:
                        continue

                    # Check 4H trend (trade with trend for longs = uptrend)
                    trend = self.get_trend_4h(highs_4h, lows_4h, idx_4h)
                    if trend != "UPTREND":
                        continue

                    # STEP 1: Check if swing high BREAKS (Indication)
                    break_idx = None
                    for j in range(idx, min(idx + 20, len(highs_1h))):
                        if highs_1h[j] > level:
                            break_idx = j
                            break
                    if break_idx is None:
                        continue

                    # STEP 2: Wait for CORRECTION back to level
                    correction_idx = None
                    for j in range(break_idx, min(break_idx + 50, len(closes_1h))):
                        if lows_1h[j] <= level:
                            correction_idx = j
                            break
                    if correction_idx is None:
                        continue

                    # Find SL on 4H (swing low below level)
                    sl = None
                    for j in range(idx_4h, max(0, idx_4h - 15), -1):
                        if lows_4h[j] < level:
                            sl = lows_4h[j]
                            break
                    if sl is None or level - sl < 0.0001:
                        continue

                    # Find TP on 4H (next swing high above)
                    tp = None
                    for j in range(idx_4h, min(idx_4h + 40, len(highs_4h))):
                        if highs_4h[j] > level * 1.002:
                            tp = highs_4h[j]
                            break
                    if tp is None:
                        continue

                    # Check RR
                    risk = level - sl
                    reward = tp - level
                    if risk <= 0 or reward <= 0:
                        continue
                    rr = reward / risk
                    if rr < 2.0:
                        continue

                    # Find CONTINUATION BREAK on 15M
                    continuation_found = False
                    entry_price = 0
                    entry_idx_15m = None

                    correction_ts = timestamps_1h[correction_idx]

                    for j, ts in enumerate(h15_timestamps):
                        if ts < correction_ts:
                            continue
                        if ts > correction_ts + timedelta(hours=30):
                            break

                        # Continuation break: price closes above level
                        if closes_15m[j] > level:
                            continuation_found = True
                            entry_price = level  # Enter at the break level
                            entry_idx_15m = j
                            break

                    if not continuation_found:
                        continue

                    # Check trade outcome
                    outcome = None
                    for j in range(
                        entry_idx_15m, min(entry_idx_15m + 300, len(closes_15m))
                    ):
                        # TP hit first = WIN
                        if highs_15m[j] >= tp:
                            outcome = "WIN"
                            break
                        # SL hit first = LOSS
                        if lows_15m[j] <= sl:
                            outcome = "LOSS"
                            break

                    if outcome:
                        setups.append({"rr": rr, "outcome": outcome})

                # Results for this pair
                print(f"\n  Setup funnel:")
                print(f"    Indication (breaks): {debug_info['total_indication']}")
                print(f"    Correction waited: {debug_info['correction_waited']}")
                print(f"    Continuation found: {debug_info['continuation_found']}")
                print(f"    Entered: {len(setups)}")

                if setups:
                    wins = len([s for s in setups if s["outcome"] == "WIN"])
                    losses = len([s for s in setups if s["outcome"] == "LOSS"])
                    wr = wins / len(setups) * 100
                    avg_rr = sum(s["rr"] for s in setups) / len(setups)
                    ev = (wins / len(setups) * avg_rr) - (losses / len(setups) * 1)

                    print(f"\n  RESULTS:")
                    print(f"    Wins: {wins} | Losses: {losses}")
                    print(f"    Win Rate: {wr:.0f}%")
                    print(f"    Avg RR: {avg_rr:.2f}:1")
                    print(f"    EV: {ev:.2f}R")

                    all_setups.extend(setups)
                else:
                    print("  No valid setups")

            except Exception as e:
                print(f"  Error: {e}")
                import traceback

                traceback.print_exc()

        # ============================================
        # TOTAL RESULTS
        # ============================================
        print("\n" + "=" * 70)
        print("  TOTAL RESULTS - ICC CORRECTED")
        print("=" * 70)

        if all_setups:
            wins = len([s for s in all_setups if s["outcome"] == "WIN"])
            losses = len([s for s in all_setups if s["outcome"] == "LOSS"])
            total = len(all_setups)

            print(f"\n  Total setups: {total}")
            print(f"  Wins: {wins} | Losses: {losses}")
            print(f"\n  WIN RATE: {wins / total * 100:.1f}%")

            avg_rr = sum(s["rr"] for s in all_setups) / total
            print(f"  Average RR: {avg_rr:.2f}:1")

            ev = (wins / total * avg_rr) - (losses / total * 1)
            print(f"  EXPECTED VALUE: {ev:.2f}R per trade")

            # Breakdown by outcome
            wins_rr = [s["rr"] for s in all_setups if s["outcome"] == "WIN"]
            losses_rr = [s["rr"] for s in all_setups if s["outcome"] == "LOSS"]
            if wins_rr:
                print(f"  Avg Win RR: {sum(wins_rr) / len(wins_rr):.2f}:1")
            if losses_rr:
                print(f"  Avg Loss RR: {sum(losses_rr) / len(losses_rr):.2f}:1")
        else:
            print("  No setups found")


if __name__ == "__main__":
    ICCCorrected().run_backtest()
