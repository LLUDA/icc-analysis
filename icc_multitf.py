#!/usr/bin/env python3
"""
ICC BACKTEST - Multi-Timeframe
- 4H: Determine trend direction
- 1H: Find breaks and corrections
- 15M: Entry confirmation
- 4H levels: SL and TP
"""

import yfinance as yf
from datetime import timedelta


class MultiTFBacktest:
    """Multi-timeframe ICC backtest"""

    def __init__(self):
        self.pairs = ["GBPUSD=X"]

    def get_swings(self, highs, lows, lookback=5):
        """Find swing highs and lows"""
        swings_high = []
        swings_low = []

        for i in range(lookback, len(highs) - lookback):
            if highs[i] == max(highs[i - lookback : i + lookback + 1]):
                swings_high.append((i, highs[i]))
            if lows[i] == min(lows[i - lookback : i + lookback + 1]):
                swings_low.append((i, lows[i]))

        return swings_high, swings_low

    def get_trend_4h(self, df_4h):
        """Determine trend on 4H"""
        highs = df_4h["High"].values
        lows = df_4h["Low"].values

        swings_high, swings_low = self.get_swings(highs, lows)

        if len(swings_high) < 4 or len(swings_low) < 4:
            return "RANGE"

        # Check last 4 swing highs and lows
        recent_hh = [h for _, h in swings_high[-4:]]
        recent_ll = [l for _, l in swings_low[-4:]]

        # Higher highs + Higher lows = Uptrend
        if recent_hh[-1] > recent_hh[0] and recent_ll[-1] > recent_ll[0]:
            return "UPTREND"
        # Lower highs + Lower lows = Downtrend
        elif recent_hh[-1] < recent_hh[0] and recent_ll[-1] < recent_ll[0]:
            return "DOWNTREND"

        return "RANGE"

    def run_backtest(self):
        """Run backtest"""
        pair = self.pairs[0]

        print("=" * 70)
        print("  ICC MULTI-TIMEFRAME BACKTEST")
        print(f"  Pair: {pair}")
        print("  4H: Trend | 1H: Setup | 15M: Entry")
        print("  4H Levels: SL & TP")
        print("=" * 70)

        # Load all timeframes
        print("\n  Loading data...")
        df_4h = yf.Ticker(pair).history(period="2y", interval="4h")
        df_1h = yf.Ticker(pair).history(period="730d", interval="1h")
        df_15m = yf.Ticker(pair).history(period="60d", interval="15m")

        print(f"  4H: {len(df_4h)} candles")
        print(f"  1H: {len(df_1h)} candles")
        print(f"  15M: {len(df_15m)} candles")

        setups = []

        # Convert 4H timestamps to 1H index
        h4_timestamps = df_4h.index.tolist()

        # Find setups on 1H
        highs_1h = df_1h["High"].values
        lows_1h = df_1h["Low"].values
        closes_1h = df_1h["Close"].values
        timestamps_1h = df_1h.index

        swings_high_1h, swings_low_1h = self.get_swings(highs_1h, lows_1h)

        print(f"\n  1H Swings: {len(swings_high_1h)} highs, {len(swings_low_1h)} lows")

        # For each swing on 1H, check if it aligns with 4H trend
        for i in range(10, len(swings_low_1h) - 10):
            idx_1h, level = swings_low_1h[i]

            # Get corresponding 4H timestamp
            timestamp_1h = timestamps_1h[idx_1h]

            # Find 4H candle at this time
            idx_4h = None
            for j, ts in enumerate(h4_timestamps):
                if abs((ts - timestamp_1h).total_seconds()) < 3600 * 3:
                    idx_4h = j
                    break

            if idx_4h is None or idx_4h < 5:
                continue

            # Get 4H trend at this point
            df_4h_up_to_point = df_4h.iloc[: idx_4h + 1]
            trend = self.get_trend_4h(df_4h_up_to_point)

            # Only trade shorts in downtrend
            if trend != "DOWNTREND":
                continue

            # Check if 1H swing low was broken
            broke = False
            for j in range(idx_1h, min(idx_1h + 15, len(lows_1h))):
                if lows_1h[j] < level:
                    broke = True
                    break

            if not broke:
                continue

            # Find 4H SL (swing high above break level)
            highs_4h = df_4h["High"].values
            sl_4h = None
            for j in range(idx_4h, max(0, idx_4h - 10), -1):
                if highs_4h[j] > level:
                    sl_4h = highs_4h[j]
                    break

            if sl_4h is None:
                continue

            # Find 4H TP (next swing low below)
            lows_4h = df_4h["Low"].values
            tp_4h = None
            for j in range(idx_4h, min(idx_4h + 30, len(lows_4h))):
                if lows_4h[j] < level * 0.995:
                    tp_4h = lows_4h[j]
                    break

            if tp_4h is None:
                tp_4h = level * 0.97

            # Wait for correction on 1H (price returns to level)
            correction = False
            correction_idx = None
            for j in range(idx_1h, min(idx_1h + 30, len(closes_1h))):
                if highs_1h[j] >= level:
                    correction = True
                    correction_idx = j
                    break

            if not correction:
                continue

            # Now look for entry on 15M
            # Get 15M data around the correction
            correction_time = timestamps_1h[correction_idx]

            # Find 15M candles
            h15_timestamps = df_15m.index.tolist()

            h15_start_idx = None
            for j, ts in enumerate(h15_timestamps):
                if ts >= correction_time - timedelta(hours=2):
                    h15_start_idx = j
                    break

            if h15_start_idx is None:
                continue

            # Look for entry signal on 15M (break of correction low)
            highs_15m = df_15m["High"].values
            lows_15m = df_15m["Low"].values
            closes_15m = df_15m["Close"].values

            entry_found = False
            entry_price = 0
            entry_idx_15m = None

            for j in range(h15_start_idx, min(h15_start_idx + 60, len(closes_15m))):
                # Entry when price breaks below correction low
                if lows_15m[j] < level:
                    entry_found = True
                    entry_price = closes_15m[j]
                    entry_idx_15m = j
                    break

            if not entry_found:
                continue

            # Calculate RR using 4H levels
            risk = sl_4h - entry_price
            reward = entry_price - tp_4h

            if risk <= 0 or reward <= 0:
                continue

            rr = reward / risk

            # Require minimum 2:1
            if rr < 2.0:
                continue

            # Simulate trade on 15M
            for j in range(entry_idx_15m, min(entry_idx_15m + 100, len(closes_15m))):
                if lows_15m[j] <= tp_4h:
                    setups.append({"trend": trend, "rr": rr, "outcome": "WIN"})
                    break
                if highs_15m[j] >= sl_4h:
                    setups.append({"trend": trend, "rr": rr, "outcome": "LOSS"})
                    break

        # LONGS
        for i in range(10, len(swings_high_1h) - 10):
            idx_1h, level = swings_high_1h[i]

            timestamp_1h = timestamps_1h[idx_1h]

            idx_4h = None
            for j, ts in enumerate(h4_timestamps):
                if abs((ts - timestamp_1h).total_seconds()) < 3600 * 3:
                    idx_4h = j
                    break

            if idx_4h is None or idx_4h < 5:
                continue

            df_4h_up_to_point = df_4h.iloc[: idx_4h + 1]
            trend = self.get_trend_4h(df_4h_up_to_point)

            if trend != "UPTREND":
                continue

            # Check if broken
            broke = False
            for j in range(idx_1h, min(idx_1h + 15, len(highs_1h))):
                if highs_1h[j] > level:
                    broke = True
                    break

            if not broke:
                continue

            # SL on 4H
            lows_4h = df_4h["Low"].values
            sl_4h = None
            for j in range(idx_4h, max(0, idx_4h - 10), -1):
                if lows_4h[j] < level:
                    sl_4h = lows_4h[j]
                    break

            if sl_4h is None:
                continue

            # TP on 4H
            highs_4h = df_4h["High"].values
            tp_4h = None
            for j in range(idx_4h, min(idx_4h + 30, len(highs_4h))):
                if highs_4h[j] > level * 1.005:
                    tp_4h = highs_4h[j]
                    break

            if tp_4h is None:
                tp_4h = level * 1.03

            # Wait for correction
            correction = False
            correction_idx = None
            for j in range(idx_1h, min(idx_1h + 30, len(closes_1h))):
                if lows_1h[j] <= level:
                    correction = True
                    correction_idx = j
                    break

            if not correction:
                continue

            # Entry on 15M
            correction_time = timestamps_1h[correction_idx]
            h15_timestamps = df_15m.index.tolist()

            h15_start_idx = None
            for j, ts in enumerate(h15_timestamps):
                if ts >= correction_time - timedelta(hours=2):
                    h15_start_idx = j
                    break

            if h15_start_idx is None:
                continue

            highs_15m = df_15m["High"].values
            lows_15m = df_15m["Low"].values
            closes_15m = df_15m["Close"].values

            entry_found = False
            entry_price = 0
            entry_idx_15m = None

            for j in range(h15_start_idx, min(h15_start_idx + 60, len(closes_15m))):
                if highs_15m[j] > level:
                    entry_found = True
                    entry_price = closes_15m[j]
                    entry_idx_15m = j
                    break

            if not entry_found:
                continue

            risk = entry_price - sl_4h
            reward = tp_4h - entry_price

            if risk <= 0 or reward <= 0:
                continue

            rr = reward / risk

            if rr < 2.0:
                continue

            for j in range(entry_idx_15m, min(entry_idx_15m + 100, len(closes_15m))):
                if highs_15m[j] >= tp_4h:
                    setups.append({"trend": trend, "rr": rr, "outcome": "WIN"})
                    break
                if lows_15m[j] <= sl_4h:
                    setups.append({"trend": trend, "rr": rr, "outcome": "LOSS"})
                    break

        # ============================================
        # Results
        # ============================================
        print("\n" + "=" * 70)
        print("  RESULTS")
        print("=" * 70)

        if not setups:
            print("\n  No valid setups found!")
            return

        total = len(setups)
        wins = len([s for s in setups if s["outcome"] == "WIN"])
        losses = len([s for s in setups if s["outcome"] == "LOSS"])

        print(f"\n  Total setups: {total}")
        print(f"  Wins: {wins}")
        print(f"  Losses: {losses}")
        print(f"\n  WIN RATE: {wins / total * 100:.1f}%")

        if wins:
            avg_rr = sum(s["rr"] for s in setups) / total
            print(f"  Average RR: {avg_rr:.2f}:1")

            ev = (wins / total * avg_rr) - (losses / total * 1)
            print(f"  EXPECTED VALUE: {ev:.2f}R per trade")


if __name__ == "__main__":
    MultiTFBacktest().run_backtest()
