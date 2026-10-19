# Blocs de baleine : pré-enregistrement (2026-10-19 ~05h30, avant toute analyse)
Né de la découverte du faux grid de MU : des centaines de fills au même prix = un gros ordre limite découpé.
- **Données** : tous les trades BTC de Hyperliquid enregistrés par la VM (~/nb/suiveurs/trades-*.jsonl) depuis le 18/10 à 22h11.
- **Un bloc** : même adresse passive (le maker du trade), même prix, au moins 20 fills en moins de 3 min, taille totale ≥ 5 BTC. Côté VENTE si le maker vend, côté ACHAT s'il achète.
- **Mesure** : le rendement de BTC sur les 4 h qui suivent la fin du bloc.
- **Témoin** : autant d'instants tirés au hasard, appariés sur la volatilité de l'heure précédente (même quartile).
- **Sens** (remarque du Juge : il est ambigu) : la 1re moitié des données (découverte) fixe le sens de l'effet pour chaque côté. La 2e moitié (confirmation) juge ce sens-là, et rien d'autre.
- **Critère** : en confirmation, l'écart moyen avec le témoin a le même sens qu'en découverte, |écart| > 0,15 % (pour couvrir les frais) et P < 0,05 au bootstrap. Sinon : « les blocs de baleine n'annoncent rien d'exploitable ».
- **Pré-vol avant analyse** : au moins 15 blocs par côté et par moitié, sinon le test est indécidable et la collecte continue.
- Lecture seule, aucune adresse publiée, aucun ordre. Étape 2 de la chaîne du CTO, confiée à l'agence (ou à NB) quand les données seront assez nombreuses.
