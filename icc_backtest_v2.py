#!/usr/bin/env python3
"""
ICC BACKTEST v2 - Proper ICC Logic
1. Break → Correction → Look for CLUES → Entry
2. Only count trades with proper clues
3. Be water - adaptive analysis
"""

import yfinance as yf
import sys
from datetime import datetime, timedelta


class ICCBacktest:
    """Proper ICC backtest with clues"""

    def __init__(self):
        self.results = {}

        self.pairs = {
            "GBPCAD=X": "LONDON",
            "GBPUSD=X": "LONDON",
            "GBPJPY=X": "LONDON",
            "EURJPY=X": "LONDON",
            "USDJPY=X": "NY",
            "EURUSD=X": "NY",
            "XAUUSD=X": "LONDON",
            "BTC-USD": "24H",
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

    def check_clues(self, candles_after_break, direction):
        """
        Look for clues during correction
        STRICT REQUIREMENTS:
        - For SHORT: Need LH/LL pattern forming (structure change)
        - For LONG: Need HL/HH pattern forming (structure change)

        Returns: has_clues, clue_strength, narrative
        """
        if len(candles_after_break) < 10:
            return False, 0, "Not enough data"

        highs = [c["high"] for c in candles_after_break]
        lows = [c["low"] for c in candles_after_break]
        closes = [c["close"] for c in candles_after_break]

        strength = 0
        clues_found = []

        if direction == "SHORT":
            # Need CLEAR bearish structure forming
            # 1. Lower highs (at least 2)
            # 2. Lower lows forming OR price compressing

            # Find swing highs
            swing_highs = []
            for i in range(2, len(highs) - 2):
                if highs[i] > highs[i - 1] and highs[i] > highs[i + 1]:
                    swing_highs.append(highs[i])

            # Check if lower highs forming
            if len(swing_highs) >= 3:
                lower_highs = sum(
                    1
                    for i in range(1, len(swing_highs))
                    if swing_highs[i] < swing_highs[i - 1]
                )
                if lower_highs >= 2:
                    clues_found.append(f"LH pattern ({lower_highs} lower highs)")
                    strength += 3

            # Check if making lower lows (not making higher lows)
            swing_lows = []
            for i in range(2, len(lows) - 2):
                if lows[i] < lows[i - 1] and lows[i] < lows[i + 1]:
                    swing_lows.append(lows[i])

            if len(swing_lows) >= 2:
                lower_lows = sum(
                    1
                    for i in range(1, len(swing_lows))
                    if swing_lows[i] < swing_lows[i - 1]
                )
                if lower_lows >= 1:
                    clues_found.append(f"LL pattern forming")
                    strength += 2

        elif direction == "LONG":
            # Need CLEAR bullish structure forming
            # 1. Higher lows (at least 2)
            # 2. Higher highs forming OR price compressing

            # Find swing lows
            swing_lows = []
            for i in range(2, len(lows) - 2):
                if lows[i] < lows[i - 1] and lows[i] < lows[i + 1]:
                    swing_lows.append(lows[i])

            # Check if higher lows forming
            if len(swing_lows) >= 3:
                higher_lows = sum(
                    1
                    for i in range(1, len(swing_lows))
                    if swing_lows[i] > swing_lows[i - 1]
                )
                if higher_lows >= 2:
                    clues_found.append(f"HL pattern ({higher_lows} higher lows)")
                    strength += 3

            # Check if making higher highs
            swing_highs = []
            for i in range(2, len(highs) - 2):
                if highs[i] > highs[i - 1] and highs[i] > highs[i + 1]:
                    swing_highs.append(highs[i])

            if len(swing_highs) >= 2:
                higher_highs = sum(
                    1
                    for i in range(1, len(swing_highs))
                    if swing_highs[i] > swing_highs[i - 1]
                )
                if higher_highs >= 1:
                    clues_found.append(f"HH pattern forming")
                    strength += 2

        narrative = " | ".join(clues_found) if clues_found else "No structure clues"

        # STRICT: Need strength >= 3 for valid clues
        has_clues = strength >= 3

        return has_clues, strength, narrative

    def analyze_break(self, df, break_idx, break_level, direction):
        """
        Analyze what happened after a break
        Returns setup quality based on clues
        """
        highs = df["High"].values
        lows = df["Low"].values
        opens = df["Open"].values
        closes = df["Close"].values
        timestamps = df.index

        # Get candles after break
        post_candles = []
        for i in range(break_idx, min(break_idx + 30, len(closes))):
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
        has_clues, clue_strength, clue_narrative = self.check_clues(
            post_candles, direction
        )

        # Analyze continuation
        if len(post_candles) >= 10:
            first_5 = post_candles[:5]
            last_5 = post_candles[-5:]

            if direction == "SHORT":
                # For shorts: Did price continue down?
                start_price = first_5[0]["close"]
                end_price = last_5[-1]["close"]

                if end_price < start_price:
                    outcome = "TRENDED"
                elif end_price > start_price * 1.001:  # Moved up > 0.1%
                    outcome = "REVERSED"
                else:
                    outcome = "RANGED"
            else:
                # For longs
                start_price = first_5[0]["close"]
                end_price = last_5[-1]["close"]

                if end_price > start_price:
                    outcome = "TRENDED"
                elif end_price < start_price * 0.999:  # Moved down > 0.1%
                    outcome = "REVERSED"
                else:
                    outcome = "RANGED"
        else:
            outcome = "UNKNOWN"

        return {
            "has_clues": has_clues,
            "clue_strength": clue_strength,
            "clue_narrative": clue_narrative,
            "outcome": outcome,
            "direction": direction,
            "break_level": break_level,
            "post_candles": post_candles[:10],
        }

    def find_setups(self, df, pair):
        """Find all ICC setups"""
        setups = []

        highs = df["High"].values
        lows = df["Low"].values
        closes = df["Close"].values
        opens = df["Open"].values
        timestamps = df.index

        swings_high, swings_low = self.get_swings(highs, lows, lookback=5)

        if len(swings_high) < 3 or len(swings_low) < 3:
            return setups

        # Find breaks of structure
        for i in range(5, len(swings_low) - 5):
            # Check bearish breaks (broke below swing low)
            low_idx, low_level = swings_low[i]

            if low_idx + 5 >= len(closes):
                continue

            # Analyze this bearish break
            result = self.analyze_break(df, low_idx, low_level, "SHORT")
            result["type"] = "BREAK_DOWN"
            result["pair"] = pair
            result["time"] = timestamps[low_idx]
            result["break_level"] = low_level

            setups.append(result)

        # Find bullish breaks (broke above swing high)
        for i in range(5, len(swings_high) - 5):
            high_idx, high_level = swings_high[i]

            if high_idx + 5 >= len(closes):
                continue

            result = self.analyze_break(df, high_idx, high_level, "LONG")
            result["type"] = "BREAK_UP"
            result["pair"] = pair
            result["time"] = timestamps[high_idx]
            result["break_level"] = high_level

            setups.append(result)

        return setups

    def run_backtest(self):
        """Run full backtest"""
        print("=" * 70)
        print("  ICC BACKTEST v2 - WITH CLUES")
        print("  Break → Correction → CLUES → Entry")
        print("=" * 70)

        all_setups = []

        for pair, session in self.pairs.items():
            print(f"\n  Testing {pair}...")

            try:
                df = yf.Ticker(pair).history(period="2y", interval="4h")

                if len(df) < 200:
                    print(f"    Not enough data")
                    continue

                setups = self.find_setups(df, pair)
                all_setups.extend(setups)
                print(f"    Found {len(setups)} breaks")

            except Exception as e:
                print(f"    Error: {e}")

        return all_setups

    def analyze_results(self, setups):
        """Analyze with and without clues"""
        print("\n" + "=" * 70)
        print("  RESULTS ANALYSIS")
        print("=" * 70)

        # ALL BREAKS (no filter)
        all_total = len(setups)
        all_reversed = sum(1 for s in setups if s["outcome"] == "REVERSED")
        all_trended = sum(1 for s in setups if s["outcome"] == "TRENDED")
        all_ranged = sum(1 for s in setups if s["outcome"] == "RANGED")

        print("\n📊 ALL BREAKS (No Clues Filter):")
        print(f"  Total: {all_total}")
        print(f"  Reversed: {all_reversed} ({all_reversed / all_total * 100:.1f}%)")
        print(f"  Trended: {all_trended} ({all_trended / all_total * 100:.1f}%)")
        print(f"  Ranged: {all_ranged} ({all_ranged / all_total * 100:.1f}%)")
        print(f"  Win Rate (trending): {all_trended / all_total * 100:.1f}%")

        # WITH CLUES ONLY
        with_clues = [s for s in setups if s["has_clues"]]
        clues_total = len(with_clues)

        if clues_total > 0:
            clues_reversed = sum(1 for s in with_clues if s["outcome"] == "REVERSED")
            clues_trended = sum(1 for s in with_clues if s["outcome"] == "TRENDED")
            clues_ranged = sum(1 for s in with_clues if s["outcome"] == "RANGED")

            print(f"\n📊 WITH CLUES ONLY:")
            print(f"  Total: {clues_total}")
            print(
                f"  Reversed: {clues_reversed} ({clues_reversed / clues_total * 100:.1f}%)"
            )
            print(
                f"  Trended: {clues_trended} ({clues_trended / clues_total * 100:.1f}%)"
            )
            print(f"  Ranged: {clues_ranged} ({clues_ranged / clues_total * 100:.1f}%)")
            print(f"  Win Rate (trending): {clues_trended / clues_total * 100:.1f}%")
            print(
                f"  Improvement: +{clues_trended / clues_total * 100 - all_trended / all_total * 100:.1f}%"
            )

        # BY PAIR - WITH CLUES
        print(f"\n📊 BY PAIR (With Clues):")
        by_pair = {}
        for s in setups:
            pair = s["pair"]
            if pair not in by_pair:
                by_pair[pair] = {"all": 0, "with_clues": 0, "trended": 0}
            by_pair[pair]["all"] += 1
            if s["has_clues"]:
                by_pair[pair]["with_clues"] += 1
            if s["has_clues"] and s["outcome"] == "TRENDED":
                by_pair[pair]["trended"] += 1

        for pair, data in sorted(by_pair.items(), key=lambda x: -x[1]["all"]):
            all_c = data["all"]
            with_c = data["with_clues"]
            trended = data["trended"]
            if with_c >= 5:
                wr = trended / with_c * 100
                print(
                    f"  {pair:15} All: {all_c:3} | Clues: {with_c:3} | Trended: {trended:3} | Win: {wr:.0f}%"
                )
            else:
                print(
                    f"  {pair:15} All: {all_c:3} | Clues: {with_c:3} (not enough data)"
                )

        # BY CLUE STRENGTH
        print(f"\n📊 BY CLUE STRENGTH:")
        for strength in [1, 2, 3]:
            strength_setups = [s for s in setups if s["clue_strength"] >= strength]
            if strength_setups:
                total = len(strength_setups)
                trended = sum(1 for s in strength_setups if s["outcome"] == "TRENDED")
                print(
                    f"  Strength >= {strength}: {total} setups | Win Rate: {trended / total * 100:.1f}%"
                )

        # SUMMARY
        print("\n" + "=" * 70)
        print("  SUMMARY")
        print("=" * 70)

        if all_total > 0 and clues_total > 0:
            basic_wr = all_trended / all_total * 100
            clue_wr = clues_trended / clues_total * 100
            improvement = clue_wr - basic_wr

            print(f"\n  Trading ALL breaks: {basic_wr:.1f}% win rate")
            print(f"  Trading WITH CLUES only: {clue_wr:.1f}% win rate")
            print(f"  Improvement: +{improvement:.1f}%")
            print(
                f"\n  Setups filtered out: {all_total - clues_total} ({100 * (all_total - clues_total) / all_total:.0f}%)"
            )


if __name__ == "__main__":
    backtest = ICCBacktest()
    setups = backtest.run_backtest()
    backtest.analyze_results(setups)
