#!/usr/bin/env python3
"""Microstructure de marché pour piloter le grid neutre (Tony 0624).

Quatre lentilles demandées par Tony, toutes calculées sur données live Binance
Futures (gratuit, déjà utilisé par btc_trendiness.py / asset_demand.py) :

  1. VOLUME PROFILE  : distribution du volume échangé par niveau de prix sur 24h.
       - POC  (Point of Control) = prix le plus échangé = aimant / centre naturel.
       - VAH/VAL = bornes de la "value area" (70% du volume) = range probable.
       - HVN (high-volume nodes) = zones où le prix colle (bon pour le grid).
       - LVN (low-volume nodes)  = zones où le prix traverse vite (à éviter).
  2. VWAP            : prix moyen pondéré volume + bandes ±1σ/±2σ = ancre de
       réversion. Prix loin du VWAP = tension; prix qui oscille autour = range.
  3. DEEP TRADES/CVD : delta des trades agressifs (acheteurs vs vendeurs au marché)
       + isolation des GROS trades (top 5% taille = "deep"/baleines). Net signé =
       qui pousse vraiment. Équilibré → range; one-sided → tendance en formation.
  4. LIQUIDITY WALLS : plus gros murs de liquidité au repos dans le carnet (proxy
       du heatmap sur un snapshot). Murs bid = support, murs ask = résistance =
       bornes candidates du range / aimants à liquidation.

SYNTHÈSE : positionne le prix courant vs POC/VWAP/value-area, mesure la distance
aux murs, et émet une reco GRID : centre suggéré, bornes suggérées, et si la
microstructure est range-friendly (déployer) ou trend-y (rester cash).

Usage: market_microstructure.py [SYMBOL=BTCUSDT] [HOURS=24]
Sortie: JSON sur stdout (+ résumé lisible sur stderr si --human).
"""
import json
import sys
import urllib.request

FAPI = "https://fapi.binance.com/fapi/v1"
N_BUCKETS = 60
VALUE_AREA_PCT = 0.70
LARGE_TRADE_PCTL = 0.95     # top 5% des tailles = "deep" trades
WALL_BUCKETS = 80           # granularité de l'agrégation du carnet
BALANCED_CVD_TH = 12.0      # |cvd%| < → flux équilibré (range)
ONE_SIDED_CVD_TH = 25.0     # |cvd%| > → flux directionnel (tendance)


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def volume_profile(klines):
    highs = [float(k[2]) for k in klines]
    lows = [float(k[3]) for k in klines]
    vols = [float(k[5]) for k in klines]
    lo, hi = min(lows), max(highs)
    if hi <= lo:
        return None
    width = (hi - lo) / N_BUCKETS
    buckets = [0.0] * N_BUCKETS
    for h, l, v in zip(highs, lows, vols):
        b_lo = int((l - lo) / width)
        b_hi = int((h - lo) / width)
        b_lo = max(0, min(N_BUCKETS - 1, b_lo))
        b_hi = max(0, min(N_BUCKETS - 1, b_hi))
        span = b_hi - b_lo + 1
        share = v / span
        for b in range(b_lo, b_hi + 1):
            buckets[b] += share
    total = sum(buckets)
    poc_idx = max(range(N_BUCKETS), key=lambda i: buckets[i])
    # value area: grandir autour du POC jusqu'à 70% du volume
    lo_i = hi_i = poc_idx
    acc = buckets[poc_idx]
    while acc < VALUE_AREA_PCT * total and (lo_i > 0 or hi_i < N_BUCKETS - 1):
        up = buckets[hi_i + 1] if hi_i < N_BUCKETS - 1 else -1
        dn = buckets[lo_i - 1] if lo_i > 0 else -1
        if up >= dn:
            hi_i += 1
            acc += buckets[hi_i]
        else:
            lo_i -= 1
            acc += buckets[lo_i]

    def price_of(i):
        return lo + (i + 0.5) * width

    avg = total / N_BUCKETS
    hvn = sorted(
        [round(price_of(i), 4) for i in range(N_BUCKETS) if buckets[i] > 1.6 * avg]
    )
    lvn = sorted(
        [round(price_of(i), 4) for i in range(N_BUCKETS)
         if buckets[i] < 0.35 * avg and lo_i <= i <= hi_i]
    )
    return {
        "poc": round(price_of(poc_idx), 4),
        "vah": round(price_of(hi_i), 4),
        "val": round(price_of(lo_i), 4),
        "value_area_width_pct": round((price_of(hi_i) - price_of(lo_i)) / price_of(poc_idx) * 100, 2),
        "range_lo": round(lo, 4),
        "range_hi": round(hi, 4),
        "hvn": hvn[:6],
        "lvn_in_value": lvn[:6],
    }


