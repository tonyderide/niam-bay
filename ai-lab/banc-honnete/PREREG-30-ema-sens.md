# Pré-enregistrement 30 : la règle de Tony, avec le sens donné par l'EMA
Écrit le 29/10/2026 à 21h4x, avant tout calcul de cette règle. Demande de Tony : « si on avait regardé l'EMA ». L'idée : au lieu de changer de sens après une perte, on ne prend que le sens de la tendance.
La famille compte déjà 7 tests sur l'EMA. Tous sont PERD, ÉCHEC, NON DÉMONTRÉ ou INDÉCIDABLE (registre, lignes 25 à 62). On attend donc un échec, et le test est loyal quand même.

## Règle
- **Sortie :** celle de Tony (addendum B de PREREG-28) :
  - un SL fixe à s ;
  - dès +a, un trailing à t ;
  - toujours en position, sans levier au-delà de 10 × le capital ;
  - frais taker de 0,05 % par côté.
- **Sens de chaque nouveau trade :** **long** si la dernière clôture horaire **terminée** est au-dessus de son EMA(N) horaire, **short** si elle est dessous. Il n'y a pas d'autre inversion. La règle ne regarde pas le futur : l'EMA est calculée sur les heures terminées avant l'entrée.
- **Réglages :**
  - N ∈ {20, 50, 200} ;
  - les 156 combinaisons (s, a, t) de PREREG-28 B ;
  - soit 468 réglages.
- **Mises :**
  - **(i)** mise fixe : 10 € de risque sur 1 000 € ;
  - **(ii)** martingale plafonnée : ×2 après une perte, au plus 3 doublements, puis retour à 10 €.

## Données, choix, jugement
- **Données :** bougies 1 min, vérifiées SHA-256.
- **Choix :** sur BTCUSDT 2024-2025, le réglage qui a la meilleure espérance par trade (en mises), avec la mise (i). Il est figé.
- **Jugement unique, sur trois terrains :** BTC 2026, ETH 2024-01 → 2026-09, SOL 2024-01 → 2026-09.

## Témoin
Même règle, mêmes sorties, mais **sens tiré à pile ou face**, avec la même proportion de longs que la règle EMA, sur 200 tirages. p = part des tirages qui font une espérance au moins aussi bonne. Ce témoin mesure si l'EMA apporte quelque chose de plus qu'un sens au hasard.

## Rapporté
- Pour chaque terrain : espérance par trade, total avec la mise (i), gains bruts contre frais, part des mois positifs (capital remis à 1 000 € chaque mois) avec (i) et (ii), pire mois.
- Le krach du 10/10/2025 sur SOL rejoué avec le réglage figé.

## Verdict
- **GAGNE** si les trois terrains ont une espérance > 0, des gains bruts > frais, et p < 0,05 contre le témoin.
- **NON DÉMONTRÉ** si au moins un terrain est > 0 sans tout le reste.
- **PERD** sinon.

## Relecture d'équité, avant le calcul
- Les frais sont les mêmes que pour le témoin.
- Le réglage le plus favorable est choisi sur BTC.
- La bougie ambiguë compte en SL (pessimiste), mais à 1 min c'est rare.
- L'EMA horaire ne voit que des heures terminées : pas de fuite.
