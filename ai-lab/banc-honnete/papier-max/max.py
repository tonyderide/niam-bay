"""PREREG-50 : effet MAX en papier EN AVANT (semaines du lundi 09/11/2026 au lundi 26/04/2027), 150 perpétuels figés (univers.json).
Prix publics seulement (fapi/v1/klines 1d). Aucun ordre. Sans état.  python3 max.py | python3 max.py juger (à partir du 03/05/2027)"""
import datetime as dt, json, os, random, sys, time, urllib.request, urllib.error
ICI = os.path.dirname(os.path.abspath(__file__)); DON = os.path.join(ICI, "donnees"); JMS = 86_400_000; TK = 0.0005
U = json.load(open(os.path.join(ICI, "univers.json")))["symboles"]
ut = lambda y, m, d: int(dt.datetime(y, m, d, tzinfo=dt.timezone.utc).timestamp() * 1000)
HIST0, L0, LFIN = ut(2026, 10, 1), ut(2026, 11, 9), ut(2027, 4, 26)
LUNDIS = list(range(L0, LFIN + 1, 7 * JMS))
def klines(s, t0):
    u = f"https://fapi.binance.com/fapi/v1/klines?symbol={s}&interval=1d&startTime={t0}&limit=500"
    for e in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "nb-papier"}), timeout=20) as r: k = json.load(r); break
        except urllib.error.HTTPError as x:
            if x.code == 400: return []
            if e == 3: raise
        except Exception:
            if e == 3: raise
        time.sleep(5 * (e + 1))
    now = int(time.time() * 1000); return [[int(x[0]), float(x[1]), float(x[4])] for x in k if int(x[6]) < now and int(x[0]) < LFIN + 7 * JMS]
def charger(maj=True):
    os.makedirs(DON, exist_ok=True); D = {}
    for s in U:
        f = os.path.join(DON, f"{s}.json"); k = json.load(open(f)) if os.path.exists(f) else []
        if maj:
            t0 = k[-1][0] + JMS if k else HIST0
            if t0 < LFIN + 7 * JMS: k += [x for x in klines(s, t0) if x[0] >= t0]; time.sleep(0.05)
            json.dump(k, open(f, "w"))
        D[s] = {x[0]: (x[1], x[2]) for x in k}
    return D
def max30(D, s, lu):
    r = [D[s][d][1] / D[s][d - JMS][1] - 1 for d in range(lu - 30 * JMS, lu, JMS) if d in D[s] and d - JMS in D[s]]
    return max(r) if len(r) >= 25 else None
def rend(D, s, lu):
    if lu not in D[s]: return None
    fin = lu + 7 * JMS
    if fin in D[s]: return D[s][fin][0] / D[s][lu][0] - 1
    d = max(x for x in D[s] if x < fin); return D[s][d][1] / D[s][lu][0] - 1        # retrait : dernier prix
def semaines(D):
    now = int(time.time() * 1000); return [lu for lu in LUNDIS if lu + 7 * JMS <= now and any(lu + 6 * JMS in D[s] for s in U)]
def eligibles(D, lu): return [s for s in U if lu in D[s] and max30(D, s, lu) is not None]
def poids(D, lu):
    e = eligibles(D, lu)
    if len(e) < 10: return {}
    m = {s: max30(D, s, lu) for s in e}; o = sorted(e, key=m.get); q = len(e) // 5
    return {**{s: 0.5 / q for s in o[:q]}, **{s: -0.5 / q for s in o[-q:]}}     # long MAX faible, short MAX fort
def serie(D, W, L):
    prev = {}; out = []
    for lu, w in zip(L, W):
        fr = TK * sum(abs(w.get(s, 0) - prev.get(s, 0)) for s in set(w) | set(prev))
        out.append((sum(v * rend(D, s, lu) for s, v in w.items()), fr)); prev = w
    return out
def mettre_a_jour():
    D = charger(); L = semaines(D)
    if not L: print("aucune semaine terminée (première : lundi 09/11/2026)"); return
    W = [poids(D, lu) for lu in L]; S = serie(D, W, L)
    net = sum(g - f for g, f in S); j = dt.datetime.fromtimestamp(L[-1] / 1000, dt.timezone.utc).strftime("%Y-%m-%d")
    json.dump(dict(maj_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), derniere_semaine=j, semaines=len(L), net=net), open(os.path.join(ICI, "etat.json"), "w"), indent=1)
    J = os.path.join(ICI, "journal.md"); deja = open(J).read()
    ligne = f"| {j} | {len(L)} | {100*(S[-1][0]-S[-1][1]):+.2f} % | {100*net:+.2f} % | {100*sum(f for _, f in S):.2f} % | {len(W[-1])} |"
    if f"| {j} |" not in deja:
        with open(J, "a") as f: f.write(ligne + "\n")
    print(ligne)
def juger():
    D = charger(); L = semaines(D)
    if not L or L[-1] != LFIN: sys.exit("période pas finie (jugement unique le 03/05/2027 ou après)")
    W = [poids(D, lu) for lu in L]; net = sum(g - f for g, f in serie(D, W, L)); kp = []
    for a, b in zip(W, W[1:]):
        for sg in (1, -1):
            A = {s for s, v in a.items() if v * sg > 0}; B = {s for s, v in b.items() if v * sg > 0}
            if A and B: kp.append(len(A & B) / len(B))
    kp = sum(kp) / len(kp); rng = random.Random(50); tem = []
    for _ in range(1000):
        T = []; prev = {1: set(), -1: set()}
        for lu, w in zip(L, W):
            e = eligibles(D, lu); cote = {}; n = {sg: sum(1 for v in w.values() if v * sg > 0) for sg in (1, -1)}
            for sg in (1, -1):
                g = [s for s in prev[sg] if s in e and rng.random() < kp][:n[sg]]
                pris = set(g) | (cote.get(1, set()) if sg == -1 else set())
                cote[sg] = set(g) | set(rng.sample(sorted(set(e) - pris), n[sg] - len(g)))
            T.append({**{s: 0.5 / n[1] for s in cote[1]}, **{s: -0.5 / n[-1] for s in cote[-1]}} if n[1] else {}); prev = cote
        tem.append(sum(g - f for g, f in serie(D, T, L)))
    p = sum(t >= net for t in tem) / len(tem); v = "GAGNE" if net > 0 and p < 0.05 else "NON DÉMONTRÉ" if net > 0 else "PERD"
    r = dict(net=net, conservation=kp, temoin_moy=sum(tem) / len(tem), p=p, verdict=v); json.dump(r, open(os.path.join(ICI, "jugement.json"), "w"), indent=1); print(r)
if __name__ == "__main__":
    juger() if sys.argv[1:] == ["juger"] else mettre_a_jour()
