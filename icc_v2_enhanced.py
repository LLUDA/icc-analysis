#!/usr/bin/env python3
"""
ICC METHOD V2 - Enhanced Filters
==================================
Added filters to push win rate to 70%+:
1. Stronger trend definition (requires clearer structure)
2. Only trade at significant structure levels
3. Wait for correction to fully complete
4. Require momentum confirmation
"""

import yfinance as yf


class ICCV2:
    """ICC with enhanced filters"""

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

    def get_trend_strength(self, highs, lows, idx):
        """
        Get trend with strength score
        Returns: (trend, strength_score)
        """
        if idx < 15:
            return "RANGE", 0

        # Get last 6 swings for stronger signal
        recent_h = [h for i, h in self.get_swings(highs[:idx], True)][-6:]
        recent_l = [l for i, l in self.get_swings(lows[:idx], False)][-6:]

        if len(recent_h) < 5 or len(recent_l) < 5:
            return "RANGE", 0

        # Calculate slope
        h_slope = recent_h[-1] - recent_h[0]
        l_slope = recent_l[-1] - recent_l[0]

        # UPTREND: HH+HL with positive slope
        if recent_h[-1] > recent_h[0] and recent_l[-1] > recent_l[0]:
            strength = (h_slope + l_slope) / 2
            return "UPTREND", strength
        # DOWNTREND: LH+LL with negative slope
        elif recent_h[-1] < recent_h[0] and recent_l[-1] < recent_l[0]:
            strength = -(h_slope + l_slope) / 2
            return "DOWNTREND", strength
        return "RANGE", 0

    def is_significant_level(self, level, recent_highs, recent_lows):
        """Check if level is significant (not noise)"""
        # Level should be away from recent extremes
        max_high = (
            max(recent_highs[-20:]) if len(recent_highs) >= 20 else max(recent_highs)
        )
        min_low = min(recent_lows[-20:]) if len(recent_lows) >= 20 else min(recent_lows)

        # Not too close to current price
        mid = (max_high + min_low) / 2
        range_size = max_high - min_low

        if range_size == 0:
            return False

        # Level should be in middle third of recent range
        distance_from_mid = abs(level - mid) / range_size
        return distance_from_mid < 0.4

    def run_backtest(self):
        """Run enhanced backtest"""
        print("=" * 70)
        print("  ICC V2 - ENHANCED FILTERS")
        print("  Stronger trend + Significant levels + Full correction")
        print("=" * 70)

        all_setups = []

        for pair in self.pairs:
            print(f"\n{'=' * 60}")
            print(f"  {pair}")
            print(f"{'=' * 60}")

            try:
                df_4h = yf.Ticker(pair).history(period="2y", interval="4h")
                df_1h = yf.Ticker(pair).history(period="2y", interval="1h")

                if len(df_4h) < 500 or len(df_1h) < 1000:
                    print("  Not enough data")
                    continue

                print(f"  4H bars: {len(df_4h)}, 1H bars: {len(df_1h)}")

                highs_4h = df_4h["High"].values
                lows_4h = df_4h["Low"].values
                h4_timestamps = df_4h.index.tolist()

                highs_1h = df_1h["High"].values
                lows_1h = df_1h["Low"].values
                closes_1h = df_1h["Close"].values
                timestamps_1h = df_1h.index.tolist()

                swings_low_1h = self.get_swings(lows_1h, False)
                swings_high_1h = self.get_swings(highs_1h, True)

                setups = []
                debug = {
                    "total": 0,
                    "trend_ok": 0,
                    "significant": 0,
                    "corrected": 0,
                    "continuation": 0,
                }

                # ============================================
                # SHORTS
                # ============================================
                for idx, level in swings_low_1h[15:-40]:
                    ts_1h = timestamps_1h[idx]
                    debug["total"] += 1

                    # Find 4H index
                    idx_4h = None
                    for j, ts in enumerate(h4_timestamps):
                        if abs((ts - ts_1h).total_seconds()) < 3600 * 3:
                            idx_4h = j
                            break
                    if idx_4h is None or idx_4h < 10:
                        continue

                    # Check trend strength (V2: stronger filter)
                    trend, strength = self.get_trend_strength(highs_4h, lows_4h, idx_4h)
                    if trend != "DOWNTREND":
                        continue
                    if strength > 0:  # Negative for downtrend
                        continue
                    debug["trend_ok"] += 1

                    # Check if level is significant (V2: filter noise)
                    if not self.is_significant_level(
                        level, highs_1h[:idx], lows_1h[:idx]
                    ):
                        continue
                    debug["significant"] += 1

                    # Swing low breaks (Indication)
                    break_idx = None
                    for j in range(idx, min(idx + 20, len(lows_1h))):
                        if lows_1h[j] < level:
                            break_idx = j
                            break
                    if break_idx is None:
                        continue

                    # Wait for FULL correction (V2: wait longer)
                    correction_idx = None
                    for j in range(break_idx, min(break_idx + 80, len(closes_1h))):
                        if highs_1h[j] >= level:
                            correction_idx = j
                            break
                    if correction_idx is None:
                        continue

                    # V2: Correction must have some depth
                    correction_depth = highs_1h[correction_idx] - lows_1h[break_idx]
                    if correction_depth < 0.0005:  # Minimum correction
                        continue
                    debug["corrected"] += 1

                    # Find SL (swing high on 4H)
                    sl = None
                    for j in range(idx_4h, max(0, idx_4h - 25), -1):
                        if highs_4h[j] > level:
                            sl = highs_4h[j]
                            break
                    if sl is None:
                        continue

                    # Find TP (swing low on 4H below)
                    tp = None
                    for j in range(idx_4h, min(idx_4h + 60, len(lows_4h))):
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

                    # Wait for CONTINUATION BREAK
                    continuation_found = False
                    entry_idx = None

                    for j in range(
                        correction_idx, min(correction_idx + 50, len(closes_1h))
                    ):
                        if closes_1h[j] < level:
                            continuation_found = True
                            entry_idx = j
                            break

                    if not continuation_found:
                        continue
                    debug["continuation"] += 1

                    # Check outcome
                    outcome = None
                    for j in range(entry_idx, min(entry_idx + 150, len(closes_1h))):
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
                for idx, level in swings_high_1h[15:-40]:
                    ts_1h = timestamps_1h[idx]

                    # Find 4H index
                    idx_4h = None
                    for j, ts in enumerate(h4_timestamps):
                        if abs((ts - ts_1h).total_seconds()) < 3600 * 3:
                            idx_4h = j
                            break
                    if idx_4h is None or idx_4h < 10:
                        continue

                    # Check trend strength
                    trend, strength = self.get_trend_strength(highs_4h, lows_4h, idx_4h)
                    if trend != "UPTREND":
                        continue
                    if strength < 0:  # Positive for uptrend
                        continue
                    debug["trend_ok"] += 1

                    # Check if level is significant
                    if not self.is_significant_level(
                        level, highs_1h[:idx], lows_1h[:idx]
                    ):
                        continue
                    debug["significant"] += 1

                    # Swing high breaks
                    break_idx = None
                    for j in range(idx, min(idx + 20, len(highs_1h))):
                        if highs_1h[j] > level:
                            break_idx = j
                            break
                    if break_idx is None:
                        continue

                    # Wait for FULL correction
                    correction_idx = None
                    for j in range(break_idx, min(break_idx + 80, len(closes_1h))):
                        if lows_1h[j] <= level:
                            correction_idx = j
                            break
                    if correction_idx is None:
                        continue

                    # Minimum correction depth
                    correction_depth = highs_1h[break_idx] - lows_1h[correction_idx]
                    if correction_depth < 0.0005:
                        continue
                    debug["corrected"] += 1

                    # Find SL
                    sl = None
                    for j in range(idx_4h, max(0, idx_4h - 25), -1):
                        if lows_4h[j] < level:
                            sl = lows_4h[j]
                            break
                    if sl is None:
                        continue

                    # Find TP
                    tp = None
                    for j in range(idx_4h, min(idx_4h + 60, len(highs_4h))):
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

                    # Wait for CONTINUATION BREAK
                    continuation_found = False
                    entry_idx = None

                    for j in range(
                        correction_idx, min(correction_idx + 50, len(closes_1h))
                    ):
                        if closes_1h[j] > level:
                            continuation_found = True
                            entry_idx = j
                            break

                    if not continuation_found:
                        continue
                    debug["continuation"] += 1

                    # Check outcome
                    outcome = None
                    for j in range(entry_idx, min(entry_idx + 150, len(closes_1h))):
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
                    f"\n  Funnel: total={debug['total']}, trend_ok={debug['trend_ok']}, "
                    f"significant={debug['significant']}, corrected={debug['corrected']}, "
                    f"continuation={debug['continuation']}"
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
        print("  TOTAL RESULTS - ICC V2")
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

            # Win rate distribution
            win_rates = {}
            for s in all_setups:
                rr_bucket = int(s["rr"])
                if rr_bucket not in win_rates:
                    win_rates[rr_bucket] = {"wins": 0, "total": 0}
                win_rates[rr_bucket]["total"] += 1
                if s["outcome"] == "WIN":
                    win_rates[rr_bucket]["wins"] += 1

            print(f"\n  WR by RR bucket:")
            for rr in sorted(win_rates.keys()):
                data = win_rates[rr]
                wr_bucket = data["wins"] / data["total"] * 100
                print(
                    f"    {rr}-{rr + 1}:1 → {wr_bucket:.0f}% WR ({data['total']} trades)"
                )
        else:
            print("  No setups found")


if __name__ == "__main__":
    ICCV2().run_backtest()
