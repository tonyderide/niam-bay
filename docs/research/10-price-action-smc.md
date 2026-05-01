# Price Action / SMC / Wyckoff / Order Flow for Crypto Bots (2025-2026)

**Research date**: 2026-04-30
**Scope**: codable signals from discretionary methods, with measurable edge
**Bias check**: ICT/SMC space is heavily monetized by educators ($19-$200/mo indicators, courses). Treat performance claims with extra scrutiny.

---

## TL;DR

- **SMC is codable** but has **no peer-reviewed validation**. Best Python lib: `joshyattridge/smart-money-concepts` (1.6k stars, v0.0.26 March 2025) — implements FVG, BOS, CHoCH, OB, liquidity. Use it as a *feature generator*, not a strategy.
- **Most measurable edges are derivatives-data-driven**, not pattern-driven: liquidation heatmaps (Coinglass API $29/mo), CVD divergence on perps, OI+funding regime detection.
- **Wyckoff is too discretionary to fully automate**; the codable subset = volume profile (HVN/LVN) + range detection.
- **Honest skepticism**: SMC backtests claiming 60%+ win rates almost always come from sellers of the methodology. The single semi-rigorous backtest found (2,600 trades, 26 months) reports 61.2% WR / 2.17 PF but **withholds drawdown** and the author sells the indicator. No academic study validates ICT/SMC.
- **Codable signals with the strongest claim to edge** (ranked):
  1. Liquidation cluster proximity (Coinglass heatmap) → mean-reversion target
  2. CVD/price divergence on perps → exhaustion signal
  3. Funding+OI extremes → contrarian regime filter
  4. Anchored VWAP from regime pivots → dynamic S/R
  5. HVN levels from volume profile → magnet/target
  6. FVG/order blocks → confluence layer only, not standalone

---

## 1. Smart Money Concepts (SMC) — codable but unproven

**Concepts**: Liquidity grabs, Fair Value Gaps (FVG), Order Blocks (OB), Break of Structure (BOS), Change of Character (CHoCH).

**Codability**: high. The `smart-money-concepts` Python package (joshyattridge, 1.6k stars) exposes:
```python
smc.fvg(ohlc, join_consecutive=False)
smc.swing_highs_lows(ohlc, swing_length=50)
smc.bos_choch(...); smc.ob(...); smc.liquidity(...)
```
All return DataFrames suitable for backtesting/feature engineering.

