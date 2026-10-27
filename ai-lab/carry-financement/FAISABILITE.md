# Faisabilité sur le compte Kraken de Tony (27/10/2026 20h00)

Vérifiée sur l'API publique `derivatives/api/v3/instruments` + tickers. Compte : environ 5,90 $.

| Contrat | pas minimal | valeur minimale |
|---|---|---|
| BTC | 0,0001 | ~8,06 $ |
| BNB | 0,01 | ~7,49 $ |
| ETH | 0,001 | ~2,34 $ |
| XRP | 1 | ~1,32 $ |
| LINK | 0,1 | ~1,15 $ |
| SOL | 0,01 | ~1,01 $ |
| LTC | 0,01 | ~0,57 $ |
| ADA | 1 | ~0,21 $ |
| DOT | 0,1 | ~0,10 $ |
| AVAX | 0,01 | ~0,09 $ |
| DOGE | 1 | ~0,08 $ |

- La marge initiale est de 1 à 2 % : la taille n'est pas limitée par la marge, **elle est limitée par le risque**.
- Le pire repli du backtest Binance (PREREG-25) est de −73 % du montant engagé par côté. Pour que ce repli ne vide pas un compte de 5,90 $, il faut au plus **~8 $ par côté, soit ~2,7 $ par position**.
- À 2,7 $ par position, **BTC, BNB et ETH ne sont pas tradables** (minimum au-dessus, ou arrondi trop grossier). Il faudrait une version à 8 contrats, qui n'a pas été testée.
- Conclusion : même si le test papier confirme, la version testée n'est pas exécutable proprement avec 5,90 $. Il faudrait soit plus de capital (~25 $ pour tous les contrats à ~8 $ par position), soit pré-enregistrer et tester la variante sans BTC/BNB/ETH avant de s'en servir.
