"""L'assiette honnête : une fourchette de calories et de protéines, et QUEL aliment peser pour la resserrer.
Les quantités viennent d'une estimation sur photo (NB les donne), chacune avec son incertitude.

  python3 assiette.py patate_douce:200±50 boeuf_5:120±30 guacamole:50±20 creme:20±10 huile:5±4 tomate:120±30
Valeurs pour 100 g (CIQUAL / USDA, arrondies) ; la variance d'un aliment = (kcal/g × incertitude)²."""
import math, sys

ALIMENTS = {  # kcal, protéines (g) pour 100 g, cuit sauf indication
    "patate_douce": (90, 2.0), "pomme_de_terre": (85, 2.0), "riz": (130, 2.7), "pates": (155, 5.5), "pain": (265, 9.0),
    "boeuf_5": (160, 26.0), "boeuf_15": (250, 25.0), "poulet": (165, 31.0), "saumon": (205, 22.0), "oeuf": (145, 12.5),
    "thon": (130, 29.0), "tofu": (125, 13.0), "lentilles": (115, 9.0), "pois_chiches": (165, 9.0),
    "guacamole": (155, 2.0), "avocat": (160, 2.0), "creme": (290, 2.5), "fromage_frais": (250, 6.0), "fromage": (390, 25.0),
    "yaourt_grec": (95, 9.0), "huile": (900, 0.0), "beurre": (745, 0.7),
    "tomate": (18, 0.9), "concombre": (15, 0.7), "salade": (15, 1.3), "brocoli": (35, 2.8), "oignon": (40, 1.1),
}


def lire(arg):
    nom, q = arg.split(":")
    g, inc = (q.split("±") + ["0"])[:2]
    if nom not in ALIMENTS:
        sys.exit(f"aliment inconnu : {nom} (connus : {', '.join(sorted(ALIMENTS))})")
    return nom, float(g), float(inc)


def main(args):
    items = [lire(a) for a in args]
    kcal = sum(ALIMENTS[n][0] * g / 100 for n, g, _ in items)
    prot = sum(ALIMENTS[n][1] * g / 100 for n, g, _ in items)
    var = {n: (ALIMENTS[n][0] / 100 * inc) ** 2 for n, g, inc in items}
    sd = math.sqrt(sum(var.values()))
    print(f"≈ {kcal:.0f} kcal (fourchette {kcal - 1.64 * sd:.0f} à {kcal + 1.64 * sd:.0f}, à 90 %) · {prot:.0f} g de protéines")
    total = sum(var.values()) or 1
    for n, v in sorted(var.items(), key=lambda x: -x[1])[:3]:
        reste = math.sqrt(total - v)
        print(f"  peser {n} : {100 * v / total:.0f} % de l'incertitude → fourchette ±{1.64 * reste:.0f} kcal au lieu de ±{1.64 * sd:.0f}")


if __name__ == "__main__":
    main(sys.argv[1:])
