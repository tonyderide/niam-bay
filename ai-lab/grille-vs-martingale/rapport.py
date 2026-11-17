"""PREREG-76 : met t76.json en tableaux (aucun calcul nouveau)."""
import json, os
D = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "t76.json")))
R, N6, RU, H, V = D["quatre_paires"], D["six_neuves"], D["ruine_4"], D["hasard_resume"], D["verdicts"]
f = lambda x: "—" if x is None else f"{x:+.2f}".replace(".", ",")
p = lambda x: f"{100 * x:.1f} %".replace(".", ",")
B = ["A", "B", "C", "C+", "C-", "achat"]
print("VERDICTS :", json.dumps(V, ensure_ascii=False)); print()
print("| Mesure (4 paires, 02/2024 → 09/2026, en $) | " + " | ".join(B) + " |"); print("|---|" + "---|" * len(B))
def L(nom, fn): print(f"| {nom} | " + " | ".join(fn(b) for b in B) + " |")
L("Total", lambda b: f(R[b]["total"]))
L("P1 (02/2024 → 12/2025)", lambda b: f(R[b].get("P1"))); L("P2 (01 → 09/2026)", lambda b: f(R[b].get("P2")))
L("Mois positifs", lambda b: f"{R[b]['mois_positifs']}/{R[b]['n_mois']}")
L("Pire mois", lambda b: f(R[b]["pire_mois"]))
L("Pire baisse du portefeuille", lambda b: f(R[b].get("pire_baisse")))
L("Point le plus bas", lambda b: f(R[b].get("plus_bas")))
L("Positions fermées (gagnantes)", lambda b: f"{R[b]['positions_fermees']} ({R[b]['gagnantes']})" if "positions_fermees" in R[b] else "—")
L("Pire série : pertes d'affilée (somme)", lambda b: f"{R[b]['pire_serie_n']} ({f(R[b]['pire_serie_somme'])})" if "pire_serie_n" in R[b] else "—")
L("Pire position / meilleure", lambda b: f"{f(R[b]['pire_trade'])} / {f(R[b]['meilleur_trade'])}" if "pire_trade" in R[b] else "—")
L("Frais payés", lambda b: f(-R[b]["frais"]) if "frais" in R[b] else "—")
L("Par dollar échangé (points de base)", lambda b: f(R[b].get("par_dollar_echange_pb")))
L("Gain / pire baisse", lambda b: f(R[b]["total"] / -R[b]["pire_baisse"]) if R[b].get("pire_baisse") else "—")
L("Paires positives (sur 4)", lambda b: str(R[b]["paires_positives"]))
L("Ruine à 90 j, compte 6,40 $ (fréquence)", lambda b: f"{p(RU[b]['p_ruine'])} ({RU[b]['ruines']}/{RU[b]['departs']})")
L("Perdant après 90 j (fréquence)", lambda b: p(RU[b]["p_perte_90j"]) if "p_perte_90j" in RU[b] else "—")
L("Pire résultat à 90 j", lambda b: f(RU[b].get("pire_90j")))
L("6 paires neuves : total", lambda b: f(N6[b]["total"])); L("6 paires neuves : positives", lambda b: f"{N6[b]['paires_positives']}/6")
L("Hasard (200 mélanges) : médiane", lambda b: f(H[b]["mediane"])); L("Hasard : 5e → 95e centile", lambda b: f"{f(H[b]['p05'])} → {f(H[b]['p95'])}")
L("Part des mélanges ≥ au réel", lambda b: p(H[b]["p_valeur"]))
print(); d = R["B_moins_A"]; d6 = N6["B_moins_A"]; h = H["B_moins_A"]
print(f"B − A : total {f(d['total'])} $ ; B mieux {d['mois_B_mieux']}/{d['n_mois']} mois ; P1 {f(d['P1'])}, P2 {f(d['P2'])} ; par paire {d['par_paire']} ; "
      f"6 neuves {f(d6['total'])} $, B mieux sur {d6['paires_B_mieux']}/6 {d6['par_paire']} ; hasard : médiane {f(h['mediane'])}, 5e–95e {f(h['p05'])} → {f(h['p95'])}, "
      f"B − A > 0 dans {p(h['part_positive'])} des mélanges, mélanges ≥ au réel {p(h['p_valeur'])}")
for b in ("A", "B"):
    x = R[b]; print(f"{b} : branche gagne {x['branche_gagne']}, branche perd {x['branche_perd']}, sans protection {x['sans_protection']}, sorties {x['sorties']} (1 grille, 2 stop, 3 objectif, 4 vrai stop, 5 fin)")
print(); print("Par paire :"); print("| Paire | " + " | ".join(B) + " |"); print("|---|" + "---|" * len(B))
for c in R["A"]["par_paire"]: print(f"| {c} | " + " | ".join(f(R[b]["par_paire"][c]) for b in B) + " |")
for c in N6["A"]["par_paire"]: print(f"| {c} (neuve) | " + " | ".join(f(N6[b]["par_paire"][c]) for b in B) + " |")
print(f"| DOGE (info) | " + " | ".join(f(D["doge_info"][b]["total"]) for b in B) + " |")
print(); print("Par mois (4 paires) :"); print("| Mois | A | B | B − A | C | C+ | C- | achat |"); print("|---|---|---|---|---|---|---|---|")
for m in R["A"]["mois"]:
    print(f"| {m} | {f(R['A']['mois'][m])} | {f(R['B']['mois'][m])} | {f(R['B']['mois'][m] - R['A']['mois'][m])} | {f(R['C']['mois'][m])} | {f(R['C+']['mois'][m])} | {f(R['C-']['mois'][m])} | {f(R['achat']['mois'][m])} |")
print(); print("Ruine, détail :", json.dumps(RU, ensure_ascii=False)); print("Ruine 6 neuves (info) :", json.dumps({b: D['ruine_6_info'][b]['p_ruine'] for b in D['ruine_6_info']}, ensure_ascii=False))
