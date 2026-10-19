# Applique PREREG-REVALID-2024.md.
import json, time, urllib.request, random, calendar, bisect
ts = lambda d: calendar.timegm(time.strptime(d, "%Y-%m-%d"))
A, B = ts("2024-01-01"), ts("2026-01-01"); FEE = 0.001
def get(url, body=None):
    for _ in range(8):
        try:
            req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None, headers={"Content-Type": "application/json"})
            return json.load(urllib.request.urlopen(req, timeout=60))
        except Exception: time.sleep(3)
    raise SystemExit("API KO " + url)
def h1(sym):
    out = {}; t = A - 200*3600
    while t < B:
        for c in get(f"https://futures.kraken.com/api/charts/v1/trade/{sym}/1h?from={t}&to={min(B, t+1800*3600)}")["candles"]:
            out[c["time"]//1000] = (float(c["open"]), float(c["close"]))
        t += 1800*3600; time.sleep(0.2)
    T = sorted(out); return T, [out[x] for x in T]
def funding(coin, a, b):
    out = {}; t = a*1000
    while t < b*1000:
        d = get("https://api.hyperliquid.xyz/info", {"type": "fundingHistory", "coin": coin, "startTime": t, "endTime": b*1000})
        if not d: break
        for x in d: out[x["time"]//3600000*3600] = float(x["fundingRate"])
        nt = d[-1]["time"] + 1
        if nt <= t: break
        t = nt; time.sleep(0.3)
    return out
def rand_null(series, n, H, rnd, lo, hi):
    return sum(rnd.choice((1,-1))*(series[i+H]/series[i]-1) - FEE for i in (rnd.randrange(lo, hi-H) for _ in range(n)))
def report(name, per):  # per: {coin: [(t, r)]}, null: function
    tot = {c: sum(r for _, r in v) for c, v in per.items()}; S = sum(tot.values()); n = sum(len(v) for v in per.values())
    yr = {Y: sum(r for v in per.values() for t, r in v if time.gmtime(t).tm_year == Y) for Y in (2024, 2025)}
    return tot, S, n, yr
SYM = {"BTC": "PF_XBTUSD", "ETH": "PF_ETHUSD", "SOL": "PF_SOLUSD"}
D = {c: h1(s) for c, s in SYM.items()}
# ---------- Piste A : chocs ----------
A_tr, A_null_args = {}, {}
for c, (T, V) in D.items():
    cl = [v[1] for v in V]; r = [0] + [cl[i]/cl[i-1]-1 for i in range(1, len(cl))]; tr = []; busy = -1
    for t in range(169, len(cl)-26):
        if T[t] < A or t <= busy: continue
        w = r[t-168:t]; m = sum(w)/168; sd = (sum((x-m)**2 for x in w)/167)**.5
        if abs(r[t]) > 2*sd:
            s = 1 if r[t] > 0 else -1; tr.append((T[t+1], s*(cl[t+25]/cl[t+1]-1) - FEE)); busy = t+25
    A_tr[c] = tr; A_null_args[c] = (cl, len(tr), bisect.bisect_left(T, A), len(cl)-1)
# ---------- Piste B : funding ----------
F = {c: funding(c, A - 91*86400, B) for c in D}
F26 = {c: funding(c, ts("2026-01-01"), ts("2026-07-01")) for c in D}
def pct(xs, p): xs = sorted(xs); return xs[min(len(xs)-1, int(p/100*len(xs)))]
def pisteB(c, fixed=False):
    T, V = D[c]; idx = {t: i for i, t in enumerate(T)}; op = [v[0] for v in V]; f = F[c]; keys = sorted(f); tr = []; busy = 0
    if fixed: hi0, lo0 = pct(F26[c].values(), 90), pct(F26[c].values(), 10)
    for h in keys:
        if h < A or h < busy or h+3600 not in idx or h+5*3600 not in idx: continue
        if fixed: hi, lo = hi0, lo0
        else:
            j0 = bisect.bisect_left(keys, h - 90*86400); j1 = bisect.bisect_left(keys, h); w = [f[k] for k in keys[j0:j1]]
            if len(w) < 1000: continue
            hi, lo = pct(w, 90), pct(w, 10)
        s = -1 if f[h] > hi else 1 if f[h] < lo else 0
        if s: tr.append((h+3600, s*(op[idx[h+5*3600]]/op[idx[h+3600]]-1) - FEE)); busy = h+5*3600
    return tr, op
B_tr = {}; B_null = {}
for c in D:
    tr, op = pisteB(c); B_tr[c] = tr; B_null[c] = (op, len(tr), bisect.bisect_left(D[c][0], A), len(op)-1)
B_fix = {c: pisteB(c, True)[0] for c in D}
for name, per, H, args in (("A chocs 1h suite k=2 H=24", A_tr, 24, A_null_args), ("B funding contrarien P90 4h", B_tr, 4, B_null)):
    tot, S, n, yr = report(name, per)
    R = sorted(sum(rand_null(*args[c][:2], H, rnd, *args[c][2:]) for c in per) for rnd in (random.Random(j) for j in range(500)))
    win = sum(v > 0 for v in tot.values()) >= 2 and S > R[475] and n >= 30 and all(v > 0 for v in yr.values())
    print(f"\n== {name} ==")
    for c in per: print(f"  {c}: trades {len(per[c]):4} | net {tot[c]*100:+7.1f} % | gagnants {sum(r>0 for _, r in per[c])/max(1,len(per[c])):.0%}")
    print(f"  SOMME {S*100:+.1f} % | hasard médiane {R[250]*100:+.1f} % p95 {R[475]*100:+.1f} % | 2024 {yr[2024]*100:+.1f} % | 2025 {yr[2025]*100:+.1f} %")
    print("  VERDICT :", "GAGNE" if win else "PERD")
print("\n[indicatif] B avec seuils figés 2026 :", " ".join(f"{c} {len(v)} tr {sum(r for _, r in v)*100:+.1f}%" for c, v in B_fix.items()))
