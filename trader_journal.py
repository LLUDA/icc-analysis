#!/usr/bin/env python3
"""
ICC TRADER'S JOURNAL - Self Learning
Analyzing why setups work and fail
Journalling for future reference
"""

import yfinance as yf
from datetime import datetime, timedelta
import json


class TraderJournal:
    """
    Self-learning journal for ICC analysis
    I need to understand:
    1. Why certain clues lead to wins
    2. Why certain clues lead to losses
    3. What patterns work in different conditions
    """

    def __init__(self):
        self.win_journal = []
        self.loss_journal = []
        self.learnings = {}

    def get_swings(self, highs, lows, lookback=5):
        swings_high = []
        swings_low = []
        for i in range(lookback, len(highs) - lookback):
            if highs[i] == max(highs[i - lookback : i + lookback + 1]):
                swings_high.append((i, highs[i]))
            if lows[i] == min(lows[i - lookback : i + lookback + 1]):
                swings_low.append((i, lows[i]))
        return swings_high, swings_low

    def analyze_setups(self, df, pair):
        """
        Analyze ALL setups - winners and losers
        For each, understand WHY
        """
        results = []

        highs = df["High"].values
        lows = df["Low"].values
        closes = df["Close"].values
        opens = df["Open"].values
        timestamps = df.index

        swings_high, swings_low = self.get_swings(highs, lows)

        for i in range(5, len(swings_low) - 10):
            low_idx, low_level = swings_low[i]

            if low_idx + 15 >= len(closes):
                continue

            # Get candles after break
            post = []
            for j in range(low_idx, min(low_idx + 20, len(closes))):
                post.append(
                    {
                        "time": timestamps[j],
                        "open": opens[j],
                        "high": highs[j],
                        "low": lows[j],
                        "close": closes[j],
                    }
                )

            # Analyze what happened
            outcome = self.analyze_outcome(post)
            clues = self.detect_clues(post, "SHORT")
            context = self.get_market_context(post)

            results.append(
                {
                    "pair": pair,
                    "type": "SHORT",
                    "level": low_level,
                    "outcome": outcome,
                    "clues": clues,
                    "context": context,
                    "candles": post[:10],
                }
            )

        return results

    def analyze_outcome(self, candles):
        """Determine if trade would have won or lost"""
        if len(candles) < 10:
            return "UNKNOWN"

        start = candles[0]["close"]
        end = candles[-1]["close"]
        movement = (start - end) / start * 100

        if movement > 1:  # Moved down > 1%
            return "WIN"
        elif movement < -1:  # Moved up > 1%
            return "LOSS"
        else:
            return "BREAKEVEN"

    def detect_clues(self, candles, direction):
        """Detect clues that were present"""
        clues = []

        highs = [c["high"] for c in candles]
        lows = [c["low"] for c in candles]
        closes = [c["close"] for c in candles]

        # Find swing highs and lows
        swing_highs = []
        swing_lows = []
        for i in range(2, len(highs) - 2):
            if highs[i] > highs[i - 1] and highs[i] > highs[i + 1]:
                swing_highs.append(highs[i])
            if lows[i] < lows[i - 1] and lows[i] < lows[i + 1]:
                swing_lows.append(lows[i])

        if direction == "SHORT":
            # Check for lower highs
            if len(swing_highs) >= 3:
                lh_count = sum(
                    1
                    for i in range(1, len(swing_highs))
                    if swing_highs[i] < swing_highs[i - 1]
                )
                if lh_count >= 2:
                    clues.append(f"LH:{lh_count}")

            # Check for lower lows
            if len(swing_lows) >= 3:
                ll_count = sum(
                    1
                    for i in range(1, len(swing_lows))
                    if swing_lows[i] < swing_lows[i - 1]
                )
                if ll_count >= 2:
                    clues.append(f"LL:{ll_count}")

        return " ".join(clues) if clues else "NONE"

    def get_market_context(self, candles):
        """Get context - volatility, volume proxy, range"""
        if len(candles) < 5:
            return "UNKNOWN"

        closes = [c["close"] for c in candles]
        highs = [c["high"] for c in candles]
        lows = [c["low"] for c in candles]

        # Calculate volatility
        returns = [
            (closes[i] - closes[i - 1]) / closes[i - 1] * 100
            for i in range(1, len(closes))
        ]
        avg_return = sum(abs(r) for r in returns) / len(returns)

        # Calculate range
        total_range = sum(h - l for h, l in zip(highs, lows)) / len(highs)
        avg_price = sum(closes) / len(closes)
        volatility = total_range / avg_price * 100

        if volatility > 1.5:
            vol_context = "HIGH_VOL"
        elif volatility > 0.8:
            vol_context = "MED_VOL"
        else:
            vol_context = "LOW_VOL"

        return vol_context

    def journal_learning(self, results):
        """
        Analyze results and journal learnings
        This is for MY future reference
        """

        # Separate wins and losses
        wins = [r for r in results if r["outcome"] == "WIN"]
        losses = [r for r in results if r["outcome"] == "LOSS"]

        print("\n" + "=" * 70)
        print("  TRADERS JOURNAL - SELF LEARNING")
        print("=" * 70)

        # WIN ANALYSIS
        print("\n📈 WHY WINS HAPPENED:")
        print("-" * 50)

        win_clues = {}
        win_context = {}

        for w in wins:
            clue = w["clues"]
            ctx = w["context"]
            win_clues[clue] = win_clues.get(clue, 0) + 1
            win_context[ctx] = win_context.get(ctx, 0) + 1

        # Most common clues in wins
        print("\nMost common clues in WINNING setups:")
        for clue, count in sorted(win_clues.items(), key=lambda x: -x[1])[:5]:
            pct = count / len(wins) * 100
            print(f"  {clue}: {count} ({pct:.0f}%)")

        print("\nMarket context in WINNING setups:")
        for ctx, count in sorted(win_context.items(), key=lambda x: -x[1]):
            pct = count / len(wins) * 100
            print(f"  {ctx}: {count} ({pct:.0f}%)")

        # LOSS ANALYSIS
        print("\n📉 WHY LOSSES HAPPENED:")
        print("-" * 50)

        loss_clues = {}
        loss_context = {}

        for l in losses:
            clue = l["clues"]
            ctx = l["context"]
            loss_clues[clue] = loss_clues.get(clue, 0) + 1
            loss_context[ctx] = loss_context.get(ctx, 0) + 1

        # Most common clues in losses
        print("\nMost common clues in LOSING setups:")
        for clue, count in sorted(loss_clues.items(), key=lambda x: -x[1])[:5]:
            pct = count / len(losses) * 100
            print(f"  {clue}: {count} ({pct:.0f}%)")

        print("\nMarket context in LOSING setups:")
        for ctx, count in sorted(loss_context.items(), key=lambda x: -x[1]):
            pct = count / len(losses) * 100
            print(f"  {ctx}: {count} ({pct:.0f}%)")

        # KEY LEARNINGS
        print("\n" + "=" * 70)
        print("  KEY LEARNINGS FOR FUTURE")
        print("=" * 70)

        # Compare clues
        print("\n🔍 CLUE EFFECTIVENESS:")
        all_clues = set(list(win_clues.keys()) + list(loss_clues.keys()))

        clue_analysis = []
        for clue in all_clues:
            w = win_clues.get(clue, 0)
            l = loss_clues.get(clue, 0)
            total = w + l
            if total >= 10:  # Only analyze if enough data
                win_rate = w / total * 100
                clue_analysis.append((clue, w, l, win_rate))

        clue_analysis.sort(key=lambda x: -x[3])

        print("\nClues ranked by win rate:")
        for clue, w, l, wr in clue_analysis[:10]:
            print(f"  {clue}: {wr:.0f}% WR ({w}W/{l}L)")

        # What clues to AVOID
        print("\n⚠️ CLUES TO BE CAREFUL WITH:")
        for clue, w, l, wr in clue_analysis[-5:]:
            if w + l >= 10:
                print(f"  {clue}: {wr:.0f}% WR ({w}W/{l}L)")

        # Context effectiveness
        print("\n📊 CONTEXT EFFECTIVENESS:")
        ctx_analysis = []
        all_ctx = set(list(win_context.keys()) + list(loss_context.keys()))

        for ctx in all_ctx:
            w = win_context.get(ctx, 0)
            l = loss_context.get(ctx, 0)
            total = w + l
            if total >= 20:
                win_rate = w / total * 100
                ctx_analysis.append((ctx, w, l, win_rate))

        ctx_analysis.sort(key=lambda x: -x[3])

        for ctx, w, l, wr in ctx_analysis:
            print(f"  {ctx}: {wr:.0f}% WR ({w}W/{l}L)")

        return {
            "wins": len(wins),
            "losses": len(losses),
            "clue_analysis": clue_analysis,
            "context_analysis": ctx_analysis,
        }


def main():
    pairs = ["GBPCAD=X", "GBPUSD=X", "EURUSD=X", "USDJPY=X"]

    journal = TraderJournal()
    all_results = []

    print("Analyzing historical setups...")

    for pair in pairs:
        try:
            print(f"  {pair}...")
            df = yf.Ticker(pair).history(period="2y", interval="4h")

            if len(df) > 200:
                results = journal.analyze_setups(df, pair)
                all_results.extend(results)
        except:
            pass

    if all_results:
        analysis = journal.journal_learning(all_results)

        # Save journal for future reference
        print("\n\n" + "=" * 70)
        print("  JOURNAL SAVED FOR FUTURE REFERENCE")
        print("=" * 70)


if __name__ == "__main__":
    main()
