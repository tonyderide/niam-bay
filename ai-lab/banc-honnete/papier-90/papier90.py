"""PREREG-65 : règle à 90 % (SL 10 %, activation 1 %, trailing 0,5 %, inversion après perte) en papier EN AVANT, 04/11/2026 → 03/05/2027 UTC.
Prix et financement PUBLICS (Binance fapi, sans clé). Aucun ordre, aucun compte. python3 papier90.py -> etat.json, journal.md, trades.csv ; python3 papier90.py juger (à partir du 04/05/2027)."""
import datetime as dt, hashlib, json, os, statistics as st, sys, time, urllib.request, urllib.error
ICI = os.path.dirname(os.path.abspath(__file__)); S, A, T_, TK = 0.10, 0.01, 0.005, 0.0005; MM, JM = 60_000, 86_400_000; NT = 100
C = "BTC ETH SOL XRP DOGE ADA LINK AVAX LTC BNB DOT BCH ATOM".split()
ms = lambda a, m, j: int(dt.datetime(a, m, j, tzinfo=dt.timezone.utc).timestamp() * 1000)
D0, FIN = ms(2026, 11, 4), ms(2027, 5, 4)
def get(u):
    for e in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "nb-papier"}), timeout=30) as r: return json.load(r)
        except Exception:
            if e == 3: raise
            time.sleep(5 * (e + 1))
def klines(s, t0, t1):
    o = []; t = t0
    while t < t1:
        k = get(f"https://fapi.binance.com/fapi/v1/klines?symbol={s}USDT&interval=1m&startTime={t}&endTime={t1 - 1}&limit=1500")
        if not k: raise RuntimeError(f"{s}: pas de bougie à {t}")
        for x in k:
            if int(x[0]) != t: raise RuntimeError(f"{s}: trou à {t}")
            o.append((t, float(x[1]), float(x[2]), float(x[3]), float(x[4]))); t += MM
    return o
def funding(s, t0, t1):
    o = {}; t = t0
    while t < t1:
        k = get(f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={s}USDT&startTime={t}&endTime={t1 - 1}&limit=1000")
        if not k: break
        for x in k: o[int(x["fundingTime"]) // MM * MM] = float(x["fundingRate"])
        t = int(k[-1]["fundingTime"]) + 1
        if len(k) < 1000: break
    return o
def neuf(): return dict(pos=None, inv=1.0, n=0, w=0, somme=0.0, cap=1.0, pic=1.0, baisse=0.0, fin=0.0, k=0)
def sens_hasard(c, sim, k): return 1.0 if hashlib.sha256(f"{c}|{sim}|{k}".encode()).digest()[0] < 128 else -1.0
def minute(z, b, fr, sens_f, sortie=None):
    """Même logique que `chaine` (t62.py). z = compte, b = (t, o, h, l, c), fr = taux de financement ou None."""
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
    if px < 0: return
    r = s * (px / e - 1) - TK - TK * px / e + p["f"]
    z["n"] += 1; z["k"] += 1; z["w"] += r > 0; z["somme"] += r; z["cap"] *= 1 + r; z["pic"] = max(z["pic"], z["cap"]); z["baisse"] = min(z["baisse"], z["cap"] / z["pic"] - 1)
    if r <= 0: z["inv"] = -z["inv"]
    if sortie is not None: sortie.append((p["t0"], t, s, e, px, r))
    z["pos"] = None
def resume(E):
    Z = [E["reel"][c] for c in C]; fin = [z for z in Z if z["n"]]
    return dict(trades=sum(z["n"] for z in Z), gagnants=st.mean(z["w"] / z["n"] for z in fin) if fin else 0, esp=st.mean(z["somme"] / z["n"] for z in fin) if fin else 0,
                portefeuille=st.mean(z["cap"] for z in Z) - 1, positives=sum(z["cap"] > 1 for z in Z), baisse_med=st.median(z["baisse"] for z in Z), fin=st.mean(z["fin"] for z in Z))
def temoin(E):
    o = []
    for i in range(NT):
        v = [E["tem"][c][i] for c in C]; v = [z["somme"] / z["n"] for z in v if z["n"]]
        if v: o.append(st.mean(v))
    return o
def maj():
    f = os.path.join(ICI, "etat.json"); E = json.load(open(f)) if os.path.exists(f) else dict(jusqua=D0, reel={c: neuf() for c in C}, tem={c: [neuf() for _ in range(NT)] for c in C})
    aj = min(int(time.time() * 1000) // JM * JM, FIN)
    if aj <= E["jusqua"]: print("aucun jour UTC terminé à traiter (premier jour : 04/11/2026)"); return
    B = {c: klines(c, E["jusqua"], aj) for c in C}; FR = {c: funding(c, E["jusqua"], aj) for c in C}; lignes = []   # tout ou rien : rien n'est écrit si une pièce échoue
    for c in C:
        for b in B[c]:
            fr = FR[c].get(b[0]); so = []; minute(E["reel"][c], b, fr, lambda z: z["inv"], so)
            lignes += [f"{c},{x[0]},{x[1]},{x[2]:+.0f},{x[3]},{x[4]},{x[5]:.6f}" for x in so]
            for i in range(NT): minute(E["tem"][c][i], b, fr, lambda z, i=i: sens_hasard(c, i, z["k"]))
    E["jusqua"] = aj; json.dump(E, open(f + ".tmp", "w")); os.replace(f + ".tmp", f); R = resume(E); m = temoin(E); J = dt.datetime.fromtimestamp((aj - 1) / 1000, dt.timezone.utc).strftime("%Y-%m-%d")
    json.dump(dict(R, dernier_jour=J, maj_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), temoin_esp=st.mean(m) if m else None), open(os.path.join(ICI, "resume.json"), "w"), indent=1)
    if lignes: open(os.path.join(ICI, "trades.csv"), "a").write("\n".join(lignes) + "\n")
    L = os.path.join(ICI, "journal.md"); li = f"| {J} | {R['trades']} | {100*R['gagnants']:.1f} % | {100*R['esp']:+.3f} % | {100*R['portefeuille']:+.2f} % | {R['positives']}/13 | {100*R['baisse_med']:.1f} % | {100*R['fin']:+.2f} % | {100*st.mean(m) if m else 0:+.3f} % |"
    if f"| {J} |" not in open(L).read(): open(L, "a").write(li + "\n")
    print(li)
def juger():
    E = json.load(open(os.path.join(ICI, "etat.json")))
    if E["jusqua"] < FIN: sys.exit("période pas finie (jugement unique le 04/05/2027 ou après)")
    R = resume(E); m = temoin(E); b = sum(x < R["esp"] for x in m) / len(m)
    ok = R["gagnants"] >= .90 and R["esp"] > 0 and R["positives"] >= 7 and R["portefeuille"] > 0 and R["baisse_med"] > -.30 and b >= .95
    print(R, "témoin battu", b, "VERDICT :", "TIENT" if ok else "NE TIENT PAS")
if __name__ == "__main__": juger() if len(sys.argv) > 1 and sys.argv[1] == "juger" else maj()
