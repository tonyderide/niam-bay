# Suiveurs cachés d'un gros compte : pré-enregistrement (2026-10-18 ~22h15, avant la collecte)
- Collecte : tous les trades BTC de Hyperliquid (WebSocket public « trades »), avec les deux adresses (acheteur, vendeur). Lecture seule, sur la VM, pendant **48 h**.
- Meneur choisi d'avance : **0x6f0306dc…c88d** (BTC, long uniquement). Un « achat du meneur » = une rafale (≥ 1 trade où il est acheteur, rafales séparées par plus de 60 s).
- Pour chaque adresse B (hors meneur) : S = nombre d'achats du meneur suivis par au moins un achat de B entre 1 et 120 s.
- **Témoin contre la co-réaction de marché** : on prend les rafales d'achat des AUTRES gros acheteurs (taille ≥ la taille médiane d'une rafale du meneur), dans les mêmes heures. Pour B, R = taux de « suivi en 1-120 s » après ces rafales-là. Sous H0, le taux de suivi après le meneur égale R.
- Test : binomial unilatéral P(X ≥ S | n = achats du meneur, p = R). **Bonferroni** sur toutes les adresses qui ont au moins 3 suivis.
- Découverte = 24 premières heures ; confirmation = 24 suivantes (p < 0,05, même sens).
- Si le meneur fait moins de 15 achats en 24 h, le test est **indécidable** (pré-vol) et je le dis.
- Aucune identification de personne, aucun contact, aucune copie de trade (Gardien). Aucune adresse de suiveur publiée.

## Amendement n°1 (2026-10-18 22:34, AVANT toute analyse du flux collecté)
Pré-vol : 0x6f03 ne fait qu'environ 1,2 rafale d'achat BTC par jour, et la dernière date d'il y a ~85 h. Le test serait indécidable (seuil : 15 par 24 h).
Nouveau meneur, désigné par une règle mécanique : parmi les 30 comptes robustes de ai-lab/qui-copie, celui qui a le plus de rafales d'achat BTC par jour, c'est-à-dire **0x0b7879fdafb34632b6b92287158bbb8705cf11f0** (environ 1000000000.0 rafales par jour, 1 dans son historique). Le reste du protocole ne change pas. La collecte, qui ne dépend d'aucun meneur, a commencé à 22h11.

## Amendement n°2 (2026-10-18 22:34, toujours AVANT toute analyse)
L'amendement n°1 était faux : mon calcul divisait par une durée quasi nulle, et il avait désigné un compte qui n'a fait qu'**une seule** rafale (0x0b7879…). Règle corrigée : au moins 15 rafales, et une durée d'au moins 1 jour au dénominateur. Meneur : **0xe76fd4b0280512cce263595ef0d7fcbd101941d5**, avec 10,0 rafales d'achat BTC par jour (21 rafales sur 1.9 jours).
