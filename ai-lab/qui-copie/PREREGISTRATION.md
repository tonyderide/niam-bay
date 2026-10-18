# Qui copie qui sur Hyperliquid : pré-enregistrement (2026-10-18 ~22h05, avant toute donnée)
- Comptes : les comptes « robustes » du leaderboard (critère de la nuit du 17/10) qui ont au moins 5 fills sur les 6 dernières heures au moment de la collecte, 30 au maximum. Historique paginé, jusqu'à 10 000 fills ou 30 jours.
- Événement : une ouverture (dir commence par « Open ») d'un coin, dans un sens. Les ouvertures d'un même compte à moins de 60 s les unes des autres comptent pour UNE rafale.
- Paire orientée A→B, sur le même coin et dans le même sens : nombre de rafales de A suivies d'une rafale de B entre 1 et 120 s.
- **Asymétrie** (contre les chocs communs) : on compte aussi B→A. Une nouvelle commune produit les deux ordres, une copie un seul.
- **Null** : on décale toutes les rafales de B d'un même décalage aléatoire entre 1 h et 24 h (circulaire), 1000 fois. p = part des décalages qui donnent au moins autant de A→B.
- Découpage temporel : 1re moitié = découverte, 2e moitié = confirmation (jamais vue).
- **Critère d'une copie** : en découverte, A→B ≥ 10, A→B ≥ 3 × B→A et p < 0,05 / (nombre de paires testées) (Bonferroni). En confirmation, A→B ≥ 3 × B→A et p < 0,05.
- Pré-vol (ai-lab/prevol) sur le nombre de rafales avant d'interpréter. Je ne nommerai aucune paire en public. Pas de copie automatique, jamais : c'est de la mesure.
