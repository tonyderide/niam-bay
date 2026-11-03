"""PREREG-68 : sortie SL 5 %, activation 10 %, trailing 1 %, inversion après perte, en papier EN AVANT, 04/11/2026 → 03/05/2027 UTC.
Mêmes trades, deux comptes de 1 000 € par pièce : B mise fixe 10 €, C martingale m = 2, k = 4. Prix et financement PUBLICS, aucun ordre.
python3 papier68.py -> etat.json, journal.md, trades.csv ; python3 papier68.py juger (à partir du 04/05/2027)."""
import datetime as dt, hashlib, json, os, statistics as st, sys, time
ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(ICI, "..", "papier-90"))
from papier90 import klines, funding, ms, C, JM
S, A, T_, TK = 0.05, 0.10, 0.01, 0.0005; NT = 100; K0, M0 = 1000.0, 10.0
D0, FIN = ms(2026, 11, 4), ms(2027, 5, 4)
def eur(): return dict(cap=K0, mise=M0, p=0, bas=K0)
def neuf(): return dict(pos=None, inv=1.0, n=0, w=0, somme=0.0, fin=0.0, k=0, B=eur(), C=eur())
def sens_hasard(c, sim, k): return 1.0 if hashlib.sha256(f"68|{c}|{sim}|{k}".encode()).digest()[0] < 128 else -1.0
def jouer(g, r, m, k):
    """Même logique que `jouer` (t67.py)."""
    if g["cap"] < 50: return
    pos = min(g["mise"] / S, 10 * g["cap"]); g["cap"] += pos * r; g["bas"] = min(g["bas"], g["cap"])
    if r <= 0:
        g["p"] += 1; g["mise"] *= m
        if k > 0 and g["p"] >= k: g["mise"] = M0; g["p"] = 0
    else: g["mise"] = M0; g["p"] = 0
def clore(z, px, t, sortie):
    p = z["pos"]; s = p["s"]; e = p["e"]; r = s * (px / e - 1) - TK - TK * px / e + p["f"]
    z["n"] += 1; z["k"] += 1; z["w"] += r > 0; z["somme"] += r; jouer(z["B"], r, 1.0, 0); jouer(z["C"], r, 2.0, 4)
    if r <= 0: z["inv"] = -z["inv"]
    if sortie is not None: sortie.append((p["t0"], t, s, e, px, r))
    z["pos"] = None
def minute(z, b, fr, sens_f, sortie=None, derniere=False):
    """Même logique que `chaine` (t67.py). z = compte, b = (t, o, h, l, c), fr = taux de financement ou None."""
    t, op, h, l, c = b
    if z["pos"] is None:
        s = sens_f(z); z["pos"] = dict(s=s, e=op, sl=op * (1 - S * s), actif=False, pic=0.0, f=0.0, t0=t)
    p = z["pos"]; s = p["s"]; e = p["e"]
    if fr is not None:
        v = -s * fr * op / e; p["f"] += v; z["fin"] += v
    hi = h if s > 0 else l; lo = l if s > 0 else h; stop = p["sl"]; px = -1.0
    if p["actif"]:
        ts = p["pic"] * (1 - T_ * s); stop = max(p["sl"], ts) if s > 0 else min(p["sl"], ts)
    if (lo - stop) * s <= 0: px = min(op, stop) if s > 0 else max(op, stop)
    elif p["actif"]: p["pic"] = max(p["pic"], hi) if s > 0 else min(p["pic"], hi)
    elif (hi - e * (1 + A * s)) * s >= 0: p["actif"] = True; p["pic"] = hi
    if px < 0 and derniere: px = c
    if px >= 0: clore(z, px, t, sortie)
def bilan(Z, v):
    r = [z[v]["cap"] - K0 for z in Z]
    return dict(moyen=st.mean(r), median=st.median(r), positives=sum(x > 0 for x in r), bas=min(z[v]["bas"] for z in Z), sous500=sum(z[v]["bas"] <= 500 for z in Z))
