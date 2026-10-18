# Test de Turing inversé des traders : pré-enregistrement (2026-10-18, avant toute donnée de test)

Question : à quel point le comportement d'un compte est-il **mécanique**, c'est-à-dire prévisible par une règle simple à partir du marché ?
Ce test mesure la *prévisibilité*, pas « bot ou humain » : aucune adresse ne sera étiquetée « humaine » ni « machine » (conseil, Gardien).

- Comptes (5, choisis avant de voir les résultats) : 0x6f03… (BTC, la cible du jumeau), 0x8d0c… (SOL), 0x79b1… (multi), 0xa0d1… (HYPE), 0x1457978f… (HYPE).
- Pour chacun : son coin principal ; série horaire « le compte ouvre-t-il au moins une position sur ce coin pendant l'heure H ? ».
- Variables connues au début de H : r1, r6, r24 (rendements), dd24 (écart au plus haut 24 h), heure UTC, « a ouvert en H-1 ».
- Découpage **temporel** : les 70 % premières heures pour l'entraînement, les 30 % dernières pour le test (jamais vues).
- Modèle : arbre de profondeur ≤ 2, appris sur l'entraînement seulement, avec des feuilles d'au moins 10 heures.
- Témoins : taux de base de l'entraînement ; « comme l'heure d'avant » (taux observés à l'entraînement après une heure avec ou sans ouverture).
- **Mécanicité = skill de Brier sur le test** : 1 − Brier(arbre) / Brier(meilleur témoin).
- **Critère** : « mécanique » si skill > 0,10 ET P(skill > 0) > 0,9 au bootstrap par blocs de 24 h. « Pas mécanique » sinon. Si un compte a moins de 10 heures avec ouverture dans le test, il est « indécidable ».
- Juge différé : pour les comptes jugés mécaniques, l'arbre figé est rejugé sur les 7 jours suivants (en direct, sur la VM).

## Amendement n°1 (2026-10-18, 20:35, avant le passage n°2)
Le passage n°1 était surtout indécidable : trop peu d'ouvertures dans le test, à cause de la limite de 2000 fills. Pour le passage n°2, l'historique est **paginé** avec userFillsByTime (en remontant le temps, jusqu'à 10 000 fills ou 60 jours par compte). Comptes, variables, modèle, découpage 70/30, témoins et critère sont **inchangés**.
