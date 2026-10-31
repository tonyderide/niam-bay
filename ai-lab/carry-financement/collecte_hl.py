"""PREREG-33 : collecte Hyperliquid (API publique, lecture seule). Bougies 1d de tous les perps, puis financement des contrats qui entrent dans un univers."""
import calendar, json, os, sys, time, urllib.request
DOS = "data_hl"; J = 86400000; URL = "https://api.hyperliquid.xyz/info"
POIDS = [0.0, time.time()]  # poids consommé dans la minute courante
def post(body, poids):
    if time.time() - POIDS[1] > 60: POIDS[:] = [0.0, time.time()]
    if POIDS[0] + poids > 1000: time.sleep(max(0, 61 - (time.time() - POIDS[1]))); POIDS[:] = [0.0, time.time()]
    POIDS[0] += poids
    for essai in range(6):
        try:
            req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
            return json.load(urllib.request.urlopen(req, timeout=60))
        except Exception as e:
            print("erreur", body.get("coin", body.get("req", {}).get("coin")), e, flush=True); time.sleep(10 * (essai + 1))
    raise SystemExit("API injoignable")
if not os.path.exists(f"{DOS}/meta.json"): json.dump(post({"type": "meta"}, 20), open(f"{DOS}/meta.json", "w"))
NOMS = [u["name"] for u in json.load(open(f"{DOS}/meta.json"))["universe"]]
FK = f"{DOS}/klines.json"; K = json.load(open(FK)) if os.path.exists(FK) else {}
for i, s in enumerate(NOMS):
    if s in K: continue
    r = post({"type": "candleSnapshot", "req": {"coin": s, "interval": "1d", "startTime": 0, "endTime": 1900000000000}}, 60)
    K[s] = [[x["t"], float(x["o"]), float(x["c"]), float(x["v"]) * float(x["c"]), x["n"]] for x in r]  # ouverture, open, close, volume $, nb trades
    if i % 20 == 0: json.dump(K, open(FK, "w")); print(i, s, len(r), flush=True)
json.dump(K, open(FK, "w")); print("bougies ok", len(K), flush=True)
# univers (règle du PREREG) -> liste des contrats et date de première entrée
C = {s: {k[0]: k for k in v if k[4] > 0} for s, v in K.items() if s != "NFTI"}
def univers(t):
    cand = {s: sum(k[3] for d, k in v.items() if t - 30 * J <= d < t) for s, v in C.items() if sum(1 for d in v if d < t) >= 60}
    return sorted(cand, key=lambda s: -cand[s])[:30], len(cand)
t0 = None
for y in range(2023, 2027):
    for m in range(1, 13):
        t = calendar.timegm((y, m, 1, 0, 0, 0)) * 1000
        if univers(t)[1] >= 30: t0 = t; break
    if t0: break
dates = [t0] + [calendar.timegm((y, 1, 1, 0, 0, 0)) * 1000 for y in range(2024, 2027) if calendar.timegm((y, 1, 1, 0, 0, 0)) * 1000 > t0]
U = {str(t): univers(t)[0] for t in dates}
json.dump({"debut": t0, "univers": U}, open(f"{DOS}/univers.json", "w"))
premiere = {}
for t in dates:
    for s in U[str(t)]: premiere.setdefault(s, t)
print("début", time.strftime("%F", time.gmtime(t0 / 1000)), "contrats", len(premiere), flush=True)
FF = f"{DOS}/funding.json"; F = json.load(open(FF)) if os.path.exists(FF) else {}
fin = int(time.time() * 1000)
for i, (s, t) in enumerate(sorted(premiere.items())):
    if s in F and F[s] and F[s][-1][0] > fin - 2 * 3600000: continue
    f = F.get(s, []); a = f[-1][0] + 1 if f else t - 8 * J
    while a < fin:
        r = post({"type": "fundingHistory", "coin": s, "startTime": a}, 20 + 25)
        if not r: break
        f += [[x["time"], float(x["fundingRate"])] for x in r]; a = r[-1]["time"] + 1
        if len(r) < 500: break
    F[s] = f; json.dump(F, open(FF, "w")); print(i, s, len(f), flush=True)
print("financement ok", len(F))