def vwap_bands(klines):
    num = den = 0.0
    tps = []
    for k in klines:
        h, l, c, v = float(k[2]), float(k[3]), float(k[4]), float(k[5])
        tp = (h + l + c) / 3.0
        tps.append((tp, v))
        num += tp * v
        den += v
    if den <= 0:
        return None
    vwap = num / den
    var = sum(v * (tp - vwap) ** 2 for tp, v in tps) / den
    sigma = var ** 0.5
    return {
        "vwap": round(vwap, 4),
        "upper_1s": round(vwap + sigma, 4),
        "lower_1s": round(vwap - sigma, 4),
        "upper_2s": round(vwap + 2 * sigma, 4),
        "lower_2s": round(vwap - 2 * sigma, 4),
        "sigma_pct": round(sigma / vwap * 100, 2),
    }


def deep_trades(symbol):
    at = _get(f"{FAPI}/aggTrades?symbol={symbol}&limit=1000")
    qtys = sorted(float(t["q"]) for t in at)
    if not qtys:
        return None
    thr = qtys[int(len(qtys) * LARGE_TRADE_PCTL)]
    buy = sell = lbuy = lsell = 0.0
    for t in at:
        q = float(t["q"])
        if t["m"]:          # m=true => taker SELL
            sell += q
            if q >= thr:
                lsell += q
        else:               # taker BUY
            buy += q
            if q >= thr:
                lbuy += q
    tot = buy + sell
    cvd = (buy - sell) / tot * 100 if tot else 0.0
    ltot = lbuy + lsell
    big = (lbuy - lsell) / ltot * 100 if ltot else 0.0
    if abs(cvd) < BALANCED_CVD_TH:
        flow = "EQUILIBRE"
    elif cvd > ONE_SIDED_CVD_TH:
        flow = "PRESSION_ACHAT"
    elif cvd < -ONE_SIDED_CVD_TH:
        flow = "PRESSION_VENTE"
    else:
        flow = "MIXTE"
    return {
        "flow": flow,
        "cvd_pct": round(cvd, 1),
        "big_trade_delta_pct": round(big, 1),
        "big_trade_share_pct": round(ltot / tot * 100, 1) if tot else 0.0,
    }


def liquidity_walls(symbol):
    d = _get(f"{FAPI}/depth?symbol={symbol}&limit=1000")
    bids = [(float(p), float(q)) for p, q in d["bids"]]
    asks = [(float(p), float(q)) for p, q in d["asks"]]
    if not bids or not asks:
        return None
    mid = (bids[0][0] + asks[0][0]) / 2.0

    def top_walls(levels):
        # agrège par bucket de prix puis prend les 3 plus gros
        if not levels:
            return []
        prices = [p for p, _ in levels]
        lo, hi = min(prices), max(prices)
        width = (hi - lo) / WALL_BUCKETS if hi > lo else 1.0
        agg = {}
        for p, q in levels:
            b = int((p - lo) / width) if width else 0
            agg.setdefault(b, [0.0, 0.0, 0.0])
            agg[b][0] += q
            agg[b][1] += p * q
            agg[b][2] += q
        walls = []
        for b, (qsum, pqsum, _) in agg.items():
            vwprice = pqsum / qsum if qsum else lo
            walls.append((round(vwprice, 4), round(qsum, 2)))
        walls.sort(key=lambda x: -x[1])
        return walls[:3]

    bw = top_walls(bids)
    aw = top_walls(asks)
    nearest_bid = max((p for p, _ in bw), default=None)
    nearest_ask = min((p for p, _ in aw), default=None)
    return {
        "mid": round(mid, 4),
        "bid_walls": [{"price": p, "size": q} for p, q in bw],
        "ask_walls": [{"price": p, "size": q} for p, q in aw],
        "support_wall": nearest_bid,
        "resistance_wall": nearest_ask,
        "wall_range_pct": round((nearest_ask - nearest_bid) / mid * 100, 2)
        if (nearest_bid and nearest_ask) else None,
    }


# --- Gates validés par l'agency (conseil 0624) ---
SPACING_FLOOR_PCT = 0.5     # plancher fee-safe live (round-trip taker Kraken)
MIN_LEVELS = 6              # en-dessous = grid pile-ou-face, pas "petit mais tout le temps"
TARGET_LEVELS = 12         # cible Tony "12, 6 de chaque côté"
VA_WIDTH_MIN = 0.8         # value-area trop étroite → spacing ne couvre pas les frais
VA_WIDTH_MAX = 4.0         # trop large → ce n'est pas un range, c'est l'empreinte d'une tendance
SIGMA_MIN = 0.4            # marché mort
SIGMA_MAX = 1.8            # trop violent pour la régularité
CENTER_AGREE_PCT = 0.4     # |VWAP-POC| au-delà = centre ambigu
CVD_VETO = 35.0            # flux agressif extrême = tendance en formation → skip


