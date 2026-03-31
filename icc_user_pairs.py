#!/usr/bin/env python3
"""
ICC Backtest - User's Pairs (XAUUSD, US30, GBPCAD, USDJPY)
"""

import yfinance as yf
from datetime import datetime, timedelta


class ICCUserPairs:
    """Test ICC method on user's specific pairs"""

    def __init__(self):
        self.pairs = ["GC=F", "^DJI", "GBPCAD=X", "USDJPY=X"]
        self.names = {
            "GC=F": "XAUUSD (Gold)",
            "^DJI": "US30 (Dow)",
            "GBPCAD=X": "GBPCAD",
            "USDJPY=X": "USDJPY",
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

    def run_backtest(self):
        current_time = datetime.now()

        print("=" * 70)
        print("  ICC BACKTEST - YOUR PAIRS")
        print("  Period: Last 60 days")
        print("  Method: Indication → Correction → Continuation")
        print("  Filter: Correction ≤ 70% of original move")
        print("=" * 70)

        all_setups = []

        for pair in self.pairs:
            name = self.names.get(pair, pair)
            print(f"\n{'=' * 55}")
            print(f"  {name}")
            print(f"{'=' * 55}")

            try:
                end_date = current_time.strftime("%Y-%m-%d")
                start_date = (current_time - timedelta(days=60)).strftime("%Y-%m-%d")

                df_4h = yf.Ticker(pair).history(
                    start=start_date, end=end_date, interval="4h"
                )
                df_1h = yf.Ticker(pair).history(
                    start=start_date, end=end_date, interval="1h"
                )

                if len(df_4h) < 100 or len(df_1h) < 200:
                    print(f"  Not enough data ({len(df_4h)} 4H, {len(df_1h)} 1H)")
                    continue

                print(
                    f"  Data: {df_1h.index[0].strftime('%b %d')} to {df_1h.index[-1].strftime('%b %d')}"
                )
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

                    trend = self.get_trend(highs_4h, lows_4h, idx_4h)
                    if trend != "DOWNTREND":
                        continue

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

                    correction_idx = None
                    for j in range(break_idx, min(break_idx + 50, len(closes_1h))):
                        if highs_1h[j] >= level:
                            correction_idx = j
                            break
                    if correction_idx is None:
                        continue

                    correction_depth = highs_1h[correction_idx] - level
                    correction_pct = correction_depth / move_size
                    if correction_pct > 0.70:
                        continue

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
                                "entry": level,
                                "sl": sl,
                                "tp": tp,
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

                    trend = self.get_trend(highs_4h, lows_4h, idx_4h)
                    if trend != "UPTREND":
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
                    if correction_pct > 0.70:
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
                    if rr < 2.0:
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
                                "entry": level,
                                "sl": sl,
                                "tp": tp,
                                "rr": rr,
                                "correction_pct": correction_pct * 100,
                                "outcome": outcome,
                                "entry_time": entry_time.strftime("%b %d %H:%M"),
                            }
                        )

                if setups:
                    print(f"\n  SETUPS: {len(setups)}")
                    for i, s in enumerate(setups, 1):
                        emoji = "🟢" if s["outcome"] == "WIN" else "🔴"
                        print(f"\n  {i}. {emoji} {s['direction']} | {s['entry_time']}")
                        print(
                            f"     Entry: {s['entry']:.5f} | SL: {s['sl']:.5f} | TP: {s['tp']:.5f}"
                        )
                        print(
                            f"     RR: {s['rr']:.2f}:1 | Correction: {s['correction_pct']:.0f}%"
                        )
                    all_setups.extend(setups)
                else:
                    print("  No valid setups")

            except Exception as e:
                print(f"  Error: {e}")

        # TOTAL
        print("\n" + "=" * 70)
        print("  TOTAL RESULTS - YOUR PAIRS")
        print("=" * 70)

        if all_setups:
            wins = len([s for s in all_setups if s["outcome"] == "WIN"])
            losses = len([s for s in all_setups if s["outcome"] == "LOSS"])
            total = len(all_setups)

            print(f"\n  Total setups: {total}")
            print(f"  Wins: {wins} 🟢 | Losses: {losses} 🔴")
            print(f"\n  WIN RATE: {wins / total * 100:.0f}%")
            print(f"  Average RR: {sum(s['rr'] for s in all_setups) / total:.2f}:1")
        else:
            print("\n  No setups found")


if __name__ == "__main__":
    ICCUserPairs().run_backtest()
