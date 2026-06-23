#!/usr/bin/env python3
"""Mesure la "demande" (pression acheteur/vendeur) sur un actif perp (Tony 0623).

Complément du filtre de régime BTC (btc_trendiness.py) : BTC donne le régime
global, ce script donne la pression LOCALE sur un actif. Trois signaux live
(données Binance Futures, proxy de demande de l'actif) :

  1. funding  : taux de funding perp = positionnement (>0 longs paient, <0 shorts paient)
  2. imbalance: déséquilibre du carnet top-100 (bids vs asks) = demande au repos
  3. taker    : delta des trades agressifs (acheteurs au marché vs vendeurs)

Score net = moyenne(imbalance, taker) en %. Verdict :
  |score| < BALANCED_TH  → EQUILIBRE (range-friendly, bon pour le grid neutre)
  score >  ONE_SIDED_TH  → DEMANDE_LONG (pression acheteuse one-sided → move haussier probable)
  score < -ONE_SIDED_TH  → DEMANDE_SHORT (pression vendeuse one-sided → move baissier probable)

Sortie JSON sur stdout. Usage: asset_demand.py [SYMBOL=DOTUSDT]
"""
import json, sys, urllib.request

BALANCED_TH = 15.0   # |score| < → équilibré
ONE_SIDED_TH = 25.0  # |score| > → déséquilibre marqué

FAPI = "https://fapi.binance.com/fapi/v1"

def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def demand(symbol="DOTUSDT"):
    fr = float(_get(f"{FAPI}/premiumIndex?symbol={symbol}")["lastFundingRate"]) * 100.0
    d = _get(f"{FAPI}/depth?symbol={symbol}&limit=100")
    bid = sum(float(q) for _, q in d["bids"]); ask = sum(float(q) for _, q in d["asks"])
    imb = (bid - ask) / (bid + ask) * 100.0 if (bid + ask) else 0.0
    at = _get(f"{FAPI}/aggTrades?symbol={symbol}&limit=1000")
    buyv = sum(float(t["q"]) for t in at if not t["m"])   # m=false => taker BUY
    sellv = sum(float(t["q"]) for t in at if t["m"])       # m=true  => taker SELL
    taker = (buyv - sellv) / (buyv + sellv) * 100.0 if (buyv + sellv) else 0.0
    score = (imb + taker) / 2.0
    if abs(score) < BALANCED_TH:
        verdict = "EQUILIBRE"
    elif score > ONE_SIDED_TH:
        verdict = "DEMANDE_LONG"
    elif score < -ONE_SIDED_TH:
        verdict = "DEMANDE_SHORT"
    else:
        verdict = "MIXTE"
    return {
        "symbol": symbol, "verdict": verdict, "score": round(score, 1),
        "funding_pct": round(fr, 4), "imbalance_pct": round(imb, 1),
        "taker_delta_pct": round(taker, 1),
    }

if __name__ == "__main__":
    sym = sys.argv[1] if len(sys.argv) > 1 else "DOTUSDT"
    try:
        print(json.dumps(demand(sym)))
    except Exception as e:
        print(json.dumps({"verdict": "ERROR", "error": str(e)}))
        sys.exit(1)
