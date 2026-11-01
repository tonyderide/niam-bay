"""PREREG-45 : réversion transversale à 1 jour, test papier EN AVANT (03/11/2026 → 02/05/2027), 50 perpétuels figés dans univers.json.
Prix PUBLICS seulement (Binance fapi/v1/klines 1d, sans clé). Aucun ordre. Sans état : tout est recalculé à chaque passage.
  python3 reversion.py        -> donnees/, journal.md, etat.json        python3 reversion.py juger  -> verdict (à partir du 03/05/2027)"""
import datetime as dt, json, os, random, sys, time, urllib.request
ICI = os.path.dirname(os.path.abspath(__file__)); DON = os.path.join(ICI, "donnees"); JMS = 86_400_000; TK = 0.0005
U = json.load(open(os.path.join(ICI, "univers.json")))["symboles"]
SIG0 = int(dt.datetime(2026, 11, 2, tzinfo=dt.timezone.utc).timestamp() * 1000)      # premier jour de signal
J0 = SIG0 + JMS                                                                        # premier jour tenu : 03/11/2026
FIN = int(dt.datetime(2027, 5, 3, tzinfo=dt.timezone.utc).timestamp() * 1000)         # exclu : dernier jour tenu 02/05/2027
def klines(s, t0):
    u = f"https://fapi.binance.com/fapi/v1/klines?symbol={s}&interval=1d&startTime={t0}&limit=500"
    for e in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "nb-papier"}), timeout=20) as r: k = json.load(r); break
        except urllib.error.HTTPError as x:
            if x.code == 400: return []          # symbole retiré
            if e == 3: raise
        except Exception:
            if e == 3: raise
        time.sleep(5 * (e + 1))
    now = int(time.time() * 1000)
    return [[int(x[0]), float(x[1]), float(x[4])] for x in k if int(x[6]) < now and int(x[0]) < FIN]
def charger(maj=True):
    os.makedirs(DON, exist_ok=True); D = {}
    for s in U:
        f = os.path.join(DON, f"{s}.json"); k = json.load(open(f)) if os.path.exists(f) else []
        if maj:
            t0 = k[-1][0] + JMS if k else SIG0
            if t0 < FIN: k += [x for x in klines(s, t0) if x[0] >= t0]
            json.dump(k, open(f, "w"))
        D[s] = {x[0]: (x[1], x[2]) for x in k}
    return D
def jours_tenus(D):
    fin = max((max(v) for v in D.values() if v), default=0)
    return list(range(J0, min(fin + JMS, FIN), JMS))
def poids(D, d):
    """Classement par rendement de la veille (ouverture → clôture) parmi les pièces cotées la veille ET ce jour."""
    e = [s for s in U if d - JMS in D[s] and d in D[s]]
    if len(e) < 10: return {}
    r = {s: D[s][d - JMS][1] / D[s][d - JMS][0] - 1 for s in e}; o = sorted(e, key=r.get); q = len(e) // 5
    return {**{s: 0.5 / q for s in o[:q]}, **{s: -0.5 / q for s in o[-q:]}}     # long les perdantes, short les gagnantes
def serie(D, W, J):
    prev = {}; out = []
    for d, w in zip(J, W):
        fr = TK * sum(abs(w.get(s, 0) - prev.get(s, 0)) for s in set(w) | set(prev))
        g = sum(v * (D[s][d][1] / D[s][d][0] - 1) for s, v in w.items()); out.append((g, fr)); prev = w
    return out
def mettre_a_jour():
    D = charger(); J = jours_tenus(D)
    if not J: print("aucun jour tenu terminé (premier jour tenu : 03/11/2026 UTC)"); return
    W = [poids(D, d) for d in J]; S = serie(D, W, J)
    net = sum(g - f for g, f in S); brut = sum(g for g, _ in S); fr = sum(f for _, f in S)
    j = dt.datetime.fromtimestamp(J[-1] / 1000, dt.timezone.utc).strftime("%Y-%m-%d")
    et = dict(maj_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), dernier_jour=j, jours=len(J), net=net, brut=brut, frais=fr,
              dernier_jour_net=S[-1][0] - S[-1][1], longs=[s for s, v in W[-1].items() if v > 0], shorts=[s for s, v in W[-1].items() if v < 0])
    json.dump(et, open(os.path.join(ICI, "etat.json"), "w"), indent=1)
    L = os.path.join(ICI, "journal.md"); deja = open(L).read()
    ligne = f"| {j} | {len(J)} | {100*et['dernier_jour_net']:+.2f} % | {100*net:+.2f} % | {100*brut:+.2f} % | {100*fr:.2f} % | {len(W[-1])} | {et['maj_utc']} |"
    if f"| {j} |" not in deja:
        with open(L, "a") as f: f.write(ligne + "\n")
    print(ligne)
def juger():
    D = charger(); J = jours_tenus(D)
    if not J or J[-1] != FIN - JMS: sys.exit("période pas finie (jugement unique le 03/05/2027 ou après)")
    W = [poids(D, d) for d in J]; net = sum(g - f for g, f in serie(D, W, J))
    kp = []
    for a, b in zip(W, W[1:]):
        for sg in (1, -1):
            A = {s for s, v in a.items() if v * sg > 0}; B = {s for s, v in b.items() if v * sg > 0}
            if A and B: kp.append(len(A & B) / len(B))
    kp = sum(kp) / len(kp); rng = random.Random(45); tem = []
    for _ in range(1000):
        T = []; prev = {1: set(), -1: set()}
        for d, w in zip(J, W):
            e = [s for s in U if d - JMS in D[s] and d in D[s]]; cote = {}
            n = {sg: sum(1 for v in w.values() if v * sg > 0) for sg in (1, -1)}
            for sg in (1, -1):
                g = [s for s in prev[sg] if s in e and rng.random() < kp][:n[sg]]
                pris = set(g) | (cote.get(1, set()) if sg == -1 else set())
                cote[sg] = set(g) | set(rng.sample(sorted(set(e) - pris), n[sg] - len(g)))
            T.append({**{s: 0.5 / n[1] for s in cote[1]}, **{s: -0.5 / n[-1] for s in cote[-1]}} if n[1] else {}); prev = cote
        tem.append(sum(g - f for g, f in serie(D, T, J)))
    p = sum(t >= net for t in tem) / len(tem)
    v = "GAGNE" if net > 0 and p < 0.05 else "NON DÉMONTRÉ" if net > 0 else "PERD"
    r = dict(net=net, conservation=kp, temoin_moy=sum(tem) / len(tem), p=p, verdict=v); json.dump(r, open(os.path.join(ICI, "jugement.json"), "w"), indent=1); print(r)
if __name__ == "__main__":
    juger() if sys.argv[1:] == ["juger"] else mettre_a_jour()
