# Darwin sweeps — synthèse 5 backtests (2026-05-10 nuit → 0511 02h)

**Auteur** : Niam-Bay (cycle 33, vacation J+2 Strasbourg)
**Statut** : Doc décisionnel — tu décides quoi déployer.
**Base** : 30 jours Binance 1min + 7 jours Binance 1sec, frais maker Kraken 0.04% × 2 = 0.08% RT, capital $46/pair, levier ×5, gate RSI[36-66]+ATR%[1.12-2.17].

---

## TL;DR — 3 trouvailles

1. **Les filtres volume liftent +1.5 à +7 pts de PnL** sur 30j. Aucun n'est dans le bot prod. C'est la trouvaille la plus actionable.
2. **La config déployée (sp=2.0% lvl=6) est largement sous-optimale** vs sp=3.0% lvl=4 avec filtre volume. Sur LINK : 2.80% baseline → 15.97% avec `spike_avoid_2x`. Lift ×5.7.
3. **SOL est faible.** Best config 1.09% / 30j vs ADA à 17.65%. **ADA mériterait de remplacer SOL** dans le trio.

---

## Récap des 5 sweeps (par ordre chronologique d'exécution)

| Sweep | Dimension | Données | Findings |
|---|---|---|---|
| `headless_search.py` (21:47) | Darwin évolutionnaire pop=30 gen=25 | Kraken OHLC 1h/4h | Pas reparsé ici — pré-existant 0408 |
| `grid_backtest_1min.py` (22:16) | Baseline 1min grid LINK/SOL/DOT | Binance 30j 1min | 5/4/4 RTs, +$0.74/RT |
| `comprehensive_sweep.py` (01:39) | spacing × levels × pairs | Binance 30j 1min | 7 spacings × 4 levels × 6 pairs = 168 configs |
| `volume_sweep.py` (01:42) | + filtres volume | Idem | 8 modes volume × 9 configs = 72 résultats |
| `advanced_sweep.py` (01:52) | + ATR dynamique, trend skip, asym, timeout | Idem | 12 variantes × 3 paires = 36 résultats |
| `sweep_1s.py` (02:09) | Tick précision 1s | Binance 7j 1sec | 63 résultats — validation top configs |

---

## Finding 1 : volume filters liftent +1.5 à +7 pts

`volume_sweep.py` teste 8 modes sur les configs candidates :

| Pair | Spacing | Levels | Baseline | Best mode | Best PnL% | **Lift** |
|---|---|---|---|---|---|---|
| ADA | 0.030 | 4 | 10.65% | `all3` (min_vol+spike_avoid+vwap) | **17.65%** | **+7.00** |
| LINK | 0.030 | 4 | 10.65% | `spike_avoid_2x` | 15.97% | +5.32 |
| DOT | 0.020 | 4 | 9.50% | `vwap+spike2x` | 14.10% | +4.60 |
| LINK | 0.020 | 6 (déployé) | 2.80% | `min_vol_1.0` | 6.07% | +3.27 |
| DOT | 0.020 | 6 (déployé) | 6.33% | `vwap+spike2x` | 9.40% | +3.07 |
| DOT | 0.010 | 4 | 11.41% | `vwap+spike2x` | 14.01% | +2.60 |

**Interprétation** :
- `spike_avoid_2x` = skip nouveau buy si vol > 2× moyenne 24h → évite d'acheter dans les pumps
- `vwap+spike2x` = centre la grille sur VWAP 4h + spike avoid → suit le « vrai » mid + filtre pump
- `all3` = combine min_vol_1.0 + spike_avoid_2x + vwap → ADA en raffole, DOT déteste (-36% sur DOT sp=0.02 lvl=6 — probable double filtre qui kill toute liquidité)

**Le filtre n'est pas universel** — chaque paire a sa préférence. Note critique : `all3` sur DOT casse tout.

## Finding 2 : 4 niveaux > 6 niveaux dans 5/6 paires

`comprehensive_sweep.py` montre dans le top 10 :
- 9 sur 10 sont **levels=4**, seul 1 est levels=6 (DOT sp=0.015 lvl=6 à 8.69%)
- Levels=8 et 10 n'apparaissent pas dans le top 20

