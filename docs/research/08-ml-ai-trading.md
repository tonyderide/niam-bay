# 08 — ML / AI / RL Trading for Crypto (2025-2026)

**Date**: 2026-04-30
**Author**: Niam-Bay research analyst
**Scope**: Honest assessment of ML/DL/RL applied to retail crypto trading, with a $135 account in mind.

---

## TL;DR

Most "ML beats buy-and-hold" papers are **lab artifacts**: zero fees, no slippage, walk-forward done wrong, regime-locked test sets. The headline "120x NAV" DQN paper exists but is outlier-class and not reproducible at retail scale. Real, after-fee retail edges from ML in 2025-2026 are **thin to non-existent** for accounts under ~$1k. The only ML branches with mild empirical support are (a) **regime detection** feeding a rule-based executor, and (b) **sentiment scoring** as a *filter* on existing signals. For a $135 account, **a well-tuned grid + simple trend filter beats any ML pipeline you can realistically run**, because (i) fees + slippage eat 60-80% of any 1%/day theoretical edge, (ii) you cannot afford the data + compute to retrain weekly, and (iii) ML pipelines amplify drawdowns when regime breaks. Recommendation: **don't run ML as a price predictor**. Use it sparingly as a *regime classifier* (HMM/GMM, not deep nets) feeding the existing grid logic.

---

## 1. LSTM / Transformer for price prediction

**Academic reality** (mdpi, IEEE, arxiv 2024-2026): Transformers slightly edge LSTM on directional accuracy (typically 55-62% on hourly BTC). Hybrid LSTM+XGBoost outperforms either alone. One Temporal Fusion Transformer paper claimed +4% over 2 weeks beating buy-and-hold by 6%, but **explicitly used 0 fees**. With realistic 0.1% taker fees, that edge collapses to roughly break-even.

**Live performance**: A 2025 Springer paper reports LSTM cumulative returns of ~65% in <1 year vs LightGBM/EMA/MACD/B&H — **but** the test window straddled a strong BTC bull (Jan-Oct 2025, +90% B&H), so the LSTM *under-performed* B&H in absolute terms; the "win" is risk-adjusted only.

**Verdict**: LSTM/Transformer for price prediction = **mostly hype** for retail. Directional accuracy 55-58% is real, but after fees + slippage + bid-ask, expectancy is ~0.

URLs:
- https://arxiv.org/html/2506.22055v1 (LSTM+XGBoost hybrid)
- https://www.mdpi.com/2227-7390/13/12/1908 (CNN-LSTM autoencoder)
- https://link.springer.com/article/10.1007/s44163-025-00519-y (comparative ML models)

## 2. Reinforcement Learning (PPO / DQN / SAC)

**Headline results 2025-2026**:
- A DQN framework (Taylor & Francis 2025) on BTC 2022-mid-2025 reported **120x NAV growth**. Read carefully: this is in-sample-leaky and uses idealized fills. Not reproducible in dry-run.
- A multi-agent RL system (NeuralArb Nov 2025) returned **+4.7% during the -11% Nov 2025 crash**.
- PPO is the 2025 favorite (most papers, most stable). One paper claims PPO cuts execution cost 36.93% via limit-order policies.
- SAC marketed for HFT / market making.

**FinRL-Contest 2025 (the actual benchmark)**: median submission Sharpe ~0.5-1.0 on out-of-sample crypto, **far below** what papers advertise. Top contestants overfit, bottom half lose money.

**Reality check**: 167-paper meta-analysis (arxiv 2512.10913) finds RL trading suffers from publication bias — only winners get published. Most live deployments fail within 60 days due to regime drift. Stable Baselines3 + a gym env trains in hours but **cannot survive a regime change without retraining**.

**Verdict**: RL is academically interesting, **not retail-ready**. Compute + retraining cadence kills it for $135 accounts.

URLs:
- https://www.tandfonline.com/doi/full/10.1080/23322039.2025.2594873 (DQN BTC)
- https://www.neuralarb.com/2025/11/20/reinforcement-learning-in-dynamic-crypto-markets/
- https://arxiv.org/html/2512.10913v1 (RL meta-analysis)

## 3. FinRL framework status

**State 2026**: 12k stars, actively maintained. Split into FinRL (research), FinRL-X / FinRL-Trading (production-ish), FinRL_Crypto (Binance via CCXT). FinRL-AlphaSeek is the 2025 crypto contest variant.

**What works**: training pipelines, environment abstractions, paper reproduction, contest infrastructure.

**What doesn't**: production deployment. Authors themselves acknowledge FinRL "historically focused on strategy training rather than live execution. Bridging to a real exchange requires substantial additional work — real-time ingestion, fees, slippage, latency are not modeled rigorously". The community fork `berendgort/FinRL_Crypto` exists *specifically* to fight overfitting in the original.

**Verdict**: research toolkit, not a trading product.

