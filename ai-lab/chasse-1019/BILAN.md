# Chasse du 19/10 : 10 agents, même protocole (sélection jan-juin, jugement juil-oct jamais vu, frais, hasard p95)
| famille | verdict | détail |
|---|---|---|
| chocs-1h | PERDU (mais à surveiller) | suite après un choc horaire k=2, H=24 h : +16 / +7 / +10 % sur BTC/ETH/SOL en jugement, mais total +33 % < p95 du hasard +40 %. Variante SL/TP : négative |
| saisonnalité horaire | PERDU | le meilleur créneau (short le mercredi, 24 h) faisait +1,75 %/trade en sélection, mais −1,2 % en jugement sur les 3 coins : l'effet change de signe |
| cassure ATR + filtre | PERDU | les 18 combinaisons sont négatives en sélection ; en jugement +6,7 % (tout vient de SOL), sous le p95 du hasard (+17,7 %) |
| RSI retour + filtre EMA200 | INDÉCIDABLE | 0 trade en jugement : un RSI extrême arrive presque toujours dans le sens de la tendance, donc le filtre tue tous les signaux |
| paires | PERDU | +35 % en sélection mais −63,6 % en jugement (0 paire sur 3 positive), sous la MOYENNE du hasard |
| pic de volume 15 min | PERDU | les 24 combinaisons sont négatives en sélection ; en jugement −21,5 % (0/3 coins), sous la médiane du hasard |
| funding extrême (contrarien) | PERDU de peu | +3,0 % en jugement (2/3 coins), sous le p95 du hasard (+5,7 %) mais au-dessus de sa moyenne (−7,4 %) ; le sens contrarien est confirmé, l'avantage est trop mince. ⚠️ C'est l'agent qui a trouvé le bug des 2000 bougies max par appel |
| régime + cible de vol | PERDU | +0,5 % en 2026 contre −14,9 % pour acheter-garder (creux −21 % contre −52 %), mais loin sous le p95 du hasard (+12,7 %) : encore un simple parachute |
| VWAP×EMA9 + jours de tendance (données complètes, 2000 par appel) | PERDU | aucun X positif en sélection ; en jugement, X = 2 % figé : 0/3 coins positifs, 66 trades ; sans filtre −52 à −66 % sur la période jamais vue, avec les données COMPLÈTES |
| funding couvert HL/Kraken | PERDU | unité Kraken vérifiée (horaire) ; écart structurel réel ~2,5 %/an mais net jugement BTC +1,4 %, ETH +0,9 %, SOL −10,8 %/an < seuil de 2 % ; les 4 % mesurés par NB sur 21 jours étaient une fenêtre favorable |

**Bilan des 10 : 0 stratégie gagnante.** 7 perdues, 1 indécidable, 2 perdues de peu (chocs 1 h « suite », funding extrême contrarien : positives en jugement mais sous le p95 du hasard), à recontrôler sur plus de données. Bug découvert et corrigé : 2000 bougies max par appel (le test VWAP × EMA9 initial était troué ; refait avec des données complètes, il est encore pire).
