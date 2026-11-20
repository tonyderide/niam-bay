#!/usr/bin/env python3
"""Le bureau : une idée de trading décrite en JSON -> verdict honnête, sur crypto (Kraken) ou actions/ETF (Yahoo).

Il réutilise le moteur du banc (../banc-honnete/banc.py : signaux sur bougie close, entrée à l'ouverture suivante,
frais 0,05 % par côté, témoin de hasard) et ajoute : les actions en journalier, le verrou de pré-enregistrement
(l'idée doit être commitée et inchangée avant tout calcul), un registre, et le suivi sur papier des idées qui passent.
Aucun ordre réel, jamais.

Idée (JSON) :
{"nom": "...", "texte_tony": "la phrase d'origine", "tf": "1d", "marches": ["QQQ", "SPY", "IWM"],
 "long": "baisse_suite(3)", "short": null, "sortie": {"max_bougies": 5}, "notes": "choix de traduction",
 "equite": "ce qui pourrait fausser le test, dans un sens ou dans l'autre"}
- marches : au moins 3, tous crypto (BTC, ETH, SOL… = perpétuels Kraken) ou tous actions/ETF/indices Yahoo (QQQ, SPY, ^NDX, AAPL…).
  Actions : "tf" = "1d" seulement, cours ajustés des dividendes. "classe": "actions" ou "crypto" force la classe si un nom est ambigu.
- long / short / sortie : le vocabulaire de banc.py (ema, sma, rsi, atr, macd, bb_upper, adx, highest, shift, cross_up…), plus :
  baisse_suite(n), hausse_suite(n) : n clôtures de suite en baisse / hausse ; variation(n) : rendement sur n bougies ;
  ecart_ouverture() : ouverture / clôture précédente − 1 ; jour_semaine() (0 = lundi), jour_mois(), mois(), heure() ; egal(serie, valeur).
Verdict, sur deux périodes séparées (crypto : 2024-2025 et 2026 ; actions : 2005-2015 et 2016-2026) :
  GAGNE = dans CHAQUE période : somme > 0, au moins 60 % des marchés positifs, somme au-dessus du 95e centile de 500 tirages
  au hasard (mêmes nombres de trades, mêmes sorties, mêmes sens possibles), et au moins 30 trades.
  NON ÉVALUABLE = moins de 30 trades ou moins de 3 marchés dans une période. PERD = somme totale <= 0. NON DÉMONTRÉ = le reste.
Usage : bureau verifier idee.json | juger idee.json | papier | liste | auto-test
"""
import datetime, json, math, os, pickle, random, re, subprocess, sys, time, urllib.request

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.abspath(os.path.join(ICI, "..", ".."))
sys.path.insert(0, os.path.join(ICI, "..", "banc-honnete"))
import banc  # noqa: E402

TIRAGES = 500
FIN_ACTIONS = "2026-11-01"  # fin figée : le même calcul redonne le même résultat
PERIODES_ACTIONS = (("2005-2015", banc.ts("2005-01-01"), banc.ts("2016-01-01")), ("2016-2026", banc.ts("2016-01-01"), banc.ts(FIN_ACTIONS)))
REGISTRE = os.path.join(ICI, "REGISTRE.md")
PAPIER = os.path.join(ICI, "papier")
fr = lambda x, nd=1: f"{x:+.{nd}f}".replace(".", ",")

_ns_banc = banc.namespace


def namespace(T, C):
    """Le vocabulaire du banc, plus quelques mots simples. Tout est calculé sur des bougies closes (aucun regard vers l'avenir)."""
    ns = _ns_banc(T, C); S = banc.S; c, o, n = ns["close"], ns["open"], len(C)
    def _suite(sens):
        def f(k):
            r = S([False] * n); run = 0
            for i in range(1, n):
                run = run + 1 if (c[i] - c[i - 1]) * sens > 0 else 0; r[i] = run >= k
            return r
        return f
    gm = [time.gmtime(t) for t in T]
    ns.update(baisse_suite=_suite(-1), hausse_suite=_suite(1),
              variation=lambda k=1: S([0.0] * k + [c[i] / c[i - k] - 1 for i in range(k, n)]),
              ecart_ouverture=lambda: S([0.0] + [o[i] / c[i - 1] - 1 for i in range(1, n)]),
              jour_semaine=lambda: S(g.tm_wday for g in gm), jour_mois=lambda: S(g.tm_mday for g in gm),
              mois=lambda: S(g.tm_mon for g in gm), heure=lambda: S(g.tm_hour for g in gm),
              egal=lambda s, v: S(x == v for x in s))
    return ns


