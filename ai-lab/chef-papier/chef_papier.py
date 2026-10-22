"""PREREG-22 : le chef d'orchestre EN PAPIER (aucun ordre réel). Lecture seule de l'API publique Kraken Futures.
  choisir : lundi, entre 00:00 et 00:59 UTC — instantané des bougies, choix du chef + témoins T1 (moitiés de cases) et T2 (1 000 décalages), écrits et poussés sur GitHub.
  solder  : mercredi, entre 00:00 et 00:59 UTC — gain des trades ENTRÉS dans [lundi précédent 01:00, lundi 01:00) pour le chef, T1 (1 000 tirages) et T2 (1 000).
Code figé pendant le test (toute correction est journalisée). Voir ../banc-honnete/PREREG-22-chef-papier.md."""
import hashlib, itertools, json, os, pickle, random, subprocess, sys, time, urllib.request

ICI0 = os.path.dirname(os.path.abspath(__file__)); DEPOT = os.path.dirname(os.path.dirname(ICI0))
ICI = "/tmp/claude-1000/-home-tony/2c25ff3c-37a9-4b0e-a8fd-9600199a4cb4/scratchpad/chef-blanc" if os.environ.get("NB_A_BLANC") else ICI0
os.makedirs(ICI, exist_ok=True)
sys.path.insert(0, os.path.join(ICI0, "..", "banc-honnete"))
import t17_lib as L  # noqa: E402

G = [("ARB", "BNB", "INJ"), ("FET", "GRT", "ALGO"), ("CRV", "LDO", "IMX"), ("RUNE", "EGLD", "SAND"), ("MANA", "AXS", "APE"), ("DYDX", "GALA", "COMP")]
COUPLES = ((0.005, 0.005), (0.01, 0.01), (0.015, 0.01), (0.02, 0.01), (0.03, 0.015))
BLANC = os.environ.get("NB_A_BLANC")   # essai à blanc : epoch UTC simulé, rien n'est poussé, sorties dans /tmp
W = 7 * 86400; NT = 1000; HIST = 70 * W          # 70 semaines d'historique : 8 de score + jusqu'à 52 de décalage T2 + marge
DONNEES = os.path.join(ICI, "instantanes"); os.makedirs(DONNEES, exist_ok=True)


def sha(b): return hashlib.sha256(b).hexdigest()


def code_sha():
    h = hashlib.sha256()
    for f in (__file__, os.path.join(ICI0, "..", "banc-honnete", "t17_lib.py")): h.update(open(f, "rb").read())
    return h.hexdigest()


def lundi_utc(t):
    t = int(t); d = time.gmtime(t); debut_jour = t - (d.tm_hour * 3600 + d.tm_min * 60 + d.tm_sec)
    return debut_jour - d.tm_wday * 86400


