#!/usr/bin/env python3
"""
ICC LIVE ANALYSIS - Today's Potential Setups
============================================
Scans for ICC setups forming NOW
"""

import yfinance as yf
from datetime import datetime, timedelta


class ICCLiveAnalysis:
    """Analyze current market for ICC setups"""

    def __init__(self):
        self.pairs = ["EURUSD=X", "AUDUSD=X", "GBPUSD=X", "GBPJPY=X", "USDJPY=X"]
        self.names = {
            "EURUSD=X": "EURUSD",
            "AUDUSD=X": "AUDUSD",
            "GBPUSD=X": "GBPUSD",
            "GBPJPY=X": "GBPJPY",
            "USDJPY=X": "USDJPY",
        }

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
        print("  🔍 ICC LIVE ANALYSIS - TODAY'S MARKET")
        print(f"  {current_time.strftime('%Y-%m-%d %H:%M')}")
        print("=" * 70)

        all_opportunities = []

        for pair in self.pairs:
            name = self.names.get(pair, pair)
            print(f"\n{'=' * 55}")
            print(f"  📊 {name}")
            print(f"{'=' * 55}")

            try:
                # Load recent data
                df_4h = yf.Ticker(pair).history(period="10d", interval="4h")
                df_1h = yf.Ticker(pair).history(period="5d", interval="1h")

                if len(df_4h) < 10 or len(df_1h) < 20:
                    print("  Not enough data")
                    continue

                highs_4h = df_4h["High"].values
                lows_4h = df_4h["Low"].values
                closes_4h = df_4h["Close"].values
                h4_timestamps = df_4h.index.tolist()

                highs_1h = df_1h["High"].values
                lows_1h = df_1h["Low"].values
                closes_1h = df_1h["Close"].values
                timestamps_1h = df_1h.index.tolist()

                current_price = closes_1h[-1]
                print(f"\n  💹 Current Price: {current_price:.5f}")
                print(
                    f"  📅 Data: {h4_timestamps[0].strftime('%b %d')} to {h4_timestamps[-1].strftime('%b %d %H:%M')}"
                )

                # Trend analysis
                trend_4h = self.get_trend(highs_4h, lows_4h, len(highs_4h))
                trend_1h = self.get_trend(highs_1h, lows_1h, len(highs_1h), lookback=3)

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

                print(f"\n  📈 TREND:")
                print(f"     4H: {emoji_4h} {trend_4h}")
                print(f"     1H: {emoji_1h} {trend_1h}")

                # Recent structure
                swings_low_1h = self.get_swings(lows_1h, False)
                swings_high_1h = self.get_swings(highs_1h, True)

                print(f"\n  📍 RECENT STRUCTURE (1H):")

                # Recent swing lows
                recent_lows = [
                    (i, l) for i, l in swings_low_1h[-5:] if i < len(closes_1h) - 5
                ]
                if recent_lows:
                    print(f"     Recent Swing Lows:")
                    for i, level in recent_lows[-3:]:
                        if i < len(timestamps_1h):
                            dist_pct = (current_price - level) / level * 100
                            print(f"       {level:.5f} ({dist_pct:+.2f}% away)")

                # Recent swing highs
                recent_highs = [
                    (i, h) for i, h in swings_high_1h[-5:] if i < len(closes_1h) - 5
                ]
                if recent_highs:
                    print(f"     Recent Swing Highs:")
                    for i, level in recent_highs[-3:]:
                        if i < len(timestamps_1h):
                            dist_pct = (current_price - level) / level * 100
                            print(f"       {level:.5f} ({dist_pct:+.2f}% away)")

                # Analyze for ICC setups
                opportunities = self.find_opportunities(
                    pair,
                    name,
                    highs_4h,
                    lows_4h,
                    h4_timestamps,
                    highs_1h,
                    lows_1h,
                    closes_1h,
                    timestamps_1h,
                    current_price,
                    trend_4h,
                    trend_1h,
                )

                all_opportunities.extend(opportunities)

            except Exception as e:
                print(f"  Error: {e}")
                import traceback

                traceback.print_exc()

        # SUMMARY
        print("\n" + "=" * 70)
        print("  🎯 TODAY'S ICC OPPORTUNITIES SUMMARY")
        print("=" * 70)

        if all_opportunities:
            # Sort by priority
            all_opportunities.sort(key=lambda x: x["priority"], reverse=True)

            for i, opp in enumerate(all_opportunities, 1):
                print(f"\n  {i}. {opp['emoji']} {opp['pair']} {opp['direction']}")
                print(f"     Entry Zone: {opp['entry_zone']}")
                print(f"     Reason: {opp['reason']}")
                print(
                    f"     Priority: {'⭐⭐⭐ HIGH' if opp['priority'] >= 3 else '⭐⭐ MEDIUM' if opp['priority'] >= 2 else '⭐ LOW'}"
                )
        else:
            print("\n  No clear ICC setups detected right now.")
            print("  Continue monitoring for corrections.")

        return all_opportunities

    def find_opportunities(
        self,
        pair,
        name,
        highs_4h,
        lows_4h,
        h4_timestamps,
        highs_1h,
        lows_1h,
        closes_1h,
        timestamps_1h,
        current_price,
        trend_4h,
        trend_1h,
    ):
        """Find potential ICC opportunities"""
        opportunities = []

        swings_low = self.get_swings(lows_1h, False)
        swings_high = self.get_swings(highs_1h, True)

        # Look for recent structure breaks that might correct
        for i, level in swings_low[-5:]:
            if i >= len(closes_1h) - 10:
                continue

            # Check if this low was broken recently
            for j in range(i + 1, min(i + 15, len(lows_1h))):
                if j < len(lows_1h) and lows_1h[j] < level:
                    # Structure was broken - look for SHORT opportunity

                    # Check trends
                    if trend_4h == "DOWNTREND" or trend_1h == "DOWNTREND":
                        # Measure the move
                        move_size = level - lows_1h[j]
                        if move_size > 0:
                            # Check if price is correcting back
                            for k in range(j, min(j + 30, len(closes_1h))):
                                if k < len(closes_1h) and highs_1h[k] >= level:
                                    correction = highs_1h[k] - level
                                    corr_pct = correction / move_size * 100

                                    if corr_pct <= 80:
                                        opportunities.append(
                                            {
                                                "pair": name,
                                                "direction": "SHORT 🔴",
                                                "entry_zone": f"{level:.5f} (at break level)",
                                                "reason": f"Correction {corr_pct:.0f}% - awaiting continuation below {level:.5f}",
                                                "priority": 3 if corr_pct <= 50 else 2,
                                                "emoji": "🔴",
                                                "level": level,
                                                "type": "SHORT",
                                            }
                                        )
                                    break
                    break

        # Look for LONG opportunities (broken swing highs)
        for i, level in swings_high[-5:]:
            if i >= len(closes_1h) - 10:
                continue

            for j in range(i + 1, min(i + 15, len(highs_1h))):
                if j < len(highs_1h) and highs_1h[j] > level:
                    if trend_4h == "UPTREND" or trend_1h == "UPTREND":
                        move_size = highs_1h[j] - level
                        if move_size > 0:
                            for k in range(j, min(j + 30, len(closes_1h))):
                                if k < len(closes_1h) and lows_1h[k] <= level:
                                    correction = level - lows_1h[k]
                                    corr_pct = correction / move_size * 100

                                    if corr_pct <= 80:
                                        opportunities.append(
                                            {
                                                "pair": name,
                                                "direction": "LONG 🟢",
                                                "entry_zone": f"{level:.5f} (at break level)",
                                                "reason": f"Correction {corr_pct:.0f}% - awaiting continuation above {level:.5f}",
                                                "priority": 3 if corr_pct <= 50 else 2,
                                                "emoji": "🟢",
                                                "level": level,
                                                "type": "LONG",
                                            }
                                        )
                                    break
                    break

        return opportunities


if __name__ == "__main__":
    ICCLiveAnalysis().run_analysis()