banc.namespace = namespace


# ---------- données ----------
def classe_de(spec):
    if spec.get("classe") in ("crypto", "actions"): return spec["classe"]
    cr = [m in banc.SYM for m in spec["marches"]]
    if all(cr): return "crypto"
    if not any(cr): return "actions"
    sys.exit("refus : mélange de crypto et d'actions dans la même idée (ou nom ambigu : préciser \"classe\")")


def _df_vers_bougies(df):
    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    return [int(x.timestamp()) for x in df.index], [tuple(float(v) for v in r) for r in zip(df.Open, df.High, df.Low, df.Close, df.Volume)]


def actions(ticker):
    f = f"{banc.CACHE}/yf_{re.sub(r'[^A-Za-z0-9.-]', '_', ticker)}_1d_{FIN_ACTIONS}.pkl"
    if os.path.exists(f): return pickle.load(open(f, "rb"))
    import yfinance as yf
    T, C = _df_vers_bougies(yf.Ticker(ticker).history(start="1999-01-01", end=FIN_ACTIONS, interval="1d", auto_adjust=True))
    if len(T) < 600: sys.exit(f"refus : pas assez de données pour {ticker} ({len(T)} jours)")
    os.makedirs(banc.CACHE, exist_ok=True); pickle.dump((T, C), open(f, "wb")); return T, C


def donnees(spec):
    if classe_de(spec) == "crypto":
        return {m: banc.candles(banc.SYM.get(m, f"PF_{m}USD"), spec["tf"]) for m in spec["marches"]}, banc.PERIODES
    return {m: actions(m) for m in spec["marches"]}, PERIODES_ACTIONS


