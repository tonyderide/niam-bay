"""Le banc automatique : une stratégie décrite en JSON -> verdict honnête (2 périodes, frais, hasard).

Spec (exemple) :
{"nom": "RSI 30 + EMA200", "tf": "1h", "marches": ["BTC", "ETH", "SOL"],
 "long": "cross_down(rsi(14), 30) & (close > ema(200))", "short": null,
 "sortie": {"sl": 0.01, "tp": 0.02, "max_bougies": 48}}
- "long"/"short" : expressions sur des séries (open high low close volume, ema(n), sma(n), rsi(n), atr(n), vwap(),
  macd(), macd_signal(), supertrend(n, m), bb_upper(n, k), bb_lower(n, k), adx(n), highest(s, n), lowest(s, n), shift(s, k), cross_up(a, b), cross_down(a, b)),
  combinées avec & | ~ et < > <= >=. Valeur évaluée sur la bougie close ; entrée à l'ouverture suivante.
- "sortie" : sl/tp en fraction (optionnels), "max_bougies" (optionnel), "inverse": true = sortie sur signal opposé, "si_long"/"si_short": expression de sortie.
  Sans sl/tp/max, la position est tenue jusqu'au signal opposé (toujours en position).
Verdict : GAGNE si, sur 2024-2025 ET 2026, somme > 0, >= 2 marchés/3 positifs, somme > p95 de 500 tirages au hasard
(mêmes sorties, mêmes nombres de trades, instants et sens aléatoires), et >= 30 trades par période.
Usage : python3 banc.py spec.json
"""
import calendar, json, math, os, pickle, random, sys, time, urllib.request

FEE = 0.0005
SYM = {"BTC": "PF_XBTUSD", "ETH": "PF_ETHUSD", "SOL": "PF_SOLUSD"}
for _c in "XRP DOGE ADA LINK AVAX DOT LTC BCH UNI ATOM NEAR FIL AAVE APT OP TRX XLM ETC".split(): SYM[_c] = f"PF_{_c}USD"
STEP = {"5m": 300, "15m": 900, "30m": 1800, "1h": 3600, "4h": 14400, "12h": 43200, "1d": 86400}
CACHE = os.path.expanduser("~/.cache/banc-honnete")
ts = lambda d: calendar.timegm(time.strptime(d, "%Y-%m-%d"))
PERIODES = (("2024-2025", ts("2024-01-01"), ts("2026-01-01")), ("2026", ts("2026-01-01"), ts("2026-10-17")))


