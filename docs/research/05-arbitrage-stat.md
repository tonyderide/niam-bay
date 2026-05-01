# 05 — Arbitrage & Statistical Strategies (Crypto, 2025-2026)

**Author**: research analyst  
**Date**: 2026-04-30  
**Capital constraint**: ~$135 (Kraken Futures, retail)  
**Scope**: Funding-rate arb, cross-exchange arb, contrarian funding signals, triangular arb, stat-arb pairs, liquidation cascades, DeFi yield comparison.

---

## TL;DR

- **Funding-rate cash-and-carry**: ~14% APY (2024) → ~19% APY (2025) on majors. Academic samples show up to 115% in 6 months on alts with max DD 1.92%, but retail needs minimum **$300+** to cover fees and basis dust. Below that, fees eat the carry.
- **Cross-exchange arb (Kraken/Binance/Bybit)**: dead for retail. Spreads 200-800 ms life, latency 8-15 ms required, withdrawal lag kills the trade. Skip.
- **Extreme funding contrarian**: works as a *filter* not a primary signal. Q3 2025 BitMEX data: funding positive 92% of time → "extreme" must be re-defined per regime. Pre-Oct-10 cascade, sustained >15% APR for 14+ days flagged the top.
- **Triangular arb**: ~1.7% per loop on $200 in cherry-picked Binance examples; in practice <0.2% after fees, requires colocation. Not viable on Kraken Futures.
- **Stat-arb (cointegration)**: BTC-ETH pair Sharpe 2.45, ~16.3% annual in published 2025 study. 37/90 pairs cointegrated 2019-2024. **Most realistic edge for $135 capital** if implemented spot-only or 2x leverage.
- **Liquidation cascades**: tradable as macro filter (avoid grid bots when OI > regime-norm + funding sustained > 15% APR). Oct 10-11 2025: $19B OI wiped in 36h.
- **Curve/DeFi yield**: 4-8% stable APY, gas+impermanent loss kills it under $1k. Kraken Futures funding > Curve risk-adj at this size.

**Recommendation for $135**: stat-arb BTC-ETH pair (paper-traded first) > funding carry on a single Kraken perp short hedged by spot. Skip cross-exchange and triangular.

---

## 1. Funding Rate Arbitrage (Cash-and-Carry)

**Mechanic**: long spot + short perp (or reverse). Earn the funding payment, neutral on price.

| Metric | Value | Source |
|---|---|---|
| Avg APY 2024 | 14.39% | ArbitrageGhost / 2025 academic |
| Avg APY 2025 | 19.26% | same |
| Conservative monthly | ~0.45% (5.4% APY) | Buildix |
| BIS structural carry | 7-8% / yr persistent | BIS WP 1087 |
| SOL/XRP basis spike Jul 2025 | 50% annualized | Amberdata |
| Max funding cap (Kraken) | ±0.25% / hr | Kraken docs |
| Acad study 60 scenarios (BTC/ETH/XRP/BNB/SOL) | up to 115.9% / 6mo, max DD 1.92% | ScienceDirect 2025 |
| Min recommended capital | $300 | Gate Learn |

**For $135**: marginal. Kraken Futures taker ~0.05% + spot maker ~0.16% = ~0.42% round-trip drag. With BTC funding ~0.01%/8h (~11% APY), break-even ~14 days.

**Risks**: vol spike → basis whip → short-leg liquidation if margin tight; negative funding regime (8% of time) flips the trade; phantom fills on small balances.

**Disagreement**: ArbitrageGhost claims "10-30% minimal directional risk"; ScienceDirect 2025 says strategy has **lower volatility than HODL but comparable profits** — alpha is risk-adjusted, not absolute.

---

## 2. Cross-Exchange Arbitrage (Kraken vs Binance vs Bybit)

**State 2025**: dominated by HFT bots, retail dead.

- Spread life: **200-800 ms** before arbed away (Hyrotrader, Medium HFT).
- Latency budget: AWS → Binance Tokyo 5-12 ms; Bybit Singapore 6-14 ms; Kraken Virginia 8-15 ms. Retail 100-500 ms = too slow.
- Fees: Binance 0.075% w/ BNB discount; Bybit 0.03% taker VIP; Kraken 0.16-0.26% spot.
- Withdrawal lag: 10-60 min on-chain → spread gone before funds arrive.

**Verdict for $135**: not viable. Skip.

**Regulatory**: Binance restricted in many US states; Kraken delisted some pairs post-SEC 2024 settlement. Cross-venue legal arb in 2025 narrows to Bybit ↔ Bitget for non-US.

---

## 3. Extreme Funding Rate as Contrarian Signal

**Threshold convention**: > +0.05% / 8h = extreme greed; < -0.05% / 8h = extreme fear.

