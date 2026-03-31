#!/usr/bin/env python3
"""
ICC HUNTER v4 - Dynamic TF Analysis
Lower TF breaking major swings = Indication of continuation/correction/change
Session awareness for pair behavior
"""

import yfinance as yf
import sys
from datetime import datetime, timezone


class ICCHunter:
    """Hunts ICC setups with dynamic TF analysis"""

    def __init__(self, symbol):
        self.symbol = symbol
        self.ticker = yf.Ticker(symbol)
        self.data = {}

        # Session times (UTC)
        self.sessions = {
            "SYDNEY": (22, 7),
            "TOKYO": (0, 9),
            "LONDON": (8, 17),
            "NY": (13, 22),
        }

        # Session pairs
        self.session_pairs = {
            "LONDON": ["GBPJPY=X", "GBPUSD=X", "GBPCAD=X", "EURGBP=X", "XAUUSD=X"],
            "NY": ["USDJPY=X", "EURUSD=X", "USDCAD=X", "XAUUSD=X"],
            "TOKYO": ["EURJPY=X", "GBPJPY=X", "USDJPY=X"],
        }

    def get_current_session(self):
        """Get current trading session"""
        utc_hour = datetime.now(timezone.utc).hour

        if 8 <= utc_hour < 17:
            return "LONDON"
        elif 13 <= utc_hour < 22:
            return "NY"
        elif 0 <= utc_hour < 9:
            return "TOKYO"
        elif 22 <= utc_hour or utc_hour < 0:
            return "SYDNEY"
        return "QUIET"

    def get_active_pairs_for_session(self, session):
        """Get pairs active during session"""
        active = []
        for s, pairs in self.session_pairs.items():
            if session in s:
                active.extend(pairs)
        return list(set(active))

    def fetch_data(self):
        """Get data from multiple timeframes"""
        try:
            self.data["4h"] = self.ticker.history(period="30d", interval="4h")
            self.data["1h"] = self.ticker.history(period="5d", interval="1h")
            self.data["15m"] = self.ticker.history(period="2d", interval="15m")
            self.data["5m"] = self.ticker.history(period="1d", interval="5m")
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

    def check_structure_break(
        self, lower_df, higher_swings_high, higher_swings_low, higher_name
    ):
        """
        Is the lower TF breaking major swings of the higher TF?
        This answers: Continuation, Correction, or Change?
        """
        highs = lower_df["High"].values
        lows = lower_df["Low"].values
        closes = lower_df["Close"].values
        current = closes[-1]

        lower_highs, lower_lows = self.get_swings(highs, lows)

        result = {
            "breaking": False,
            "direction": None,
            "broken_level": None,
            "break_type": None,  # BREAKOUT or BREAKDOWN
            "narrative": "",
        }

        if not higher_swings_high or not higher_swings_low:
            return result

        # Check recent highs from lower TF
        recent_lower_highs = lower_highs[-5:] if len(lower_highs) >= 5 else lower_highs
        recent_lower_lows = lower_lows[-5:] if len(lower_lows) >= 5 else lower_lows

        # Is lower TF making new highs ABOVE higher TF swings?
        for high in higher_swings_high[-3:]:
            for lh in recent_lower_highs:
                if lh > high:
                    result["breaking"] = True
                    result["direction"] = "BULLISH"
                    result["broken_level"] = high
                    result["break_type"] = "BREAKOUT"
                    result["narrative"] = (
                        f"1H broke ABOVE {higher_name} swing at {high:.5f}"
                    )
                    return result

        # Is lower TF making new lows BELOW higher TF swings?
        for low in higher_swings_low[-3:]:
            for ll in recent_lower_lows:
                if ll < low:
                    result["breaking"] = True
                    result["direction"] = "BEARISH"
                    result["broken_level"] = low
                    result["break_type"] = "BREAKDOWN"
                    result["narrative"] = (
                        f"1H broke BELOW {higher_name} swing at {low:.5f}"
                    )
                    return result

        return result

    def analyze_tf(self, df, tf_name):
        """Analyze timeframe structure"""
        highs = df["High"].values
        lows = df["Low"].values
        closes = df["Close"].values
        current = closes[-1]

        swings_high, swings_low = self.get_swings(highs, lows)

        result = {
            "tf": tf_name,
            "trend": None,
            "trend_direction": None,
            "swings_high": swings_high,
            "swings_low": swings_low,
            "current": current,
            "narrative": "",
        }

        if len(swings_high) >= 2 and len(swings_low) >= 2:
            recent_h = swings_high[-2:]
            recent_l = swings_low[-2:]

            hh = recent_h[-1] > recent_h[-2] if len(recent_h) >= 2 else False
            hl = recent_l[-1] > recent_l[-2] if len(recent_l) >= 2 else False
            lh = recent_h[-1] < recent_h[-2] if len(recent_h) >= 2 else False
            ll = recent_l[-1] < recent_l[-2] if len(recent_l) >= 2 else False

            if hh and hl:
                result["trend"] = "UPTREND"
                result["trend_direction"] = "LONG"
            elif lh and ll:
                result["trend"] = "DOWNTREND"
                result["trend_direction"] = "SHORT"
            elif hh or hl:
                result["trend"] = "PULLBACK UP"
                result["trend_direction"] = "LONG"
            elif lh or ll:
                result["trend"] = "PULLBACK DOWN"
                result["trend_direction"] = "SHORT"
            else:
                result["trend"] = "RANGE"

            result["narrative"] = f"{result['trend']}"

        return result

    def analyze(self):
        """Full ICC analysis"""
        if not self.fetch_data():
            return None

        current = float(self.data["4h"]["Close"].iloc[-1])
        session = self.get_current_session()

        # Check if this pair is active in current session
        pair_active = any(self.symbol in pairs for pairs in self.session_pairs.values())
        session_status = "🔥 ACTIVE" if pair_active else "💤 QUIET"

        print("=" * 70)
        print(f"  🎯 ICC HUNTER v4 - {self.symbol.upper()}")
        print(f"  Price: {current:.5f}")
        print(f"  Session: {session} ({session_status})")
        print("=" * 70)

        # Analyze each TF
        tf_4h = self.analyze_tf(self.data["4h"], "4H")
        tf_1h = self.analyze_tf(self.data["1h"], "1H")
        tf_15m = self.analyze_tf(self.data["15m"], "15M")

        # THE KEY QUESTION: Is lower TF breaking major swings of higher TF?

        print("\n📊 STRUCTURE ANALYSIS")
        print("-" * 70)

        # 4H Structure
        print(f"\n  4H: {tf_4h['narrative']}")
        if tf_4h["swings_high"]:
            print(
                f"      Recent highs: {[round(h, 5) for h in tf_4h['swings_high'][-3:]]}"
            )
        if tf_4h["swings_low"]:
            print(
                f"      Recent lows: {[round(l, 5) for l in tf_4h['swings_low'][-3:]]}"
            )

        # 1H Structure
        print(f"\n  1H: {tf_1h['narrative']}")
        if tf_1h["swings_high"]:
            print(
                f"      Recent highs: {[round(h, 5) for h in tf_1h['swings_high'][-3:]]}"
            )
        if tf_1h["swings_low"]:
            print(
                f"      Recent lows: {[round(l, 5) for l in tf_1h['swings_low'][-3:]]}"
            )

        # THE INDICATION: Is 1H breaking 4H major swings?
        print("\n" + "=" * 70)
        print("  ⚡ THE INDICATION")
        print("=" * 70)

        break_result = self.check_structure_break(
            self.data["1h"], tf_4h["swings_high"], tf_4h["swings_low"], "4H"
        )

        if break_result["breaking"]:
            icon = "🔴" if break_result["direction"] == "BEARISH" else "🟢"
            print(f"\n  {icon} STRUCTURE BREAK: {break_result['narrative']}")
            print(f"     → 1H is showing BREAK of 4H structure")
            print(f"     → This means 4H structure is CHANGING")
        else:
            print(f"\n  ⏳ 1H inside 4H structure")
            print(f"     → Not breaking 4H swings yet")
            print(f"     → 4H trend intact")

        # 15M confirmation
        print("\n" + "=" * 70)
        print("  🎯 ENTRY CONFIRMATION (15M)")
        print("=" * 70)

        # Check if 15M is breaking 1H swings
        break_15m = self.check_structure_break(
            self.data["15m"], tf_1h["swings_high"], tf_1h["swings_low"], "1H"
        )

        if break_15m["breaking"]:
            icon = "🔴" if break_15m["direction"] == "BEARISH" else "🟢"
            print(f"\n  {icon} 15M confirming: {break_15m['narrative']}")
        else:
            print(f"\n  ⏳ 15M inside 1H structure")

        # SUMMARY
        print("\n" + "=" * 70)
        print("  📋 ICC SETUP SUMMARY")
        print("=" * 70)

        # Determine action
        if break_result["breaking"]:
            direction = "SHORT" if break_result["direction"] == "BEARISH" else "LONG"
            probability = 85
            setup_type = f"STRUCTURE BREAK on 1H"

            print(f"\n  🎯 ACTION: {direction}")
            print(f"  📝 TYPE: {setup_type}")
            print(f"  📊 PROBABILITY: {probability}%")
            print(f"\n  📍 BROKEN LEVEL: {break_result['broken_level']:.5f}")
            print(f"     → Wait for pullback to this level for entry")

            # Entry zone = the broken level
            print(f"\n  🎯 ENTRY ZONE: {break_result['broken_level']:.5f}")
            print(f"     (Wait for price to return to this zone)")

        else:
            # No break, go with 4H trend
            direction = tf_4h["trend_direction"]
            probability = 60
            setup_type = f"No break yet - following 4H trend"

            print(f"\n  🎯 ACTION: {direction or 'WAITING'}")
            print(f"  📝 TYPE: {setup_type}")
            print(f"  📊 PROBABILITY: {probability}%")

        print("\n" + "=" * 70)

        return {
            "direction": direction,
            "probability": probability,
            "setup_type": setup_type,
            "break": break_result,
            "4h": tf_4h,
            "1h": tf_1h,
            "15m": tf_15m,
            "current": current,
            "session": session,
            "pair_active": pair_active,
        }


