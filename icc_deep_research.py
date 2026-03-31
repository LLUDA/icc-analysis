#!/usr/bin/env python3
"""
ICC DEEP RESEARCH - Finding More Setups
==========================================
Analyzing various filters and patterns to find more setups
"""

import yfinance as yf
from datetime import datetime, timedelta


class ICCDeepResearch:
    """Deep research into finding more setups"""

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
        ]
        self.names = {
            "GBPJPY=X": "GBPJPY",
            "EURUSD=X": "EURUSD",
            "GBPUSD=X": "GBPUSD",
            "USDJPY=X": "USDJPY",
            "GBPCAD=X": "GBPCAD",
            "EURJPY=X": "EURJPY",
            "AUDUSD=X": "AUDUSD",
            "USDCAD=X": "USDCAD",
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
        """Original 4H trend with 5 swings"""
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

    def get_trend_loose(self, highs, lows, idx):
        """Looser 4H trend - only needs 3 swings"""
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

    def get_trend_1h(self, highs, lows, idx):
        """1H trend as alternative"""
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

    def check_momentum(self, closes, idx, direction):
        """Check if momentum is aligned"""
        if idx < 20:
            return False
        lookback = 20
        recent = closes[max(0, idx - lookback) : idx]
        if len(recent) < 10:
            return False
        # Simple momentum: recent closes mostly above/below average
        avg = sum(recent) / len(recent)
        if direction == "LONG":
            return (
                recent[-1] > avg
                and sum(1 for c in recent if c > avg) > len(recent) * 0.6
            )
        else:
            return (
                recent[-1] < avg
                and sum(1 for c in recent if c < avg) > len(recent) * 0.6
            )

    def check_volatility(self, highs, lows, idx, min_range_pct=0.5):
        """Check if market has enough volatility"""
        if idx < 20:
            return True
        lookback = 20
        ranges = [
            (highs[i] - lows[i]) / lows[i] for i in range(max(0, idx - lookback), idx)
        ]
        if not ranges:
            return True
        avg_range = sum(ranges) / len(ranges)
        # Require some volatility
        return avg_range > 0.0001  # At least 0.01% average range

    def run_analysis(self):
        """Run deep analysis with various filters"""
        current_time = datetime.now()

        print("=" * 70)
        print("  ICC DEEP RESEARCH - FINDING MORE SETUPS")
        print("=" * 70)

        all_trades = []

        for pair in self.pairs:
            name = self.names.get(pair, pair)
            print(f"\n{'=' * 50}")
            print(f"  {name}")
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

                swings_low_1h = self.get_swings(lows_1h, False)
                swings_high_1h = self.get_swings(highs_1h, True)

                for idx, level in swings_low_1h:
                    if idx < 10 or idx > len(closes_1h) - 40:
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
                    trend_loose = self.get_trend_loose(highs_4h, lows_4h, idx_4h)
                    trend_1h = self.get_trend_1h(highs_1h, lows_1h, idx)

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
                        all_trades.append(
                            {
                                "pair": name,
                                "direction": "SHORT",
                                "rr": rr,
                                "correction_pct": correction_pct,
                                "trend_4h": trend_4h,
                                "trend_loose": trend_loose,
                                "trend_1h": trend_1h,
                                "outcome": outcome,
                            }
                        )

                for idx, level in swings_high_1h:
                    if idx < 10 or idx > len(closes_1h) - 40:
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
                    trend_loose = self.get_trend_loose(highs_4h, lows_4h, idx_4h)
                    trend_1h = self.get_trend_1h(highs_1h, lows_1h, idx)

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
                        all_trades.append(
                            {
                                "pair": name,
                                "direction": "LONG",
                                "rr": rr,
                                "correction_pct": correction_pct,
                                "trend_4h": trend_4h,
                                "trend_loose": trend_loose,
                                "trend_1h": trend_1h,
                                "outcome": outcome,
                            }
                        )

                print(f"  Collected {len(all_trades)} trades so far...")

            except Exception as e:
                print(f"  Error: {e}")

        # ============================================
        # ANALYSIS
        # ============================================
        print("\n" + "=" * 70)
        print("  DEEP ANALYSIS RESULTS")
        print("=" * 70)

        if not all_trades:
            print("  No trades collected")
            return

        print(f"\n  Total trades: {len(all_trades)}")

        # Filter: Original (4H trend strict + ≤70% correction + 2:1 RR)
        original = [
            t
            for t in all_trades
            if t["trend_4h"] != "RANGE"
            and t["correction_pct"] <= 0.70
            and t["rr"] >= 2.0
        ]
        if original:
            wins = len([t for t in original if t["outcome"] == "WIN"])
            print(f"\n  ORIGINAL FILTER (4H trend + ≤70% corr + 2:1 RR):")
            print(f"    Setups: {len(original)}, WR: {wins / len(original) * 100:.0f}%")

        # Test 1: Looser 4H trend (3 swings instead of 5)
        loose_trend = [
            t
            for t in all_trades
            if t["trend_loose"] != "RANGE"
            and t["correction_pct"] <= 0.70
            and t["rr"] >= 2.0
        ]
        if loose_trend:
            wins = len([t for t in loose_trend if t["outcome"] == "WIN"])
            print(f"\n  FILTER 1 - Looser 4H trend (3 swings):")
            print(
                f"    Setups: {len(loose_trend)}, WR: {wins / len(loose_trend) * 100:.0f}%"
            )
            print(f"    +{len(loose_trend) - len(original)} more setups")

        # Test 2: 1H trend aligned (instead of 4H)
        trend_1h = [
            t
            for t in all_trades
            if t["trend_1h"] != "RANGE"
            and t["correction_pct"] <= 0.70
            and t["rr"] >= 2.0
        ]
        if trend_1h:
            wins = len([t for t in trend_1h if t["outcome"] == "WIN"])
            print(f"\n  FILTER 2 - 1H trend only:")
            print(f"    Setups: {len(trend_1h)}, WR: {wins / len(trend_1h) * 100:.0f}%")
            print(f"    +{len(trend_1h) - len(original)} more setups")

        # Test 3: Either 4H OR 1H trend (union)
        either_trend = [
            t
            for t in all_trades
            if (t["trend_4h"] != "RANGE" or t["trend_1h"] != "RANGE")
            and t["correction_pct"] <= 0.70
            and t["rr"] >= 2.0
        ]
        if either_trend:
            wins = len([t for t in either_trend if t["outcome"] == "WIN"])
            print(f"\n  FILTER 3 - Either 4H OR 1H trend:")
            print(
                f"    Setups: {len(either_trend)}, WR: {wins / len(either_trend) * 100:.0f}%"
            )
            print(f"    +{len(either_trend) - len(original)} more setups")

        # Test 4: Correction ≤ 80% (looser)
        loose_corr = [
            t
            for t in all_trades
            if t["trend_4h"] != "RANGE"
            and t["correction_pct"] <= 0.80
            and t["rr"] >= 2.0
        ]
        if loose_corr:
            wins = len([t for t in loose_corr if t["outcome"] == "WIN"])
            print(f"\n  FILTER 4 - Correction ≤ 80%:")
            print(
                f"    Setups: {len(loose_corr)}, WR: {wins / len(loose_corr) * 100:.0f}%"
            )
            print(f"    +{len(loose_corr) - len(original)} more setups")

        # Test 5: Correction ≤ 60% (stricter)
        strict_corr = [
            t
            for t in all_trades
            if t["trend_4h"] != "RANGE"
            and t["correction_pct"] <= 0.60
            and t["rr"] >= 2.0
        ]
        if strict_corr:
            wins = len([t for t in strict_corr if t["outcome"] == "WIN"])
            print(f"\n  FILTER 5 - Correction ≤ 60% (stricter):")
            print(
                f"    Setups: {len(strict_corr)}, WR: {wins / len(strict_corr) * 100:.0f}%"
            )

        # Test 6: RR ≥ 1.5 (looser)
        loose_rr = [
            t
            for t in all_trades
            if t["trend_4h"] != "RANGE"
            and t["correction_pct"] <= 0.70
            and t["rr"] >= 1.5
        ]
        if loose_rr:
            wins = len([t for t in loose_rr if t["outcome"] == "WIN"])
            print(f"\n  FILTER 6 - RR ≥ 1.5 (looser):")
            print(f"    Setups: {len(loose_rr)}, WR: {wins / len(loose_rr) * 100:.0f}%")
            print(f"    +{len(loose_rr) - len(original)} more setups")

        # Test 7: Combined - Looser trend + Looser correction
        combined = [
            t
            for t in all_trades
            if (t["trend_4h"] != "RANGE" or t["trend_1h"] != "RANGE")
            and t["correction_pct"] <= 0.80
            and t["rr"] >= 2.0
        ]
        if combined:
            wins = len([t for t in combined if t["outcome"] == "WIN"])
            print(f"\n  FILTER 7 - Combined (Either trend + ≤80% corr):")
            print(f"    Setups: {len(combined)}, WR: {wins / len(combined) * 100:.0f}%")
            print(f"    +{len(combined) - len(original)} more setups")

        # Test 8: By pair - which pairs give most setups?
        print(f"\n  SETUPS BY PAIR (original filter):")
        for pair in set(t["pair"] for t in original):
            subset = [t for t in original if t["pair"] == pair]
            wins = len([t for t in subset if t["outcome"] == "WIN"])
            wr = wins / len(subset) * 100
            avg_rr = sum(t["rr"] for t in subset) / len(subset)
            print(f"    {pair}: {len(subset)} setups, {wr:.0f}% WR, {avg_rr:.2f}:1 RR")

        # Test 9: Direction bias
        longs = [t for t in original if t["direction"] == "LONG"]
        shorts = [t for t in original if t["direction"] == "SHORT"]
        if longs:
            wins = len([t for t in longs if t["outcome"] == "WIN"])
            print(f"\n  DIRECTION ANALYSIS:")
            print(f"    LONGS: {len(longs)} setups, {wins / len(longs) * 100:.0f}% WR")
        if shorts:
            wins = len([t for t in shorts if t["outcome"] == "WIN"])
            print(
                f"    SHORTS: {len(shorts)} setups, {wins / len(shorts) * 100:.0f}% WR"
            )

        # Test 10: Best combo that maintains 70%+ WR
        print(f"\n  OPTIMIZED FILTER COMBINATIONS:")

        # Combo A: Looser trend + Original correction
        combo_a = [
            t
            for t in all_trades
            if (t["trend_4h"] != "RANGE" or t["trend_1h"] != "RANGE")
            and t["correction_pct"] <= 0.70
            and t["rr"] >= 2.0
        ]
        if combo_a:
            wins = len([t for t in combo_a if t["outcome"] == "WIN"])
            wr = wins / len(combo_a) * 100
            status = "✓" if wr >= 70 else "✗"
            print(
                f"    A) Either trend + ≤70%: {len(combo_a)} setups, {wr:.0f}% WR {status}"
            )

        # Combo B: Strict 4H + Looser correction
        combo_b = [
            t
            for t in all_trades
            if t["trend_4h"] != "RANGE"
            and t["correction_pct"] <= 0.80
            and t["rr"] >= 2.0
        ]
        if combo_b:
            wins = len([t for t in combo_b if t["outcome"] == "WIN"])
            wr = wins / len(combo_b) * 100
            status = "✓" if wr >= 70 else "✗"
            print(
                f"    B) 4H trend + ≤80%: {len(combo_b)} setups, {wr:.0f}% WR {status}"
            )

        # Combo C: Both trends + ≤80% + RR ≥ 1.5
        combo_c = [
            t
            for t in all_trades
            if (t["trend_4h"] != "RANGE" and t["trend_1h"] != "RANGE")
            and t["correction_pct"] <= 0.80
            and t["rr"] >= 1.5
        ]
        if combo_c:
            wins = len([t for t in combo_c if t["outcome"] == "WIN"])
            wr = wins / len(combo_c) * 100
            status = "✓" if wr >= 70 else "✗"
            print(
                f"    C) Both trends + ≤80% + RR≥1.5: {len(combo_c)} setups, {wr:.0f}% WR {status}"
            )


if __name__ == "__main__":
    ICCDeepResearch().run_analysis()