**Hypothèse** : moins de niveaux = capital plus concentré sur les premiers niveaux qui se remplissent plus souvent. Plus de niveaux = capital étalé sur des niveaux qui ne se touchent jamais en 30j.

**Implication** : le bot prod tourne à `levels=6`. La gain potentiel en passant à `levels=4` est documenté ci-dessous (Finding 5).

## Finding 3 : SOL est marginal, ETH est mauvais

Best par paire (30j 1min comprehensive) :

| Pair | Best PnL% | Best config |
|---|---|---|
| DOT | 13.04% | sp=0.015 lvl=4 |
| LINK | 10.65% | sp=0.030 lvl=4 |
| ADA | 10.65% | sp=0.030 lvl=4 |
| BTC | 1.81% | sp=0.020 lvl=4 (marginal) |
| **SOL** | **1.09%** | sp=0.030 lvl=4 (proche zéro) |
| **ETH** | **-4.06%** | toutes configs négatives |

→ SOL et ETH sont les **mauvaises paires** sur la fenêtre 30j actuelle.

## Finding 4 : 1-second tick ne change pas la hiérarchie

`sweep_1s.py` (7j 1-sec, 604,800 candles × 3 paires) :

| Pair | Best PnL% (1s, 7j) | Best PnL% (1min, 30j) | Verdict |
|---|---|---|---|
| DOT | 10.95% / 7d → annualisé 570% | 13.04% / 30d | Hiérarchie tient |
| ADA | 10.95% / 7d → annualisé 570% | 10.65% / 30d | Hiérarchie tient |
| LINK | 7.30% / 7d → annualisé 380% | 10.65% / 30d | Hiérarchie tient |

**Pas de signal high-freq manqué** au pas de la minute. La granularité 1min suffit pour calibrer la stratégie. C'est rassurant — pas besoin de poll < 30s côté bot.

## Finding 5 : Advanced features (ATR dynamique, trend skip, asym, timeout) = bruit

`advanced_sweep.py` teste 12 variantes sur les 3 best configs vol-aware :

| Variante | Effet observable |
|---|---|
| `baseline_static` | référence |
| `trend_skip_5pct` / `trend_skip_3pct` | **0 effet** sur ADA/LINK/DOT — la condition trend ne déclenche pas sur 30j calme |
| `asym_buy_uptrend` | **0 effet** mesurable |
| `level_timeout_1440` (24h) | DOT : 14.10 → 16.79 (+2.69, marginal). Autres : 0 effet |
| `atr_k=1.5` | DOT : 14.10 → 15.48 (marginal, +50% RTs). LINK : -3.90 (**destructeur**) |
| `atr_k=2.0` | DOT neutre. LINK : -3.10. ADA : 4.65 (**destructeur**) |
| `atr_k=3.0` | Toutes les paires perdent |
| `ATR2.0+trend3+timeout24h` | DOT : 15.36 (marginal). Best combo |

**Conclusion advanced** : seul `level_timeout_1440` (et marginalement ATR1.5 sur DOT) apporte quelque chose. **Ne pas multiplier les features avant que les fondamentaux soient en place** (= volume filter + bonne config spacing/levels).

---

## Comparaison config déployée vs optimale

**Config actuelle (déployée 2026-05-09 23h)** :
- 3 paires : LINK + SOL + DOT
- Spacing 2.0%
- 6 niveaux
- Capital $46/pair = $138 total
- Gate V4 RSI[36-66]+ATR%[1.12-2.17]
- Pas de filtre volume

PnL backtest 30j (baseline, sp=2% lvl=6) :
- LINK : 2.80%
- SOL  : **-2.26%** (mauvais)
- DOT  :  6.33%
- **Total : 6.87% / 30j ≈ $3.16 sur $138**

**Config optimale candidate (vol-aware, sp=3% lvl=4)** :
- ADA `all3` mode : **17.65%**
- LINK `spike_avoid_2x` : 15.97%
- DOT `vwap+spike2x` à sp=2% lvl=4 : 14.10% (DOT préfère sp=2%, pas 3%)
- **Total backtest : 47.72% / 30j ≈ $21.95 sur $138**

**Dégradation live attendue** : -50 à -70% selon la règle empirique 2026-05-01 (live Sharpe = 30-50% du backtest pour le grid sur alts) :
- Estimation conservatrice (×30%) : $6.6/30j
- Estimation médiane (×40%)     : $8.8/30j

