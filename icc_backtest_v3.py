#!/usr/bin/env python3
"""
ICC BACKTEST v3 - LEARNED FROM JOURNAL
Incorporating learnings from trader_journal.py:
1. Volatility filtering - avoid low vol/ranging markets
2. Session weighting - London > NY > Tokyo
3. Combined clues - multiple confirming signals
4. Stronger structure requirements
"""

import yfinance as yf
import sys
from datetime import datetime, timedelta


class ICCBacktestLearned:
    """Backtest with journal learnings applied"""

    def __init__(self):
        self.results = {}

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

        # Session quality weighting
        self.session_quality = {
            "LONDON": 1.0,
            "NY": 0.85,
            "TOKYO": 0.70,
            "24H": 0.80,
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

    def get_volatility(self, highs, lows, closes):
        """Calculate market volatility context - adjusted for 4H data"""
        if len(highs) < 10:
            return "UNKNOWN"

        # Calculate range as % of price
        ranges = [(highs[i] - lows[i]) / closes[i] * 100 for i in range(len(highs))]
        avg_range = sum(ranges) / len(ranges)

        # Adjusted thresholds for 4H data
        if avg_range > 0.8:
            return "HIGH_VOL"
        elif avg_range > 0.4:
            return "MED_VOL"
        else:
            return "LOW_VOL"

    def is_vol_expanding(
        self, pre_highs, pre_lows, pre_closes, post_highs, post_lows, post_closes
    ):
        """Check if volatility is expanding after the break (good sign)"""
        if len(pre_highs) < 5 or len(post_highs) < 5:
            return False

        # Pre-break volatility
        pre_ranges = [
            (pre_highs[i] - pre_lows[i]) / pre_closes[i] * 100
            for i in range(len(pre_highs))
        ]
        pre_avg = sum(pre_ranges) / len(pre_ranges)

        # Post-break volatility
        post_ranges = [
            (post_highs[i] - post_lows[i]) / post_closes[i] * 100
            for i in range(len(post_highs))
        ]
        post_avg = sum(post_ranges) / len(post_ranges)

        # Volatility expanding = good (market is active)
        return post_avg > pre_avg * 1.2

    def check_structure(self, candles_after_break, direction):
        """
        STRICT structure check - learned from journal
        Only trade when structure is CLEAR
        """
        if len(candles_after_break) < 10:
            return False, 0, []

        highs = [c["high"] for c in candles_after_break]
        lows = [c["low"] for c in candles_after_break]
        closes = [c["close"] for c in candles_after_break]

        clues = []
        strength = 0

        if direction == "SHORT":
            # Need CLEAR bearish structure
            # 1. Lower highs (at least 2 consecutive)
            # 2. Lower lows forming OR compression

            # Find swing highs
            swing_highs = []
            for i in range(2, len(highs) - 2):
                if highs[i] > highs[i - 1] and highs[i] > highs[i + 1]:
                    swing_highs.append((i, highs[i]))

            # Check for consecutive lower highs
            if len(swing_highs) >= 3:
                lh_count = 0
                for i in range(1, len(swing_highs)):
                    if swing_highs[i][1] < swing_highs[i - 1][1]:
                        lh_count += 1

                if lh_count >= 2:
                    clues.append(f"LH:{lh_count}")
                    strength += 3

            # Find swing lows
            swing_lows = []
            for i in range(2, len(lows) - 2):
                if lows[i] < lows[i - 1] and lows[i] < lows[i + 1]:
                    swing_lows.append((i, lows[i]))

            # Check for lower lows
            if len(swing_lows) >= 2:
                ll_count = 0
                for i in range(1, len(swing_lows)):
                    if swing_lows[i][1] < swing_lows[i - 1][1]:
                        ll_count += 1

                if ll_count >= 1:
                    clues.append(f"LL:{ll_count}")
                    strength += 2

            # Check for compression (tight range)
            recent_range = max(highs[-5:]) - min(lows[-5:])
            if recent_range < avg(closes[-5:]) * 0.005:  # < 0.5% range
                clues.append("COMPRESSED")
                strength += 1

        elif direction == "LONG":
            # Need CLEAR bullish structure
            # 1. Higher lows (at least 2 consecutive)
            # 2. Higher highs forming OR compression

            # Find swing lows
            swing_lows = []
            for i in range(2, len(lows) - 2):
                if lows[i] < lows[i - 1] and lows[i] < lows[i + 1]:
                    swing_lows.append((i, lows[i]))

            # Check for consecutive higher lows
            if len(swing_lows) >= 3:
                hl_count = 0
                for i in range(1, len(swing_lows)):
                    if swing_lows[i][1] > swing_lows[i - 1][1]:
                        hl_count += 1

                if hl_count >= 2:
                    clues.append(f"HL:{hl_count}")
                    strength += 3

            # Find swing highs
            swing_highs = []
            for i in range(2, len(highs) - 2):
                if highs[i] > highs[i - 1] and highs[i] > highs[i + 1]:
                    swing_highs.append((i, highs[i]))

            # Check for higher highs
            if len(swing_highs) >= 2:
                hh_count = 0
                for i in range(1, len(swing_highs)):
                    if swing_highs[i][1] > swing_highs[i - 1][1]:
                        hh_count += 1

                if hh_count >= 1:
                    clues.append(f"HH:{hh_count}")
                    strength += 2

            # Check for compression
            recent_range = max(highs[-5:]) - min(lows[-5:])
            if recent_range < avg(closes[-5:]) * 0.005:
                clues.append("COMPRESSED")
                strength += 1

        return strength >= 3, strength, clues

    def analyze_break(self, df, break_idx, break_level, direction, pair):
        """
        Analyze what happened after a break
        """
        highs = df["High"].values
        lows = df["Low"].values
        opens = df["Open"].values
        closes = df["Close"].values
        timestamps = df.index

        # Get candles after break
        post_candles = []
        for i in range(break_idx, min(break_idx + 40, len(closes))):
            post_candles.append(
                {
                    "high": highs[i],
                    "low": lows[i],
                    "open": opens[i],
                    "close": closes[i],
                    "time": timestamps[i],
                }
            )

        # Get pre-break data
        pre_start = max(0, break_idx - 15)
        pre_highs = highs[pre_start:break_idx]
        pre_lows = lows[pre_start:break_idx]
        pre_closes = closes[pre_start:break_idx]

        post_highs = [c["high"] for c in post_candles]
        post_lows = [c["low"] for c in post_candles]
        post_closes = [c["close"] for c in post_candles]

        # Check volatility BEFORE break
        pre_vol = self.get_volatility(pre_highs, pre_lows, pre_closes)

        # Check if volatility is expanding after break
        vol_expanding = self.is_vol_expanding(
            pre_highs, pre_lows, pre_closes, post_highs, post_lows, post_closes
        )

        # Check structure clues
        has_structure, strength, structure_clues = self.check_structure(
            post_candles, direction
        )

        # Analyze outcome - using same methodology as v2
        if len(post_candles) >= 10:
            first_5 = post_candles[:5]
            last_5 = post_candles[-5:]

            if direction == "SHORT":
                start_price = first_5[0]["close"]
                end_price = last_5[-1]["close"]

                if end_price < start_price:
                    outcome = "TRENDED"
                elif end_price > start_price * 1.001:  # Moved up > 0.1%
                    outcome = "REVERSED"
                else:
                    outcome = "RANGED"
            else:
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
            "has_structure": has_structure,
            "strength": strength,
            "structure_clues": structure_clues,
            "outcome": outcome,
            "direction": direction,
            "break_level": break_level,
            "volatility": pre_vol,
            "vol_expanding": vol_expanding,
            "pair": pair,
            "session": self.pairs.get(pair, "UNKNOWN"),
            "time": timestamps[break_idx],
        }

    def find_setups(self, df, pair):
        """Find all ICC setups"""
        setups = []

        highs = df["High"].values
        lows = df["Low"].values
        closes = df["Close"].values
        timestamps = df.index

        swings_high, swings_low = self.get_swings(highs, lows, lookback=5)

        if len(swings_high) < 3 or len(swings_low) < 3:
            return setups

        # Find bearish breaks
        for i in range(5, len(swings_low) - 5):
            low_idx, low_level = swings_low[i]
            if low_idx + 5 >= len(closes):
                continue

            result = self.analyze_break(df, low_idx, low_level, "SHORT", pair)
            result["type"] = "BREAK_DOWN"
            result["break_level"] = low_level
            setups.append(result)

        # Find bullish breaks
        for i in range(5, len(swings_high) - 5):
            high_idx, high_level = swings_high[i]
            if high_idx + 5 >= len(closes):
                continue

            result = self.analyze_break(df, high_idx, high_level, "LONG", pair)
            result["type"] = "BREAK_UP"
            result["break_level"] = high_level
            setups.append(result)

        return setups

    def run_backtest(self):
        """Run full backtest"""
        print("=" * 70)
        print("  ICC BACKTEST v3 - LEARNED FROM JOURNAL")
        print("  +Volatility Filter +Session Weighting +Stronger Structure")
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
                print(f"    Found {len(setups)} breaks")

            except Exception as e:
                print(f"    Error: {e}")

        return all_setups

    def analyze_results(self, setups):
        """Comprehensive analysis with learnings applied"""
        print("\n" + "=" * 70)
        print("  RESULTS - ALL BREAKS (BASELINE)")
        print("=" * 70)

        all_total = len(setups)
        all_trended = sum(1 for s in setups if s["outcome"] == "TRENDED")
        all_reversed = sum(1 for s in setups if s["outcome"] == "REVERSED")
        all_ranged = sum(1 for s in setups if s["outcome"] == "RANGED")

        print(f"\n  Total setups: {all_total}")
        print(f"  Trended (Wins): {all_trended} ({all_trended / all_total * 100:.1f}%)")
        print(
            f"  Reversed (Losses): {all_reversed} ({all_reversed / all_total * 100:.1f}%)"
        )
        print(f"  Ranged: {all_ranged} ({all_ranged / all_total * 100:.1f}%)")
        print(f"  Win Rate: {all_trended / all_total * 100:.1f}%")

        # ============================================
        # FILTER 1: Structure clues
        # ============================================
        print("\n" + "=" * 70)
        print("  FILTER 1: STRUCTURE CLUES ONLY")
        print("=" * 70)

        with_structure = [s for s in setups if s["has_structure"]]
        ws_total = len(with_structure)
        ws_trended = sum(1 for s in with_structure if s["outcome"] == "TRENDED")
        ws_reversed = sum(1 for s in with_structure if s["outcome"] == "REVERSED")

        print(f"\n  Total with structure: {ws_total}")
        print(f"  Trended: {ws_trended} ({ws_trended / ws_total * 100:.1f}%)")
        print(f"  Reversed: {ws_reversed} ({ws_reversed / ws_total * 100:.1f}%)")
        print(f"  Win Rate: {ws_trended / ws_total * 100:.1f}%")
        print(
            f"  Improvement: +{ws_trended / ws_total * 100 - all_trended / all_total * 100:.1f}%"
        )

        # ============================================
        # FILTER 2: Structure + Volatility Expansion
        # ============================================
        print("\n" + "=" * 70)
        print("  FILTER 2: STRUCTURE + VOL EXPANDING")
        print("=" * 70)

        vol_expanding = [s for s in with_structure if s.get("vol_expanding", False)]
        ve_total = len(vol_expanding)
        ve_trended = sum(1 for s in vol_expanding if s["outcome"] == "TRENDED")
        ve_reversed = sum(1 for s in vol_expanding if s["outcome"] == "REVERSED")

        print(f"\n  Total with structure + vol expanding: {ve_total}")
        if ve_total > 0:
            print(f"  Trended: {ve_trended} ({ve_trended / ve_total * 100:.1f}%)")
            print(f"  Reversed: {ve_reversed} ({ve_reversed / ve_total * 100:.1f}%)")
            print(f"  Win Rate: {ve_trended / ve_total * 100:.1f}%")
            print(
                f"  Improvement: +{ve_trended / ve_total * 100 - all_trended / all_total * 100:.1f}%"
            )

        # ============================================
        # FILTER 3: Structure + Volatility Level
        # ============================================
        print("\n" + "=" * 70)
        print("  FILTER 3: STRUCTURE + HIGH/MED VOL")
        print("=" * 70)

        high_vol = [
            s for s in with_structure if s["volatility"] in ["HIGH_VOL", "MED_VOL"]
        ]
        hv_total = len(high_vol)
        hv_trended = sum(1 for s in high_vol if s["outcome"] == "TRENDED")

        print(f"\n  Total with high/med vol: {hv_total}")
        if hv_total > 0:
            print(f"  Win Rate: {hv_trended / hv_total * 100:.1f}%")
            print(
                f"  Improvement: +{hv_trended / hv_total * 100 - all_trended / all_total * 100:.1f}%"
            )

        # ============================================
        # FILTER 4: Combined (Structure + Vol Expanding)
        # ============================================
        print("\n" + "=" * 70)
        print("  FILTER 4: STRUCTURE + VOL EXPANDING (STRICT)")
        print("=" * 70)

        # Use vol_expanding with strength >= 4
        vol_exp_strict = [
            s
            for s in with_structure
            if s.get("vol_expanding", False) and s["strength"] >= 4
        ]
        ves_total = len(vol_exp_strict)
        ves_trended = sum(1 for s in vol_exp_strict if s["outcome"] == "TRENDED")

        print(f"\n  Total with strict filter: {ves_total}")
        if ves_total > 0:
            print(f"  Win Rate: {ves_trended / ves_total * 100:.1f}%")
            print(
                f"  Improvement: +{ves_trended / ves_total * 100 - all_trended / all_total * 100:.1f}%"
            )

        # ============================================
        # BY STRENGTH LEVEL
        # ============================================
        print("\n" + "=" * 70)
        print("  BY STRUCTURE STRENGTH")
        print("=" * 70)

        for strength in [3, 4, 5]:
            strong = [s for s in setups if s["strength"] >= strength]
            if strong:
                s_total = len(strong)
                s_trended = sum(1 for x in strong if x["outcome"] == "TRENDED")
                print(f"\n  Strength >= {strength}:")
                print(f"    Total: {s_total}")
                print(f"    Win Rate: {s_trended / s_total * 100:.1f}%")

        # ============================================
        # BY VOLATILITY
        # ============================================
        print("\n" + "=" * 70)
        print("  BY VOLATILITY (with structure)")
        print("=" * 70)

        for vol in ["HIGH_VOL", "MED_VOL", "LOW_VOL"]:
            vol_setups = [s for s in with_structure if s["volatility"] == vol]
            if vol_setups:
                v_total = len(vol_setups)
                v_trended = sum(1 for x in vol_setups if x["outcome"] == "TRENDED")
                print(f"\n  {vol}:")
                print(f"    Total: {v_total}")
                print(f"    Win Rate: {v_trended / v_total * 100:.1f}%")

        # ============================================
        # BY SESSION
        # ============================================
        print("\n" + "=" * 70)
        print("  BY SESSION (with structure)")
        print("=" * 70)

        for session in ["LONDON", "NY", "TOKYO"]:
            sess_setups = [s for s in with_structure if s["session"] == session]
            if sess_setups:
                s_total = len(sess_setups)
                s_trended = sum(1 for x in sess_setups if x["outcome"] == "TRENDED")
                print(f"\n  {session}:")
                print(f"    Total: {s_total}")
                print(f"    Win Rate: {s_trended / s_total * 100:.1f}%")

        # ============================================
        # BY PAIR
        # ============================================
        print("\n" + "=" * 70)
        print("  BY PAIR (with structure)")
        print("=" * 70)

        by_pair = {}
        for s in setups:
            if s["has_structure"]:
                pair = s["pair"]
                if pair not in by_pair:
                    by_pair[pair] = {"total": 0, "trended": 0}
                by_pair[pair]["total"] += 1
                if s["outcome"] == "TRENDED":
                    by_pair[pair]["trended"] += 1

        sorted_pairs = sorted(
            by_pair.items(),
            key=lambda x: -x[1]["trended"] / x[1]["total"] if x[1]["total"] > 10 else 0,
        )

        for pair, data in sorted_pairs:
            total = data["total"]
            trended = data["trended"]
            if total >= 5:
                wr = trended / total * 100
                print(f"\n  {pair}:")
                print(f"    Total: {total} | Win Rate: {wr:.1f}%")

        # ============================================
        # FINAL SUMMARY
        # ============================================
        print("\n" + "=" * 70)
        print("  FINAL SUMMARY - PROGRESSION")
        print("=" * 70)

        print(
            f"\n  Baseline (all breaks):           {all_trended / all_total * 100:.1f}% win rate ({all_total} setups)"
        )
        print(
            f"  + Structure filter:             {ws_trended / ws_total * 100:.1f}% win rate ({ws_total} setups)"
        )
        print(
            f"  + Vol expanding:                {ve_trended / ve_total * 100:.1f}% win rate ({ve_total} setups)"
        )
        if hv_total > 0:
            print(
                f"  + High/Med vol:                  {hv_trended / hv_total * 100:.1f}% win rate ({hv_total} setups)"
            )
        if ves_total > 0:
            print(
                f"  + Vol expanding (strict):         {ves_trended / ves_total * 100:.1f}% win rate ({ves_total} setups)"
            )

        print(
            f"\n  Best filter improvement: +{max(ve_trended / ve_total * 100, hv_trended / hv_total * 100 if hv_total > 0 else 0, ves_trended / ves_total * 100 if ves_total > 0 else 0) - all_trended / all_total * 100:.1f}%"
        )

        if hv_total > 0:
            print(
                f"\n  Overall improvement: +{hv_trended / hv_total * 100 - all_trended / all_total * 100:.1f}%"
            )
            print(
                f"  Setups filtered out: {all_total - hv_total} ({100 * (all_total - hv_total) / all_total:.0f}%)"
            )


def avg(lst):
    """Simple average helper"""
    return sum(lst) / len(lst) if lst else 0


if __name__ == "__main__":
    backtest = ICCBacktestLearned()
    setups = backtest.run_backtest()
    backtest.analyze_results(setups)
