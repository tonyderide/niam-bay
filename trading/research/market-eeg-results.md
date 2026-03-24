# Market EEG — Backtest Results

**Date**: 2026-03-24 01:50
**Data**: 3 months hourly candles (Dec 2025 — Mar 2026)
**Capital**: $100, Leverage: 5x, Fees: 0.02% maker

## Concept

Apply FFT (Fast Fourier Transform) on rolling price windows to classify
the market into 4 states, analogous to brain EEG frequency bands:

| State | Volatility | Action |
|-------|-----------|--------|
| DELTA | < 0.15% | Sleep — don't trade |
| ALPHA | 0.15-0.55% | Grid trading (tight spacing) |
| BETA | 0.55-1.2% | Grid trading (wide spacing) |
| GAMMA | > 1.2% | Stop — protect capital |

## Results by Pair

### ETHUSD

- **Period**: 2025-12-21 to 2026-03-22
- **Price**: 2995.8800 -> 2045.4700 (-31.7%)

**EEG Distribution:**

| State | Hours | % |
|-------|-------|---|
| DELTA | 0 | 0.0% |
| ALPHA | 821 | 38.4% |
| BETA | 1205 | 56.4% |
| GAMMA | 110 | 5.1% |

**Performance:**

| Metric | Baseline | EEG Filter | EEG Adaptive |
|--------|----------|------------|--------------|
| Final Balance | $112.88 | $55.14 | $74.57 |
| Total Profit | $14.52 | $-43.46 | $-24.80 |
| ROI | 12.88% | -44.86% | -25.43% |
| Fees Paid | $3.2816 | $2.7988 | $1.2512 |
| Round Trips | 165 | 141 | 63 |
| Max Drawdown | 33.70% | 50.56% | 47.30% |
| Time in Market | 100.0% | 92.3% | 92.3% |
| Profit/Hour | $0.0066 | $-0.0215 | $-0.0122 |

### ADAUSD

- **Period**: 2025-12-21 to 2026-03-22
- **Price**: 0.3705 -> 0.2503 (-32.4%)

**EEG Distribution:**

| State | Hours | % |
|-------|-------|---|
| DELTA | 0 | 0.0% |
| ALPHA | 185 | 8.7% |
| BETA | 1845 | 86.4% |
| GAMMA | 106 | 5.0% |

**Performance:**

| Metric | Baseline | EEG Filter | EEG Adaptive |
|--------|----------|------------|--------------|
| Final Balance | $116.06 | $86.52 | $76.08 |
| Total Profit | $17.99 | $-11.82 | $-23.29 |
| ROI | 16.06% | -13.48% | -23.92% |
| Fees Paid | $3.8712 | $3.3274 | $1.2553 |
| Round Trips | 194 | 167 | 63 |
| Max Drawdown | 42.29% | 41.98% | 36.37% |
| Time in Market | 100.0% | 92.5% | 92.5% |
| Profit/Hour | $0.0082 | $-0.0058 | $-0.0115 |

### SOLUSD

- **Period**: 2025-12-21 to 2026-03-22
- **Price**: 125.7800 -> 85.8700 (-31.7%)

**EEG Distribution:**

| State | Hours | % |
|-------|-------|---|
| DELTA | 0 | 0.0% |
| ALPHA | 596 | 27.9% |
| BETA | 1465 | 68.6% |
| GAMMA | 75 | 3.5% |

**Performance:**

| Metric | Baseline | EEG Filter | EEG Adaptive |
|--------|----------|------------|--------------|
| Final Balance | $93.55 | $87.76 | $97.79 |
| Total Profit | $-4.83 | $-10.75 | $-1.57 |
| ROI | -6.45% | -12.24% | -2.21% |
| Fees Paid | $3.2444 | $2.9879 | $1.2966 |
| Round Trips | 163 | 150 | 65 |
| Max Drawdown | 46.00% | 53.95% | 43.91% |
| Time in Market | 100.0% | 93.9% | 93.9% |
| Profit/Hour | $-0.0022 | $-0.0052 | $-0.0008 |

## Key Question: Does EEG Filter Improve Profitability?

### ETHUSD

- EEG Filter ROI: **-44.86%** vs Baseline **12.88%** -> WORSE
- EEG Adaptive ROI: **-25.43%** vs Baseline **12.88%** -> WORSE
- EEG Filter Drawdown: **50.56%** vs Baseline **33.70%** -> RISKIER
- EEG Filter Profit/Hour: **$-0.0215** vs Baseline **$0.0066** -> LESS EFFICIENT
- Fees saved by EEG Filter: **$0.4828**

### ADAUSD

- EEG Filter ROI: **-13.48%** vs Baseline **16.06%** -> WORSE
- EEG Adaptive ROI: **-23.92%** vs Baseline **16.06%** -> WORSE
- EEG Filter Drawdown: **41.98%** vs Baseline **42.29%** -> SAFER
- EEG Filter Profit/Hour: **$-0.0058** vs Baseline **$0.0082** -> LESS EFFICIENT
- Fees saved by EEG Filter: **$0.5438**

### SOLUSD

- EEG Filter ROI: **-12.24%** vs Baseline **-6.45%** -> WORSE
- EEG Adaptive ROI: **-2.21%** vs Baseline **-6.45%** -> BETTER
- EEG Filter Drawdown: **53.95%** vs Baseline **46.00%** -> RISKIER
- EEG Filter Profit/Hour: **$-0.0052** vs Baseline **$-0.0022** -> LESS EFFICIENT
- Fees saved by EEG Filter: **$0.2564**

## Conclusion

### The honest answer: EEG filtering does NOT improve profitability in this dataset.

**What the data shows:**

1. **Baseline (always-on grid) wins on ETH and ADA.** The grid's constant market-making captures more round-trips and profits, even through the GAMMA chaos zones. ROI: +12.88% (ETH), +16.06% (ADA).

2. **EEG Filter (ALPHA+BETA only) loses across all three pairs.** Pausing during GAMMA sounds smart in theory, but the grid resets when it comes back online, losing continuity. The few hours saved (5-8% of time) don't compensate for missed oscillations and reset costs.

3. **EEG Adaptive is the only partial win** — on SOL it beats baseline (-2.21% vs -6.45%) by using wider spacing in BETA, which reduces overtrading. But it still loses on ETH and ADA.

4. **Zero DELTA hours detected.** In 3 months of crypto, the market never "slept" by our definition. The volatility floor on hourly crypto data is above 0.15%. The DELTA filter is useless for crypto.

5. **GAMMA avoidance hurts more than it helps.** The ~5% of time in GAMMA is actually when the grid captures the biggest swings. Closing positions at GAMMA onset locks in losses.

**Why this happens — the fundamental problem:**

The EEG concept assumes that GAMMA = danger. But for a *grid* strategy, high volatility = more fills = more profit. The grid THRIVES on oscillation, even violent oscillation. The real danger is a one-directional move (which is what happened: -32% trend). The EEG/FFT approach classifies volatility magnitude, not directionality.

**What would actually help:**

- A **trend filter** (e.g., moving average slope) to pause the grid in strong trends
- A **mean-reversion indicator** to confirm the market is oscillating, not trending
- Keep the FFT idea but use it to detect **periodicity** (is the market oscillating regularly?) rather than just volatility bands

### Deployment recommendation for Martin: DO NOT deploy EEG filter as-is.

The baseline grid is already the best performer on this data. The EEG concept is interesting but needs fundamental rework to detect trend vs oscillation rather than volatility bands.
