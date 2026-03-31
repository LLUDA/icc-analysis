#!/usr/bin/env python3
"""
ICC BACKTEST - 2 Years of Data
Tests: Break → Correction → Continuation logic
Session-aware analysis
"""

import yfinance as yf
import sys
from datetime import datetime, timedelta
import json


class ICCBacktest:
    """Backtest ICC logic on historical data"""

    def __init__(self):
        self.results = {}
        self.trades = []

        # Session times (UTC)
        self.sessions = {
            "LONDON": (8, 17),
            "NY": (13, 22),
            "TOKYO": (0, 9),
            "OVERLAP": (13, 17),  # London + NY
        }

        # Pairs and their primary sessions
        self.pairs = {
            "GBPCAD=X": ["LONDON"],
            "GBPUSD=X": ["LONDON"],
            "GBPJPY=X": ["LONDON", "TOKYO"],
            "EURJPY=X": ["LONDON", "TOKYO"],
            "USDJPY=X": ["NY", "TOKYO"],
            "EURUSD=X": ["NY", "LONDON"],
            "XAUUSD=X": ["LONDON", "NY"],
            "BTC-USD": ["24H"],
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

    def get_session(self, timestamp):
        """Get active session from timestamp"""
        hour = timestamp.hour

        sessions = []
        if 8 <= hour < 17:
            sessions.append("LONDON")
        if 13 <= hour < 22:
            sessions.append("NY")
        if 0 <= hour < 9:
            sessions.append("TOKYO")
        if 13 <= hour < 17:
            sessions.append("OVERLAP")

        return sessions if sessions else ["QUIET"]

    def analyze_candle_pattern(self, candles, direction):
        """
        Analyze if price continued or ranged after break
        Returns: 'TRENDED', 'RANGED', 'REVERSED'
        """
        if len(candles) < 5:
            return "UNKNOWN"

        # Calculate range and movement
        opens = [c["open"] for c in candles]
        closes = [c["close"] for c in candles]
        highs = [c["high"] for c in candles]
        lows = [c["low"] for c in candles]

        start_price = opens[0]
        end_price = closes[-1]
        movement = abs(end_price - start_price) / start_price * 100

        # Calculate volatility (range)
        avg_range = sum(h - l for h, l in zip(highs, lows)) / len(candles)
        avg_price = sum(closes) / len(closes)
        volatility = (avg_range / avg_price) * 100

        # Check if price ranged (didn't move much)
        if movement < volatility * 0.5:
            return "RANGED"

        # Check if price moved in expected direction
        if direction == "LONG" and end_price > start_price:
            return "TRENDED"
        if direction == "SHORT" and end_price < start_price:
            return "TRENDED"

        # Moved opposite = reversed
        return "REVERSED"

    def find_icc_setups(self, df, pair):
        """
        Find ICC setups in historical data
        Look for: Break → Correction → Continuation
        """
        setups = []

        highs = df["High"].values
        lows = df["Low"].values
        closes = df["Close"].values
        opens = df["Open"].values
        timestamps = df.index

        # Get swings on 4H
        swings_high, swings_low = self.get_swings(highs, lows, lookback=5)

        if len(swings_high) < 3 or len(swings_low) < 3:
            return setups

        # Find breaks of structure
        for i in range(10, len(swings_low) - 2):
            # Check for bearish break (broke below a swing low)
            current_idx = swings_low[i][0]
            broken_level = swings_low[i][1]

            # Price after this low
            if current_idx + 2 >= len(closes):
                continue

            # Get candles after the break
            post_break = []
            for j in range(current_idx, min(current_idx + 20, len(closes))):
                post_break.append(
                    {
                        "open": opens[j],
                        "high": highs[j],
                        "low": lows[j],
                        "close": closes[j],
                        "time": timestamps[j],
                    }
                )

            # Analyze what happened after break
            outcome = self.analyze_candle_pattern(post_break, "SHORT")

            # Get session
            session = self.get_session(timestamps[current_idx])

            setups.append(
                {
                    "type": "BREAK_DOWN",
                    "level": broken_level,
                    "time": timestamps[current_idx],
                    "session": session,
                    "pair": pair,
                    "outcome": outcome,
                    "post_break_candles": post_break[:10],  # Store 10 candles after
                }
            )

        return setups

    def run_backtest(self, pair, period="2y"):
        """Run backtest on a single pair"""
        print(f"  Testing {pair}...")

        try:
            ticker = yf.Ticker(pair)
            df = ticker.history(period=period, interval="4h")
        except:
            return []

        if len(df) < 100:
            return []

        setups = self.find_icc_setups(df, pair)
        return setups

    def run_all(self):
        """Run backtest on all pairs"""
        print("=" * 70)
        print("  ICC BACKTEST - 2 YEARS")
        print("=" * 70)

        all_setups = []

        for pair in self.pairs.keys():
            try:
                ticker = yf.Ticker(pair)
                df = ticker.history(period="2y", interval="4h")

                if len(df) < 100:
                    print(f"  {pair}: Not enough data")
                    continue

                setups = self.find_icc_setups(df, pair)
                all_setups.extend(setups)
                print(f"  {pair}: Found {len(setups)} setups")

            except Exception as e:
                print(f"  {pair}: Error - {e}")

        return all_setups

    def analyze_results(self, setups):
        """Analyze backtest results"""
        print("\n" + "=" * 70)
        print("  BACKTEST RESULTS")
        print("=" * 70)

        if not setups:
            print("  No setups found")
            return

        total = len(setups)

        # By outcome
        outcomes = {}
        for s in setups:
            outcome = s["outcome"]
            outcomes[outcome] = outcomes.get(outcome, 0) + 1

        print(f"\n📊 BY OUTCOME:")
        print(f"  Total setups: {total}")
        for outcome, count in sorted(outcomes.items(), key=lambda x: -x[1]):
            pct = count / total * 100
            print(f"  {outcome}: {count} ({pct:.1f}%)")

        # By session
        print(f"\n📊 BY SESSION:")
        by_session = {}
        for s in setups:
            for session in s["session"]:
                if session not in by_session:
                    by_session[session] = {
                        "total": 0,
                        "trended": 0,
                        "ranged": 0,
                        "reversed": 0,
                    }
                by_session[session]["total"] += 1
                by_session[session][s["outcome"].lower()] += 1

        for session, data in sorted(by_session.items(), key=lambda x: -x[1]["total"]):
            total = data["total"]
            trended = data["trended"]
            ranged = data["ranged"]
            reversed = data["reversed"]

            win_rate = trended / total * 100 if total > 0 else 0
            print(f"\n  {session}:")
            print(f"    Total: {total}")
            print(f"    Trended: {trended} ({trended / total * 100:.1f}%)")
            print(f"    Ranged: {ranged} ({ranged / total * 100:.1f}%)")
            print(f"    Reversed: {reversed} ({reversed / total * 100:.1f}%)")
            print(f"    Win Rate (if trading continuation): {win_rate:.1f}%")

        # By pair
        print(f"\n📊 BY PAIR:")
        by_pair = {}
        for s in setups:
            pair = s["pair"]
            if pair not in by_pair:
                by_pair[pair] = {"total": 0, "trended": 0, "ranged": 0, "reversed": 0}
            by_pair[pair]["total"] += 1
            by_pair[pair][s["outcome"].lower()] += 1

        for pair, data in sorted(by_pair.items(), key=lambda x: -x[1]["total"]):
            total = data["total"]
            trended = data["trended"]
            ranged = data["ranged"]

            if total >= 5:  # Only show pairs with enough data
                win_rate = trended / total * 100 if total > 0 else 0
                print(
                    f"  {pair:15} Total: {total:3} | Trended: {trended:3} ({win_rate:.0f}%) | Ranged: {ranged:3}"
                )

        # Best sessions for trading
        print(f"\n📊 BEST SESSIONS FOR TRADING:")
        best_sessions = []
        for session, data in by_session.items():
            if data["total"] >= 10:
                win_rate = data["trended"] / data["total"] * 100
                best_sessions.append((session, win_rate, data["total"]))

        best_sessions.sort(key=lambda x: -x[1])
        for session, win_rate, total in best_sessions[:5]:
            print(f"  {session:10} Win Rate: {win_rate:.1f}% ({total} trades)")

        return setups


def main():
    backtest = ICCBacktest()
    setups = backtest.run_all()
    backtest.analyze_results(setups)


if __name__ == "__main__":
    main()