URLs:
- https://github.com/AI4Finance-Foundation/FinRL
- https://github.com/AI4Finance-Foundation/FinRL_Crypto
- https://open-finance-lab.github.io/FinRL_Contest_2025/

## 4. Sentiment analysis (Twitter/X, Reddit, news)

**LLM-based scoring** (BERT/RoBERTa/GPT fine-tunes) outperforms VADER/lexicon by 10-15% on classification accuracy. Concrete findings (mdpi 2025, RIT thesis 2025):
- Including sentiment + volume features improves directional accuracy to ~63%.
- Negative sentiment → immediate volatility spike (10-30 min lag).
- Positive sentiment → delayed but persistent effect (hours-days).
- Reddit leads Twitter as a *high-volatility* indicator.

**Edge measurable?** Yes, but **small and decaying**. A 2025 paper warns: "a sentiment strategy that worked in 2017 may fail by 2025" — the alpha is being arb'd out, plus the echo-chamber problem (everyone reads the same Lunarcrush/Santiment dashboards).

**Practical**: sentiment as a **filter**, not a signal. e.g., "don't open longs when 24h sentiment z-score < -2". Cheap to implement (Lunarcrush API ~$30/mo, or scrape Reddit free).

URLs:
- https://www.mdpi.com/2306-5729/10/4/50
- https://www.mdpi.com/2227-9091/11/9/159
- https://www.mdpi.com/2504-2289/8/6/63

## 5. On-chain metrics

**MVRV, NUPL, SOPR, exchange flows, whale flows**: all available free/cheap (Glassnode free tier, CryptoQuant, Santiment).

**Predictive power 2025**: Asymmetric. On-chain is good at calling **macro tops/bottoms** (MVRV-Z > 7 = top, < -1 = bottom; NUPL > 0.75 = euphoria) but **noisy at intraday scale**. Exchange inflows correlate with sell pressure 6-24h out — useful for *position sizing* not entry timing.

**Notable 2025 fact**: MVRV peaked at only 2.524 vs 3.5+ in 2017/2021 — 2025 cycle structurally different, suggesting on-chain thresholds are not stationary. Backtests (Amberdata): NUPL+SOPR + stop-loss combo beats B&H in volatile windows but underperforms in calm bull.

**Verdict**: useful as **macro regime input**, not a trading signal. Worth integrating cheaply.

URLs:
- https://blog.amberdata.io/onchain-valuation-what-bitcoins-realized-price-says-about-2026
- https://www.ainvest.com/news/bitcoin-chain-signals-decoding-institutional-buying-market-sentiment-2025-2509/

## 6. Hybrid ML + rule-based (the only pattern that works)

**Best-practice consensus (2025-2026)**: ML for **regime detection**, rules for **execution**. Specifically:
- HMM or GMM on BTC returns → 3-state classifier (bull/bear/range).
- Rule engine reads regime → switches strategy (grid in range, trend-follow in bull, flat/short in bear).
- Retrain regime model monthly, not daily.

This is **proven less fragile** than end-to-end ML. Papers (Springer 2026, arxiv 2511.00665) consistently show hybrid suffers smaller drawdowns during regime breaks.

**For Niam-Bay/Martin specifically**: this aligns with existing grid architecture. A simple regime filter (e.g., 200-day MA slope + ATR% + volume z-score → 3-state HMM) feeding the existing AutoGridScheduler is the highest-ROI ML add-on.

URLs:
- https://link.springer.com/article/10.1007/s10614-026-11338-3 (regime-aware framework)
- https://arxiv.org/html/2511.00665v1 (TA + ML, Bitcoin)

## 7. Feature engineering — what ML actually finds useful

XGBoost SHAP rankings (2025 papers): **Lag-1 return ~44%, Lag-2 ~34%, Lag-3 ~22%** (memory beyond 3 bars = noise). RSI(14), MACD, Bollinger %B marginal but consistent. Volume z-score / OBV useful for regime. Cyclical sin/cos hour/day = small free intraday edge. Cross-asset (ETH/BTC, DXY) helps daily, useless intraday. Stochastic, Williams %R, ADX = redundant.

URL: https://www.mdpi.com/2674-1032/4/4/77

## 8. Top open-source ML trading repos 2025-2026

| Repo | Stars | ML stack | Honest take |
|------|-------|----------|-------------|
| `freqtrade/freqtrade` + FreqAI | 25k+ | LightGBM, XGBoost, PyTorch (Catboost dropped 2025.12) | Best ML integration. RL module exists. Backtests OK, live results variable. |
| `jesse-ai/jesse` | 5k+ | Custom ML pipeline | Best **honest backtester** — zero look-ahead bias, JesseGPT helper. |
| `hummingbot/hummingbot` | 6k+ | Mostly market-making, light ML | $34B volume across 140 venues, but ML is not the core. |
| `AI4Finance-Foundation/FinRL` | 12k+ | DRL (PPO/SAC/A2C) | Research; not production. |
| `asavinov/intelligent-trading-bot` | 1k+ | Sklearn / XGBoost | Educational; small community. |
| `berendgort/FinRL_Crypto` | small | Anti-overfitting DRL | Niche but conceptually honest. |

