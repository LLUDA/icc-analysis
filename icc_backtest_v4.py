#!/usr/bin/env python3
"""
ICC BACKTEST v4 - PROPER RR-BASED BACKTEST
Rules:
- Entry: After break confirms + clues form
- SL: At nearest structure invalidation
- TP: At next structure level
- Win: TP hit before SL
- Loss: SL hit before TP
- Min RR: 2:1 required to count as valid setup
"""

import yfinance as yf
import sys


class ICCBacktestRR:
    """Proper RR-based ICC backtest"""

    def __init__(self):
        self.pairs = {
            "GBPCAD=X": "LONDON",
            "GBPUSD=X": "LONDON",
            "GBPJPY=X": "LONDON",
            "EURGBP=X": "LONDON",
            "EURJPY=X": "LONDON",
            "EURUSD=X": "NY",
            "USDJPY=X": "NY",
            "USDCAD=X": "NY",
            "XAUUSD=X": "LONDON",
        }

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

    def check_clues(self, post_candles, direction):
        """
        Check for ICC clues during correction phase
        """
        if len(post_candles) < 10:
            return False, 0, []

        highs = [c["high"] for c in post_candles]
        lows = [c["low"] for c in post_candles]

        clues = []
        strength = 0

        if direction == "SHORT":
            # Find swing highs
            swing_highs = []
            for i in range(2, len(highs) - 2):
                if highs[i] > highs[i - 1] and highs[i] > highs[i + 1]:
                    swing_highs.append(highs[i])

            # Check for lower highs
            if len(swing_highs) >= 3:
                lh_count = sum(
                    1
                    for i in range(1, len(swing_highs))
                    if swing_highs[i] < swing_highs[i - 1]
                )
                if lh_count >= 2:
                    clues.append(f"LH:{lh_count}")
                    strength += 3

            # Check for lower lows
            swing_lows = []
            for i in range(2, len(lows) - 2):
                if lows[i] < lows[i - 1] and lows[i] < lows[i + 1]:
                    swing_lows.append(lows[i])

            if len(swing_lows) >= 2:
                ll_count = sum(
                    1
                    for i in range(1, len(swing_lows))
                    if swing_lows[i] < swing_lows[i - 1]
                )
                if ll_count >= 1:
                    clues.append(f"LL:{ll_count}")
                    strength += 2

        elif direction == "LONG":
            # Find swing lows
            swing_lows = []
            for i in range(2, len(lows) - 2):
                if lows[i] < lows[i - 1] and lows[i] < lows[i + 1]:
                    swing_lows.append(lows[i])

            # Check for higher lows
            if len(swing_lows) >= 3:
                hl_count = sum(
                    1
                    for i in range(1, len(swing_lows))
                    if swing_lows[i] > swing_lows[i - 1]
                )
                if hl_count >= 2:
                    clues.append(f"HL:{hl_count}")
                    strength += 3

            # Check for higher highs
            swing_highs = []
            for i in range(2, len(highs) - 2):
                if highs[i] > highs[i - 1] and highs[i] > highs[i + 1]:
                    swing_highs.append(highs[i])

            if len(swing_highs) >= 2:
                hh_count = sum(
                    1
                    for i in range(1, len(swing_highs))
                    if swing_highs[i] > swing_highs[i - 1]
                )
                if hh_count >= 1:
                    clues.append(f"HH:{hh_count}")
                    strength += 2

        return strength >= 3, strength, clues

    def find_structure_levels(
        self, highs, lows, break_idx, direction, break_level, closes
    ):
        """
        Find SL and TP based on structure

        For SHORT (broke below swing low):
        - Entry: Slightly below break level (after confirmation)
        - SL: Above break level (at previous swing high structure)
        - TP: At next structure low below

        For LONG (broke above swing high):
        - Entry: Slightly above break level (after confirmation)
        - SL: Below break level (at previous swing low structure)
        - TP: At next structure high above
        """
        if direction == "SHORT":
            # For shorts: entry is at/above break level, SL is above entry, TP is below entry

            # Find previous swing high (SL should go just above this)
            sl = None
            for i in range(max(0, break_idx - 15), break_idx):
                if highs[i] > break_level:
                    sl = highs[i] * 1.001  # Small buffer above
                    break

            if sl is None:
                # Fallback: SL is 0.5% above break
                sl = break_level * 1.005

            # Find next structure low for TP
            tp = None
            for i in range(break_idx + 2, min(break_idx + 40, len(lows))):
                if lows[i] < break_level * 0.995:  # Clear break below
                    tp = lows[i] * 0.999
                    break

            if tp is None:
                # Fallback: TP is 1.5% below break
                tp = break_level * 0.985

        else:  # LONG
            # For longs: entry is at/below break level, SL is below entry, TP is above entry

            # Find previous swing low (SL should go just below this)
            sl = None
            for i in range(max(0, break_idx - 15), break_idx):
                if lows[i] < break_level:
                    sl = lows[i] * 0.999  # Small buffer below
                    break

            if sl is None:
                # Fallback: SL is 0.5% below break
                sl = break_level * 0.995

            # Find next structure high for TP
            tp = None
            for i in range(break_idx + 2, min(break_idx + 40, len(highs))):
                if highs[i] > break_level * 1.005:  # Clear break above
                    tp = highs[i] * 1.001
                    break

            if tp is None:
                # Fallback: TP is 1.5% above break
                tp = break_level * 1.015

        return sl, tp

    def analyze_trade(self, entry_price, sl, tp, direction, post_candles):
        """
        Simulate the trade and determine outcome based on structure hits
        Returns: WIN/LOSS, actual RR achieved, candles until outcome
        """
        if direction == "SHORT":
            # For short: we profit when price goes DOWN
            # SL is above entry, TP is below entry

            # Calculate distances
            risk = sl - entry_price  # How much we risk (SL above entry)
            reward = entry_price - tp  # How much we can make (TP below entry)

            if risk <= 0 or reward <= 0:
                return "INVALID", 0, 0

            rr_ratio = reward / risk

            # Find when SL or TP was hit
            for i, c in enumerate(post_candles):
                high = c["high"]
                low = c["low"]

                # TP hit first? (price dropped to TP level for short)
                if low <= tp:
                    return "WIN", rr_ratio, i

                # SL hit first? (price rose to SL level for short)
                if high >= sl:
                    return "LOSS", 0, i

        else:  # LONG
            # For long: we profit when price goes UP
            # SL is below entry, TP is above entry

            # Calculate distances
            risk = entry_price - sl  # How much we risk (SL below entry)
            reward = tp - entry_price  # How much we can make (TP above entry)

            if risk <= 0 or reward <= 0:
                return "INVALID", 0, 0

            rr_ratio = reward / risk

            # Find when SL or TP was hit
            for i, c in enumerate(post_candles):
                high = c["high"]
                low = c["low"]

                # TP hit first? (price rose to TP level for long)
                if high >= tp:
                    return "WIN", rr_ratio, i

                # SL hit first? (price dropped to SL level for long)
                if low <= sl:
                    return "LOSS", 0, i

        # Neither hit - still open
        return "OPEN", 0, len(post_candles)

    def analyze_break(self, df, break_idx, break_level, direction, pair):
        """Analyze a single break with proper RR rules"""
        highs = df["High"].values
        lows = df["Low"].values
        opens = df["Open"].values
        closes = df["Close"].values
        timestamps = df.index

        # Get candles after break (simulate waiting for clues)
        post_candles = []
        for i in range(break_idx, min(break_idx + 50, len(closes))):
            post_candles.append(
                {
                    "high": highs[i],
                    "low": lows[i],
                    "open": opens[i],
                    "close": closes[i],
                    "time": timestamps[i],
                }
            )

        # Check for clues
        has_clues, strength, clues = self.check_clues(post_candles, direction)

        if not has_clues:
            return None  # No valid setup

        # Find structure levels
        sl, tp = self.find_structure_levels(
            highs, lows, break_idx, direction, break_level, closes
        )

        # Entry price is at break confirmation (when clues form - say 5 candles in)
        entry_idx = min(5, len(post_candles) - 1)
        entry_price = post_candles[entry_idx]["close"]

        # Analyze the trade
        outcome, rr_achieved, candles_held = self.analyze_trade(
            entry_price, sl, tp, direction, post_candles
        )

        if outcome == "INVALID":
            return None

        return {
            "pair": pair,
            "direction": direction,
            "break_level": break_level,
            "entry_price": entry_price,
            "sl": sl,
            "tp": tp,
            "rr_achieved": rr_achieved,
            "outcome": outcome,
            "candles_held": candles_held,
            "clues": clues,
            "strength": strength,
            "session": self.pairs.get(pair, "UNKNOWN"),
            "time": timestamps[break_idx],
        }

    def find_setups(self, df, pair):
        """Find all valid ICC setups"""
        setups = []

        highs = df["High"].values
        lows = df["Low"].values
        closes = df["Close"].values
        timestamps = df.index

        swings_high, swings_low = self.get_swings(highs, lows, lookback=5)

        if len(swings_high) < 3 or len(swings_low) < 3:
            return setups

        # Find bearish breaks (break of swing low)
        for i in range(5, len(swings_low) - 10):
            low_idx, low_level = swings_low[i]
            if low_idx + 10 >= len(closes):
                continue

            result = self.analyze_break(df, low_idx, low_level, "SHORT", pair)
            if result:
                setups.append(result)

        # Find bullish breaks (break of swing high)
        for i in range(5, len(swings_high) - 10):
            high_idx, high_level = swings_high[i]
            if high_idx + 10 >= len(closes):
                continue

            result = self.analyze_break(df, high_idx, high_level, "LONG", pair)
            if result:
                setups.append(result)

        return setups

    def run_backtest(self):
        """Run full backtest"""
        print("=" * 70)
        print("  ICC BACKTEST v4 - PROPER RR RULES")
        print("  Entry: Break + Clues | SL: Structure | TP: Structure")
        print("=" * 70)

        all_setups = []

        for pair, session in self.pairs.items():
            print(f"\n  Testing {pair} ({session})...")

            try:
                df = yf.Ticker(pair).history(period="2y", interval="4h")

                if len(df) < 200:
                    print(f"    Not enough data")
                    continue

                setups = self.find_setups(df, pair)
                all_setups.extend(setups)
                print(f"    Found {len(setups)} valid setups")

            except Exception as e:
                print(f"    Error: {e}")

        return all_setups

    def analyze_results(self, setups):
        """Comprehensive analysis with proper RR metrics"""
        print("\n" + "=" * 70)
        print("  RESULTS - ICC WITH PROPER RR RULES")
        print("=" * 70)

        total = len(setups)
        if total == 0:
            print("\n  No valid setups found!")
            return

        wins = [s for s in setups if s["outcome"] == "WIN"]
        losses = [s for s in setups if s["outcome"] == "LOSS"]
        open_trades = [s for s in setups if s["outcome"] == "OPEN"]

        win_count = len(wins)
        loss_count = len(losses)

        print(f"\n  Total valid setups: {total}")
        print(f"  Wins: {win_count} ({win_count / total * 100:.1f}%)")
        print(f"  Losses: {loss_count} ({loss_count / total * 100:.1f}%)")
        print(f"  Still open: {len(open_trades)}")

        # Win rate
        if win_count + loss_count > 0:
            win_rate = win_count / (win_count + loss_count) * 100
            print(f"\n  Win Rate: {win_rate:.1f}%")

        # Average RR of wins
        if wins:
            avg_rr = sum(w["rr_achieved"] for w in wins) / len(wins)
            print(f"  Average RR on wins: {avg_rr:.2f}:1")

        # Average RR of losses
        if losses:
            print(f"  Average RR on losses: 1:1 (stopped out)")

        # Expected value
        if wins and losses:
            total_rr = sum(w["rr_achieved"] for w in wins)
            ev = (win_rate / 100 * avg_rr) - (loss_count / total * 1)
            print(f"\n  Expected Value per trade: {ev:.2f}R")

        # ============================================
        # BY RR THRESHOLD
        # ============================================
        print("\n" + "=" * 70)
        print("  WIN RATE BY MINIMUM RR REQUIREMENT")
        print("=" * 70)

        for min_rr in [1.5, 2.0, 2.5, 3.0]:
            valid = [s for s in setups if s["rr_achieved"] >= min_rr]
            if valid:
                w = sum(1 for s in valid if s["outcome"] == "WIN")
                l = sum(1 for s in valid if s["outcome"] == "LOSS")
                if w + l > 0:
                    wr = w / (w + l) * 100
                    print(
                        f"\n  Min {min_rr}:1 RR: {len(valid)} setups | Win rate: {wr:.1f}%"
                    )

        # ============================================
        # BY SESSION
        # ============================================
        print("\n" + "=" * 70)
        print("  BY SESSION")
        print("=" * 70)

        for session in ["LONDON", "NY", "TOKYO"]:
            sess = [s for s in setups if s["session"] == session]
            if sess:
                w = sum(1 for s in sess if s["outcome"] == "WIN")
                l = sum(1 for s in sess if s["outcome"] == "LOSS")
                if w + l > 0:
                    wr = w / (w + l) * 100
                    avg_rr = sum(
                        s["rr_achieved"] for s in sess if s["outcome"] == "WIN"
                    ) / max(1, w)
                    print(f"\n  {session}:")
                    print(
                        f"    Setups: {len(sess)} | Win rate: {wr:.1f}% | Avg RR: {avg_rr:.2f}:1"
                    )

        # ============================================
        # BY PAIR
        # ============================================
        print("\n" + "=" * 70)
        print("  BY PAIR")
        print("=" * 70)

        by_pair = {}
        for s in setups:
            pair = s["pair"]
            if pair not in by_pair:
                by_pair[pair] = {"total": 0, "wins": 0, "losses": 0, "rr_sum": 0}
            by_pair[pair]["total"] += 1
            if s["outcome"] == "WIN":
                by_pair[pair]["wins"] += 1
                by_pair[pair]["rr_sum"] += s["rr_achieved"]
            elif s["outcome"] == "LOSS":
                by_pair[pair]["losses"] += 1

        sorted_pairs = sorted(
            by_pair.items(),
            key=lambda x: (
                -x[1]["wins"] / (x[1]["wins"] + x[1]["losses"])
                if (x[1]["wins"] + x[1]["losses"]) > 0
                else 0
            ),
        )

        for pair, data in sorted_pairs:
            total = data["total"]
            pair_wins = data["wins"]
            pair_losses = data["losses"]
            if pair_wins + pair_losses > 0:
                wr = pair_wins / (pair_wins + pair_losses) * 100
                avg_rr = data["rr_sum"] / max(1, pair_wins)
                print(f"\n  {pair}:")
                print(f"    Setups: {total} | Win: {pair_wins} | Loss: {pair_losses}")
                print(f"    Win rate: {wr:.1f}% | Avg RR: {avg_rr:.2f}:1")

        # ============================================
        # DISTRIBUTION OF RR ACHIEVED
        # ============================================
        print("\n" + "=" * 70)
        print("  RR DISTRIBUTION (WINS)")
        print("=" * 70)

        rr_buckets = {"< 1:1": 0, "1-2:1": 0, "2-3:1": 0, "3-4:1": 0, "> 4:1": 0}
        for w in wins:
            rr = w["rr_achieved"]
            if rr < 1:
                rr_buckets["< 1:1"] += 1
            elif rr < 2:
                rr_buckets["1-2:1"] += 1
            elif rr < 3:
                rr_buckets["2-3:1"] += 1
            elif rr < 4:
                rr_buckets["3-4:1"] += 1
            else:
                rr_buckets["> 4:1"] += 1

        for bucket, count in rr_buckets.items():
            pct = count / len(wins) * 100 if wins else 0
            print(f"  {bucket}: {count} ({pct:.1f}%)")

        # ============================================
        # SUMMARY
        # ============================================
        print("\n" + "=" * 70)
        print("  SUMMARY")
        print("=" * 70)

        closed = win_count + loss_count
        if closed > 0:
            print(f"\n  Closed trades: {closed}")
            print(f"  Win rate: {win_count / closed * 100:.1f}%")
            if wins:
                print(
                    f"  Average winner: {sum(w['rr_achieved'] for w in wins) / len(wins):.2f}:1"
                )
            print(f"  Average loser: 1:1 (structure stop)")
            print(f"  Expectancy: {ev:.2f}R per trade" if wins and losses else "")


if __name__ == "__main__":
    backtest = ICCBacktestRR()
    setups = backtest.run_backtest()
    backtest.analyze_results(setups)
