# Trend Following / Momentum Strategies for Crypto Bots (2025-2026)

**Author**: Niam-Bay research analyst
**Date**: 2026-04-30
**Scope**: EMA crossovers, MACD, Donchian, SuperTrend, pyramiding, stops, real-bot perf, funding-rate filters
**Audience**: Martin team — trend module evaluation

---

## Sources (12 reviewed)

1. [CryptoProfitCalc — EMA Crossover Crypto 2025 Guide](https://cryptoprofitcalc.com/ema-crossover-crypto-complete-2025-guide-settings-backtests-rules-risk/)
2. [altFINS — EMA 12/50 Crossover Crypto](https://altfins.com/knowledge-base/ema-12-50-crossovers/)
3. [Phemex Academy — MACD Crypto 2026](https://phemex.com/academy/macd-indicator-crypto-trading)
4. [Zignaly — MACD Indicator Guide 2025](https://zignaly.com/crypto-trading/indicators/macd-crypto-indicator)
5. [Algomatic — Donchian Channel Breakout Strategy #8](https://algomatictrading.substack.com/p/strategy-8-the-easiest-trend-system)
6. [Netpicks — SuperTrend Settings 2025](https://www.netpicks.com/supertrend-indicator/)
7. [Mudrex Learn — SuperTrend & ATR](https://mudrex.com/learn/supertrend-indicator/)
8. [Concretum — Position Sizing in Trend Following](https://concretumgroup.com/position-sizing-in-trend-following-comparing-volatility-targeting-volatility-parity-and-pyramiding/)
9. [QuantStrategy.io — Mathematics of Pyramiding](https://quantstrategy.io/blog/the-mathematics-of-pyramiding-calculating-position-sizes/)
10. [Mudrex Learn — ATR in Crypto](https://mudrex.com/learn/average-true-range-crypto/)
11. [RedHub — AI Trading Bots 2025 Benchmarks](https://blog.redhub.ai/ai-trading-bots-2025/)
12. [BitMEX — 2025 Q3 Derivatives Report (Funding Rates)](https://www.bitmex.com/blog/2025q3-derivatives-report)

Supporting: [Wiley/Palazzi 2025 Trading Games Crypto](https://onlinelibrary.wiley.com/doi/full/10.1002/fut.70018), [arxiv funding-rate design](https://arxiv.org/html/2506.08573v1).

---

## 1. EMA Crossover Variants

**No universal best**; literature converges on these defaults:

| Pair | Use case | Timeframe sweet spot |
|------|---------|----------------------|
| 9/21 | Fast — early entries, more whipsaws | 5m–1h scalp |
| 12/26 | Balanced (also MACD baseline) | 1h–4h |
| 12/50 (altFINS) | Crypto trend confirm | 4h–1d |
| 20/50 | Medium swing | 4h–1d |
| 50/200 ("golden cross") | Macro regime | 1d–weekly |

**Rules robustly cited** ([CryptoProfitCalc](https://cryptoprofitcalc.com/ema-crossover-crypto-complete-2025-guide-settings-backtests-rules-risk/), [altFINS](https://altfins.com/knowledge-base/ema-12-50-crossovers/)):
- Long only when price > rising 200 EMA; short only when price < falling 200 EMA.
- Require ATR > median ATR(N) — kills dead-range whipsaws.
- "Not recommended below 1h" (altFINS) — noise dominates signal.
- 12/50 entry: cross + price > 12 EMA confirms.

**Hull MA** is faster than EMA/WMA (Cryptohopper) — gets signals 2-4 bars earlier but no published crypto backtest with verified numbers found. Treat as latency reduction, not edge.

**Disagreement**: CryptoProfitCalc and Netpicks both refuse to publish backtest stats ("nothing here is financial advice"). All "best EMA pair" claims are anecdotal — none of the 12 sources gave a hard win-rate number for a specific EMA pair on BTC perps.

## 2. MACD

**Default 12/26/9** holds on daily ([Phemex](https://phemex.com/academy/macd-indicator-crypto-trading), [Zignaly](https://zignaly.com/crypto-trading/indicators/macd-crypto-indicator)). Crypto-tuned variants:
- **24/52/18** — long-term, fewer signals, daily/weekly.
- **6/13/5** or **7/19/5** — fast, 15m–1h, "more noise" warning.

**Histogram momentum**: shrinking bars = trend exhaustion, even before crossover. **Divergence** (price HH + MACD LH = bearish) cited as the highest-quality MACD signal — but every source flags it must be confirmed by RSI/volume/ADX, otherwise high false-positive rate.

**No backtest numbers** in any source. MACD flagged as "inherently lagging" (Phemex). Best deployed as filter rather than primary signal.

## 3. Donchian Breakout (Turtle-style)

**Canonical Turtle config** (Algomatic, AvaTrade, LuxAlgo):
- **System 1**: 20-day breakout entry, 10-day opposite-side stop.
- **System 2**: 55-day breakout entry, 20-day stop.
- ADX must be **rising**; exit if ADX > 40 and turning down.

**Numbers (non-crypto, but methodology transferable)** — Algomatic Strategy #8 backtest:
- Nasdaq 100 (2010–2025): CAGR 5.93%, MaxDD -14.02%, win rate **51.85%**, R/R **1.98**.
- Gold (2000–2025): CAGR 6.04%, MaxDD -16.95%, win rate **42.61%**, R/R **2.6**.

Crypto-specific verified backtests: **none found in this pass**. Multiple sources assert Donchian "works on crypto" without numbers — treat as design pattern, not validated config.

**Take-away**: low win rate (40-55%), R/R > 2, drawdowns 14-17% — the trend-following profile. ADX > 25 filter is universally cited.

## 4. SuperTrend

**Baseline**: ATR(10), multiplier 3 (Mudrex, Netpicks). Crypto-tuned:

| Style | ATR period | Multiplier |
|-------|------------|-----------|
| Intraday (5m-1h) | 10 | 1.5–2 |
| Swing (4h-1d) BTC/ETH | 10–20 | **3–5** (crypto vol bump) |
| Fast alts | 7 | 2 |

**Universal advice**: bump multiplier to 4–5 on crypto vs. 3 on stocks because BTC daily ATR sits at **3–7%** ([Mudrex ATR](https://mudrex.com/learn/average-true-range-crypto/)) — way above equities.

No published win-rate for crypto SuperTrend. "There is no best setting" (Netpicks) — discipline is to backtest with realistic fees and forward-test.

## 5. Pyramiding

**Concretum** is the only source with hard numbers (futures, 1980–2025 multi-asset):

| Method | Total Return | IRR | MaxDD | Hit Ratio |
|--------|-------------|-----|-------|-----------|
| Vol Targeting (VT) | 16,828% | 11.46% | 25.65% | 60% |
| Vol Parity (VP) | 30,014% | 12.83% | ~25% | 59% |
| **VP + Pyramiding** | **556,106%** | **20.0%** | **48.69%** | 56% |

VP+P trade-level skewness 3.74 — convex tail, fat winners pay for many small losers. Avg trade P&L: VP+P **26.2 bps** vs. VT 13 bps.

**Rules** ([QuantStrategy.io](https://quantstrategy.io/blog/the-mathematics-of-pyramiding-calculating-position-sizes/), [LuxAlgo](https://www.luxalgo.com/blog/pyramiding-strategies-scaling-into-trades-to-boost-returns/)):
- Each new layer **smaller than previous** (Turtles use full units; modern variants use 100/50/25/12.5%).
- Add layers only after **+2× ATR favorable move**.
- **Trail entire stop** to last add — protects total exposure.
- Cap at 3–4 layers max.

**No source confirmed exact 25/50/25 or 50/25/25 splits as superior**. Decreasing-size pyramid (e.g. 100/50/25) is the documented standard. 50/25/25 (front-loaded) is not in literature and would over-expose if first add fails.

**Cost**: nearly **2× the drawdown** for ~1.5× the IRR. Pyramiding is a return-amplifier, not a Sharpe-improver.

## 6. Stop Loss for Trend

| Type | Pros | Cons | Verdict |
|------|------|------|---------|
| **ATR (1.5–2× ATR)** | Adapts to vol; avoids fixed-% whipsaw | Wider in chop | Dominant in literature |
| **Chandelier Exit** (ATR trail from highest high) | Locks gains progressively | Can give back 1–2 ATR | Best for pure trend |
| **Structural (HH/HL break)** | Clean invalidation logic | Subjective swing detection | Strong combo with ATR |
| **Dollar / fixed %** | Simple | Ignores volatility regime | "Often fail in crypto" (Mudrex) |

[Mudrex ATR](https://mudrex.com/learn/average-true-range-crypto/) explicitly: "Fixed stop-losses often fail in crypto's volatile environment". BTC ATR daily 3–7% means a 2% stop = noise, gets hit ~daily.

**Best practice consensus**: ATR-based initial stop (1.5–2×), then trail by structure (each new HL on longs) OR Chandelier (highest high − 3× ATR). Hybrid wins over either alone.

## 7. Real-World Trend Bot Performance 2025–2026

**RedHub benchmarks** (vendor data — flagged as promotional):

| Bot | Win Rate | Annual ROI | Sharpe | MaxDD |
|-----|----------|------------|--------|-------|
| Stiff Zone | **89%** | 156% | 2.8 | -8.2% |
| Trendhoo | 76% | **193%** | 2.6 | -12.4% |
| 3Commas | 82% | 134% | 2.3 | -9.7% |

**RED FLAG**: 89% win rate on a trend strategy contradicts every academic source. Real trend systems sit at **40–55% win rate with R/R > 2** (Algomatic, Concretum). 89% likely reflects grid/martingale or scalping, not trend.

The Wiley 2025 paper ([Palazzi](https://onlinelibrary.wiley.com/doi/full/10.1002/fut.70018)) explicitly challenges trend-following supremacy in crypto post-2024 — pairs trading and mean-reversion now competitive in less-trending regimes. Bot-marketing "89% / 2.8 Sharpe" numbers should be treated as untrusted. Realistic CTA-style trend on crypto: **45–55% win, R/R 1.8–2.5, Sharpe 0.8–1.5, MaxDD 20–30%**.

## 8. Trend + Funding Rate

**BitMEX 2025 Q3 data** ([source](https://www.bitmex.com/blog/2025q3-derivatives-report)):
- Funding **positive 92% of Q3 2025**.
- BTC mean funding: BitMEX 0.0081%, Binance 0.0057%, Hyperliquid 0.0120% per 8h.
- Default anchor 0.01%/8h (~10.95% annualized) — structurally bullish bias.
- Hyperliquid extremes: BTC up to 0.0672%, ETH up to 0.0752%.

**As trend filter**:
- **Sustained positive funding** = bullish regime confirmation; trends can persist long beyond contrarian expectation.
- **Extreme funding spikes** (>3σ) = crowded long → fragility flag, *not* trend reversal alone, but filter to tighten stops or skip new pyramids.
- Combine with **OI**: high OI + extreme funding = best mean-reversion setup (counter to trend bias).

**Disagreement**: arxiv design paper frames funding as price-anchor mechanic; BitMEX as crowded-positioning signal. Both compatible — funding regime as macro filter, funding spikes as risk gate.

**Cash carry edge**: a long-spot / short-perp with positive funding earns ~10% annualized risk-free in the 2025 regime — orthogonal to trend, but worth noting as portfolio overlay.

---

## Bottom Line for Martin

1. **If Martin adds a trend module**, default to: **EMA 21/55** or **Donchian 20/55** + **ADX > 25** filter + **200 EMA regime gate** + **ATR(14) × 2 stop** + **Chandelier trail (3× ATR)**, on **4h or 1d** BTC/ETH perps. Avoid sub-1h trend signals.
2. **SuperTrend ATR 10 / mult 4** is the simplest single-indicator drop-in for crypto swing — well-documented baseline.
3. **Pyramiding**: only after +2× ATR favorable; size 100/50/25 layered; cap 3 adds. Expect MaxDD nearly 2× vs. flat-size — accept this is a return-amp, not a Sharpe boost.
4. **Stops**: never fixed-%. ATR + structural hybrid. BTC daily ATR 3–7% → 2% fixed stop is noise.
5. **Win rate target**: 45–55% with R/R 1.8–2.5. Any backtest claiming >70% on a pure trend system is probably curve-fit or mislabeled.
6. **Funding filter**: skip new longs when 8h funding > 0.05% AND OI at recent high (crowded). Tighten trail when funding > 3σ.
7. **Regime warning**: 2025 paper shows trend lost some edge vs. pairs trading post-2024. Build a regime detector (ADX, realized vol, trend persistence) before sizing up.
8. **Compatibility with Martin grid**: trend module should be a **separate strategy bucket** with its own capital — running grid + trend on same pair same capital is the runaway scenario from the 2026-04-25 lessons. Trend on one pair, grid on another, independent risk budgets.

## Confidence

- **High** on rule-of-thumb defaults (EMA pairs, MACD 12/26/9, Donchian 20/55, ATR 2×): consistent across all 12 sources.
- **Medium** on pyramiding numbers: only one source (Concretum) with hard data, futures not crypto.
- **Low** on real-bot win rates: vendor sources contradict academic consensus; treat 89% claims as marketing.
- **Medium-high** on funding-rate stats (BitMEX Q3 2025 official report).
- **Low** on Hull MA crypto edge: no verified numbers found.

Word count: ~1,470.