**Real perf data**: almost none of these repos publish audited live track records. FreqAI strategies on r/Freqtrade show **wide variance** — some users +20% YTD, many -30%, no statistical evidence of edge over good rule-based.

URLs:
- https://github.com/freqtrade/freqtrade
- https://github.com/jesse-ai/jesse
- https://github.com/hummingbot/hummingbot

## 9. Common pitfalls (the graveyard)

1. **Data leakage**: normalizing whole dataset before split → future info bleeds in. Frequent and devastating.
2. **Look-ahead bias**: indicator uses current-bar close to decide current bar.
3. **Overfit hyperparams**: papers report "best of 50 runs" tuned on test set.
4. **Survivor bias on coins**: top-30 today excludes dead alts → inflates 2-5x.
5. **Regime lock**: train on 2021-23 bear, test on 2024-25 bull = flatters trend-followers.
6. **Fee/slippage absent**: 0.1% × 4 trades/day = ~15% annual headwind. Most papers ignore.
7. **Retraining cadence**: too rare = stale, too frequent = chasing noise.

URL: https://www.blockchain-council.org/cryptocurrency/backtesting-ai-crypto-trading-strategies-avoiding-overfitting-lookahead-bias-data-leakage/

## 10. Honest answer for a $135 retail account

**Don't run ML as a price predictor.** Reasons:
- Fees on Kraken (0.16-0.26% taker) eat any 55-58% directional edge. Math: edge × 2 × fee = 0.06 × 2 × 0.002 = 0.024% per trade expectancy, dwarfed by 0.4% round-trip cost.
- $135 cannot meaningfully diversify; ML benefits from cross-asset features it can't trade.
- Compute & data: weekly retraining + Glassnode/Lunarcrush APIs cost more than the account makes.
- Drawdown amplification: ML errors cluster (regime change), and a 30% DD on $135 = $40 — psychologically destructive.

**What to actually do** (ranked by ROI for the existing Martin grid):
1. **Regime filter (cheap ML)**: HMM/GMM on weekly BTC returns → enable/disable grids. ~1 day of work, real edge.
2. **Sentiment kill-switch**: if Lunarcrush galaxy score crashes >20% in 24h → pause new grid orders. Free-ish.
3. **On-chain macro overlay**: pause longs when MVRV-Z > 5; size up when < 0. Glassnode free tier sufficient.
4. **Skip everything else** (LSTM, RL, FinRL, FreqAI). Not worth the complexity at this account size.

**Brutal summary**: ML in 2025-2026 retail crypto is **80% hype, 15% useful as a filter, 5% genuine alpha** — and that 5% is captured by funds with co-located servers and PhD teams, not a $135 Kraken account. Stick to good rules, use ML only to *gate* those rules.

---

## Sources (key URLs)

- LSTM/Transformer: https://arxiv.org/html/2506.22055v1 ; https://www.mdpi.com/2227-7390/13/12/1908 ; https://link.springer.com/article/10.1007/s44163-025-00519-y
- RL: https://www.tandfonline.com/doi/full/10.1080/23322039.2025.2594873 ; https://arxiv.org/html/2512.10913v1 ; https://finrl-contest.readthedocs.io/en/latest/finrl2025/task2.html
- FinRL: https://github.com/AI4Finance-Foundation/FinRL ; https://github.com/AI4Finance-Foundation/FinRL_Crypto
- Sentiment: https://www.mdpi.com/2306-5729/10/4/50 ; https://www.mdpi.com/2504-2289/8/6/63
- On-chain: https://blog.amberdata.io/onchain-valuation-what-bitcoins-realized-price-says-about-2026 ; https://www.ainvest.com/news/bitcoin-chain-signals-decoding-institutional-buying-market-sentiment-2025-2509/
- Hybrid/regime: https://link.springer.com/article/10.1007/s10614-026-11338-3 ; https://arxiv.org/html/2511.00665v1
- Features: https://www.mdpi.com/2674-1032/4/4/77
- Repos: https://github.com/freqtrade/freqtrade ; https://github.com/jesse-ai/jesse ; https://github.com/hummingbot/hummingbot
- Pitfalls: https://www.blockchain-council.org/cryptocurrency/backtesting-ai-crypto-trading-strategies-avoiding-overfitting-lookahead-bias-data-leakage/
- Retail honesty: https://coincub.com/are-crypto-trading-bots-worth-it-2025/ ; https://medium.com/@kayakero_10555/crypto-futures-grid-trading-for-small-accounts-a-beginners-edge-e5c0fb87d4ea
