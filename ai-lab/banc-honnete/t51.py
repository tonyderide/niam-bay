"""PREREG-51 : tournant du mois BTC (règles : PREREG-51-tournant-du-mois.md, commit b7e3e7f). Binance comptant 1d public."""
import calendar, datetime as dt, json, os, random, statistics as st, urllib.request
J = 86_400_000; FR = 0.001; F = "t51_btc.json"
if not os.path.exists(F):
    K, t = [], 1502928000000
    while t < 1793491200000:
        k = json.load(urllib.request.urlopen(f"https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&startTime={t}&endTime=1793491199999&limit=1000"))
        if not k: break
        K += [[int(x[0]), float(x[1]), float(x[4])] for x in k]; t = int(k[-1][0]) + J
    json.dump(K, open(F, "w"))
C = {x[0]: (x[1], x[2]) for x in json.load(open(F))}
ms = lambda d: calendar.timegm(d.timetuple()) * 1000
def fen(debut):
    fin = debut + 4 * J
    if debut not in C or fin not in C: return None
    return C[fin][1] / C[debut][0] - 1 - 2 * FR, debut
W = []    # (année/mois suivant, rendement, début, liste des débuts possibles pour le témoin)
for a in range(2017, 2027):
    for m in range(1, 13):
        if (a, m) < (2017, 10) or (a, m) > (2026, 10): continue
        pm = dt.date(a, m, 1) - dt.timedelta(days=1); deb = ms(pm - dt.timedelta(days=1))         # avant-dernier jour du mois précédent
        r = fen(deb)
        if r is None: continue
        jours_mois = [ms(dt.date(pm.year, pm.month, d)) for d in range(1, calendar.monthrange(pm.year, pm.month)[1] + 1)]
        autres = [d for d in jours_mois if abs(d - deb) >= 5 * J and fen(d)]
        W.append(((a, m), r[0], deb, autres))
H = [w for w in W if w[0][0] <= 2025]; S = [w for w in W if w[0][0] == 2026]
def res(X):
    r = [w[1] for w in X]; return dict(n=len(r), moy=st.mean(r), med=st.median(r), pos=sum(v > 0 for v in r) / len(r))
def temoin(X, seed, n=1000):
    rng = random.Random(seed); m = st.mean(w[1] for w in X); t = [st.mean(fen(rng.choice(w[3]))[0] for w in X) for _ in range(n)]
    return st.mean(t), sum(v >= m for v in t) / n
out = dict(hist=res(H), j2026=res(S), par_an={a: res([w for w in W if w[0][0] == a]) for a in sorted({w[0][0] for w in W})})
out["hist"]["temoin_moy"], out["hist"]["p"] = temoin(H, 510)
out["j2026"]["temoin_moy"], out["j2026"]["p"] = temoin(S, 51)
bh = lambda X: C[X[-1][2] + 4 * J][1] / C[X[0][2]][0] - 1
out["acheter_garder"] = dict(hist=bh(H), j2026=bh(S)); out["fenetres_2026"] = [(f"{w[0][0]}-{w[0][1]:02d}", round(w[1], 4)) for w in S]
a, b = out["hist"], out["j2026"]
out["verdict"] = "GAGNE" if a["moy"] > 0 and b["moy"] > 0 and b["p"] < 0.05 else "NON DÉMONTRÉ" if b["moy"] > 0 else "PERD"
json.dump(out, open("t51.json", "w"), indent=1); print(json.dumps({k: v for k, v in out.items() if k != "par_an"}, indent=1))
print({a: (v["n"], round(v["moy"], 4)) for a, v in out["par_an"].items()})
