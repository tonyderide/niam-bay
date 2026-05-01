# Mean Reversion Crypto Strategies 2025-2026 — Research

Date: 2026-04-30
Scope: Bollinger / RSI / pairs / stat-arb / vol sizing / regime filters / live bots.

## Sources reviewed

1. SetupAlpha 2025 — Mean-Reversion Failures — https://setupalpha.com/blogs/articles/mean-reversion-strategy-failures-complete-fix-guide
2. CoinCryptoRank 2025 — Stat-Arb Models — https://coincryptorank.com/blog/stat-arb-models-deep-dive
3. Mind Math Money 2025 — Bollinger Guide — https://www.mindmathmoney.com/articles/master-bollinger-bands-the-complete-trading-guide-2025
4. Mudrex — Bollinger Settings 2025 — https://mudrex.com/learn/bollinger-bands-in-crypto-trading/
5. SSRN (Arda) — BB regimes BTC/USDT — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5775962
6. Sword Red — BB+RSI strategy — https://medium.com/@redsword_23261/enhanced-mean-reversion-strategy-with-bollinger-bands-and-rsi-integration-87ec8ca1059f
7. Thrive 2025 — Regime Detection — https://thrive.fi/blog/trading/crypto-market-regime-detection
8. Amberdata 2025 — Cointegration > Correlation — https://blog.amberdata.io/crypto-pairs-trading-why-cointegration-beats-correlation
9. Wundertrading — Pairs Trading — https://wundertrading.com/journal/en/learn/article/crypto-pairs-trading-strategy
10. QuantInsti / Rong Fan — Perpetual pair trading — https://blog.quantinsti.com/crypto-perpetual-contract-pair-trading-project-rong-fan/
11. Janelle Turing Mar 2025 — OU Crypto — https://janelleturing.medium.com/python-ornstein-uhlenbeck-for-crypto-mean-reversion-trading-287856264f7a
12. Mind Math Money 2026 — RSI Guide — https://www.mindmathmoney.com/articles/the-ultimate-guide-to-the-rsi-indicator-mastering-rsi-trading-strategies-and-settings-2025
13. Stoic.ai — Mean Reversion Crypto — https://stoic.ai/blog/mean-reversion-trading-how-i-profit-from-crypto-market-overreactions/
14. NostalgiaForInfinity (Freqtrade) — https://github.com/iterativv/NostalgiaForInfinity
15. BitMEX Q3 2025 Derivatives Report — https://www.bitmex.com/blog/2025q3-derivatives-report
16. ScienceDirect — Funding Rate Arbitrage — https://www.sciencedirect.com/science/article/pii/S2096720925000818

## Key findings (with concrete numbers)

### 1. Bollinger Bands — params that win in 2025

- **Daily default**: BB(20, 2.0) "works well on daily BTC/ETH" (Mind Math Money).
- **Intraday 5–15m**: **BB(10, 1.5)** is retail consensus (Mind Math Money, Mudrex). 1.5σ → band touch ~13% vs ~5% for 2σ.
- **Swing**: BB(50, 2.5) on daily.
- **Regime (SSRN BTC/USDT)**: "during bear phases breakout strategies outperform while mean-reversion signals **fail**; in accumulation phases mean reversion regains limited profitability". → Only trade when *bands flat and parallel*.
- **BB+RSI combo (Sword Red)**: BB(20, 2) + RSI(14) at 30/70, BTC/USDT 2h, Nov–Dec 2024. No published win rate — "performance varies greatly".

### 2. RSI — thresholds for crypto perps

- **30/70 baseline** — multiple sources flag it as too noisy for crypto.
- **Crypto-tuned: 20/80** ("better signals in crypto's volatility").
- **Regime-adaptive**: bull → oversold<40, overbought>90; bear → oversold<10, overbought>60.
- **Adaptive period (SetupAlpha)**: RSI(10) in high vol, RSI(20) in low vol.
- **Percentile entry**: long when RSI in **bottom 10th percentile of 252-day range** (more robust than fixed 30).
- **Perp behavior**: liquidation cascades cause flash oversold; mean-rev bounce lands within **24–72h** once funding stabilizes.

