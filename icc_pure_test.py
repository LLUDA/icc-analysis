#!/usr/bin/env python3
"""
ICC BACKTEST - Pure Price Action
Method:
1. Price makes a swing
2. Price BREAKS below/above the swing (indication)
3. Wait for correction back to that level
4. Enter at break level
5. SL at significant swing
6. TP at structure (min 2:1 RR)
"""

import yfinance as yf


class PureICCBacktest:
    """Pure ICC price action"""

    def __init__(self):
        self.pairs = ["GBPUSD=X"]

    def run_backtest(self):
        """Run backtest on one pair"""
        pair = self.pairs[0]

        print("=" * 70)
        print("  ICC PURE PRICE ACTION BACKTEST")
        print(f"  Pair: {pair}")
        print("=" * 70)

        df = yf.Ticker(pair).history(period="2y", interval="4h")
        print(f"\n  Loaded {len(df)} candles")

        highs = df["High"].values
        lows = df["Low"].values
        closes = df["Close"].values

        # Find swing points
        def get_swing_points(data, is_high=True):
            swings = []
            for i in range(5, len(data) - 5):
                if is_high:
                    if data[i] == max(data[i - 5 : i + 6]):
                        swings.append((i, data[i]))
                else:
                    if data[i] == min(data[i - 5 : i + 6]):
                        swings.append((i, data[i]))
            return swings

        swing_highs = get_swing_points(highs, True)
        swing_lows = get_swing_points(lows, False)

        print(f"  Swing highs: {len(swing_highs)}")
        print(f"  Swing lows: {len(swing_lows)}")

        setups = []

        # ============================================
        # Find BREAKS of swing lows (SHORT setups)
        # ============================================
        print("\n  Scanning for SHORT setups...")

        for i in range(10, len(swing_lows) - 5):
            idx, level = swing_lows[i]

            # Check if price actually BROKE below this swing low
            broke = False
            for j in range(idx, min(idx + 10, len(lows))):
                if lows[j] < level:
                    broke = True
                    break

            if not broke:
                continue

            # SL: Find recent swing high above break level
            sl = None
            for j in range(idx - 1, max(0, idx - 20), -1):
                if highs[j] > level:
                    sl = highs[j]
                    break

            if sl is None:
                continue

            # TP: Find next structure low
            tp = None
            for j in range(idx + 1, min(idx + 40, len(lows))):
                if lows[j] < level * 0.995:
                    tp = lows[j]
                    break

            if tp is None:
                tp = level * 0.97  # Fallback 3% below

            # Calculate RR
            entry = level  # Enter at break level (when retested)
            risk = sl - entry
            reward = entry - tp

            if risk <= 0 or reward <= 0:
                continue

            rr = reward / risk

            if rr < 2.0:
                continue  # Skip if not 2:1

            # Wait for correction (price returns to level)
            correction = False
            entry_idx = None
            for j in range(idx, min(idx + 20, len(closes))):
                if highs[j] >= level:
                    correction = True
                    entry_idx = j
                    break

            if not correction:
                continue

            # Simulate trade from entry
            entry_price = closes[entry_idx]

            for j in range(entry_idx, min(entry_idx + 50, len(closes))):
                if lows[j] <= tp:
                    setups.append(
                        {
                            "type": "SHORT",
                            "entry": entry_price,
                            "sl": sl,
                            "tp": tp,
                            "rr": rr,
                            "outcome": "WIN",
                        }
                    )
                    break
                if highs[j] >= sl:
                    setups.append(
                        {
                            "type": "SHORT",
                            "entry": entry_price,
                            "sl": sl,
                            "tp": tp,
                            "rr": rr,
                            "outcome": "LOSS",
                        }
                    )
                    break

        print(
            f"    Found {len([s for s in setups if s['type'] == 'SHORT'])} SHORT setups"
        )

        # ============================================
        # Find BREAKS of swing highs (LONG setups)
        # ============================================
        print("\n  Scanning for LONG setups...")

        for i in range(10, len(swing_highs) - 5):
            idx, level = swing_highs[i]

            # Check if price actually BROKE above this swing high
            broke = False
            for j in range(idx, min(idx + 10, len(highs))):
                if highs[j] > level:
                    broke = True
                    break

            if not broke:
                continue

            # SL: Find recent swing low below break level
            sl = None
            for j in range(idx - 1, max(0, idx - 20), -1):
                if lows[j] < level:
                    sl = lows[j]
                    break

            if sl is None:
                continue

            # TP: Find next structure high
            tp = None
            for j in range(idx + 1, min(idx + 40, len(highs))):
                if highs[j] > level * 1.005:
                    tp = highs[j]
                    break

            if tp is None:
                tp = level * 1.03  # Fallback 3% above

            # Calculate RR
            entry = level  # Enter at break level
            risk = entry - sl
            reward = tp - entry

            if risk <= 0 or reward <= 0:
                continue

            rr = reward / risk

            if rr < 2.0:
                continue

            # Wait for correction
            correction = False
            entry_idx = None
            for j in range(idx, min(idx + 20, len(closes))):
                if lows[j] <= level:
                    correction = True
                    entry_idx = j
                    break

            if not correction:
                continue

            # Simulate trade
            entry_price = closes[entry_idx]

            for j in range(entry_idx, min(entry_idx + 50, len(closes))):
                if highs[j] >= tp:
                    setups.append(
                        {
                            "type": "LONG",
                            "entry": entry_price,
                            "sl": sl,
                            "tp": tp,
                            "rr": rr,
                            "outcome": "WIN",
                        }
                    )
                    break
                if lows[j] <= sl:
                    setups.append(
                        {
                            "type": "LONG",
                            "entry": entry_price,
                            "sl": sl,
                            "tp": tp,
                            "rr": rr,
                            "outcome": "LOSS",
                        }
                    )
                    break

        print(
            f"    Found {len([s for s in setups if s['type'] == 'LONG'])} LONG setups"
        )

        # ============================================
        # Analyze results
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

        shorts = [s for s in setups if s["type"] == "SHORT"]
        longs = [s for s in setups if s["type"] == "LONG"]

        if shorts:
            sw = len([s for s in shorts if s["outcome"] == "WIN"])
            print(
                f"\n  SHORTS: {len(shorts)} | Win: {sw} ({sw / len(shorts) * 100:.0f}%)"
            )

        if longs:
            lw = len([s for s in longs if s["outcome"] == "WIN"])
            print(f"  LONGS: {len(longs)} | Win: {lw} ({lw / len(longs) * 100:.0f}%)")

        # Average RR
        avg_rr = sum(s["rr"] for s in setups) / total
        print(f"\n  Average RR: {avg_rr:.2f}:1")

        # Expected value
        ev = (wins / total * avg_rr) - (losses / total * 1)
        print(f"  EXPECTED VALUE: {ev:.2f}R per trade")


if __name__ == "__main__":
    PureICCBacktest().run_backtest()
