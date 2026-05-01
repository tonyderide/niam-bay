# 07 - Backtesting Frameworks for Crypto Bot Strategies (2025-2026)

**Author:** Research analyst (Claude)
**Date:** 2026-04-30
**Context:** Niam-Bay / Martin Grid bot — Java backend, Kraken Futures perpetuals, $135 capital, 90+ days backtest target.

---

## TL;DR

For Tony's setup (Java backend + tiny capital + Kraken Futures perps), the **single best framework is `backtesting.py`** for the first iteration, with **`vectorbt` (free)** as the upgrade path once parameter sweeps become the bottleneck. Reasons: (1) Java is a dead end for backtesting libs — no maintained crypto framework exists in Java; pretending otherwise wastes weeks. (2) `backtesting.py` runs in 30 lines, eats Kraken CSV directly, models maker/taker fees natively, and is easy to call from Java via a `ProcessBuilder` shim or a tiny FastAPI sidecar. (3) `vectorbt` (open-source, not PRO) handles 1000+ parameter combos in seconds when you outgrow it. **Avoid Freqtrade and Jesse** — they are bot-execution engines that *include* backtesting; using them means rewriting the Martin grid logic in their DSL, which defeats the purpose of the Java backend. **Avoid NautilusTrader** unless you migrate to Rust/Python end-to-end ($135 capital does not justify it).

Mandatory data realism additions for any framework:
- **Slippage:** 0.05 % liquid majors / 0.2-0.5 % alts (taker), Kraken-Futures specific.
- **Fees:** 0.02 % maker / 0.05 % taker baseline; 0 % maker promo currently active on Kraken Pro Futures.
- **Funding:** every 4 h on Kraken Futures (NOT 8 h like Binance/Bybit) — pull from `/derivatives/api/v4/historicalfundingrates`.
- **OHLCV is enough** for a grid bot at 1 m / 5 m. Order-book reconstruction is overkill until you scale past $10 k.

---

## 1. Best backtesting frameworks 2025-2026

| Framework | Lang | Speed | Crypto perps | Funding rate | Live bridge | Verdict for Tony |
|---|---|---|---|---|---|---|
| **backtesting.py** | Py | medium | manual | manual | none | **WINNER for v1** — minimal, eats CSV, called from Java easily |
| **vectorbt (OSS)** | Py + Numba | very fast (M trades/s) | manual | manual | none | **Upgrade path** — for parameter sweeps |
| vectorbt PRO | Py | fastest | yes | yes | yes | $400/yr — skip until profitable |
| Backtrader | Py | slow (event loop) | partial | manual | yes | Mature but unmaintained since 2023; skip |
| Zipline-reloaded | Py | slow | poor (equities-first) | no | no | Equity-centric, skip |
| **NautilusTrader** | Rust core / Py | very fast | yes (native) | yes | yes | Best institutional choice; overkill at $135 |
| Freqtrade | Py | medium | yes (futures mode) | yes | yes | **Bot itself, not a lib** — replaces Martin, not augments it |
| Jesse | Py | medium | yes | yes | paid | Crypto-native UX; same trap as Freqtrade |
| Lean / QuantConnect | C# / Py | fast | yes | yes | yes | Cloud-locked; hard to backtest local Java strategy |
| HftBacktest | Py + Rust | tick-level | yes | partial | no | For HFT/MM only; not for grids |

Sources: autotradelab, python.financial, awesome-systematic-trading, NautilusTrader, Freqtrade docs.

**Disagreement flag:** the "industry-standard" framing of vectorbt PRO on EliteTrader is marketing. Multiple 2026 reviews (qmr.ai, Greyhound Analytics) put NautilusTrader as the technical leader and `backtesting.py`/vectorbt-OSS as best price/perf for retail. For a $135 bot, retail tooling is the right answer.

---

## 2. Walk-forward analysis