### 3. Z-score / pairs trading — best pairs 2025-2026

- **Standard rule**: enter |z|>2, exit at 0 (or opposite ±2).
- **Cointegration > correlation** — confusing them "leads to painful losses" (Amberdata).
- **Strong cointegration 2025**: BTC–ETH, ETH–LTC. Also commonly traded: SOL/AVAX, BNB/ETH.
- **BTC–ETH backtest (Wundertrading)**: 16.34% annualized, 8.45% vol, **Sharpe 2.45**.
- **Perp pair (QuantInsti, Rong Fan)**: ETC-USDT vs RLC-USDT, hedge ratio 11.46. Sharpe **1.11 default → 1.14 optimized**. $10k → $90.7k. Uses percentile entries (0.99/0.01), TP 0.40–0.60 percentile, SL −20% to −30%.
- **Tests required**: ADF / Phillips-Perron **p<0.05**; drop assets with >2% missing data.

### 4. Stat-arb — half-life, Kalman

- **Half-life**: HL = -ln(2)/λ from AR(1) on spread. Example: λ=-0.06165 → HL=11.24 days; full reversion ~22.5 days.
- **Hard rule (CoinCryptoRank)**: reject pairs where HL > trading horizon. Rising median HL = "structural deterioration" — rotate pairs.
- **Hurst H<0.5** confirms mean reversion; H≈0.5 = random walk → discard.
- **Kalman filter**: needed for *time-varying* cointegration (hedge ratios drift in crypto).
- **Caveat**: Kinlay + 2025 commentary — Kalman stat-arb "does not perform well in crypto in high-fee environments". Only viable on low-fee perps (Binance/Bybit maker), with capture efficiency **>60% of theoretical spread** (CoinCryptoRank benchmark).

### 5. Volatility-adjusted sizing

- **ATR period for crypto: 10–12** (vs 14 default).
- **Formula**: Size = (Risk% × Equity) / (ATRMultiple × ATR).
- **Stop multiplier**: 2–3× ATR baseline; **3–4× ATR for crypto mean-rev** (SetupAlpha) — looser stops survive reversion-vol spikes.
- **Risk per trade: 0.5% for crypto** (vs 1% traditional). Portfolio heat cap **6–8%**.
- **Vol-regime gates**: ATR percentile <0.2 (252 bars) → mean-rev favored; >0.8 → disable or cut size 50–70%.
- **Entry rule**: enter only when "ATR has declined 30%+ from its peak" (volatility exhaustion = reversion confirmed).
- **EWMA**: auto-scale-down when residual realized vol **>1.8× 30-day average**.

### 6. When mean reversion fails — regime detection

Consensus across 5 sources (SetupAlpha, Thrive, Mudrex, MMM, ChartGuys):

- **ADX<20 = ranging → mean-rev OK**.
- **ADX 20–25 = transition, reduce size**.
- **ADX>25–30 = trending, DO NOT mean-revert** ("becomes dangerous" — SetupAlpha).
- **ADX>40 = strong trend; >60 = extreme**.
- **Compound score (Thrive)**: ADX(±2) + BB-width percentile(1–2) + MA-slope ±0.02(1–2) + ATR percentile(1–2). ML upgrades: Random Forest (n=100, depth=5) or HMM (3 states).
- **MA filter (SetupAlpha)**: only mean-revert when price within 5% of 200-day MA *and* slope flat.
- **Crypto holding period**: **1–3 days** (vs 5–10 equities).

### 7. Real-world bots 2025-2026

- **Freqtrade**: well-suited for hourly mean-rev; Binance/Kraken/Coinbase/Bitget via CCXT.
- **NostalgiaForInfinity (NFI)**: dominant Freqtrade mean-rev-flavored strategy 2025. Official backtests Nov 2025→Jan 2026. Recommended: **6–12 open trades, 40–80 pair whitelist, unlimited stake**. No publicly aggregated Sharpe.
- **Hummingbot**: market-making focused; perps support (one-way mode) Binance/Kraken/Bitget. Used for funding-rate arb more than indicator mean-rev.
- **Funding mean-rev (BitMEX Q3 2025)**: funding **positive >92% of the time** (+0.01% interest component) → short-perp/long-spot basis trade still prints, but crowded vs 2022–23.
- **Stoic.ai / 3Commas**: no audited live numbers — treat as zero-evidence.

