# 06 — Risk Management & Position Sizing for Crypto Bots (2025-2026)

**Date**: 2026-04-30
**Capital cible**: $135 sur Kraken Futures, leverage 5-10x, perte récente -18.7%, objectif 1€/jour
**Sources**: 12 articles, recherche académique 2025-2026

---

## TL;DR (small-account reality)

Sur $135 avec 5-10x leverage, la math de Kelly/Optimal-f sort des chiffres ridicules ($1-3 par trade). La règle qui sauve un compte de cette taille n'est pas l'optimisation du sizing — c'est **le circuit breaker brutal**. Conclusion convergente des 12 sources :

1. **Risk per trade : 1% strict** = $1.35 max par trade. Pas 2%, pas Half-Kelly, juste 1%. Tout le reste est mort statistique sur ce nominal.
2. **Stop loss : 2x ATR(14)** sur 1h ou 4h selon timeframe. Multiplier 1.5x si scalp, 3x si swing. Crypto exige plus large que tradfi (3-7% daily ATR sur BTC en 2026).
3. **Circuit breaker à 3 pertes consécutives OU -3% daily** = arrêt 24h forcé. Non négociable. La perte -18.7% = exactement ce que ce mécanisme aurait stoppé à -3%.
4. **Drawdown trigger à -10%** = halve le sizing. À -15% = stop total + audit.
5. **Pas de Kelly à 25%** sur ce nominal : transaction costs Kraken (0.05% maker / 0.05% taker futures) bouffent l'edge théorique.
6. **Tail hedge non viable < $500** : les puts BTC OTM coûtent $5-15 minimum, soit 4-11% du compte. Hedge passif = stables 20-30% du capital.

**Action** : viser 0.5%-1% risk/trade ($0.70-$1.35), 3 trades/jour max, halt à -3% daily. Objectif 1€/jour = +0.7%/jour = parfaitement faisable mais demande 60%+ winrate avec R:R 1.2+.

---

## 1. Kelly Criterion — Half/Quarter/Dynamic

**Formule**: `f* = (b·p − q) / b` où b=R:R, p=winrate, q=1-p.

