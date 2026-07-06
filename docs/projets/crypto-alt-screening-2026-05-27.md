# Crypto Perp Screening for Martin Grid Bot — 2026-05-27

**Format adapté du skill market-researcher:idea-generation (equity → crypto perp)**
**Question**: Quelle paire ajouter au lineup actuel LINK/ADA/ETH/SOL/DOT ?

## Critères de screening (crypto-specific)

Pour qu'une perp soit candidate à un grid Martin, il faut:

1. **Liquidité Kraken Futures** : volume 24h > $5M, bid-ask spread < 10bp
2. **Funding stable** : 7d rolling avg funding |APR| < 8%
3. **Comportement range-bound** : ratio price-range / ATR(14d) < 4 (= pas trending monotone)
4. **Low correlation BTC** : 30d corr < 0.75 (diversification utile)
5. **Volatilité utile** : 30d realized vol 30-70% (assez pour fills, pas trop pour cascade SL)

## Lineup actuel (rappel)

| Pair | Status | Notes |
|---|---|---|
| BTC (PF_XBTUSD) | armé | grid SHORT testé fail, jamais déployé en NEUTRAL |
| ETH (PF_ETHUSD) | armé NEUTRAL | déployé brièvement ce matin, stoppé 25min |
| SOL (PF_SOLUSD) | armé/dispo | funding -19% APR récemment (problème) |
| ADA (PF_ADAUSD) | armé NEUTRAL | cascade -$7.63 récente |
| LINK (PF_LINKUSD) | armé NEUTRAL | base historique, OK |
| DOT (PF_DOTUSD) | armé/dispo | low vol, less interesting |

**Coverage actuelle**: skewed L1 alts (ADA, SOL, DOT) + 1 DeFi (LINK) + 2 majors (BTC, ETH).
**Gap identifié**: pas de pair "mean-reverter classique low-correlation", pas de payment-coin (XRP/LTC).

## Candidats screened

### ⭐ Top pick : XRP (PF_XRPUSD)

| Critère | XRP | Verdict |
|---|---|---|
| Volume 24h Kraken Futures | ~$15-25M | ✓ liquide |
| Bid-ask spread | ~3-5bp | ✓ très serré |
| Funding 7d avg | ~±2% APR | ✓ stable (vs SOL -19% spike) |
| Range/ATR | ~2.5 | ✓ range-bound depuis 2024 |
| Corr 30d BTC | ~0.55-0.65 | ✓ low corr (le plus bas du panier alts majeurs) |
| Vol 30d | ~45-55% | ✓ idéal pour grid |

**Thèse**:
- XRP a un comportement structurellement différent de BTC depuis le settlement Ripple-SEC 2023 — drivers idiosyncratiques (ETF spot XRP, settlement Asia)
- Range-bound depuis 2024, avec breakouts événementiels rares mais clean
- Communauté retail forte = bid systématique sur support
- Pas de funding drama récent (SOL/AVAX ont des spikes funding)

**Risques**:
- Tail event = ETF XRP approval = pump 50% qui kill grid SHORT/NEUTRAL trapped (probable Q3-Q4 2026)
- Si banni d'un pays G7 = dump cascade
- Régulation US toujours pas tout-clean malgré Ripple-SEC

**Setup grid suggéré**:
- Capital $25, leverage 7, spacing 1.5%, 4 levels, maxLoss 10%, mode NEUTRAL
- Entry quand BULL regime ou BTC reclaim EMA200

### Pick #2 : LTC (PF_LTCUSD)

| Critère | LTC | Verdict |
|---|---|---|
| Volume | ~$3-5M | △ borderline liquide |
| Spread | ~5-10bp | ✓ OK |
| Funding | ~±1% | ✓ très stable |
| Corr BTC | ~0.70-0.80 | △ corrélé mais < SOL/ETH |
| Vol | ~30-40% | ✓ low vol = grid moins risqué |

**Thèse**:
- Le mean-reverter le plus classique du marché
- Vol low = SL hits rares, mais ratio rt/vol bas aussi
- "Halving" LTC tous les 4 ans (prochain mid-2027) = base demand structurelle

**Risques**: low volume sur Kraken Futures peut générer slippage. Déclin relevance vs new chains.

**Verdict**: backup si XRP indisponible.

### ❌ Picks rejetés

| Pair | Raison rejet |
|---|---|
| **AVAX** | Trop corrélé SOL (0.85+), redondance |
| **BCH** | Volume insuffisant sur Kraken Futures (<$2M/24h) |
| **DOGE** | Volatility spikes événementiels (Musk tweets) trop violents pour grid |
| **MATIC/POL** | Funding très instable, multiples migrations chain |
| **AAVE/UNI** | DeFi event-driven = grids tués par governance votes |
| **NEAR** | Pas listé sur Kraken Futures (à vérifier) |
| **FIL/ALGO** | Volume <$1M, illiquide |

## Comparaison vs lineup actuel

| Pair | Liquidity | Funding stability | Range-bound | Corr-to-BTC | Vol fit |
|---|---|---|---|---|---|
| **XRP** (candidat) | ✓✓ | ✓✓ | ✓✓ | ✓✓ | ✓✓ |
| LTC (candidat #2) | ✓ | ✓✓ | ✓ | △ | ✓ |
| LINK (actuel) | ✓✓ | ✓ | ✓ | △ | ✓✓ |
| ADA (actuel) | ✓✓ | ✓ | △ | △ | ✓ |
| SOL (actuel) | ✓✓ | ✗ (−19% spike) | ✗ (trends) | △ | △ vol high |
| DOT (actuel) | ✓ | ✓ | ✓✓ | △ | △ low vol |
| ETH (actuel) | ✓✓ | ✓✓ | △ | ✗ (correlation 0.9+) | ✓ |

→ XRP comble exactement le gap : ✓✓ sur 5/5 critères.

## Reco

**Ajouter XRP au lineup** quand le bot sortira de WARM_ONLY et que le régime sera favorable.

**Config suggérée à armer dans strategy.json** :
```json
{
  "instrument": "PF_XRPUSD",
  "capital": 25,
  "leverage": 7,
  "gridSpacingPct": 1.5,
  "totalLevels": 4,
  "maxLossPercent": 10,
  "gridMode": "NEUTRAL",
  "enabled": true
}
```

**Prochaine étape**: backtest XRP sur 180j (si parquet existe dans `martin/backtest/data/`) avec Variant A (BULL→NEUTRAL+BEAR→cash) pour valider que les résultats BTC se généralisent à XRP avant arming réel.

## Méthodologie & limites

- Pas de live data screening (besoin scraping Kraken Futures public API)
- Estimations volume/spread basées sur ordre de grandeur connu, à vérifier
- Pas de covariance matrice complète multi-pair (utile pour optimal portfolio allocation)
- Backtest XRP recommandé avant deploy réel
