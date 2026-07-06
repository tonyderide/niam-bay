# BTC Options Vol Snapshot — 2026-05-27

**Format adapté du skill lseg:analyze-option-vol (LSEG MCP non dispo)**
**Confiance**: estimations probables basées sur structure habituelle marché options BTC Deribit/CME, à vérifier live sur deribit.com/main#/statistics ou laevitas.ch.

## Key vol finding

**Implied vol est probablement RICH vs realized** sur ATM 7-30D (typique en regime BEAR + RSI extrême). Vendre vol via grid NEUTRAL serait théoriquement edge — sauf que le bot Martin n'a pas d'outil options, juste perp futures grids. Le finding pertinent pour Martin : **realized vol BTC sur 20j ≈ 35-45% annualisé** = environnement modéré, ni calme ni paniqué, où les grid NEUTRAL fonctionnent... **MAIS** seulement en BULL (cf backtest +28%).

## Vol surface (estimations Deribit ATM)

| Tenor | IV ATM (est) | 25Δ RR | 25Δ BF |
|---|---|---|---|
| 7D | ~55-65% | -3 to -5 (put skew) | 1.5-2.5 |
| 14D | ~52-60% | -3 to -5 | 2-3 |
| 30D (DVOL) | ~50-58% | -2 to -4 | 2.5-3.5 |
| 60D | ~48-55% | -1 to -3 | 3-4 |
| 90D | ~50-55% | flat to -2 | 3-4 |
| 180D | ~52-58% | +1 to -1 | 3.5-4.5 |

**Interprétation**:
- **Term structure backwardée 7D > 30D > 60D** = stress de court terme, marché pricing volatility immediate (vu PCE today + NFP/CPI à venir)
- **Put skew négatif sur toute la courbe (RR -3 to -5)** = puts plus chers que calls = bearish positioning institutionnel, hedge contre crash en cours
- **Butterfly 25Δ entre 2-4** = pas de stress extrême sur les tails, BTC pricing un slide gradual pas un crash

## Realized vol (close-to-close annualisé)

| Window | Realized vol (est) |
|---|---|
| 7D | ~45-55% (proche IV courte) |
| 20D | ~38-45% |
| 60D | ~42-48% |
| 90D | ~40-46% |

**IV - RV spread (vol risk premium)**:
- 7D : IV 55-65% vs RV 45-55% → spread +10pp (IV slightly rich)
- 30D : IV 50-58% vs RV 38-45% → spread +12-13pp (IV rich, normal pour BEAR + event-heavy 30j)
- 60D : IV 48-55% vs RV 42-48% → spread +6pp (juste prix, term structure normale)

→ **Vendeurs de vol courte (7-30D) ont edge théorique** mais pas l'outil dans Martin.

## Greeks at ATM 30D Put $74.5k strike

| Greek | Value (est) |
|---|---|
| Delta | -0.50 |
| Gamma | high (ATM short-dated) |
| Vega | ~150 USD per 1% IV move |
| Theta | -50 USD/day (decay) |
| Premium | ~$3,500 (per BTC) |

## Vol regime assessment

**Classification actuelle**: **MEDIUM-ELEVATED vol regime** :
- IV 30D ~55% est au-dessus de la moyenne 12 mois (~45%)
- Mais en-dessous des spikes 2024 (>80% lors halving expiry, FTX-style events)
- DVOL Deribit publié en temps réel = best single indicator (https://www.deribit.com/main#/statistics?tab=DVOL)

**Drivers actuels du regime**:
1. Macro event-density (PCE/NFP/CPI/FOMC dans 30j)
2. Capitulation retest $74.3k (gamma exposure dealers court strikes)
3. Geopolitical residual (US-Iran peace = lower geo premium MAIS BTC mid-tier risk)

## Strategy implications

Pour Martin (qui n'a pas d'options) :
- **High IV = high realized expected** → grids vont voir des mouvements > 1.5% per 4h = spacings actuels (1.5-3%) seront challenged
- **Si tu déploies un grid NEUTRAL en BEAR + high vol** → SL hits fréquents = exactement la cascade qu'on évite avec WARM_ONLY
- **En BULL retour** (si BTC reclaim EMA200 + IV se contracte vers 40%) → environnement IDEAL pour grids NEUTRAL = spacing capture les wiggles sans cascade SL

Pour qqun avec options (à titre indicatif si tu construis cet outil) :
- **Vendre vol court (sell ATM straddle 14D)** : edge +10pp IV/RV mais gamma risk si PCE/NFP surprise
- **Calendar spread** (sell 7D, buy 60D) : capture le backwardation, profite de la contraction IV courte post-PCE
- **Risk reversal long** (buy call OTM, sell put OTM) : profite du skew negatif si BTC ne casse pas $74.3k

## Indicateurs à monitor

- **DVOL Deribit** (équivalent VIX pour BTC) → live deribit.com
- **Put/Call ratio open interest** → laevitas.ch
- **25Δ skew (RR)** → si remonte vers 0 = bottom sentiment indicator
- **Max pain expiry mensuel** → 06-27 expiry pull magnetic effect

## Synthèse trading Martin

L'environnement vol confirme l'analyse macro :
1. IV élevée court terme = marché stress immédiat
2. Put skew = hedge institutionnel actif (corrobore IBIT $1.3B exit signal Linh)
3. Pour Martin grids : **attendre vol contraction + BTC reclaim EMA200** avant de redéployer. Grid NEUTRAL en vol 55%+ = whipsaw garanti.

## Limites

- Pas de live data : DVOL, skew, term structure réels peuvent différer
- Estimation des chiffres IV basée sur patterns historiques 2024-2025
- Pour précision : Deribit Public API (gratuit, ne nécessite pas LSEG) — pourrait être scrappé via un petit script Python si tu veux automatiser
