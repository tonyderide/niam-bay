# Suivi de tendance (horizon : semaines) : pré-enregistrement (2026-10-19 ~04h35, avant tout calcul)
Données : marks journaliers Kraken Futures, BTC ETH SOL DOT LINK, de 2024-01-01 à 2026-10-16. Frais : 0,10 % par changement de position, plus 0,01 %/jour de financement en position.
Règles, toutes figées (paramètres classiques de la littérature, aucun réglage) :
- **T1 EMA 50/200** : long si EMA50 > EMA200, sinon hors marché.
- **T2 EMA 50/200 long-short** : long si EMA50 > EMA200, short sinon.
- **T3 Donchian 20/10** : on entre long si la clôture dépasse le plus haut de 20 jours, on sort si elle passe sous le plus bas de 10 jours. Symétrique en short.
- **T4 Donchian 55/20** : comme T3, avec 55 et 20 jours (la « tortue » classique).
- **T5 momentum 3 mois** : long si le rendement sur 90 jours est > 0, sinon hors marché. Revu chaque semaine.
Témoins : (a) acheter et garder ; (b) 1000 stratégies au hasard avec le même temps passé en position.
Juge : **2024-2025 = sélection, 2026 = jugement** (période jamais utilisée pour choisir). Une règle « marche » si, sur 2026, son rendement est > 0 ET > acheter-garder ET > 95e percentile du hasard, ET si son pire creux est inférieur à celui d'acheter-garder. On rapporte aussi le taux de gagnants et le gain moyen d'un gagnant comparé à celui d'un perdant.

## Résultat (2026-10-19 ~04h45)
| règle | 2024-2025 (sélection) | 2026 (jugement) | pire creux 2026 | hasard p95 2026 |
|---|---|---|---|---|
| acheter-garder | +4,5 % | −17,3 % | −54 % | – |
| T1 EMA 50/200 long | −3,0 % | **+2,6 %** | **−11 %** | +12,5 % |
| T2 EMA 50/200 long-short | −28,3 % | −10,2 % | −44 % | +3,0 % |
| T3 Donchian 20/10 | −51,6 % | −5,9 % | −40 % | +8,8 % |
| T4 Donchian 55/20 | −20,3 % | −5,9 % | −29 % | +14,9 % |
| T5 momentum 3 mois | +21,9 % | −11,6 % | −26 % | +17,9 % |
**Aucune règle ne passe le critère.** La plus intéressante est T1 : en 2026, elle a évité l'essentiel de la baisse (+2,6 % contre −17,3 % pour acheter-garder, creux −11 % contre −54 %). Mais elle ne bat pas le hasard qui passe autant de temps en position (p95 +12,5 %) et elle perdait en 2024-2025. C'est un **parachute** (elle coupe les gros creux), **pas une machine à gagner**. T5, la meilleure en sélection, s'effondre en jugement : encore la chance de sélection.
