"""tableaux mois par mois (3 réglages figés aux meilleures parts 2024-2025) + regard après coup sur toute la grille"""
import json, numpy as np
from etude import REG, FAM, NOMS_MOIS, decrire
J = json.load(open("jugement.json")); G = np.load("grille.npz"); RES = G["RES"]
top = sorted(J, key=lambda n: -J[n]["choix_2024_2025_3pieces"]["part_positifs"])[:3]
for n in top:
    b = J[n]; print(f"\n### {n} : {b['fige']}\n| Mois | BTC | ETH | SOL | Autres pièces : part de mois positifs | Autres pièces : moyenne |\n|---|---|---|---|---|---|")
    M = b["mois_par_mois_3pieces"]; A = b["J2_autres_1h_pessimiste"]
    for k, m in enumerate(NOMS_MOIS):
        f = lambda v: "—" if v is None else f"{v:+.1f}"
        print(f"| {m}{' (2026)' if k >= 24 else ''} | {f(M['BTCUSDT'][k])} | {f(M['ETHUSDT'][k])} | {f(M['SOLUSDT'][k])} | {A['part_positifs_par_mois'][k]:.0%} | {A['moyenne_par_mois'][k]:+.1f} |")
print("\n## après coup (toute la grille, 6 132 réglages, BTC/ETH/SOL 1 min)")
p24 = (RES[:, :, :24] > 0).mean((1, 2)); p26 = (RES[:, :, 24:] > 0).mean((1, 2)); pall = (RES > 0).mean((1, 2))
print("max part 2024-2025", p24.max(), "| max part 2026", p26.max(), "| max part sur les 99 mois", pall.max())
print("réglages à 27/27 en 2026 :", int((p26 == 1).sum()))
for q in np.where(p26 == 1)[0][:10]: print("   ", decrire(REG[q]), "| 2024-25", round(p24[q], 3), "| moy 2026", round(float(np.nanmean(RES[q, :, 24:])), 2), "| pire mois 24-25", round(float(np.nanmin(RES[q, :, :24])), 1))
print("réglages à 72/72 en 2024-2025 :", int((p24 == 1).sum()))
for f, n in FAM.items():
    q = [i for i, g in enumerate(REG) if g[0] == f]; print(n, "max part 99 mois", round(float(pall[q].max()), 3), "| réglages >= 90 % sur 2024-25", int((p24[q] >= .9).sum()))