def candles(sym, tf):
    debut = "2022-11-01" if tf == "1d" else "2023-11-01"  # en journalier, la SMA200 a besoin de ~200 j avant 2024
    os.makedirs(CACHE, exist_ok=True); f = f"{CACHE}/{sym}_{tf}_{debut}.pkl"
    if os.path.exists(f): return pickle.load(open(f, "rb"))
    step = STEP[tf]; a, b = ts(debut), ts("2026-10-17"); out = {}; t = a
    while t < b:  # l'API rend 2000 bougies max par appel : tranches de 1800
        for _ in range(8):
            try:
                d = json.load(urllib.request.urlopen(f"https://futures.kraken.com/api/charts/v1/trade/{sym}/{tf}?from={t}&to={min(b, t + 1800 * step)}", timeout=60))["candles"]; break
            except Exception: time.sleep(3)
        for c in d: out[c["time"] // 1000] = tuple(float(c[x]) for x in ("open", "high", "low", "close", "volume"))
        t += 1800 * step; time.sleep(0.2)
    T = sorted(out); r = (T, [out[x] for x in T]); pickle.dump(r, open(f, "wb")); return r


class S(list):  # série : opérations élément par élément
    def _op(self, o, f): return S(f(a, b) for a, b in zip(self, o if isinstance(o, list) else [o] * len(self)))
    __lt__ = lambda s, o: s._op(o, lambda a, b: a < b); __gt__ = lambda s, o: s._op(o, lambda a, b: a > b)
    __le__ = lambda s, o: s._op(o, lambda a, b: a <= b); __ge__ = lambda s, o: s._op(o, lambda a, b: a >= b)
    __and__ = lambda s, o: s._op(o, lambda a, b: bool(a) and bool(b)); __or__ = lambda s, o: s._op(o, lambda a, b: bool(a) or bool(b))
    __invert__ = lambda s: S(not a for a in s)
    __add__ = lambda s, o: s._op(o, lambda a, b: a + b); __sub__ = lambda s, o: s._op(o, lambda a, b: a - b)
    __mul__ = lambda s, o: s._op(o, lambda a, b: a * b); __truediv__ = lambda s, o: s._op(o, lambda a, b: a / b if b else 0)
    __rmul__ = __mul__; __radd__ = __add__


def namespace(T, C):
    o, h, l, c, v = (S(x[k] for x in C) for k in range(5)); n = len(C)
    def ema(k, s=None):
        s = c if s is None else s; e = s[0]; r = S()
        for x in s: e += (x - e) * 2 / (k + 1); r.append(e)
        return r
    def sma(k, s=None):
        s = c if s is None else s; r = S(); acc = 0
        for i, x in enumerate(s): acc += x - (s[i - k] if i >= k else 0); r.append(acc / min(i + 1, k))
        return r
    def rma(s, k):
        r = S([s[0]])
        for x in s[1:]: r.append(r[-1] + (x - r[-1]) / k)
        return r
    def rsi(k=14):
        up = S([0] + [max(0, c[i] - c[i - 1]) for i in range(1, n)]); dn = S([0] + [max(0, c[i - 1] - c[i]) for i in range(1, n)])
        U, D = rma(up, k), rma(dn, k); return S(100 - 100 / (1 + U[i] / D[i]) if D[i] else 100 for i in range(n))
    def atr(k=14):
        tr = S([h[0] - l[0]] + [max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1])) for i in range(1, n)]); return rma(tr, k)
    def vwap():  # remis à zéro chaque jour UTC
        r = S(); pv = vv = 0; day = None
        for i in range(n):
            if T[i] // 86400 != day: pv = vv = 0; day = T[i] // 86400
            pv += (h[i] + l[i] + c[i]) / 3 * v[i]; vv += v[i]; r.append(pv / vv if vv else c[i])
        return r
    macd = lambda f=12, s=26: ema(f) - ema(s)
    macd_signal = lambda f=12, s=26, g=9: ema(g, macd(f, s))
    def supertrend(k=10, m=3):  # +1 haussier, -1 baissier
        a = atr(k); d = S([1] * n); up = [0] * n; dn = [0] * n
        for i in range(n):
            hl2 = (h[i] + l[i]) / 2; u, w = hl2 - m * a[i], hl2 + m * a[i]
            if i:
                u = max(u, up[i - 1]) if c[i - 1] > up[i - 1] else u; w = min(w, dn[i - 1]) if c[i - 1] < dn[i - 1] else w
                d[i] = 1 if (d[i - 1] == -1 and c[i] > dn[i - 1]) else -1 if (d[i - 1] == 1 and c[i] < up[i - 1]) else d[i - 1]
            up[i], dn[i] = u, w
        return d
    def stdev(k, s=None):
        s = c if s is None else s; m = sma(k, s); return S((sum((x - m[i]) ** 2 for x in s[max(0, i - k + 1):i + 1]) / min(i + 1, k)) ** .5 for i in range(n))
    bb_upper = lambda k=20, m=2: sma(k) + stdev(k) * m
    bb_lower = lambda k=20, m=2: sma(k) - stdev(k) * m
    def adx(k=14):  # ADX de Wilder
        pdm = S([0] + [max(h[i] - h[i - 1], 0) if h[i] - h[i - 1] > l[i - 1] - l[i] else 0 for i in range(1, n)])
        mdm = S([0] + [max(l[i - 1] - l[i], 0) if l[i - 1] - l[i] > h[i] - h[i - 1] else 0 for i in range(1, n)])
        a = atr(k); P, M = rma(pdm, k), rma(mdm, k)
        dx = S(abs(P[i] - M[i]) / (P[i] + M[i]) * 100 if (P[i] + M[i]) else 0 for i in range(n)); return rma(dx, k)
    vmin = lambda a, b: S(min(x, y) for x, y in zip(a, b)); vmax = lambda a, b: S(max(x, y) for x, y in zip(a, b))
    absv = lambda a: S(abs(x) for x in a)
    shift = lambda s, k=1: S([s[0]] * k + s[:-k])
    highest = lambda s, k: S(max(s[max(0, i - k + 1):i + 1]) for i in range(n))
    lowest = lambda s, k: S(min(s[max(0, i - k + 1):i + 1]) for i in range(n))
    cross_up = lambda a, b: (shift(a) <= (shift(b) if isinstance(b, list) else b)) & (a > b)
    cross_down = lambda a, b: (shift(a) >= (shift(b) if isinstance(b, list) else b)) & (a < b)
    return {k: x for k, x in locals().items() if not k.startswith("_")} | {"open": o, "high": h, "low": l, "close": c, "volume": v}


