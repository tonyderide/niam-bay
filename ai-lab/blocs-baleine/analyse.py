"""Blocs de baleine (PREREGISTRATION.md + précisions du 27/10). Lancé sur la VM : python3 analyse.py ~/nb/suiveurs FIN_MS"""
import glob, json, math, os, random, statistics, sys
DOS, FIN = os.path.expanduser(sys.argv[1]), int(sys.argv[2]); M = 60000
prix_min = {}; series = {}  # (passif, px) -> fills en cours
blocs = []
def clore(cle, run):
    if len(run) >= 20 and sum(z for _, z in run) >= 5:
        blocs.append({"fin": run[-1][0], "cote": cle[2], "n": len(run), "btc": sum(z for _, z in run)})
for f in sorted(glob.glob(os.path.join(DOS, "trades-*.jsonl"))):
    for l in open(f):
        try: x = json.loads(l)
        except Exception: continue
        t = x["t"]
        if t > FIN: break
        px, sz = float(x["px"]), float(x["sz"]); prix_min[t // M] = px
        passif, cote = (x["u"][1], "VENTE") if x["s"] == "B" else (x["u"][0], "ACHAT")
        cle = (passif, x["px"], cote); run = series.get(cle)
        if run and t - run[0][0] < 3 * M: run.append((t, sz))
        else:
            if run: clore(cle, run)
            series[cle] = [(t, sz)]
        if len(series) > 200000:  # ménage : clore les séries trop vieilles
            for k in [k for k, r in series.items() if t - r[0][0] >= 3 * M]: clore(k, series.pop(k))
for k, r in series.items(): clore(k, r)
mins = sorted(prix_min); m0, m1 = mins[0], mins[-1]
def p_at(m):  # dernier prix connu à la minute m
    while m >= m0 and m not in prix_min: m -= 1
    return prix_min.get(m)
def vol(m):
    r = [p_at(k) / p_at(k - 1) - 1 for k in range(m - 59, m + 1) if p_at(k) and p_at(k - 1)]
    return statistics.pstdev(r) if len(r) > 30 else None
def ret(m):
    a, b = p_at(m), p_at(m + 240); return b / a - 1 if a and b else None
milieu = (m0 + m1) // 2; dernier = m1 - 240
V = {m: vol(m) for m in range(m0 + 60, dernier + 1, 5)}  # grille de 5 min pour les quartiles et les témoins
vs = sorted(v for v in V.values() if v is not None); q = [vs[len(vs) * i // 4] for i in (1, 2, 3)]
quart = lambda v: sum(v > x for x in q)
pool = {}
for m, v in V.items():
    if v is not None: pool.setdefault((m < milieu, quart(v)), []).append(m)
rnd = random.Random(19); R = {}
for b in blocs:
    m = b["fin"] // M
    if m + 240 > m1 or m < m0 + 60: continue
    v = vol(m); r = ret(m)
    if v is None or r is None: continue
    t = None
    for _ in range(20):
        c = rnd.choice(pool[(m < milieu, quart(v))]); rt = ret(c)
        if rt is not None: t = rt; break
    if t is None: continue
    R.setdefault((b["cote"], "découverte" if m < milieu else "confirmation"), []).append((r, t))
print(f"données {json.dumps([m0*M, m1*M])}, blocs détectés {len(blocs)}")
for k in sorted(R): print("pré-vol", k, len(R[k]))
ok = all(len(R.get((c, h), [])) >= 15 for c in ("ACHAT", "VENTE") for h in ("découverte", "confirmation"))
if not ok: print("VERDICT : INDÉCIDABLE (moins de 15 blocs dans au moins une case) ; la collecte continue"); sys.exit()
for c in ("ACHAT", "VENTE"):
    d = R[(c, "découverte")]; e = R[(c, "confirmation")]
    sens = 1 if statistics.mean(r - t for r, t in d) > 0 else -1
    ecart = statistics.mean(r for r, _ in e) - statistics.mean(t for _, t in e)
    rb = random.Random(7); opp = 0
    for _ in range(10000):
        s = [e[rb.randrange(len(e))] for _ in e]; opp += sens * (statistics.mean(r for r, _ in s) - statistics.mean(t for _, t in s)) <= 0
    P = opp / 10000; g = sens * ecart > 0 and abs(ecart) > 0.0015 and P < 0.05
    print(f"{c} : sens découverte {'+' if sens > 0 else '−'} ; confirmation écart {100*ecart:+.3f} % (n={len(e)}), P={P:.3f} → {'EXPLOITABLE' if g else 'rien d exploitable'}")
