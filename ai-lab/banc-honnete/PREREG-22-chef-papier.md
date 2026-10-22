# Pré-enregistrement 22 : le chef d'orchestre EN PAPIER sur l'avenir
Figé le 22/10/2026 à 02h58, APRÈS relecture d'équité par le quant (corrections intégrées) et AVANT tout code.
Pourquoi : PREREG-20 a confirmé un timing du chef sur des marchés neufs (2 périodes, audit sans bug), mais toutes les périodes passées ont maintenant été vues. Seules des semaines FUTURES peuvent confirmer sans contamination. Aucun ordre réel.

## Règle (strictement celle de PREREG-20)
Bibliothèques : les 6 groupes de PREREG-20 (G1 ARB BNB INJ · G2 FET GRT ALGO · G3 CRV LDO IMX · G4 RUNE EGLD SAND · G5 MANA AXS APE · G6 DYDX GALA COMP), 120 stratégies chacun (t17_lib, exécution honnête, taker 0,05 %/côté). Chaque lundi 00:00 UTC : top 10 au score des trades SORTIS sur les 8 semaines précédentes, score > 0.

## Journal horodaté (sur la VM)
- **Lundi 00:15 UTC — CHOIX** : télécharger les bougies publiques ; archiver l'instantané (empreinte SHA-256) ; calculer les choix du chef ET, sur ce MÊME instantané, les moitiés de cases de T1 et les 1 000 choix de T2 (décalage 9-52 semaines) ; écrire ~/nb/chef-papier/choix-AAAA-SS.json (choix, empreintes du code et des données) ; le pousser sur GitHub (dépôt niam-bay) AVANT 01:00 UTC — l'horodatage du push enregistré par GitHub sert de preuve par un tiers. Un seul fichier par semaine, en ajout seulement.
- **Semaine comptée** : trades ENTRÉS dans [lundi 01:00, lundi suivant 01:00) UTC, pour le chef comme pour T1 et T2 (aucune entrée antérieure au choix daté).
- **Mercredi 00:15 UTC — SOLDE** de la semaine précédente (tous les trades, qui durent ≤ 24 h, sont fermés) : un SEUL instantané pour chef, T1 et T2 ; ligne ajoutée à ~/nb/chef-papier/journal.jsonl, poussée sur GitHub.
- **Pannes** : semaine ratée (pas de choix poussé avant 01:00) = invalide pour TOUS, on prolonge jusqu'à 26 semaines valides ; > 3 semaines ratées = test invalide ; alerte écrite si aucun fichier à 01:00. Marché retiré ou trou de bougies : traité à l'identique pour tous (retiré = 0 partout). Code FIGÉ pendant le test ; toute correction est journalisée et recalculée pour toutes les branches.

## Durée et verdict
26 semaines à partir du premier lundi après mise en service (au plus tôt le 26/10/2026).
Puissance (revue du quant) : contre T1, 26 semaines suffisent (z ≈ 3,4 si l'effet historique tient) ; contre T2 il faut ≈ 70 semaines.
- **Verdict principal à 26 semaines valides** : somme du chef > 95e centile de T1 (sommes appariées des 6 groupes) ET ≥ 4/6 groupes au-dessus de la médiane de T1 (secondaire) → « timing contre T1 confirmé en papier », sinon « non démontré ».
- **Verdict T2 à 52 semaines valides** (puissance ≈ 40 % à 26 : on ne le juge pas avant) : somme du chef > 95e centile de T2.
Rentabilité affichée (sans conditionner le verdict) : aux frais taker 0,05 %, et avec 5 pb de glissement par côté pour TOUS (chef et témoins) ; et séparément sur les seuls marchés « liquides » = moins de 20 % de bougies 15 min plates sur les 90 jours précédant le 26/10/2026 (liste figée au démarrage). Diagnostic : trades du chef vs moyenne T1 ET T2 (±10 %).
Arrêt anticipé : aucun (on ne regarde pas pour arrêter ; seulement un point d'étape public à 13 semaines, sans décision).

## Mise en service (22/10/2026, 03h17)
Script figé : ai-lab/chef-papier/chef_papier.py (commit 2d8261d, empreinte code da33810971b5b8af, incluant t17_lib.py). Essai à blanc réussi (choix S42 + solde, choix S43), hors test.
Cron du PC : lundis et mercredis, toutes les 15 min de 0 h à 3 h (heure locale) ; le script n'agit que dans la fenêtre 00:00-00:59 UTC et une seule fois par semaine. Premier choix réel : lundi 26/10/2026 (semaine 2026-S44).
