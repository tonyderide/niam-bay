# Market Making Strategies for Crypto Bots (2025-2026)

**Research date:** 2026-04-30
**Author:** Niam-Bay research analyst
**Scope:** Practical MM for retail crypto bots, with focus on Kraken Futures viability for a Java-based bot at 100-300ms latency.

---

## TL;DR

- **Avellaneda-Stoikov is the academic backbone**, but raw equations need heavy customization. Hummingbot's "simplified" implementation reduces it to two knobs: `min_spread` and `max_spread`, with inventory skew interpolating linearly between them.
- **Inventory skew** is the single most impactful protection against trending markets. Standard formula: `Adjusted Bid = Mid - HalfSpread - InventorySkew * InventoryDeviation`. Hummingbot's `inventory_target_base_pct` + `inventory_range_multiplier` is the production-grade abstraction.
- **Adverse selection / toxic flow detection** is real and crippling. VPIN is the canonical metric; in practice retail bots get adversely-selected for ~10% of effective spread on average. Defense = wider spreads + auto-withdraw on high VPIN.
- **Kraken Futures maker rebates only kick in at $250M+ 30-day volume** (-0.003%), going to -0.006% at $1B+. **Below $100M volume, you pay 0% to 0.02% maker — no rebate**. A retail bot will not earn rebates at Kraken Futures; the edge case for low-spread MM does not work without scale.
- **Latency reality:** retail at 100-300ms achieves only **31-48% hit rate** vs <50ms latency at 82%. Java bot at 100-300ms is **non-viable for tight-spread MM** on liquid pairs (BTC/ETH); marginal viability on illiquid pairs with wide spreads (>30bps) where speed matters less.
- **Real net APY 2025-2026:** Hummingbot publishes **no audited performance**. Liquidity Mining yields exclude P&L from trading. Anecdotal reports of profitable Hummingbot users exist but no verified APY numbers. Conservative estimate for retail PMM on Tier-1 CEX: **negative to flat after fees and adverse selection**, unless pair is illiquid AND volatility is moderate.

**Verdict for Niam-Bay:** Pure market making on Kraken Futures with a 100-300ms Java bot is **not recommended as primary strategy**. Grid trading (already deployed in Martin) is structurally similar but more forgiving on latency.

---

## 1. Avellaneda-Stoikov Model

The 2008 paper is the reference model. Two outputs:

**Reservation price** (mid skewed by inventory):
```
r(s, q, t) = s − q · γ · σ² · (T − t)
```
where `s` = mid, `q` = signed inventory, `γ` = risk aversion, `σ²` = variance, `T-t` = time-to-horizon.

**Optimal bid-ask spread:**
```
δᵃ + δᵇ = γ·σ²·(T−t) + (2/γ) · ln(1 + γ/κ)
```
where `κ` = order book intensity (how fast orders fill at given distance).

### Practical translation (Hummingbot)

Hummingbot derives γ from user-defined min/max spread bounds:
```
γ ≤ (Max_Spread − Min_Spread) / (2 · |q| · σ²)
```
A simplified "easy mode" reduces the model to: pick min spread (competitive) and max spread (worst-case inventory), and the bot interpolates.

