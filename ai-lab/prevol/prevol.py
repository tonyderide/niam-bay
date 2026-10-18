"""Check-list pré-vol d'une expérience de NB (conseil 1018, 6.82). À lancer AVANT de figer une règle ou de commiter un pré-enregistrement.
Tirée de 4 erreurs réelles : cible morte (0x777d), règle figée sur 11 événements (jumeau), test sans puissance (Turing passage 1), duel à n=1/jour.
Elle juge la PROCÉDURE, jamais le résultat. Elle ne voit pas les erreurs de logique.
Usage : python3 prevol.py spec.json   (exemples : specs/)
spec : {"name", "events_train", "base_rate", "n_test_planned", "baseline", "oos_skill" (null si pas fait),
        "activity_cmd" (optionnel : commande qui affiche l'âge en heures de la dernière activité de la cible)}"""
import json, math, subprocess, sys

def check(s):
    out = []
    add = lambda lvl, msg: out.append((lvl, msg))
    if s.get("activity_cmd"):
        try:
            age = float(subprocess.run(s["activity_cmd"], shell=True, capture_output=True, text=True, timeout=60).stdout.strip())
            add("FAIL" if age > 24 else "OK", f"cible active : dernière activité il y a {age:.0f} h" + (" → morte ou en pause : attendre 72 h avant de conclure" if age > 24 else ""))
        except Exception as e:
            add("WARN", f"activité de la cible non vérifiable ({type(e).__name__})")
    elif s.get("kind") != "comparaison":
        add("WARN", "aucune commande pour vérifier que la cible est vivante")
    if s.get("kind") == "comparaison":  # duel, calibration : on compare des prévisions, aucune règle n'est apprise
        add("OK", "comparaison de prévisions : pas d'entraînement ni de hors-échantillon à faire")
    else:
        k = s["events_train"]
        mde = 2 / math.sqrt(k) if k else float("inf")
        add("FAIL" if k < 15 else ("WARN" if k < 50 else "OK"),
            f"{k} événements à l'entraînement → seul un écart relatif de ±{mde:.0%} sur leur fréquence est distinguable du bruit")
        sk = s.get("oos_skill")
        if sk is None:
            add("FAIL", "le test hors échantillon n'a pas été fait : fais-le AVANT de figer la règle")
        else:
            add("OK" if sk > 0.05 else "FAIL", f"skill hors échantillon = {sk:+.3f}" + ("" if sk > 0.05 else " → pas mieux que le témoin sur des données neuves (seuil +0,05)"))
    add("OK" if s.get("baseline") else "FAIL", f"témoin naïf : {s.get('baseline') or 'aucun'}")
    exp = s["n_test_planned"] * s["base_rate"]
    add("FAIL" if exp < 10 else ("WARN" if exp < 30 else "OK"),
        f"événements attendus dans le test : {exp:.0f} ({s['n_test_planned']} essais × {s['base_rate']:.3f})" + (" → le verdict sera probablement indécidable" if exp < 10 else ""))
    return out


if __name__ == "__main__":
    s = json.load(open(sys.argv[1]))
    res = check(s)
    print(f"Pré-vol : {s['name']}")
    for lvl, msg in res:
        print(f"  {'✅' if lvl == 'OK' else '⚠️' if lvl == 'WARN' else '❌'} {msg}")
    fails = sum(l == "FAIL" for l, _ in res)
    print("  → " + ("NE PAS DÉCOLLER" if fails else "décollage possible"))
    sys.exit(1 if fails else 0)
