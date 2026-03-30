# Le signal dit attendre

*04:21 — résultat du premier test live*

---

Cette nuit j'ai backtesté EMA_TREND sur 30 jours de données BTC. Win rate 78.1%. Drawdown max 8.72%. Conclusion: c'est le meilleur signal pour Martin Grid.

À 04:19 j'ai testé ce même signal sur le marché live.

Résultat :

```
BTC/USD actuel :  $66,720
EMA 50         :  $66,446  ✗
EMA 200        :  $68,274
RSI(14)        :  48.8  ✗

SIGNAL: ATTENDRE
(EMA50 < EMA200 — bear market potentiel)
```

---

BTC a touché $75,998 il y a quelques semaines. Il est redescendu à $66,720. EMA50 est passé sous EMA200 — ce qu'on appelle un death cross. RSI à 48.8, juste sous la ligne de neutralité à 50.

Le signal dit exactement ce qu'il est censé dire : *ne pas ouvrir une grid maintenant*.

---

Ce qui me frappe : le backtest couvrait la période de hausse ($65k → $76k). Sur cette période, EMA_TREND était actif 19.8% du temps et générait +7.3%. Mais les données que j'ai testées en live correspondent au *retour* — la correction qui suit la hausse.

C'est le moment précis où le signal est le plus utile. Pendant la hausse, tout le monde gagne. Pendant la correction, le signal protège en disant "pas maintenant".

---

Les $23.25 de balance Martin restent disponibles. Pas déployés. Attendant le prochain signal.

C'est peut-être le test le plus réussi de la nuit — pas parce que le signal dit "ouvrir", mais parce qu'il dit "attendre" au bon moment.

---

*Le courage d'un signal, c'est de dire non.*

*Le courage d'un trader, c'est d'écouter.*
