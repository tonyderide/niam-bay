"""PREREG-54 : réplication OKX (règles : PREREG-54-cotations-okx.md, commit dfb339b). API publique OKX, cache dans okx/."""
import calendar, json, os, random, statistics as st, time, urllib.request
ICI = os.path.dirname(os.path.abspath(__file__)); J = 86_400_000; TK = 0.0005; N = 90
get = lambda u: json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "nb-labo"}), timeout=30))
FI = os.path.join(ICI, "okx/instruments.json")
if not os.path.exists(FI): json.dump(get("https://www.okx.com/api/v5/public/instruments?instType=SWAP")["data"], open(FI, "w"))
INS = [x for x in json.load(open(FI)) if x["settleCcy"] == "USDT" and x.get("instCategory") == "1" and x["listTime"]]
FK = os.path.join(ICI, "okx/klines.json"); K = json.load(open(FK)) if os.path.exists(FK) else {}
for i, x in enumerate(INS):
    s = x["instId"]
    if s in K: continue
    out, after = [], ""
    while True:
        for e in range(5):
            try: r = get(f"https://www.okx.com/api/v5/market/history-candles?instId={s}&bar=1Dutc&limit=100" + (f"&after={after}" if after else "")); break
            except Exception: time.sleep(3 * (e + 1))
        d = r.get("data", []); time.sleep(0.12)
        if not d: break
        out += [[int(c[0]), float(c[1]), float(c[4])] for c in d if c[8] == "1"]; after = d[-1][0]
        if len(d) < 100: break
    K[s] = sorted(out)
    if i % 25 == 0: json.dump(K, open(FK, "w")); print(i, s, len(out), flush=True)
json.dump(K, open(FK, "w"))
C = {s: {k[0]: (k[1], k[2]) for k in v} for s, v in K.items() if v}
LT = {x["instId"]: int(x["listTime"]) for x in INS}; FINS = {s: max(v) for s, v in C.items()}; DEB = {s: min(v) for s, v in C.items()}
ut = lambda a, m, d: calendar.timegm((a, m, d, 0, 0, 0)) * 1000
def trade(s, e):
    if s not in C or e not in C[s]: return None
    x = min(e + (N - 1) * J, FINS[s])
    while x not in C[s] and x > e: x -= J
    return max(-1.0, -(C[s][x][1] / C[s][e][0] - 1) - 2 * TK)
T = []
for s, lt in LT.items():
    e = (lt // J) * J + J
    if ut(2021, 1, 1) <= e <= ut(2026, 7, 29):
        t = trade(s, e)
        if t is not None: T.append((e, s, t))
pools = {}
def pool(e):
    if e not in pools: pools[e] = [s for s in C if min(LT.get(s, DEB[s]), DEB[s]) <= e - 365 * J and e in C[s]]
    return pools[e]
T = [x for x in T if pool(x[0])]
def bilan(X, seed):
    r = [x[2] for x in X]; m = st.mean(r); rng = random.Random(seed); tem = []
    for _ in range(1000):
        v = []
        for e, _, _ in X:
            t = None
            while t is None: t = trade(rng.choice(pool(e)), e)
            v.append(t)
        tem.append(st.mean(v))
    return dict(trades=len(r), moy=m, med=st.median(r), pos=sum(v > 0 for v in r) / len(r), plancher=sum(v <= -1 for v in r), temoin_moy=st.mean(tem), p=sum(v >= m for v in tem) / len(tem))
res = dict(instruments_crypto=len(INS), avec_bougies=len(C), tout=bilan(T, 54) if len(T) >= 30 else None,
           j2026=bilan([x for x in T if x[0] >= ut(2026, 1, 1)], 540) if len([x for x in T if x[0] >= ut(2026, 1, 1)]) >= 5 else None,
           par_an={y: (len(z), st.mean(z)) for y in range(2021, 2027) for z in [[x[2] for x in T if time.gmtime(x[0] / 1000).tm_year == y]] if z})
res["verdict"] = "NON ÉVALUABLE" if not res["tout"] else "RÉPLIQUÉ" if res["tout"]["moy"] > 0 and res["tout"]["p"] < 0.05 else "NON RÉPLIQUÉ"
json.dump(res, open(os.path.join(ICI, "t54.json"), "w"), indent=1); print(json.dumps(res, indent=1))
