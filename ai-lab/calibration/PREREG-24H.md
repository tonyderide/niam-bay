# Calibration directionnelle à 24 h : pré-enregistrement (2026-10-17, avant la 1re prédiction)
- Famille unique : « le mark Kraken Futures de X sera-t-il PLUS HAUT dans 24 h qu'au moment de la prédiction ? ». X ∈ {BTC, ETH, SOL, DOT, LINK}, soit 5 par nuit.
- p est donné par moi (NB, Opus) après avoir regardé les données, avec une raison d'une ligne. Rien n'est effacé ni modifié après coup.
- Témoins calculés automatiquement sur les mêmes questions : (a) p = 0,5 ; (b) momentum naïf : p = 0,55 si les dernières 24 h sont en hausse, 0,45 sinon.
- Taille : **70 prédictions** (14 nuits), évaluation le 2026-10-31.
- **Critère** : mon jugement « vaut quelque chose » si mon Brier est inférieur à CHACUN des deux témoins d'au moins 0,005 ET si le bootstrap (10 000 tirages) donne P(mon Brier < témoin) > 0,9 face aux deux. Sinon, conclusion écrite : mon jugement directionnel à 24 h ne bat pas le hasard, donc **pas d'augmentation de taille de position** sur cette base.
