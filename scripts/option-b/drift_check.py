#!/usr/bin/env python3
"""
Drift check — Kraken truth vs Martin internal grid view.

Cycle 35 (2026-05-12 00h25 Paris). Resoudre via outil ce que le bug 0423
"phantom fills" laisse en suspens: l'absence de comparaison systematique entre
ce que Martin pense (grid/status.levels[].status == 'PLACED' + krakenOrderId)
et ce que Kraken expose (bot/orders, qui interroge live).

Rule applied:
  [verify-via-cancel-test] (patterns.nb1, 0510:08h)
  "validate critical state via Kraken pas Martin internal grid-status"

Detection categories:
  1. phantom_placed: level Martin = PLACED + krakenOrderId, mais ID absent
     de bot/orders. Symptome du bug phantom fills 0423. CRITIQUE.
  2. orphaned_kraken: order Kraken live (lmt non-reduceOnly) qui ne map a
     aucun level Martin. Souvent leftover apres restart ou mauvais cancel.
  3. sl_mismatch: Martin dit stopLossOrderId X et Kraken dit X absent.
     Symptome du bug StopLossManager 0510 (silent failure).
  4. count_drift: total levels.PLACED de Martin != orders.lmt de Kraken pour
     le symbole. Discrepance secondaire.
  5. sl_missing_when_expected: position vivante + stopLossOnExchangeEnabled=true,
     mais stopLossOrderId=null et aucune stop Kraken pour le symbole.
     Cycle 36 (2026-05-12): bug VANISHED persistant apres auto-unstuck trim.
     Position non-protegee Kraken-side, fallback = auto-unstuck L2/L3 + maxLoss.
  6. phantom_fill: levels.hasBuyFill/hasSellFill indiquent une position theorique
     != position Kraken reelle. Symptome du bug phantom fills 0423 cote FILL
     (vs phantom_placed cote ORDER). Cycle 69 (2026-05-22): observe live sur LINK
     2 fills 18:45 UTC meme nanoseconde, krakenUnrealizedPnl=0, positions[] vide.
     CRITIQUE: la grille pense detenir des positions inexistantes.

Output:
  - 1-screen summary
  - append jsonl si drift detecte (data/drifts.jsonl)
  - exit code 0 si propre, 1 si drift detecte (pour cron alert)

Usage:
  python3 scripts/option-b/drift_check.py
  python3 scripts/option-b/drift_check.py --json
  python3 scripts/option-b/drift_check.py --history

0 LLM tokens. Read-only. Stdlib + ssh.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"
DRIFT_FILE = DATA_DIR / "drifts.jsonl"

SSH_KEY = Path.home() / ".ssh" / "martin_vm.key"
VM_HOST = "ubuntu@141.253.108.141"
# Pairs interrogees pour grid/status. Inclut le pool actif courant + ETH/BTC
# qui ont rejoint le setup en cycle 66+ (Tony Agency v2). Pairs inactives
# retournent {"active": false} et sont skip.
PAIRS = ["PF_LINKUSD", "PF_DOTUSD", "PF_SOLUSD", "PF_ADAUSD",
         "PF_ETHUSD", "PF_XBTUSD"]
# Tolerance d'ecart de taille position theorique vs reelle (Kraken arrondit).
PHANTOM_FILL_TOLERANCE = 1e-6


def ssh_fetch() -> dict:
    remote_cmd = (
        "curl -s http://localhost:8081/api/bot/orders; echo '|||'; "
        "curl -s http://localhost:8081/api/bot/positions; echo '|||'; "
        + "; echo '==='; ".join(
            f"curl -s http://localhost:8081/api/grid/status/{p}" for p in PAIRS
        )
    )
    result = subprocess.run(
        ["ssh", "-i", str(SSH_KEY), "-o", "StrictHostKeyChecking=no",
         "-o", "ConnectTimeout=15", VM_HOST, remote_cmd],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"SSH failed (rc={result.returncode}): {result.stderr.strip()}")
    parts = result.stdout.split("|||")
    if len(parts) < 3:
        raise RuntimeError(f"Unexpected response shape (got {len(parts)} parts)")
    orders = json.loads(parts[0].strip())
    positions = json.loads(parts[1].strip())
    grids = {}
    for blob in parts[2].split("==="):
        blob = blob.strip()
        if not blob:
            continue
        g = json.loads(blob)
        grids[g["instrument"]] = g
    return {"orders": orders, "positions": positions, "grids": grids}


def analyze(raw: dict) -> dict:
    orders = raw["orders"]
    grids = raw["grids"]
    positions = raw.get("positions", [])

    # Index Kraken orders by id and by (symbol, type)
    krk_by_id = {o["order_id"]: o for o in orders}
    krk_by_symbol = {}
    for o in orders:
        krk_by_symbol.setdefault(o["symbol"], []).append(o)

    # Index positions by symbol with abs(size)
    pos_by_symbol = {}
    for p in positions:
        sym = p.get("symbol")
        sz = p.get("size")
        if sym and sz is not None and abs(sz) > 1e-9:
            pos_by_symbol[sym] = abs(sz)

    findings = {
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "phantom_placed": [],     # level says PLACED + has krakenOrderId but Kraken doesn't have it
        "orphaned_kraken": [],    # Kraken order exists but no Martin level claims its id
        "sl_mismatch": [],        # grid.stopLossOrderId not in Kraken
        "count_drift": [],        # per-symbol level-PLACED count != Kraken lmt count
        "sl_missing_when_expected": [],  # cycle 36: position vivante + SL active mais aucun stp Kraken
        "phantom_fill": [],       # cycle 69: hasBuyFill/hasSellFill indique position theorique inexistante chez Kraken
        "summary": {},
    }

    # Track which Kraken order_ids are claimed by some Martin level or SL slot
    claimed_ids = set()

    for pair, g in grids.items():
        if not g.get("active"):
            continue

        levels = g.get("levels", [])
        martin_placed_count = 0
        for lvl in levels:
            if lvl.get("status") == "PLACED" and lvl.get("krakenOrderId"):
                martin_placed_count += 1
                kid = lvl["krakenOrderId"]
                claimed_ids.add(kid)
                if kid not in krk_by_id:
                    findings["phantom_placed"].append({
                        "pair": pair,
                        "level_index": lvl.get("index"),
                        "level_price": lvl.get("price"),
                        "level_side": lvl.get("side"),
                        "ghost_order_id": kid,
                    })

        # phantom_fill: net flag-based position theorique vs reelle Kraken.
        # NEUTRAL grid: hasBuyFill sur buy = +1, hasSellFill sur sell = -1.
        # On compare en count (binaire) plutot qu'en taille pour eviter le
        # calcul amountPerLevel * leverage / price qui est sensible aux
        # arrondis Kraken. La verite binaire suffit pour detecter le bug:
        # si Martin compte N>0 fills nets et Kraken voit 0 position,
        # quelque chose ment.
        net_buy_fills = 0
        net_sell_fills = 0
        for lvl in levels:
            if lvl.get("side") == "buy" and lvl.get("hasBuyFill"):
                net_buy_fills += 1
            if lvl.get("side") == "sell" and lvl.get("hasSellFill"):
                net_sell_fills += 1
        net_fills = net_buy_fills - net_sell_fills
        pos_size_for_pair = pos_by_symbol.get(pair, 0.0)
        if net_fills > 0 and pos_size_for_pair < PHANTOM_FILL_TOLERANCE:
            findings["phantom_fill"].append({
                "pair": pair,
                "martin_net_fills": net_fills,
                "martin_buy_fills": net_buy_fills,
                "martin_sell_fills": net_sell_fills,
                "kraken_position_size": pos_size_for_pair,
                "amountPerLevel_usd": g.get("amountPerLevel"),
                "krakenUnrealizedPnl": g.get("krakenUnrealizedPnl"),
                "note": "grid pense detenir position long, Kraken voit 0 (phantom fill bug 0423)",
            })

        sl_id = g.get("stopLossOrderId")
        sl_enabled = g.get("stopLossOnExchangeEnabled", False)
        pos_size = pos_by_symbol.get(pair, 0.0)
        if sl_id:
            claimed_ids.add(sl_id)
            if sl_id not in krk_by_id:
                findings["sl_mismatch"].append({
                    "pair": pair,
                    "martin_sl_price": g.get("stopLossPrice"),
                    "ghost_sl_id": sl_id,
                })
        elif sl_enabled and pos_size > 1e-9:
            # Position exists + SL configured ON, but Martin has no SL id and (verify) no stop on Kraken.
            kraken_stops = [
                o for o in krk_by_symbol.get(pair, [])
                if o.get("orderType") == "stop"
            ]
            if not kraken_stops:
                findings["sl_missing_when_expected"].append({
                    "pair": pair,
                    "position_size": pos_size,
                    "centerPrice": g.get("centerPrice"),
                    "note": "stopLossOnExchangeEnabled=true mais stopLossOrderId=null et 0 stop Kraken (bug VANISHED probable)",
                })

        # Count drift: lmt orders on Kraken for that pair (excluding SL stops)
        kraken_lmts = [
            o for o in krk_by_symbol.get(pair, [])
            if o.get("orderType") == "lmt"
        ]
        if len(kraken_lmts) != martin_placed_count:
            findings["count_drift"].append({
                "pair": pair,
                "martin_levels_placed": martin_placed_count,
                "kraken_lmt_orders": len(kraken_lmts),
            })

    # Orphans: Kraken orders for known pairs whose id wasn't claimed
    known_pairs = {p for p, g in grids.items() if g.get("active")}
    for o in orders:
        if o["symbol"] not in known_pairs:
            continue
        if o["order_id"] in claimed_ids:
            continue
        # reduceOnly limit orders (TP sells) are NOT level orders in Martin's view
        # for sell levels — Martin tracks them via the sell-side level. Skip them
        # if reduceOnly + lmt; only flag if it's a fresh-buy lmt or a stop without claim.
        if o.get("reduceOnly") and o.get("orderType") == "lmt":
            # Could still be unclaimed — but Martin pattern is to post these as
            # "sell" level krakenOrderId. If not claimed, it IS an orphan.
            pass
        findings["orphaned_kraken"].append({
            "pair": o["symbol"],
            "side": o["side"],
            "orderType": o["orderType"],
            "limitPrice": o.get("limitPrice"),
            "stopPrice": o.get("stopPrice"),
            "reduceOnly": o.get("reduceOnly"),
            "order_id": o["order_id"],
        })

    n_phantom = len(findings["phantom_placed"])
    n_orphan = len(findings["orphaned_kraken"])
    n_sl = len(findings["sl_mismatch"])
    n_count = len(findings["count_drift"])
    n_sl_missing = len(findings["sl_missing_when_expected"])
    n_phantom_fill = len(findings["phantom_fill"])
    findings["summary"] = {
        "drift_detected": (n_phantom + n_orphan + n_sl + n_count + n_sl_missing + n_phantom_fill) > 0,
        "phantom_placed": n_phantom,
        "orphaned_kraken": n_orphan,
        "sl_mismatch": n_sl,
        "count_drift": n_count,
        "sl_missing_when_expected": n_sl_missing,
        "phantom_fill": n_phantom_fill,
        "verdict": classify(n_phantom, n_orphan, n_sl, n_count, n_sl_missing, n_phantom_fill),
    }
    return findings


def classify(p: int, o: int, s: int, c: int, sm: int, pf: int) -> str:
    if p > 0 or s > 0 or sm > 0 or pf > 0:
        return "CRITIQUE"  # phantom/SL/SL-missing/phantom-fill = silent failure category
    if c > 0:
        return "WARN"      # count drift = inconsistency but not necessarily silent
    if o > 0:
        return "INFO"      # orphans = often expected leftover, low-priority
    return "PROPRE"


def fmt_report(f: dict) -> str:
    s = f["summary"]
    out = []
    out.append(f"# Drift check — {f['ts']}")
    out.append(f"Verdict: **{s['verdict']}**")
    out.append("")
    out.append(f"phantom_placed: {s['phantom_placed']} | phantom_fill: {s.get('phantom_fill', 0)} | "
               f"sl_mismatch: {s['sl_mismatch']} | "
               f"sl_missing: {s.get('sl_missing_when_expected', 0)} | "
               f"count_drift: {s['count_drift']} | orphaned_kraken: {s['orphaned_kraken']}")
    out.append("")
    if f.get("phantom_fill"):
        out.append("## PHANTOM fill (Martin compte des fills sans position Kraken)")
        for x in f["phantom_fill"]:
            out.append(f"  - {x['pair']} net_fills={x['martin_net_fills']} "
                       f"(buy={x['martin_buy_fills']} sell={x['martin_sell_fills']}) "
                       f"kraken_pos={x['kraken_position_size']:.6f} "
                       f"krakenUnrealizedPnl={x.get('krakenUnrealizedPnl', 0)}")
    if f["phantom_placed"]:
        out.append("## PHANTOM placed (level dit PLACED, Kraken n'a pas l'order)")
        for x in f["phantom_placed"]:
            out.append(f"  - {x['pair']} idx={x['level_index']} {x['level_side']} @ {x['level_price']} "
                       f"ghost_id={x['ghost_order_id'][:8]}...")
    if f["sl_mismatch"]:
        out.append("## SL mismatch (StopLossManager bug 0510 type)")
        for x in f["sl_mismatch"]:
            out.append(f"  - {x['pair']} SL price {x['martin_sl_price']} "
                       f"ghost_id={x['ghost_sl_id'][:8]}...")
    if f.get("sl_missing_when_expected"):
        out.append("## SL missing (position vivante + SL active mais aucun stp Kraken — bug VANISHED)")
        for x in f["sl_missing_when_expected"]:
            out.append(f"  - {x['pair']} pos={x['position_size']:.4f} center={x['centerPrice']} "
                       f"→ {x['note']}")
    if f["count_drift"]:
        out.append("## Count drift (Martin PLACED count != Kraken lmt count)")
        for x in f["count_drift"]:
            out.append(f"  - {x['pair']} Martin={x['martin_levels_placed']} "
                       f"vs Kraken_lmt={x['kraken_lmt_orders']}")
    if f["orphaned_kraken"]:
        out.append("## Orphaned Kraken orders (no Martin level claims)")
        for x in f["orphaned_kraken"]:
            kind = x["orderType"]
            price = x.get("limitPrice") or x.get("stopPrice")
            ro = " reduceOnly" if x.get("reduceOnly") else ""
            out.append(f"  - {x['pair']} {x['side']} {kind} @ {price}{ro} id={x['order_id'][:8]}...")
    if not s["drift_detected"]:
        out.append("Aucun drift. Kraken et Martin internal sont coherents.")
    return "\n".join(out)


def append_drift(f: dict):
    if not f["summary"]["drift_detected"]:
        return
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with DRIFT_FILE.open("a") as fh:
        fh.write(json.dumps(f) + "\n")


def cmd_history():
    if not DRIFT_FILE.exists():
        print("Aucun drift enregistre.")
        return
    lines = DRIFT_FILE.read_text().splitlines()
    print(f"# Drift history — {len(lines)} entrees\n")
    for line in lines:
        f = json.loads(line)
        s = f["summary"]
        print(f"{f['ts']:<26} {s['verdict']:<10} phantom={s['phantom_placed']} "
              f"fill={s.get('phantom_fill', 0)} sl={s['sl_mismatch']} "
              f"count={s['count_drift']} orphan={s['orphaned_kraken']}")


def main():
    ap = argparse.ArgumentParser(description="Drift check Kraken vs Martin")
    ap.add_argument("--history", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.history:
        cmd_history()
        return

    raw = ssh_fetch()
    f = analyze(raw)
    append_drift(f)

    if args.json:
        print(json.dumps(f, indent=2))
    else:
        print(fmt_report(f))

    sys.exit(1 if f["summary"]["drift_detected"] else 0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
