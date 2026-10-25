"""Banc d'essai perso (essai « n de 1 ») : est-ce que X marche POUR MOI ?
Le tirage au sort décide à l'avance des jours A et B, on note un chiffre, un test de permutation juge.

  python3 banc_perso.py nouveau cafe "café 30 min avant la séance" "pas de café" --seances 16 --mesure "répétitions au développé couché à 80 kg"
  python3 banc_perso.py noter cafe 11          # note la mesure de la prochaine séance prévue
  python3 banc_perso.py verdict cafe

Règles figées à la création (pré-enregistrement) : le plan, la mesure, le sens attendu (A > B), le seuil (p < 0,05).
Les données vivent dans ~/.local/state/nb/banc-perso/<nom>.json (privé, hors dépôt)."""
import argparse, json, os, random, sys, time

DOSSIER = os.path.expanduser("~/.local/state/nb/banc-perso")


def chemin(nom):
    return os.path.join(DOSSIER, nom + ".json")


def nouveau(a):
    os.makedirs(DOSSIER, exist_ok=True)
    if os.path.exists(chemin(a.nom)):
        sys.exit("ce banc existe déjà")
    if a.seances % 2 or a.seances < 8:
        sys.exit("il faut un nombre pair de séances, au moins 8")
    plan = []
    for _ in range(a.seances // 2):  # tirage par paires : chaque paire contient un A et un B, ordre au hasard
        paire = ["A", "B"]; random.shuffle(paire); plan += paire
    b = {"nom": a.nom, "A": a.a, "B": a.b, "mesure": a.mesure, "plus_haut_mieux": not a.plus_bas_mieux,
         "cree": time.strftime("%F %H:%M"), "plan": plan, "valeurs": []}
    json.dump(b, open(chemin(a.nom), "w"), ensure_ascii=False, indent=1)
    print(f"Banc « {a.nom} » créé : {a.seances} séances, mesure = {a.mesure}.")
    print(f"Prochaine séance : {etiquette(b)}. (Ne regarde pas la suite du plan : ça biaise.)")


def charger(nom):
    if not os.path.exists(chemin(nom)):
        sys.exit("banc inconnu")
    return json.load(open(chemin(nom)))


def etiquette(b):
    i = len(b["valeurs"])
    if i >= len(b["plan"]):
        return "terminé"
    return f"séance {i + 1}/{len(b['plan'])} → {b['A'] if b['plan'][i] == 'A' else b['B']}"


def noter(a):
    b = charger(a.nom)
    if len(b["valeurs"]) >= len(b["plan"]):
        sys.exit("toutes les séances sont notées : lance verdict")
    b["valeurs"].append({"quand": time.strftime("%F %H:%M"), "bras": b["plan"][len(b["valeurs"])], "valeur": a.valeur})
    json.dump(b, open(chemin(a.nom), "w"), ensure_ascii=False, indent=1)
    print(f"noté. Prochaine : {etiquette(b)}")


def verdict(a):
    b = charger(a.nom); v = b["valeurs"]
    xa = [x["valeur"] for x in v if x["bras"] == "A"]; xb = [x["valeur"] for x in v if x["bras"] == "B"]
    if len(xa) < 4 or len(xb) < 4:
        sys.exit(f"trop tôt : {len(xa)} A et {len(xb)} B notés (il en faut au moins 4 de chaque)")
    moy = lambda x: sum(x) / len(x)
    sens = 1 if b["plus_haut_mieux"] else -1
    ecart = sens * (moy(xa) - moy(xb))
    tous = xa + xb; n = len(xa); rnd = random.Random(1); plus = 0; N = 10000
    for _ in range(N):  # test de permutation unilatéral : le hasard fait-il aussi bien ?
        rnd.shuffle(tous)
        plus += sens * (moy(tous[:n]) - moy(tous[n:])) >= ecart
    p = (plus + 1) / (N + 1)
    fini = len(v) == len(b["plan"])
    print(f"« {b['A']} » : moyenne {moy(xa):.2f} ({len(xa)} séances) | « {b['B']} » : {moy(xb):.2f} ({len(xb)})")
    print(f"écart dans le sens attendu : {ecart:+.2f} {b['mesure']} · p = {p:.3f}")
    if not fini:
        print("(provisoire : le verdict officiel se lit à la fin du plan, sinon on s'arrête quand ça arrange)")
    elif p < 0.05:
        print("VERDICT : effet DÉMONTRÉ pour toi, sur cette mesure (pas forcément pour les autres).")
    else:
        print("VERDICT : NON DÉMONTRÉ (ça ne veut pas dire que ça ne marche pas : l'effet est peut-être trop petit pour ce nombre de séances).")


def main():
    ap = argparse.ArgumentParser(); s = ap.add_subparsers(dest="cmd", required=True)
    n = s.add_parser("nouveau"); n.add_argument("nom"); n.add_argument("a"); n.add_argument("b")
    n.add_argument("--seances", type=int, default=16); n.add_argument("--mesure", required=True)
    n.add_argument("--plus-bas-mieux", action="store_true")
    o = s.add_parser("noter"); o.add_argument("nom"); o.add_argument("valeur", type=float)
    d = s.add_parser("verdict"); d.add_argument("nom")
    a = ap.parse_args(); {"nouveau": nouveau, "noter": noter, "verdict": verdict}[a.cmd](a)


if __name__ == "__main__":
    main()
