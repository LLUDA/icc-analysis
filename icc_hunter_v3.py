#!/usr/bin/env python3
"""
ICC HUNTER v3 - ICC Explained Properly
I → C → C = Indication → Correction → Continuation

Rules:
- HH/HL = Uptrend (buy at HL)
- LH/LL = Downtrend (sell at LH)
- NEVER buy at HH, NEVER sell at LL
- The indication level IS the entry level
"""

import yfinance as yf
import sys


class ICCHunter:
    """Hunts ICC setups properly"""

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

    def get_swings(self, highs, lows, lookback=5):
        """Find swing highs and lows"""
        swings_high = []
        swings_low = []

        for i in range(lookback, len(highs) - lookback):
            if highs[i] == max(highs[i - lookback : i + lookback + 1]):
                swings_high.append(highs[i])
            if lows[i] == min(lows[i - lookback : i + lookback + 1]):
                swings_low.append(lows[i])

        return swings_high, swings_low

    def analyze_tf(self, df, tf_name):
        """
        Analyze a timeframe for ICC
        Returns: trend, swings, structure status
        """
        highs = df["High"].values
        lows = df["Low"].values
        closes = df["Close"].values
        current = closes[-1]

        swings_high, swings_low = self.get_swings(highs, lows)

        result = {
            "tf": tf_name,
            "trend": None,
            "trend_direction": None,
            "last_swing": None,
            "last_swing_price": None,
            "indication_type": None,
            "indication_level": None,
            "structure_changing": False,
            "structure_break_level": None,
            "entry_zone": None,
            "narrative": "",
            "current": current,
            "swings_high": swings_high,
            "swings_low": swings_low,
        }

        if len(swings_high) >= 3 and len(swings_low) >= 3:
            recent_highs = swings_high[-3:]
            recent_lows = swings_low[-3:]

            # Determine pattern (HH/HL or LH/LL)
            hh = recent_highs[-1] > recent_highs[-2]
            hl = recent_lows[-1] > recent_lows[-2]
            lh = recent_highs[-1] < recent_highs[-2]
            ll = recent_lows[-1] < recent_lows[-2]

            if hh and hl:
                result["trend"] = "UPTREND"
                result["trend_direction"] = "LONG"
                result["last_swing"] = "HH"
                result["last_swing_price"] = recent_highs[-1]
            elif lh and ll:
                result["trend"] = "DOWNTREND"
                result["trend_direction"] = "SHORT"
                result["last_swing"] = "LL"
                result["last_swing_price"] = recent_lows[-1]
            elif hh or hl:
                result["trend"] = "UPTREND (partial)"
                result["trend_direction"] = "LONG"
                result["last_swing"] = "HH" if hh else "HL"
                result["last_swing_price"] = recent_highs[-1] if hh else recent_lows[-1]
            elif lh or ll:
                result["trend"] = "DOWNTREND (partial)"
                result["trend_direction"] = "SHORT"
                result["last_swing"] = "LL" if ll else "LH"
                result["last_swing_price"] = recent_lows[-1] if ll else recent_highs[-1]
            else:
                result["trend"] = "RANGE"

            result["narrative"] = (
                f"{result['trend']} | Last swing: {result['last_swing']} at {result['last_swing_price']:.5f}"
                if result["last_swing_price"]
                else result["trend"]
            )

            # Entry zone = last HL for longs, last LH for shorts
            if result["trend_direction"] == "LONG" and len(recent_lows) >= 1:
                result["entry_zone"] = recent_lows[-1]
            elif result["trend_direction"] == "SHORT" and len(recent_highs) >= 1:
                result["entry_zone"] = recent_highs[-1]

        return result

    def check_structure_break(self, lower_tf, higher_tf_data):
        """
        Check if lower TF is breaking structure of the TF above
        This is the INDICATION that the higher TF structure is starting to change
        """
        current = lower_tf["current"]

        result = {"breaking": False, "direction": None, "level": None, "narrative": ""}

        if not higher_tf_data["swings_high"] or not higher_tf_data["swings_low"]:
            return result

        # Get swings from higher TF
        higher_highs = higher_tf_data["swings_high"]
        higher_lows = higher_tf_data["swings_low"]

        # Check if price broke below a higher TF low (bearish break)
        for low in higher_lows[-3:]:
            if current < low:
                result["breaking"] = True
                result["direction"] = "SHORT"
                result["level"] = low
                result["narrative"] = f"1H broke below 4H swing low {low:.5f}"
                break

        # Check if price broke above a higher TF high (bullish break)
        if not result["breaking"]:
            for high in higher_highs[-3:]:
                if current > high:
                    result["breaking"] = True
                    result["direction"] = "LONG"
                    result["level"] = high
                    result["narrative"] = f"1H broke above 4H swing high {high:.5f}"
                    break

        return result

    def analyze(self, mode="swing"):
        """
        Full ICC analysis
        SWING: DAILY → 4H → 1H
        DAY: 4H → 1H → 15M
        """
        if not self.fetch_data():
            return None

        current = float(self.data["daily"]["Close"].iloc[-1])

        print("=" * 70)
        print(f"  🎯 ICC HUNTER v3 - {self.symbol.upper()}")
        print(f"  Mode: {'📅 SWING' if mode == 'swing' else '📅 DAY TRADE'}")
        print(f"  Price: {current:.5f}")
        print("=" * 70)

        if mode == "swing":
            # 4H for trend, 1H for indication, 15M for entry
            tf_trend, tf_indication, tf_entry = "4h", "1h", "15m"
        else:
            # Day trade: 4H for trend, 1H for indication, 15M for entry
            tf_trend, tf_indication, tf_entry = "4h", "1h", "15m"

        # STEP 1: Identify TREND (4H structure)
        trend_data = self.analyze_tf(self.data[tf_trend], tf_trend.upper())

        print("\n📊 STEP 1: 4H - TREND & STRUCTURE")
        print("-" * 70)
        trend_icon = (
            "📈"
            if trend_data["trend_direction"] == "LONG"
            else "📉"
            if trend_data["trend_direction"] == "SHORT"
            else "↔️"
        )
        print(f"  Structure: {trend_icon} {trend_data['trend']}")
        print(f"  {trend_data['narrative']}")

        # STEP 2: Check if 1H is breaking 4H swings (INDICATION)
        indication_data = self.analyze_tf(
            self.data[tf_indication], tf_indication.upper()
        )

        # Check structure break
        structure_break = self.check_structure_break(indication_data, trend_data)

        print(f"\n⚡ STEP 2: 1H - INDICATION (Breaking 4H Structure?)")
        print("-" * 70)

        if structure_break["breaking"]:
            icon = "🔴" if structure_break["direction"] == "SHORT" else "🟢"
            print(f"  {icon} {structure_break['narrative']}")
            print(f"     → This means 4H structure is starting to change")
        else:
            print(f"  ⏳ 1H inside 4H structure - watching for break")
            print(f"  {indication_data['narrative']}")

        # STEP 3: Check entry zone on 15M
        entry_data = self.analyze_tf(self.data[tf_entry], tf_entry.upper())

        print(f"\n🎯 STEP 3: 15M - ENTRY ZONE")
        print("-" * 70)
        print(f"  {entry_data['narrative']}")

        if entry_data["entry_zone"]:
            print(f"  Entry Level: {entry_data['entry_zone']:.5f}")

        # SUMMARY
        print("\n" + "=" * 70)
        print("  📋 ICC SETUP SUMMARY")
        print("=" * 70)

        direction = None
        probability = 0
        setup_type = ""

        # If structure break detected = indication
        if structure_break["breaking"]:
            direction = structure_break["direction"]
            probability = 85
            setup_type = (
                f"ICC - Structure break on 1H at {structure_break['level']:.5f}"
            )
        else:
            direction = trend_data["trend_direction"]
            probability = 60
            setup_type = "ICC - Waiting for 1H to break 4H structure"

        if not direction:
            print("  ⏳ NO SETUP - Price in range")
            return None

        print(f"\n  🎯 ACTION: {direction}")
        print(f"  📝 TYPE: {setup_type}")
        print(f"  📊 PROBABILITY: {probability}%")

        # Entry zone
        entry_zone = entry_data.get("entry_zone") or trend_data.get("entry_zone")
        if entry_zone:
            print(f"\n  📍 ENTRY ZONE: {entry_zone:.5f}")

        # Target = next swing in direction
        if direction == "SHORT" and trend_data["swings_low"]:
            target = trend_data["swings_low"][-1]
            print(f"  🎯 TARGET: {target:.5f} (next swing low)")
        elif direction == "LONG" and trend_data["swings_high"]:
            target = trend_data["swings_high"][-1]
            print(f"  🎯 TARGET: {target:.5f} (next swing high)")

        print("\n" + "=" * 70)

        return {
            "direction": direction,
            "probability": probability,
            "setup_type": setup_type,
            "trend": trend_data,
            "indication": indication_data,
            "structure_break": structure_break,
            "entry": entry_data,
            "entry_zone": entry_zone,
            "current": current,
            "mode": mode,
        }


