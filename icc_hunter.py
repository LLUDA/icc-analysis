#!/usr/bin/env python3
"""
ICC HUNTER - Trading Analysis Framework
Not just "what is" - but "what happened" and "what's next"
Detects breaks, tells the story, finds retracement zones
"""

import yfinance as yf
import sys
from datetime import datetime, timedelta


class ICCHunter:
    """Hunts for ICC setups by reading the full story"""

    def __init__(self, symbol):
        self.symbol = symbol
        self.ticker = yf.Ticker(symbol)
        self.data = {}
        self.story = {}
        self.breaks = {}
        self.zones = {}

    def fetch_data(self):
        """Get data from multiple timeframes"""
        try:
            self.data["daily"] = self.ticker.history(period="90d", interval="1d")
            self.data["4h"] = self.ticker.history(period="30d", interval="4h")
            self.data["1h"] = self.ticker.history(period="5d", interval="1h")
            self.data["15m"] = self.ticker.history(period="2d", interval="15m")
            return True
        except Exception as e:
            print(f"Error fetching data: {e}")
            return False

    def get_swings(self, highs, lows, lookback=5):
        """Find swing highs and lows with their positions"""
        swings_high = []
        swings_low = []

        for i in range(lookback, len(highs) - lookback):
            if highs[i] == max(highs[i - lookback : i + lookback + 1]):
                swings_high.append((i, highs[i]))
            if lows[i] == min(lows[i - lookback : i + lookback + 1]):
                swings_low.append((i, lows[i]))

        return swings_high, swings_low

    def detect_breaks(self, df, tf_name):
        """Detect when price broke key levels - THIS IS THE INDICATION"""
        highs = df["High"].values
        lows = df["Low"].values
        closes = df["Close"].values
        current = closes[-1]

        swings_high, swings_low = self.get_swings(highs, lows)

        breaks = {
            "bullish_breaks": [],  # Price broke above resistance
            "bearish_breaks": [],  # Price broke below support
            "rejections": [],  # Tried to break but failed
        }

        if len(swings_high) >= 2 and len(swings_low) >= 2:
            # Check if current price broke recent swings
            recent_highs = [h[1] for h in swings_high[-3:]]
            recent_lows = [l[1] for l in swings_low[-3:]]

            # Check for breaks above recent highs
            for i, high in enumerate(recent_highs[:-1]):
                if closes[-1] > high:
                    breaks["bullish_breaks"].append(
                        {
                            "level": high,
                            "type": "HH" if i == 0 else "earlier_high",
                            "tf": tf_name,
                        }
                    )

            # Check for breaks below recent lows
            for i, low in enumerate(recent_lows[:-1]):
                if closes[-1] < low:
                    breaks["bearish_breaks"].append(
                        {
                            "level": low,
                            "type": "LL" if i == 0 else "earlier_low",
                            "tf": tf_name,
                        }
                    )

        return breaks

    def read_story(self, df, tf_name):
        """Tell the story of what happened on this timeframe"""
        highs = df["High"].values
        lows = df["Low"].values
        closes = df["Close"].values
        opens = df["Open"].values
        current = closes[-1]

        swings_high, swings_low = self.get_swings(highs, lows)

        story = {
            "phase": None,  # ACCUMULATION, BREAK, CONTINUATION, DISTRIBUTION
            "narrative": "",
            "bullish_signals": [],
            "bearish_signals": [],
            "key_levels": [],
        }

        if len(swings_high) >= 2 and len(swings_low) >= 2:
            hh = swings_high[-1][1] > swings_high[-2][1]
            hl = swings_low[-1][1] > swings_low[-2][1]
            lh = swings_high[-1][1] < swings_high[-2][1]
            ll = swings_low[-1][1] < swings_low[-2][1]

            # Determine the story
            if hh and hl:
                story["phase"] = "UPTREND"
                story["narrative"] = "Higher highs and higher lows - buyers in control"
                story["bullish_signals"].append("HH/HL confirmed")
            elif lh and ll:
                story["phase"] = "DOWNTREND"
                story["narrative"] = "Lower highs and lower lows - sellers in control"
                story["bearish_signals"].append("LH/LL confirmed")
            elif hh or hl:
                story["phase"] = "PULLBACK"
                story["narrative"] = (
                    "Partial bullish structure - could be pullback before continuation"
                )
                story["bullish_signals"].append(
                    "Partial HH/HL - watching for completion"
                )
            elif lh or ll:
                story["phase"] = "PULLBACK"
                story["narrative"] = (
                    "Partial bearish structure - could be pullback before continuation"
                )
                story["bearish_signals"].append(
                    "Partial LH/LL - watching for completion"
                )
            else:
                story["phase"] = "RANGE"
                story["narrative"] = "Ranging - no clear direction"

        # Check for momentum
        if len(closes) >= 20:
            recent_20 = closes[-20:]
            up_moves = sum(
                1 for i in range(1, len(recent_20)) if recent_20[i] > recent_20[i - 1]
            )

            if up_moves >= 15:
                story["bullish_signals"].append(
                    f"Strong upward momentum ({up_moves}/20 candles up)"
                )
            elif up_moves <= 5:
                story["bearish_signals"].append(
                    f"Strong downward momentum ({20 - up_moves}/20 candles down)"
                )

        # Check for candle patterns suggesting rejection
        if len(closes) >= 2:
            last_wick = highs[-1] - lows[-1]
            body = abs(closes[-1] - opens[-1])

            # Long wick on one side = rejection
            if lows[-1] < min(opens[-1], closes[-1]) and last_wick > body * 2:
                story["bullish_signals"].append(
                    f"Bullish rejection - wick below {((lows[-1] / closes[-1]) - 1) * 100:.2f}%"
                )
            if highs[-1] > max(opens[-1], closes[-1]) and last_wick > body * 2:
                story["bearish_signals"].append(
                    f"Bearish rejection - wick above +{((highs[-1] / closes[-1]) - 1) * 100:.2f}%"
                )

        return story

    def calculate_retracement_zones(self, df, direction):
        """Calculate where price might pull back for entry"""
        highs = df["High"].values
        lows = df["Low"].values
        closes = df["Close"].values
        current = closes[-1]

        swings_high, swings_low = self.get_swings(highs, lows)

        zones = []

        if len(swings_high) >= 2 and len(swings_low) >= 2:
            if direction == "SHORT":
                # For shorts - calculate retracement from lows (where shorts broke)
                recent_lows = [l[1] for l in swings_low[-3:]]
                recent_highs = [h[1] for h in swings_high[-3:]]

                if recent_lows:
                    swing_low = min(recent_lows)
                    swing_high = max(recent_highs) if recent_highs else current

                    # Fibonacci retracement levels from swing low
                    diff = swing_high - swing_low
                    for fib in [0.382, 0.5, 0.618, 0.786]:
                        zone = swing_low + (diff * fib)
                        dist = (zone - current) / current * 100
                        if abs(dist) < 5:  # Within 5% of current
                            zones.append(
                                {
                                    "level": zone,
                                    "type": f"{int(fib * 100)}% retracement",
                                    "distance": dist,
                                    "direction": "SHORT",
                                }
                            )

            elif direction == "LONG":
                # For longs - calculate retracement from highs (where longs broke)
                recent_highs = [h[1] for h in swings_high[-3:]]
                recent_lows = [l[1] for l in swings_low[-3:]]

                if recent_highs:
                    swing_high = max(recent_highs)
                    swing_low = min(recent_lows) if recent_lows else current

                    # Fibonacci retracement levels from swing high
                    diff = swing_high - swing_low
                    for fib in [0.382, 0.5, 0.618, 0.786]:
                        zone = swing_high - (diff * fib)
                        dist = (current - zone) / current * 100
                        if abs(dist) < 5:
                            zones.append(
                                {
                                    "level": zone,
                                    "type": f"{int(fib * 100)}% retracement",
                                    "distance": dist,
                                    "direction": "LONG",
                                }
                            )

        return sorted(zones, key=lambda x: abs(x["distance"]))

    def analyze(self):
        """Full ICC analysis - the hunter's report"""
        if not self.fetch_data():
            return None

        current = float(self.data["daily"]["Close"].iloc[-1])

        print("=" * 70)
        print(f"  🎯 ICC HUNTER - {self.symbol.upper()}")
        print(f"  Price: {current:.5f}")
        print("=" * 70)

        # Analyze each timeframe
        all_stories = {}
        all_breaks = {}
        all_zones = {"LONG": [], "SHORT": []}

        for tf_name, df in [
            ("DAILY", self.data["daily"]),
            ("4H", self.data["4h"]),
            ("1H", self.data["1h"]),
            ("15M", self.data["15m"]),
        ]:
            if len(df) > 20:
                story = self.read_story(df, tf_name)
                breaks = self.detect_breaks(df, tf_name)

                all_stories[tf_name] = story
                all_breaks[tf_name] = breaks

                # Calculate zones for each direction
                for direction in ["LONG", "SHORT"]:
                    zones = self.calculate_retracement_zones(df, direction)
                    all_zones[direction].extend(zones)

        # Determine the OVERALL story
        bullish_count = sum(
            1
            for s in all_stories.values()
            if s["phase"] in ["UPTREND", "PULLBACK"] and s["bullish_signals"]
        )
        bearish_count = sum(
            1
            for s in all_stories.values()
            if s["phase"] in ["DOWNTREND", "PULLBACK"] and s["bearish_signals"]
        )

        # Collect all breaks
        all_bullish_breaks = []
        all_bearish_breaks = []
        for tf, breaks in all_breaks.items():
            all_bullish_breaks.extend([(b, tf) for b in breaks["bullish_breaks"]])
            all_bearish_breaks.extend([(b, tf) for b in breaks["bearish_breaks"]])

        # Determine direction
        if bullish_count > bearish_count:
            direction = "LONG"
        elif bearish_count > bullish_count:
            direction = "SHORT"
        else:
            direction = "NEUTRAL"

        # Calculate probability
        probability = self.calculate_probability(all_stories, all_breaks, direction)

        print(f"\n📊 THE STORY:")
        print("-" * 70)

        # Tell the story from each timeframe
        for tf_name, story in all_stories.items():
            if story["narrative"]:
                phase_icon = (
                    "📈"
                    if story["phase"] == "UPTREND"
                    else "📉"
                    if story["phase"] == "DOWNTREND"
                    else "↔️"
                )
                print(f"  {tf_name}: {phase_icon} {story['phase']}")
                print(f"         {story['narrative']}")

        print(f"\n🎯 RECOMMENDED ACTION: {direction} ({probability}%)")

        # Report breaks (THE INDICATION)
        print(f"\n⚡ THE INDICATION (Breaks):")
        print("-" * 70)

        if all_bullish_breaks:
            print(f"  🟢 BULLISH BREAKS:")
            for break_info, tf in all_bullish_breaks[:3]:
                print(
                    f"     • Broke above {break_info['level']:.5f} ({tf}) - {break_info['type']}"
                )

        if all_bearish_breaks:
            print(f"  🔴 BEARISH BREAKS:")
            for break_info, tf in all_bearish_breaks[:3]:
                print(
                    f"     • Broke below {break_info['level']:.5f} ({tf}) - {break_info['type']}"
                )

        if not all_bullish_breaks and not all_bearish_breaks:
            print(f"  ⏳ No breaks detected - watching for indication")

        # Report retracement zones (CONTINUATION ENTRY)
        print(f"\n📍 CONTINUATION ENTRY ZONES ({direction}):")
        print("-" * 70)

        zones = all_zones.get(direction, [])
        if zones:
            for zone in zones[:5]:
                action = "🚀 READY" if abs(zone["distance"]) < 0.5 else "⏳ Waiting"
                print(
                    f"  {action} {zone['type']} at {zone['level']:.5f} ({zone['distance']:+.2f}%)"
                )
        else:
            print(f"  No clear retracement zones - may need to wait")

        # Entry setup if we have breaks
        if direction == "SHORT" and all_bearish_breaks:
            entry_zone = all_bearish_breaks[0][0]["level"]
            print(f"\n💡 ICC SETUP:")
            print("-" * 70)
            print(f"  Type: BREAK & CONTINUATION (SHORT)")
            print(f"  What happened: Price broke below {entry_zone:.5f}")
            print(f"  Waiting for: Retracement back up")
            print(f"  Entry zone: {entry_zone * 0.998:.5f} - {entry_zone * 1.002:.5f}")
            print(f"  Stop: Above recent high")
            print(f"  Target: Next support level")

        elif direction == "LONG" and all_bullish_breaks:
            entry_zone = all_bullish_breaks[0][0]["level"]
            print(f"\n💡 ICC SETUP:")
            print("-" * 70)
            print(f"  Type: BREAK & CONTINUATION (LONG)")
            print(f"  What happened: Price broke above {entry_zone:.5f}")
            print(f"  Waiting for: Retracement back down")
            print(f"  Entry zone: {entry_zone * 0.998:.5f} - {entry_zone * 1.002:.5f}")
            print(f"  Stop: Below recent low")
            print(f"  Target: Next resistance level")

        print("\n" + "=" * 70)

        return {
            "direction": direction,
            "probability": probability,
            "breaks": {"bullish": all_bullish_breaks, "bearish": all_bearish_breaks},
            "zones": all_zones,
            "current": current,
        }

    def calculate_probability(self, stories, breaks, direction):
        """Calculate probability based on the full picture"""
        score = 50  # Base

        # Structure alignment
        aligned_count = 0
        for tf, story in stories.items():
            if direction == "LONG" and story["bullish_signals"]:
                aligned_count += 1
            elif direction == "SHORT" and story["bearish_signals"]:
                aligned_count += 1

        score += min(30, aligned_count * 7)  # Up to 30 bonus

        # Break confirmation (major boost)
        if direction == "LONG" and breaks:
            bullish_breaks = sum(len(b["bullish_breaks"]) for b in breaks.values())
            score += min(20, bullish_breaks * 10)  # Up to 20 bonus
        elif direction == "SHORT" and breaks:
            bearish_breaks = sum(len(b["bearish_breaks"]) for b in breaks.values())
            score += min(20, bearish_breaks * 10)

        return min(95, max(40, score))