def sortir(C, i, s, so, opp):
    """Trade entré à l'open i dans le sens s ; renvoie (rendement net, indice de sortie)."""
    ent = C[i][0]; sl, tp, mx = so.get("sl"), so.get("tp"), so.get("max_bougies")
    for j in range(i, len(C)):
        o, h, l, c, _ = C[j]
        if sl and ((s > 0 and l <= ent * (1 - sl)) or (s < 0 and h >= ent * (1 + sl))):
            px = min(o, ent * (1 - sl)) if s > 0 else max(o, ent * (1 + sl)); return s * (px / ent - 1) - 2 * FEE, j
        if tp and ((s > 0 and h >= ent * (1 + tp)) or (s < 0 and l <= ent * (1 - tp))): return tp - 2 * FEE, j  # un TP est toujours un gain, long ou short
        cond = so.get('_cl') if s > 0 else so.get('_cs')
        if j + 1 < len(C) and ((mx and j - i + 1 >= mx) or (opp and opp[j]) or (cond and cond[j])): return s * (C[j + 1][0] / ent - 1) - 2 * FEE, j + 1
    return s * (C[-1][3] / ent - 1) - 2 * FEE, len(C) - 1


def tester(spec, C, T, a, b):
    ns = namespace(T, C); lo = next(i for i, t in enumerate(T) if t >= a); hi = max(i for i, t in enumerate(T) if t < b) + 1
    ev = lambda e: eval(e, {"__builtins__": {}}, ns) if e else S([False] * len(C))
    L, Sh = ev(spec.get("long")), ev(spec.get("short")); so = dict(spec.get("sortie", {}))
    if so.get("si_long"): so["_cl"] = ev(so["si_long"])
    if so.get("si_short"): so["_cs"] = ev(so["si_short"])
    toujours = not (so.get("sl") or so.get("tp") or so.get("max_bougies") or so.get("si_long") or so.get("si_short"))
    C2 = C[:hi]; trades = []; i = max(lo, 250)
    while i < hi - 1:
        s = 1 if L[i] else -1 if Sh[i] else 0
        if not s: i += 1; continue
        opp = (Sh if s > 0 else L) if (toujours or so.get("inverse")) else None
        r, j = sortir(C2, i + 1, s, so, opp); trades.append((r, j - i)); i = j - 1 if toujours else j + 1  # toujours en position : on se retourne sur la bougie du signal
    return trades, C2, lo, hi, so, toujours


def hasard(C, lo, hi, trades, so, toujours, rnd, sens=(1, -1)):
    """sens = les directions que la stratégie peut prendre : une stratégie long-only est comparée à des longs au hasard."""
    tot = 0
    for _, dur in trades:
        i = rnd.randrange(lo + 1, hi - 1); s = rnd.choice(sens)
        if toujours: j = min(hi - 1, i + dur); tot += s * (C[j][0] / C[i][0] - 1) - 2 * FEE  # même durée de tenue
        else: tot += sortir(C, i, s, so, None)[0]
    return tot


def banc(spec):
    out = [f"# {spec['nom']}  ({spec['tf']})"]; ok = True
    data = {m: candles(SYM[m], spec["tf"]) for m in spec.get("marches", ["BTC", "ETH", "SOL"])}
    for per, a, b in PERIODES:
        S_ = 0; pos = 0; N = 0; R = [0.0] * 500; lig = []
        for m, (T, C) in data.items():
            tr, C2, lo, hi, so, tj = tester(spec, C, T, a, b); r = sum(x for x, _ in tr); S_ += r; pos += r > 0; N += len(tr)
            sens = tuple(x for x, e in ((1, spec.get("long")), (-1, spec.get("short"))) if e)
            for k in range(500): R[k] += hasard(C2, lo, hi, tr, so, tj, random.Random(k), sens)
            g = sum(x > 0 for x, _ in tr) / max(1, len(tr))
            lig.append(f"{m} {len(tr)} trades, {g:.0%} gagnants, somme {r * 100:+.1f} % (composé {(math.prod(1 + x for x, _ in tr) - 1) * 100:+.1f} %)")
        R.sort(); good = S_ > 0 and pos >= max(2, math.ceil(0.6 * len(data))) and S_ > R[475] and N >= 30; ok &= good  # 3 marchés : 2 ; 21 : 13
        out.append(f"{per} : " + " | ".join(lig) + f" || somme {S_ * 100:+.1f} % · hasard méd. {R[250] * 100:+.1f} % p95 {R[475] * 100:+.1f} % · rang {sum(x < S_ for x in R) / 5:.0f}e centile · {pos}/{len(data)} marchés > 0 · {'OK' if good else 'NON'}")
    out.append("VERDICT : " + ("GAGNE" if ok else "ÉCHEC"))
    return "\n".join(out)


if __name__ == "__main__":
    print(banc(json.load(open(sys.argv[1]))))