def telecharge(sym, tf, a, b):
    step = {"15m": 900, "1h": 3600}[tf]; out = {}; t = a
    while t < b:
        for _ in range(8):
            try:
                d = json.load(urllib.request.urlopen(f"https://futures.kraken.com/api/charts/v1/trade/PF_{sym}USD/{tf}?from={t}&to={min(b, t + 1800 * step)}", timeout=60))["candles"]; break
            except Exception: time.sleep(3)
        else: raise RuntimeError(f"téléchargement impossible {sym} {tf}")
        for c in d: out[c["time"] // 1000] = tuple(float(c[x]) for x in ("open", "high", "low", "close", "volume"))
        t += 1800 * step; time.sleep(0.3)
    T = sorted(x for x in out if x + step <= b)       # seulement les bougies CLOSES avant b
    return T, [out[x] for x in T]


def instantane(fin):
    """Télécharge et archive toutes les bougies des 18 marchés jusqu'à `fin` ; renvoie (données, empreinte)."""
    D = {}
    for grp in G:
        for m, tf in itertools.product(grp, ("15m", "1h")): D[(m, tf)] = telecharge(m, tf, fin - HIST, fin)
    blob = pickle.dumps(D); e = sha(blob)
    open(os.path.join(DONNEES, f"{time.strftime('%Y%m%dT%H%M', time.gmtime(fin))}-{e[:12]}.pkl"), "wb").write(blob)
    return D, e


def trades(T, C, sig, tp, sl):
    L.MAXB = 24; out = []; i = 1; hi = len(T) - 1
    while i < hi - 1:
        if sig[i]:
            r, j = L.trade(C, i + 1, sig[i], tp, sl); out.append((T[i + 1], T[j], r)); i = j + 1
        else: i += 1
    return out


def bibliotheque(D, grp):
    U = []; meta = []
    for tf, m in itertools.product(("15m", "1h"), grp):
        T, C = D[(m, tf)]; S = L.signaux(C)
        for k, (ci, (tp, sl)) in itertools.product("abcd", enumerate(COUPLES)):
            U.append(trades(T, C, S[k], tp, sl)); meta.append((tf, ci))
    return U, meta


def score(tr, a, b): return sum(r for te, ts_, r in tr if a <= ts_ < b)
def nsort(tr, a, b): return sum(1 for te, ts_, r in tr if a <= ts_ < b)


def choix_chef(U, lun, d_sem=0):
    a, b = lun - (8 + d_sem) * W, lun - d_sem * W
    sc = sorted(((score(tr, a, b), s) for s, tr in enumerate(U)), reverse=True)
    return [s for v, s in sc[:10] if v > 0]


def choisir():
    now = float(BLANC) if BLANC else time.time(); lun = lundi_utc(now)
    if not (now - lun < 3600): print("hors fenêtre (lundi 00:00-00:59 UTC)"); return
    sem = time.strftime("%G-S%V", time.gmtime(lun)); f = os.path.join(ICI, f"choix-{sem}.json")
    if os.path.exists(f): print("déjà fait", sem); return
    D, e = instantane(lun); rnd = random.Random(int(lun)); res = {"semaine": sem, "lundi_utc": lun, "ecrit_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                                               "code_sha": code_sha(), "donnees_sha": e, "groupes": []}
    for grp in G:
        U, meta = bibliotheque(D, grp)
        chef = choix_chef(U, lun)
        cases = {}
        for s, mt in enumerate(meta): cases.setdefault(mt, []).append(s)
        moities = {}
        for mt, membres in cases.items():
            m2 = sorted(membres, key=lambda s: (nsort(U[s], lun - 8 * W, lun), rnd.random())); h = len(m2) // 2
            moities[str(mt)] = [m2[:h], m2[h:]]
        t2 = [choix_chef(U, lun, rnd.randint(9, 52)) for _ in range(NT)]
        res["groupes"].append({"marches": grp, "chef": chef, "meta": meta, "moities_T1": moities, "choix_T2": t2})
    open(f, "w").write(json.dumps(res)); pousse(f, f"chef-papier : choix {sem} (avant lundi 01:00 UTC)")
    print("choix écrits et poussés", sem)


def solder():
    now = float(BLANC) if BLANC else time.time(); lun = lundi_utc(now) + 2 * 86400      # mercredi 00:00 UTC
    if not (0 <= now - lun < 3600): print("hors fenêtre (mercredi 00:00-00:59 UTC)"); return
    lun_prec = lundi_utc(now) - W; sem = time.strftime("%G-S%V", time.gmtime(lun_prec)); fc = os.path.join(ICI, f"choix-{sem}.json")
    jour = os.path.join(ICI, "journal.jsonl")
    if os.path.exists(jour) and any(json.loads(l)["semaine"] == sem for l in open(jour)): print("déjà soldé", sem); return
    if not os.path.exists(fc):
        open(jour, "a").write(json.dumps({"semaine": sem, "valide": False, "raison": "pas de choix poussé"}) + "\n"); pousse(jour, f"chef-papier : semaine {sem} invalide"); return
    ch = json.load(open(fc)); D, e = instantane(lun); a, b = lun_prec + 3600, lun_prec + W + 3600; rnd = random.Random(int(lun))
    ligne = {"semaine": sem, "valide": True, "solde_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "donnees_sha": e, "code_sha": code_sha(), "groupes": []}
    for g in ch["groupes"]:
        U, meta = bibliotheque(D, tuple(g["marches"]))
        gain_s = [sum(r for te, ts_, r in tr if a <= te < b) for tr in U]
        ntr_s = [sum(1 for te, ts_, r in tr if a <= te < b) for tr in U]
        def g_(liste): return (sum(gain_s[s] for s in liste) / len(liste)) if liste else 0.0
        chef = g["chef"]; t1 = []
        for _ in range(NT):
            pris = set(); new = []
            for s in chef:
                mt = str(tuple(meta[s])); bas, haut = g["moities_T1"][mt]; part = bas if s in bas else haut
                dispo = [x for x in part if x not in pris] or [x for x in bas + haut if x not in pris]
                x = rnd.choice(dispo); pris.add(x); new.append(x)
            t1.append(g_(new))
        ligne["groupes"].append({"marches": g["marches"], "chef": g_(chef), "trades_chef": sum(ntr_s[s] for s in chef),
                                 "T1": t1, "T2": [g_(c) for c in g["choix_T2"]]})
    open(jour, "a").write(json.dumps(ligne) + "\n"); pousse(jour, f"chef-papier : solde {sem}")
    print("soldé", sem, [round(100 * x["chef"], 2) for x in ligne["groupes"]])


def pousse(f, msg):
    if BLANC: print("[à blanc] non poussé :", msg); return
    rel = os.path.relpath(f, DEPOT)
    subprocess.run(["git", "-C", DEPOT, "add", rel], check=True)
    subprocess.run(["git", "-C", DEPOT, "commit", "-q", "-m", msg + "\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"], check=True)
    for _ in range(5):
        if subprocess.run(["git", "-C", DEPOT, "push", "-q"]).returncode == 0: return
        time.sleep(60)
    open(os.path.join(ICI, "ALERTE.txt"), "a").write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} push impossible : {msg}\n")


if __name__ == "__main__":
    {"choisir": choisir, "solder": solder}[sys.argv[1]]()
