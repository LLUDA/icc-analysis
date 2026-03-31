#!/usr/bin/env python3
"""
ICC ANALYSIS - What Separates Wins from Losses
===============================================
Deep analysis to find patterns
"""

import yfinance as yf


class ICCAnalysis:
    """ICC Analysis to find winning patterns"""

    def __init__(self):
        self.pairs = [
            "GBPJPY=X",
            "EURUSD=X",
            "USDJPY=X",
            "GBPUSD=X",
            "EURJPY=X",
            "USDCAD=X",
        ]

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

    def get_trend(self, highs, lows, idx):
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

    def run_analysis(self):
        """Analyze setups by various factors"""
        print("=" * 70)
        print("  ICC DEEP ANALYSIS")
        print("=" * 70)

        all_trades = []

        for pair in self.pairs:
            try:
                df_4h = yf.Ticker(pair).history(period="2y", interval="4h")
                df_1h = yf.Ticker(pair).history(period="2y", interval="1h")

                if len(df_4h) < 500 or len(df_1h) < 1000:
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

                # SHORTS
                for idx, level in swings_low_1h[12:-30]:
                    ts_1h = timestamps_1h[idx]

                    idx_4h = None
                    for j, ts in enumerate(h4_timestamps):
                        if abs((ts - ts_1h).total_seconds()) < 3600 * 3:
                            idx_4h = j
                            break
                    if idx_4h is None or idx_4h < 8:
                        continue

                    trend = self.get_trend(highs_4h, lows_4h, idx_4h)
                    if trend != "DOWNTREND":
                        continue

                    # Break
                    break_idx = None
                    for j in range(idx, min(idx + 15, len(lows_1h))):
                        if lows_1h[j] < level:
                            break_idx = j
                            break
                    if break_idx is None:
                        continue

                    # Correction
                    correction_idx = None
                    for j in range(break_idx, min(break_idx + 50, len(closes_1h))):
                        if highs_1h[j] >= level:
                            correction_idx = j
                            break
                    if correction_idx is None:
                        continue

                    # Calculate correction depth (as % of move)
                    move_size = level - lows_1h[break_idx]
                    correction_depth = highs_1h[correction_idx] - level
                    if move_size > 0:
                        correction_pct = correction_depth / move_size
                    else:
                        correction_pct = 0

                    # SL/TP/RR
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
                    if rr < 2.0:
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
                        all_trades.append(
                            {
                                "pair": pair,
                                "direction": "SHORT",
                                "rr": rr,
                                "outcome": outcome,
                                "correction_pct": correction_pct,
                                "risk": risk,
                            }
                        )

                # LONGS
                for idx, level in swings_high_1h[12:-30]:
                    ts_1h = timestamps_1h[idx]

                    idx_4h = None
                    for j, ts in enumerate(h4_timestamps):
                        if abs((ts - ts_1h).total_seconds()) < 3600 * 3:
                            idx_4h = j
                            break
                    if idx_4h is None or idx_4h < 8:
                        continue

                    trend = self.get_trend(highs_4h, lows_4h, idx_4h)
                    if trend != "UPTREND":
                        continue

                    # Break
                    break_idx = None
                    for j in range(idx, min(idx + 15, len(highs_1h))):
                        if highs_1h[j] > level:
                            break_idx = j
                            break
                    if break_idx is None:
                        continue

                    # Correction
                    correction_idx = None
                    for j in range(break_idx, min(break_idx + 50, len(closes_1h))):
                        if lows_1h[j] <= level:
                            correction_idx = j
                            break
                    if correction_idx is None:
                        continue

                    # Correction depth
                    move_size = highs_1h[break_idx] - level
                    correction_depth = level - lows_1h[correction_idx]
                    if move_size > 0:
                        correction_pct = correction_depth / move_size
                    else:
                        correction_pct = 0

                    # SL/TP/RR
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
                    if rr < 2.0:
                        continue

                    # Continuation
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

                    # Outcome
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
                                "pair": pair,
                                "direction": "LONG",
                                "rr": rr,
                                "outcome": outcome,
                                "correction_pct": correction_pct,
                                "risk": risk,
                            }
                        )

            except Exception as e:
                print(f"Error: {e}")

        # ============================================
        # ANALYSIS
        # ============================================
        print(f"\nTotal trades: {len(all_trades)}")

        # 1. By Correction Depth
        print("\n" + "=" * 50)
        print("ANALYSIS 1: Win Rate by Correction Depth")
        print("=" * 50)

        for bucket in [
            ("0-30%", 0, 0.3),
            ("30-50%", 0.3, 0.5),
            ("50-70%", 0.5, 0.7),
            ("70-100%+", 0.7, 999),
        ]:
            subset = [
                t for t in all_trades if bucket[1] <= t["correction_pct"] < bucket[2]
            ]
            if len(subset) >= 5:
                wins = len([t for t in subset if t["outcome"] == "WIN"])
                wr = wins / len(subset) * 100
                print(f"  {bucket[0]}: {wr:.1f}% WR ({len(subset)} trades)")

        # 2. By RR
        print("\n" + "=" * 50)
        print("ANALYSIS 2: Win Rate by RR")
        print("=" * 50)

        for bucket in [
            ("2-3:1", 2, 3),
            ("3-4:1", 3, 4),
            ("4-5:1", 4, 5),
            ("5+:1", 5, 999),
        ]:
            subset = [t for t in all_trades if bucket[1] <= t["rr"] < bucket[2]]
            if len(subset) >= 5:
                wins = len([t for t in subset if t["outcome"] == "WIN"])
                wr = wins / len(subset) * 100
                print(f"  {bucket[0]}: {wr:.1f}% WR ({len(subset)} trades)")

        # 3. By Pair
        print("\n" + "=" * 50)
        print("ANALYSIS 3: Win Rate by Pair")
        print("=" * 50)

        for pair in set(t["pair"] for t in all_trades):
            subset = [t for t in all_trades if t["pair"] == pair]
            wins = len([t for t in subset if t["outcome"] == "WIN"])
            wr = wins / len(subset) * 100
            avg_rr = sum(t["rr"] for t in subset) / len(subset)
            print(f"  {pair}: {wr:.1f}% WR, {avg_rr:.2f}:1 RR ({len(subset)} trades)")

        # 4. By Direction
        print("\n" + "=" * 50)
        print("ANALYSIS 4: Win Rate by Direction")
        print("=" * 50)

        for direction in ["LONG", "SHORT"]:
            subset = [t for t in all_trades if t["direction"] == direction]
            if subset:
                wins = len([t for t in subset if t["outcome"] == "WIN"])
                wr = wins / len(subset) * 100
                print(f"  {direction}: {wr:.1f}% WR ({len(subset)} trades)")

        # 5. Best combinations
        print("\n" + "=" * 50)
        print("ANALYSIS 5: Best Combinations (Targeting 70%+ WR)")
        print("=" * 50)

        # Find filters that achieve 70%+
        for pair in set(t["pair"] for t in all_trades):
            for corr_bucket in [("shallow", 0, 0.5), ("deep", 0.5, 999)]:
                for rr_bucket in [("low", 2, 3.5), ("high", 3.5, 999)]:
                    subset = [
                        t
                        for t in all_trades
                        if t["pair"] == pair
                        and corr_bucket[1] <= t["correction_pct"] < corr_bucket[2]
                        and rr_bucket[1] <= t["rr"] < rr_bucket[2]
                    ]
                    if len(subset) >= 10:
                        wins = len([t for t in subset if t["outcome"] == "WIN"])
                        wr = wins / len(subset) * 100
                        if wr >= 60:
                            print(
                                f"  {pair} + {corr_bucket[0]} correction + {rr_bucket[0]} RR: {wr:.1f}% WR ({len(subset)} trades)"
                            )


if __name__ == "__main__":
    ICCAnalysis().run_analysis()
