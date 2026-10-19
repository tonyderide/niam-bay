"""Suivi de tendance (protocole 3ecd89f). Lecture seule, API charts Kraken Futures (1d)."""
import json, random, time, urllib.request
D = 86400; ts = lambda d: int(time.mktime(time.strptime(d, "%Y-%m-%d")))
SYM = {"BTC": "PF_XBTUSD", "ETH": "PF_ETHUSD", "SOL": "PF_SOLUSD", "DOT": "PF_DOTUSD", "LINK": "PF_LINKUSD"}
FEE, CARRY = 0.001, 0.0001


def daily(sym):
    out = {}; t = ts("2023-06-01"); end = ts("2026-10-17")
    while t < end:
        d = json.load(urllib.request.urlopen(f"https://futures.kraken.com/api/charts/v1/mark/{sym}/1d?from={t}&to={min(end, t + 1000 * D)}", timeout=30))["candles"]
        for c in d: out[c["time"] // 1000] = float(c["close"])
        t += 1000 * D; time.sleep(0.5)
    T = sorted(out); return T, [out[x] for x in T]


def ema(x, n):
    e = [x[0]]
    for v in x[1:]: e.append(e[-1] + (v - e[-1]) * 2 / (n + 1))
    return e


def positions(rule, c):
    n = len(c); p = [0] * n
    if rule in ("T1", "T2"):
        a, b = ema(c, 50), ema(c, 200)
        for i in range(200, n): p[i] = 1 if a[i] > b[i] else (-1 if rule == "T2" else 0)
    elif rule in ("T3", "T4"):
        hi, lo = (20, 10) if rule == "T3" else (55, 20); pos = 0
        for i in range(hi, n):
            if pos <= 0 and c[i] > max(c[i - hi:i]): pos = 1
            elif pos >= 0 and c[i] < min(c[i - hi:i]): pos = -1
            elif pos == 1 and c[i] < min(c[i - lo:i]): pos = 0
            elif pos == -1 and c[i] > max(c[i - lo:i]): pos = 0
            p[i] = pos
    elif rule == "T5":
        for i in range(90, n): p[i] = (1 if c[i] / c[i - 90] - 1 > 0 else 0) if i % 7 == 0 else p[i - 1]
    return p


def perf(T, c, p, a, b):
    eq = 1.0; peak = 1.0; dd = 0.0; trades = []; cur = None
    for i in range(1, len(c)):
        if not (a <= T[i] < b): continue
        r = c[i] / c[i - 1] - 1; pos = p[i - 1]
        g = pos * r - (CARRY if pos else 0) - (FEE * abs(p[i - 1] - p[i - 2]) if i >= 2 else 0)
        eq *= 1 + g; peak = max(peak, eq); dd = min(dd, eq / peak - 1)
        if pos != 0:
            cur = (cur or 1.0) * (1 + g)
        if cur is not None and (i + 1 >= len(p) or p[i] != pos):
            trades.append(cur - 1); cur = None
    return eq - 1, dd, trades


DATA = {k: daily(s) for k, s in SYM.items()}
rnd = random.Random(1019)
for period, (a, b) in (("2024-2025 (sélection)", (ts("2024-01-01"), ts("2026-01-01"))), ("2026 (JUGEMENT)", (ts("2026-01-01"), ts("2026-10-17")))):
    print(f"\n== {period} ==")
    bh = sum(perf(T, c, [1] * len(c), a, b)[0] for T, c in DATA.values()) / 5
    bhdd = sum(perf(T, c, [1] * len(c), a, b)[1] for T, c in DATA.values()) / 5
    print(f"acheter-garder : rendement moyen {bh*100:+.1f} %, pire creux moyen {bhdd*100:.0f} %")
    for rule in ("T1", "T2", "T3", "T4", "T5"):
        R = []; DD = []; TR = []; expo = []
        for T, c in DATA.values():
            p = positions(rule, c); r, dd, tr = perf(T, c, p, a, b); R.append(r); DD.append(dd); TR += tr
            expo.append(sum(1 for i, t in enumerate(T) if a <= t < b and p[i] != 0) / max(1, sum(1 for t in T if a <= t < b)))
        rand = []
        for _ in range(300):
            s = 0
            for (T, c), e in zip(DATA.values(), expo):
                q = [0] * len(c); i = 0
                while i < len(c):
                    L = rnd.randint(5, 40); on = rnd.random() < e
                    for j in range(i, min(len(c), i + L)): q[j] = (1 if rule != "T2" else rnd.choice([1, -1])) if on else 0
                    i += L
                s += perf(T, c, q, a, b)[0]
            rand.append(s / 5)
        rand.sort(); p95 = rand[int(0.95 * len(rand))]
        m = sum(R) / 5; d = sum(DD) / 5
        w = [x for x in TR if x > 0]; l = [x for x in TR if x <= 0]
        wr = len(w) / len(TR) if TR else 0
        ok = period.startswith("2026") and m > 0 and m > bh and m > p95 and d > bhdd
        print(f"{rule} rendement moyen {m*100:+6.1f} % | pire creux {d*100:4.0f} % | trades {len(TR):3} | gagnants {wr:4.0%} | gagnant moyen {sum(w)/max(1,len(w))*100:+.1f} % / perdant moyen {sum(l)/max(1,len(l))*100:+.1f} % | hasard p95 {p95*100:+.1f} %" + (" → MARCHE" if ok else ""))
