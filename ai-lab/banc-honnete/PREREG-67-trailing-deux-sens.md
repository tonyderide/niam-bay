# Pré-enregistrement 67 : trailing stop dans les deux sens en même temps
Écrit et commité le 03/11/2026 au soir, avant tout calcul. Idée de Tony : « si je fais du trailing SL dans les deux sens ça devrait marcher ».

**NON EXÉCUTÉ.** Annoncé par erreur : Tony a refusé ce test avant tout calcul (« Non martingale avec inversion », un trade à la fois, pas les deux sens en même temps). Aucun calcul, aucun résultat, aucun script (t67.py est celui de PREREG-67-martingale-inversion-gain-tard.md). Gardé pour un historique honnête ; ne compte pour aucun verdict. Annoté le 05/11/2026.

Prédiction écrite d'avance : gagne quand le prix part fort et loin, perd quand il hésite (les deux stops sont touchés tour à tour), avec deux fois les frais. Le résultat dépendra donc surtout du régime. À vérifier.

## Règle
Pour chaque pièce, deux comptes égaux : un **long** et un **short**, ouverts ensemble, chacun avec son SL et son trailing. Quand une jambe sort, elle se rouvre seule à la minute suivante, dans le même sens. 1 min, frais 0,05 % par côté, sans levier ni martingale, sans financement. Pas de rééquilibrage entre les deux jambes (variante non testée : rouvrir les deux ensemble).

## Réglages (3, aucun choix, tous rapportés)
A : SL 10 %, activation 1 %, trailing 0,5 %. B : SL 5 %, activation 10 %, trailing 1 %. C : SL 1 %, activation 1 %, trailing 0,5 % (règle d'origine de Tony).

## Données
13 pièces (BTC, ETH, SOL, XRP, DOGE, ADA, LINK, AVAX, LTC, BNB, DOT, BCH, ATOM). P1 = 01/02/2024 → 31/12/2025. P2 = 01/01 → 30/09/2026.

## Verdict, par réglage
**« MARCHE »** si sur P1 ET P2 : portefeuille > 0, au moins 7 pièces sur 13 positives, baisse médiane moins forte que −30 %. **« GAGNE MAIS TROP DE RISQUE »** si les deux premiers critères tiennent, pas le 3e. **« NON »** sinon. Comme 3 réglages sont testés sans correction, un seul « MARCHE » resterait à confirmer en avant.