**Comparable** : la config déployée à 30% du backtest = $0.95/30j. Le gain potentiel = **×7-10** sur le rendement net.

---

## Recommandations (pour ta décision)

### Niveau 1 — Le plus prudent (juste les volume filters)

Garder pairs/spacing/levels actuels (LINK+SOL+DOT, 2%, 6 niveaux). Activer juste un filtre volume par paire :
- LINK → `min_vol_1.0` (lift +3.27)
- DOT → `vwap+spike2x` (lift +3.07)
- SOL → garder baseline (`all3` est destructeur sur SOL, pas testé exhaustivement)

Gain estimé : +$1.40 sur 30j vs actuel (vs +$3.16 baseline = +44% en relatif).

### Niveau 2 — Switch SOL → ADA + volume filters

Trois paires : LINK + DOT + **ADA** (au lieu de SOL).
- Garder sp=2% lvl=6 (transition douce)
- LINK `min_vol_1.0`, DOT `vwap+spike2x`, ADA tester d'abord 2 modes vu sa sensibilité

Gain estimé : +$2 à +$3 sur 30j vs actuel.

### Niveau 3 — Refonte complète (cf. backtest optimal)

- 3 paires : ADA + LINK + DOT
- Spacing 3% (LINK, ADA) et 2% (DOT)
- 4 niveaux
- Volume filter par paire (cf. tableau Finding 1)

Gain estimé : +$5 à +$8 sur 30j (×7-10 vs config actuelle).

**Risque** : config jamais testée live. Plus de buy fills par niveau (capital concentré) = moins de réserve si downtrend. Recommandé d'attendre 7j de validation après déploiement progressif.

### Niveau 4 — Tester ATR-dynamic uniquement sur DOT

Si tu veux explorer, `atr_k=1.5` sur DOT seulement donne +1.4% lift et +50% de RTs (plus actif sans casser). À considérer après Niveau 1-2.

### Ce que je NE recommande PAS

- Activer ATR-dynamic sur LINK ou ADA (négatif)
- Combiner trop de features (ATR + trend + asym) — overfitting risque
- `all3` sur DOT (catastrophique)

---

## Caveats critiques

1. **Backtest = Binance spot, live = Kraken Futures**. Funding rate (~0.01-0.03% / 8h soit ~0.03-0.1% / jour) n'est PAS modélisé dans le backtest. Sur 30j ça peut peser 1-3 pts de PnL.
2. **Slippage non modélisé** — fills considérés au prix limite exact. En réalité Kraken Futures maker order remplit au prix exact si touché, mais entre les fills le market peut rebondir → opportunités manquées non capturées.
3. **Régime spécifique au backtest 0411-0510** : uptrend modéré BTC, RSI choppy. Si le régime change (downtrend dur), tous les chiffres baissent.
4. **Gate V4 RSI+ATR n'a pas été VALIDÉ dans ces sweeps** — les filtres RSI[36-66]+ATR%[1.12-2.17] sont appliqués mais on n'a pas testé "sans gate" comme contre-factuel.
5. **Le bug `handleFillNeutral` côté Martin** (cycle 28-32) peut faire perdre des sells. Le backtest assume des sells systématiquement postés.

---

## Données brutes

Tous les JSON résultats sont dans `ai-lab/darwin/` (non commitées — git status untracked) :
- `comprehensive_sweep_results.json` (73 KB, 168 configs)
- `volume_sweep_results.json` (18 KB, 72 configs)
- `advanced_sweep_results.json` (9.8 KB, 36 configs)
- `sweep_1s_results.json` (18 KB, 63 configs, tick précision)
- `grid_backtest_1min_results.json` (888 B, 3 configs baseline)
- `darwin_max_results.json` + `darwin_max_results_with_fees.json` (évolutionnaire darwin)

Les scripts source sont à côté.

---

## Méthode

Synthèse cycle 33 (NB autonome) — script Python ad-hoc qui parse les 4 JSON principaux + cross-référence avec config déployée. Aucune nouvelle exécution de backtest (validation lecture seule des résultats que tu avais déjà générés la veille).

**Frontière respectée** : 0 modif VM, 0 modif Martin code, 0 modif config trading. Output unique = ce doc.