Source: [hummingbot.org technical deep dive](https://hummingbot.org/blog/technical-deep-dive-into-the-avellaneda--stoikov-strategy/), [Open Crypto Trading Initiative simplified A-S](https://medium.com/open-crypto-market-data-initiative/simplified-avellaneda-stoikov-market-making-608b9d437403).

---

## 2. Hummingbot Strategies (2025-2026)

| Strategy | Use case | Status |
|----------|----------|--------|
| **Pure Market Making (PMM v1)** | Single pair, single CEX spot | Stable, monolithic |
| **PMM Simple V2** | Modular controllers, easier extension | Active dev 2025 |
| **Avellaneda Market Making** | Inventory-aware A-S | Available |
| **Liquidity Mining** | Earn token rewards for placing maker orders | Active, rewards exclude trading P&L |
| **Cross-Exchange MM (XEMM)** | Quote on exchange A, hedge on exchange B | Available, requires inventory on both |

### Real performance data
- Hummingbot publishes **no audited APY numbers**. Backtesting dashboard outputs Net PNL, Max DD, Sharpe, Profit Factor — but no aggregated user results.
- Liquidity Mining "Yield/Day" explicitly excludes P&L from trading. Users may show 5-15% APY in token rewards while losing money on the underlying inventory.
- Anecdotal: one user since 2021 launched an algo-trading startup (cited in Hummingbot blog). No numbers disclosed.

Source: [hummingbot.org/strategies](https://hummingbot.org/strategies/), [docs.hummingbot.io faq/liquidity-mining](https://docs.hummingbot.io/faq/liquidity-mining/).

---

## 3. Inventory Skew Formulas

**Hummingbot model:**
- `inventory_target_base_pct` (e.g. 50%)
- `inventory_range_multiplier` (e.g. 1.0)

Allowable range: `Target ± (Multiplier × Total_Order_Size_as_%_of_Portfolio)`.

Example: 10 BTC portfolio, 50% target, 1 BTC order, 1.0 multiplier → range 40%-60%. Above 60%: no buys. Below 40%: no sells.

**Linear quote skew (canonical):**
```
Adjusted_Bid = Mid − HalfSpread − InventorySkew · (q − q_target)
Adjusted_Ask = Mid + HalfSpread − InventorySkew · (q − q_target)
```

When inventory is too long, both bid AND ask shift down → ask becomes more aggressive (sells faster), bid less aggressive (buys slower). Symmetric when short.

Source: [hummingbot inventory-skew docs](https://hummingbot.org/strategies/v1-strategies/strategy-configs/inventory-skew/), [GitHub inventory_skew_calculator.pyx](https://github.com/hummingbot/hummingbot/blob/master/hummingbot/strategy/pure_market_making/inventory_skew_calculator.pyx).

---

## 4. Adverse Selection Protection

**Toxic flow** = informed traders picking off stale quotes. Two sources in crypto:
1. **Speed asymmetry** — others see CEX move first, hit your DEX/slow-venue quote.
2. **Coverage asymmetry** — others see liquidations / OTC / correlated assets.

**Empirical impact:** adverse-selection costs ≈ **10% of effective spread** on average in crypto (Tiniç & Sensoy, Nottingham repository).

### Detection: VPIN

Volume-Synchronized Probability of Informed Trading (Easley, López de Prado, O'Hara, 2010). Computed in volume buckets (not time):
```
VPIN = Σ |V_buy − V_sell| / Σ V_total
```
over rolling N volume buckets.

**Rule:** when VPIN > threshold (typically 0.4-0.6 depending on asset), market makers widen spreads or withdraw. The 2010 Flash Crash saw VPIN at historical highs **1 hour before** the crash.

### Practical defenses for retail bots
- **Markout PnL monitoring** — track P&L 1s, 10s, 60s after each fill. Negative markout = adverse selection.
- **Auto-cancel on rapid mid-price move** (>2σ in 1 second).
- **Quote refresh on order book imbalance** (e.g. bid_volume / ask_volume > 3:1 → skew quotes away).
- **Withdraw entirely** during news / liquidation cascades.

Sources: [VPIN paper](https://www.quantresearch.org/VPIN.pdf), [Easley/López de Prado Flow Toxicity NYU Stern](https://www.stern.nyu.edu/sites/default/files/assets/documents/con_035928.pdf), [CoinAPI order flow toxicity](https://www.coinapi.io/learn/glossary/order-flow-toxicity), [arxiv 2508.20225 Optimal Quoting under Adverse Selection](https://arxiv.org/abs/2508.20225).

---

## 5. Kraken Futures Maker Rebates — Edge Calculation

**Actual fee schedule (verified 2026-04-30):**

| 30-day volume | Maker | Taker |
|---------------|-------|-------|
| $0+ | 0.0200% | 0.0500% |
| $100M+ | **0.0000%** | 0.0200% |
| $250M+ | **−0.0030%** | 0.0175% |
| $500M+ | −0.0050% | 0.0150% |
| $1B+ | −0.0060% | 0.0135% |

**Critical finding:** the often-cited "−0.01% maker fee" is **not the standard rate**. It only existed during specific super-volume promo tiers and required $1B+ volume. The standard retail maker fee is **0.02%** — meaning each maker fill *costs* 2bps, not earns.

**Edge math for retail (assuming 0.02% maker, no rebate):**
- Round-trip cost: 2 fills × 0.02% = 4bps
- Minimum profitable spread (excluding adverse selection): >4bps
- With adverse selection ~10% of effective spread: realistic minimum profitable spread ≈ 6-8bps
- Below this, you're paying to provide liquidity.

**Conclusion:** Kraken Futures maker rebate edge **does not exist for retail**. Need >$250M monthly volume to flip from cost to rebate.

Sources: [Kraken fee schedule](https://www.kraken.com/features/fee-schedule), [Kraken super-volume rebate blog](https://blog.kraken.com/product/kraken-derivatives/announcing-super-volume-rebate-tiers-for-kraken-futures).

---

## 6. Volatility-Adjusted Spreads

**EWMA** (Riskmetrics, λ ≈ 0.94 daily, 0.97 intraday):
```
σ²ₙ = λ · σ²ₙ₋₁ + (1−λ) · r²ₙ₋₁
```
Computationally cheap, no mean reversion.

**GARCH(1,1):**
```
σ²ₙ = ω + α · r²ₙ₋₁ + β · σ²ₙ₋₁
```
Adds long-run mean (ω) — better in regime-changing crypto. Typical fitted params for BTC: α ≈ 0.10, β ≈ 0.85.

**Square-root-of-time scaling** (essential for spread sizing across horizons):
```
σ(T) = σ(t) · √(T/t)
```
Example: 1s vol of 0.1% → 30s vol = 0.1% · √30 ≈ 0.548%.

**Spread formula (rule of thumb):**
```
Spread = max(min_spread, k · σ(refresh_interval))
```
where `k` is risk-aversion multiplier (typically 1.5-3.0).

Sources: [EWMA & GARCH calculator (O'Connell)](https://ryanoconnellfinance.com/calculators/ewma-volatility-calculator/), [Volatility-Time-Market-Making (Medium)](https://medium.com/@cryptotrade606/volatility-time-and-market-making-why-scaling-risk-matters-0e1ac9c1f96d).

---

## 7. Latency Requirements — Java Bot at 100-300ms?

**Hard data on hit rate by latency** (CoinAPI / Adrian Keller production system):

| Latency | Fill success rate |
|---------|-------------------|
| <50ms | 82% |
| 50-100ms | 67% |
| 100-150ms | 48% |
| >150ms | 31% |

**Crypto MM is "millisecond, not microsecond" game** — exchange matching engines themselves take 5-10ms, so going below ~10ms client-side has diminishing returns.

**For a Java bot at 100-300ms:**
- Tight-spread MM on BTC/ETH (spreads 1-3bps): **not viable** — you'll be picked off >50% of the time.
- Wide-spread MM on illiquid alts (spreads 20-100bps): **marginally viable** — latency matters less when the spread is wider than the typical move during the latency window.
- Grid trading (Niam-Bay's Martin): **viable** — grid orders are placed in advance and don't compete on speed; this is structurally a passive form of MM that tolerates 100-300ms.

Sources: [HFT in crypto: latency reality (Keller)](https://medium.com/@laostjen/high-frequency-trading-in-crypto-latency-infrastructure-and-reality-594e994132fd), [CoinAPI scalping 2025](https://www.coinapi.io/blog/is-crypto-scalping-still-profitable-2025-coinapi-data-driven-insights), [LuxAlgo latency standards](https://www.luxalgo.com/blog/latency-standards-in-trading-systems/).

---

## 8. Real-World Performance 2025-2026

**The dirty secret:** there is no public, audited, reproducible MM bot APY data for retail crypto. Sources disagree:

- **Hummingbot Foundation:** publishes backtest infrastructure, no aggregated user APY.
- **Capstone study (AUA 2025):** cointegrated pairs trading achieved Sharpe 3.97, MaxDD 7.94% — but this is stat-arb, not MM.
- **XBTO research 2020-2025:** trend-following Sharpe 1.62 vs passive BTC 0.95. Not MM.
- **Cointelegraph 2025:** grid bots "double-digit profits" in downtrends — vague, no methodology.
- **Coincub 2025:** "costs, latency and competition erase most retail advantages... bots remain useful tools, but never a guaranteed source of income."

**Realistic estimate for retail PMM (synthesized):**
- Best case (illiquid alts, moderate vol, manual oversight): **5-15% APY net of fees**, with high variance and tail risk.
- Median case (BTC/ETH pairs on Kraken Futures, no rebate, 200ms latency): **negative to flat**.
- Liquidity Mining token rewards: 5-30% APY in tokens, but ignores P&L on inventory which can be -50% in a drawdown.

Sources: [AUA Capstone 2025 algorithmic trading review](https://cse.aua.am/wp-content/uploads/2025/06/Capstone-final.pdf), [XBTO crypto risk-adjusted performance](https://www.xbto.com/resources/the-quality-of-returns-crypto-risk-adjusted-performance), [Coincub 2025 bots review](https://coincub.com/are-crypto-trading-bots-worth-it-2025/).

---

## Disagreements / Open Questions

1. **Avellaneda-Stoikov in practice:** academic consensus says it's the optimal model; practitioners (Hummingbot blog, Crypto Chassis) say it's "too theoretical, requires customization." Both are right — A-S is the framework, not the implementation.
2. **VPIN reliability:** original 2010 paper claims it predicted Flash Crash 1h ahead; later academic critiques (Andersen & Bondarenko 2014) argue it's just a noisy lagging indicator. Use as one signal among many, not standalone trigger.
3. **Maker rebates as edge:** institutional MMs swear by them (DWF Labs, Wintermute); retail-focused authors note rebates require volumes retail will never hit. Both correct — different tiers, different game.

---

## Recommendations for Niam-Bay / Martin

1. **Do not pivot Martin from grid to MM.** Grid is structurally MM-lite without the latency disadvantage.
2. If exploring MM: target **illiquid pairs with >30bps natural spread**, not BTC/ETH.
3. **Implement markout-PnL monitoring** as a standalone telemetry layer — useful for grid too (detects when fills are systematically toxic).
4. **EWMA volatility** is enough; GARCH overhead not worth it at 100-300ms.
5. **Forget Kraken Futures maker rebates.** Compute edge assuming 0.02% maker fee.

---

## Sources Consulted

1. [Hummingbot — Technical Deep Dive into Avellaneda-Stoikov](https://hummingbot.org/blog/technical-deep-dive-into-the-avellaneda--stoikov-strategy/)
2. [Crypto Chassis — Simplified Avellaneda-Stoikov](https://medium.com/open-crypto-market-data-initiative/simplified-avellaneda-stoikov-market-making-608b9d437403)
3. [Hummingbot — Pure Market Making strategy](https://hummingbot.org/strategies/v1-strategies/pure-market-making/)
4. [Hummingbot — Inventory Skew](https://hummingbot.org/strategies/v1-strategies/strategy-configs/inventory-skew/)
5. [GitHub — Hummingbot inventory_skew_calculator](https://github.com/hummingbot/hummingbot/blob/master/hummingbot/strategy/pure_market_making/inventory_skew_calculator.pyx)
6. [VPIN original paper (Easley, López de Prado, O'Hara)](https://www.quantresearch.org/VPIN.pdf)
7. [NYU Stern — Flow Toxicity and Liquidity in HF World](https://www.stern.nyu.edu/sites/default/files/assets/documents/con_035928.pdf)
8. [CoinAPI — Order Flow Toxicity glossary](https://www.coinapi.io/learn/glossary/order-flow-toxicity)
9. [arXiv 2508.20225 — Optimal Quoting under Adverse Selection](https://arxiv.org/abs/2508.20225)
10. [Kraken — Fee Schedule](https://www.kraken.com/features/fee-schedule)
11. [Kraken Blog — Super-Volume Rebate Tiers Futures](https://blog.kraken.com/product/kraken-derivatives/announcing-super-volume-rebate-tiers-for-kraken-futures)
12. [Adrian Keller — HFT in Crypto: Latency, Infrastructure, Reality](https://medium.com/@laostjen/high-frequency-trading-in-crypto-latency-infrastructure-and-reality-594e994132fd)
13. [LuxAlgo — Latency Standards in Trading Systems](https://www.luxalgo.com/blog/latency-standards-in-trading-systems/)
14. [Ryan O'Connell — EWMA & GARCH Volatility](https://ryanoconnellfinance.com/volatility-estimation-garch/)
15. [Crypto Trade — Volatility, Time, and Market-Making](https://medium.com/@cryptotrade606/volatility-time-and-market-making-why-scaling-risk-matters-0e1ac9c1f96d)
16. [AUA 2025 Capstone — Algorithmic Trading Review](https://cse.aua.am/wp-content/uploads/2025/06/Capstone-final.pdf)
17. [XBTO — Crypto Risk-Adjusted Performance](https://www.xbto.com/resources/the-quality-of-returns-crypto-risk-adjusted-performance)
18. [Coincub — Are Crypto Trading Bots Worth It in 2025](https://coincub.com/are-crypto-trading-bots-worth-it-2025/)
19. [DWF Labs — 4 Core Crypto Market Making Strategies](https://www.dwf-labs.com/news/4-common-strategies-that-crypto-market-makers-use)
20. [ScienceDirect — Bitcoin wild moves: Order flow toxicity](https://www.sciencedirect.com/science/article/pii/S0275531925004192)
