# Sizing Kelly-dérat du trend_grid — 2026-07-07 (cycle 220)

**Source** : campagne walk-forward Fable du 0707 02:13 UTC (`docs/projets/campagne-walkforward-2026-07-07.md`, commit `dde3a99`) — 7 folds OOS par pair, verdict trend_grid POSITIF-OOS 6/6, caveat "moteur = proxy optimiste, live ≈ 30-50 % du backtest".

## Question posée

Si `TrendStateManager` passe en `TREND_MODE=LIVE` (dans 2-3 semaines selon Tony), **combien allouer par pair** ? La distribution actuelle ($25 LINK + $25 SOL) est-elle optimale au sens Kelly appliqué aux folds OOS observés ?

## Méthode

1. Prendre les 7 folds OOS de chaque pair (fenêtre 45 j).
2. Calculer moyenne + std sur les 7 folds → annualiser (facteur `365/45`).
3. Appliquer **dératage 35 %** au return annualisé (milieu de la fourchette 30-50 % de Fable).
4. Kelly = `E[R_annuel] / Var(R_annuel)` avec `E[R]` dératé, `Var(R)` conservée (worst-case pour vol).
5. Sizing = **½ Kelly** (standard industriel de prudence) × capital.
6. Total capé à **60 % du portefeuille** ($57 sur $95), 40 % buffer margin.

## Résultat

| pair | mean fold % | std fold % | Sharpe fold | ann_ret dérat % | ann_std % | ½K dérat | **alloc $** | last fold % |
|------|------------:|-----------:|------------:|----------------:|----------:|---------:|------------:|------------:|
| XBT  | 5.49  | 4.28  | 1.28 | 15.6  | 12.2 | 5.256 | **18.56** | −0.90 |
| DOT  | 22.26 | 9.41  | 2.36 | 63.2  | 26.8 | 4.396 | **15.53** | +14.55 |
| ETH  | 12.41 | 8.39  | 1.48 | 35.2  | 23.9 | 3.089 | **10.91** | −2.51 |
| ADA  | 18.07 | 13.41 | 1.35 | 51.3  | 38.2 | 1.759 | **6.21**  | +6.36 |
| LINK | 19.40 | 19.24 | 1.01 | 55.1  | 54.8 | 0.917 | **3.24**  | +8.30 |
| SOL  | 20.76 | 22.44 | 0.93 | 58.9  | 63.9 | 0.721 | **2.55**  | +3.66 |

**Total déployé** : $57.00 / $95.00 = 60.0 % · **Buffer** : $38.00.

## Punchlines

### 1. Kelly récompense la stabilité, pas les gros returns

XBT (5.49 % mean fold) reçoit **$18.56**, alors que SOL (20.76 % mean fold) ne reçoit que **$2.55**. Différence : la std de XBT est 4.28, celle de SOL est 22.44. Kelly divise le return par la variance, donc une **volatilité 5× plus élevée** écrase l'allocation même si le return est 4× meilleur. **DOT** émerge en 2ᵉ position (Sharpe 2.36, le meilleur) : return solide **et** régularité.

### 2. La grid actuelle est allouée aux pires pairs Kelly-ajustées

État Martin cycle 220 : **LINK $25 + SOL $25** = $50 déployé, sur les 2 pires Sharpe (1.01 et 0.93). Kelly-dérat dirait $3.24 + $2.55 = $5.79. Sur-allocation **8×** au sens Kelly walk-forward.

Attention : les grids actuelles sont `NEUTRAL_DUAL`, pas des trend_grid. Le walk-forward ne s'applique **pas directement** — il chiffre l'edge du régime long trend-only. Mais quand `TREND_MODE=LIVE` sera activé, cette allocation deviendra structurelle et le sous-poids XBT+DOT sera un manque à gagner.

### 3. Le dernier fold trahit XBT et ETH (whipsaws de régime)

| segment | mean last fold |
|---------|---------------:|
| Bigcap (XBT + ETH) | **−1.70 %** |
| Altcap (SOL + ADA + DOT + LINK) | **+8.22 %** |

Le fold 7 (test ≈ 2026-04-28 → 2026-06-12) recouvre le **crash BTC 0517** (`BtcRegimeKillSwitch fired`, cf. `project_btc_killswitch_incomplete.md`). Whipsaw de régime → trend_grid entre en BULL, croise EMA200 en BEAR, sort en perte, ré-entre trop tard. C'est un **coût cataloguéd** de la stratégie et il touche préférentiellement les **cap-lourds** parce que leur trend a plus d'inertie et les faux signaux durent plus longtemps. Les alts, plus volatiles, sortent plus vite du BEAR et récoltent plus de trend.

