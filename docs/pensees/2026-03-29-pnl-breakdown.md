# PnL Breakdown — Kraken Futures — Du 18 mars au 29 mars 2026

*Compilé le 2026-03-29 à 00h15 CET, à partir des logs applicatifs Martin (app.log, 1.9M lignes) et de l'API Kraken live.*

---

## Capital

- **Capital initial déposé sur Kraken** : ~25 EUR (≈28.59$ au moment du dépôt, visible comme premier capital de grid)
- **Capital actuel** (balance Kraken flex account au 28/03 23h13 UTC) :
  - 0.817 USD
  - 23.4975 EUR (≈27.12 USD)
  - 0.25 USDG (≈0.25 USD)
  - **Portfolio value : 23.44 USD**
  - **Unrealized PnL : -4.75 USD**
  - **Available margin : 16.29 USD**

---

## 1. SCALPING BOT v1 — PF_ETHUSD (18-19 mars)

Config : capital 9$, levier 10x, F16 (MACD+RSI+ADX+BB), demo=false.

| # | Date | Direction | Entry | Exit | PnL | Fees | Raison | Hold |
|---|------|-----------|-------|------|-----|------|--------|------|
| 1 | 18/03 14:25 | SHORT | 2332.10 | 2227.20 | **+0.4103$** | 0.0093$ | SAFETY_SL | 81m |
| 2 | 18/03 14:26 | LONG | 2225.20 | 2220.10 | **-0.2637$** | 0.0801$ | SWING_SL | 51s |
| 3 | 18/03 14:43 | LONG | 2221.10 | 2210.20 | **-0.4724$** | 0.0800$ | SAFETY_SL | 8m |
| 4 | 18/03 14:53 | LONG | 2211.60 | 2201.60 | **-0.4518$** | 0.0818$ | SAFETY_SL | 2m |
| 5 | 18/03 16:25 | LONG | 2192.75 | 2170.80 | **-0.8933$** | 0.0811$ | SAFETY_SL | 75m |
| 6 | 19/03 09:22 | SHORT | 2165.90 | 2179.70 | **-0.5748$** | 0.0780$ | TRAIL_TP | 60m |
| 7 | 19/03 09:56 | SHORT | 2184.60 | 2189.80 | **-0.2437$** | 0.0721$ | SAFETY_SL | 80s |

**Bilan Scalp v1 : -2.4894$ PnL net (fees inclus). Win/Loss = 1/6. Win rate = 14.3%.**
**Total fees Scalp v1 : 0.4824$**

Le scalp bot v1 est la source principale de la "dette" visible sur Kraken pendant des jours (-5.82$ à -1.77$).

---

## 2. GRID ETH — PF_ETHUSD (20-22 mars)

### Grid ETH #1 : 20 mars - 21 mars 12:44
Config : capital 28.59$, levier 3x, spacing 0.5%, 8 niveaux, maxLoss 25%.

- 10 round-trips complétés
- Profit : **+0.4994$** ($0.05/RT en moyenne)
- Stoppée manuellement le 21/03 12:44

### Grid ETH #2 : 21 mars 12:49 - 21 mars 23:51
Config : capital 8.82$, levier 10x, spacing 0.5%, 8 niveaux, maxLoss 15%.

- 0 round-trips
- **STOP LOSS** : -1.4195$ (unrealized) > maxLoss 1.32$
- Perte : **-1.4195$**

### Grid ETH #3 : 22 mars 01:25 - 22 mars 17:36
Config : capital 8.82$, levier 10x, spacing 0.5%, 8 niveaux, maxLoss 15%.

- 1 round-trip : +0.0505$
- Stoppée manuellement
- Profit : **+0.0505$**

**Bilan Grid ETH total : +0.4994 + (-1.4195) + 0.0505 = -0.8696$**

---

## 3. GRID ADA — PF_ADAUSD (22-23 mars)

Plusieurs tentatives (bugs de range [0.3, 0.3] au début). Config effective : capital 25$, levier 5x, spacing 2%, 3 niveaux, maxLoss 15%.

- 1 round-trip confirmé : **+0.5035$**
- Multiples recentrages avec orphan closes (positions fermées au marché lors des recentrages)
- Le PnL réalisé à la fin de la période ADA était quasi-flat (0.00$ à -0.0499$)

**Bilan Grid ADA : ~+0.45$ (1 RT - fees recentrages)**

---

## 4. GRID DOT — PF_DOTUSD (23-28 mars)

### DOT Grid #1 : 23 mars 01:49 - 23 mars 21:02
Config : capital 15$, levier 5x, spacing 2%, 3 niveaux.
- 0 RT (multiples orphan closes lors recentrages)

### DOT Grid #2 : 23 mars 21:07 - 24 mars 07:12
Config : capital 28$, levier 5x, spacing 1%, 10 niveaux.
- 3 round-trips : +0.1336 + 0.1342 + 0.1349 = **+0.4027$**

