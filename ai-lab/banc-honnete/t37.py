"""PREREG-37 : prime de variance BTC/ETH (règles : PREREG-37-prime-variance.md, commit bd0e880).
DVOL Deribit (public) + comptant Binance 1 h (public). Cache dans variance/."""
import datetime as dt, json, math, os, random, time, urllib.request
ICI = os.path.dirname(os.path.abspath(__file__)); C = os.path.join(ICI, "variance"); os.makedirs(C, exist_ok=True)
H, J = 3_600_000, 86_400_000
FIN_DATA = int(dt.datetime(2026, 10, 31, tzinfo=dt.timezone.utc).timestamp() * 1000)
J26 = int(dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc).timestamp() * 1000)
J26F = int(dt.datetime(2026, 10, 1, tzinfo=dt.timezone.utc).timestamp() * 1000)

def get(url):
    for e in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "nb-labo"}), timeout=30) as r: return json.load(r)
        except Exception:
            if e == 4: raise
            time.sleep(3 * (e + 1))

def dvol(pc):
    f = os.path.join(C, f"dvol_{pc}.json")
    if os.path.exists(f): return json.load(open(f))
    out, fin = {}, FIN_DATA
    while True:
        r = get(f"https://www.deribit.com/api/v2/public/get_volatility_index_data?currency={pc}&start_timestamp=1577836800000&end_timestamp={fin}&resolution=1D")["result"]
        for x in r["data"]: out[int(x[0])] = float(x[1])
        if not r.get("continuation") or not r["data"]: break
        fin = int(r["continuation"]); time.sleep(0.3)
    out = {k: out[k] for k in sorted(out)}; json.dump(out, open(f, "w")); return {int(k): v for k, v in out.items()}

def spot(pc, t0):
    f = os.path.join(C, f"spot_{pc}.json")
    if os.path.exists(f): return {int(k): v for k, v in json.load(open(f)).items()}
    out, t = {}, t0
    while t < FIN_DATA:
        k = get(f"https://api.binance.com/api/v3/klines?symbol={pc}USDT&interval=1h&startTime={t}&endTime={FIN_DATA - 1}&limit=1000")
        if not k: break
        for x in k: out[int(x[0])] = float(x[4])
        t = int(k[-1][0]) + H; time.sleep(0.15)
    json.dump(out, open(f, "w")); return out

def boot(x, n=10000, b=30, seed=37):
    m = sum(x) / len(x); c = [v - m for v in x]; rng = random.Random(seed); N = len(c); ge = 0
    for _ in range(n):
        s, k = 0.0, 0
        while k < N:
            i = rng.randrange(N)
            for j in range(b):
                if k >= N: break
                s += c[(i + j) % N]; k += 1
        ge += (s / N) >= m
    return ge / n

def stats(g):
    if not g: return {}
    s = sorted(g); n = len(s); q = max(1, int(0.05 * n))
    return dict(n=n, moy=sum(g) / n, med=s[n // 2], gagnants=sum(v > 0 for v in g) / n, pire=s[0], cvar5=sum(s[:q]) / q, sous_m1=sum(v < -1 for v in g))

res = {}
for pc in ("BTC", "ETH"):
    D = dvol(pc); jours = sorted(D); P = spot(pc, jours[0])
    print(pc, "DVOL", len(D), "jours depuis", dt.datetime.utcfromtimestamp(jours[0] / 1000).date(), "; spot", len(P), "heures", flush=True)
    rows = []
    for t in jours:
        if t + 30 * J > FIN_DATA or t + 30 * J > max(P): continue
        px = [P.get(t + h * H) for h in range(721)]
        if sum(v is None for v in px) > 24: continue
        px = [v for v in px if v is not None]
        rv2 = sum(math.log(b / a) ** 2 for a, b in zip(px, px[1:])) * 8760 / 720 * 1e4
        K = (D[t] - 2) ** 2
        rows.append(dict(t=t, dvol=D[t], rv=math.sqrt(rv2), g=(K - rv2) / K, gv=((D[t] - 2) - math.sqrt(rv2)) / (D[t] - 2)))
    hist = [r for r in rows if r["t"] < J26]; j26 = [r for r in rows if J26 <= r["t"] < J26F]
    mens = rows[::30]; mh = [r for r in mens if r["t"] < J26]; m26 = [r for r in mens if J26 <= r["t"] < J26F]
    R = dict(debut=str(dt.datetime.utcfromtimestamp(rows[0]["t"] / 1000).date()),
             hist=stats([r["g"] for r in hist]), j2026=stats([r["g"] for r in j26]),
             mens_hist=stats([r["g"] for r in mh]), mens_2026=stats([r["g"] for r in m26]),
             vol_swap_hist=stats([r["gv"] for r in hist]), vol_swap_2026=stats([r["gv"] for r in j26]),
             dvol_moy_hist=sum(r["dvol"] for r in hist) / len(hist), rv_moy_hist=sum(r["rv"] for r in hist) / len(hist),
             dvol_moy_2026=sum(r["dvol"] for r in j26) / len(j26), rv_moy_2026=sum(r["rv"] for r in j26) / len(j26))
    R["p_2026"] = boot([r["g"] for r in j26]); R["p_hist"] = boot([r["g"] for r in hist], n=2000)
    R["queue"] = (-R["mens_hist"]["pire"]) > 12 * R["mens_hist"]["moy"]
    R["pires_mois"] = sorted(((round(r["g"], 2), str(dt.datetime.utcfromtimestamp(r["t"] / 1000).date())) for r in mens))[:5]
    res[pc] = R; print(pc, json.dumps(R, indent=1, default=str), flush=True)
ok = all(res[p]["hist"]["moy"] > 0 and res[p]["j2026"]["moy"] > 0 and res[p]["p_2026"] < 0.05 for p in res)
v = "GAGNE" if ok else "NON DÉMONTRÉ" if all(res[p]["j2026"]["moy"] > 0 for p in res) else "PERD"
res["verdict"] = v; res["risque_de_queue"] = any(res[p]["queue"] for p in ("BTC", "ETH"))
json.dump(res, open(os.path.join(ICI, "t37.json"), "w"), indent=1, default=str)
print("VERDICT", v, "| RISQUE DE QUEUE" if res["risque_de_queue"] else "")
