#!/usr/bin/env python3
"""
Option B Tracker — snapshot live Martin state and compare to backtest curve.

Cycle 33 (2026-05-11 12h25 Paris) lesson:
  "Apres deploy, faire comparable vs best-known pour quantifier le cout
   de la prudence". Cycle 34 (this file) implements that.

What it does:
  - SSH to VM, fetch /api/system/status + /api/bot/balance + /api/grid/active
    + per-grid /api/grid/status
  - Append a compact JSON snapshot to data/snapshots.jsonl
  - Compute expected portfolio value vs backtest (linear interpolation
    of +15.9% / 30j net) and report deviation
  - Print 1-screen summary

Deploy ref: 2026-05-11 13:00 Paris (Option B strategy v9)
  Baseline PV: $138.21 (post-LINK-close pre-deploy realized +$1.00)
  Backtest projection: +15.9% / 30j net (volume-validated, 1min granularity)
  Live derate expectation: 50% -> ~+8% / 30j realistic ($138.21 -> $149.27)

Usage:
  python3 scripts/option-b/tracker.py             # snapshot + report
  python3 scripts/option-b/tracker.py --history   # show all past snapshots
  python3 scripts/option-b/tracker.py --json      # raw JSON (for scripting)

State:
  scripts/option-b/data/snapshots.jsonl  (1 JSON per line, append-only)

0 LLM tokens. Pure stdlib + ssh. Re-entrant.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

# ---- constants (Option B deploy ref) ----
DEPLOY_TS_UTC = dt.datetime(2026, 5, 11, 11, 0, 0, tzinfo=dt.timezone.utc)  # 13h Paris = 11h UTC
DEPLOY_PV = 138.21
BACKTEST_NET_30D = 0.159       # +15.9% net over 30 days (volume-validated sweep)
LIVE_DERATE = 0.50              # rule: derate live to 50% of backtest
EXPECTED_NET_30D = BACKTEST_NET_30D * LIVE_DERATE  # = +7.95%/30j realistic

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"
SNAP_FILE = DATA_DIR / "snapshots.jsonl"

SSH_KEY = Path.home() / ".ssh" / "martin_vm.key"
VM_HOST = "ubuntu@141.253.108.141"
PAIRS = ["PF_LINKUSD", "PF_DOTUSD", "PF_SOLUSD", "PF_ADAUSD"]


def ssh_fetch() -> dict:
    """Run a single SSH command that returns all needed JSON blobs."""
    remote_cmd = (
        "curl -s http://localhost:8081/api/system/status; echo '|||'; "
        "curl -s http://localhost:8081/api/bot/balance; echo '|||'; "
        "curl -s http://localhost:8081/api/grid/active; echo '|||'; "
        + "; echo '==='; ".join(
            f"curl -s http://localhost:8081/api/grid/status/{p}" for p in PAIRS
        )
        + "; echo '|||'; "
        "curl -s 'http://localhost:8081/api/signal/ema_trend?instrument=PF_XBTUSD'"
    )
    result = subprocess.run(
        [
            "ssh",
            "-i", str(SSH_KEY),
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=15",
            VM_HOST,
            remote_cmd,
        ],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"SSH failed (rc={result.returncode}): {result.stderr.strip()}")
    parts = result.stdout.split("|||")
    if len(parts) < 5:
        raise RuntimeError(f"Unexpected response shape (got {len(parts)} parts)")

    system = json.loads(parts[0].strip())
    balance = json.loads(parts[1].strip())
    active = json.loads(parts[2].strip())
    grids_raw = parts[3].split("===")
    grids = {}
    for blob in grids_raw:
        blob = blob.strip()
        if not blob:
            continue
        g = json.loads(blob)
        grids[g["instrument"]] = g
    btc = json.loads(parts[4].strip())
    return {"system": system, "balance": balance, "active": active, "grids": grids, "btc": btc}


def build_snapshot(raw: dict) -> dict:
    flex = raw["balance"]["accounts"]["flex"]
    pv = flex.get("portfolioValue")
    bal = flex.get("balanceValue")
    upnl = flex.get("totalUnrealized") or flex.get("pnl")
    snap = {
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "pv": pv,
        "balanceValue": bal,
        "uPnL": upnl,
        "uptime_h": raw["system"].get("uptime_seconds", 0) / 3600.0,
        "btc": {
            "price": raw["btc"].get("price"),
            "ema200": raw["btc"].get("ema200"),
            "rsi": raw["btc"].get("rsi"),
            "trend": raw["btc"].get("emaStatus"),
            "signal": raw["btc"].get("signal"),
        },
        "active_grids": raw["active"],
        "per_grid": {},
    }
    for pair, g in raw["grids"].items():
        if not g.get("active"):
            continue
        snap["per_grid"][pair] = {
            "capital": g.get("capital"),
            "krakenUnrealizedPnl": g.get("krakenUnrealizedPnl"),
            "krakenRealizedPnl": g.get("krakenRealizedPnl"),
            "completedRoundTrips": g.get("completedRoundTrips"),
            "centerPrice": g.get("centerPrice"),
            "stopLossPrice": g.get("stopLossPrice"),
            "closeOnly": g.get("closeOnly"),
            "fills_count": len(g.get("fills", [])),
            "startedAt": g.get("startedAt"),
        }
    return snap


def expected_pv_at(ts: dt.datetime) -> dict:
    """Compute expected PV at given UTC datetime, linear interpolation from deploy."""
    if ts < DEPLOY_TS_UTC:
        return {"expected_realistic": DEPLOY_PV, "expected_backtest": DEPLOY_PV,
                "elapsed_days": 0.0, "progress_pct": 0.0}
    elapsed = (ts - DEPLOY_TS_UTC).total_seconds() / 86400.0
    progress = elapsed / 30.0  # fraction of 30j window
    realistic = DEPLOY_PV * (1.0 + EXPECTED_NET_30D * progress)
    backtest = DEPLOY_PV * (1.0 + BACKTEST_NET_30D * progress)
    return {
        "expected_realistic": realistic,
        "expected_backtest": backtest,
        "elapsed_days": elapsed,
        "progress_pct": progress * 100.0,
    }


def diagnose(snap: dict) -> dict:
    ts = dt.datetime.fromisoformat(snap["ts"])
    exp = expected_pv_at(ts)
    actual = snap["pv"]
    diff_vs_realistic = actual - exp["expected_realistic"]
    diff_vs_backtest = actual - exp["expected_backtest"]
    pct_vs_realistic = (diff_vs_realistic / exp["expected_realistic"]) * 100.0
    pct_vs_backtest = (diff_vs_backtest / exp["expected_backtest"]) * 100.0
    return {
        "elapsed_days": exp["elapsed_days"],
        "progress_pct_of_30d": exp["progress_pct"],
        "actual_pv": actual,
        "expected_realistic_pv": exp["expected_realistic"],
        "expected_backtest_pv": exp["expected_backtest"],
        "diff_vs_realistic_usd": diff_vs_realistic,
        "diff_vs_realistic_pct": pct_vs_realistic,
        "diff_vs_backtest_usd": diff_vs_backtest,
        "diff_vs_backtest_pct": pct_vs_backtest,
        "cumul_vs_deploy_usd": actual - DEPLOY_PV,
        "cumul_vs_deploy_pct": ((actual - DEPLOY_PV) / DEPLOY_PV) * 100.0,
    }


def append_snapshot(snap: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with SNAP_FILE.open("a") as f:
        f.write(json.dumps(snap) + "\n")


def load_snapshots() -> list[dict]:
    if not SNAP_FILE.exists():
        return []
    out = []
    for line in SNAP_FILE.read_text().splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def fmt_report(snap: dict, diag: dict) -> str:
    btc = snap["btc"]
    lines = []
    lines.append(f"# Option B Tracker — {snap['ts']}")
    lines.append(
        f"Deploy: {DEPLOY_TS_UTC.isoformat()} | baseline ${DEPLOY_PV:.2f} | "
        f"backtest +{BACKTEST_NET_30D*100:.1f}%/30j (live ~+{EXPECTED_NET_30D*100:.1f}%/30j)"
    )
    lines.append("")
    lines.append(f"## Etat live")
    lines.append(f"PV ${snap['pv']:.2f} | uPnL ${snap['uPnL']:+.3f} | "
                 f"grids actives {len(snap['active_grids'])} ({', '.join(snap['active_grids'])})")
    if btc.get("price"):
        cushion = (btc["price"] - btc["ema200"]) / btc["ema200"] * 100.0
        lines.append(
            f"BTC ${btc['price']:,.0f} {btc['trend']} | EMA200 ${btc['ema200']:,.0f} "
            f"(+{cushion:.2f}%) | RSI {btc['rsi']:.1f} | signal {btc['signal']}"
        )
    lines.append("")

    lines.append("## Par grid")
    for pair, g in snap["per_grid"].items():
        co = " CLOSE-ONLY" if g.get("closeOnly") else ""
        sl = f"SL ${g['stopLossPrice']}" if g["stopLossPrice"] else "SL none"
        lines.append(
            f"- {pair:<12} cap ${g['capital']:.0f} | uPnL "
            f"${g['krakenUnrealizedPnl']:+.4f} | RT {g['completedRoundTrips']} | "
            f"fills {g['fills_count']} | {sl}{co}"
        )
    lines.append("")

    lines.append("## Vs backtest")
    lines.append(
        f"Ecoulé: {diag['elapsed_days']:.2f}j "
        f"({diag['progress_pct_of_30d']:.1f}% du 30j)"
    )
    lines.append(
        f"Cumul deploy: {diag['cumul_vs_deploy_usd']:+.2f}$ "
        f"({diag['cumul_vs_deploy_pct']:+.3f}%)"
    )
    lines.append(
        f"Vs realistic curve ({EXPECTED_NET_30D*100:.1f}%/30j): "
        f"{diag['diff_vs_realistic_usd']:+.2f}$ ({diag['diff_vs_realistic_pct']:+.2f}%)"
    )
    lines.append(
        f"Vs backtest curve ({BACKTEST_NET_30D*100:.1f}%/30j): "
        f"{diag['diff_vs_backtest_usd']:+.2f}$ ({diag['diff_vs_backtest_pct']:+.2f}%)"
    )
    lines.append("")

    # Verdict
    pct_r = diag["diff_vs_realistic_pct"]
    if diag["elapsed_days"] < 1.0:
        verdict = "TROP-TOT (< 24h, bruit dominant)"
    elif pct_r > 2.0:
        verdict = "AHEAD du curve realistic (>+2%)"
    elif pct_r > -2.0:
        verdict = "ON-TRACK (+/- 2% du curve realistic)"
    elif pct_r > -5.0:
        verdict = "BEHIND mais tolerable (-2 a -5%)"
    else:
        verdict = "BEHIND-CRITIQUE (< -5% vs realistic)"
    lines.append(f"Verdict: **{verdict}**")
    return "\n".join(lines)


def cmd_history():
    snaps = load_snapshots()
    if not snaps:
        print("Aucun snapshot encore. Lance le tracker sans argument.")
        return
    print(f"# History — {len(snaps)} snapshots\n")
    print(f"{'TS':<26} {'PV':>9} {'uPnL':>8} {'Δ deploy':>10} {'vs real':>9} grids")
    for s in snaps:
        d = diagnose(s)
        pv = s["pv"]
        upnl = s["uPnL"] or 0.0
        cu = d["cumul_vs_deploy_usd"]
        vr = d["diff_vs_realistic_usd"]
        ng = len(s["active_grids"])
        print(f"{s['ts']:<26} ${pv:>7.2f} ${upnl:>+7.3f} ${cu:>+8.2f} ${vr:>+7.2f} {ng}")


def main():
    ap = argparse.ArgumentParser(description="Option B tracker")
    ap.add_argument("--history", action="store_true", help="show all past snapshots")
    ap.add_argument("--json", action="store_true", help="output raw JSON only")
    ap.add_argument("--no-save", action="store_true", help="don't append to snapshots.jsonl")
    args = ap.parse_args()

    if args.history:
        cmd_history()
        return

    raw = ssh_fetch()
    snap = build_snapshot(raw)
    diag = diagnose(snap)

    if not args.no_save:
        append_snapshot(snap)

    if args.json:
        print(json.dumps({"snapshot": snap, "diagnosis": diag}, indent=2))
    else:
        print(fmt_report(snap, diag))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
