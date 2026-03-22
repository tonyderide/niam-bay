# Analyse de la branche `autre-branch` du bot Martin

*Analyse du 2026-03-22*

---

## Structure des branches

- **master** : 4 commits en avance (Grid fixes, backtest doc, param sweep, /api/system/status)
- **autre-branch** : 1 commit unique (`b2c5454 — strategie and port upadte`)
- **Base commune** : commit `03327c3` (F16 strategy)
- Le ScalpingBotService.java est **identique** sur les deux branches (0 lignes de diff)

Le vrai delta d'autre-branch est un seul gros commit qui ajoute ~38 900 lignes.

---

## Ce que contient le commit unique d'autre-branch

### 1. Backtest Python massif (~90 fichiers, ~30 000+ lignes)

Une collection exhaustive de scripts de backtesting Python :

| Categorie | Fichiers | Description |
|-----------|----------|-------------|
| Agents individuels | `agent01` a `agent10`, `agent1`-`agent4` | Strategies autonomes (combo vote, momentum, session, ichimoku, mean reversion, EMA/ADX, freqtrade, vol adaptive, ML, combiner) |
| Experts | `expert_martingale`, `expert_meanrev`, `expert_multitf`, `expert_trend`, `expert_volume` | Strategies avancees specialisees |
| Optimiseurs | `optimize_bb_trail`, `optimize_macd_trail`, `optimize_signals`, `optimize_taker`, `optimize_trail` | Grid search de parametres |
| Comparateurs | `compare_bb_trail`, `compare_strategies`, `compare_trailing`, `full_comparison`, `mega_compare` | Benchmarks croises |
| Backtests iteratifs | `backtest_v2` a `backtest_v8_final` | Evolution progressive des strategies |
| Strategies specifiques | `asymmetric_martingale`, `trailing_filtered`, `innovative_strategies`, `invent_strategy` | Approches experimentales |
| Donnees historiques | 16 fichiers JSON | ETH OHLC (1m, 5m, 15m, 30m, 60m) sur differentes periodes |
| Resultats | `full_comparison_results.txt`, `martingale_results.txt`, `strategy_comparison.txt`, `research_strategies.md` | Documentation des resultats |

### 2. Simulateur backend ameliore

**`ScalpingSimulatorService.java`** — +303/-97 lignes de diff :

- Support de **5 strategies configurables** (etait MACD_RSI uniquement) :
  - `MACD_RSI` : MACD histogram cross + filtre RSI (existant)
  - `MOMENTUM_SCORE` : Score combine MACD+RSI+EMA (seuil >= 3 pour LONG)
  - `EMA_CROSS` : Croisement EMA rapide/lente
  - `SWING_STOP` : Signal MACD+RSI + stop sous swing low/high
  - `REVERSAL_TRAIL` : Inversion immediate apres loss (pas de cooldown)
- Support de **deux formats JSON** pour les donnees (array brut ou `{candles: [...]}`)
- **Swing stop** comme alternative au trailing classique
- Fix du bug martingale : `consecutiveLosses > maxDoublings` au lieu de `>=`
- Pre-calcul des EMA arrays complets pour performance

**`SimulationRequest.java`** — Nouveaux parametres :
- `strategy` (type de strategie)
- `swingLookback`, `swingOffsetPct`, `useSwingStop`
- `dataFile` (source de donnees fichier)

### 3. Frontend simulation ameliore

- **`simulation.component.ts`** : Selecteur de strategie avec 4 options, source de donnees (fichier/live), chargement de fichiers historiques
- **`simulation.component.html`** : UI complete avec panneaux de config, grille de parametres, selecteurs de source de donnees
- **`simulation.component.scss`** : Nouveaux styles
- **`proxy.conf.json`** : Proxy Angular vers `localhost:8081` (le backend)

### 4. Brainstorm UI/UX (.superpowers/)

6 fichiers HTML de mockups pour le design du chart enrichi (legende, RSI, trailing stop, design final). Artefacts de session de brainstorming avec un outil AI.

### 5. Changements Grid Controller

- **Defaults modifies** : `gridSpacing 0.5% -> 0.7%`, `totalLevels 8 -> 6`, `maxLossPercent 25% -> 50%`
- **SystemController supprime** (71 lignes) — endpoint `/api/system/status` retire

### 6. Suppressions

- `backtest_grid_optimize.py` (223 lignes) — remplace par les nouveaux scripts
- `docs/backtest-2026-03-19.md` (90 lignes) — doc de backtest supprimee

---

## Strategies dans le live bot (ScalpingBotService)

Le bot live est **identique** sur les deux branches. Il execute la **Strategy F16** :

