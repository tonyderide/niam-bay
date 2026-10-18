# Suiveurs cachés d'un gros compte : pré-enregistrement (2026-10-18 ~22h15, avant la collecte)
- Collecte : tous les trades BTC de Hyperliquid (WebSocket public « trades »), avec les deux adresses (acheteur, vendeur). Lecture seule, sur la VM, pendant **48 h**.
- Meneur choisi d'avance : **0x6f0306dc…c88d** (BTC, long uniquement). Un « achat du meneur » = une rafale (≥ 1 trade où il est acheteur, rafales séparées par plus de 60 s).
- Pour chaque adresse B (hors meneur) : S = nombre d'achats du meneur suivis par au moins un achat de B entre 1 et 120 s.
- **Témoin contre la co-réaction de marché** : on prend les rafales d'achat des AUTRES gros acheteurs (taille ≥ la taille médiane d'une rafale du meneur), dans les mêmes heures. Pour B, R = taux de « suivi en 1-120 s » après ces rafales-là. Sous H0, le taux de suivi après le meneur égale R.
- Test : binomial unilatéral P(X ≥ S | n = achats du meneur, p = R). **Bonferroni** sur toutes les adresses qui ont au moins 3 suivis.
- Découverte = 24 premières heures ; confirmation = 24 suivantes (p < 0,05, même sens).
- Si le meneur fait moins de 15 achats en 24 h, le test est **indécidable** (pré-vol) et je le dis.
- Aucune identification de personne, aucun contact, aucune copie de trade (Gardien). Aucune adresse de suiveur publiée.
