"""PREREG-35 : test papier EN AVANT de la règle d'inversion journalière de PREREG-32 (réglage figé SL 15 % / +5 % / trailing 3 %).
Lecture de prix PUBLICS seulement (Binance USDT-M, /fapi/v1/klines, sans clé, sans compte). Aucun ordre.
Sans état : à chaque passage, tout est recalculé depuis l'ouverture du 01/11/2026 00:00 UTC sur les jours UTC TERMINÉS.
  python3 papier.py          -> met à jour donnees/*.json, journal.md (une ligne par jour terminé), etat.json
  python3 papier.py juger    -> verdict (seulement à partir du 01/05/2027 00:00 UTC, fin de la période)
Bibliothèque standard seulement (cron sans venv). La simulation `chaine` est la transcription ligne à ligne de t32.py (mode 0 et 2)."""
import datetime as dt, json, os, random, sys, time, urllib.request

PANIER = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "BNBUSDT", "DOGEUSDT", "ADAUSDT", "LINKUSDT", "AVAXUSDT", "LTCUSDT"]
S, A, T = 0.15, 0.05, 0.03          # SL fixe, activation du trailing, écart du trailing (figés par PREREG-32)
TK = 0.0005                         # taker 0,05 % par côté
JMS = 86_400_000
DEBUT = int(dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc).timestamp() * 1000)
FIN = int(dt.datetime(2027, 5, 1, tzinfo=dt.timezone.utc).timestamp() * 1000)   # exclu : dernier jour jugé = 30/04/2027
ICI = os.path.dirname(os.path.abspath(__file__))
DON = os.path.join(ICI, "donnees")


def klines(sym, t0):
    """Bougies journalières terminées [t0, min(maintenant, FIN)), format [ouverture_ms, o, h, l, c]."""
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={sym}&interval=1d&startTime={t0}&limit=500"
    for essai in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "nb-papier"}), timeout=20) as r:
                k = json.load(r)
            break
        except Exception:
            if essai == 3: raise
            time.sleep(5 * (essai + 1))
    now = int(time.time() * 1000)
    return [[int(x[0]), float(x[1]), float(x[2]), float(x[3]), float(x[4])] for x in k if int(x[6]) < now and int(x[0]) < FIN]


def chaine(o, h, l, c, mode, pl=0.5, rng=None, fin_periode=False):
    """mode 0 : inversion après perte (départ long) ; 2 : sens au hasard P(long)=pl. Jour ambigu = SL d'abord.
    Retourne (trades fermés [(net, sens, i_entree, i_sortie)], position ouverte ou None).
    fin_periode=True : la position encore ouverte au dernier jour sort à la clôture (comme t32.py) ; sinon elle reste ouverte."""
    Tn = len(o); i = 0; sv = 1.0; out = []; ouverte = None
    while i < Tn:
        sens = sv if mode == 0 else (1.0 if rng.random() < pl else -1.0)
        e = o[i]; i0 = i; sl = e * (1 - S * sens); actif = False; pic = 0.0
        while True:
            px = -1.0
            hi = h[i] if sens > 0 else l[i]; lo = l[i] if sens > 0 else h[i]; stop = sl
            if actif:
                ts = pic * (1 - T * sens); stop = max(sl, ts) if sens > 0 else min(sl, ts)
            if (lo - stop) * sens <= 0: px = min(o[i], stop) if sens > 0 else max(o[i], stop)
            elif actif: pic = max(pic, hi) if sens > 0 else min(pic, hi)
            elif (hi - e * (1 + A * sens)) * sens >= 0: actif = True; pic = hi
            if px < 0 and i == Tn - 1:
                if fin_periode: px = c[i]
                else:
                    ouverte = dict(sens=sens, entree=e, i_entree=i0, stop=stop, actif=actif, pic=pic,
                                   latent=sens * (c[i] / e - 1) - TK - TK * c[i] / e)
                    return out, ouverte
            if px >= 0:
                r = sens * (px / e - 1) - TK - TK * px / e
                out.append((r, sens, i0, i))
                if mode == 0 and r <= 0: sv = -sv
                break
            i += 1
        i += 1
    return out, ouverte


def charger(maj=True):
    os.makedirs(DON, exist_ok=True); D = {}
    for s in PANIER:
        f = os.path.join(DON, f"{s}.json")
        k = json.load(open(f)) if os.path.exists(f) else []
        if maj:
            t0 = k[-1][0] + JMS if k else DEBUT
            nv = klines(s, t0) if t0 < FIN else []
            k += [x for x in nv if x[0] >= t0]
            json.dump(k, open(f, "w"))
        assert all(b[0] - a[0] == JMS for a, b in zip(k, k[1:])), f"trou dans {s}"
        assert not k or k[0][0] == DEBUT, f"{s} ne commence pas au 01/11/2026"
        D[s] = k
    return D


