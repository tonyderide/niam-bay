# Pré-enregistrement : croisements nets + filtre de tendance, 2024-2025
Figé le 2026-10-19 vers 19h30, avant tout téléchargement des données 2024-2025.

## Règle (aucun réglage ne sera changé après coup)
- Bougies de 3 minutes, construites à partir du 1m « trade » de Kraken.
- VWAP remis à zéro chaque jour à 00h UTC. EMA9 sur la clôture.
- Signal net : l'écart EMA9/VWAP vaut au moins 0,5 % et tient 5 bougies d'affilée.
- **Tendance de fond** : EMA200 des clôtures en 1 heure, calculée uniquement sur des heures closes (donc sans regarder le futur).
  - Un signal long n'est pris que si le prix est au-dessus de l'EMA200 1h. Un signal short n'est pris que s'il est en dessous.
  - Un signal net contre la tendance ferme la position et laisse à plat.
- Entrée et sortie à l'ouverture de la bougie suivante. Frais taker de 0,05 % par côté. Pas de SL.
- Marchés : BTC, ETH, SOL (PF_*). Période : 2024-01-01 au 2025-12-31. Les données sont paginées par tranches de 1 800 minutes au maximum.

## Critère de succès (tous requis)
1. Le total est > 0 sur les 3 marchés.
2. Sur chacun des 3 marchés, le résultat dépasse le 95e centile de 500 tirages au hasard. Chaque tirage reprend le même nombre d'entrées, le même temps en position et la même alternance long/short… ; version simple retenue : des entrées et sorties aux mêmes dates, mais avec un sens long ou short tiré au hasard.
3. Le résultat est positif sur chaque année (2024 et 2025) prise séparément, sur au moins 2 marchés sur 3.

À titre indicatif seulement (ces chiffres n'entrent pas dans le verdict) : acheter et garder, et la même règle sans filtre de tendance.

## Résultat (1019 ~20h, tendance2024.py → tendance2024.log)
| | Trades | Total | Hasard p95 | 2024 | 2025 | Sans filtre tendance (indicatif) | Garder (indicatif) |
|---|---|---|---|---|---|---|---|
| BTC | 972 | −44,7 % | −15,0 % | −5,2 % | −41,6 % | −37,6 % | +107 % |
| ETH | 1 321 | −39,9 % | −28,8 % | −10,5 % | −32,9 % | +32,1 % | +30 % |
| SOL | 1 768 | −86,1 % | −52,0 % | −76,9 % | −39,8 % | −81,3 % | +22 % |

**VERDICT : ÉCHEC** sur les 3 critères. Le filtre de tendance n'aide pas : il fait même pire que la même règle sans filtre. Le +20 % de juillet-octobre 2026 venait de la période, pas de la règle.
