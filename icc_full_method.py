#!/usr/bin/env python3
"""
ICC FULL METHOD - Everything Combined
- 4H: Trend + SL/TP levels
- 1H: Structure breaks + Clues (LH/HL patterns)
- 15M: Entry confirmation
"""

import yfinance as yf
from datetime import timedelta


class ICCFullMethod:
    """ICC Full Method with clues"""

    def __init__(self):
        self.pairs = ["GBPUSD=X", "EURUSD=X", "GBPJPY=X", "EURJPY=X"]

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
        """Get trend from last 4 swings on 4H"""
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

    def check_clues_1h(self, highs, lows, correction_start, direction):
        """
        Check for clues during correction on 1H
        SHORT: Want Lower Highs (LH) forming
        LONG: Want Higher Lows (HL) forming
        """
        lookback = 20
        data_start = max(0, correction_start - lookback)

        if direction == "SHORT":
            # Find swing highs in correction
            swing_highs = []
            for i in range(data_start, correction_start + 5):
                if highs[i] == max(highs[max(0, i - 3) : min(len(highs), i + 4)]):
                    swing_highs.append(highs[i])

            if len(swing_highs) >= 3:
                # Count lower highs
                lh_count = 0
                for i in range(1, len(swing_highs)):
                    if swing_highs[i] < swing_highs[i - 1]:
                        lh_count += 1
                return lh_count >= 2  # At least 2 lower highs = valid clue

        else:  # LONG
            # Find swing lows in correction
            swing_lows = []
            for i in range(data_start, correction_start + 5):
                if lows[i] == min(lows[max(0, i - 3) : min(len(lows), i + 4)]):
                    swing_lows.append(lows[i])

            if len(swing_lows) >= 3:
                # Count higher lows
                hl_count = 0
                for i in range(1, len(swing_lows)):
                    if swing_lows[i] > swing_lows[i - 1]:
                        hl_count += 1
                return hl_count >= 2  # At least 2 higher lows = valid clue

        return False

    def run_backtest(self):
        """Run backtest on all pairs"""
        print("=" * 70)
        print("  ICC FULL METHOD BACKTEST")
        print("  4H: Trend + SL/TP | 1H: Breaks + Clues | 15M: Entry")
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
                df_15m = yf.Ticker(pair).history(period="60d", interval="15m")

                if len(df_15m) < 500:
                    print("  Not enough 15M data")
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

                # ============================================
                # SHORTS
                # ============================================
                for idx, level in swings_low_1h[10:-20]:
                    ts_1h = timestamps_1h[idx]

                    # Find 4H index
                    idx_4h = None
                    for j, ts in enumerate(h4_timestamps):
                        if abs((ts - ts_1h).total_seconds()) < 3600 * 3:
                            idx_4h = j
                            break
                    if idx_4h is None or idx_4h < 5:
                        continue

                    # Check 4H trend (trade only with trend for short = downtrend)
                    trend = self.get_trend_4h(highs_4h, lows_4h, idx_4h)
                    if trend != "DOWNTREND":
                        continue

                    # Check if 1H swing low broke
                    broke = False
                    for j in range(idx, min(idx + 15, len(lows_1h))):
                        if lows_1h[j] < level:
                            broke = True
                            break
                    if not broke:
                        continue

                    # Find SL on 4H (swing high above)
                    sl = None
                    for j in range(idx_4h, max(0, idx_4h - 10), -1):
                        if highs_4h[j] > level:
                            sl = highs_4h[j]
                            break
                    if sl is None:
                        continue

                    # Find TP on 4H (swing low below)
                    tp = None
                    for j in range(idx_4h, min(idx_4h + 30, len(lows_4h))):
                        if lows_4h[j] < level * 0.995:
                            tp = lows_4h[j]
                            break
                    if tp is None:
                        continue

                    # Wait for correction back to level
                    correction_idx = None
                    for j in range(idx, min(idx + 30, len(closes_1h))):
                        if highs_1h[j] >= level:
                            correction_idx = j
                            break
                    if correction_idx is None:
                        continue

                    # CHECK CLUES on 1H during correction
                    has_clues = self.check_clues_1h(
                        highs_1h, lows_1h, correction_idx, "SHORT"
                    )
                    if not has_clues:
                        continue  # Skip if no lower highs forming

                    # Find entry on 15M
                    entry_found = False
                    entry_price = 0
                    entry_idx_15m = None

                    for j, ts in enumerate(h15_timestamps):
                        if ts >= ts_1h and ts <= ts_1h + timedelta(hours=20):
                            if lows_15m[j] < level:  # Break of correction
                                entry_found = True
                                entry_price = closes_15m[j]
                                entry_idx_15m = j
                                break

                    if not entry_found:
                        continue

                    # Check RR
                    risk = sl - entry_price
                    reward = entry_price - tp
                    if risk <= 0 or reward <= 0:
                        continue
                    rr = reward / risk
                    if rr < 2.0:
                        continue

                    # Check outcome on 15M
                    for j in range(
                        entry_idx_15m, min(entry_idx_15m + 200, len(closes_15m))
                    ):
                        if lows_15m[j] <= tp:
                            setups.append(
                                {"rr": rr, "outcome": "WIN", "has_clues": True}
                            )
                            break
                        if highs_15m[j] >= sl:
                            setups.append(
                                {"rr": rr, "outcome": "LOSS", "has_clues": True}
                            )
                            break

                # ============================================
                # LONGS
                # ============================================
                for idx, level in swings_high_1h[10:-20]:
                    ts_1h = timestamps_1h[idx]

                    idx_4h = None
                    for j, ts in enumerate(h4_timestamps):
                        if abs((ts - ts_1h).total_seconds()) < 3600 * 3:
                            idx_4h = j
                            break
                    if idx_4h is None or idx_4h < 5:
                        continue

                    trend = self.get_trend_4h(highs_4h, lows_4h, idx_4h)
                    if trend != "UPTREND":
                        continue

                    # Check if broke
                    broke = False
                    for j in range(idx, min(idx + 15, len(highs_1h))):
                        if highs_1h[j] > level:
                            broke = True
                            break
                    if not broke:
                        continue

                    # SL on 4H
                    sl = None
                    for j in range(idx_4h, max(0, idx_4h - 10), -1):
                        if lows_4h[j] < level:
                            sl = lows_4h[j]
                            break
                    if sl is None:
                        continue

                    # TP on 4H
                    tp = None
                    for j in range(idx_4h, min(idx_4h + 30, len(highs_4h))):
                        if highs_4h[j] > level * 1.005:
                            tp = highs_4h[j]
                            break
                    if tp is None:
                        continue

                    # Wait for correction
                    correction_idx = None
                    for j in range(idx, min(idx + 30, len(closes_1h))):
                        if lows_1h[j] <= level:
                            correction_idx = j
                            break
                    if correction_idx is None:
                        continue

                    # CHECK CLUES
                    has_clues = self.check_clues_1h(
                        highs_1h, lows_1h, correction_idx, "LONG"
                    )
                    if not has_clues:
                        continue

                    # Entry on 15M
                    entry_found = False
                    for j, ts in enumerate(h15_timestamps):
                        if ts >= ts_1h and ts <= ts_1h + timedelta(hours=20):
                            if highs_15m[j] > level:
                                entry_found = True
                                entry_price = closes_15m[j]
                                entry_idx_15m = j
                                break

                    if not entry_found:
                        continue

                    risk = entry_price - sl
                    reward = tp - entry_price
                    if risk <= 0 or reward <= 0:
                        continue
                    rr = reward / risk
                    if rr < 2.0:
                        continue

                    for j in range(
                        entry_idx_15m, min(entry_idx_15m + 200, len(closes_15m))
                    ):
                        if highs_15m[j] >= tp:
                            setups.append(
                                {"rr": rr, "outcome": "WIN", "has_clues": True}
                            )
                            break
                        if lows_15m[j] <= sl:
                            setups.append(
                                {"rr": rr, "outcome": "LOSS", "has_clues": True}
                            )
                            break

                # Results for this pair
                if setups:
                    wins = len([s for s in setups if s["outcome"] == "WIN"])
                    losses = len([s for s in setups if s["outcome"] == "LOSS"])
                    wr = wins / len(setups) * 100
                    avg_rr = sum(s["rr"] for s in setups) / len(setups)
                    ev = (wins / len(setups) * avg_rr) - (losses / len(setups) * 1)

                    print(f"\n  Setups (with clues): {len(setups)}")
                    print(f"  Wins: {wins} | Losses: {losses}")
                    print(f"  Win Rate: {wr:.0f}%")
                    print(f"  Avg RR: {avg_rr:.2f}:1")
                    print(f"  Expected Value: {ev:.2f}R")

                    all_setups.extend(setups)
                else:
                    print("  No valid setups with clues")

            except Exception as e:
                print(f"  Error: {e}")

        # ============================================
        # TOTAL RESULTS
        # ============================================
        print("\n" + "=" * 70)
        print("  TOTAL RESULTS - ICC WITH CLUES")
        print("=" * 70)

        if all_setups:
            wins = len([s for s in all_setups if s["outcome"] == "WIN"])
            losses = len([s for s in all_setups if s["outcome"] == "LOSS"])
            total = len(all_setups)

            print(f"\n  Total setups: {total}")
            print(f"  Wins: {wins}")
            print(f"  Losses: {losses}")
            print(f"\n  WIN RATE: {wins / total * 100:.1f}%")

            avg_rr = sum(s["rr"] for s in all_setups) / total
            print(f"  Average RR: {avg_rr:.2f}:1")

            ev = (wins / total * avg_rr) - (losses / total * 1)
            print(f"  EXPECTED VALUE: {ev:.2f}R per trade")


if __name__ == "__main__":
    ICCFullMethod().run_backtest()