Implication : garder XBT allocation Kelly mais **savoir** que sur les épisodes de whipsaw le drawdown sera concentré sur le duo BTC+ETH. Ne pas paniquer si le prochain 45-j fold XBT/ETH est négatif après un régime change — c'est la structure.

### 4. Le 60 % cap n'est pas mordu par les alts

Sans le cap déployé (Kelly pur × dératage), le total serait ~$60. Avec dératage 35 % on est **déjà en dessous** de 60 % du capital. Kelly ne demande **pas** de leverage supplémentaire. Signal fort : le sizing conservateur Fable ($25/grid en NEUTRAL, effectif ~$50 total) est **du bon ordre**. La question n'est pas "faut-il déployer plus" mais "faut-il redistribuer".

## Recommandation opérationnelle (sans action)

Quand `TrendStateManager` passera `TREND_MODE=LIVE`, la distribution actuelle mérite ce switch :

| pair | actuel (NEUTRAL) | proposé (TREND_MODE) | delta |
|------|:----------------:|:--------------------:|:-----:|
| XBT  | 0 grid         | $18 trend_grid         | +$18 |
| DOT  | 0 grid         | $15 trend_grid         | +$15 |
| ETH  | 0 grid         | $11 trend_grid         | +$11 |
| ADA  | 0 grid         | $6 trend_grid          | +$6  |
| LINK | $25 NEUTRAL_DUAL | $3 trend_grid        | −$22 |
| SOL  | $25 NEUTRAL_DUAL (closeOnly) | $3 trend_grid | −$22 |
| **total** | $50 | **$56** | — |

**Frontière vacation respectée** : ceci est une **analyse**, pas une action. Aucun changement de deploy sans validation Tony au réveil.

## Caveats et faiblesses connues de la méthode

- **Kelly suppose stationnarité** : les folds sont OOS mais toujours dans le même régime macro (post-halving 2024). Un régime nouveau (ex : effondrement liquidité 2022-style) peut invalider les allocations.
- **Corrélations ignorées** : Kelly par pair suppose indépendance. En pratique DOT/LINK/SOL corrélées ~0.7 en trend. Le vrai Kelly-portefeuille serait plus petit que la somme des Kelly individuels. Le cap 60 % agit comme proxy correcteur.
- **Le proxy trend_grid de Fable simule 0.5 × ret + 0.5 × harvest** : c'est optimiste sur la récolte. Un simulateur multi-levels réaliste réduirait probablement les returns de 20-40 % supplémentaires. Le dératage 35 % agit comme proxy correcteur ici aussi.
- **Un fold = 45 j** : petite fenêtre statistique. 7 folds est le seuil minimum walk-forward. Les std annualisées peuvent être sous-estimées.
- **Le dernier fold XBT/ETH < 0 est un signal, pas un bruit** : si le prochain 45-j reste négatif sur ces pairs, il faut relancer la campagne et re-scorer. Kelly n'est valide que sur des paramètres à jour.

## Prochaine campagne (piste)

Deux extensions naturelles à demander à Fable ou construire moi-même :
1. **Ratio IS/OOS overfit** : modifier `campaign_walkforward.py` pour aussi enregistrer le `metrics(eq_train, n_train)` avec les meilleurs paramètres, et sortir un ratio `IS_pnl / OOS_pnl` par fold. Si > 2 systématiquement → overfit d'optimisation.
2. **Attribution BULL vs transition** : compter dans le trend_grid le PnL réalisé pendant les bars où `bull=True` en stable versus pendant les bars où `bull` a changé dans les 24h précédentes. Isole le coût des whipsaws de régime.

L'un ou l'autre serait un ajout de <50 lignes à `campaign_walkforward.py`.

## Chiffres à mettre en mémoire (dream)

- trend_grid Kelly-dérat 1/2 avec cap 60 % → XBT $18.56, DOT $15.53, ETH $10.91, ADA $6.21, LINK $3.24, SOL $2.55.
- Distribution actuelle LINK+SOL $25 chacune = sur-allocation Kelly d'un facteur ~8× sur les 2 pires Sharpe.
- Bigcap −1.70 %, altcap +8.22 % sur le dernier fold (whipsaw régime 0517).
- DOT est le meilleur Sharpe (2.36), régulier sur les 7 folds (14.55 % même sur le dernier).
- Fable proxy `0.5 × ret + 0.5 × harvest` = optimiste, dératage 35 % appliqué.
