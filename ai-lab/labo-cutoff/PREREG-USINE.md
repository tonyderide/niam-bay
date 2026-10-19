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

## Résultat (2026-10-19 ~02h50)
- **31 584 stratégies réelles** testées, et 32 832 au hasard. **Stratégies trouvées selon le critère : 0.**
- Le top 20 de janvier-juin gagnait +0,90 % par pari en entraînement et **perd −0,68 % en test**. C'est PIRE que le top 20 du hasard (−0,08 % en test). Ce top 20 est presque entièrement fait de « shorts après une hausse » : ça marchait en janvier-juin (marché baissier) et ça a cassé en juillet-octobre (rebond).
- **318 stratégies dépassent 85 % de gagnants en test avec un gain positif** (par exemple BTC sous l'EMA200 de 2 %, long, TP 2 %, SL 4 % : 98 % de gagnants, +1,65 %/pari). **Toutes perdaient en janvier-juin** : c'est le « acheter les creux », qui ne paie que dans un marché qui remonte. C'est exactement le piège du 90 % : il dépend du régime du marché, pas de la stratégie.
- **Le seul candidat positif sur les deux périodes** : DOT, 4 % sous l'EMA20, long, TP 2 % / SL 2 % (entraînement +0,80 %, 58 paris ; test +0,69 %, 29 paris, 72 % de gagnants, P(>0) = 0,93). Il échoue de justesse au critère, et sur peu de paris. Trouvé parmi 31 584 stratégies, il peut être de la chance : à tester **en direct, sur papier, pré-enregistré**, avant d'y croire.
