"""[info, contrôle de PREREG-21] Le filtre multi-unités améliore-t-il le gain PAR TRADE, ou seulement le nombre de trades (frais) ?"""
import itertools
from t24 import Marche, SORTIES, C0, C1
M = {m: Marche(m) for m in ("XBT", "ETH", "SOL")}
mieux = 0; n = 0; tot = {0: [0.0, 0], 1: [0.0, 0], 2: [0.0, 0]}
for m, k, sig, (tp, sl) in itertools.product(("XBT", "ETH", "SOL"), (3, 5), (1, 2), SORTIES):
    pt = {}
    for f in (0, 1, 2):
        R = M[m].strat(k, sig, f, tp, sl, C0, C1)[0]; pt[f] = sum(R) / max(1, len(R)); tot[f][0] += sum(R); tot[f][1] += len(R)
    for f in (1, 2): mieux += pt[f] > pt[0]; n += 1
print(f"2026 : gain moyen PAR TRADE filtré > non filtré dans {mieux}/{n} cas")
for f, (s, c) in tot.items(): print(f"  F{f} : {c} trades, {1e4*s/max(1,c):+.1f} pb par trade en moyenne")