- **Standard split:** 70 % in-sample / 30 % out-of-sample per window, OR 60/40 if data is short.
- **Anchored** = IS start fixed at t0, IS grows each step. Use when regime stability matters and you don't want recent data to dominate.
- **Rolling** = IS window of fixed length slides forward. Use for crypto — regimes change every 30-90 days, fixed-length windows stay responsive.
- **Recommended for Tony's 90-day backtest:**
  - Rolling, IS = 21 days, OOS = 9 days, step = 9 days → ~8 OOS windows.
  - Aggregate OOS Sharpe / drawdown / hit-rate. If OOS performance is < 50 % of IS, the grid is overfit.
- Source: QuantInsti, MultiCharts, Unger Academy, Build Alpha, arXiv 2512.12924 (2025 microstructure WF paper).

---

## 3. Survivorship & look-ahead bias

- **Survivorship in crypto is brutal:** 14 000 / 24 000 listed tokens are dead (>58 %). Studies show inflation of backtest returns by **200-400 %** when you ignore delisted symbols. (CoinAPI, StratBase)
- **Mitigation for Tony:** Martin trades a fixed Kraken Futures whitelist (PI_XBTUSD, PI_ETHUSD, etc.) — survivorship risk is low *but not zero*. Kraken has delisted PI_LTCUSD / PI_XRPUSD perp variants. Keep the historical symbol list.
- **Look-ahead bias** is the bigger risk. Common leaks:
  - Indicators computed with `.shift(-1)` or full-series normalization.
  - Using bar `t` close to decide and *also* fill at bar `t` close (impossible IRL).
  - Using daily highs/lows to time intra-day entries.
- **Rule:** signal at close of bar `t` → execute at open of bar `t+1`, or at `t` close + 1 tick with slippage. backtesting.py and vectorbt both default to next-bar fill if you use `next_open`.

Source: CoinAPI, blockchain-council, LuxAlgo, Bitsgap.

---

## 4. Slippage modeling on Kraken Futures perps

Industry consensus (LuxAlgo, DolphinDB, BacktestMe, Bitget Academy):

| Asset class | Taker slippage | Maker slippage |
|---|---|---|
| BTC/ETH perps | 0.02-0.05 % | ~0 (rebate territory) |
| Top-10 alts | 0.05-0.15 % | ~0.02 % |
| Mid/low-cap alts | 0.2-0.5 % | 0.05-0.2 % |

For Kraken Futures perps specifically: spread on PI_XBTUSD typically 0.5-1 bp, on PI_ETHUSD 1-2 bp. Conservative model: **flat 5 bp taker + 0 maker** for majors. For small-cap perps, scale linearly with 30-day mean spread.

**Advanced (when you go past $1 k):** model slippage as `f(order_size / top_5_levels_depth)`. Kraken's full depth feed is free via WebSocket v2 (`book` channel). Source: Kraken Blog "API Unlocked 3".

---

## 5. Funding rate modeling

