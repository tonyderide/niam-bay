"""PREREG-26 B : test papier en avant du carry du financement (bras B1 = signal Kraken, B2 = signal Binance).
API publiques seulement, aucune clé, AUCUN ordre. Lancé chaque jour vers 00:05 UTC. Idempotent.
Journal : ~/nb/carry-papier/jours.jsonl (une ligne par jour : positions décidées à 00:00 UTC + prix à 00:00)."""
import bisect, calendar, json, os, time, urllib.request
J = 86400000
SYM = ["PF_XBTUSD","PF_DOTUSD","PF_SOLUSD","PF_LINKUSD","PF_ADAUSD","PF_ETHUSD","PF_XRPUSD","PF_LTCUSD","PF_BNBUSD","PF_DOGEUSD","PF_AVAXUSD"]
BIN = dict(zip(SYM, ["BTCUSDT","DOTUSDT","SOLUSDT","LINKUSDT","ADAUSDT","ETHUSDT","XRPUSDT","LTCUSDT","BNBUSDT","DOGEUSDT","AVAXUSDT"]))
DEBUT, FIN, FEE = 1793145600000, 1797984000000, 0.0005   # 28/10/2026 00:00 UTC → 23/12/2026 00:00 UTC
DOS = os.path.expanduser("~/nb/carry-papier"); os.makedirs(DOS, exist_ok=True); JOUR = os.path.join(DOS, "jours.jsonl")
get = lambda u: json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "nb"}), timeout=30))

def fin_kraken(s):
    return [(calendar.timegm(time.strptime(r["timestamp"], "%Y-%m-%dT%H:%M:%SZ")) * 1000, r["relativeFundingRate"])
            for r in get(f"https://futures.kraken.com/derivatives/api/v4/historicalfundingrates?symbol={s}")["rates"]]

def somme(F, a, b, inclut_b=False):
    T = [x[0] for x in F]; f = bisect.bisect_right if inclut_b else bisect.bisect_left
    return sum(x[1] for x in F[f(T, a):f(T, b)])

def prix_a(s, d):  # clôture de la bougie 1 h qui finit à d
    r = get(f"https://futures.kraken.com/api/charts/v1/trade/{s}/1h?from={d//1000 - 3*3600}&to={d//1000}")
    c = [x for x in r.get("candles", []) if int(x["time"]) + 3600000 == d]
    return float(c[0]["close"]) if c else None

def poids(score):
    ok = sorted([s for s in score if score[s] is not None], key=lambda s: score[s]); w = {s: 0.0 for s in SYM}
    if len(ok) >= 6:
        for s in ok[:3]: w[s] = 1/3
        for s in ok[-3:]: w[s] = -1/3
    return w

def noter_jour(d):
    fk = {s: fin_kraken(s) for s in SYM}
    fb = {s: [(x["fundingTime"], float(x["fundingRate"])) for x in
              get(f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={BIN[s]}&startTime={d - 8*J}&endTime={d - 1}&limit=1000")] for s in SYM}
    px = {s: prix_a(s, d) for s in SYM}
    b1 = poids({s: somme(fk[s], d - 7*J, d) if px[s] else None for s in SYM})
    b2 = poids({s: somme(fb[s], d - 7*J, d) if px[s] else None for s in SYM})
    return {"jour_utc": time.strftime("%F", time.gmtime(d / 1000)), "t": d, "prix": px, "B1": b1, "B2": b2, "note": time.strftime("%F %T", time.gmtime())}

def bilan(L):
    fk = {s: fin_kraken(s) for s in SYM}; out = {}
    for bras in ("B1", "B2"):
        prev = {s: 0.0 for s in SYM}; net = 0.0; par = {s: 0.0 for s in SYM}; frais = 0.0
        for a, b in zip(L, L[1:]):
            w = a[bras]
            for s in SYM:
                c = FEE * abs(w[s] - prev[s]); r = (b["prix"][s] / a["prix"][s] - 1) if a["prix"][s] and b["prix"][s] else 0.0
                v = w[s] * r - w[s] * somme(fk[s], a["t"], b["t"], True) - c; par[s] += v; net += v; frais += c
            prev = w
        out[bras] = {"jours": len(L) - 1, "net": net, "frais": frais, "gagnantes": sum(v > 0 for v in par.values()), "par": par}
    return out

if __name__ == "__main__":
    L = [json.loads(l) for l in open(JOUR)] if os.path.exists(JOUR) else []
    vus = {x["t"] for x in L}; maintenant = int(time.time() * 1000)
    d = max(DEBUT, (L[-1]["t"] + J) if L else DEBUT)
    while d <= min(FIN, maintenant - 5 * 60000):
        if d not in vus:
            x = noter_jour(d); L.append(x); open(JOUR, "a").write(json.dumps(x) + "\n")
        d += J
    if len(L) >= 2:
        B = bilan(L); json.dump(B, open(os.path.join(DOS, "bilan.json"), "w"), indent=1)
        print(time.strftime("%F %T"), " · ".join(f"{k} {v['jours']} j net {100*v['net']:+.2f} % gagnantes {v['gagnantes']}/11" for k, v in B.items()))
    else:
        print(time.strftime("%F %T"), "jours notés :", len(L))