| Composant | Detail |
|-----------|--------|
| Signal d'entree | MACD(5,13,4) histogram cross zero + RSI filter (< 55 LONG, > 45 SHORT) |
| Filtre ADX | ADX >= 20 requis (pas de trade si marche range) |
| Filtre BB Squeeze | BBwidth < 0.3% = squeeze, attend le breakout |
| Stop-loss | Swing stop 1h (3 dernieres bougies horaires) comme SL de securite sur Kraken |
| Trailing stop | 2 niveaux : 1.5% wide -> 1.0% tight apres 0.3% de profit |
| Martingale | Desactive (sizeMultiplier toujours 1.0), capital dynamique (compound) |
| Risk management | 10% max daily loss, trading hours 08-22 UTC, 60s cooldown apres loss |
| Position sizing | Capital dynamique (initial + PnL realise), 90% de la marge, via API Kraken |
| Tick | Toutes les 10 secondes |

---

## Ce qui est mieux sur autre-branch

1. **Simulateur multi-strategies** : Permet de tester 5 strategies differentes au lieu d'une seule, avec tous les parametres configurables depuis le frontend
2. **Donnees historiques** : 16 fichiers JSON de donnees ETH sur differentes periodes et timeframes — precieux pour le backtesting reproductible
3. **Recherche exhaustive** : ~40 scripts Python couvrant pratiquement toutes les approches connues (momentum, mean reversion, ichimoku, ML, etc.)
4. **Fix simulator** : Correction du bug `>=` vs `>` pour le compteur martingale
5. **Frontend simulation** : UI beaucoup plus riche avec choix de strategie et source de donnees

---

## Ce qui est mieux sur master

1. **Grid fixes** (`698bd1c`) : Detection d'orphans, market check au demarrage, maxLoss 25% — code de production important
2. **Grid param sweep** (`95c6c95`) : 0.5%/8 niveaux optimal comme defaults
3. **SystemController** (`3bdf81d`) : Endpoint `/api/system/status` pour monitoring
4. **Backtest doc** (`7c228d1`) : Documentation du backtest Grid +24-30% ROI

---

## Ce qui devrait etre merge

### Oui, merger :
- `ScalpingSimulatorService.java` ameliore (multi-strategies, fix bug, formats JSON)
- `SimulationRequest.java` avec les nouveaux parametres
- Les composants frontend simulation (`.ts`, `.html`, `.scss`)
- Le `proxy.conf.json` (utile pour le dev local)
- Les fichiers de donnees historiques (`backtest/*.json`)
- Le `research_strategies.md` (documentation de recherche)

### A discuter :
- Les ~40 scripts Python de backtest — utiles comme reference mais encombrent le repo. Envisager un sous-dossier ou un repo separe.
- Les fichiers `.superpowers/brainstorm/` — artefacts de session, pas necessaires dans git

### Ne PAS merger :
- Les changements GridController (defaults 0.7%/6/50%) — master a deja les valeurs optimisees (0.5%/8/25%)
- La suppression de SystemController — master vient de l'ajouter
- La suppression de `docs/backtest-2026-03-19.md`
- La suppression de `backtest_grid_optimize.py`

---

## Risques du merge

| Risque | Impact | Mitigation |
|--------|--------|------------|
| **Conflit GridController defaults** | Les valeurs de master (0.5%/8/25%) seraient ecrasees par 0.7%/6/50% | Cherry-pick selectif ou resolution manuelle |
| **SystemController supprime** | L'endpoint `/api/system/status` disparaitrait | Garder la version master |
| **Taille du repo** | +38 000 lignes, JSON de donnees potentiellement lourds | Les JSON de donnees pourraient etre dans .gitignore ou un LFS |
| **Backtest doc supprimee** | Perte de `docs/backtest-2026-03-19.md` | Garder la version master |
| **Pas de conflit ScalpingBotService** | Le bot live est identique — zero risque | Aucun |

---

## Recommandation

**Ne pas merger la branche entiere.** Faire un cherry-pick selectif :

```bash
# 1. Creer une branche de merge propre depuis master
git checkout -b merge-autre-branch-simulation master

# 2. Cherry-pick uniquement les fichiers utiles depuis autre-branch
git checkout origin/autre-branch -- backend/src/main/java/com/martin/scalping/ScalpingSimulatorService.java
git checkout origin/autre-branch -- backend/src/main/java/com/martin/scalping/SimulationRequest.java
git checkout origin/autre-branch -- frontend/src/app/components/simulation/
git checkout origin/autre-branch -- frontend/proxy.conf.json
git checkout origin/autre-branch -- backtest/*.json
git checkout origin/autre-branch -- backtest/research_strategies.md

# 3. Commit et merge dans master
```

Cela recupere le simulateur ameliore et les donnees sans casser les Grid defaults ni perdre le SystemController.
