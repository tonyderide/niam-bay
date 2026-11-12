"""PREREG-74 : choix sur P1 (4 paires), contrôle sur P2 et sur 6 paires jamais vues."""
import sys, json, numpy as np
from t69 import regime, couper, ms
from t73 import sim, danger, tendance, CAP0

Dd = sys.argv[1]
C4 = ["SOL", "LINK", "ADA", "DOT"]
C6 = ["ATOM", "AVAX", "BCH", "BNB", "XRP", "LTC"]
X = {}
for c in C4 + C6:
    a = couper(np.load("../dca-martingale/refait/donnees/SOLUSDT-1m.npy" if c == "SOL" else f"{Dd}/{c}.npy"), 2880)
    tt = a[:, 0].astype(np.int64)
    X[c] = (a, tt, danger(tt, a[:, 4]), tendance(tt, a[:, 4]), regime(tt, a[:, 2], a[:, 3], a[:, 4]))
PER = {"P1": (ms(2024, 2, 1), ms(2026, 1, 1)), "P2": (ms(2026, 1, 1), ms(2026, 10, 1))}
#        nom     écart  reposé pause filtre
VAR = [("W5", 0.05, 0, 0, 0), ("W7", 0.07, 0, 0, 0), ("W10", 0.10, 0, 0, 0), ("W5R", 0.05, 1, 0, 0), ("W7R", 0.07, 1, 0, 0),
       ("W5P", 0.05, 0, 1, 0), ("W7P", 0.07, 0, 1, 0), ("W5F", 0.05, 0, 0, 1)]
V = {v[0]: v for v in VAR}


def run(c, d, f, esp, rearm, pause, flt):
    a, tt, DG, UP, RG = X[c]; w = (tt >= d) & (tt < f); x = a[w]
    R = RG[w].copy() if pause else np.ones(int(w.sum()), np.bool_)
    return sim(tt[w].copy(), x[:, 1].copy(), x[:, 2].copy(), x[:, 3].copy(), x[:, 4].copy(), R, DG[w].copy(), CAP0, 1,
               UP[w].copy(), flt, rearm, esp, 0)


def bloc(nom, paires, pn):
    _, esp, rearm, pause, flt = V[nom]; d, f = PER[pn]
    r = {c: run(c, d, f, esp, rearm, pause, flt) for c in paires}; Lm = min(len(v[7]) for v in r.values())
    port = sum(v[7][:Lm] for v in r.values()); pk = np.maximum.accumulate(port)
    res = {c: round(v[0] - CAP0, 1) for c, v in r.items()}
    o = dict(total=round(sum(res.values()), 1), par_paire=res, positives=sum(v > 0 for v in res.values()),
             arretees=[c for c, v in r.items() if v[5] or v[6]], baisse_port=round(float((port / pk - 1).min()), 3),
             frais=round(sum(v[2] for v in r.values()), 1), exec=sum(int(v[3]) for v in r.values()))
    print(nom, pn, len(paires), "paires :", json.dumps(o, ensure_ascii=False), flush=True)
    return o


OUT = {"choix_P1": {}}
for nom in V:
    OUT["choix_P1"][nom] = bloc(nom, C4, "P1")
w5p2 = bloc("W5", C4, "P2")
OUT["temoin_ok"] = OUT["choix_P1"]["W5"]["total"] == 881.4 and w5p2["total"] == -245.0
ok = {n: o for n, o in OUT["choix_P1"].items() if not o["arretees"] and o["baisse_port"] > -0.30}
X_ = max(ok, key=lambda n: ok[n]["total"]) if ok else "W5"
OUT["X"] = X_
print("CHOIX X* =", X_, flush=True)
T1 = w5p2 if X_ == "W5" else bloc(X_, C4, "P2")
N1, N2 = bloc(X_, C6, "P1"), bloc(X_, C6, "P2")
OUT["controles"] = {"T1_4p_P2": T1, "T2_6p_P1": N1, "T3_6p_P2": N2}
OUT["info_W5"] = {"4p_P2": w5p2} if X_ == "W5" else {"4p_P2": w5p2, "6p_P1": bloc("W5", C6, "P1"), "6p_P2": bloc("W5", C6, "P2")}
t1 = T1["total"] > 0; t2 = N1["total"] > 0 and N1["positives"] >= 4 and not N1["arretees"]; t3 = N2["total"] > 0
if not OUT["temoin_ok"]:
    v = "NON CONCLUANT (témoin)"
elif X_ == "W5":
    v = "NON (W5 reste la meilleure)"
elif t1 and t2 and t3:
    v = "TIENT"
else:
    i = OUT["info_W5"]
    mieux = T1["total"] > w5p2["total"] and N1["total"] + N2["total"] > i["6p_P1"]["total"] + i["6p_P2"]["total"]
    v = "MIEUX QUE W5 SANS PREUVE" if mieux else "NON"
OUT["T"] = dict(T1=t1, T2=t2, T3=t3); OUT["verdict"] = v
print("VERDICT :", v, json.dumps(OUT["T"]), flush=True)
json.dump(OUT, open("t74.json", "w"), ensure_ascii=False, indent=1)
