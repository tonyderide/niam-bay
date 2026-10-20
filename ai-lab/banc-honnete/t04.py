import json, time, urllib.request, random, calendar
ts = lambda d: calendar.timegm(time.strptime(d, "%Y-%m-%d")); FEE = 0.0005
def get(sym, res, a, b):
    step = {"1h": 3600, "4h": 14400}[res]; out = {}; t = a - 100*step
    while t < b:
        for _ in range(8):
            try: d = json.load(urllib.request.urlopen(f"https://futures.kraken.com/api/charts/v1/trade/{sym}/{res}?from={t}&to={min(b, t+1800*step)}", timeout=60))["candles"]; break
            except Exception: time.sleep(3)
        for c in d: out[c["time"]//1000] = tuple(float(c[x]) for x in ("open","high","low","close"))
        t += 1800*step; time.sleep(0.2)
    T = sorted(out); return T, [out[x] for x in T]
def cut(T, C, a, b):
    idx = [i for i, t in enumerate(T) if a <= t < b]; return C[idx[0]:idx[-1]+1], idx[0]
# ---- A : stop suiveur X% avec retournement
def trailA(C, X, s0=1):
    pos = s0; ent = C[0][0]; ext = ent; eq = 1 - FEE
    for o, h, l, c in C:
        st = ext*(1-X) if pos > 0 else ext*(1+X)
        if (pos > 0 and l <= st) or (pos < 0 and h >= st):
            px = min(o, st) if pos > 0 else max(o, st)
            eq *= (1 + pos*(px/ent-1) - FEE) * (1 - FEE); pos = -pos; ent = px; ext = px
            ext = max(ext, h) if False else ext
            continue
        ext = max(ext, h) if pos > 0 else min(ext, l)
    eq *= 1 + pos*(C[-1][3]/ent-1) - FEE
    return eq-1
# ---- B : Donchian 20 + chandelier 3*ATR22
def atr(C, n=22):
    a = [C[0][1]-C[0][2]]
    for i in range(1, len(C)):
        tr = max(C[i][1]-C[i][2], abs(C[i][1]-C[i-1][3]), abs(C[i][2]-C[i-1][3])); a.append(a[-1]+(tr-a[-1])/n)
    return a
def ride(C, A, i, s):  # entre à l'open i, sortie chandelier ; renvoie (r, j)
    ent = C[i][0]; ext = ent
    for j in range(i, len(C)):
        o, h, l, c = C[j]; st = ext - s*3*A[j-1]
        if (s > 0 and l <= st) or (s < 0 and h >= st):
            px = min(o, st) if s > 0 else max(o, st); return s*(px/ent-1) - 2*FEE, j
        ext = max(ext, h) if s > 0 else min(ext, l)
    return s*(C[-1][3]/ent-1) - 2*FEE, len(C)-1
def turtle(C, A, lo):
    tr = []; i = max(lo, 21)
    while i < len(C)-1:
        hh = max(x[1] for x in C[i-20:i]); ll = min(x[2] for x in C[i-20:i]); c = C[i][3]
        if c > hh or c < ll:
            r, j = ride(C, A, i+1, 1 if c > hh else -1); tr.append(r); i = j+1
        else: i += 1
    return tr
SYM = {"BTC": "PF_XBTUSD", "ETH": "PF_ETHUSD", "SOL": "PF_SOLUSD"}
A0, J1, J7, END = ts("2024-01-01"), ts("2026-01-01"), ts("2026-07-01"), ts("2026-10-17")
D = {res: {k: get(s, res, A0, END) for k, s in SYM.items()} for res in ("1h", "4h")}
ok = True
print("== A : stop suiveur X % + retournement (1h) ==")
sel = {X: sum(trailA(cut(*D["1h"][k], J1, J7)[0], X) for k in SYM) for X in (.01, .02, .03, .05, .08)}
print("  sélection janv-juin 2026 :", " ".join(f"{X*100:.0f}%→{v*100:+.0f}" for X, v in sel.items()))
X = max(sel, key=sel.get); print(f"  X figé = {X*100:.0f} %")
for per, a, b in (("2024-2025", A0, J1), ("juil-oct 2026", J7, END)):
    rs = {k: trailA(cut(*D["1h"][k], a, b)[0], X) for k in SYM}; S = sum(rs.values())
    alt = sum(trailA(cut(*D["1h"][k], a, b)[0], X, -1) for k in SYM)
    g = S > 0 and S > max(S, alt) - 1e-12 and sum(v > 0 for v in rs.values()) >= 2
    ok &= g; print(f"  {per}: " + " ".join(f"{k} {v*100:+.1f}%" for k, v in rs.items()) + f" | somme {S*100:+.1f}% | départ short {alt*100:+.1f}% | {'OK' if g else 'NON'}")
print("== B : Donchian 20 + chandelier 3×ATR ==")
for res in ("1h", "4h"):
    for per, a, b in (("2024-2025", A0, J1), ("2026", J1, END)):
        S = 0; pos = 0; R = [0]*500; info = []
        for k in SYM:
            T, C = D[res][k]; A = atr(C); lo = next(i for i, t in enumerate(T) if t >= a); hi = max(i for i, t in enumerate(T) if t < b)+1
            Cc = C[:hi]; Ac = A[:hi]; tr = turtle(Cc, Ac, lo); r = sum(tr); S += r; pos += r > 0; info.append(f"{k} {len(tr)}tr {r*100:+.1f}%")
            for j in range(500):
                rnd = random.Random(j); R[j] += sum(ride(Cc, Ac, rnd.randrange(lo+1, hi-1), rnd.choice((1,-1)))[0] for _ in tr)
        R.sort(); g = S > 0 and S > R[475] and pos >= 2; ok &= g
        print(f"  {res} {per}: " + " | ".join(info) + f" | somme {S*100:+.1f}% | hasard p95 {R[475]*100:+.1f}% | {'OK' if g else 'NON'}", flush=True)
print("VERDICT :", "GAGNE" if ok else "PERD")
