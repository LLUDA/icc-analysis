#!/usr/bin/env python3
"""
ICC HUNTER v2 - Based on Steven's Timeframe Hierarchy
DAILY = Trend & Zones | 4H = Indication (Break) | 1H = Entry Reason
"""

import yfinance as yf
import sys
from datetime import datetime, timedelta


class ICCHunter:
    """Hunts ICC setups using proper timeframe hierarchy"""

    def __init__(self, symbol):
        self.symbol = symbol
        self.ticker = yf.Ticker(symbol)
        self.data = {}

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

    def get_major_swings(self, highs, lows, lookback=5):
        """Find major swing highs and lows"""
        swings_high = []
        swings_low = []

        for i in range(lookback, len(highs) - lookback):
            if highs[i] == max(highs[i - lookback : i + lookback + 1]):
                swings_high.append((i, highs[i]))
            if lows[i] == min(lows[i - lookback : i + lookback + 1]):
                swings_low.append((i, lows[i]))

        return swings_high, swings_low

    def analyze_trend(self, df):
        """DAILY: Identify trend and structure"""
        highs = df["High"].values
        lows = df["Low"].values
        closes = df["Close"].values
        current = closes[-1]

        swings_high, swings_low = self.get_major_swings(highs, lows)

        result = {
            "trend": "RANGE",
            "hh_count": 0,
            "hl_count": 0,
            "lh_count": 0,
            "ll_count": 0,
            "swing_highs": [],
            "swing_lows": [],
            "optimal_zone": None,
            "narrative": "",
        }

        if len(swings_high) >= 2 and len(swings_low) >= 2:
            # Get recent swings
            recent_highs = [h[1] for h in swings_high[-4:]]
            recent_lows = [l[1] for l in swings_low[-4:]]

            result["swing_highs"] = recent_highs
            result["swing_lows"] = recent_lows

            # Count HH, HL, LH, LL
            for i in range(1, len(recent_highs)):
                if recent_highs[i] > recent_highs[i - 1]:
                    result["hh_count"] += 1
                else:
                    result["lh_count"] += 1

            for i in range(1, len(recent_lows)):
                if recent_lows[i] > recent_lows[i - 1]:
                    result["hl_count"] += 1
                else:
                    result["ll_count"] += 1

            # Determine trend
            if (
                result["hh_count"] > result["lh_count"]
                and result["hl_count"] > result["ll_count"]
            ):
                result["trend"] = "UPTREND"
                result["narrative"] = (
                    f"Higher highs ({result['hh_count']}) and higher lows ({result['hl_count']})"
                )
                # Optimal zone = previous resistance that was broken
                if len(recent_highs) >= 3:
                    result["optimal_zone"] = {
                        "level": recent_highs[-2],
                        "type": "Previous resistance (broken)",
                        "direction": "LONG",
                    }
            elif (
                result["lh_count"] > result["hh_count"]
                and result["ll_count"] > result["hl_count"]
            ):
                result["trend"] = "DOWNTREND"
                result["narrative"] = (
                    f"Lower highs ({result['lh_count']}) and lower lows ({result['ll_count']})"
                )
                # Optimal zone = previous support that was broken
                if len(recent_lows) >= 3:
                    result["optimal_zone"] = {
                        "level": recent_lows[-2],
                        "type": "Previous support (broken)",
                        "direction": "SHORT",
                    }
            else:
                result["trend"] = "PULLBACK"
                result["narrative"] = (
                    "Mixed structure - could be pullback in existing trend"
                )

        return result

    def detect_indication(self, df):
        """
        TF2: Detect the INDICATION

        The INDICATION = BREAK of structure level
        Sequence: BREAK → RETRACEMENT → CONTINUATION

        The retracement IS part of the story, not a conflict.
        We look for price to break a level, then pull back, then continue.
        """
        highs = df["High"].values
        lows = df["Low"].values
        closes = df["Close"].values
        current = closes[-1]

        swings_high, swings_low = self.get_major_swings(highs, lows)

        result = {
            "has_break": False,
            "break_level": None,
            "break_direction": None,
            "in_retracement": False,
            "continuation_ready": False,
            "continuation_zone": None,
            "target": None,
            "narrative": "",
            "phase": None,  # BREAK, RETRACEMENT, or CONTINUATION
        }

        if len(swings_high) >= 3 and len(swings_low) >= 3:
            recent_highs = [h[1] for h in swings_high[-4:]]
            recent_lows = [l[1] for l in swings_low[-4:]]

            # Find the swing sequence
            # For bearish: we want to see a break below a low, then potentially a retracement up, then continuation down
            # For bullish: we want to see a break above a high, then potentially a retracement down, then continuation up

            # Check if current price is near recent structure levels
            last_high = recent_highs[-1]
            last_low = recent_lows[-1]
            prev_high = recent_highs[-2] if len(recent_highs) >= 2 else None
            prev_low = recent_lows[-2] if len(recent_lows) >= 2 else None

            # Calculate range
            if prev_high and prev_low:
                range_high = max(prev_high, last_high)
                range_low = min(prev_low, last_low)
                range_mid = (range_high + range_low) / 2

                # Is price near a broken level?
                # For bearish continuation: price should be BELOW the broken low
                # After break, price often retraces UP toward the broken level

                # Check if this looks like a bearish setup
                if current < prev_low:
                    # Price broke below previous low
                    result["has_break"] = True
                    result["break_direction"] = "BEARISH"
                    result["break_level"] = prev_low

                    # Is price retracing UP toward the broken level?
                    if current > range_mid:
                        result["in_retracement"] = True
                        result["phase"] = "RETRACEMENT"
                        result["narrative"] = (
                            f"Break below {prev_low:.5f} - Price retracing UP toward broken level"
                        )
                        result["continuation_zone"] = {
                            "level": prev_low,
                            "zone": f"{prev_low * 0.998:.5f} - {prev_low * 1.002:.5f}",
                        }
                    else:
                        # Price continuing down = continuation
                        result["continuation_ready"] = True
                        result["phase"] = "CONTINUATION"
                        result["narrative"] = (
                            f"Continuation: Price holding below broken level {prev_low:.5f}"
                        )

                    # Calculate target (where price first moved from this level)
                    swing_range = (
                        last_high - last_low if last_high and last_low else None
                    )
                    if swing_range:
                        result["target"] = last_low - swing_range

                # Check if this looks like a bullish setup
                elif current > prev_high:
                    result["has_break"] = True
                    result["break_direction"] = "BULLISH"
                    result["break_level"] = prev_high

                    # Is price retracing DOWN toward the broken level?
                    if current < range_mid:
                        result["in_retracement"] = True
                        result["phase"] = "RETRACEMENT"
                        result["narrative"] = (
                            f"Break above {prev_high:.5f} - Price retracing DOWN toward broken level"
                        )
                        result["continuation_zone"] = {
                            "level": prev_high,
                            "zone": f"{prev_high * 0.998:.5f} - {prev_high * 1.002:.5f}",
                        }
                    else:
                        result["continuation_ready"] = True
                        result["phase"] = "CONTINUATION"
                        result["narrative"] = (
                            f"Continuation: Price holding above broken level {prev_high:.5f}"
                        )

                    swing_range = (
                        last_high - last_low if last_high and last_low else None
                    )
                    if swing_range:
                        result["target"] = last_high + swing_range

                else:
                    # Price between structure - could be building
                    result["phase"] = "BUILDING"
                    result["narrative"] = (
                        "Price between structure levels - watching for break"
                    )

            else:
                result["narrative"] = "Not enough structure data"
        else:
            result["narrative"] = "Not enough swing data for indication"

        return result

    def find_entry_reason(self, df):
        """1H/15M: Find entry reasons"""
        highs = df["High"].values
        lows = df["Low"].values
        closes = df["Close"].values
        opens = df["Open"].values
        current = closes[-1]

        result = {
            "bullish_signals": [],
            "bearish_signals": [],
            "near_zone": False,
            "zone_distance": 0,
        }

        if len(closes) >= 5:
            # Check for close above/below patterns
            last_close = closes[-1]
            prev_high = highs[-2]
            prev_low = lows[-2]

            # Close above previous high = bullish entry reason
            if last_close > prev_high:
                result["bullish_signals"].append(
                    f"Close above previous high ({prev_high:.5f})"
                )

            # Close below previous low = bearish entry reason
            if last_close < prev_low:
                result["bearish_signals"].append(
                    f"Close below previous low ({prev_low:.5f})"
                )

        # Check wicks/rejections
        if len(closes) >= 2:
            last_wick = highs[-1] - lows[-1]
            body = abs(closes[-1] - opens[-1])

            if lows[-1] < min(opens[-1], closes[-1]) and last_wick > body * 1.5:
                pct = ((lows[-1] / closes[-1]) - 1) * 100
                result["bullish_signals"].append(
                    f"Bullish rejection (wick to {pct:.2f}%)"
                )

            if highs[-1] > max(opens[-1], closes[-1]) and last_wick > body * 1.5:
                pct = ((highs[-1] / closes[-1]) - 1) * 100
                result["bearish_signals"].append(
                    f"Bearish rejection (wick to +{pct:.2f}%)"
                )

        return result

    def analyze(self, mode="swing"):
        """
        Full ICC analysis with proper timeframe hierarchy

        mode='swing': DAILY→4H→1H (Trend→Break→Entry)
        mode='day':   4H→1H→15M (Trend→Break→Entry)
        """
        if not self.fetch_data():
            return None

        current = float(self.data["daily"]["Close"].iloc[-1])

        print("=" * 70)
        print(f"  🎯 ICC HUNTER v2 - {self.symbol.upper()}")
        print(f"  Mode: {'📅 SWING' if mode == 'swing' else '📅 DAY TRADE'}")
        print(f"  Price: {current:.5f}")
        print("=" * 70)

        if mode == "swing":
            return self._analyze_swing(current)
        else:
            return self._analyze_daytrade(current)

    def _analyze_swing(self, current):
        """SWING: DAILY→4H→1H"""

        # STEP 1: DAILY - Trend & Structure
        daily = self.analyze_trend(self.data["daily"])

        print("\n📊 STEP 1: DAILY - THE MAP (Trend & Zones)")
        print("-" * 70)
        trend_icon = (
            "📈"
            if daily["trend"] == "UPTREND"
            else "📉"
            if daily["trend"] == "DOWNTREND"
            else "↔️"
        )
        print(f"  Trend: {trend_icon} {daily['trend']}")
        print(f"  {daily['narrative']}")

        if daily["optimal_zone"]:
            zone = daily["optimal_zone"]
            print(f"\n  🎯 OPTIMAL ZONE: {zone['level']:.5f}")
            print(f"     ({zone['type']})")

        # STEP 2: 4H - The Indication (BREAK → RETRACEMENT → CONTINUATION)
        indication_4h = self.detect_indication(self.data["4h"])

        print("\n⚡ STEP 2: 4H - THE INDICATION")
        print("-" * 70)

        if indication_4h["has_break"]:
            phase_icon = "🔴" if indication_4h["break_direction"] == "BEARISH" else "🟢"
            phase_label = indication_4h["phase"] or "BREAK"

            print(f"  {phase_icon} {phase_label}: {indication_4h['narrative']}")
            print(f"     Broken level: {indication_4h['break_level']:.5f}")

            if indication_4h["continuation_zone"]:
                cz = indication_4h["continuation_zone"]
                print(f"\n  📍 CONTINUATION ZONE: {cz['zone']}")
                print(f"     (Watch for price to re-enter this zone for entry)")

            if indication_4h["target"]:
                print(f"\n  🎯 TARGET: {indication_4h['target']:.5f}")

            if indication_4h["in_retracement"]:
                print(f"\n  ⏳ RETRACEMENT IN PROGRESS (Normal, expected)")
        else:
            print(f"  ⏳ {indication_4h['narrative']}")

        # Also check 1H for indication
        indication_1h = self.detect_indication(self.data["1h"])
        if indication_1h["has_break"]:
            phase_icon = "🔴" if indication_1h["break_direction"] == "BEARISH" else "🟢"
            print(f"\n  {phase_icon} 1H: {indication_1h['narrative']}")

        # STEP 3: 1H - Entry Reasons
        entry_1h = self.find_entry_reason(self.data["1h"])

        print("\n🎯 STEP 3: 1H - ENTRY REASONS")
        print("-" * 70)

        if entry_1h["bullish_signals"]:
            print(f"  🟢 BULLISH:")
            for sig in entry_1h["bullish_signals"]:
                print(f"     • {sig}")

        if entry_1h["bearish_signals"]:
            print(f"  🔴 BEARISH:")
            for sig in entry_1h["bearish_signals"]:
                print(f"     • {sig}")

        if not entry_1h["bullish_signals"] and not entry_1h["bearish_signals"]:
            print(f"  ⏳ No clear entry reason yet")

        # SUMMARY
        return self._summarize(daily, indication_4h, entry_1h, "SWING")

    def _analyze_daytrade(self, current):
        """DAY TRADE: 4H→1H→15M"""

        # STEP 1: 4H - Trend & Structure
        h4_trend = self.analyze_trend(self.data["4h"])

        print("\n📊 STEP 1: 4H - THE MAP (Trend & Zones)")
        print("-" * 70)
        trend_icon = (
            "📈"
            if h4_trend["trend"] == "UPTREND"
            else "📉"
            if h4_trend["trend"] == "DOWNTREND"
            else "↔️"
        )
        print(f"  Trend: {trend_icon} {h4_trend['trend']}")
        print(f"  {h4_trend['narrative']}")

        if h4_trend["optimal_zone"]:
            zone = h4_trend["optimal_zone"]
            print(f"\n  🎯 OPTIMAL ZONE: {zone['level']:.5f}")
            print(f"     ({zone['type']})")

        # STEP 2: 1H - The Indication (BREAK → RETRACEMENT → CONTINUATION)
        indication_1h = self.detect_indication(self.data["1h"])

        print("\n⚡ STEP 2: 1H - THE INDICATION")
        print("-" * 70)

        if indication_1h["has_break"]:
            phase_icon = "🔴" if indication_1h["break_direction"] == "BEARISH" else "🟢"
            phase_label = indication_1h["phase"] or "BREAK"

            print(f"  {phase_icon} {phase_label}: {indication_1h['narrative']}")
            print(f"     Broken level: {indication_1h['break_level']:.5f}")

            if indication_1h["continuation_zone"]:
                cz = indication_1h["continuation_zone"]
                print(f"\n  📍 CONTINUATION ZONE: {cz['zone']}")

            if indication_1h["target"]:
                print(f"\n  🎯 TARGET: {indication_1h['target']:.5f}")

            if indication_1h["in_retracement"]:
                print(f"\n  ⏳ RETRACEMENT IN PROGRESS")
        else:
            print(f"  ⏳ {indication_1h['narrative']}")

        # Also check 15M for indication
        indication_15m = self.detect_indication(self.data["15m"])
        if indication_15m["has_break"]:
            phase_icon = (
                "🔴" if indication_15m["break_direction"] == "BEARISH" else "🟢"
            )
            print(f"\n  {phase_icon} 15M: {indication_15m['narrative']}")

        # STEP 3: 15M - Entry Reasons
        entry_15m = self.find_entry_reason(self.data["15m"])

        print("\n🎯 STEP 3: 15M - ENTRY REASONS")
        print("-" * 70)

        if entry_15m["bullish_signals"]:
            print(f"  🟢 BULLISH:")
            for sig in entry_15m["bullish_signals"]:
                print(f"     • {sig}")

        if entry_15m["bearish_signals"]:
            print(f"  🔴 BEARISH:")
            for sig in entry_15m["bearish_signals"]:
                print(f"     • {sig}")

        if not entry_15m["bullish_signals"] and not entry_15m["bearish_signals"]:
            print(f"  ⏳ No clear entry reason yet")

        # SUMMARY
        return self._summarize(h4_trend, indication_1h, entry_15m, "DAY")

    def _summarize(self, trend_data, indication, entry_reasons, mode):
        """
        Generate setup summary

        THE ICC FLOW:
        1. TF1 (Trend): Identify trend direction
        2. TF2 (Indication): BREAK → RETRACEMENT → CONTINUATION
        3. TF3 (Entry): Price re-enters zone + entry reason

        The retracement is NOT a conflict - it's part of the story.
        """
        print("\n" + "=" * 70)
        print(f"  📋 ICC SETUP SUMMARY ({mode} TRADE)")
        print("=" * 70)

        trend = trend_data["trend"]
        direction = None
        probability = 0
        setup_type = None
        phase = indication.get("phase", None)

        # Determine direction from trend
        if trend == "UPTREND":
            direction = "LONG"
        elif trend == "DOWNTREND":
            direction = "SHORT"
        else:
            direction = (
                indication.get("break_direction") == "BULLISH" and "LONG" or "SHORT"
                if indication.get("has_break")
                else None
            )

        if not indication.get("has_break"):
            print("  ⏳ NO BREAK DETECTED")
            print(f"     Watching for break of structure on {mode} TF")
            return None

        # Calculate probability based on phase
        if indication.get("continuation_ready"):
            probability = 85
            setup_type = f"🚀 CONTINUATION READY - Enter when price holds below/above {indication['break_level']:.5f}"
        elif indication.get("in_retracement"):
            probability = 75
            setup_type = f"⏳ IN RETRACEMENT - Wait for price to return to zone {indication['break_level']:.5f}"
        elif phase == "BREAK":
            probability = 70
            setup_type = f"⚡ NEW BREAK - Watching for retracement then continuation"
        else:
            probability = 65
            setup_type = f"📊 BUILDING - Watching for setup to develop"

        print(f"\n  📖 THE STORY:")
        print(f"     TF1: {trend}")
        print(f"     TF2: {phase or 'Watching for break'}")
        print(f"     → {setup_type}")

        print(f"\n  🎯 ACTION: {direction}")
        print(f"  📊 PROBABILITY: {probability}%")

        if indication.get("continuation_zone"):
            cz = indication["continuation_zone"]
            print(f"\n  📍 ENTRY ZONE: {cz['zone']}")
            print(f"     (Price must return to this zone for entry)")

        if indication.get("target"):
            print(f"  🎯 TARGET: {indication['target']:.5f}")

        # Entry reason status
        if direction == "LONG" and entry_reasons.get("bullish_signals"):
            print(f"\n  ✅ ENTRY REASON: PRESENT")
            for sig in entry_reasons["bullish_signals"]:
                print(f"     • {sig}")
        elif direction == "SHORT" and entry_reasons.get("bearish_signals"):
            print(f"\n  ✅ ENTRY REASON: PRESENT")
            for sig in entry_reasons["bearish_signals"]:
                print(f"     • {sig}")
        else:
            print(f"\n  ⏳ ENTRY REASON: WAITING")
            print(f"     (Price must return to zone + give entry reason)")

        print("\n" + "=" * 70)

        return {
            "direction": direction,
            "probability": probability,
            "setup_type": setup_type,
            "trend": trend_data,
            "indication": indication,
            "entry_reasons": entry_reasons,
            "current": self.data["daily"]["Close"].iloc[-1],
            "mode": mode,
            "phase": phase,
        }


