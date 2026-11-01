"""PREREG-47 : short des nouvelles cotations CRYPTO de Binance, test papier EN AVANT (cotations du 02/11/2026 au 28/02/2027, tenues 90 jours).
Prix publics seulement (fapi exchangeInfo, klines 1d, fundingRate ; sans clé, sans compte). Aucun ordre.
  python3 cotations.py        -> registre.json (cotations, pools témoins), donnees/, journal.md, etat.json
  python3 cotations.py juger  -> verdict (à partir du 01/06/2027)"""
import datetime as dt, json, os, random, statistics as st, sys, time, urllib.request, urllib.error
ICI = os.path.dirname(os.path.abspath(__file__)); DON = os.path.join(ICI, "donnees"); J = 86_400_000; TK = 0.0005; N = 90
ut = lambda y, m, d: int(dt.datetime(y, m, d, tzinfo=dt.timezone.utc).timestamp() * 1000)
DEBUT, FIN_COT, JUGE = ut(2026, 11, 2), ut(2027, 3, 1), ut(2027, 6, 1)
REG = os.path.join(ICI, "registre.json")
def get(u):
    for e in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "nb-papier"}), timeout=30) as r: return json.load(r)
        except urllib.error.HTTPError as x:
            if x.code == 400: return None
            if e == 3: raise
        except Exception:
            if e == 3: raise
        time.sleep(5 * (e + 1))
def jour(ms): return dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc).strftime("%Y-%m-%d")
def klines(s, t0):
    out = []; now = int(time.time() * 1000)
    while True:
        k = get(f"https://fapi.binance.com/fapi/v1/klines?symbol={s}&interval=1d&startTime={t0}&limit=500")
        if not k: return out
        out += [[int(x[0]), float(x[1]), float(x[4])] for x in k if int(x[6]) < now]
        if len(k) < 500: return out
        t0 = int(k[-1][0]) + J
def financement(s, t0):
    out = []
    while True:
        r = get(f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={s}&startTime={t0}&limit=1000"); time.sleep(0.7)
        if not r: return out
        out += [[x["fundingTime"], float(x["fundingRate"])] for x in r]
        if len(r) < 1000: return out
        t0 = r[-1]["fundingTime"] + 1
def coin_perps(ei): return [s for s in ei["symbols"] if s["contractType"] == "PERPETUAL" and s["quoteAsset"] == "USDT" and s.get("underlyingType") == "COIN"]
def trade(k, f, e):
    """k : bougies [t, o, c] depuis e ; f : financement. Retourne (net, ferme, jours)."""
    k = [x for x in k if x[0] >= e][:N]
    if not k or k[0][0] != e: return None
    x = k[-1]; brut = -(x[2] / k[0][1] - 1); fin = sum(r for t, r in f if e <= t < x[0] + J)
    return max(-1.0, brut + fin - 2 * TK), len(k) == N, len(k)
def mettre_a_jour():
    os.makedirs(DON, exist_ok=True); R = json.load(open(REG)) if os.path.exists(REG) else {"cotations": {}, "pools": {}, "statuts": {}}
    ei = get("https://fapi.binance.com/fapi/v1/exchangeInfo"); now = int(time.time() * 1000)
    for s in coin_perps(ei):
        ob = int(s["onboardDate"]); sy = s["symbol"]; R["statuts"][sy] = s["status"]
        if DEBUT <= ob < FIN_COT and sy not in R["cotations"]:
            e = (ob // J) * J + J
            R["cotations"][sy] = {"onboard": ob, "entree": e, "vu_le": jour(now)}
            # pool témoin figé à la découverte : pièces COIN cotées depuis plus de 365 jours avant l'entrée, en cours de cotation
            R["pools"][str(e)] = R["pools"].get(str(e)) or sorted(x["symbol"] for x in coin_perps(ei) if int(x["onboardDate"]) <= e - 365 * J and x["status"] == "TRADING")
    json.dump(R, open(REG, "w"), indent=1)
    lignes = []; ouverts = fermes = 0; nets_f, nets_o = [], []
    for sy, c in sorted(R["cotations"].items(), key=lambda x: x[1]["entree"]):
        e = c["entree"]
        if e + J > now: continue                                 # 2e bougie pas encore terminée
        fk = os.path.join(DON, f"{sy}.json"); d = json.load(open(fk)) if os.path.exists(fk) else {"k": [], "f": []}
        if len([x for x in d["k"] if x[0] >= e]) < N:
            t0 = d["k"][-1][0] + J if d["k"] else e; d["k"] += [x for x in klines(sy, t0) if x[0] >= t0]
            t1 = d["f"][-1][0] + 1 if d["f"] else e; d["f"] += financement(sy, t1)
            json.dump(d, open(fk, "w"))
        t = trade(d["k"], d["f"], e)
        if not t: continue
        retire = R["statuts"].get(sy) != "TRADING" and d["k"] and d["k"][-1][0] < now - 3 * J
        if t[1] or retire: fermes += 1; nets_f.append(t[0])
        else: ouverts += 1; nets_o.append(t[0])
    et = dict(maj_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), cotations_vues=len(R["cotations"]), ouverts=ouverts, fermes=fermes,
              moy_fermes=st.mean(nets_f) if nets_f else None, moy_ouverts_latent=st.mean(nets_o) if nets_o else None)
    json.dump(et, open(os.path.join(ICI, "etat.json"), "w"), indent=1)
    j = jour(now - J); L = os.path.join(ICI, "journal.md"); deja = open(L).read()
    f = lambda v: "—" if v is None else f"{100*v:+.1f} %"
    ligne = f"| {j} | {len(R['cotations'])} | {ouverts} | {fermes} | {f(et['moy_fermes'])} | {f(et['moy_ouverts_latent'])} | {et['maj_utc']} |"
    if f"| {j} |" not in deja:
        with open(L, "a") as fh: fh.write(ligne + "\n")
    print(ligne)
def juger():
    if time.time() * 1000 < JUGE: sys.exit("jugement unique le 01/06/2027 ou après")
    R = json.load(open(REG)); T = []
    for sy, c in R["cotations"].items():
        fk = os.path.join(DON, f"{sy}.json")
        if not os.path.exists(fk): continue
        d = json.load(open(fk)); t = trade(d["k"], d["f"], c["entree"])
        if t: T.append((c["entree"], t[0]))
    if len(T) < 20: sys.exit(f"NON ÉVALUABLE : {len(T)} trades (< 20)")
    m = st.mean(t for _, t in T); rng = random.Random(47); cache = {}; tem = []
    def temoin(s, e):
        if (s, e) not in cache:
            k = klines(s, e); cache[(s, e)] = trade(k, financement(s, e), e) if k else None
        return cache[(s, e)]
    for _ in range(1000):
        r = []
        for e, _ in T:
            pool = R["pools"][str(e)]; t = None; essais = 0
            while t is None and essais < 50: t = temoin(rng.choice(pool), e); essais += 1
            if t: r.append(t[0])
        tem.append(st.mean(r))
    p = sum(x >= m for x in tem) / len(tem)
    v = "GAGNE" if m > 0 and p < 0.05 else "NON DÉMONTRÉ" if m > 0 else "PERD"
    res = dict(trades=len(T), moyenne=m, mediane=st.median(t for _, t in T), temoin_moy=st.mean(tem), p=p, verdict=v)
    json.dump(res, open(os.path.join(ICI, "jugement.json"), "w"), indent=1); print(res)
if __name__ == "__main__":
    juger() if sys.argv[1:] == ["juger"] else mettre_a_jour()
