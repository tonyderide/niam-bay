# Cross-Pair Correlation Trading on Kraken

**Date**: 2026-03-22
**Status**: Research / Not yet implemented

---

## The Concept

Crypto assets are highly correlated -- when BTC moves, the market follows. But correlations are not perfect. Temporary divergences happen: ETH drops 5% while SOL only drops 1%, or XRP pumps while ADA stays flat. One of them is "wrong." Pair trading bets on the convergence back to the normal relationship.

This is a **market-neutral strategy** in theory: you don't care if the market goes up or down, you only care about the *relative* movement between two assets.

---

## 1. Correlation Matrix (Typical Values)

Based on recent data (late 2025 / early 2026), here are approximate 30-day rolling correlations:

|       | BTC  | ETH  | SOL  | XRP  | ADA  | LINK |
|-------|------|------|------|------|------|------|
| **BTC** | 1.00 | 0.92 | 0.93 | 0.80 | 0.88 | 0.85 |
| **ETH** |      | 1.00 | 0.93 | 0.78 | 0.95 | 0.90 |
| **SOL** |      |      | 1.00 | 0.75 | 0.88 | 0.83 |
| **XRP** |      |      |      | 1.00 | 0.82 | 0.72 |
| **ADA** |      |      |      |      | 1.00 | 0.85 |
| **LINK**|      |      |      |      |      | 1.00 |

**Key observations:**
- BTC-ETH, ETH-ADA, ETH-SOL, and BTC-SOL are the most correlated pairs (>0.90)
- XRP is the most "independent" -- lower correlation with everything, especially LINK (0.72)
- These correlations fluctuate. In high-volatility events, correlations spike to ~0.99 (everything dumps together). In calm markets, they can drop to 0.70-0.80.
- **Critical point**: Correlation at 0.99 (as BTC-SOL hit in late 2025) means almost no divergence opportunities. The strategy works best when correlations are high but not extreme (0.80-0.95 range).

**Best candidate pairs for pair trading:**
1. **ETH/SOL** -- High correlation (0.93), similar market cap tier, both smart contract platforms
2. **ETH/ADA** -- Very high correlation (0.95), but ADA is much smaller/more volatile
3. **BTC/ETH** -- The classic pair, most liquid, most studied

---

## 2. Pair Trading Setup

### The Ratio Method

Track the price ratio between two assets over time:

```
Ratio = Price_A / Price_B
Example: ETH/SOL ratio = ETH_price / SOL_price
```

If ETH = 3500 USD and SOL = 175 USD, the ratio is 20.0.

Calculate the **rolling mean** and **rolling standard deviation** of this ratio over N periods (typically 20-60 days for daily data, or 24-168 hours for hourly data).

### Entry and Exit Rules

| Signal | Condition | Action |
|--------|-----------|--------|
| **Long Entry** | Z-score < -2.0 | Buy the underperformer (A), Short the outperformer (B) |
| **Short Entry** | Z-score > +2.0 | Short A, Buy B |
| **Exit** | Z-score crosses 0 | Close both positions |
| **Stop Loss** | Z-score > 3.5 or < -3.5 | Close everything -- the relationship may be broken |

### Position Sizing

Both legs must be **dollar-neutral**: equal notional value on each side.

With 100 EUR capital:
- 50 EUR long on Asset A
- 50 EUR short on Asset B (requires margin/futures)

---

## 3. Z-Score Calculation

```
Z-score = (Current_Ratio - Mean_Ratio) / StdDev_Ratio
```

### Example with ETH/SOL

Suppose over the last 30 days:
- Mean ETH/SOL ratio = 20.0
- StdDev = 0.8
- Current ratio = 21.8

Z-score = (21.8 - 20.0) / 0.8 = **+2.25**

This means ETH is relatively overpriced vs SOL (or SOL is underpriced vs ETH). The trade: **short ETH, long SOL**.

### Important: Cointegration > Correlation

Correlation tells you two assets move in the same direction. **Cointegration** tells you their ratio is mean-reverting -- which is what you actually need for pair trading.

Two assets can be highly correlated but not cointegrated (they drift apart permanently). Always test for cointegration (Engle-Granger test or Johansen test) before trading a pair.