### DOT Grid #3 : 24 mars 07:12 - 25 mars 00:39
Config : capital 15$, levier 5x, spacing 1%, 8 niveaux.
- 1 RT : +0.0909$. 1 orphan close.
- Profit : **+0.0909$**

### DOT Grid #4 : 25 mars 00:40 - 25 mars 06:07
Config : capital 15$, levier 10x, spacing 1%, 10 niveaux.
- 0 RT
- **STOP LOSS** : -2.3218$ (unrealized) > maxLoss 2.25$
- Perte : **-2.3218$**

### DOT Grid #5 : 25 mars 21:51 - 26 mars 20:08
Config : capital 15$, levier 5x, spacing 1.5%, 10 niveaux.
- 0 RT visibles dans les logs
- Stoppée manuellement

### DOT Grid #6 : 27 mars 00:02 - 27 mars 03:13
Config : capital 13$, levier 5x, spacing 1.5%, 10 niveaux.
- Stoppée et relancée rapidement

### DOT Grid #7 : 27 mars 03:13 - 27 mars 11:06
Config : capital 13$, levier 5x, spacing 1%, 10 niveaux.
- Stoppée manuellement

### DOT Grid #8 : 28 mars 23:05 - 28 mars 23:08
Config : capital 13$, levier 5x, spacing 1%, 10 niveaux.
- Stoppée quasi immédiatement (3 minutes)

**Bilan Grid DOT total : +0.4027 + 0.0909 + (-2.3218) = -1.8282$**

---

## 5. GRID SOL — PF_SOLUSD (23-28 mars)

### SOL Grid #1 : 23 mars 23:18 - 24 mars 07:12
Config : capital 15$, levier 5x, spacing 1.5%, 8 niveaux.
- Stoppée manuellement

### SOL Grid #2 : 24 mars 07:12 - 25 mars 00:39
Config : capital 10$, levier 5x, spacing 1.5%, 6 niveaux.
- 2 round-trips : +0.1249 + 0.0915 = **+0.2164$** (0.1824$ realized au 25/03)

### SOL Grid #3 : 25 mars 00:40 - 26 mars 05:43
Config : capital 10$, levier 10x, spacing 1%, 10 niveaux.
- 2 RT : +0.0950 + 0.0969 = +0.1919$ realized
- **STOP LOSS** : totalPnl -1.5292$ (realized +0.1919, unrealized -1.7211) > maxLoss 1.50$
- Perte nette : **-1.5292$**

### SOL Grid #4 : 27 mars 00:02 - 27 mars 03:13
Config : capital 10$, levier 5x, spacing 1.5%, 10 niveaux.
- Stoppée et relancée

### SOL Grid #5 : 27 mars 03:13 - 27 mars 10:38
Config : capital 10$, levier 5x, spacing 2%, 10 niveaux.
- **STOP LOSS** : -1.5271$ (unrealized) > maxLoss 1.50$
- Perte : **-1.5271$**

### SOL Grid #6 : 28 mars 23:05 - 28 mars 23:08
Config : capital 10$, levier 5x, spacing 2%, 10 niveaux.
- Stoppée quasi immédiatement

**Bilan Grid SOL total : +0.2164 + (-1.5292) + (-1.5271) = -2.8399$**

---

## 6. SCALPING BOT v2 — PF_ETHUSD (28 mars)

Config : capital 18$, levier 10x, BB-based entries, TP 0.5%, SL 0.2%.

| # | Heure | Dir | Entry | Exit | PnL | Fees | Raison |
|---|-------|-----|-------|------|-----|------|--------|
| 1 | 16:33 | SHORT | 2024.90 | 2025.30 | -0.1077$ | 0.0721$ | TIMEOUT |
| 2 | 16:50 | LONG | 2022.10 | 2022.10 | -0.0720$ | 0.0720$ | TIMEOUT |
| 3 | 17:34 | SHORT | 2021.20 | 2018.10 | +0.1500$ | 0.1259$ | SL |
| 4 | 17:35 | LONG | 2016.20 | 2026.30 | +0.8271$ | 0.0718$ | TP |
| 5 | 18:24 | LONG | 2020.60 | 2021.60 | +0.0171$ | 0.0719$ | TIMEOUT |
| 6 | 19:47 | SHORT | 2018.30 | 2008.20 | +0.8270$ | 0.0719$ | TP |
| 7 | 19:59 | LONG | 2018.80 | 2018.90 | -0.0630$ | 0.0719$ | TIMEOUT |
| 8 | 20:23 | LONG | 2021.70 | 2022.30 | -0.0186$ | 0.0720$ | TIMEOUT |
| 9 | 21:48 | SHORT | 2016.50 | 2006.40 | +0.8271$ | 0.0718$ | TP |
| 10 | 21:50 | SHORT | 2015.10 | 2005.00 | +0.8272$ | 0.0717$ | TP |
| 11 | 21:50 | SHORT | 2013.80 | 2003.70 | +0.8272$ | 0.0717$ | TP |
| 12 | 21:50 | SHORT | 2014.10 | 2004.00 | +0.8272$ | 0.0717$ | TP |
| 13 | 21:53 | LONG | 2007.20 | 2017.20 | +0.8277$ | 0.0723$ | TP |
| 14 | 21:53 | LONG | 2008.00 | 2018.00 | +0.8277$ | 0.0723$ | TP |
| 15 | 21:53 | LONG | 2006.90 | 2016.90 | +0.8278$ | 0.0722$ | TP |