def synth(price, vp, vw, dt, lw):
    """Verdict deploy validé par l'agency : VP+VWAP+faisabilité décident ;
    murs + CVD sont ADVISORY (CVD = veto extrême uniquement ; murs jamais un
    gate car single-snapshot Binance ≠ venue d'exécution Kraken)."""
    notes = []
    reasons_cash = []

    if not vp or not vw:
        return {"verdict": "ERROR", "notes": ["volume profile / vwap manquant"]}

    # 1. value-area : largeur + position du prix
    va_w = vp["value_area_width_pct"]
    if price > vp["vah"]:
        reasons_cash.append("prix AU-DESSUS de la value area (extension/cassure haute)")
    elif price < vp["val"]:
        reasons_cash.append("prix EN-DESSOUS de la value area (extension/cassure basse)")
    else:
        notes.append("prix DANS la value area (équilibre, grid-friendly)")
    if va_w < VA_WIDTH_MIN:
        reasons_cash.append(f"value-area trop étroite ({va_w}% < {VA_WIDTH_MIN}%)")
    elif va_w > VA_WIDTH_MAX:
        reasons_cash.append(f"value-area trop large ({va_w}% > {VA_WIDTH_MAX}% = tendance)")

    # 2. VWAP : centre + volatilité
    dev = (price - vw["vwap"]) / vw["vwap"] * 100
    sig = vw["sigma_pct"]
    notes.append(f"écart VWAP {dev:+.2f}% | σ {sig}%")
    center_gap = abs(vw["vwap"] - vp["poc"]) / price * 100
    center = vp["poc"] if center_gap < CENTER_AGREE_PCT else round((vp["poc"] + vw["vwap"]) / 2, 6)
    if center_gap >= CENTER_AGREE_PCT:
        notes.append(f"POC≠VWAP ({center_gap:.2f}%) → centre = moyenne (signal affaibli)")
    if sig < SIGMA_MIN:
        reasons_cash.append(f"σ trop faible ({sig}% < {SIGMA_MIN}%)")
    elif sig > SIGMA_MAX:
        reasons_cash.append(f"σ trop élevée ({sig}% > {SIGMA_MAX}%)")

    # 3. faisabilité géométrique (l'apport-clé du conseil) — bornes = value area pure
    lower, upper = vp["val"], vp["vah"]
    box_pct = (upper - lower) / center * 100
    spacing_floor = max(SPACING_FLOOR_PCT, 0.6 * sig)
    max_levels = int(box_pct / spacing_floor)
    feasible = max_levels >= MIN_LEVELS
    if not feasible:
        reasons_cash.append(
            f"INFAISABLE: box {box_pct:.2f}% / spacing {spacing_floor:.2f}% = {max_levels} niveaux < {MIN_LEVELS}"
        )
    levels = min(TARGET_LEVELS, max_levels - (max_levels % 2)) if feasible else 0
    spacing_pct = round(box_pct / levels, 3) if levels else None

    # 4. CVD : ADVISORY, veto extrême seulement
    if dt:
        notes.append(f"[advisory] flux {dt['flow']} CVD {dt['cvd_pct']}% gros {dt['big_trade_delta_pct']}%")
        if abs(dt["cvd_pct"]) > CVD_VETO and dt["flow"] in ("PRESSION_ACHAT", "PRESSION_VENTE"):
            reasons_cash.append(f"VETO flux extrême ({dt['cvd_pct']}% one-sided = tendance)")

    # 5. murs : ADVISORY pur (jamais un gate — Binance ≠ Kraken, spoofable)
    if lw and lw.get("wall_range_pct"):
        notes.append(
            f"[advisory/eyeball] murs Binance corridor {lw['wall_range_pct']}% "
            f"(sup {lw['support_wall']} / rés {lw['resistance_wall']}) — non-contraignant sur Kraken"
        )

    verdict = "DEPLOY" if not reasons_cash else "CASH"
    plan = None
    if verdict == "DEPLOY":
        plan = {
            "center": round(center, 6), "lower": round(lower, 6), "upper": round(upper, 6),
            "gridSpacingPct": spacing_pct, "totalLevels": levels,
            "suggestedLeverage": 2 if sig < 1.0 else 1, "maxLossPercent": 8,
        }
    return {
        "verdict": verdict,
        "reasons_cash": reasons_cash,
        "deploy_plan": plan,
        "box_pct": round(box_pct, 2),
        "max_feasible_levels": max_levels,
        "notes": notes,
    }


def run(symbol="BTCUSDT", hours=24):
    kl = _get(f"{FAPI}/klines?symbol={symbol}&interval=1m&limit={hours*60}")
    price = float(kl[-1][4])
    vp = volume_profile(kl)
    vw = vwap_bands(kl)
    dt = deep_trades(symbol)
    lw = liquidity_walls(symbol)
    return {
        "symbol": symbol, "price": round(price, 4), "hours": hours,
        "volume_profile": vp, "vwap": vw, "deep_trades": dt,
        "liquidity_walls": lw, "synthesis": synth(price, vp, vw, dt, lw),
    }


if __name__ == "__main__":
    sym = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "BTCUSDT"
    hrs = 24
    for a in sys.argv[2:]:
        if a.isdigit():
            hrs = int(a)
    try:
        out = run(sym, hrs)
        print(json.dumps(out, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
