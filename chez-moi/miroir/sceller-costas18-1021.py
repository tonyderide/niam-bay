import json, time
P = json.load(open("predictions.json")); now = time.strftime("%Y-%m-%dT%H:%M")
i = "moi-calcul-costas18"; assert not any(x["id"] == i for x in P)
P.append({"id": i, "family": "moi-calcul",
  "claim": "Costas n=18 : mon compteur termine avant le 22/10 05:30 (Paris) ET trouve exactement 15 096 (valeur OEIS A008404)", "p": 0.85,
  "why": "n=1..16 déjà identiques à l'OEIS (compteur fiable ~97 %). n=17 lancé à 22:17, ~330 s par colonne, fin ~23:25 ; n=18 ~x4,7 par colonne (vu de 16 à 17) -> ~1550 s x 9 colonnes = ~3 h 55 -> ~03:20 ; à x6 -> ~04:25. Risques : croissance pire que x7, PC éteint.",
  "baselines": {"p05": 0.5}, "made": now, "resolve_at": "2026-10-22T05:30",
  "cmd": "python3 ~/nb/miroir/golomb_suivi.py 2026-10-22T05:30 \"= 15096 (\" costas18-suivi.txt", "test": "out.strip()==\"1\"", "outcome": None})
json.dump(P, open("predictions.json", "w"), indent=1, ensure_ascii=False); print("scellé", i, now)
