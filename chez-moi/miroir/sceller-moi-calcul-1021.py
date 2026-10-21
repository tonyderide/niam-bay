import json, time
P = json.load(open("predictions.json")); now = time.strftime("%Y-%m-%dT%H:%M")
why0 = "L=143 réfutée à 21:56 en 1510 s ; rapports récents 1,30 1,39 1,20 1,24 (moy. ~1,28). "
new = [
 ("moi-calcul-golomb15-L146", "Golomb 15 : L=146 réfutée avant le 22/10 01:00 (heure de Paris)", 0.85, "2026-10-22T01:00", "L=146 : impossible",
  why0 + "Projection x1,24 : 23:55 ; x1,30 : ~00:07. Une heure de marge, risque = ralentissement brutal ou PC éteint."),
 ("moi-calcul-golomb15-L149", "Golomb 15 : L=149 réfutée avant le 22/10 05:30 (heure de Paris)", 0.62, "2026-10-22T05:30", "L=149 : impossible",
  why0 + "x1,24 -> 03:40 ; x1,28 -> 04:27 ; x1,35 -> 06:07 (raté). Pile sur la crête : je dis 62 %."),
 ("moi-calcul-golomb15-151", "Golomb 15 : règle de longueur 151 trouvée avant le 22/10 19:00 (heure de Paris)", 0.70, "2026-10-22T19:00", "L=151 : RÈGLE",
  why0 + "151 est l'optimum connu (je le crois à ~97 %) ; L=150 finirait vers 05:30-08:00, 151 trouvée en cours de route. Principal risque : PC éteint dans la journée (le calcul ne survit pas à un arrêt)."),
]
for i, c, p, dl, motif, why in new:
    assert not any(x["id"] == i for x in P)
    P.append({"id": i, "family": "moi-calcul", "claim": c, "p": p, "why": why, "baselines": {"p05": 0.5}, "made": now, "resolve_at": dl,
              "cmd": f"python3 ~/nb/miroir/golomb_suivi.py {dl} \"{motif}\"", "test": "out.strip()==\"1\"", "outcome": None})
json.dump(P, open("predictions.json", "w"), indent=1, ensure_ascii=False); print(len(P), "prédictions ;", now)
for x in P:
    if x["family"] == "moi-calcul": print(x["id"], x["p"], x["resolve_at"])
