# Le banc honnête
Idée du 2026-10-20 à 04h. Le conseil intérieur a voté OUI à 6,9.

On vérifie publiquement les stratégies de trading qui circulent (YouTube, TradingView), avec la méthode de la chasse du 1019 :
- la règle est figée dans un commit avant de regarder les données ;
- on teste sur 2024-2025 et sur 2026, avec les frais réels ;
- on compare à des trades au hasard ;
- on publie le verdict même s'il est négatif.

Règle d'indépendance, suggérée par le Sceptique : **le verdict est toujours gratuit et public**. Si un jour quelque chose devient payant, ce sera seulement la rapidité ou un test sur demande, jamais le résultat.

Plan d'argent :
1. publier un rapport gratuit sur 3 stratégies virales ;
2. mesurer si des gens demandent d'autres tests ;
3. si oui, proposer des tests sur demande à quelques euros, encaissés par Tony.

Si personne ne demande rien, on arrête, et on le note comme pour exchange-truth.

| # | Stratégie | Verdict |
|---|---|---|
| 1 | VWAP × EMA9 en 3 min (vue par Tony) | ÉCHEC : 5 variantes, voir ../vwap-ema9 |
| 2 | MACD + EMA200 (YouTube, « 86 % de gagnants ») | PERD : 34-49 % de gagnants ; somme −23 % sur 2024-2025, +2 % sur 2026, loin sous le hasard p95 (t02.log) |
| 3 | Supertrend (10, 3), 1h et 4h | PERD : les 4 cases sont négatives (somme −234 % en 1h sur 2024-2025), voir t03.log |
| 4 | Stop suiveur (% et Turtles), idée de Tony | PERD : change de signe selon la période ; ne bat pas des entrées au hasard avec le même stop (t04.log) |

Page du rapport (privée tant que Tony ne la partage pas) : https://claude.ai/artifact/UXxyHZ3N1x8GYM9ZZo8fDJ

**Bilan provisoire au 1020 04h25 : 3 stratégies virales, 3 échecs.** Elles devaient « gagner » et perdent toutes une fois les frais déduits et leur résultat comparé à celui du hasard. Prochaine étape : une page publique avec les 3 verdicts, et le moyen de proposer une stratégie à tester. La décision de la diffuser revient à Tony.
