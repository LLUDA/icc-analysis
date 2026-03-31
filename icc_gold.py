#!/usr/bin/env python3
"""
ICC LIVE - GOLD (XAUUSD) Analysis
==================================
"""

import yfinance as yf
from datetime import datetime, timedelta


class ICCGoldAnalysis:
    """Detailed Gold analysis"""

    def __init__(self):
        self.pair = "GC=F"

    def get_swings(self, data, is_high=True, lookback=5):
        swings = []
        for i in range(lookback, len(data) - lookback):
            if is_high:
                if data[i] == max(data[i - lookback : i + lookback + 1]):
                    swings.append((i, data[i]))
            else:
                if data[i] == min(data[i - lookback : i + lookback + 1]):
                    swings.append((i, data[i]))
        return swings

    def get_trend(self, highs, lows, idx, lookback=5):
        if idx < lookback + 5:
            return "RANGE"
        recent_h = [h for i, h in self.get_swings(highs[:idx], True)][-lookback:]
        recent_l = [l for i, l in self.get_swings(lows[:idx], False)][-lookback:]
        if len(recent_h) < 3 or len(recent_l) < 3:
            return "RANGE"
        if recent_h[-1] > recent_h[0] and recent_l[-1] > recent_l[0]:
            return "UPTREND"
        elif recent_h[-1] < recent_h[0] and recent_l[-1] < recent_l[0]:
            return "DOWNTREND"
        return "RANGE"

    def run_analysis(self):
        current_time = datetime.now()

        print("=" * 70)
        print("  🥇 GOLD (XAUUSD) LIVE ANALYSIS")
        print(f"  {current_time.strftime('%Y-%m-%d %H:%M UTC')}")
        print("=" * 70)

        try:
            # Load data
            df_4h = yf.Ticker(self.pair).history(period="30d", interval="4h")
            df_1h = yf.Ticker(self.pair).history(period="7d", interval="1h")
            df_15m = yf.Ticker(self.pair).history(period="2d", interval="15m")

            print(f"\n  📊 DATA LOADED:")
            print(
                f"     4H: {len(df_4h)} bars ({df_4h.index[0].strftime('%b %d')} to {df_4h.index[-1].strftime('%b %d')})"
            )
            print(f"     1H: {len(df_1h)} bars")
            print(f"     15M: {len(df_15m)} bars")

            highs_4h = df_4h["High"].values
            lows_4h = df_4h["Low"].values
            closes_4h = df_4h["Close"].values
            h4_timestamps = df_4h.index.tolist()

            highs_1h = df_1h["High"].values
            lows_1h = df_1h["Low"].values
            closes_1h = df_1h["Close"].values
            timestamps_1h = df_1h.index.tolist()

            highs_15m = df_15m["High"].values
            lows_15m = df_15m["Low"].values
            closes_15m = df_15m["Close"].values
            timestamps_15m = df_15m.index.tolist()

            current_price = closes_15m[-1] if len(closes_15m) > 0 else closes_1h[-1]
            current_time_actual = (
                timestamps_15m[-1] if len(timestamps_15m) > 0 else timestamps_1h[-1]
            )

            print(f"\n  💰 CURRENT PRICE: ${current_price:.2f}")
            print(f"  🕐 Last Update: {current_time_actual.strftime('%Y-%m-%d %H:%M')}")

            # Trend analysis
            trend_4h = self.get_trend(highs_4h, lows_4h, len(highs_4h))
            trend_1h = self.get_trend(highs_1h, lows_1h, len(highs_1h))
            trend_15m = (
                self.get_trend(highs_15m, lows_15m, len(highs_15m))
                if len(highs_15m) > 10
                else "RANGE"
            )

            print(f"\n  📈 TREND:")
            emoji_4h = (
                "🟢"
                if trend_4h == "UPTREND"
                else "🔴"
                if trend_4h == "DOWNTREND"
                else "⚪"
            )
            emoji_1h = (
                "🟢"
                if trend_1h == "UPTREND"
                else "🔴"
                if trend_1h == "DOWNTREND"
                else "⚪"
            )
            emoji_15m = (
                "🟢"
                if trend_15m == "UPTREND"
                else "🔴"
                if trend_15m == "DOWNTREND"
                else "⚪"
            )

            print(f"     Daily/4H: {emoji_4h} {trend_4h}")
            print(f"     1H:       {emoji_1h} {trend_1h}")
            print(f"     15M:      {emoji_15m} {trend_15m}")

            # Key levels
            swings_low_4h = self.get_swings(lows_4h, False)
            swings_high_4h = self.get_swings(highs_4h, True)
            swings_low_1h = self.get_swings(lows_1h, False)
            swings_high_1h = self.get_swings(highs_1h, True)

            print(f"\n  🎯 KEY 4H LEVELS:")
            recent_lows_4h = [(l) for i, l in swings_low_4h[-5:]]
            recent_highs_4h = [(h) for i, h in swings_high_4h[-5:]]

            if recent_lows_4h:
                nearest_low = min(recent_lows_4h)
                dist = (current_price - nearest_low) / current_price * 100
                print(f"     Nearest 4H Swing Low: ${nearest_low:.2f} ({dist:+.2f}%)")
            if recent_highs_4h:
                nearest_high = min(recent_highs_4h)
                dist = (current_price - nearest_high) / current_price * 100
                print(f"     Nearest 4H Swing High: ${nearest_high:.2f} ({dist:+.2f}%)")

            print(f"\n  📍 RECENT 1H SWINGS:")
            print(f"     Swing Lows (recent 5):")
            for i, level in [(i, l) for i, l in swings_low_1h[-5:]]:
                if i < len(timestamps_1h):
                    dist = (current_price - level) / current_price * 100
                    ts = timestamps_1h[i].strftime("%H:%M")
                    print(f"       ${level:.2f} ({dist:+.2f}%) - {ts}")

            print(f"     Swing Highs (recent 5):")
            for i, level in [(i, h) for i, h in swings_high_1h[-5:]]:
                if i < len(timestamps_1h):
                    dist = (current_price - level) / current_price * 100
                    ts = timestamps_1h[i].strftime("%H:%M")
                    print(f"       ${level:.2f} ({dist:+.2f}%) - {ts}")

            # Find ICC setups
            print(f"\n  🔍 ICC SETUP SCAN:")
            setups = self.find_icc_setups(
                highs_4h,
                lows_4h,
                h4_timestamps,
                highs_1h,
                lows_1h,
                closes_1h,
                timestamps_1h,
                current_price,
            )

            if setups:
                print(f"\n  ✅ FOUND {len(setups)} POTENTIAL SETUPS!")
                for i, setup in enumerate(setups, 1):
                    print(f"\n  SETUP {i}:")
                    print(f"     Direction: {setup['direction']} {setup['emoji']}")
                    print(f"     Entry Zone: ${setup['entry']:.2f}")
                    print(
                        f"     Correction: {setup['correction']:.0f}% ({setup['correction_status']})"
                    )
                    print(f"     Trend: {setup['trend']}")
                    print(f"     Quality: {setup['quality']}")
            else:
                print(f"\n  ⚠️ No ICC setups right now.")
                print(f"     Monitor for corrections after structure breaks.")

        except Exception as e:
            print(f"\n  ❌ Error: {e}")
            import traceback

            traceback.print_exc()

    def find_icc_setups(
        self,
        highs_4h,
        lows_4h,
        h4_timestamps,
        highs_1h,
        lows_1h,
        closes_1h,
        timestamps_1h,
        current_price,
    ):
        """Find ICC setups in gold"""
        setups = []

        swings_low = self.get_swings(lows_1h, False)
        swings_high = self.get_swings(highs_1h, True)

        trend_4h = self.get_trend(highs_4h, lows_4h, len(highs_4h))
        trend_1h = self.get_trend(highs_1h, lows_1h, len(highs_1h))

        # SHORTS - Look for broken swing lows
        for i, level in swings_low[-8:]:
            if i >= len(closes_1h) - 5:
                continue

            # Check if this level was broken
            for j in range(i + 1, min(i + 20, len(lows_1h))):
                if lows_1h[j] < level:
                    # Structure broken - look for correction
                    move_size = level - lows_1h[j]
                    if move_size <= 0:
                        continue

                    for k in range(j, min(j + 40, len(closes_1h))):
                        if highs_1h[k] >= level:
                            correction = highs_1h[k] - level
                            corr_pct = correction / move_size * 100

                            if corr_pct <= 80:
                                setups.append(
                                    {
                                        "direction": "SHORT",
                                        "emoji": "🔴",
                                        "entry": level,
                                        "correction": corr_pct,
                                        "correction_status": "✅ PASS"
                                        if corr_pct <= 50
                                        else "✅ OK"
                                        if corr_pct <= 70
                                        else "⚠️ MARGINAL",
                                        "trend": f"4H: {trend_4h}, 1H: {trend_1h}",
                                        "quality": "⭐⭐⭐ HIGH"
                                        if corr_pct <= 50
                                        else "⭐⭐ MEDIUM"
                                        if corr_pct <= 70
                                        else "⭐ LOW",
                                    }
                                )
                            break
                    break

        # LONGS - Look for broken swing highs
        for i, level in swings_high[-8:]:
            if i >= len(closes_1h) - 5:
                continue

            for j in range(i + 1, min(i + 20, len(highs_1h))):
                if highs_1h[j] > level:
                    move_size = highs_1h[j] - level
                    if move_size <= 0:
                        continue

                    for k in range(j, min(j + 40, len(closes_1h))):
                        if lows_1h[k] <= level:
                            correction = level - lows_1h[k]
                            corr_pct = correction / move_size * 100

                            if corr_pct <= 80:
                                setups.append(
                                    {
                                        "direction": "LONG",
                                        "emoji": "🟢",
                                        "entry": level,
                                        "correction": corr_pct,
                                        "correction_status": "✅ PASS"
                                        if corr_pct <= 50
                                        else "✅ OK"
                                        if corr_pct <= 70
                                        else "⚠️ MARGINAL",
                                        "trend": f"4H: {trend_4h}, 1H: {trend_1h}",
                                        "quality": "⭐⭐⭐ HIGH"
                                        if corr_pct <= 50
                                        else "⭐⭐ MEDIUM"
                                        if corr_pct <= 70
                                        else "⭐ LOW",
                                    }
                                )
                            break
                    break

        return setups


if __name__ == "__main__":
    ICCGoldAnalysis().run_analysis()
