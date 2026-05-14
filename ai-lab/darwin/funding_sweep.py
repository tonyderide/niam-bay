#!/usr/bin/env python3
"""Funding harvest backtest on Kraken Futures perps.

Strategy:
- Fetch historical funding rates from Kraken (resolution = 4h ticks)
- For each pair, simulate: short if funding > +threshold, long if < -threshold
- Hold position N hours, encash funding rate × notional × duration_periods
- Account for entry/exit fees + price drift (mark-to-market)
"""
import json, urllib.request, time
from pathlib import Path

CACHE_DIR = Path(__file__).parent / "data_cache"
CACHE_DIR.mkdir(exist_ok=True)

# Kraken Futures perp symbols
PAIRS = [
    "PF_XBTUSD", "PF_ETHUSD", "PF_LINKUSD", "PF_SOLUSD", "PF_DOTUSD", "PF_ADAUSD",
    "PF_LTCUSD", "PF_ATOMUSD", "PF_AVAXUSD", "PF_AAVEUSD", "PF_UNIUSD", "PF_INJUSD",
    "PF_NEARUSD", "PF_FILUSD", "PF_DOGEUSD", "PF_XRPUSD", "PF_OPUSD", "PF_ARBUSD",
    "PF_APTUSD", "PF_SUIUSD", "PF_TIAUSD",
]
FUNDING_THRESHOLDS = [0.0001, 0.00015, 0.0002, 0.0003]  # per 8h: 0.01% / 0.015% / 0.02% / 0.03%
HOLD_PERIODS = [3, 6, 12, 24]  # hours to hold position
CAPITAL = 30.0
LEVERAGE = 5  # lower lev for funding plays (longer hold)
FEE_RT = 0.001  # entry+exit taker
DAYS_BACK = 30


def fetch_kraken_funding(symbol):
    cache = CACHE_DIR / f"funding_{symbol}_30d.json"
    if cache.exists() and (time.time() - cache.stat().st_mtime) < 86400:
        return json.loads(cache.read_text())
    url = f"https://futures.kraken.com/derivatives/api/v3/historicalfundingrates?symbol={symbol}"
    try:
        d = json.loads(urllib.request.urlopen(url, timeout=20).read())
        rates = d.get("rates", [])
        # rates: list of {timestamp, fundingRate, relativeFundingRate}
        cache.write_text(json.dumps(rates))
        return rates
    except Exception as e:
        print(f"  fetch fail {symbol}: {e}")
        return []


def simulate(rates, threshold, hold_hours):
    """Each rate is paid every 4h (Kraken Futures funding interval).
    rates: list sorted by timestamp ascending (oldest first).
    """
    if len(rates) < 30:
        return None
    notional = CAPITAL * LEVERAGE
    pnl_net = 0.0
    trades = 0
    cooldown_until = 0
    hold_periods = max(1, hold_hours // 4)  # convert hours to 4h periods

    for i, r in enumerate(rates):
        ts = r.get("timestamp", "")
        rate = float(r.get("fundingRate", 0))
        if i < cooldown_until:
            continue
        # Decision: if rate > threshold, short to receive funding
        # if rate < -threshold, long to receive funding
        if abs(rate) < threshold:
            continue
        # Take position, hold N periods
        if i + hold_periods >= len(rates):
            break
        # Sum of funding paid to us during hold
        funding_received = 0.0
        for j in range(hold_periods):
            funding_received += abs(float(rates[i+j].get("fundingRate", 0))) * notional
        # Subtract entry+exit fees
        trade_pnl = funding_received - FEE_RT * notional
        # Note: ignore price drift (assumes hedge or stable price for funding-pure play)
        pnl_net += trade_pnl
        trades += 1
        cooldown_until = i + hold_periods + 1

    pnl_pct = pnl_net / CAPITAL * 100
    return {
        "trades": trades, "pnl_net": round(pnl_net, 4),
        "pnl_pct": round(pnl_pct, 2),
    }


def main():
    print(f"Funding Harvest sweep | cap=${CAPITAL} lev={LEVERAGE}x fee_rt={FEE_RT*100}%")
    print(f"Pairs={len(PAIRS)} thresholds={FUNDING_THRESHOLDS} hold_hours={HOLD_PERIODS}")
    print()
    for sym in PAIRS:
        print(f"  fetching funding {sym}...", end="")
        rates = fetch_kraken_funding(sym)
        print(f" {len(rates)} rates")
        time.sleep(0.5)

    print(f"\nRunning sims...")
    results = []
    for sym in PAIRS:
        rates_path = CACHE_DIR / f"funding_{sym}_30d.json"
        if not rates_path.exists(): continue
        rates = json.loads(rates_path.read_text())
        if len(rates) < 30: continue
        # Take last 30 days = ~180 ticks (4h each)
        rates = rates[-180:]
        for th in FUNDING_THRESHOLDS:
            for hh in HOLD_PERIODS:
                r = simulate(rates, th, hh)
                if r is None: continue
                r["pair"] = sym.replace("PF_", "").replace("USD", "")
                r["threshold"] = th; r["hold_h"] = hh
                results.append(r)

    results.sort(key=lambda x: -x["pnl_net"])
    print(f"\n=== TOP 20 par PnL net 30d ===")
    print(f"{'pair':6}{'th%/8h':9}{'hold_h':8}{'trades':8}{'PnL$':10}{'PnL%':8}")
    for r in results[:20]:
        print(f"{r['pair']:6}{r['threshold']*100:7.3f}% {r['hold_h']:7d}{r['trades']:7d}{r['pnl_net']:+8.3f}  {r['pnl_pct']:+6.2f}%")

    best = {}
    for r in results:
        if r["pnl_net"] <= 0: continue
        if r["pair"] not in best or r["pnl_net"] > best[r["pair"]]["pnl_net"]:
            best[r["pair"]] = r
    print(f"\n=== Meilleur par pair (PnL>0) — {len(best)}/{len(PAIRS)} ===")
    for p, r in sorted(best.items(), key=lambda x: -x[1]["pnl_net"]):
        print(f"  {p:6} th={r['threshold']*100:.3f}% hold={r['hold_h']}h → {r['trades']} trades PnL=${r['pnl_net']:+.3f} ({r['pnl_pct']:+.2f}%)")

    profitable = sorted(best.values(), key=lambda x: -x["pnl_net"])
    print(f"\n=== Portfolios funding harvest ===")
    for n in [3, 5, 8]:
        if len(profitable) < n: continue
        top = profitable[:n]
        total_pnl = sum(r["pnl_net"] for r in top)
        total_cap = n * CAPITAL
        print(f"  Top-{n}: {', '.join(r['pair'] for r in top)} → ${total_pnl:+.2f} / ${total_cap} = {total_pnl/total_cap*100:+.2f}% net 30d")

    Path("funding_sweep_results.json").write_text(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
