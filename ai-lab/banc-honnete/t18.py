"""PREREG-15 : confirmation du candidat SOL 1 h EMA 9/21, TP 2 % / SL 1 %."""
import random
import banc
import t17_lib as L
A, B = banc.ts("2024-01-01"), banc.ts("2026-10-17"); C0 = banc.ts("2026-01-01")
PAIRES = "XRP DOGE ADA LINK AVAX DOT LTC BCH UNI ATOM NEAR FIL AAVE APT OP TRX XLM ETC".split()
# --- Test A ---
tot = 0.0; pos = 0; info = []
for m in PAIRES:
    T, C = banc.candles(banc.SYM[m], "1h"); s = L.sig_ema(C, 9, 21)
    R, nl, ns, lo, hi = L.strat(C, T, s, 0.02, 0.01, A, B); g = sum(R); tot += g; pos += g > 0
    info.append((m, g, len(R), nl, ns, lo, hi, C))
rnd = random.Random(15); J = []
for _ in range(500):
    t = 0.0
    for m, g, n, nl, ns, lo, hi, C in info:
        for sens, cnt in ((1, nl), (-1, ns)):
            for _ in range(cnt): t += L.trade(C, rnd.randrange(lo + 1, hi - L.MAXB), sens, 0.02, 0.01)[0]
    J.append(t)
J.sort(); okA = tot > 0 and tot > J[475] and pos >= 10
print("Test A (18 paires jamais vues, 2024 -> oct. 2026) :")
for m, g, n, *_ in sorted(info, key=lambda x: -x[1]): print(f"  {m:5} {100*g:+7.1f} % ({n} trades)")
print(f"  somme {100*tot:+.1f} % | positives {pos}/18 | jumeaux méd {100*J[250]:+.1f} % p95 {100*J[475]:+.1f} % -> {'RÉUSSI' if okA else 'RATÉ'}")
# --- Test B ---
T, C = banc.candles(banc.SYM["SOL"], "1h"); vois = []
for (f, s_, tp, sl) in ((9, 21, 0.015, 0.0075), (9, 21, 0.025, 0.0125), (9, 21, 0.02, 0.015), (8, 21, 0.02, 0.01), (10, 20, 0.02, 0.01)):
    R = L.strat(C, T, L.sig_ema(C, f, s_), tp, sl, C0, B)[0]; vois.append(sum(R)); print(f"Test B : EMA {f}/{s_} TP {tp:.2%} SL {sl:.2%} -> 2026 {100*sum(R):+.1f} % ({len(R)} trades)")
okB = sum(v > 0 for v in vois) >= 4; print(f"  voisins positifs {sum(v > 0 for v in vois)}/5 -> {'RÉUSSI' if okB else 'RATÉ'}")
# --- Test C ---
L.FEE = 0.0005 + 0.0005
R = L.strat(C, T, L.sig_ema(C, 9, 21), 0.02, 0.01, C0, B)[0]; okC = sum(R) > 0
print(f"Test C : +5 pb de glissement par côté -> 2026 {100*sum(R):+.1f} % ({len(R)} trades) -> {'RÉUSSI' if okC else 'RATÉ'}")
print("VERDICT :", "CONFIRMÉ (-> papier en direct)" if okA and okB and okC else "NON CONFIRMÉ (chance / régime 2026)")