- **Kraken Futures funding interval = 4 hours** (different from Binance/Bybit's 8 h). Source: blog.kraken.com/product/quick-primer-on-funding-rates.
- Endpoint: `GET /derivatives/api/v4/historicalfundingrates?symbol=PI_XBTUSD` — free, no auth.
- For backtest accounting at every 4 h boundary: `pnl_funding -= position_notional * funding_rate`.
- **Watch out:** funding can flip sign mid-trade. A grid bot that holds a long during 6-8 funding intervals on a strong uptrend can pay 0.3-0.6 % cumulative — eats most of the grid edge.
- Academic refs: arXiv 2506.08573 (2026 design paper), ScienceDirect S2096720925000818.

---

## 6. Maker/taker fee accuracy on Kraken Futures

Current schedule (2026-04, source: support.kraken.com/articles/360048917612):
- **Standard tier:** 0.02 % maker / 0.05 % taker.
- **Promo (active):** **0 % maker** on Kraken Pro Futures across all tiers.
- Volume tiers reduce taker to 0.01 %; rebates kick in only for institutional ($100 M+ 30-day).

**Backtest implication:** Martin is a grid bot — almost 100 % maker fills. With the 0 % promo, fee drag is ~0. Without promo, 0.02 % per fill × 2 (entry+exit) = 0.04 % round-trip. A 0.6 % grid spacing therefore loses 6.7 % of gross to fees.

In `backtesting.py`: `Backtest(..., commission=0.0002, exclusive_orders=True)`. In vectorbt: `Portfolio.from_signals(..., fees=0.0002, slippage=0.0005)`.

---

## 7. Order book reconstruction vs OHLCV

| Approach | Use when | Cost | Tony's bot? |
|---|---|---|---|
| OHLCV 1-5 m | grid, swing, trend | low (Kraken CSV free) | **Yes** |
| OHLCV + trade tape | scalping, mean-reversion | medium | only if scalp module added |
| Full L2 reconstruction | market-making, HFT, large size | high (TB of data) | No — overkill for $135 |

For a grid bot with 0.6 % spacing and seconds-to-hours holding time, **OHLCV 1 m is sufficient**. The fill assumption "limit order at level X gets hit if low <= X (long) or high >= X (short)" is accurate to within ~3-5 bp. HftBacktest is the right tool only if you build a true market-maker. (Sources: Mathworks, QuantConnect forum, hftbacktest.readthedocs.io, Mudrex Medium series.)

---

## 8. Monte Carlo / bootstrapping

2026 industry consensus: **1000 runs minimum**, ideally 5000 (StrategyQuant, BacktestBase, NinjaTrader).

Three useful methods for Tony:
1. **Trade-order shuffle:** randomize order of N trades, recompute equity curve → distribution of max drawdown.
2. **Bootstrap with replacement:** sample N trades from the trade list with replacement → confidence interval on Sharpe / CAGR.
3. **Regime-blocked bootstrap:** sample blocks of K consecutive trades to preserve serial correlation. Best for grid bots since trades cluster.

**Decision rule:** if 95th-percentile MC drawdown > 2× backtest drawdown, the strategy is fragile. Source: PickMyTrade, QuantProof, BacktestBase.

Reported field result: strategies passing 1000-run MC show **30-50 % lower live failure rate** (BuildAlpha 2026 study).

---

## 9. Overfitting prevention

Checklist (compiled from LuxAlgo, ArrowAlgo, Quantlane, MDPI GT-Score paper, PredictNow):

1. **OOS reserve:** keep last 30 % of data untouched until final eval.
2. **Walk-forward:** see §2.
3. **Parameter sensitivity:** sweep each param ±20 %; if Sharpe drops > 50 % the strategy is overfit.
4. **Complexity penalty:** prefer 2-3 parameters max. GT-Score (MDPI 2026, 19/1/60) explicitly penalizes parameter count.
5. **Regularization for ML models:** L1/L2 if you ever add an ML signal layer.
6. **Reject "too good" results:** Sharpe > 3 on a $135 retail grid is almost certainly a bug or look-ahead.

---

## 10. Free historical data for Kraken Futures

| Source | What you get | Cost | URL |
|---|---|---|---|
| **Kraken official CSV dump** | OHLCVT 1/5/15/30/60/240/720/1440 m, full history per market | **Free** | support.kraken.com/articles/360047124832 |
| Kraken historical trade dump | tick trades (T&S) | Free | support.kraken.com/articles/360047543791 |
| Kraken Futures REST | OHLC + funding + trade history, paginated | Free, public | docs.kraken.com/api/docs/futures-api/trading/historical-data |
| Historical funding rates | per-symbol, all-time | Free, public | docs.kraken.com/api/docs/futures-api/trading/historical-funding-rates |
| CryptoDataDownload | Kraken spot CSV | Free | cryptodatadownload.com/data/kraken |
| Freqtrade `download-data` | Wrapper over Kraken Futures REST, saves to JSON/parquet | Free | freqtrade.io/en/stable/data-download |
| CoinAPI Metrics | funding + OI + perps, multi-exchange | Free dev tier (limited) | coinapi.io |
| Amberdata bulk parquet | full L2 + perps | Paid | amberdata.io/kraken-market-data |

**Caveat:** Kraken's *spot* CSV dump covers spot pairs (XBTUSD), not futures (PI_XBTUSD). For futures OHLC and funding: use the Futures REST endpoint via Freqtrade's `download-data` (handles pagination + retries) or write a small Python loop. The endpoint returns all history available since contract launch (BTC perps go back to 2020).

---

## Concrete recommendation for Niam-Bay

**Step 1 (this week):** Write a 100-line Python script using `backtesting.py` that:
- Pulls Kraken Futures OHLC 1m + funding via `requests` (or Freqtrade's CLI).
- Replays the Martin grid logic (port the Java `GridStrategy` rules, not the whole engine).
- Models 5 bp slippage, 0.02 % fee, 4-h funding deductions.
- Runs walk-forward (rolling 21d/9d) over 90 days.

**Step 2 (when grid params need tuning):** Port the script to `vectorbt` (open-source). Same data, same fee model, but you can sweep 1000 (spacing × levels × leverage) combos in <60 s.

**Step 3 (only if profitable in live):** Consider NautilusTrader for a unified Python research-to-prod stack. Until then, keep Java backend + Python sidecar; talk via REST or `ProcessBuilder`.

**Do NOT** rewrite the bot in Freqtrade or Jesse. Their framework boundaries don't fit a custom grid scheduler with the AutoGridScheduler / Compounder logic Tony already has.

---

## Sources

- [Backtrader vs NautilusTrader vs VectorBT vs Zipline-reloaded (autotradelab)](https://autotradelab.com/blog/backtrader-vs-nautilusttrader-vs-vectorbt-vs-zipline-reloaded)
- [The Python Backtesting Landscape 2026](https://python.financial/)
- [NautilusTrader](https://nautilustrader.io/)
- [awesome-systematic-trading (GitHub)](https://github.com/wangzhe3224/awesome-systematic-trading)
- [Best Crypto Backtesting Platforms 2026 — StratBase](https://stratbase.ai/en/blog/best-crypto-backtesting-platforms)
- [Best Freqtrade Alternatives 2026 — alexbobes](https://alexbobes.com/crypto/best-freqtrade-alternatives/)
- [Backtesting.py docs](https://kernc.github.io/backtesting.py/)
- [VectorBT docs](https://vectorbt.dev/)
- [HftBacktest docs](https://hftbacktest.readthedocs.io/)
- [Walk-Forward Optimization — QuantInsti](https://blog.quantinsti.com/walk-forward-optimization-introduction/)
- [Walk Forward Optimization — QuantConnect](https://www.quantconnect.com/docs/v2/writing-algorithms/optimization/walk-forward-optimization)
- [Interpretable Hypothesis-Driven Trading — arXiv 2512.12924](https://arxiv.org/html/2512.12924v1)
- [How to Backtest Crypto Strategy 2026 — Coin Bureau](https://coinbureau.com/guides/how-to-backtest-your-crypto-trading-strategy)
- [Eliminate Survivorship Bias in Crypto Backtesting — CoinAPI](https://www.coinapi.io/blog/how-to-eliminate-survivorship-bias-in-crypto-backtesting)
- [Survivorship Bias Dead Coins — StratBase](https://stratbase.ai/en/blog/survivorship-bias-crypto)
- [Backtesting AI Crypto Strategies Safely — Blockchain Council](https://www.blockchain-council.org/cryptocurrency/backtesting-ai-crypto-trading-strategies-avoiding-overfitting-lookahead-bias-data-leakage/)
- [Crypto Backtesting Guide 2025 — Bitsgap](https://bitsgap.com/blog/crypto-backtesting-guide-2025-tools-tips-and-how-bitsgap-helps)
- [Backtesting Limitations Slippage and Liquidity — LuxAlgo](https://www.luxalgo.com/blog/backtesting-limitations-slippage-and-liquidity-explained/)
- [HFT Backtesting Best Practices — DolphinDB](https://medium.com/@DolphinDB_Inc/best-practices-for-strategy-backtesting-in-cryptocurrency-markets-with-dolphindb-b271be022fc3)
- [Backtest Crypto with Real Market Data — CoinAPI](https://www.coinapi.io/blog/backtest-crypto-strategies-with-real-market-data)
- [Kraken API Unlocked — Market Data Feeds](https://blog.kraken.com/product/api/unlocked-3-the-market-data-feeds-systematic-traders-use)
- [Kraken Perpetual Futures](https://www.kraken.com/features/futures/perpetual)
- [Designing Funding Rates for Perpetual Futures — arXiv 2506.08573](https://arxiv.org/html/2506.08573v1)
- [Funding Rate Arbitrage CEX/DEX — ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2096720925000818)
- [Quick Primer on Funding Rates — Kraken Blog](https://blog.kraken.com/product/quick-primer-on-funding-rates)
- [Kraken Futures Historical Funding Rates API](https://docs.kraken.com/api/docs/futures-api/trading/historical-funding-rates/)
- [Kraken Futures Historical Data API](https://docs.kraken.com/api/docs/futures-api/trading/historical-data/)
- [Fees for Derivatives — Kraken](https://support.kraken.com/articles/360048917612-fee-schedule)
- [0% Maker Fees on Futures — Kraken](https://support.kraken.com/articles/0-maker-fees-on-futures-trading-on-kraken-pro)
- [Kraken Fees Guide 2026 — Bitget Academy](https://www.bitget.com/academy/kraken-fees-guide)
- [Kraken Downloadable OHLCVT Data](https://support.kraken.com/articles/360047124832-downloadable-historical-ohlcvt-open-high-low-close-volume-trades-data)
- [Kraken Downloadable Time and Sales](https://support.kraken.com/articles/360047543791-downloadable-historical-market-data-time-and-sales-)
- [CryptoDataDownload Kraken](https://www.cryptodatadownload.com/data/kraken/)
- [Freqtrade Data Downloading](https://www.freqtrade.io/en/stable/data-download/)
- [Freqtrade Leverage / Futures](https://www.freqtrade.io/en/stable/leverage/)
- [HftBacktest PyPI](https://pypi.org/project/hftbacktest/)
- [QuantConnect Limit Order Book Backtesting](https://www.quantconnect.com/forum/discussion/826/how-to-backtest-with-historical-limit-order-book-data/)
- [The Problem with OHLC Data — Mohsen Hassan](https://medium.com/@MohsenHassan/the-problem-with-ohlc-data-a20ed7afa4e)
- [Backtest MasterClass Order Book — Mudrex](https://medium.com/mudrex/backtest-masterclass-part-5-b656735b531a)
- [5 Monte Carlo Methods — StrategyQuant](https://strategyquant.com/blog/new-robustness-tests-on-the-strategyquant-codebase-5-monte-carlo-methods-to-bulletproof-your-trading-strategies/)
- [Monte Carlo Trading Simulation — PickMyTrade](https://blog.pickmytrade.trade/monte-carlo-trading-simulation-strategy-robustness-testing/)
- [Monte Carlo Simulations Validation — QuantProof](https://quantproof.io/blog/monte-carlo-simulations-trading-strategy-validation)
- [Monte Carlo Stress Test — BacktestBase](https://www.backtestbase.com/education/monte-carlo-stress-testing)
- [What Is Overfitting — LuxAlgo](https://www.luxalgo.com/blog/what-is-overfitting-in-trading-strategies/)
- [Avoiding Overfitting — ArrowAlgo](https://arrowalgo.com/avoiding-overfitting-how-to-build-robust-trading-algorithms/)
- [Avoid Overfitting — Quantlane](https://quantlane.com/blog/avoid-overfitting-trading-strategies/)
- [GT-Score Robust Objective Function — MDPI](https://www.mdpi.com/1911-8074/19/1/60)
- [Optimizing Without Overfitting — PredictNow](https://predictnow-ai.medium.com/optimizing-trading-strategies-without-overfitting-365fbf1dc5fe)
- [Best Backtesting Library for Python — Mayer-Krebs](https://www.qmr.ai/best-backtesting-library-for-python/)
- [Vectorbt vs Backtrader — Greyhound Analytics](https://greyhoundanalytics.com/blog/vectorbt-vs-backtrader/)
- [VectorBT PRO Industry Standard — Elite Trader](https://www.elitetrader.com/et/threads/industry-standard-backtest-tool-is-vectorbt-pro.370565/)
- [From Backtest to Live with VectorBT 2025 — Tinnerholm](https://medium.com/@samuel.tinnerholm/from-backtest-to-live-going-live-with-vectorbt-in-2025-step-by-step-guide-681ff5e3376e)
