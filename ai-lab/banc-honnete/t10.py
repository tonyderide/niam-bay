import banc, calendar, time, random, statistics
M = ["BTC","ETH","SOL","XRP","DOGE","ADA","LINK","AVAX","DOT","LTC","BCH","UNI","ATOM","NEAR","FIL","AAVE","APT","OP","TRX","XLM","ETC"]
px = {}
for m in M:
    T, C = banc.candles(banc.SYM[m], "1d"); px[m] = {t: c[0] for t, c in zip(T, C)}  # open du jour
lundi0 = calendar.timegm((2023, 1, 2, 0, 0, 0)); W = []; t = lundi0
while t < calendar.timegm((2026, 10, 13, 0, 0, 0)): W.append(t); t += 7 * 86400
def r(m, a, b): return px[m][b] / px[m][a] - 1 if a in px[m] and b in px[m] else None
def semaines(L, sens, a, b, rnd=None):
    out = []
    for k in range(L, len(W) - 1):
        if not (a <= W[k] < b): continue
        past = {m: r(m, W[k - L], W[k]) for m in M}; nxt = {m: r(m, W[k], W[k + 1]) for m in M}
        ok = [m for m in M if past[m] is not None and nxt[m] is not None]
        if len(ok) < 12: continue
        if rnd: rnd.shuffle(ok); hi, lo = ok[:5], ok[5:10]
        else:
            ok.sort(key=lambda m: past[m]); lo, hi = ok[:5], ok[-5:]
            if sens == "retournement": hi, lo = lo, hi
        out.append(0.5 * statistics.mean(nxt[m] for m in hi) - 0.5 * statistics.mean(nxt[m] for m in lo) - 0.001)
    return out
A, B, J0, J1, CUT = banc.ts("2024-01-01"), banc.ts("2026-01-01"), banc.ts("2026-01-05"), banc.ts("2026-10-13"), banc.ts("2026-07-01")
res = []
for L in (1, 2, 4):
    for sens in ("momentum", "retournement"):
        s = semaines(L, sens, A, B); res.append((sum(s), L, sens, len(s), sum(x > 0 for x in s) / len(s)))
        print(f"  L={L} {sens:13} 2024-25 : somme {sum(s)*100:+7.1f} % sur {len(s)} semaines, {sum(x > 0 for x in s)/len(s):.0%} positives", flush=True)
tot, L, sens, n, _ = max(res); print(f"\nSÉLECTION : L={L} {sens}")
j = semaines(L, sens, J0, J1); S = sum(j)
R = sorted(sum(semaines(L, sens, J0, J1, random.Random(i))) for i in range(2000))
win = S > 0 and S > R[1900] and sum(x > 0 for x in j) / len(j) > 0.5
print(f"JUGEMENT 2026 : somme {S*100:+.1f} % sur {len(j)} semaines, {sum(x > 0 for x in j)/len(j):.0%} positives · hasard méd. {R[1000]*100:+.1f} % p95 {R[1900]*100:+.1f} % · rang {sum(x < S for x in R)/20:.0f}e centile")
print("VERDICT :", "GAGNE" if win else "ÉCHEC")
a1 = semaines(L, sens, J0, CUT); a2 = semaines(L, sens, CUT, J1)
print(f"[info] jan-juin {sum(a1)*100:+.1f} % ({len(a1)} sem.) · juil-oct, après cutoff {sum(a2)*100:+.1f} % ({len(a2)} sem.)")