In crypto, cointegration relationships are **unstable**. They can hold for months and then break permanently (e.g., LUNA/ETH in 2022). Regular re-testing is mandatory.

---

## 4. Implementation on Kraken

### Option A: Futures on Both Sides (Recommended)

Use Kraken Futures perpetual contracts for both legs.

| Parameter | Detail |
|-----------|--------|
| **Long leg** | Open a long perpetual future |
| **Short leg** | Open a short perpetual future |
| **Leverage** | Up to 5x available (use 2-3x max for this strategy) |
| **Maker fee** | 0.02% per trade |
| **Taker fee** | 0.05% per trade |
| **Funding rate** | -0.01% to +0.01% every 8 hours (variable) |

**Advantages:**
- Easy to short
- Lower fees than spot
- Single account, single margin pool
- Can use multi-collateral (hold EUR or USDT as collateral)

**Disadvantages:**
- Funding rates eat into profits on long-held positions
- Liquidation risk with leverage
- Not all pairs available on Kraken Futures

### Option B: Long Spot + Short Futures

| Leg | Venue | Fee |
|-----|-------|-----|
| Long | Kraken Spot | 0.26% taker / 0.16% maker |
| Short | Kraken Futures | 0.05% taker / 0.02% maker |

**Disadvantages:**
- Spot fees are much higher (0.16-0.26% vs 0.02-0.05%)
- Capital split across two systems
- More complex to manage

**Verdict: Option A (futures-only) is clearly better for this strategy.**

### Fee Impact Per Round-Trip

A round-trip = 4 trades (open long + open short + close long + close short).

**Using limit orders (maker fees) on futures:**
- 4 x 0.02% = **0.08% total round-trip cost**

**Using market orders (taker fees) on futures:**
- 4 x 0.05% = **0.20% total round-trip cost**

**Plus funding rates:**
- Holding for 24h = 3 funding periods = potentially 0.03% per leg = 0.06% additional
- Holding for 3 days = ~0.18% additional

**Realistic total cost per trade (limit orders, 2-day hold):**
- Fees: 0.08%
- Funding: ~0.12%
- Slippage: ~0.05-0.10%
- **Total: ~0.25-0.30% per round-trip**

This means you need the ratio to move at least 0.30% in your favor just to break even.

---

## 5. Risks

### Risk 1: Permanent Decorrelation
One coin fundamentally changes (gets hacked, regulation, new competitor). The ratio never returns to mean. This is the #1 risk.

**Mitigation:** Strict stop-loss at z-score 3.5. Never trade pairs where one asset has existential risk (small-caps, meme coins).

### Risk 2: Not Actually Market-Neutral
If both assets are 0.90+ correlated to BTC and BTC drops 30%, both your long AND short lose money (the long drops more than the short gains, or vice versa). You are only neutral to the *relative* movement, not to the absolute level.

**Mitigation:** This strategy works best in sideways/low-volatility markets, not during crashes.

### Risk 3: Leverage and Liquidation
With 2-3x leverage and both legs moving against you (rare but possible), liquidation can wipe the account.

**Mitigation:** Keep leverage at 2x max. Maintain excess margin.

### Risk 4: Funding Rate Drag
If you're long on one side and funding rates are consistently negative (you pay), the carry cost can eat all your profits over days/weeks.

**Mitigation:** Monitor funding rates. Close positions faster. Target trades that resolve in 1-3 days.

### Risk 5: Low Liquidity on Alt Pairs
SOL, ADA, LINK futures may have wider spreads and thinner order books than BTC/ETH. Slippage can be significant.

**Mitigation:** Stick to BTC/ETH pair if capital is small. Most liquid, tightest spreads.

---

## 6. Realistic Expectations with 100 EUR

Let's be brutally honest.

### The Math

