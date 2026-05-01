# 09 — Open Source Crypto Trading Bots: Comparative Review (2025-2026)

**Date**: 2026-04-30
**Author**: Niam-Bay research analyst
**Scope**: Comparative review of 10+ bots/strategies/platforms with real performance data, links, and disagreements between sources.

---

## TL;DR

- **Freqtrade** dominates the open-source space (~25k stars, Python, futures support on Binance + Bybit since 2023, FreqAI ML pipeline with reinforcement learning). It is the de-facto research platform.
- **NostalgiaForInfinity (NFIX)** is the single most-watched community strategy — actively maintained (last blacklist push Feb 24 2026, GH Actions backtests Nov 2025 → Jan 2026). Multi-signal mean reversion on 5m timeframe. Disagreement between sources: official backtests show modest positive returns ($100 → $102.57 sample) while YouTube/community videos paint mixed-to-negative real-money results.
- **Hummingbot** owns market-making/liquidity-mining. New V2 Controller framework (since 2023) is the Lego-block model Tony's grid bot conceptually resembles. Whitepaper claims 10–50% APY for liquidity mining; real-world Discord users report far lower after fees.
- **SaaS warning**: 3Commas leaked 150k API keys in 2022; Pionex hit a US multi-state consent order in 2025 + AMF blacklist in France. Open source remains the safer path for serious capital.
- **Gekko / Zenbot** = effectively dead (no major updates in years). **Gunbot** alive but closed-source/paid ($59 lifetime).
- **Top 3 to fork/learn from for Tony** (see section 11):
  1. `iterativv/NostalgiaForInfinity` — community-validated mean reversion logic
  2. `hummingbot/hummingbot` V2 Controllers — modular grid/PMM architecture
  3. `Netanelshoshan/freqAI-LSTM` — concrete ML scoring template inside Freqtrade

---

## 1. Freqtrade — the reference platform

- https://github.com/freqtrade/freqtrade — ~25k stars, Python, MIT.
- 30+ exchanges via CCXT. Futures via `trading_mode: futures` on Binance (stop-limit + stop-market) and Bybit (isolated only).
- **FreqAI**: classifiers, regressors, and reinforcement learning with Tensorboard. Caveat from docs: "the reward function provided… is a benchmark and **not for live production**."
- Telegram + WebUI built-in; Discord webhooks supported.

**Verdict**: the platform to benchmark Niam-Bay against. Martin (Java/Kraken-only) lacks the ML and multi-exchange surface.

---

## 2. Hummingbot — market making & liquidity

- https://github.com/hummingbot/hummingbot — ~6k stars, v2.13 (March 2026).
- **Strategy V2** (since 2023): "Lego-like" Controllers loaded by `v2_with_controllers.py`. Multiple controllers per process, each with its own pair/logic.
- Notable controllers: **PMM Simple V2**, **Grid Strike** (executors per level with TP/SL, can trail trend), **Perpetual Market Making**.
- Liquidity Mining: whitepaper claims **10–50% APY** (simulation). Real Discord reports: rewards collapse when bots crowd a campaign — actual PMM net-of-fees is a fraction of headline.

**Inspiration for Niam-Bay**: V2 Controllers map 1:1 onto how `AutoGridScheduler` should be refactored — multiple isolated controllers, not one monolith.

---

## 3. Jesse — backtesting purist

- https://github.com/jesse-ai/jesse — ~6.6k stars.
- Zero look-ahead-bias backtests, 300+ indicators, **JesseGPT** assistant, ML pipeline, scales to 1000s of routes/machine.
- Live trading limited to Binance, Bybit, Bitget.

**Use-case for Tony**: rigorously backtest a Niam-Bay hypothesis here before porting to Java.

---

## 4. OctoBot — beginner-friendly hybrid

- https://github.com/Drakkar-Software/OctoBot — ~5.4k stars, v2.1.1 (March 2026).
- Strategies: Grid, DCA, Crypto Baskets, **AI connectors (OpenAI/Ollama)**, TradingView, classic TA. 2025-2026 additions: **Hyperliquid DEX**, Polymarket (beta), AI-agent trading, mobile app.
- Revenue from exchange partnerships, no sub on OSS tier (cloud $9.99+/mo).

---

## 5. Gekko / Zenbot / Gunbot — dead, dying, paid

