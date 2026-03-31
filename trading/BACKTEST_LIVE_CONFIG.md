# Backtest Results — Martin Grid Strategy

**Config:** conservative
**Period:** 90 days of 1h candles (Kraken)
**Date:** 2026-04-01 01:46

## Fee Structure
- Maker fee: 0.02% per fill (both sides)
- Taker fee: 0.05% orphan closes on recenter
- Funding rate: 0.010% per 8h on open notional
- ADX filter: skip fills when ADX(14) > 25

## Per-Pair Results

| Pair | Capital | Lev | Spacing | Lvls | RTs | Gross | Fees | Orphan | Funding | Net | ROI% | MaxDD% | Sharpe | PF | Active% |
|------|---------|-----|---------|------|-----|-------|------|--------|---------|-----|------|--------|--------|----|---------| 
| DOT | $22 | x3 | 1.00% | 8 | 23 | $4.34 | $0.21 | $0.34 | $1.64 | $2.14 | 9.7% | 108.9% | 0.35 | 1.13 | 44% |

## Portfolio Summary

| Metric | Value |
|--------|-------|
| Total Capital | $22 |
| Total Round Trips | 23 |
| Gross Profit | $4.34 |
| Total Fees (maker) | $0.21 |
| Orphan Costs (taker) | $0.34 |
| Funding Paid | $1.64 |
| **Net Profit** | **$2.14** |
| **Portfolio ROI** | **9.7%** |
| Max Drawdown (worst pair) | 108.9% |
| Monthly Avg Net | $0.71 |

## Monthly Breakdown

| Month | DOT | Total |
|-------|------|-------|
| 2026-01 | $-23.32 | $-23.32 |
| 2026-02 | $30.35 | $30.35 |
| 2026-03 | $-2.68 | $-2.68 |

## Per-Pair Details

### DOT
- Candles processed: 540
- Round trips: 23
- Recenters: 8
- ADX-blocked candles: 303 (56%)
- Unrealized at end: $0.00
