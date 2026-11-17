"""PREREG-76 : grille actuelle (A) contre grille à protection unique (B) contre martingale avec inversion (C).
Usage : python t76.py fidelite | officiel"""
import sys, os, json, time, datetime as dt, numpy as np
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ICI, "..", "banc-honnete")); sys.path.insert(0, os.path.join(ICI, "..", "cent-strategies"))
from t69 import regime, couper, ms          # noqa: E402  régime ADX<40 et BBW<4 % sur 15 min (comme SignalService.checkRegime)
from t73 import danger                      # noqa: E402  RSI14 1 h < 25 (disjoncteur)
from t75 import melange                     # noqa: E402  prix mélangés (témoin de hasard)
from sim76 import grille, martingale, achat  # noqa: E402

CACHE = os.path.expanduser("~/.cache/banc-honnete")
C4 = ["SOL", "LINK", "ADA", "DOT"]; C6 = ["ATOM", "AVAX", "BCH", "BNB", "XRP", "LTC"]
CAP = {"SOL": 1.42, "LINK": 1.18, "ADA": 1.18, "DOT": 1.02}; CAP_NEUF = 1.18
BASE, COMPTE = 3.0, 6.40
DEB, FIN = ms(2024, 2, 1), ms(2026, 10, 1); P2 = ms(2026, 1, 1)
N_HASARD, GRAINE, H_RUINE = 200, 7600, 90 * 1440
BRAS = ["A", "B", "C+", "C-", "achat"]


class Terrain:
    def __init__(self, a):
        self.t = a[:, 0].astype(np.int64); self.o, self.h, self.l, self.c = (np.ascontiguousarray(a[:, k]) for k in (1, 2, 3, 4))
        self.R = regime(self.t, self.h, self.l, self.c); self.DG = danger(self.t, self.c)

    def run(self, bras, i0, i1, cap, dec=0, prec=-1, force0=False, lot=False):
        s = slice(i0, i1)
        if bras in ("A", "B"):
            return grille(self.t[s], self.o[s], self.h[s], self.l[s], self.c[s], self.R[s], self.DG[s], cap, 1 if bras == "B" else 0, dec, prec, force0)
        if bras in ("C+", "C-"):
            return martingale(self.o[s], self.h[s], self.l[s], self.c[s], 1.0 if bras == "C+" else -1.0, BASE, lot)
        return (achat(self.o[s], self.c[s], BASE),)


def charge(c): return couper(np.load(f"{CACHE}/m1-binance/{c}.npy"), 2880)
def idx(T, x): return int(np.searchsorted(T.t, x))
def jour(x): return dt.datetime.fromtimestamp(x / 1000, dt.timezone.utc).strftime("%Y-%m-%d %H:%M")