**Empirical 2025**:
- Funding positive 92% of time (BitMEX Q3 2025 derivatives report).
- "Positive funding ≠ imminent reversal": BTC 2024 was positive 339/365 days while doubling.
- **Pre-cascade signal**: sustained funding > 15% APR for 14+ days preceded Oct 10-11 2025 cascade ($19B OI wiped, $3.21B liquidated in 60s per Amberdata).

**Backtest finding**: extreme funding is a *crowdedness* indicator, not a timing tool. Useful as **risk-off filter** (close grids, reduce leverage) more than as entry.

**Yellow.com / BeInCrypto**: pair extreme funding with on-chain (exchange inflows) + OI delta for higher-confidence reversals.

---

## 4. Triangular Arbitrage (BTC/ETH/USDT)

- Single venue, 3-leg loop (e.g. USDT → BTC → ETH → USDT).
- Optimistic case: ~1.7% net on $200 with Binance 0.1% fees (Binance Square shenylow).
- Realistic floor: bots filter < 0.2% margin; opportunities last < 1 second.
- ScienceDirect 2024 ("Wish or reality?"): exploitable triangular arb in crypto is **largely illusory** for non-colocated traders.

**For $135 on Kraken**: spot fees 0.16-0.26% per leg × 3 = ~0.6% drag. Impossible to net positive without colocation. Skip.

---

## 5. Statistical Arbitrage — Cointegration Pairs

**This is the most promising bucket for small capital.**

Methods used in 2025 literature:
- **Engle-Granger 2-step** (residual stationarity via ADF).
- **Johansen test** (multivariate, ≥ 2 series).
- **Z-score entry**: typically |Z| > 2; exit on mean reversion.

**Reported 2025 results** (IJSRA 2026-0283, Springer JAM 2025, Medium Digital Alpha):

| Pair | Sharpe | Annual return | Win rate |
|---|---|---|---|
| BTC-ETH | 2.45 | 16.34% | 64.74% |
| ETH-LTC | strong cointegration | n/a | n/a |
| Range across 37/90 cointegrated pairs | 1.58 - 2.45 | n/a | n/a |

**Sample**: 90 candidate pairs, daily data Jan 2019 - May 2024 → 37 cointegrated.

**Why this fits $135**:
- Spot-only execution possible (no leverage required).
- Holding period days-weeks → fees diluted.
- Kraken supports BTC/USD + ETH/USD spot with 0.16% maker.
- Drawdowns historically modest if z-stop at ±3.

**Caveats**:
- Cointegration breaks during regime shifts (post-ETF, post-halving). Re-test rolling 6mo.
- Copula-based extension (Springer 2025) outperforms pure Engle-Granger in tail-risk handling.
- RL-based stat-arb (arXiv 2403.12180) needs >> $135 to deploy.

---

## 6. Liquidation Cascade Strategies

**2025 events**: Oct 10-11 wiped $19B OI in 36h on Trump tariff news (Zeeshan Ali SSRN); full-year 2025 liquidations $31.4B, 60% forced longs; $3.21B in 60s (Amberdata).

**Signals**: OI surge + funding > 15% APR sustained 14d → top forming. Liquidation heatmap clusters = magnet zones. Negative funding spike + high OI → short squeeze setup.

**For $135**: too small to fade a cascade. Use as **defensive filter** for Martin grids — pause/widen when triggers fire.

---

## 7. Curve / DeFi Yield (Quick Compare)

| Strategy | APY 2025 | Min capital |
|---|---|---|
| Curve 3pool stablecoin | 4-8% | ~$1k (gas) |
| Kraken funding carry | 11-19% | $300 |
| Stat-arb BTC-ETH | 16% (Sh 2.45) | $200 |

At $135, ETH gas (~$5-15/tx) makes Curve uneconomical. Arbitrum Curve drops gas to <$1 but APY 3-5%. Kraken funding carry wins risk-adjusted at this size.

---

## Disagreements

1. **Funding APY**: ArbitrageGhost 19% vs BIS 7-8% — BIS = persistent carry only; 19% includes spikes retail often misses.
2. **Contrarian funding**: Yellow/BeInCrypto bullish; BitMEX 92% positive → contrarian shorts get steamrolled.
3. **Stat-arb durability**: 2025 papers cherry-pick post-2019; ETF era may break cointegrations.
4. **Triangular arb**: blogs claim 1.7-3%/loop; peer-reviewed 2024 SD paper = non-exploitable for retail.

---

## Recommended Action Set for $135 capital

1. **Paper-trade BTC-ETH pair** (Engle-Granger, Z>2 entry, |Z|<0.5 exit) for 4 weeks. If Sharpe > 1.5 in paper, deploy with $80.
2. **Reserve $50** for Kraken funding carry on whichever perp shows >0.03%/8h funding for ≥3 consecutive periods. Hedge with spot.
3. **Defensive filter**: monitor BTC funding > 15% APR sustained → pause Martin grids.
4. **Skip**: cross-exchange, triangular, DeFi yield at this size.