| Parameter | Value |
|-----------|-------|
| Capital | 100 EUR |
| Per-leg allocation | 50 EUR (or 100-150 EUR with 2-3x leverage) |
| Round-trip cost | ~0.25-0.30% = ~0.25-0.30 EUR per trade |
| Average profit per successful trade | ~0.5-1.5% of position = 0.50-1.50 EUR |
| Win rate (realistic) | 55-65% |
| Trades per month | 4-8 (z-score > 2 doesn't happen daily) |

### Monthly P&L Estimate (Optimistic but Honest)

```
8 trades/month x 60% win rate = 4.8 wins, 3.2 losses

Wins:  4.8 x 1.00 EUR avg profit  = +4.80 EUR
Losses: 3.2 x 0.70 EUR avg loss   = -2.24 EUR
Costs:  8 x 0.28 EUR              = -2.24 EUR
                                    --------
Net:                                +0.32 EUR/month
```

That's **0.32% monthly return**, or about **3.8% annualized**.

### With 2x Leverage

Doubles the position size, roughly doubles the P&L (and the risk):

```
Net: ~0.64 EUR/month = ~7.7% annualized
```

### The Uncomfortable Truth

**With 100 EUR, this strategy earns you less than 1 EUR per month.**

The strategy itself is sound -- hedge funds and prop desks run it with millions. But:

1. **Fees eat a disproportionate share** when positions are tiny
2. **The edge is small** (pair trading is a statistical edge, not a home run)
3. **Your time is worth more** -- monitoring ratios, managing 4 positions per trade, checking funding rates... for 0.64 EUR/month
4. **One bad trade** (stop-loss at z=3.5 on 2x leverage) can wipe 2-3 months of gains

### When Does This Make Sense?

| Capital | Monthly Return (est.) | Worth the effort? |
|---------|----------------------|-------------------|
| 100 EUR | 0.30-0.65 EUR | No. Educational only. |
| 1,000 EUR | 3-6.50 EUR | Barely. Good for learning. |
| 10,000 EUR | 30-65 EUR | Starting to be meaningful. |
| 50,000+ EUR | 150-325 EUR | Now we're talking. |

---

## 7. Verdict

### The Strategy: Solid in Theory

Pair trading is a legitimate, well-studied strategy. In crypto it works because:
- High correlations create mean-reverting ratios
- Volatility provides frequent entry signals
- 24/7 markets mean no overnight gaps

### The Reality for 100 EUR

**Don't do it manually.** The returns don't justify the time investment.

**If you want to learn the concept**, paper trade it for 2-3 months using a spreadsheet or free tools like TradingView ratio charts.

**If you want to actually run it**, you need:
1. Automation (bot to monitor z-scores and execute trades)
2. At least 5,000-10,000 EUR capital
3. A focus on BTC/ETH pair only (most liquid, lowest slippage)
4. Patience -- this is a grind, not a moonshot

### Better Use of 100 EUR

For learning and small capital, simpler strategies with fewer legs (fewer fees) are more practical:
- Single-direction momentum on one asset
- Grid trading on a single pair
- DCA into spot positions

Pair trading is a tool for when you have capital and infrastructure. At 100 EUR, the lesson is more valuable than the profit.

---

## Sources

- [Kraken Derivatives Fee Schedule](https://support.kraken.com/articles/360048917612-fee-schedule)
- [Kraken Fee Structures](https://www.kraken.com/features/fee-schedule)
- [Crypto Pairs Trading - WunderTrading](https://wundertrading.com/journal/en/learn/article/crypto-pairs-trading-strategy)
- [Trading the ETH/BTC Correlation - CME Group](https://www.cmegroup.com/articles/2023/trading-the-ether-bitcoin-correlation.html)
- [Cointegration vs Correlation - Amberdata](https://blog.amberdata.io/crypto-pairs-trading-why-cointegration-beats-correlation)
- [Crypto Correlations - DefiLlama](https://defillama.com/correlation)
- [Sharpe AI Correlation Matrix](https://sharpe.ai/correlation)
- [Crypto Correlations Hit Record Highs](https://cryptopotato.com/defillama-crypto-correlations-hit-record-highs-as-btc-sol-reaches-0-99/)
- [How to Short on Kraken](https://coinspot.io/en/trading/how-to-short-on-kraken/)
- [Kraken Margin Allowance Limits](https://support.kraken.com/articles/209238787-margin-allowance-limits)