def mois_bornes(t):
    """indices de la dernière minute de chaque mois civil"""
    m = (t // 60000 // 1440 + 4).astype(np.int64)  # inutile ; on passe par datetime64
    d = t.astype("datetime64[ms]").astype("datetime64[M]"); fin = np.nonzero(d[1:] != d[:-1])[0]
    return np.concatenate([fin, [len(t) - 1]]), [str(x) for x in d[np.concatenate([fin, [len(t) - 1]])]]


def serie_pertes(g):
    """plus longue suite de résultats négatifs d'affilée, et la pire somme d'une telle suite"""
    best = 0; cur = 0; s = 0.0; pire = 0.0
    for x in g:
        if x <= 0: cur += 1; s += x; best = max(best, cur); pire = min(pire, s)
        else: cur = 0; s = 0.0
    return best, round(pire, 4)


def resume(terr, caps, d, f, detail=True):
    """tous les bras sur un jeu de paires ; renvoie totaux, mois, pire baisse, séries, par paire"""
    out = {}; t0 = None
    for b in BRAS:
        eqs = {}; G = []; vol = 0.0; frais = 0.0; ncyc = 0; parb = {1: [0, 0.0], 2: [0, 0.0], 0: [0, 0.0]}; park = {}
        for c, T in terr.items():
            i0, i1 = idx(T, d), idx(T, f); r = T.run(b, i0, i1, caps[c]); eqs[c] = r[0]; t0 = T.t[i0:i1]
            if b != "achat":
                g = r[2]; G.append((r[1], g, c)); ncyc += len(g); st = r[-1]; frais += st[0]; vol += st[1]
                if b in ("A", "B"):
                    for kk, bb, gg in zip(r[3], r[4], g):
                        parb[int(bb)][0] += 1; parb[int(bb)][1] += float(gg); park[int(kk)] = park.get(int(kk), 0) + 1
        Lm = min(len(e) for e in eqs.values()); port = sum(e[:Lm] for e in eqs.values()); t0 = t0[:Lm]
        fin, noms = mois_bornes(t0); v = port[fin]; mm = np.diff(np.concatenate([[0.0], v]))
        pk = np.maximum.accumulate(np.maximum(port, 0.0)); dd = float((port - pk).min())
        i2 = int(np.searchsorted(t0, P2)); p1 = float(port[i2 - 1]) if 0 < i2 <= Lm else None
        o = dict(total=round(float(port[-1]), 4), par_paire={c: round(float(e[-1]), 4) for c, e in eqs.items()},
                 paires_positives=sum(e[-1] > 0 for e in eqs.values()), mois=dict(zip(noms, [round(float(x), 4) for x in mm])),
                 mois_positifs=int((mm > 0).sum()), n_mois=len(mm), pire_mois=round(float(mm.min()), 4),
                 pire_baisse=round(dd, 4), plus_bas=round(float(port.min()), 4),
                 ruine_parcours_complet=bool(port.min() <= -COMPTE), P1=None if p1 is None else round(p1, 4),
                 P2=None if p1 is None else round(float(port[-1]) - p1, 4))
        if b != "achat":
            # pire série : résultats des positions fermées, toutes paires, dans l'ordre du temps
            tous = sorted([(int(i), float(x)) for ii, gg, _ in G for i, x in zip(ii, gg)]); gl = [x for _, x in tous]
            n_, p_ = serie_pertes(gl); pp = max((serie_pertes(list(gg))[0], c) for _, gg, c in G)
            o.update(positions_fermees=ncyc, gagnantes=int(sum(x > 0 for x in gl)), pire_serie_n=n_, pire_serie_somme=p_,
                     pire_serie_une_paire=pp[0], pire_trade=round(min(gl), 4) if gl else 0.0, meilleur_trade=round(max(gl), 4) if gl else 0.0,
                     frais=round(frais, 4), volume=round(vol, 2), par_dollar_echange_pb=round(1e4 * float(port[-1]) / vol, 3) if vol else None)
            if b in ("A", "B"):
                o["branche_gagne"] = dict(n=parb[1][0], somme=round(parb[1][1], 4)); o["branche_perd"] = dict(n=parb[2][0], somme=round(parb[2][1], 4))
                o["sans_protection"] = dict(n=parb[0][0], somme=round(parb[0][1], 4)); o["sorties"] = park
        out[b] = o if detail else dict(total=o["total"], mois_positifs=o["mois_positifs"])
    # C = moyenne des deux départs
    mc = {k: (out["C+"]["mois"][k] + out["C-"]["mois"][k]) / 2 for k in out["C+"]["mois"]} if detail else {}
    out["C"] = dict(total=round((out["C+"]["total"] + out["C-"]["total"]) / 2, 4))
    if detail:
        out["C"].update(mois={k: round(v, 4) for k, v in mc.items()}, mois_positifs=sum(v > 0 for v in mc.values()), n_mois=len(mc),
                        pire_mois=round(min(mc.values()), 4),
                        par_paire={c: round((out["C+"]["par_paire"][c] + out["C-"]["par_paire"][c]) / 2, 4) for c in terr},
                        P1=None if out["C+"]["P1"] is None else round((out["C+"]["P1"] + out["C-"]["P1"]) / 2, 4),
                        P2=None if out["C+"]["P2"] is None else round((out["C+"]["P2"] + out["C-"]["P2"]) / 2, 4))
        out["C"]["paires_positives"] = sum(v > 0 for v in out["C"]["par_paire"].values())
        ma, mb = out["A"]["mois"], out["B"]["mois"]
        out["B_moins_A"] = dict(total=round(out["B"]["total"] - out["A"]["total"], 4), mois_B_mieux=sum(mb[k] > ma[k] for k in ma), n_mois=len(ma),
                                P1=None if out["A"]["P1"] is None else round(out["B"]["P1"] - out["A"]["P1"], 4),
                                P2=None if out["A"]["P2"] is None else round(out["B"]["P2"] - out["A"]["P2"], 4),
                                par_paire={c: round(out["B"]["par_paire"][c] - out["A"]["par_paire"][c], 4) for c in terr})
        out["B_moins_A"]["paires_B_mieux"] = sum(v > 0 for v in out["B_moins_A"]["par_paire"].values())
    return out


def ruine(terr, caps, d, f):
    """départs chaque jour à 00h00 UTC, 90 jours, les paires ensemble sur un compte de COMPTE $ : ruine si le gain cumulé
    (positions valorisées à la clôture de chaque minute) touche -COMPTE."""
    T0 = next(iter(terr.values())); i0, i1 = idx(T0, d), idx(T0, f); res = {b: [] for b in BRAS}
    for s in range(i0, i1 - H_RUINE + 1, 1440):
        for b in BRAS:
            port = sum(T.run(b, s, s + H_RUINE, caps[c])[0] for c, T in terr.items()); res[b].append((float(port.min()), float(port[-1])))
    out = {}
    for b in BRAS:
        mn = np.array([x[0] for x in res[b]]); fn = np.array([x[1] for x in res[b]])
        out[b] = dict(departs=len(mn), ruines=int((mn <= -COMPTE).sum()), p_ruine=round(float((mn <= -COMPTE).mean()), 4),
                      p_perte_90j=round(float((fn < 0).mean()), 4), mediane_90j=round(float(np.median(fn)), 4), pire_90j=round(float(fn.min()), 4),
                      pire_plus_bas=round(float(mn.min()), 4))
    out["C"] = dict(departs=out["C+"]["departs"] * 2, ruines=out["C+"]["ruines"] + out["C-"]["ruines"],
                    p_ruine=round((out["C+"]["p_ruine"] + out["C-"]["p_ruine"]) / 2, 4))
    return out


if __name__ == "__main__":
    mode = sys.argv[1]; t00 = time.time()
    def log(*x): print(f"[{time.time() - t00:6.0f}s]", *x, flush=True)

    if mode == "fidelite":
        K = f"{CACHE}/k1m-76"; PREC = {"SOL": 2, "LINK": 1, "ADA": 0, "DOT": 1}
        d0 = int(dt.datetime(2026, 11, 11, 22, 45, tzinfo=dt.timezone.utc).timestamp() * 1000); f0 = ms(2026, 11, 17)
        OUT = {"A": {}, "B_info": {}}; tous = []; jours = {}
        for c in C4:
            T = Terrain(np.load(f"{K}/{c}.npy")); i0, i1 = idx(T, d0), idx(T, f0)
            for b in ("A", "B"):
                eq, ci, cg, ck, cb, st = T.run(b, i0, i1, CAP[c], dec=2, prec=PREC[c], force0=True)
                tt = T.t[i0:i1]; jf = [idx(T, ms(2026, 11, j)) - i0 - 1 for j in range(12, 18)]
                pj = np.diff(np.concatenate([[0.0], eq[jf]])) * 100
                cyc = [dict(t=jour(tt[i]), c=round(g * 100, 2), sortie=int(k), branche=int(bb)) for i, g, k, bb in zip(ci, cg, ck, cb)]
                (OUT["A"] if b == "A" else OUT["B_info"])[c] = dict(total_c=round(eq[-1] * 100, 2), par_jour_c=[round(float(x), 2) for x in pj], cycles=cyc,
                                                               exec=int(st[2]), protections=int(st[3]), vrais_stops=int(st[4]), disjoncteur=int(st[5]), grilles=int(st[6]))
                if b == "A":
                    tous += [(x["t"], c, x["c"], x["sortie"], x["branche"]) for x in cyc]
                    for k, x in enumerate(pj): jours[11 + k] = jours.get(11 + k, 0.0) + float(x)
        tous.sort(); g = [x[2] for x in tous if x[3] != 5]
        print("BRAS A rejoué du 2026-11-11 22:45Z au 2026-11-17 00:00Z (Kraken 1 min, lots réels, passage à la minute 2)")
        for x in tous: print("  ", x[0], x[1], f"{x[2]:+6.2f} c", {1: "grille", 2: "STOP", 3: "OBJECTIF", 4: "VRAI STOP", 5: "fin"}[x[3]], {0: "", 1: "gagne", 2: "perd"}[x[4]])
        tot = sum(OUT["A"][c]["total_c"] for c in C4)
        print("positions fermées :", len(g), "| net (c) :", round(tot, 2), "| par jour 11(fin)..16 (c) :", {k: round(v, 2) for k, v in jours.items()})
        print("gains de 4 à 8 c :", sum(4 <= x <= 8 for x in g), "| pertes de 5 à 10 c :", sum(-10 <= x <= -5 for x in g),
              "| branche gagne :", round(sum(x[2] for x in tous if x[4] == 1), 2), "c sur", sum(x[4] == 1 for x in tous),
              "| branche perd :", round(sum(x[2] for x in tous if x[4] == 2), 2), "c sur", sum(x[4] == 2 for x in tous))
        pire = min(jours, key=lambda k: jours[k])
        fidA = 14 <= len(g) <= 56 and -30 <= tot <= 10 and pire == 14 and jours[14] < 0 and sum(4 <= x <= 8 for x in g) >= 2 and sum(-10 <= x <= -5 for x in g) >= 2
        # bras C : DOGE, départ short, 3 $, ouverture 2026-11-10 17:40Z
        T = Terrain(np.load(f"{K}/DOGE.npy")); i0 = idx(T, int(dt.datetime(2026, 11, 10, 17, 40, tzinfo=dt.timezone.utc).timestamp() * 1000))
        eq, ti, tg, tn, ts, st = martingale(T.o[i0:], T.h[i0:], T.l[i0:], T.c[i0:], -1.0, BASE, True)
        tr = [dict(t=jour(T.t[i0 + i]), c=round(g * 100, 2), niveau=int(k), sens=int(s)) for i, g, k, s in zip(ti, tg, tn, ts)]
        print("BRAS C DOGE départ short 3 $ :", tr[:3]); fidC = 24 <= tr[0]["c"] <= 31 and tr[0]["t"].startswith("2026-11-14")
        OUT.update(A_net_c=round(tot, 2), A_fermees=len(g), A_par_jour_c={k: round(v, 2) for k, v in jours.items()}, C_doge=tr, fidele_A=bool(fidA), fidele_C=bool(fidC))
        print("FIDÈLE A :", fidA, "| FIDÈLE C :", fidC)
        json.dump(OUT, open(os.path.join(ICI, f"fidelite{sys.argv[2] if len(sys.argv) > 2 else ''}.json"), "w"), ensure_ascii=False, indent=1); sys.exit()

    # ---------------------------------------------------------------------------------------------- officiel
    OUT = {}
    def sauve(): json.dump(OUT, open(os.path.join(ICI, "t76.json"), "w"), ensure_ascii=False, indent=1)
    brut = {c: charge(c) for c in C4}; T4 = {c: Terrain(brut[c]) for c in C4}
    OUT["quatre_paires"] = resume(T4, CAP, DEB, FIN); log("4 paires :", {b: OUT["quatre_paires"][b]["total"] for b in ("A", "B", "C+", "C-", "C", "achat")}); sauve()
    OUT["ruine_4"] = ruine(T4, CAP, DEB, FIN); log("ruine :", json.dumps(OUT["ruine_4"], ensure_ascii=False)); sauve()
    T6 = {c: Terrain(charge(c)) for c in C6}; cap6 = {c: CAP_NEUF for c in C6}
    OUT["six_neuves"] = resume(T6, cap6, DEB, FIN); log("6 neuves :", {b: OUT["six_neuves"][b]["total"] for b in ("A", "B", "C+", "C-", "C", "achat")})
    OUT["ruine_6_info"] = ruine(T6, cap6, DEB, FIN); sauve()
    TD = {"DOGE": Terrain(charge("DOGE"))}; OUT["doge_info"] = resume(TD, {"DOGE": CAP_NEUF}, DEB, FIN); del T6, TD; sauve()
    rng = np.random.default_rng(GRAINE); HZ = []
    for r in range(N_HASARD):
        Th = {c: Terrain(melange(brut[c], rng)) for c in C4}; x = resume(Th, CAP, DEB, FIN, detail=False)
        HZ.append({b: x[b]["total"] for b in ("A", "B", "C+", "C-", "C", "achat")}); OUT["hasard"] = HZ
        if r % 10 == 9: log("hasard", r + 1, HZ[-1]); sauve()
    R = OUT["quatre_paires"]; H = {b: np.array([h[b] for h in HZ]) for b in HZ[0]}; hd = H["B"] - H["A"]
    OUT["hasard_resume"] = {b: dict(mediane=round(float(np.median(v)), 4), p05=round(float(np.percentile(v, 5)), 4), p95=round(float(np.percentile(v, 95)), 4),
                                    p_valeur=round(float((v >= R[b]["total"]).mean()), 4)) for b, v in H.items()}
    OUT["hasard_resume"]["B_moins_A"] = dict(mediane=round(float(np.median(hd)), 4), p05=round(float(np.percentile(hd, 5)), 4), p95=round(float(np.percentile(hd, 95)), 4),
                                             part_positive=round(float((hd > 0).mean()), 4), p_valeur=round(float((hd >= R["B_moins_A"]["total"]).mean()), 4))
    # ---------------------------------------------------------------------------------------------- verdicts (règles du prereg)
    N6 = OUT["six_neuves"]; d = R["B_moins_A"]; d6 = N6["B_moins_A"]
    b1 = d["total"] > 0; b2 = d["mois_B_mieux"] >= 22; b3 = d6["total"] > 0 and d6["paires_B_mieux"] >= 4; b4 = d["P1"] > 0 and d["P2"] > 0
    vB = "B BAT A" if (b1 and b2 and b3 and b4) else ("B MIEUX SANS PREUVE" if (b1 and sum([b2, b3, b4]) >= 2) else "NON DÉMONTRÉ")
    gB = R["B"]["total"] > 0 and R["B"]["total"] > OUT["hasard_resume"]["B"]["p95"] and N6["B"]["total"] > 0
    C = R["C"]; c1 = C["total"] > 0; c2 = R["C+"]["total"] > 0 and R["C-"]["total"] > 0; c3 = C["mois_positifs"] >= 20
    c4 = C["total"] > OUT["hasard_resume"]["C"]["p95"]; c5 = N6["C"]["total"] > 0 and N6["C"]["paires_positives"] >= 4
    c6 = OUT["ruine_4"]["C"]["p_ruine"] < 0.05; c7 = C["P1"] > 0 and C["P2"] > 0
    vC = "DÉMONTRÉ" if all([c1, c2, c3, c4, c5, c6, c7]) else "NON DÉMONTRÉ"
    OUT["verdicts"] = dict(B_contre_A=vB, criteres_B=dict(B1_total=b1, B2_mois=b2, B3_neuves=b3, B4_deux_periodes=b4), B_gagne_de_l_argent=bool(gB),
                           C=vC, criteres_C=dict(C1_total=c1, C2_deux_departs=c2, C3_mois=c3, C4_hasard=c4, C5_neuves=c5, C6_ruine=c6, C7_deux_periodes=c7))
    log("VERDICTS", json.dumps(OUT["verdicts"], ensure_ascii=False)); sauve()
