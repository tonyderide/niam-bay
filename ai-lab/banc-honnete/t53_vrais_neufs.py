"""PREREG-53, vérification après verdict : ne garder que les VRAIS jetons neufs (la paire USDT apparaît le même mois que la première paire, toutes cotations confondues, du même actif).
Premier mois de chaque symbole : listing S3 de data.binance.vision (data/spot/monthly/klines/<SYM>/1d/)."""
import json, os, re, urllib.request, concurrent.futures as cf, random, statistics as st, time
ICI = os.path.dirname(os.path.abspath(__file__)); get = lambda u: urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "nb-labo"}), timeout=60).read().decode()
S = json.load(open(os.path.join(ICI, "comptant/symboles.json"))); F = os.path.join(ICI, "comptant/premiers_mois.json")
QUOTES = ["USDT", "BTC", "ETH", "BNB", "BUSD", "USDC", "FDUSD", "TUSD", "PAX", "USDS", "TRY", "EUR", "BRL", "AUD", "GBP", "RUB", "BIDR", "IDRT", "UAH", "NGN", "ZAR", "DAI", "JPY", "TRX", "XRP", "DOGE", "DOT", "VAI", "BKRW", "BVND", "GYEN", "PLN", "RON", "ARS", "MXN", "COP", "CZK", "AEUR", "EURI", "U"]
def base(s):
    for q in sorted(QUOTES, key=len, reverse=True):
        if s.endswith(q) and len(s) > len(q): return s[:-len(q)]
    return None
def premier(s):
    try: x = get(f"https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?prefix=data/spot/monthly/klines/{s}/1d/&delimiter=/")
    except Exception: return s, None
    m = re.findall(r"-1d-(\d{4}-\d{2})\.zip<", x); return s, (min(m) if m else None)
if not os.path.exists(F):
    with cf.ThreadPoolExecutor(32) as ex: P = dict(ex.map(premier, S))
    json.dump(P, open(F, "w"))
P = json.load(open(F)); PB = {}
for s, m in P.items():
    b = base(s)
    if b and m: PB[b] = min(PB.get(b, m), m)
src = open(os.path.join(ICI, "t53.py")).read(); ns = {"__file__": os.path.join(ICI, "t53.py")}; exec(src[:src.index("out = {}")], ns)
mesure, nouv, pool, A0, B0, BF = (ns[k] for k in ("mesure", "nouv", "pool", "A0", "B0", "BF"))
vrai = lambda s: P.get(s) is not None and P[s] == PB.get(s[:-4])
for nom, (a, b) in (("A_2018_2020", (A0, B0)), ("B_2021_2026", (B0, BF + 1))):
    T = [(e, s, mesure(s, e)) for e, s in nouv if a <= e < b]; T = [x for x in T if x[2] is not None and pool(x[0])]
    V = [x for x in T if vrai(x[1])]; r = [x[2] for x in V]; m = st.mean(r); rng = random.Random(53); tem = []
    for _ in range(1000):
        v = []
        for e, _, _ in V:
            t = None
            while t is None: t = mesure(rng.choice(pool(e)), e)
            v.append(t)
        tem.append(st.mean(v))
    print(nom, "trades", len(T), "dont vrais neufs", len(V), "moy", round(m, 4), "méd", round(st.median(r), 4), "témoin", round(st.mean(tem), 4), "p", sum(x >= m for x in tem) / 1000,
          {y: (len(z), round(st.mean(z), 3)) for y in range(2018, 2027) for z in [[x[2] for x in V if time.gmtime(x[0] / 1000).tm_year == y]] if z})