def col(k):
    return [x[1] for x in k], [x[2] for x in k], [x[3] for x in k], [x[4] for x in k]


def jour(ms):
    return dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc).strftime("%Y-%m-%d")


def mettre_a_jour():
    D = charger(); fin = all(k and k[-1][0] == FIN - JMS for k in D.values())
    n = min(len(k) for k in D.values())
    if n == 0: print("aucun jour terminé depuis le 01/11/2026 00:00 UTC"); return
    etat = {"maj_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "dernier_jour": jour(D[PANIER[0]][n - 1][0]),
            "jours": n, "pieces": {}}
    tot_ferme = tot_latent = 0.0
    for s in PANIER:
        o, h, l, c = col(D[s][:n]); tr, ov = chaine(o, h, l, c, 0, fin_periode=fin)
        ferme = sum(t[0] for t in tr); lat = ov["latent"] if ov else 0.0
        tot_ferme += ferme; tot_latent += lat
        etat["pieces"][s] = {"trades": len(tr), "gagnants": sum(t[0] > 0 for t in tr), "net_ferme": round(ferme, 6),
                             "latent": round(lat, 6), "position": None if not ov else
                             {"sens": "long" if ov["sens"] > 0 else "short", "entree": ov["entree"], "depuis": jour(D[s][ov["i_entree"]][0]),
                              "stop": round(ov["stop"], 8), "trailing_actif": ov["actif"]}}
    m = len(PANIER); etat["net_panier_ferme"] = round(tot_ferme / m, 6); etat["net_panier_avec_latent"] = round((tot_ferme + tot_latent) / m, 6)
    bh = sum(D[s][n - 1][4] / D[s][0][1] - 1 - TK - TK * D[s][n - 1][4] / D[s][0][1] for s in PANIER) / m
    etat["acheter_garder_panier"] = round(bh, 6)
    json.dump(etat, open(os.path.join(ICI, "etat.json"), "w"), indent=1, ensure_ascii=False)
    J = os.path.join(ICI, "journal.md")
    deja = open(J).read() if os.path.exists(J) else ""
    ligne = (f"| {etat['dernier_jour']} | {n} | {etat['net_panier_ferme']*100:+.2f} % | {etat['net_panier_avec_latent']*100:+.2f} % | "
             f"{sum(p['trades'] for p in etat['pieces'].values())} | "
             + " ".join(f"{s[:-4]}:{'L' if p['position'] and p['position']['sens']=='long' else 'S' if p['position'] else '-'}" for s, p in etat["pieces"].items())
             + f" | {bh*100:+.2f} % | {etat['maj_utc']} |")
    if f"| {etat['dernier_jour']} |" not in deja:
        with open(J, "a") as f: f.write(ligne + "\n")
    print(ligne)


def juger():
    D = charger(maj=True)
    if not all(k and k[-1][0] == FIN - JMS for k in D.values()):
        sys.exit("période pas finie (jugement unique le 01/05/2027 ou après) : rien à juger")
    net = {}; pl = {}
    for s in PANIER:
        o, h, l, c = col(D[s]); tr, _ = chaine(o, h, l, c, 0, fin_periode=True)
        net[s] = sum(t[0] for t in tr); pl[s] = (sum(t[1] > 0 for t in tr) / len(tr)) if tr else 0.5
    nr = sum(net.values()) / len(PANIER)
    rng = random.Random(35); tem = []
    for _ in range(1000):
        x = 0.0
        for s in PANIER:
            o, h, l, c = col(D[s]); tr, _ = chaine(o, h, l, c, 2, pl=pl[s], rng=rng, fin_periode=True); x += sum(t[0] for t in tr)
        tem.append(x / len(PANIER))
    p = sum(t >= nr for t in tem) / len(tem)
    v = "GAGNE" if nr > 0 and p < 0.05 else "NON DÉMONTRÉ" if nr > 0 else "PERD"
    moy = sum(tem) / len(tem); et = (sum((t - moy) ** 2 for t in tem) / len(tem)) ** 0.5
    r = {"net_panier": nr, "par_piece": net, "part_longs": pl, "temoin_moy": moy, "temoin_et": et, "p": p, "verdict": v}
    json.dump(r, open(os.path.join(ICI, "jugement.json"), "w"), indent=1)
    print(json.dumps(r, indent=1))


if __name__ == "__main__":
    juger() if sys.argv[1:] == ["juger"] else mettre_a_jour()