- **Gekko**: still downloadable, no meaningful development. Effectively abandoned.
- **Zenbot**: rebranded as Bot18/Zalgobot, no major updates "in months" per multiple sources. JavaScript, fading.
- **Gunbot**: alive but **closed-source**, $59 lifetime Standard, higher tiers for futures + backtest. https://www.gunbot.com/
- Source: https://captainaltcoin.com/best-bitcoin-trading-bots/ + https://slashdot.org/software/p/Gekko-Crypto/alternatives

**Skip all three** for new projects.

---

## 6. SaaS bots: 3Commas vs Pionex

| | 3Commas | Pionex |
|---|---|---|
| Cost | Pro $49/mo, Grid Bot $99/mo | $0 sub, 0.05% trading fee, 10% profit fee on arbitrage bot |
| Bots | DCA, Grid, Signal, Smart Trade terminal | 16 free bots (Grid, DCA, Arbitrage, Dual Investment) |
| Trust issue | **2022 leak: 150k API keys exposed** | **2025 US multi-state consent order**; AMF (France) blacklist; PH/MY warnings |
| Exchange support | 20+ via API | Pionex-native only |

Sources: https://3commas.io/blog/pionex-review + https://captainaltcoin.com/pionex-vs-3commas/ + https://www.daytrading.com/pionex

**Verdict**: both are legit operating businesses, but neither is appropriate for capital where API-key-leak or geofencing matters. Pionex is fine for $500 grid experiments, not for serious infrastructure.

---

## 7. Custom Python bots — top open-source repos

- **FinRL** — https://github.com/AI4Finance-Foundation/FinRL — 12k stars. Deep reinforcement-learning library for trading, actively maintained 2025. Heavyweight but academically rigorous.
- **awesome-crypto-trading-bots** — https://github.com/botcrypto-io/awesome-crypto-trading-bots — curated index, refreshed 2025.
- **awesome-freqtrade** — https://github.com/just-nilux/awesome-freqtrade — strategies, snippets, FreqAI resources.
- **stratestic** — https://github.com/diogomatoschaves/stratestic — Python lib for testing/optimizing strategies with proper risk-adjusted metrics.

---

## 8. Famous Freqtrade strategies — actual 2025-2026 status

| Strategy | Repo | Status | Notes |
|---|---|---|---|
| **NostalgiaForInfinityX (NFIX)** | https://github.com/iterativv/NostalgiaForInfinity | **Active**, weekly commits | 5m timeframe, 6–12 trades, USDT pairs, 40–80 pair list. Sample official backtest: $100 → $102.57. Dynamic funding fees in 2025.12. |
| **CryptoFrog** | https://github.com/froggleston/cryptofrog-strategies | Slower cadence | Smooth HA + bbw_expansion + MFI logic. One published backtest: $100 → $97.85 (slightly negative). https://www.freqst.com/ has more recent runs. |
| **Mabel** | community variant of CryptoFrog | Sparse | Limited 2025 published data. Treat as legacy. |
| **freqtrade-strategies (official)** | https://github.com/freqtrade/freqtrade-strategies | Active | Sample/educational, not optimized for live use. |
| **freqAI-LSTM** | https://github.com/Netanelshoshan/freqAI-LSTM | Active | Dynamic weighting + LSTM scoring inside FreqAI. |

**Disagreement**: `freqst.com` and `strat.ninja` rank strategies differently depending on pair list and time window — same strategy can show +30% on one ranking and -5% on another. Sources warn: "impressive backtest results … should not be assumed as achievable or realistic."

---

## 9. Performance metrics — what to trust, what to ignore

| Metric | Trust signal | Gaming risk |
|---|---|---|
| **Sharpe** | BTC 2020-2025 baseline ~0.95 | Inflated in low-vol windows; "Sharpe > 3 in backtest" = red flag |
| **Sortino** | BTC baseline 1.93; XBTO Trend 3.83 | Same window-selection gaming as Sharpe |
| **Calmar** | BTC baseline 0.84 | Sensitive to single max-DD event; cherry-pick start date |
| **Profit Factor** | 1.5–2.0 good, 2.0–3.0 excellent | **>3.0 almost always overfitted** |
| **Win rate** | Useful only with avg-win/avg-loss ratio | High win rate hides massive losers (martingale, no SL) |
| **Max DD** | Hard to fake | Often computed on closed trades only — hides unrealized DD |
| **K-Ratio** | Detects overfitting before live | Underused, ask for it |

**Rule of thumb from systematic studies**: live Sharpe is typically **30–50% lower** than backtest Sharpe. Source: https://highstrike.com/what-is-a-good-sharpe-ratio/ + https://algostrategyanalyzer.com/en/blog/advanced-trading-metrics/

