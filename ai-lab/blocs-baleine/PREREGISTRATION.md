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

## Précisions d'exécution (27/10/2026 20h3x, AVANT d'avoir compté le moindre bloc)
- Données : `~/nb/suiveurs/trades-*.jsonl` sur la VM, du 18/10 22:11 au 27/10 vers 19:30 UTC (la collecte continue ; on fige la fin à l'heure de lancement du calcul).
- Teneur d'ordre (passif) : Hyperliquid donne `users = [acheteur, vendeur]` ; si `s == "B"` (l'acheteur a pris l'initiative), le passif est le vendeur, sinon l'acheteur.
- Bloc : fills consécutifs de la même adresse passive au même prix, avec moins de 3 min entre le premier et le dernier fill (la série est coupée dès qu'un fill tombe à plus de 3 min du premier), ≥ 20 fills, ≥ 5 BTC au total.
- Prix : dernier prix échangé à chaque minute. Rendement 4 h = prix(fin + 4 h) / prix(fin) − 1. Volatilité de l'heure précédente = écart-type des rendements minute des 60 minutes avant ; quartiles sur toutes les minutes de la période.
- Moitiés : découpage du temps en deux moitiés égales. Témoin : pour chaque bloc, un instant tiré au hasard dans la même moitié et le même quartile de volatilité (graine 19), en excluant les 4 dernières heures de données.
- Bootstrap : 10 000 tirages de la différence de moyennes (blocs − témoins), P = part des tirages dans le sens opposé à celui de la découverte.
