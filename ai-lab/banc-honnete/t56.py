"""PREREG-56 : réplication Hyperliquid (règles : PREREG-56-cotations-hyperliquid.md, commit 34f42d7)."""
import calendar, json, os, random, statistics as st, time, urllib.request
ICI = os.path.dirname(os.path.abspath(__file__)); J = 86_400_000; TK = 0.00045; N = 90
def info(q):
    for e in range(5):
        try: return json.load(urllib.request.urlopen(urllib.request.Request("https://api.hyperliquid.xyz/info", data=json.dumps(q).encode(), headers={"Content-Type": "application/json"}), timeout=30))
        except Exception: time.sleep(5 * (e + 1))
FM = os.path.join(ICI, "hl/meta.json")
if not os.path.exists(FM): json.dump(info({"type": "meta"}), open(FM, "w"))
U = json.load(open(FM))["universe"]
FK = os.path.join(ICI, "hl/klines.json"); K = json.load(open(FK)) if os.path.exists(FK) else {}
for x in U:
    c = x["name"]
    if c in K: continue
    k = info({"type": "candleSnapshot", "req": {"coin": c, "interval": "1d", "startTime": 0, "endTime": 1793500000000}}) or []
    K[c] = [[int(b["t"]), float(b["o"]), float(b["c"])] for b in k]; time.sleep(0.25)
json.dump(K, open(FK, "w"))
C = {c: {b[0]: (b[1], b[2]) for b in v} for c, v in K.items() if v}
DEB = {c: min(v) for c, v in C.items()}; FINS = {c: max(v) for c, v in C.items()}
ut = lambda a, m, d: calendar.timegm((a, m, d, 0, 0, 0)) * 1000
def trade(c, e):
    if c not in C or e not in C[c]: return None
    x = min(e + (N - 1) * J, FINS[c])
    while x not in C[c] and x > e: x -= J
    return max(-1.0, -(C[c][x][1] / C[c][e][0] - 1) - 2 * TK)
T = [(DEB[c] + J, c, trade(c, DEB[c] + J)) for c in C if DEB[c] >= ut(2023, 6, 1) and DEB[c] + J <= ut(2026, 7, 29)]
pools = {}
def pool(e):
    if e not in pools: pools[e] = [c for c in C if DEB[c] <= e - 365 * J and e in C[c]]
    return pools[e]
T = [x for x in T if x[2] is not None and pool(x[0])]
def bilan(X, seed):
    if len(X) < 5: return None
    r = [x[2] for x in X]; m = st.mean(r); rng = random.Random(seed); tem = []
    for _ in range(1000):
        v = []
        for e, _, _ in X:
            t = None
            while t is None: t = trade(rng.choice(pool(e)), e)
            v.append(t)
        tem.append(st.mean(v))
    return dict(trades=len(r), moy=m, med=st.median(r), pos=sum(v > 0 for v in r) / len(r), plancher=sum(v <= -1 for v in r), temoin_moy=st.mean(tem), p=sum(v >= m for v in tem) / len(tem))
# information : pièces absentes de Binance (comptant et perpétuels) avant leur cotation sur Hyperliquid
PM = json.load(open(os.path.join(ICI, "comptant/premiers_mois.json"))); KB = json.load(open(os.path.join(ICI, "../carry-financement/data-univers/klines.json")))
def binance_avant(c, e):
    b = c[1:].upper() if c[0] == "k" and c[1:].isupper() else c
    mois = time.strftime("%Y-%m", time.gmtime(e / 1000))
    for s, m in PM.items():
        if m and m < mois and (s.startswith(b) and s[len(b):] in ("USDT", "BTC", "BUSD", "BNB", "ETH", "USDC", "FDUSD")): return True
    for s in (b + "USDT", "1000" + b + "USDT"):
        if KB.get(s) and KB[s][0][0] < e - 7 * J: return True
    return False
neufs = [x for x in T if not binance_avant(x[1], x[0])]
res = dict(contrats=len(U), retires=sum(1 for x in U if x.get("isDelisted")), avec_bougies=len(C), tout=bilan(T, 56) if len(T) >= 30 else None,
           info_neufs_hors_binance=bilan(neufs, 560), retires_parmi_trades=sum(1 for x in T if any(u["name"] == x[1] and u.get("isDelisted") for u in U)),
           par_an={y: (len(z), st.mean(z)) for y in range(2023, 2027) for z in [[x[2] for x in T if time.gmtime(x[0] / 1000).tm_year == y]] if z})
res["verdict"] = "NON ÉVALUABLE" if not res["tout"] else "RÉPLIQUÉ" if res["tout"]["moy"] > 0 and res["tout"]["p"] < 0.05 else "NON RÉPLIQUÉ"
json.dump(res, open(os.path.join(ICI, "t56.json"), "w"), indent=1); print(json.dumps(res, indent=1))