## Bottom line for Martin bot

Martin is a **grid bot**, which is itself a structured mean-reversion strategy (buy low / sell high in a band). The research maps directly:

1. **Regime gate is the #1 missing piece**. Add an ADX(14) filter on the grid's pair: **disable / pause grid when ADX > 25** on the 1h or 4h timeframe. This single rule would have prevented multiple of Martin's runaway-loss episodes (Apr 25 lessons).
2. **Spacing → BB-equivalent**: Martin's 0.6% spacing was "too tight on weekend" per existing memory. The 2025 BB consensus (10-period, 1.5σ on intraday) implies spacing should adapt to **realized vol over the past N candles**. Hard target: spacing ≈ **1.0–1.5× ATR(14)** on the grid's timeframe — not a fixed %.
3. **Half-life screen for pair selection**: before deploying a grid on a new pair, run Engle-Granger / ADF on log-prices and reject if **HL > intended grid lifespan**. Drop the pair if H ≥ 0.5 (random walk).
4. **Vol-adjusted position sizing**: replace fixed grid step quantity with **size = riskBudget / (ATR × multiplier)**. Cap portfolio heat at 6–8% (SetupAlpha rule).
5. **Stop the grid when regime breaks**: if ATR jumps above 80th percentile of 252-bar range, **flat the position** (matches Tony's "if rentable" stance — strict consensus before staying in).
6. **Funding-rate edge** if Martin moves to perps: positive funding 92% of the time → grids on perps should slightly bias *short-side density* to harvest the funding skew, not symmetric.
7. **Don't trust vendor bot claims**. NFI on Freqtrade is the only mean-rev-flavored strategy with a publicly auditable backtest pipeline; everything else (3Commas, Stoic.ai) is unverified marketing.

## Confidence per finding

| Finding | Confidence | Rationale |
|---|---|---|
| BB(20,2) on daily, BB(10,1.5) intraday | **High** | 4+ sources agree |
| RSI 80/20 better than 30/70 in crypto | **Med-High** | 3 sources, but no audited backtest |
| BTC-ETH cointegration & Sharpe ~2.4 | **Medium** | One quoted backtest, period unclear |
| Half-life cutoff = trading horizon | **High** | Theoretically sound, repeated by multiple stat-arb sources |
| Kalman filter for crypto stat-arb | **Medium** | Theory strong, but live perf "doesn't work well" per Kinlay/2025 commentary |
| ATR(10–12) for crypto | **Medium** | Retail consensus, no academic anchor |
| ADX>25 disables mean-rev | **High** | Universal across all 5 regime-detection sources |
| Holding period 1–3 days for crypto | **Medium** | Single source (SetupAlpha), but logically consistent |
| Funding positive >92% | **High** | Official BitMEX Q3 2025 report |
| NFI as best Freqtrade mean-rev | **Medium** | Most-watched repo, but no audited public Sharpe |
| Stoic.ai / 3Commas marketing claims | **Low / Reject** | No audited numbers anywhere |

## Disagreements / open questions

- **BB std-dev for crypto intraday**: 1.5 (Mind Math Money, Mudrex) vs 2.0 (default everywhere else). Resolution: backtest both on Martin's actual pair distribution.
- **RSI thresholds**: 30/70 vs 20/80 vs adaptive percentile — no source provides head-to-head crypto-perp backtest. Worth running internally.
- **Kalman filter viability in crypto**: theory sources say yes, practitioner sources say no due to fees. Likely depends on per-trade cost structure (Kraken Pro fees are higher than Binance VIP).
- **Whether grid bots qualify as mean-rev "done right"**: not one source explicitly evaluates grid bots in the mean-rev framework — gap worth closing internally.