**Performance evidence**: a Medium backtest of 2,600 trades over 10 assets (BTC, ETH, SOL, XRP, gold, FX, NAS100, SPX) Jan 2024–Mar 2026 reports **61.2% win rate, 2.17 profit factor, +2.27R per win** ([Quantum Algo, 2026](https://medium.com/@space.garaa/i-backtested-2-600-trades-using-smart-money-concepts-heres-what-actually-works-bb3c671098c6)). **Caveats**: no drawdown reported, no max consecutive losses, author sells the TradingView indicator ($19/mo) and a course → conflict of interest.

**Skepticism (section 10)**:
- No peer-reviewed academic study validates ICT/SMC.
- Claims that "smart money hunts retail liquidity" are unfalsifiable — retail liquidity in BTC perps is a small fraction of CME + institutional flow.
- Marketed win rates (70-90%) on educator pages are unreplicated.
- Verdict: **use SMC primitives as features in a multi-signal model**, not as a standalone strategy.

Sources: [SMC GitHub](https://github.com/joshyattridge/smart-money-concepts), [DailyPriceAction SMC guide](https://dailypriceaction.com/blog/smart-money-concepts/), [Altrady SMC](https://www.altrady.com/crypto-trading/smart-money-concept), [SMC skepticism — LiteFinance](https://www.litefinance.org/blog/for-beginners/best-technical-indicators/smart-money-concept/).

---

## 2. Wyckoff method — partially codable

**Codable subset**:
- Range detection (consolidation after trend) → Bollinger width contraction or ATR/price ratio threshold.
- Spring/upthrust = false breakout below/above range, easy to detect post-hoc with 5-15 bars confirmation.
- Volume confirmation (climactic volume = N×avg volume on bar with low close-to-low ratio).

**Hard to code**: the "composite man" narrative phases (PS, SC, AR, ST, LPS) which require subjective sequencing. No mainstream open-source library implements full Wyckoff phase detection in 2025.

**Practical implementations 2025**: Phemex, 3Commas, TradeSanta document Wyckoff *strategies* but actual automation reduces to range-breakout + volume filter + RSI/MACD confluence. There's no Wyckoff-specific bot with audited live performance.

Sources: [3Commas Wyckoff guide](https://3commas.io/blog/the-wyckoff-method-explained), [Phemex Wyckoff 5 steps](https://phemex.com/academy/wyckoff-accumulation), [Binance Academy Wyckoff](https://www.binance.com/en/academy/articles/the-wyckoff-method-explained).

---

## 3. Order flow / footprint — retail tools 2025

**Retail platforms**:
- **Exocharts** (crypto-native): VWAP, bid-ask imbalance, stacked imbalances, liquidations, OI. ~$50/mo tier.
- **Bookmap**: $16-79/mo, real-time DOM heatmap.
- **ATAS**: ~$85/mo, cluster charts.
- **Quantower**: $70/mo or $1,590 lifetime.
- **Cignals.io**: crypto-focused order flow.

**Codable signal**: bid/ask imbalance ratio ≥ 3:1 at a price level → directional pressure. Requires L2/trades feed (most CEX REST APIs don't expose; need WebSocket trade tape + order book).

Sources: [NinjaTrader footprint](https://ninjatrader.com/futures/blogs/ninjatrader-order-flow/), [Buildix footprint guide 2026](https://www.buildix.trade/blog/how-to-read-footprint-charts-crypto-trading-guide-2026), [Exocharts](https://exocharts.com/), [Cignals.io](https://cignals.io/).

---

## 4. Liquidation data — Coinglass as edge

**API**: `GET open-api-v4.coinglass.com/api/futures/liquidation/heatmap/model1`
- Params: exchange, symbol, range (12h/24h/3d/7d/30d/90d/180d/1y).
- **Pricing**: starts $29/mo for hobbyists, scales for L2/L3 books.
- Coverage: Binance, OKX, Bybit, CME, Bitget, Deribit + others.

**Edge**: liquidation clusters act as price magnets — leveraged longs/shorts at clustered leverage levels create predictable cascade zones. Codable signal: **distance to nearest large liquidation cluster** (in % of price) as a feature; entries on bounce after cluster wipe show measurable mean-reversion in studies cited by Coinglass community (no independent academic validation).

Sources: [Coinglass heatmap](https://www.coinglass.com/pro/futures/LiquidationHeatMap), [Coinglass API docs](https://docs.coinglass.com/reference/liquidation-heatmap), [CoinGlass pricing](https://www.coinglass.com/pricing).

---

## 5. CVD (Cumulative Volume Delta) — divergence signal

**Definition**: Σ(buy_market_volume − sell_market_volume).

**Codable signal**: classic divergence
- Price LL + CVD HL → bullish reversal candidate.
- Price HH + CVD LH → bearish exhaustion.

**2025 advances**: aggregated CVD across exchanges (multi-venue), ML divergence detection. Coinglass exposes spot CVD chart.

**Caveat**: CVD on perps vs spot tells different stories — perp CVD includes leveraged speculation noise; spot CVD is closer to "real" demand. Combine both.

**Empirical edge**: no large-N peer-reviewed study, but consistently used by professional desks. Treat as confirmation layer, not standalone trigger.

Sources: [Bookmap CVD guide](https://bookmap.com/blog/how-cumulative-volume-delta-transform-your-trading-strategy), [Phemex CVD ultimate guide](https://phemex.com/academy/what-is-cumulative-delta-cvd-indicator), [Coinglass CVD](https://www.coinglass.com/learn/what-is-cumulative-volume-delta-cvd), [LuxAlgo CVD](https://www.luxalgo.com/blog/cumulative-volume-delta-explained/).

---

## 6. Open Interest — regime signal

**Codable signal pairs (highest edge)**:
- **Rising OI + rising price** → trend continuation, longs adding.
- **Rising OI + falling price** → shorts adding, bearish.
- **Falling OI + rising price** → short squeeze (longs taking profit, shorts covering).
- **Falling OI + falling price** → long capitulation.

**With funding rate**:
- Funding > +0.05%/8h sustained + rising OI → crowded long → fade setup.
- Cross-exchange funding divergence > 0.1% → arbitrage entry.

**Practical**: every serious 2025 crypto bot architecture includes OI delta + funding as features ([Gate Wiki 2026](https://web3.gate.com/crypto-wiki/article/how-do-futures-open-interest-and-funding-rates-signal-crypto-derivatives-market-trends-in-2026-20260202), [BitMEX 2025 Q3 derivatives report](https://www.bitmex.com/blog/2025q3-derivatives-report), [Amberdata funding rates](https://blog.amberdata.io/funding-rates-how-they-impact-perpetual-swap-positions)).

---

## 7. VWAP & Anchored VWAP

**Standard VWAP**: ambiguous in 24/7 crypto (no session boundary). Use rolling 24h or daily UTC.

**Anchored VWAP**: anchor at swing high/low, halving, ETF approval, BOS, regime pivot — acts as dynamic S/R. **Most useful PA tool that's trivially codable** (cumulative Σ(price×vol)/Σ(vol) from anchor).

Codable strategy: long when price reclaims rising AVWAP from major swing low + volume confirmation; short symmetric. Easily backtestable in Python (pandas cumsum); no exotic library required.

Sources: [Mudrex VWAP 2025](https://mudrex.com/learn/vwap-in-crypto/), [TrendSpider AVWAP](https://trendspider.com/learning-center/anchored-vwap-trading-strategies/), [QuantVPS VWAP backtest Python](https://www.quantvps.com/blog/backtest-vwap-trading-strategy-python).

---

## 8. Volume Profile / VPVR

**Codable**: yes, with caveats. Use **fixed-range volume profile** (FRVP) over a defined lookback, not VPVR (which is screen-relative and visual).

**Signal**: HVN = magnet/target/S-R; LVN = fast-traversal zone (price doesn't linger). Standard implementation: bin price range into N buckets, sum volume per bin, top decile = HVN.

**Reality check**: popular bot platforms (Shrimpy, Coinrule, 3Commas) **don't natively support volume profile**. Custom implementation required (Python: `pandas.cut` + groupby aggregation is ~10 LOC).

Sources: [Coinglass VPVR](https://www.coinglass.com/learn/vpvr-legend-en), [GoodCrypto VP guide](https://goodcrypto.app/ultimate-guide-to-volume-profile-vpvr-vpsv-vpfr-explained/), [AltcoinTrading VPVR](https://www.altcointrading.net/strategy/vpvr-trading-volume-profile-visible-fixed/).

---

## 9. Hybrid SMC + indicators + bot — 2025-2026 state

**Working pattern (the only architecture with credible results)**: SMC primitives as features → ML/rule layer for filtering → execution.

- Gainium community: SMC indicators feeding 3Commas/Gainium bots; mixed reports, no audited track records.
- LuxAlgo SMC indicator: most popular paid SMC layer, integrated via TradingView webhooks.
- Cryptotailor: paid SMC automation, anecdotal reports.

**No publicly audited successful 2025-2026 implementation** of pure SMC bot exists. All credible setups use SMC as a confluence/filter layer with derivatives data (OI, funding, liquidations) doing the heavy lifting.

Sources: [Gainium SMC community](https://community.gainium.io/t/smart-money-concepts-smc-indicators-and-automation/61), [LuxAlgo SMC](https://www.luxalgo.com/library/indicator/smart-money-concepts-smc/), [Cryptotailor SMC automation](https://cryptotailor.io/academy/tutorials/smart-money-concepts-automated-trading).

---

## 10. Honest skepticism — is SMC profitable for retail?

**Findings**:
- Zero peer-reviewed academic studies validate ICT/SMC.
- All "high win rate" claims (70-90%) come from educators selling courses/indicators.
- The most rigorous public backtest (2,600 trades) reports 61% WR / 2.17 PF but **omits drawdown** — a critical red flag.
- "Smart money hunts retail liquidity" thesis is unfalsifiable; retail liquidity is a tiny fraction of total flow vs ETFs/CME.
- ICT founder's own track record is undocumented.

**Position**: SMC patterns (FVG, OB, BOS) are real *artifacts* of price action — they exist on charts. Whether trading them generates positive expected value above naive baselines (buy-and-hold, momentum, mean-reversion) is **unproven**. Use as features, not gospel.

---

## Codable signals ranked by evidence quality

| Signal | Codability | Evidence quality | Edge claim |
|---|---|---|---|
| OI + funding extreme regime filter | Trivial | Strong (multi-source) | Contrarian fade |
| Liquidation cluster proximity (Coinglass) | API call | Medium-strong | Mean-reversion magnet |
| CVD divergence on perps + spot | Easy | Medium (practitioner consensus) | Exhaustion |
| Anchored VWAP from regime pivot | Trivial | Medium | Dynamic S/R |
| HVN/LVN from FRVP | Easy | Medium | Magnet/target |
| FVG (smc lib) | Library | Weak (no academic) | Confluence only |
| Order Block / BOS / CHoCH | Library | Weak | Confluence only |
| Wyckoff phase detection | Hard | Weak | Discretionary |
| Bid/ask imbalance footprint | Needs L2 feed | Medium | Microstructure |

---

## Disagreements found

- **Educators vs skeptics on SMC**: educators claim 60-90% WR; skeptics argue no manipulation evidence and retail liquidity is irrelevant.
- **CVD on perps vs spot**: practitioners disagree on which is the "true" signal — most now triangulate both.
- **VWAP anchoring**: no consensus on which event to anchor (halving, ETF, regime, swing) — depends on regime.
- **Wyckoff in crypto**: Finimize and Wyckoff Analytics argue it works; quants argue lack of crypto-specific volume normalization makes Wyckoff phases ambiguous on 24/7 markets.

---

**File**: `/home/tony/projets/tonyderide/niam-bay/docs/research/10-price-action-smc.md`
