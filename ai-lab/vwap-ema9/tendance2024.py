# Applique PREREG-TENDANCE-2024.md à la lettre.
import json, time, urllib.request, random, pickle, os
ts = lambda d: int(time.mktime(time.strptime(d + " UTC", "%Y-%m-%d %Z"))) if False else int(__import__("calendar").timegm(time.strptime(d, "%Y-%m-%d")))
A, B = ts("2024-01-01"), ts("2026-01-01")
P = "/tmp/claude-1000/-home-tony/2c25ff3c-37a9-4b0e-a8fd-9600199a4cb4/scratchpad/c3m_2024_%s.pkl"
def candles(sym):
    if os.path.exists(P % sym): return pickle.load(open(P % sym, "rb"))
    out = {}; t = A
    while t < B:
        try: d = json.load(urllib.request.urlopen(f"https://futures.kraken.com/api/charts/v1/trade/{sym}/1m?from={t}&to={min(B, t+1800*60)}", timeout=60))["candles"]
        except Exception: time.sleep(3); continue
        for c in d: out[c["time"]//1000] = tuple(float(c[x]) for x in ("open","high","low","close","volume"))
        t += 1800*60; time.sleep(0.12)
    b = {}
    for t in sorted(out):
        v = out[t]; k = t//180*180; o = b.get(k)
        b[k] = v if o is None else (o[0], max(o[1], v[1]), min(o[2], v[2]), v[3], o[4]+v[4])
    T = sorted(b); r = (T, [b[t] for t in T]); pickle.dump(r, open(P % sym, "wb")); return r
def sim(T, C, trend=True, fee=0.0005):
    n = len(C); e = C[0][3]; pv = vv = 0; day = None; want = 0; run = 0; pos = 0; entry = 0
    ema200 = None; hcur = None; hclose = None; legs = []  # (i_in, i_out, sens)
    for i in range(n):
        o, h, l, c, v = C[i]; hr = T[i]//3600
        if hr != hcur:  # l'heure précédente est close -> mise à jour EMA200 1h
            if hclose is not None: ema200 = hclose if ema200 is None else ema200 + (hclose-ema200)*2/201
            hcur = hr
        hclose = c
        d = T[i]//86400
        if d != day: pv = vv = 0; day = d
        pv += (h+l+c)/3*v; vv += v; vw = pv/vv if vv else c
        e = c if i == 0 else e + (c-e)*2/10
        g = e/vw - 1; s = 1 if g > .005 else -1 if g < -.005 else 0
        run = run+1 if s and s == want else (1 if s else 0); want = s if s else want
        if not (s and run >= 5 and i+1 < n): continue
        tgt = s
        if trend:
            if ema200 is None: continue
            if (s > 0 and c <= ema200) or (s < 0 and c >= ema200): tgt = 0
        if tgt != pos:
            if pos: legs.append((ji, i+1, pos))
            pos = tgt; ji = i+1
    if pos: legs.append((ji, n-1, pos))
    return legs
def score(C, legs, fee=0.0005, dirs=None, T=None, year=None):
    eq = 1.0; k = 0
    for (a, b, s) in legs:
        if T and year and time.gmtime(T[a]).tm_year != year: continue
        if dirs is not None: s = dirs[k]; k += 1
        eq *= (1 + s*(C[b][0]/C[a][0]-1) - 2*fee)
    return eq-1
SYM = {"BTC": "PF_XBTUSD", "ETH": "PF_ETHUSD", "SOL": "PF_SOLUSD"}
ok = {"c1": True, "c2": True, "c3": 0}
for k, s in SYM.items():
    T, C = candles(s)
    legs = sim(T, C); r = score(C, legs)
    R = sorted(score(C, legs, dirs=[rnd.choice((1,-1)) for _ in legs]) for rnd in (random.Random(j) for j in range(500)))
    y = {Y: score(C, legs, T=T, year=Y) for Y in (2024, 2025)}
    nofilt = score(C, sim(T, C, trend=False)); bh = C[-1][3]/C[0][0]-1
    ok["c1"] &= r > 0; ok["c2"] &= r > R[475]; ok["c3"] += all(v > 0 for v in y.values())
    print(f"{k}: trades {len(legs):4} | total {r*100:+7.1f}% | hasard p95 {R[475]*100:+6.1f}% | 2024 {y[2024]*100:+.1f}% 2025 {y[2025]*100:+.1f}% | [indic] sans tendance {nofilt*100:+.1f}% | garder {bh*100:+.1f}% | bougies {len(C)}", flush=True)
print("CRITÈRES : 1 (>0 partout)", ok["c1"], "| 2 (>p95 partout)", ok["c2"], "| 3 (2 années positives sur ≥2 marchés)", ok["c3"] >= 2)
print("VERDICT :", "GAGNANTE" if ok["c1"] and ok["c2"] and ok["c3"] >= 2 else "ÉCHEC")
