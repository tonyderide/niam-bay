# PREREG vwap-ema9-tendance (écrit avant tout calcul)
Données: Kraken Futures trade candles 1m (PF_XBTUSD, PF_ETHUSD, PF_SOLUSD), agrégées en 3m (alignées sur minute multiple de 3 UTC).
Signal: EMA9 des clôtures 3m vs VWAP de session (reset 00:00 UTC, prix typique (H+L+C)/3 pondéré volume). Croisement haussier -> long, baissier -> short, évalué à la clôture de la bougie 3m; entrée à l'open de la 3m suivante.
Sortie: SL 0,1 % (détecté intra-bougie via high/low, exécuté au prix SL), sinon croisement inverse (clôture à l'open suivant), sinon fin de journée UTC (open de la dernière bougie... clôture de 23:57). Pas de re-entrée après SL tant qu'aucun nouveau croisement.
Filtre tendance (sans futur): signal pris seulement si |close_signal/open_00:00UTC - 1| > X ET le signe du croisement = signe du rendement du jour (alignement). Les sorties ne sont pas filtrées.
Grille X sélectionnée sur 2026-01-01..2026-06-30: {0.3,0.5,0.75,1,1.5,2} %. Critère de sélection: rendement net total cumulé (somme des 3 coins) maximal, avec >= 60 trades sur la sélection; X figé ensuite.
Frais: 0,05 % par côté. SL: 0,1 % fixe (non optimisé).
Jugement: 2026-07-01..2026-10-16, X figé. Témoin: 300 tirages, même nombre de trades et mêmes durées de détention, instants d'entrée aléatoires, côté aléatoire, même SL 0,1 % et frais; comparer le total net par coin au p95.
GAGNE = en jugement net>0 sur >=2 coins/3 ET > p95 hasard (sur ces coins) ET >=30 trades (par coin considéré, total).
Rapport: trades, % gagnants, gain moyen net, total, pire creux (drawdown de la courbe cumulée).
Note: l'API renvoie max 2000 bougies/appel; fenêtre ajustée (pas d'impact sur règles).