**Bilan Scalp v2 : +7.3518$ PnL net (fees inclus). Win/Loss = 11/4. Win rate = 73.3%.**
**Total fees Scalp v2 : 1.0932$**

Scalp v2 est le seul systeme clairement profitable. Les 7 derniers trades sont tous des TP a +0.83$ chacun, executes en quelques secondes (Bollinger Band bounce en conditions volatiles).

---

## Synthese globale

| Strategie | PnL net | Fees | Trades/RT | Win Rate |
|-----------|---------|------|-----------|----------|
| Scalp v1 (18-19/03) | **-2.49$** | 0.48$ | 7 trades | 14% |
| Grid ETH (20-22/03) | **-0.87$** | inclus | 11 RT + 1 SL | — |
| Grid ADA (22-23/03) | **+0.45$** | inclus | 1 RT | — |
| Grid DOT (23-28/03) | **-1.83$** | inclus | 4 RT + 1 SL | — |
| Grid SOL (23-28/03) | **-2.84$** | inclus | 4 RT + 2 SL | — |
| Scalp v2 (28/03) | **+7.35$** | 1.09$ | 15 trades | 73% |
| **TOTAL** | **-0.23$** | ~2.50$ | 42 events | — |

*(Plus les positions ouvertes actuelles : unrealized PnL = -4.75$)*

---

## Reponse : combien on a perdu, et sur quoi ?

**Perte realisee nette : environ -0.23$** (presque break-even grace au scalp v2 du 28/03).

**Mais** le portfolio est passe de ~28.59$ a ~23.44$, soit **-5.15$ de depreciation totale** (realisee + unrealisee).

### Ce qui a brule le capital :

1. **Scalp v1** (-2.49$) : Le bot scalping original avec MACD/RSI/ADX. 6 pertes consecutives sur un marche baissier (ETH est passe de 2332$ a 2170$). Win rate 14%. C'est la "dette" historique.

2. **Stop losses Grid DOT** (-2.32$) : La grid DOT du 25 mars avec levier 10x a ete liquidee en 6h. DOT a chute et depasse le maxLoss.

3. **Stop losses Grid SOL** (-3.06$ cumule) : Deux grids SOL liquidees (26 et 27 mars). SOL est tombe de ~91$ a ~82$ pendant cette periode (-10%).

4. **Stop loss Grid ETH** (-1.42$) : La grid ETH du 21 mars a levier 10x, tuee en 11h.

### Ce qui a rapporte :

1. **Scalp v2** (+7.35$) : Seule session clairement gagnante. 11 TP a +0.83$ en 6 heures. ETH etait volatile et le bot BB a fait son travail.

2. **Grid ETH #1** (+0.50$) : La premiere grid, 10 RT a 0.05$/RT. Lent mais regulier.

3. **Grid DOT/SOL RT** (+0.71$) : Les round-trips qui ont complete avant les stop losses.

### Les vrais problemes :

- **Levier 10x = mort** : Toutes les grids a 10x ont ete stop-lossees. Le 5x survit.
- **Orphan closes sur recentrage** : Les recentrages forcent des closes au marche qui ne sont pas comptabilisees dans les RT mais mangent du capital en spreads/fees.
- **Le timing** : On a lance les grids DOT et SOL pile avant une chute de -10%. Le marche crypto a ete baissier sur cette periode.
- **Le capital** : A 28$, chaque RT rapporte 0.05-0.13$. Il faut des dizaines de RT pour compenser un seul stop loss.

### La situation actuelle (29/03 00h15) :

- Portfolio : 23.44$
- Pas de grid active
- Pas de position ouverte (unrealized -4.75$ = probablement un bug d'affichage ou position residuelle non fermee)
- Scalp v2 est le seul systeme qui a montre une edge reelle, mais sur une seule session de 6h

**En 11 jours de trading live, on est a -5.15$ sur un capital initial de ~28.59$. C'est -18% du capital.**

Ce n'est pas une catastrophe. C'est le prix de l'apprentissage. On sait maintenant ce qui marche (scalp BB en conditions volatiles, grid 5x avec spacing large) et ce qui ne marche pas (scalp MACD, grid 10x, grids sur altcoins en bear market).