def donnees_fraiches(spec, depuis):
    """Pour le papier : bougies récentes, sans cache, la bougie en cours retirée."""
    now = int(time.time()); out = {}
    for m in spec["marches"]:
        if classe_de(spec) == "crypto":
            step = banc.STEP[spec["tf"]]; sym = banc.SYM.get(m, f"PF_{m}USD"); d = {}; t = depuis - 700 * step
            while t < now:
                for _ in range(5):
                    try:
                        cs = json.load(urllib.request.urlopen(f"https://futures.kraken.com/api/charts/v1/trade/{sym}/{spec['tf']}?from={t}&to={min(now, t + 1800 * step)}", timeout=60))["candles"]; break
                    except Exception: cs = []; time.sleep(3)
                for c in cs: d[c["time"] // 1000] = tuple(float(c[x]) for x in ("open", "high", "low", "close", "volume"))
                t += 1800 * step; time.sleep(0.2)
            T = sorted(x for x in d if x + step <= now); out[m] = (T, [d[x] for x in T])
        else:
            import yfinance as yf
            T, C = _df_vers_bougies(yf.Ticker(m).history(period="5y", interval="1d", auto_adjust=True))
            k = len(T) - 1 if T and time.gmtime(T[-1])[:3] == time.gmtime(now)[:3] else len(T)  # la séance du jour n'est pas finie
            out[m] = (T[:k], C[:k])
    return out


# ---------- calcul ----------
def hasard(C, lo, hi, trades, so, toujours, rnd, sens):
    if toujours or not so.get("inverse"): return banc.hasard(C, lo, hi, trades, so, toujours, rnd, sens)
    tot = 0  # sortie sur signal inverse : le témoin garde la même durée de tenue, sinon il courrait jusqu'au stop
    for _, dur in trades:
        so2 = dict(so); so2["max_bougies"] = max(1, min(dur, so.get("max_bougies") or dur))
        tot += banc.sortir(C, rnd.randrange(lo + 1, hi - 1), rnd.choice(sens), so2, None)[0]
    return tot


def evaluer(spec, data, periodes):
    """Cœur sans effet de bord : renvoie (verdict, raisons, détail par période)."""
    sens = tuple(x for x, e in ((1, spec.get("long")), (-1, spec.get("short"))) if e); det = []
    for per, a, b in periodes:
        som = 0.0; pos = N = nm = 0; R = [0.0] * TIRAGES; par = {}; pire = 0.0; bh = []; inv = []
        for m, (T, C) in data.items():
            if sum(1 for t in T if a <= t < b) < 200: par[m] = None; continue
            tr, C2, lo, hi, so, tj = banc.tester(spec, C, T, a, b); r = sum(x for x, _ in tr)
            som += r; pos += r > 0; N += len(tr); nm += 1; d0 = max(lo, 250)
            for k in range(TIRAGES): R[k] += hasard(C2, lo, hi, tr, so, tj, random.Random(k), sens)
            bh.append(C2[hi - 1][3] / C2[d0][0] - 1 if hi - 1 > d0 else 0.0); inv.append(min(1.0, sum(x for _, x in tr) / max(1, hi - d0)))
            pire = min([pire] + [x for x, _ in tr])
            par[m] = {"trades": len(tr), "somme": r, "gagnants": sum(x > 0 for x, _ in tr) / max(1, len(tr))}
        R.sort(); besoin = max(2, math.ceil(0.6 * nm))
        det.append({"periode": per, "somme": som, "trades": N, "marches": nm, "positifs": pos, "besoin": besoin, "mediane": R[TIRAGES // 2],
                    "p95": R[int(TIRAGES * 0.95)], "rang": sum(x < som for x in R) * 100 / TIRAGES, "pire_trade": pire,
                    "achat_conservation": sum(bh) / max(1, len(bh)), "temps_investi": sum(inv) / max(1, len(inv)), "par_marche": par})
    raisons = []
    for d in det:
        if d["marches"] < 3: raisons.append(f"{d['periode']} : {d['marches']} marché(s) seulement")
        if d["trades"] < 30: raisons.append(f"{d['periode']} : {d['trades']} trades (30 requis)")
    if raisons: return "NON ÉVALUABLE", raisons, det
    for d in det:
        if d["somme"] <= 0: raisons.append(f"{d['periode']} : somme négative")
        if d["positifs"] < d["besoin"]: raisons.append(f"{d['periode']} : {d['positifs']}/{d['marches']} marchés positifs ({d['besoin']} requis)")
        if d["somme"] <= d["p95"]: raisons.append(f"{d['periode']} : pas au-dessus du hasard ({d['rang']:.0f}e centile, 95e requis)")
    if not raisons: return "GAGNE", ["toutes les conditions sont remplies sur les deux périodes"], det
    return ("PERD" if sum(d["somme"] for d in det) <= 0 else "NON DÉMONTRÉ"), raisons, det


def rapport(spec, verdict, raisons, det, engage):
    L = [f"# {spec['nom']}", ""]
    if spec.get("texte_tony"): L.append(f"Idée de Tony : « {spec['texte_tony']} »")
    L += [f"Traduction : long = `{spec.get('long')}` · short = `{spec.get('short')}` · sortie = `{json.dumps(spec.get('sortie', {}), ensure_ascii=False)}`",
          f"Marchés : {', '.join(spec['marches'])} ({classe_de(spec)}) · bougies {spec['tf']} · frais 0,05 % par côté · pré-enregistrée : {engage}", "",
          "| Période | Trades | Somme | Hasard médiane | Hasard 95e | Rang | Marchés > 0 | Achat-conservation | Temps investi | Pire trade |", "|---|---|---|---|---|---|---|---|---|---|"]
    for d in det:
        L.append(f"| {d['periode']} | {d['trades']} | {fr(d['somme'] * 100)} % | {fr(d['mediane'] * 100)} % | {fr(d['p95'] * 100)} % | {d['rang']:.0f}e | "
                 f"{d['positifs']}/{d['marches']} | {fr(d['achat_conservation'] * 100)} % | {d['temps_investi'] * 100:.0f} % | {fr(d['pire_trade'] * 100)} % |")
    L.append("")
    for d in det:
        L.append(f"{d['periode']} par marché : " + " · ".join(f"{m} non coté" if p is None else f"{m} {p['trades']} trades {fr(p['somme'] * 100)} % ({p['gagnants']:.0%} gagnants)" for m, p in d["par_marche"].items()))
    L += ["", f"VERDICT : {verdict} — " + " ; ".join(raisons), "",
          "Lecture : « somme » = addition des rendements nets de chaque trade, mise égale, tous marchés. « Achat-conservation » = acheter au début et ne rien faire (moyenne des marchés), pour information.",
          "Réserves : " + ("financement des perpétuels non compté. " if classe_de(spec) == "crypto" else "cours ajustés des dividendes" + (" ; coût d'emprunt des ventes à découvert non compté. " if spec.get("short") else ". "))
          + "Un GAGNE ici n'autorise aucun ordre réel : il ouvre seulement un essai sur papier."]
    if spec.get("equite"): L.append(f"Relecture d'équité (écrite avant le calcul) : {spec['equite']}")
    return "\n".join(L)


# ---------- garde-fous ----------
def charger(path):
    spec = json.load(open(path))
    for k in ("nom", "tf", "marches", "sortie"):
        if k not in spec: sys.exit(f"refus : champ « {k} » manquant")
    if not isinstance(spec["marches"], list) or len(spec["marches"]) < 3: sys.exit("refus : au moins 3 marchés comparables (un seul marché ne distingue pas la chance)")
    if not (spec.get("long") or spec.get("short")): sys.exit("refus : ni « long » ni « short »")
    cl = classe_de(spec)
    if cl == "actions" and spec["tf"] != "1d": sys.exit("refus : actions en journalier seulement (\"tf\": \"1d\")")
    if cl == "crypto" and spec["tf"] not in banc.STEP: sys.exit(f"refus : tf inconnu ({spec['tf']})")
    exprs = [spec.get("long"), spec.get("short"), spec["sortie"].get("si_long"), spec["sortie"].get("si_short")]
    if any(e and ("__" in e or "import" in e) for e in exprs): sys.exit("refus : expression interdite")
    return spec


def synthetique(graine, n=6000, effet=0.0, t0=None, pas=86400):
    """Marche au hasard avec une légère hausse ; « effet » ajoute un gain le lendemain de 3 clôtures en baisse (pour l'auto-test)."""
    rnd = random.Random(graine); T = []; C = []; p = 100.0; run = 0; t0 = t0 or banc.ts("2005-01-03")
    for i in range(n):
        o = p * (1 + rnd.gauss(0, 0.002)); c = o * (1 + rnd.gauss(0.0003 + (effet if run >= 3 else 0), 0.012))
        C.append((o, max(o, c) * (1 + abs(rnd.gauss(0, 0.004))), min(o, c) * (1 - abs(rnd.gauss(0, 0.004))), c, 1e6)); T.append(t0 + i * pas)
        run = run + 1 if c < p else 0; p = c
    return T, C


def verifier(spec):
    """Vérifie que les expressions se calculent, sur de fausses bougies : ne regarde aucune donnée réelle."""
    T, C = synthetique(7, 900); a, b = T[300], T[-1]
    tr = banc.tester(spec, C, T, a, b)[0]
    return f"OK : expressions valides ({len(tr)} signaux sur de fausses bougies, sans valeur) · classe {classe_de(spec)} · {len(spec['marches'])} marchés · {spec['tf']}"


def git(*a):
    return subprocess.run(["git", "-C", RACINE, *a], capture_output=True, text=True)


def engagement(path):
    rel = os.path.relpath(os.path.abspath(path), RACINE)
    if git("ls-files", "--error-unmatch", rel).returncode: sys.exit("refus : l'idée n'est pas commitée. Pré-enregistrer d'abord (git add + git commit), calculer ensuite.")
    if git("diff", "--quiet", "HEAD", "--", rel).returncode: sys.exit("refus : l'idée a été modifiée depuis son commit.")
    return git("log", "-1", "--format=commit %h du %cd", "--date=format:%d/%m/%Y %H:%M", "--", rel).stdout.strip()


# ---------- commandes ----------
def cmd_juger(path):
    spec = charger(path); print(verifier(spec)); eng = engagement(path); base = os.path.abspath(path)[:-5]
    if os.path.exists(base + ".resultat.md") and "--rejouer" not in sys.argv:
        print("(déjà jugée : résultat existant)\n" + open(base + ".resultat.md").read()); return
    data, periodes = donnees(spec); verdict, raisons, det = evaluer(spec, data, periodes); txt = rapport(spec, verdict, raisons, det, eng)
    open(base + ".resultat.md", "w").write(txt + "\n"); json.dump({"verdict": verdict, "raisons": raisons, "periodes": det}, open(base + ".resultat.json", "w"), ensure_ascii=False, indent=1)
    if not os.path.exists(REGISTRE):
        open(REGISTRE, "w").write("# Registre du bureau\n\nChaque idée jugée, dans l'ordre. Plus on teste d'idées, plus un GAGNE peut venir de la chance : c'est pour cela qu'un GAGNE passe d'abord sur papier.\n\n| Date | Idée | Classe | Verdict | Sommes par période | Fichier |\n|---|---|---|---|---|---|\n")
    if os.path.basename(base) not in open(REGISTRE).read():
        open(REGISTRE, "a").write(f"| {datetime.date.today():%d/%m/%Y} | {spec['nom']} | {classe_de(spec)} | **{verdict}** | {' / '.join(fr(d['somme'] * 100) + ' %' for d in det)} | [{os.path.basename(base)}](idees/{os.path.basename(base)}.resultat.md) |\n")
    if verdict == "GAGNE":
        os.makedirs(PAPIER, exist_ok=True); f = os.path.join(PAPIER, os.path.basename(base) + ".json")
        if not os.path.exists(f): json.dump({"idee": os.path.relpath(os.path.abspath(path), ICI), "depuis": int(time.time())}, open(f, "w"))
        txt += f"\nEssai papier ouvert : {os.path.relpath(f, RACINE)}"
    print(txt)


def cmd_papier():
    """Rejoue chaque idée GAGNE sur les seules bougies postérieures à son inscription. Sans effet sur aucun compte."""
    if not os.path.isdir(PAPIER): return
    for f in sorted(x for x in os.listdir(PAPIER) if x.endswith(".json")):
        e = json.load(open(os.path.join(PAPIER, f))); spec = charger(os.path.join(ICI, e["idee"])); depuis = e["depuis"]; now = int(time.time())
        L = [f"# Papier : {spec['nom']}", "", f"Inscrite le {time.strftime('%d/%m/%Y %H:%M', time.localtime(depuis))}. Seules les bougies d'après comptent.",
             "Règle fixée d'avance : jugement à 30 trades ou à 90 jours. Somme > 0 et au moins 60 % des marchés positifs : on en parle à Tony. Sinon abandon. Jamais d'ordre réel sans son accord.", ""]
        som = 0.0; n = 0; pos = 0
        for m, (T, C) in donnees_fraiches(spec, depuis).items():
            if sum(1 for t in T if t >= depuis) < 2: L.append(f"- {m} : pas encore de bougie"); continue
            tr = banc.tester(spec, C, T, depuis, now + 1)[0]; r = sum(x for x, _ in tr); som += r; n += len(tr); pos += r > 0
            L.append(f"- {m} : {len(tr)} trades, somme {fr(r * 100, 2)} % (le dernier peut être encore ouvert)")
        jours = (now - depuis) // 86400
        L += ["", f"Au {time.strftime('%d/%m/%Y')} : {n} trades en {jours} jours, somme {fr(som * 100, 2)} %, {pos}/{len(spec['marches'])} marchés positifs."
              + (" → ÉCHÉANCE ATTEINTE : à juger." if n >= 30 or jours >= 90 else "")]
        open(os.path.join(PAPIER, f[:-5] + ".md"), "w").write("\n".join(L) + "\n"); print(L[-1])


def cmd_autotest():
    """Vérifie le banc dans les deux sens : il doit dire GAGNE quand un avantage est planté, et ne pas le dire quand il n'y en a pas."""
    spec = {"nom": "auto-test", "tf": "1d", "marches": ["A", "B", "C", "D"], "long": "baisse_suite(3)", "short": None, "sortie": {"max_bougies": 1}}
    t0 = banc.ts("2005-01-03"); per = (("1re moitié", t0, t0 + 3000 * 86400), ("2e moitié", t0 + 3000 * 86400, t0 + 6000 * 86400)); ok = True
    for nom, effet, attendu in (("avantage planté (+0,8 % le lendemain de 3 baisses)", 0.008, True), ("aucun avantage", 0.0, False)):
        v, r, det = evaluer(spec, {m: synthetique(i + (0 if effet else 100), effet=effet) for i, m in enumerate("ABCD")}, per)
        bon = (v == "GAGNE") == attendu; ok &= bon
        print(f"{'✔' if bon else '✘'} {nom} : {v} · sommes {' / '.join(fr(d['somme'] * 100) + ' %' for d in det)} · rangs {' / '.join(f'{d['rang']:.0f}e' for d in det)}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "verifier": print(verifier(charger(sys.argv[2])))
    elif cmd == "juger": cmd_juger(sys.argv[2])
    elif cmd == "papier": cmd_papier()
    elif cmd == "liste": print(open(REGISTRE).read() if os.path.exists(REGISTRE) else "Aucune idée jugée pour l'instant.")
    elif cmd == "auto-test": cmd_autotest()
    else: print(__doc__)