---

## Sources

- [Funding Rate Arbitrage in 2026 — ArbitrageGhost](https://arbitrageghost.medium.com/funding-rate-arbitrage-in-2026-the-complete-guide-with-real-calculations-40e6cf341e52)
- [Cash and Carry in Crypto — Buildix](https://www.buildix.trade/blog/cash-and-carry-crypto-delta-neutral-funding-rate-strategy-2026)
- [BIS WP 1087 Crypto Carry](https://www.bis.org/publ/work1087.pdf)
- [Exploring Risk and Return Profiles of Funding Rate Arbitrage on CEX and DEX — ScienceDirect 2025](https://www.sciencedirect.com/science/article/pii/S2096720925000818)
- [Perpetual Contract Funding Rate Arbitrage Strategy — Gate 2025](https://www.gate.com/learn/articles/perpetual-contract-funding-rate-arbitrage/2166)
- [Spot ETFs Give Rise to Crypto Basis Trading — CME](https://www.cmegroup.com/openmarkets/equity-index/2025/Spot-ETFs-Give-Rise-to-Crypto-Basis-Trading.html)
- [Funding Rates: How They Impact Perpetual Swap Positions — Amberdata](https://blog.amberdata.io/funding-rates-how-they-impact-perpetual-swap-positions)
- [Do Arbitrage Opportunities Still Exist Between Crypto Exchanges in 2025? — Digital One Agency](https://digitaloneagency.com.au/do-arbitrage-opportunities-still-exist-between-crypto-exchanges-in-2025/)
- [HFT in Crypto: Latency, Infrastructure, Reality — Adrian Keller / Medium](https://medium.com/@laostjen/high-frequency-trading-in-crypto-latency-infrastructure-and-reality-594e994132fd)
- [How Funding Rates Predict Crypto's Most Violent Reversals — Yellow.com](https://yellow.com/learn/how-to-read-funding-rates-crypto-reversals)
- [BitMEX 2025 Q3 Derivatives Report](https://www.bitmex.com/blog/2025q3-derivatives-report)
- [Wish or Reality? Triangular Arbitrage in Crypto — ScienceDirect 2024](https://www.sciencedirect.com/science/article/pii/S154461232401537X)
- [Statistical Arbitrage Strategies Using Cointegration — IJSRA 2026-0283](https://ijsra.net/sites/default/files/fulltext_pdf/IJSRA-2026-0283.pdf)
- [Cointegration-based pairs trading — Springer JAM 2025](https://link.springer.com/article/10.1057/s41260-025-00416-0)
- [Copula-based trading of cointegrated cryptocurrency pairs — IDEAS RePEc 2025](https://ideas.repec.org/a/spr/fininn/v11y2025i1d10.1186_s40854-024-00702-7.html)
- [Pairs Trading Statistical Arbitrage on Digital Assets — Moses Dada CQF / Medium](https://medium.com/digital-alpha-research/using-a-pairs-trading-statistical-arbitrage-approach-on-digital-assets-e29b10c6c651)
- [Bitcoin Futures Microstructure: Liquidation Cascades — XT Exchange / Medium](https://medium.com/@XT_com/bitcoin-futures-market-microstructure-liquidation-cascades-funding-regimes-and-open-interest-978b107b4889)
- [Anatomy of Oct 10-11 2025 Crypto Liquidation Cascade — Zeeshan Ali SSRN](https://papers.ssrn.com/sol3/Delivery.cfm/5611392.pdf?abstractid=5611392&mirid=1)
- [How $3.21B Vanished in 60 Seconds — Amberdata](https://blog.amberdata.io/how-3.21b-vanished-in-60-seconds-october-2025-crypto-crash-explained-through-7-charts)
- [How crypto derivatives liquidation drove Bitcoin's 2025 crash — CryptoSlate](https://cryptoslate.com/how-150-billion-was-liquidated-from-crypto-market-in-2025-driving-bitcoin-crash/)
- [State of DeFi 2025 — DL News](https://www.dlnews.com/research/internal/state-of-defi-2025/)
- [Best DeFi Yield Farming Strategies in 2026 — DailyCoin](https://dailycoin.com/best-defi-yield-farming-strategies-2026/)
- [Kraken Linear Multi-Collateral Derivatives Specs](https://support.kraken.com/articles/4844359082772-linear-multi-collateral-derivatives-contract-specifications)
- [Small Capital Crypto Arbitrage 2025 — CoinCryptoRank](https://coincryptorank.com/blog/starter-guide-arbitrage-small-capital)
