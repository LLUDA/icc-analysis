#!/usr/bin/env python3
"""
ICC METHOD - Pure Timeframe Analysis
=====================================
Uses 4H for trend/SL/TP and 1H for structure/entry
Avoids 15M data limitation (only 60 days available)
"""

import yfinance as yf
from datetime import timedelta


class ICCPureTimeframe:
    """ICC Method using 4H and 1H only"""

    def __init__(self):
        self.pairs = [
            "GBPUSD=X",
            "EURUSD=X",
            "GBPJPY=X",
            "EURJPY=X",
            "USDJPY=X",
            "USDCAD=X",
        ]

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

        if recent_h[-1] > recent_h[0] and recent_l[-1] > recent_l[0]:
            return "UPTREND"
        elif recent_h[-1] < recent_h[0] and recent_l[-1] < recent_l[0]:
            return "DOWNTREND"
        return "RANGE"

    def run_backtest(self):
        """Run backtest using 4H + 1H only"""
        print("=" * 70)
        print("  ICC PURE TIMEFRAME BACKTEST")
        print("  4H: Trend + SL/TP | 1H: Structure + Entry")
        print("=" * 70)

        all_setups = []

        for pair in self.pairs:
            print(f"\n{'=' * 60}")
            print(f"  {pair}")
            print(f"{'=' * 60}")

            try:
                # Load data - 4H and 1H have longer history
                df_4h = yf.Ticker(pair).history(period="2y", interval="4h")
                df_1h = yf.Ticker(pair).history(period="2y", interval="1h")

                if len(df_4h) < 500 or len(df_1h) < 1000:
                    print("  Not enough data")
                    continue

                print(f"  4H bars: {len(df_4h)}, 1H bars: {len(df_1h)}")

                # Extract data
                highs_4h = df_4h["High"].values
                lows_4h = df_4h["Low"].values
                closes_4h = df_4h["Close"].values
                h4_timestamps = df_4h.index.tolist()

                highs_1h = df_1h["High"].values
                lows_1h = df_1h["Low"].values
                closes_1h = df_1h["Close"].values
                timestamps_1h = df_1h.index.tolist()

                # Find 1H swings
                swings_low_1h = self.get_swings(lows_1h, False)
                swings_high_1h = self.get_swings(highs_1h, True)

                setups = []
                debug = {"indication": 0, "broke": 0, "corrected": 0, "continuation": 0}

                # ============================================
                # SHORTS
                # ============================================
                for idx, level in swings_low_1h[10:-30]:
                    ts_1h = timestamps_1h[idx]
                    debug["indication"] += 1

                    # Find 4H index
                    idx_4h = None
                    for j, ts in enumerate(h4_timestamps):
                        if abs((ts - ts_1h).total_seconds()) < 3600 * 3:
                            idx_4h = j
                            break
                    if idx_4h is None or idx_4h < 5:
                        continue

                    # Check 4H trend
                    trend = self.get_trend_4h(highs_4h, lows_4h, idx_4h)
                    if trend != "DOWNTREND":
                        continue

                    # STEP 1: Swing low breaks (Indication)
                    break_idx = None
                    for j in range(idx, min(idx + 25, len(lows_1h))):
                        if lows_1h[j] < level:
                            break_idx = j
                            break
                    if break_idx is None:
                        continue
                    debug["broke"] += 1

                    # STEP 2: Wait for CORRECTION back to level
                    correction_idx = None
                    for j in range(break_idx, min(break_idx + 60, len(closes_1h))):
                        if highs_1h[j] >= level:
                            correction_idx = j
                            break
                    if correction_idx is None:
                        continue
                    debug["corrected"] += 1

                    # STEP 3: Find SL (swing high on 4H)
                    sl = None
                    for j in range(idx_4h, max(0, idx_4h - 20), -1):
                        if highs_4h[j] > level:
                            sl = highs_4h[j]
                            break
                    if sl is None:
                        continue

                    # STEP 4: Find TP (swing low on 4H below)
                    tp = None
                    for j in range(idx_4h, min(idx_4h + 50, len(lows_4h))):
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

                    # STEP 5: Wait for CONTINUATION BREAK on 1H
                    continuation_found = False
                    entry_idx = None

                    # Look for close below level after correction
                    for j in range(
                        correction_idx, min(correction_idx + 40, len(closes_1h))
                    ):
                        if closes_1h[j] < level:
                            continuation_found = True
                            entry_idx = j
                            break

                    if not continuation_found:
                        continue
                    debug["continuation"] += 1

                    # STEP 6: Check outcome on 1H
                    outcome = None
                    for j in range(entry_idx, min(entry_idx + 100, len(closes_1h))):
                        if lows_1h[j] <= tp:
                            outcome = "WIN"
                            break
                        if highs_1h[j] >= sl:
                            outcome = "LOSS"
                            break

                    if outcome:
                        setups.append({"rr": rr, "outcome": outcome})

                # ============================================
                # LONGS
                # ============================================
                for idx, level in swings_high_1h[10:-30]:
                    ts_1h = timestamps_1h[idx]

                    # Find 4H index
                    idx_4h = None
                    for j, ts in enumerate(h4_timestamps):
                        if abs((ts - ts_1h).total_seconds()) < 3600 * 3:
                            idx_4h = j
                            break
                    if idx_4h is None or idx_4h < 5:
                        continue

                    # Check 4H trend
                    trend = self.get_trend_4h(highs_4h, lows_4h, idx_4h)
                    if trend != "UPTREND":
                        continue

                    # Swing high breaks (Indication)
                    break_idx = None
                    for j in range(idx, min(idx + 25, len(highs_1h))):
                        if highs_1h[j] > level:
                            break_idx = j
                            break
                    if break_idx is None:
                        continue

                    # Wait for CORRECTION
                    correction_idx = None
                    for j in range(break_idx, min(break_idx + 60, len(closes_1h))):
                        if lows_1h[j] <= level:
                            correction_idx = j
                            break
                    if correction_idx is None:
                        continue

                    # Find SL
                    sl = None
                    for j in range(idx_4h, max(0, idx_4h - 20), -1):
                        if lows_4h[j] < level:
                            sl = lows_4h[j]
                            break
                    if sl is None:
                        continue

                    # Find TP
                    tp = None
                    for j in range(idx_4h, min(idx_4h + 50, len(highs_4h))):
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

                    # Wait for CONTINUATION BREAK on 1H
                    continuation_found = False
                    entry_idx = None

                    for j in range(
                        correction_idx, min(correction_idx + 40, len(closes_1h))
                    ):
                        if closes_1h[j] > level:
                            continuation_found = True
                            entry_idx = j
                            break

                    if not continuation_found:
                        continue

                    # Check outcome
                    outcome = None
                    for j in range(entry_idx, min(entry_idx + 100, len(closes_1h))):
                        if highs_1h[j] >= tp:
                            outcome = "WIN"
                            break
                        if lows_1h[j] <= sl:
                            outcome = "LOSS"
                            break

                    if outcome:
                        setups.append({"rr": rr, "outcome": outcome})

                # Results
                print(
                    f"\n  Funnel: indication={debug['indication']}, broke={debug['broke']}, "
                    f"corrected={debug['corrected']}, continuation={debug['continuation']}"
                )

                if setups:
                    wins = len([s for s in setups if s["outcome"] == "WIN"])
                    losses = len([s for s in setups if s["outcome"] == "LOSS"])
                    wr = wins / len(setups) * 100
                    avg_rr = sum(s["rr"] for s in setups) / len(setups)
                    ev = (wins / len(setups) * avg_rr) - (losses / len(setups) * 1)

                    print(f"\n  RESULTS:")
                    print(f"    Setups: {len(setups)}")
                    print(f"    Wins: {wins} | Losses: {losses}")
                    print(f"    Win Rate: {wr:.1f}%")
                    print(f"    Avg RR: {avg_rr:.2f}:1")
                    print(f"    EV: {ev:.2f}R")

                    all_setups.extend(setups)
                else:
                    print("  No valid setups")

            except Exception as e:
                print(f"  Error: {e}")
                import traceback

                traceback.print_exc()

        # TOTAL
        print("\n" + "=" * 70)
        print("  TOTAL RESULTS")
        print("=" * 70)

        if all_setups:
            wins = len([s for s in all_setups if s["outcome"] == "WIN"])
            losses = len([s for s in all_setups if s["outcome"] == "LOSS"])
            total = len(all_setups)

            print(f"\n  Total setups: {total}")
            print(f"  Wins: {wins} | Losses: {losses}")
            print(f"\n  WIN RATE: {wins / total * 100:.1f}%")
            print(f"  Average RR: {sum(s['rr'] for s in all_setups) / total:.2f}:1")
            ev = (wins / total * (sum(s["rr"] for s in all_setups) / total)) - (
                losses / total
            )
            print(f"  EXPECTED VALUE: {ev:.2f}R per trade")
        else:
            print("  No setups found")


if __name__ == "__main__":
    ICCPureTimeframe().run_backtest()
