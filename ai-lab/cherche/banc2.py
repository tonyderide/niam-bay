#!/usr/bin/env python3
"""Banc GARDÉ DE CÔTÉ (écrit le 30/10/2026 ~02h05, avant le premier résultat de la couche sens, jamais utilisé pour régler) :
questions plus paraphrasées, sur des coins du repo que banc.py ne touche pas. Sert à vérifier que ça généralise."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import banc
banc.Q = [
    ("les frais de Kraken avalent-ils les petits gains de la grille", "les-fees-mangent-tout"),
    ("qui paie quand je fais une bêtise sur GitHub avec le nom de Tony", "le-compte-de-tony"),
    ("comment Niam-Bay pourrait payer sa propre existence", "projets/survie"),
    ("programme de fidélité en SaaS pour développeurs", "loyalty-saas"),
    ("la sonde spatiale la plus lointaine", "voyager"),
    ("ensembles sans trois points alignés, recherche façon FunSearch", "capset"),
    ("récupérer de l'argent qu'on nous doit, remboursements", "chasseur-remboursements"),
    ("faire tourner un petit LLM sur le processeur du PC", "nb-local"),
    ("nettoyer une matrice de corrélation avec Marchenko-Pastur", "rmt"),
    ("le bot de trading tient-il ses promesses", "promesses"),
    ("ce que je dis et ce que je fais vraiment", "dire-faire"),
    ("vérifier automatiquement que mes souvenirs sont vrais", "memoire-falsifiable"),
    ("est-ce qu'un trader est un robot ou un humain", "turing-inverse"),
    ("les baleines qui bougent de gros blocs", "blocs-baleine"),
    ("parier sur le sens du prix à un jour et mesurer le Brier", "calibration"),
    ("deuxième avis pour attraper mes erreurs de calcul", "second-avis"),
    ("trouver une grille cachée dans le carnet d'ordres", "grille-cachee"),
    ("couper le moteur de trading quand le bitcoin casse", "killswitch"),
    ("Tony a shorté le bitcoin en tendance haussière et s'est fait stopper deux fois", "lesson_xbt_short_uptrend"),
    ("taille de position selon le critère de Kelly", "kelly"),
]
if __name__ == "__main__":
    banc.run("-v" in sys.argv)