def scan_watchlist():
    """Scan the full watchlist"""
    symbols = [
        "GBPCAD=X",
        "GBPUSD=X",
        "GBPJPY=X",
        "EURJPY=X",
        "USDJPY=X",
        "EURUSD=X",
        "GC=F",
        "BTC-USD",
    ]

    session = ICCHunter("GBPUSD=X").get_current_session()

    print("\n" + "=" * 70)
    print(f"  🔍 ICC HUNTER v4 - WATCHLIST SCAN")
    print(f"  Session: {session}")
    print("=" * 70 + "\n")

    setups = []

    for symbol in symbols:
        hunter = ICCHunter(symbol)
        result = hunter.analyze()

        if result and result.get("direction"):
            setups.append(result)

        print("\n")

    print("=" * 70)
    print("  📋 SCAN SUMMARY")
    print("=" * 70)

    setups.sort(key=lambda x: x["probability"], reverse=True)

    for s in setups:
        fire = (
            "🔥" if s["probability"] >= 80 else "⚡" if s["probability"] >= 70 else "📊"
        )
        active = "🔥" if s.get("pair_active") else ""
        print(
            f"  {fire}{active} {s['symbol'] if hasattr(s, 'symbol') else symbol:12} {s['direction']:6} {s['probability']}%"
        )

        if s["break"]["breaking"]:
            print(f"           → {s['break']['narrative']}")

    print("\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("ICC HUNTER v4 - Dynamic TF Analysis")
        print("Usage:")
        print("  python icc_hunter_v4.py <SYMBOL>")
        print("  python icc_hunter_v4.py SCAN")
        sys.exit(1)

    command = sys.argv[1].upper()

    if command == "SCAN":
        scan_watchlist()
    else:
        hunter = ICCHunter(command)
        hunter.analyze()
