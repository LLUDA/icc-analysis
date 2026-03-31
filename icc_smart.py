#!/usr/bin/env python3
"""
ICC SMART SELECTIVE - Apply Different Filters Per Pair
=====================================================
Key insight: Some pairs work with looser filters (EURUSD, AUDUSD)
Some pairs need strict filters (others)
"""

import yfinance as yf
from datetime import datetime, timedelta


class ICCSmartSelective:
    """Smart selective ICC - different filters per pair"""

    def __init__(self):
        self.pairs = [
            "GBPJPY=X",
            "EURUSD=X",
            "GBPUSD=X",
            "USDJPY=X",
            "GBPCAD=X",
            "EURJPY=X",
            "AUDUSD=X",
            "USDCAD=X",
            "NZDUSD=X",
            "EURGBP=X",
        ]

        # PAIR-SPECIFIC FILTERS (based on analysis)
        # Format: (trend_filter, max_correction, min_rr)
        # trend_filter: "4H", "1H", "EITHER"
        # Strategy: Use looser filters for good pairs, stricter for bad pairs
        self.filters = {
            "GBPJPY=X": ("4H", 0.70, 2.0),  # Strict - only 4H trend
            "EURUSD=X": ("EITHER", 0.80, 1.5),  # LOOSE - best performer
            "GBPUSD=X": ("EITHER", 0.80, 1.5),  # LOOSE - good performer
            "USDJPY=X": ("EITHER", 0.70, 2.0),  # Moderate
            "GBPCAD=X": ("4H", 0.60, 2.0),  # Very strict - avoid
            "EURJPY=X": ("4H", 0.70, 2.0),  # Strict
            "AUDUSD=X": ("EITHER", 0.80, 1.5),  # LOOSE - great performer
            "USDCAD=X": ("4H", 0.60, 2.0),  # Very strict - avoid
            "NZDUSD=X": ("4H", 0.50, 2.0),  # Very strict - avoid
            "EURGBP=X": ("4H", 0.60, 2.0),  # Very strict - avoid
        }

        self.names = {
            "GBPJPY=X": "GBPJPY",
            "EURUSD=X": "EURUSD",
            "GBPUSD=X": "GBPUSD",
            "USDJPY=X": "USDJPY",
            "GBPCAD=X": "GBPCAD",
            "EURJPY=X": "EURJPY",
            "AUDUSD=X": "AUDUSD",
            "USDCAD=X": "USDCAD",
            "NZDUSD=X": "NZDUSD",
            "EURGBP=X": "EURGBP",
        }

    def get_swings(self, data, is_high=True, lookback=5):
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
        if idx < 12:
            return "RANGE"
        recent_h = [h for i, h in self.get_swings(highs[:idx], True)][-5:]
        recent_l = [l for i, l in self.get_swings(lows[:idx], False)][-5:]
        if len(recent_h) < 4 or len(recent_l) < 4:
            return "RANGE"
        if recent_h[-1] > recent_h[0] and recent_l[-1] > recent_l[0]:
            return "UPTREND"
        elif recent_h[-1] < recent_h[0] and recent_l[-1] < recent_l[0]:
            return "DOWNTREND"
        return "RANGE"

    def get_trend_1h(self, highs, lows, idx):
        if idx < 8:
            return "RANGE"
        recent_h = [h for i, h in self.get_swings(highs[:idx], True)][-3:]
        recent_l = [l for i, l in self.get_swings(lows[:idx], False)][-3:]
        if len(recent_h) < 2 or len(recent_l) < 2:
            return "RANGE"
        if recent_h[-1] > recent_h[0] and recent_l[-1] > recent_l[0]:
            return "UPTREND"
        elif recent_h[-1] < recent_h[0] and recent_l[-1] < recent_l[0]:
            return "DOWNTREND"
        return "RANGE"

    def check_trend_filter(self, trend_4h, trend_1h, direction, filter_type):
        """Check if trend passes filter"""
        if direction == "SHORT":
            required_trend = "DOWNTREND"
        else:
            required_trend = "UPTREND"

        if filter_type == "4H":
            return trend_4h == required_trend
        elif filter_type == "1H":
            return trend_1h == required_trend
        elif filter_type == "EITHER":
            return trend_4h == required_trend or trend_1h == required_trend
        return False

    def run_backtest(self):
        current_time = datetime.now()

        print("=" * 70)
        print("  ICC SMART SELECTIVE - Pair-Specific Filters")
        print("  Good pairs (EURUSD, AUDUSD, GBPUSD): Looser filters")
        print("  Bad pairs (GBPCAD, NZDUSD, etc): Strict filters")
        print("=" * 70)

        all_setups = []

        for pair in self.pairs:
            name = self.names.get(pair, pair)
            trend_filter, max_corr, min_rr = self.filters.get(pair, ("4H", 0.70, 2.0))

            print(f"\n{'=' * 50}")
            print(f"  {name} ({trend_filter}, ≤{max_corr * 100:.0f}%, RR≥{min_rr})")
            print(f"{'=' * 50}")

            try:
                end_date = current_time.strftime("%Y-%m-%d")
                start_date = (current_time - timedelta(days=180)).strftime("%Y-%m-%d")

                df_4h = yf.Ticker(pair).history(
                    start=start_date, end=end_date, interval="4h"
                )
                df_1h = yf.Ticker(pair).history(
                    start=start_date, end=end_date, interval="1h"
                )

                if len(df_4h) < 200 or len(df_1h) < 500:
                    print(f"  Not enough data")
                    continue

                highs_4h = df_4h["High"].values
                lows_4h = df_4h["Low"].values
                h4_timestamps = df_4h.index.tolist()

                highs_1h = df_1h["High"].values
                lows_1h = df_1h["Low"].values
                closes_1h = df_1h["Close"].values
                timestamps_1h = df_1h.index.tolist()

                print(
                    f"  Data: {df_1h.index[0].strftime('%b %d')} to {df_1h.index[-1].strftime('%b %d')}"
                )

                swings_low_1h = self.get_swings(lows_1h, False)
                swings_high_1h = self.get_swings(highs_1h, True)

                setups = []

                # SHORTS
                for idx, level in swings_low_1h:
                    if idx < 10 or idx > len(closes_1h) - 30:
                        continue

                    ts_1h = timestamps_1h[idx]

                    idx_4h = None
                    for j, ts in enumerate(h4_timestamps):
                        if abs((ts - ts_1h).total_seconds()) < 3600 * 3:
                            idx_4h = j
                            break
                    if idx_4h is None or idx_4h < 8:
                        continue

                    trend_4h = self.get_trend_4h(highs_4h, lows_4h, idx_4h)
                    trend_1h = self.get_trend_1h(highs_1h, lows_1h, idx)

                    # Trend filter
                    if not self.check_trend_filter(
                        trend_4h, trend_1h, "SHORT", trend_filter
                    ):
                        continue

                    # Break
                    break_idx = None
                    for j in range(idx, min(idx + 15, len(lows_1h))):
                        if lows_1h[j] < level:
                            break_idx = j
                            break
                    if break_idx is None:
                        continue

                    move_size = level - lows_1h[break_idx]
                    if move_size <= 0:
                        continue

                    # Correction
                    correction_idx = None
                    for j in range(break_idx, min(break_idx + 50, len(closes_1h))):
                        if highs_1h[j] >= level:
                            correction_idx = j
                            break
                    if correction_idx is None:
                        continue

                    correction_depth = highs_1h[correction_idx] - level
                    correction_pct = correction_depth / move_size

                    if correction_pct > max_corr:
                        continue

                    # SL/TP
                    sl = None
                    for j in range(idx_4h, max(0, idx_4h - 15), -1):
                        if highs_4h[j] > level:
                            sl = highs_4h[j]
                            break
                    if sl is None:
                        continue

                    tp = None
                    for j in range(idx_4h, min(idx_4h + 40, len(lows_4h))):
                        if lows_4h[j] < level * 0.998:
                            tp = lows_4h[j]
                            break
                    if tp is None:
                        continue

                    risk = sl - level
                    reward = level - tp
                    if risk <= 0 or reward <= 0:
                        continue
                    rr = reward / risk

                    if rr < min_rr:
                        continue

                    # Continuation
                    continuation_found = False
                    entry_idx = None
                    for j in range(
                        correction_idx, min(correction_idx + 35, len(closes_1h))
                    ):
                        if closes_1h[j] < level:
                            continuation_found = True
                            entry_idx = j
                            break
                    if not continuation_found:
                        continue

                    # Outcome
                    outcome = None
                    for j in range(entry_idx, min(entry_idx + 100, len(closes_1h))):
                        if lows_1h[j] <= tp:
                            outcome = "WIN"
                            break
                        if highs_1h[j] >= sl:
                            outcome = "LOSS"
                            break

                    if outcome:
                        entry_time = timestamps_1h[entry_idx]
                        setups.append(
                            {
                                "direction": "SHORT",
                                "rr": rr,
                                "correction_pct": correction_pct * 100,
                                "outcome": outcome,
                                "entry_time": entry_time.strftime("%b %d %H:%M"),
                            }
                        )

                # LONGS
                for idx, level in swings_high_1h:
                    if idx < 10 or idx > len(closes_1h) - 30:
                        continue

                    ts_1h = timestamps_1h[idx]

                    idx_4h = None
                    for j, ts in enumerate(h4_timestamps):
                        if abs((ts - ts_1h).total_seconds()) < 3600 * 3:
                            idx_4h = j
                            break
                    if idx_4h is None or idx_4h < 8:
                        continue

                    trend_4h = self.get_trend_4h(highs_4h, lows_4h, idx_4h)
                    trend_1h = self.get_trend_1h(highs_1h, lows_1h, idx)

                    if not self.check_trend_filter(
                        trend_4h, trend_1h, "LONG", trend_filter
                    ):
                        continue

                    break_idx = None
                    for j in range(idx, min(idx + 15, len(highs_1h))):
                        if highs_1h[j] > level:
                            break_idx = j
                            break
                    if break_idx is None:
                        continue

                    move_size = highs_1h[break_idx] - level
                    if move_size <= 0:
                        continue

                    correction_idx = None
                    for j in range(break_idx, min(break_idx + 50, len(closes_1h))):
                        if lows_1h[j] <= level:
                            correction_idx = j
                            break
                    if correction_idx is None:
                        continue

                    correction_depth = level - lows_1h[correction_idx]
                    correction_pct = correction_depth / move_size

                    if correction_pct > max_corr:
                        continue

                    sl = None
                    for j in range(idx_4h, max(0, idx_4h - 15), -1):
                        if lows_4h[j] < level:
                            sl = lows_4h[j]
                            break
                    if sl is None:
                        continue

                    tp = None
                    for j in range(idx_4h, min(idx_4h + 40, len(highs_4h))):
                        if highs_4h[j] > level * 1.002:
                            tp = highs_4h[j]
                            break
                    if tp is None:
                        continue

                    risk = level - sl
                    reward = tp - level
                    if risk <= 0 or reward <= 0:
                        continue
                    rr = reward / risk

                    if rr < min_rr:
                        continue

                    continuation_found = False
                    entry_idx = None
                    for j in range(
                        correction_idx, min(correction_idx + 35, len(closes_1h))
                    ):
                        if closes_1h[j] > level:
                            continuation_found = True
                            entry_idx = j
                            break
                    if not continuation_found:
                        continue

                    outcome = None
                    for j in range(entry_idx, min(entry_idx + 100, len(closes_1h))):
                        if highs_1h[j] >= tp:
                            outcome = "WIN"
                            break
                        if lows_1h[j] <= sl:
                            outcome = "LOSS"
                            break

                    if outcome:
                        entry_time = timestamps_1h[entry_idx]
                        setups.append(
                            {
                                "direction": "LONG",
                                "rr": rr,
                                "correction_pct": correction_pct * 100,
                                "outcome": outcome,
                                "entry_time": entry_time.strftime("%b %d %H:%M"),
                            }
                        )

                if setups:
                    wins = len([s for s in setups if s["outcome"] == "WIN"])
                    losses = len([s for s in setups if s["outcome"] == "LOSS"])
                    wr = wins / len(setups) * 100
                    avg_rr = sum(s["rr"] for s in setups) / len(setups)

                    print(f"\n  Setups: {len(setups)}")
                    print(f"  Wins: {wins} | Losses: {losses}")
                    print(f"  WR: {wr:.0f}% | RR: {avg_rr:.2f}:1")

                    all_setups.extend(setups)
                else:
                    print("  No setups")

            except Exception as e:
                print(f"  Error: {e}")

        # TOTAL
        print("\n" + "=" * 70)
        print("  SMART SELECTIVE RESULTS")
        print("=" * 70)

        if all_setups:
            wins = len([s for s in all_setups if s["outcome"] == "WIN"])
            losses = len([s for s in all_setups if s["outcome"] == "LOSS"])
            total = len(all_setups)

            print(f"\n  Total setups: {total}")
            print(f"  Wins: {wins} 🟢 | Losses: {losses} 🔴")
            print(f"\n  ★ WIN RATE: {wins / total * 100:.0f}%")
            avg_rr = sum(s["rr"] for s in all_setups) / total
            print(f"  Average RR: {avg_rr:.2f}:1")
            ev = (wins / total * avg_rr) - (losses / total)
            print(f"  EV: {ev:.2f}R per trade")


if __name__ == "__main__":
    ICCSmartSelective().run_backtest()