def scan_watchlist(mode="swing"):
    """Scan the full watchlist"""
    symbols = ["USDJPY=X", "GBPUSD=X", "EURJPY=X", "EURUSD=X", "GC=F", "BTC-USD"]

    mode_label = "SWING" if mode == "swing" else "DAY TRADE"

    print("\n" + "=" * 70)
    print(f"  🔍 ICC HUNTER v2 - WATCHLIST SCAN ({mode_label})")
    print("=" * 70 + "\n")

    setups = []

    for symbol in symbols:
        print(f"\n{'=' * 70}")
        print(f"  Analyzing: {symbol}")
        print(f"{'=' * 70}")

        hunter = ICCHunter(symbol)
        result = hunter.analyze(mode=mode)

        if result and result.get("direction"):
            result["symbol"] = symbol
            setups.append(result)
            print(f"  ➕ Added to setups")
        else:
            print(f"  ⏳ No setup detected")

        print("\n")

    # Summary
    print("\n" + "=" * 70)
    print(f"  📋 SCAN SUMMARY - {mode_label} SETUPS")
    print("=" * 70)

    if not setups:
        print("  ⏳ No setups detected in current scan")
        print("\n")
        return

    setups.sort(key=lambda x: x["probability"], reverse=True)

    for s in setups:
        zone_info = ""
        if s["indication"].get("break_level"):
            zone_info = f" | Level: {s['indication']['break_level']:.5f}"

        fire = (
            "🔥" if s["probability"] >= 80 else "⚡" if s["probability"] >= 70 else "📊"
        )
        print(
            f"  {fire} {s['symbol']:12} {s['direction']:6} {s['probability']}%{zone_info}"
        )

    print("\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("ICC HUNTER v2 - Trading Analysis")
        print("Usage:")
        print("  python icc_hunter_v2.py <SYMBOL>           - Swing trade analysis")
        print("  python icc_hunter_v2.py <SYMBOL> swing   - Swing trade analysis")
        print("  python icc_hunter_v2.py <SYMBOL> day     - Day trade analysis")
        print("  python icc_hunter_v2.py SCAN swing        - Scan watchlist (swing)")
        print("  python icc_hunter_v2.py SCAN day          - Scan watchlist (day)")
        print("\nExamples:")
        print("  python icc_hunter_v2.py EURJPY=X")
        print("  python icc_hunter_v2.py EURJPY=X day")
        print("  python icc_hunter_v2.py SCAN day")
        sys.exit(1)

    command = sys.argv[1].upper()
    mode = "swing"  # default

    if len(sys.argv) > 2:
        mode_arg = sys.argv[2].lower()
        if mode_arg in ["swing", "day"]:
            mode = mode_arg

    if command == "SCAN":
        scan_watchlist(mode)
    else:
        symbol = command
        hunter = ICCHunter(symbol)
        hunter.analyze(mode=mode)
