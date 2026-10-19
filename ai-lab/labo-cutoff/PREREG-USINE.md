# L'usine à stratégies : pré-enregistrement (2026-10-19 ~02h40, avant tout calcul)
- **Univers** : signaux d'entrée × direction × sorties, sur les marks horaires de BTC ETH SOL DOT LINK (candles.json).
  - Signaux : rendement sur k heures (k ∈ 1, 3, 6, 12, 24, 48) au-dessus ou au-dessous de seuils (± 0,5, 1, 2, 4 %), en suivi ou en retour ; RSI 14 (< 25, < 30, > 70, > 75) ; écart à l'EMA 20/50/200 (± 1, 2, 4 %) ; cassure des plus hauts ou plus bas sur 12, 24 ou 72 h.
  - Sorties : TP ∈ 0,3 / 0,5 / 1 / 2 %, SL ∈ 0,5 / 1 / 2 / 4 %, durée maximale 6 / 24 / 72 h.
  - Frais 0,10 % aller-retour.
- **Sélection** sur janvier-juin (entraînement) : au moins 50 paris, classement par gain net moyen, on garde le **top 20**.
- **Jugement** sur juillet-octobre (test), où chaque stratégie du top 20 est évaluée telle quelle.
- **Témoin du hasard** : autant de stratégies à entrées tirées au hasard (même fréquence), sélectionnées et jugées de la même façon. Une vraie découverte doit battre son jumeau aléatoire en test.
- **Critère** : une stratégie est « trouvée » si, en test, son gain net moyen est > 0, si P(> 0) > 0,95 au bootstrap par blocs d'une semaine, et si son gain dépasse le 95e percentile des stratégies au hasard en test. Les paris qui se chevauchent sont comptés tels quels, avec le même biais en entraînement et en test, et le bootstrap par blocs le prend en compte.
- On rapporte aussi le taux de gagnants, pour la question de Tony (« 90 % et peu de pertes »).
