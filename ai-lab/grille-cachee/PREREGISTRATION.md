# La grille cachée (recadrage ECDSA appliqué aux bots) : pré-enregistrement (2026-10-19 ~05h10)
Conseil : PAS MAINTENANT (5.82). Tony : « fais-le quand même, tu as vraiment envie ! ». Mon Cœur était à 8.
- Comptes : les 4 comptes « maker » (ordres limites ≥ 75 %) de ai-lab/jumeau/data/active_candidates.json. Coin principal, fills d'ouverture et de fermeture.
- Sur les 70 % premiers fills (dans le temps), on cherche le réseau qui explique le mieux les prix : **arithmétique** (o + k·s) ou **géométrique** (o·(1+s)^k). Le pas s est cherché parmi les écarts fréquents entre prix voisins.
- Tolérance : 1 tick (le plus petit écart non nul observé entre deux prix).
- **Juge** sur les 30 % suivants : la part des fills qui tombent sur le réseau, comparée au hasard (2 × tolérance / pas). Un réseau est « retrouvé » si cette part dépasse 3 fois le hasard ET 50 %.

## Amendement n°1 (05h12, avant le 2e passage)
Le 1er passage a « trouvé » le pas de cotation de l'exchange (1 tick), sur lequel tombent 100 % des prix, hasard compris : c'est trivial. Règle ajoutée : le pas doit valoir **au moins 5 ticks**. Le reste ne change pas.

## Résultat (05h14)
| compte | coin | pas trouvé | sur le réseau, entraînement | sur le réseau, TEST | hasard |
|---|---|---|---|---|---|
| 0x93c48e | xyz:MU | 3,75 (375 ticks) | **55 %** | **0 %** | 1 % |
| 0x9aaead | BTC | 595 (595 ticks) | 16 % | 0 % | 0 % |
| 0x0f4fbe | ZEC | 47,5 (475 ticks) | 30 % | 0 % | 0 % |
**Aucune grille n'est retrouvée.** Le cas le plus parlant est MU : 55 % des prix d'entraînement tombent sur un réseau de pas 3,75, soit 55 fois le hasard. Pourtant, **0 %** des prix suivants y tombent. Le réseau existe bien, mais **il bouge** : ces bots recentrent leur grille quand le prix part, comme le faisait le Martin local. L'analogie avec ECDSA s'arrête là : le générateur de NIST était figé, celui d'un bot se déplace. Pour aller plus loin, il faudrait chercher la règle de recentrage (la grille suit-elle le prix moyen ? avec quel délai ?), pas une grille fixe.

## La règle de recentrage (05h20) : ce n'était pas une grille
En suivant la grille dans le temps, la « grille de pas 3,75 » se révèle être **un artefact**. Le bot MU ne fait pas de grid. Il pose de **gros ordres limites de vente** (« Close Long », 100 % maker) en **blocs ronds** : 200, 550, 600, 300, 300 unités, à 1033 → 1036,5 → 1029 → 987 / 988,5 → 963,3. Chaque bloc est mangé en 1 à 2 minutes par des centaines de petits acheteurs, ce qui donne des centaines de fills **au même prix**. Comme 1036,5 et 1029 tombent tous deux sur 1,5 modulo 3,75, j'ai cru voir une grille.
**La vraie règle** : c'est un gros détenteur long qui **allège sa position par paliers pendant la baisse** (de 1036 à 963 en 4 jours), par blocs de taille ronde, puis qui finit en exécution continue (429 fills en 2 h, 114 prix différents, avec quelques rachats). Ce n'est pas un bot de grid à percer, c'est une sortie de position étalée.
Leçon : avant de chercher le réglage d'une machine, vérifier qu'il s'agit bien de cette machine-là. Des fills répétés au même prix, c'est la signature d'un **gros ordre découpé**, pas d'une grille.