def scan_watchlist(mode="swing"):
    """Scan the full watchlist"""
    symbols = ["USDJPY=X", "GBPUSD=X", "EURJPY=X", "EURUSD=X", "GC=F", "BTC-USD"]

    mode_label = "SWING" if mode == "swing" else "DAY TRADE"

    print("\n" + "=" * 70)
    print(f"  🔍 ICC HUNTER v3 - WATCHLIST SCAN ({mode_label})")
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
            print(f"  ⏳ No setup")

    print("\n" + "=" * 70)
    print(f"  📋 SCAN SUMMARY - {mode_label} SETUPS")
    print("=" * 70)

    if not setups:
        print("  ⏳ No setups detected")
        return

    setups.sort(key=lambda x: x["probability"], reverse=True)

    for s in setups:
        entry_zone = s.get("entry_zone") or 0
        fire = (
            "🔥" if s["probability"] >= 80 else "⚡" if s["probability"] >= 70 else "📊"
        )
        entry_str = f"{entry_zone:.5f}" if entry_zone else "N/A"
        print(
            f"  {fire} {s['symbol']:12} {s['direction']:6} {s['probability']}% | Entry: {entry_str}"
        )

    print("\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("ICC HUNTER v3 - ICC Explained Properly")
        print("Usage:")
        print("  python icc_hunter_v3.py <SYMBOL>           - Swing analysis")
        print("  python icc_hunter_v3.py <SYMBOL> day   - Day trade analysis")
        print("  python icc_hunter_v3.py SCAN              - Scan watchlist")
        print("  python icc_hunter_v3.py SCAN day          - Day trade scan")
        sys.exit(1)

    command = sys.argv[1].upper()
    mode = "swing"

    if len(sys.argv) > 2:
        if sys.argv[2].lower() == "day":
            mode = "day"

    if command == "SCAN":
        scan_watchlist(mode)
    else:
        hunter = ICCHunter(command)
        hunter.analyze(mode=mode)
