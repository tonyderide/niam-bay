#!/usr/bin/env python3
"""
Morning Brief — résumé quotidien envoyé sur Telegram à 7h.
Tourne via cron sur la VM.
"""

import json
import urllib.request
import time

TELEGRAM_TOKEN = "7913168011:AAG76RsddMBpUnveiEdK2HSk4PQLS7Ab454"
CHAT_ID = "6574420846"
MARTIN_API = "http://localhost:8081"
KRAKEN_API = "https://api.kraken.com/0/public"
PAIRS = {"DOT": "DOTUSD", "SOL": "SOLUSD", "ETH": "ETHUSD", "XRP": "XRPUSD", "BTC": "XBTUSD"}


def fetch_json(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "NiamBay/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except:
        return None


def get_prices():
    pairs_str = ",".join(PAIRS.values())
    data = fetch_json(f"{KRAKEN_API}/Ticker?pair={pairs_str}")
    if not data or "result" not in data:
        return {}
    prices = {}
    for name, pair in PAIRS.items():
        for k, v in data["result"].items():
            if pair.replace("USD", "") in k or pair in k:
                price = float(v["c"][0])
                change = round((price - float(v["o"])) / float(v["o"]) * 100, 2)
                prices[name] = {"price": price, "change": change}
                break
    return prices


def get_martin_status():
    active = fetch_json(f"{MARTIN_API}/api/grid/active")
    balance = fetch_json(f"{MARTIN_API}/api/bot/balance")
    stats = fetch_json(f"{MARTIN_API}/api/trades/stats")

    pf = 0
    if balance and "accounts" in balance:
        pf = round(balance["accounts"]["flex"]["portfolioValue"], 2)

    grids = []
    if active:
        for pair in active:
            status = fetch_json(f"{MARTIN_API}/api/grid/status/{pair}")
            if status:
                grids.append({
                    "pair": pair.replace("PF_", "").replace("USD", ""),
                    "lev": status.get("leverage"),
                    "rt": status.get("completedRoundTrips", 0),
                    "fills": len(status.get("fills", [])),
                    "profit": status.get("totalProfit", 0),
                    "mode": status.get("gridMode", "NEUTRAL"),
                })

    trade_stats = {}
    if stats:
        trade_stats = {
            "total": stats.get("totalTrades", 0),
            "pnl": stats.get("totalPnl", 0),
            "wr": stats.get("winRate", 0),
        }

    return pf, grids, trade_stats


def build_brief():
    prices = get_prices()
    pf, grids, trade_stats = get_martin_status()

    lines = ["☀️ MORNING BRIEF — Niam-Bay", ""]

    # Market
    lines.append("📊 MARCHÉ:")
    for name in ["BTC", "ETH", "SOL", "DOT", "XRP"]:
        if name in prices:
            p = prices[name]
            arrow = "🟢" if p["change"] >= 0 else "🔴"
            lines.append(f"  {arrow} {name}: ${p['price']:,.2f} ({p['change']:+.1f}%)")

    # Portfolio
    lines.append(f"\n💰 PORTFOLIO: ${pf}")

    # Grids
    if grids:
        lines.append(f"\n⚡ GRIDS ({len(grids)} actives):")
        for g in grids:
            lines.append(f"  {g['pair']} x{g['lev']} {g['mode']}: {g['rt']}RT {g['fills']}fills +${g['profit']}")
    else:
        lines.append("\n⚡ GRIDS: aucune (mode cash)")

    # Stats
    if trade_stats.get("total", 0) > 0:
        lines.append(f"\n📈 STATS: {trade_stats['total']} trades, PnL ${trade_stats['pnl']}, WR {trade_stats['wr']}%")

    # Recommendation
    lines.append("\n🎯 PLAN:")
    bearish = sum(1 for p in prices.values() if p["change"] < -2)
    if bearish >= 3:
        lines.append("  Marché baissier. Rester en CASH.")
    elif bearish >= 1:
        lines.append("  Marché mixte. Grid prudent x5 si Triple Lock vert.")
    else:
        lines.append("  Marché stable/vert. Grid x5 DOT 1% + SOL 2%.")

    return "\n".join(lines)


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = json.dumps({"chat_id": CHAT_ID, "text": text}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10)
    except:
        pass


def main():
    brief = build_brief()
    print(brief)
    send_telegram(brief)
    print("\nSent to Telegram.")


if __name__ == "__main__":
    main()
