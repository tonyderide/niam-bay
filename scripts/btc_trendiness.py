#!/usr/bin/env python3
"""Filtre de régime BTC pour le grid neutre (Tony 0623).

Le grid neutre GAGNE en range et SAIGNE en tendance. Ce script mesure la
"directionnalité" de BTC sur une fenêtre (def 24h en 1h) :

    directionnalité = |variation nette| / chemin total parcouru   (en %)

- BAS (peu directionnel) = beaucoup d'aller-retour, peu de net = RANGE → grid OK
- HAUT (très directionnel) = le prix va dans un sens = TENDANCE → grid accumule un bag

Sortie JSON sur stdout : {verdict, score, net_pct, path_pct, price, hours}
verdict ∈ {RANGE, TREND, MIXED}. Hystérésis pour éviter le flip-flop :
  score < RANGE_TH → RANGE  ;  score > TREND_TH → TREND  ;  entre les deux → MIXED.
"""
import json, sys, urllib.request

RANGE_TH = 35.0   # < → range (grid favorable)
TREND_TH = 50.0   # > → tendance (grid risqué)

def klines(symbol, interval, limit):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def trendiness(symbol="BTCUSDT", hours=24):
    b = klines(symbol, "1h", hours)
    o = float(b[0][1]); c = float(b[-1][4])
    closes = [float(x[4]) for x in b]
    net = (c - o) / o * 100.0
    path = sum(abs(closes[i] - closes[i-1]) for i in range(1, len(closes))) / o * 100.0
    score = abs(net) / path * 100.0 if path > 0 else 0.0
    verdict = "RANGE" if score < RANGE_TH else ("TREND" if score > TREND_TH else "MIXED")
    return {
        "verdict": verdict,
        "score": round(score, 1),
        "net_pct": round(net, 2),
        "path_pct": round(path, 2),
        "price": round(c, 0),
        "hours": hours,
    }

if __name__ == "__main__":
    hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
    sym = sys.argv[1] if len(sys.argv) > 1 else "BTCUSDT"
    try:
        print(json.dumps(trendiness(sym, hours)))
    except Exception as e:
        print(json.dumps({"verdict": "ERROR", "error": str(e)}))
        sys.exit(1)