**Ce que les praticiens utilisent en 2025** :
- **Quarter-Kelly (25%)** dominant en crypto retail — captures ~50% growth, drawdown réduit ~75% ([altrady](https://www.altrady.com/blog/risk-management/kelly-criterion-crypto-position-sizing))
- **Half-Kelly** : capture ~75% du growth optimal, réduit volatilité de 25% ([lbank](https://www.lbank.com/explore/mastering-the-kelly-criterion-for-smarter-crypto-risk-management))
- **Plafond dur** : jamais > 20% par position, peu importe ce que Kelly dit
- **Pré-requis data** : 50 trades min, 100+ recommandé

**Exemple chiffré** (winrate 55%, R:R 1.5) :
| Approche | Risk/trade | Worst DD |
|---|---|---|
| Fixed 2% | 2% | ~12% |
| Half-Kelly | 12.5% | ~38% |
| Full Kelly | 25% | ~61% |

**Disagreement** : Medium ([tmapendembe](https://medium.com/@tmapendembe_28659/kelly-criterion-for-crypto-traders-a-modern-approach-to-volatile-markets-a0cda654caa9)) recommande Half-Kelly comme "modern crypto standard". CoinMarketCap academy ([coinmarketcap](https://coinmarketcap.com/academy/article/what-is-the-kelly-bet-size-criterion-and-how-to-use-it-in-crypto-trading)) pousse Quarter-Kelly. Les trois s'accordent : **jamais Full Kelly en crypto** — un seul tweet = 20% swing, la formule ignore les transaction costs.

**Sur $135** : Quarter-Kelly à 6% = $8.10 risk. Avec 5x leverage et 2% stop, position = $405 nominal. Réaliste mais agressif.

---

## 2. Optimal f (Vince) & Secure f

Formule cherche le f qui maximise TWR (Terminal Wealth Relative) via historical worst loss.

**Problème majeur** ([quantpedia](https://quantpedia.com/beware-of-excessive-leverage-introduction-to-kelly-and-optimal-f/), [quantifiedstrategies](https://www.quantifiedstrategies.com/optimal-f-money-management/)) : drawdowns ingérables, similaires à Full Kelly. Vince lui-même a créé **Secure f** = optimal f sous contrainte de max drawdown acceptable.

**Verdict** : académiquement intéressant, **pas adapté retail crypto small account**. Demande 100+ trades historiques sur même stratégie pour calibrer. Préférer Kelly fractionné.

---

## 3. Position Sizing par ATR — règle 1% / 2%

**Formule standard** :
```
Position Size = (Capital × Risk%) / (ATR × Multiplier)
```

**Exemple BTC** ([alphaexcapital](https://www.alphaexcapital.com/prop-trading/risk-money-management-and-psychology-in-prop-trading/prop-risk-management-framework/atr-based-stop-loss-and-sizing)) :
- Compte $10k, risk 1% ($100), ATR(14) = $2000, multiplier 2x
- → Position = $100 / $4000 = 0.025 BTC ($1250 nominal)

**Règle 1% vs 2%** ([traderssecondbrain](https://traderssecondbrain.com/guides/risk-per-trade-guide)) :
- **1% = défaut universel** : 69 pertes consécutives nécessaires pour perdre 50% du compte
- **2% seulement si winrate >55% prouvé sur 100+ trades** avec R:R ≥ 2

**Crypto specifics 2026** : BTC ATR daily 3-7%, soit massif vs equities. Exige multiplier 2-3x ATR (vs 1.5-2x equities).

**Sur $135** : risk 1% = $1.35. ATR 1h BTC ~ $300. Stop 2x ATR = $600. Position = $1.35/$600 = 0.00225 BTC = $135 nominal. Avec 5x leverage = $675 position effective. **Sweet spot small account**.

---

## 4. Risk Parity / Equal Risk Contribution

Chaque pair contribue le même montant de risque au portfolio total ([quantinsti](https://blog.quantinsti.com/risk-parity-portfolio/), [mathquant](https://blog.mathquant.com/2026/04/24/risk-parity-driven-dynamic-allocation-for-rwa-multi-assets-in-crypto-markets.html)).

**Formule simplifiée** : weight_i = (1/vol_i) / Σ(1/vol_j)

**Crypto applicabilité** ([arxiv 2412.02654](https://arxiv.org/html/2412.02654v1)) : recherche 2024-2025 confirme que risk parity simple fonctionne sur baskets crypto malgré fat tails. Hierarchical Equal Risk Contribution (HERC) = version avancée pour grosses watchlists.

**Sur $135 multi-pair** : non-sensé. 1-2 pairs max (BTC, ETH). Risk parity nécessite 5+ assets pour bénéfice diversification.

---

## 5. Drawdown Control & Auto-reduction

**Règle de base** ([nadcab](https://www.nadcab.com/blog/trading-bot-risk-management-stop-loss-position-sizing-drawdown-control)) : recovery non-linéaire — perdre 20% = besoin de +25% pour récupérer ; perdre 50% = +100%.

**Triggers production 2025-2026** :
- **-5% from peak** : warning, log, pas d'action
- **-10% from peak** : halve sizing (passe de 1% à 0.5%)
- **-15% from peak** : stop trading + audit obligatoire
- **-20%+** : kill switch absolu

**Anti-martingale natif** : risk fixe en % grow le sizing en hausse, le réduit en baisse automatiquement. **Jamais de martingale** (doubler après perte) en crypto retail.

**Cas Tony** : -18.7% session = trigger -15% violé. Stop + audit auraient prévenu les pertes 15→18.7%.

---

## 6. VaR / CVaR — Crypto Fat Tails

**Parametric VaR sous-estime crypto** ([frontiersin](https://www.frontiersin.org/journals/applied-mathematics-and-statistics/articles/10.3389/fams.2025.1567626/full), [mdpi](https://www.mdpi.com/2227-7072/14/3/53)) — return distributions leptokurtic + negative skew (gauche plus heavy).

**Buffer recommandé** : +30-50% sur VaR paramétrique pour crypto. Préférer **CVaR (Expected Shortfall)** = perte moyenne au-delà du VaR threshold.

**Modèles 2025 state-of-art** :
- **SVCJ** (Stochastic Volatility with Correlated Jumps) capture jumps + heavy tails
- **Threshold-switching ES-CAViaR** Bayesian, joint VaR/ES forecast
- Self-exciting jump clustering confirmé en crypto (les jumps appellent d'autres jumps)

**Pratique small account** : VaR/CVaR overkill pour $135. Approximation simple = max daily loss historique × 1.5 = ton VaR 99% empirique.

---

## 7. Stop Loss Optimization — Backtest Comparison

**Quatre approches** ([chartswatcher](https://chartswatcher.com/pages/blog/7-advanced-stop-loss-strategies-that-actually-work-in-2025), [SSRN 5821842](https://papers.ssrn.com/sol3/Delivery.cfm/5821842.pdf?abstractid=5821842&mirid=1)) :

| Type | Standard crypto | Pros | Cons |
|---|---|---|---|
| Fixed % | 2-3% | Simple | Ignore volatilité |
| ATR | 2x ATR(14) | S'adapte volatilité | Lag sur regime change |
| Structural | Sous support clé | Logique market | Subjectif |
| Volatility (Bollinger/Chandelier) | 3 ATR trailing | Excellent en trend | Faux signaux range |

**Recherche 2025** ([SSRN](https://papers.ssrn.com/sol3/Delivery.cfm/5821842.pdf)) : combiner **ATR trailing stop + EMA slope reversal + dynamic vol filter** réduit max DD significativement vs fixed stop.

**Recommandation crypto retail** : ATR(14) × 2x **plus** flush si support cassé. Hybrid > pure technique.

---

## 8. Daily / Weekly Loss Limits — Style Prop Firm

**Standards prop crypto 2025-2026** ([velotrade](https://velotrade.com/blog/crypto-prop-firm-rules-explained), [funderpro](https://funderpro.com/blog/master-prop-firm-drawdown-rules-in-2025/)) :

- **Daily loss limit** : 4-5% (CFT = 5%)
- **Max overall drawdown** : 8-10%
- **Trailing drawdown** : suit le high water mark
- **Static drawdown** : depuis balance début journée
- Apex 3.0 (late 2025) : pas de daily limit mais overall strict

**Pour retail crypto bot small account** :
- Daily : **-3% max** ($4.05 sur $135) → halt 24h
- Weekly : **-7% max** → halt 7j + audit complet
- Monthly : **-12% max** → kill switch, redéploiement only après revue stratégie

Plus strict que prop firm car pas de funding behind.

---

## 9. Circuit Breakers Production

**Triggers consensus** ([cripton.ai](https://cripton.ai/en/guides/bot-risk-management), [3commas](https://3commas.io/blog/ai-trading-bot-risk-management-guide-2025)) :

| Mécanisme | Threshold typique | Action |
|---|---|---|
| Consecutive losses | 3-4 stops successifs | Pause 24h |
| Daily loss | -3% à -7% | Halt session |
| Drawdown peak-to-trough | -10% à -15% | Reduce sizing 50% |
| Trades/day cap | 10 max | Skip nouveaux signaux |
| API errors | 5+ en 5min | Pause + alert |
| Slippage anomaly | >2x average | Skip + alert |
| Regime change | Vol spike >2σ ou correlation flip | Switch params ou halt |

**Mai 2025 flash crash** : AI bots ont vendu $2B en 3 minutes, amplifiant le crash — d'où importance circuit breakers dégradés (pas tous-ou-rien).

**Regime detection** ([cripton.ai](https://cripton.ai/en/guides/bot-risk-management)) : monitor vol regime, si trending→high-vol = stops tighter + exits faster.

---

## 10. Black Swan Tail Hedging

**Allocation standard** ([zvv](https://zvv.com/posts/tail-risk-hedging-strategies), [optionsjive](https://optionsjive.com/blog/the-black-swan-hedge-protect-your-portfolio-from-market-crashes/)) : **0.5-2% du capital** en hedge tail.

**Instruments retail crypto** :
- **Deribit puts BTC OTM** (30-50% OTM, 6-12mo) — coût $5-50/contrat
- **Inverse ETF / inverse perp short** : 5-10% du capital en short BTC perp pendant crashes
- **Stables 20-30%** : passive hedge, le plus simple

**Crypto crash 11 Oct 2025** ([medium gwrx2005](https://medium.com/@gwrx2005/the-october-11-2025-crypto-black-swan-crash-an-academic-analysis-db92a3d2ad66)) : académiquement classé black swan crypto. Confirme jump clustering — les crashes appellent d'autres crashes.

**Sur $135** : tail hedge options non viable (cost minimum > 5% capital). Solution :
- **30% en USDC** = hedge passif
- **Hard stop -10% portfolio** = circuit breaker remplace l'hedge
- **No leverage > 5x** = élimine risque liquidation flash

---

## Recommandations spécifiques Tony / Niam-Bay

1. **Risk per trade : 1%** strict ($1.35) — pas négociable
2. **Leverage max : 5x** sur Kraken Futures — 10x = mort certaine sur ATR daily 5%+
3. **Stop loss : 2x ATR(14)** sur 1h, hard SL toujours présent
4. **Daily loss : -3%** ($4.05) → halt 24h auto via Martin
5. **Consecutive losses : 3** → pause 24h
6. **Drawdown : -10% → halve sizing, -15% → stop total**
7. **Allocation : 70% trading / 30% USDC dormant** (tail hedge passif)
8. **Pairs : BTC + ETH max** — pas de altcoins low-cap sur ce nominal
9. **R:R minimum 1.2:1** — viser 1.5:1 pour compenser fees Kraken
10. **Objectif 1€/j** = +0.7%/jour = winrate 60%+ avec R:R 1.5 = atteignable mais zéro marge d'erreur

**Le -18.7% récent confirme** : sans circuit breaker daily à -3%, Martin a continué à perdre. Implémentation prioritaire.

---

## Sources

- [Altrady — Kelly Criterion Crypto](https://www.altrady.com/blog/risk-management/kelly-criterion-crypto-position-sizing)
- [LBank — Mastering Kelly Criterion](https://www.lbank.com/explore/mastering-the-kelly-criterion-for-smarter-crypto-risk-management)
- [CoinMarketCap — Kelly Bet Size](https://coinmarketcap.com/academy/article/what-is-the-kelly-bet-size-criterion-and-how-to-use-it-in-crypto-trading)
- [Medium — Kelly for Crypto Modern](https://medium.com/@tmapendembe_28659/kelly-criterion-for-crypto-traders-a-modern-approach-to-volatile-markets-a0cda654caa9)
- [Quantpedia — Kelly & Optimal F](https://quantpedia.com/beware-of-excessive-leverage-introduction-to-kelly-and-optimal-f/)
- [QuantifiedStrategies — Optimal F](https://www.quantifiedstrategies.com/optimal-f-money-management/)
- [AlphaEx Capital — ATR Sizing](https://www.alphaexcapital.com/prop-trading/risk-money-management-and-psychology-in-prop-trading/prop-risk-management-framework/atr-based-stop-loss-and-sizing)
- [TradersSecondBrain — 1% vs 2% Rule](https://traderssecondbrain.com/guides/risk-per-trade-guide)
- [Frontiers — VaR Long Memory Crypto 2025](https://www.frontiersin.org/journals/applied-mathematics-and-statistics/articles/10.3389/fams.2025.1567626/full)
- [MDPI — CVaR Portfolio Crypto](https://www.mdpi.com/2227-7072/14/3/53)
- [SSRN — Vol-Adaptive Trend Crypto](https://papers.ssrn.com/sol3/Delivery.cfm/5821842.pdf?abstractid=5821842&mirid=1)
- [Cripton AI — Bot Risk 2026](https://cripton.ai/en/guides/bot-risk-management)
- [3Commas — AI Bot Risk Guide 2025](https://3commas.io/blog/ai-trading-bot-risk-management-guide-2025)
- [Nadcab — Bot Stop-Loss & DD Control](https://www.nadcab.com/blog/trading-bot-risk-management-stop-loss-position-sizing-drawdown-control)
- [Velotrade — Crypto Prop Firm Rules](https://velotrade.com/blog/crypto-prop-firm-rules-explained)
- [FunderPro — Drawdown Rules 2025](https://funderpro.com/blog/master-prop-firm-drawdown-rules-in-2025/)
- [ZVV — Tail Risk Hedging 2025](https://zvv.com/posts/tail-risk-hedging-strategies)
- [Medium — Oct 11 2025 Crypto Crash Analysis](https://medium.com/@gwrx2005/the-october-11-2025-crypto-black-swan-crash-an-academic-analysis-db92a3d2ad66)
- [LuxAlgo — ATR Stop Strategies](https://www.luxalgo.com/blog/5-atr-stop-loss-strategies-for-risk-control/)
- [MathQuant — Risk Parity Crypto 2026](https://blog.mathquant.com/2026/04/24/risk-parity-driven-dynamic-allocation-for-rwa-multi-assets-in-crypto-markets.html)
