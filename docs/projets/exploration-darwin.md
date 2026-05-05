# Exploration — Darwin (lecture-seule, 2026-05-05 12h45 Paris)

Cycle 9 vacation Tony, suite à inclination cycle 7 (lecture-seule projet endormi). Pas de modification — juste cataloguer.

## État actuel

**Repo :** `/home/tony/projets/tonyderide/darwin/`
**Dernier commit :** `94a4129 chore: add .gitignore, save darwin-hardening plan` (2026-04-20)
**Volume code :** ~2458 lignes (Python + HTML), pure stdlib (pas de pandas/numpy).
**Tests :** présents (`test_data.py`, `test_arena.py`, `test_agent.py`, `test_evolution.py`, `test_integration.py`).
**Worktree actif :** `.worktrees/hardening/` (Tony a commencé à hardener mais pas committé).

## Maturité

Beaucoup plus avancé que ce que ma mémoire contenait :
- **48 skills** (vs 14/22 en mémoire) — couvrant grids, scalp, martingale, DCA, EMA, RSI, BB, ADX
- **4 modes arena** : grid, scalp, martingale (avec flip long↔short), DCA
- **Brute-force optimizer** (`bruteforce.py`, 236 lignes) — teste toutes combinaisons de skills
- **UI Mission Control** : tabbed config, full UI redesign committed
- **Frais de trading** : 0.05%/trade intégrés à l'arena
- **Server WebSocket** : `server.py`, expose au front Three.js

## Bug connu (documenté par Tony lui-même)

**`indicators.py:147`** — calcul du `bb_squeeze` inclut la bougie courante dans son propre percentile :
```python
lookback = [bb_bw[j] for j in range(max(0, i - 100), i + 1) ...]
                                                    ^^^^^
```
Le `i + 1` permet à une bougie actuelle très tight de se déclarer en squeeze toute seule (lookahead-style self-inclusion). Fix prévu : passer à `range(max(0, i - 100), i)`.

## Plan de hardening (Tony, 2026-04-20)

`darwin/docs/superpowers/plans/2026-04-20-darwin-hardening.md` — **17 tâches** en 6 phases, écrit avec `superpowers:writing-plans`. Aucune tâche checkée. Audit issu d'un panel 6 agents (2 quants + 2 scalpers + 2 traders).

| Phase | Scope | Effort estimé |
|---|---|---|
| **A** Critical bug fixes | bb_squeeze + RNG seed + lookahead docs | ~1h, **prête à ship** |
| **B** Fitness + walk-forward | Sharpe×(1-MaxDD) + min-trades + 70/30 split + OOS leaderboard | ~3h |
| **C** Execution realism | Fill at next-open + slippage + maker/taker + funding | ~3h |
| **D** Indicators | ATR + MACD + VWAP + OBV + Stochastic + sessions/rvol | ~2h |
| **E** Agent DNA | ATR-stops + short-side + position-sizing + regime-gate vote | ~4h |
| **F** Evolution mechanics | Segmented crossover + decay + niching + pop≥50 | ~2h |

**Total :** ~15h pour transformer Darwin de "lottery-ticket champion generator" à "robust strategy producer". Chaque phase est mergeable indépendamment et a des tests prévus.

## Ce que Darwin pourrait apporter à Martin

Sans toucher à Martin live :
1. **Optimisation hors-ligne des paramètres grid** — Darwin peut backtester des combinaisons (spacing, levels, leverage, killPct) sur historique Kraken et identifier des fenêtres rentables. Le pattern `extract_profitable_v2.py` utilisé pour le RegimeGate IQR (cycle 0501) a déjà prouvé sa valeur. Darwin systématise ça.
2. **Découverte de nouveaux skills/conditions de gate** — l'évolutionnaire peut suggérer des combinaisons non-évidentes (ex : ADX∈[X,Y] AND RSI∈[A,B] AND volume spike). Si une combinaison robuste OOS émerge, on a un candidat de gate empirique pour Martin.
3. **Validation d'hypothèses pré-modif** — avant tout changement structurel sur Martin, faire passer la modif en simulation Darwin pour estimer l'impact 90j.

## Ce qui me semble manquer (en plus du plan A-F)

- **Pas de connexion Martin → Darwin** : Darwin n'importe pas le code de Martin (RegimeGate, GridTradingService) pour les simuler tels quels. Cela limite la validité du transfer learning. Idée : un module `martin_simulator.py` qui reproduit la logique Java en Python.
- **Pas d'output formel "candidate strategy"** — quand Darwin trouve un winner, il n'émet pas un fichier structuré (genre `strategy.json` Martin-compatible). Faciliterait le shipping.
- **Pas de comparaison head-to-head Martin actuel vs Darwin proposed** — utile pour décider si on adopte une suggestion.

## Recommandation pour Tony (au retour)

**Option fastest-win :** **Phase A** du plan hardening (bb_squeeze + RNG seed + tests). 1h, 100% safe, déboucle Phase B (fitness) qui est où la vraie valeur arrive (Sharpe + walk-forward). Je peux exécuter Phase A en autonomie pendant la vacation si tu greenlights par Telegram ou commit.

**Option creative-medium :** Construire `martin_simulator.py` (port Python de RegimeGate + GridTradingService) — permettrait de valider toute proposition Martin via Darwin avant deploy. Effort estimé 4-6h.

**Option strategic-long :** Connecter Darwin au pipeline `extract_profitable_*.py` — les fenêtres profitables détectées deviennent training data pour Darwin, et les agents évolués deviennent candidats de gate empirique. Ferme la boucle research→backtest→deploy.

## État du worktree hardening

`.worktrees/hardening/` existe avec un venv Python 3.12 et les mêmes fichiers, mais **rien n'a été committé**. Probable que Tony ait commencé puis abandonné en avril (avant le push 2026-04-20). À nettoyer au retour ou reprendre.

## Liens rapides

- README : `darwin/README.md` (résume features et architecture)
- Plan complet : `darwin/docs/superpowers/plans/2026-04-20-darwin-hardening.md`
- Tests existants : `darwin/test_*.py` (5 fichiers)
- Frontend : `darwin/web/index.html` (single-file Three.js, 662 lignes)

---

*Memo cataloguant l'état de Darwin tel que trouvé à 12h45 Paris le 2026-05-05, jour 5 vacances Tony. Aucune modification du repo darwin lors de cette exploration. Voir cycle 9 dans `vacation-autonomy.md` pour le contexte.*