def resume(E):
    Z = [E["reel"][c] for c in C]; fin = [z for z in Z if z["n"]]
    return dict(trades=sum(z["n"] for z in Z), gagnants=st.mean(z["w"] / z["n"] for z in fin) if fin else 0, esp=st.mean(z["somme"] / z["n"] for z in fin) if fin else 0,
                fin=st.mean(z["fin"] for z in Z), en_cours=sum(z["pos"] is not None for z in Z), B=bilan(Z, "B"), C=bilan(Z, "C"))
def temoin(E, v): return [st.mean(E["tem"][c][i][v]["cap"] - K0 for c in C) for i in range(NT)]
def maj():
    f = os.path.join(ICI, "etat.json"); E = json.load(open(f)) if os.path.exists(f) else dict(jusqua=D0, reel={c: neuf() for c in C}, tem={c: [neuf() for _ in range(NT)] for c in C})
    aj = min(int(time.time() * 1000) // JM * JM, FIN)
    if aj <= E["jusqua"]: print("aucun jour UTC terminé à traiter (premier jour : 04/11/2026)"); return
    B = {c: klines(c, E["jusqua"], aj) for c in C}; FR = {c: funding(c, E["jusqua"], aj) for c in C}; lignes = []   # tout ou rien : rien n'est écrit si une pièce échoue
    for c in C:
        for b in B[c]:
            fr = FR[c].get(b[0]); so = []; d = aj == FIN and b[0] == aj - 60_000; minute(E["reel"][c], b, fr, lambda z: z["inv"], so, d)
            lignes += [f"{c},{x[0]},{x[1]},{x[2]:+.0f},{x[3]},{x[4]},{x[5]:.6f}" for x in so]
            for i in range(NT): minute(E["tem"][c][i], b, fr, lambda z, i=i: sens_hasard(c, i, z["k"]), None, d)
    E["jusqua"] = aj; json.dump(E, open(f + ".tmp", "w")); os.replace(f + ".tmp", f); R = resume(E); tb = st.mean(temoin(E, "B")); tc = st.mean(temoin(E, "C")); J = dt.datetime.fromtimestamp((aj - 1) / 1000, dt.timezone.utc).strftime("%Y-%m-%d")
    json.dump(dict(R, dernier_jour=J, maj_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), temoin_B=tb, temoin_C=tc), open(os.path.join(ICI, "resume.json"), "w"), indent=1)
    if lignes: open(os.path.join(ICI, "trades.csv"), "a").write("\n".join(lignes) + "\n")
    L = os.path.join(ICI, "journal.md"); b, m = R["B"], R["C"]; li = f"| {J} | {R['trades']} | {100*R['gagnants']:.1f} % | {b['moyen']:+.0f} € | {b['positives']}/13 | {b['bas']:.0f} € | {tb:+.0f} € | {m['moyen']:+.0f} € | {m['positives']}/13 | {m['bas']:.0f} € | {tc:+.0f} € |"
    if f"| {J} |" not in open(L).read(): open(L, "a").write(li + "\n")
    print(li)
def juger():
    E = json.load(open(os.path.join(ICI, "etat.json")))
    if E["jusqua"] < FIN: sys.exit("période pas finie (jugement unique le 04/05/2027 ou après)")
    R = resume(E); print(R)
    for v, nom in (("B", "B mise fixe"), ("C", "C martingale")):
        x = R[v]; t = temoin(E, v); b = sum(y < x["moyen"] for y in t) / len(t); ok = x["moyen"] > 0 and x["positives"] >= 7 and x["sous500"] == 0 and b >= .95
        print(nom, x, "témoin battu", b, "VERDICT :", "TIENT" if ok else "NE TIENT PAS")
if __name__ == "__main__": juger() if len(sys.argv) > 1 and sys.argv[1] == "juger" else maj()