def scan_watchlist():
    """Scan the full watchlist and report opportunities"""
    watchlist = [
        ("USDJPY=X", "GBPUSD=X", "EURJPY=X", "EURUSD=X", "GC=F", "BTC-USD", "^DJI")
    ]

    print("\n" + "=" * 70)
    print("  🔍 ICC HUNTER - WATCHLIST SCAN")
    print("=" * 70 + "\n")

    results = []

    for symbol in watchlist[0]:
        hunter = ICCHunter(symbol)
        result = hunter.analyze()
        if result:
            results.append((symbol, result))
        print("\n")

    # Summary
    print("=" * 70)
    print("  📋 SCAN SUMMARY - HOTTEST SETUPS")
    print("=" * 70)

    setups = []
    for symbol, result in results:
        if result["direction"] != "NEUTRAL":
            setups.append(
                (symbol, result["direction"], result["probability"], result["breaks"])
            )

    setups.sort(key=lambda x: x[2], reverse=True)

    for symbol, direction, prob, breaks in setups:
        break_type = ""
        if direction == "SHORT" and breaks["bearish"]:
            break_type = f" broke {breaks['bearish'][0][0]['level']:.4f}"
        elif direction == "LONG" and breaks["bullish"]:
            break_type = f" broke {breaks['bullish'][0][0]['level']:.4f}"

        fire = "🔥" if prob >= 70 else "⚡" if prob >= 60 else "📊"
        print(f"  {fire} {symbol:12} {direction:6} {prob}%{break_type}")

    print("\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("ICC HUNTER - Trading Analysis")
        print("Usage:")
        print("  python icc_hunter.py SCAN           - Scan full watchlist")
        print("  python icc_hunter.py <SYMBOL>        - Analyze single symbol")
        print("  python icc_hunter.py EURJPY=X       - Example")
        sys.exit(1)

    command = sys.argv[1].upper()

    if command == "SCAN":
        scan_watchlist()
    else:
        symbol = command if "=" in command or "-" in command else command
        hunter = ICCHunter(symbol)
        hunter.analyze()