Common gaming patterns to flag:
1. Start backtest in March 2020 (post-COVID bottom)
2. Hyperopt on the same window used for reporting (in-sample = out-of-sample)
3. No fees / no slippage / no funding
4. Closed-trade-only DD (ignores open underwater positions)
5. Pair-list cherry-picking (delisted shitcoins removed retroactively)

---

## 10. Community signals

- **Freqtrade Discord** — `#strategy-collection`; NFIX has its own server. Best live signal.
- **Hummingbot Discord** — V2 Controller walkthroughs, MM campaign coordination.
- **Jesse Discord** — strategy code reviews, JesseGPT prompts.
- **r/algotrading** — best threads on overfitting.
- **GitHub Issues** — best signal for "still maintained?"

---

## 11. Top 3 recommendations for Tony (fork or learn from)

### 1. iterativv/NostalgiaForInfinity
- Link: https://github.com/iterativv/NostalgiaForInfinity
- **Why**: 200+ tagged buy/sell signals composed from MFI, EMA, RSI, BB. Real-time community validation (active blacklist updates → someone is running it with capital). For Niam-Bay's grid Martin, the **signal-tagging architecture** is a goldmine: each entry/exit reasoned and labeled, which is exactly the explainability layer Tony's Cockpit currently lacks.
- **Action**: read `populate_entry_trend` and the dynamic blacklist machinery; port the tag-and-reason pattern into Martin's grid orders.

### 2. hummingbot/hummingbot — V2 Controllers
- Link: https://github.com/hummingbot/hummingbot + https://hummingbot.org/strategies/v2-strategies/controllers/
- **Why**: Tony's `AutoGridScheduler` is a single-strategy monolith. Hummingbot V2 Controllers solve exactly that problem — multiple isolated strategies sharing one process, with executors managing per-level TP/SL. The **Grid Strike** controller is the closest open-source analog to Martin and has a cleaner ABI.
- **Action**: study `v2_with_controllers.py` and one Grid Strike config; this is the architectural target for Niam-Bay's next refactor.

### 3. Netanelshoshan/freqAI-LSTM
- Link: https://github.com/Netanelshoshan/freqAI-LSTM
- **Why**: concrete, runnable example of dynamic weighting + LSTM scoring inside Freqtrade — the "ML signal layer above grid" pattern Tony has been circling. Smaller and more readable than FinRL.
- **Action**: backtest as-is on BTC/ETH perp data; use it as a reference for adding a regime classifier on top of Martin's grid (e.g. "tighten spacing in chop, widen in trend").

---

## Sources

- Freqtrade: https://github.com/freqtrade/freqtrade — https://www.freqtrade.io/en/stable/leverage/ — https://docs.freqtrade.io/en/2025.10/freqai-reinforcement-learning/
- NFIX: https://github.com/iterativv/NostalgiaForInfinity — https://alexbobes.com/crypto/automated-crypto-trading-with-freqtrade-and-nostalgiaforinfinity/
- CryptoFrog: https://github.com/froggleston/cryptofrog-strategies — https://www.freqst.com/ — https://strat.ninja/
- Hummingbot: https://github.com/hummingbot/hummingbot — https://hummingbot.org/strategies/v2-strategies/controllers/ — https://hummingbot.org/strategies/v1-strategies/liquidity-mining/ — https://hummingbot.org/blog/demystifying-liquidity-mining-rewards/
- Jesse: https://github.com/jesse-ai/jesse — https://jesse.trade/ — https://gainium.io/review/jesse
- OctoBot: https://github.com/Drakkar-Software/OctoBot — https://www.gncrypto.news/trading-bots/octobot-review/
- SaaS: https://3commas.io/blog/pionex-review — https://captainaltcoin.com/pionex-vs-3commas/ — https://www.daytrading.com/pionex
- Legacy bots: https://captainaltcoin.com/best-bitcoin-trading-bots/
- ML/RL: https://github.com/Netanelshoshan/freqAI-LSTM — https://github.com/AI4Finance-Foundation/FinRL
- Awesome lists: https://github.com/just-nilux/awesome-freqtrade — https://github.com/botcrypto-io/awesome-crypto-trading-bots — https://github.com/diogomatoschaves/stratestic
- Metrics: https://highstrike.com/what-is-a-good-sharpe-ratio/ — https://algostrategyanalyzer.com/en/blog/advanced-trading-metrics/ — https://www.xbto.com/resources/sharpe-sortino-and-calmar-a-practical-guide-to-risk-adjusted-return-metrics-for-crypto-investors
