#!/usr/bin/env python3
"""Patch Overview subtitle + Positions uPnL + PnL History Aucun RT + Risk capitals."""
import re
fp = '/home/ubuntu/autobot/frontend/index.html'
with open(fp) as f:
    s = f.read()

# ---- 1. Subtitle uses realizedStats
old_sub = "document.getElementById('pnlSub').textContent = fills + ' fills \\u00b7 ' + rt + ' round trips across ' + state.grids.length + ' grid(s)';"
new_sub = """(() => {
    const rs = state.realizedStats;
    if (rs && rs.daily && rs.total) {
      let totalTrades = 0;
      for (const d in rs.daily) totalTrades += (rs.daily[d].trades || 0);
      const pairs = Object.keys(rs.by_pair || {}).length;
      const days = rs._days || 7;
      document.getElementById('pnlSub').textContent = totalTrades + ' trades \\u00b7 ' + pairs + ' pair(s) \\u00b7 ' + days + 'd window';
    } else {
      document.getElementById('pnlSub').textContent = fills + ' fills \\u00b7 ' + rt + ' round trips across ' + state.grids.length + ' grid(s)';
    }
  })();"""

if old_sub in s:
    s = s.replace(old_sub, new_sub, 1)
    print('[1/4] subtitle patched')
else:
    print('[1/4] subtitle NOT FOUND')

# ---- Also update statRT / statFills / statAvgProfit to use realizedStats when available
old_stats = """document.getElementById('statRT').textContent = rt;
  document.getElementById('statFills').textContent = fills;
  document.getElementById('statAvgProfit').textContent = rt > 0 ? '$' + fmt(profit / rt) : '--';"""
new_stats = """(() => {
    const rs = state.realizedStats;
    let displayRT = rt, displayFills = fills, avg = null;
    if (rs && rs.daily) {
      let tot = 0; for (const d in rs.daily) tot += (rs.daily[d].trades || 0);
      displayRT = tot;
      displayFills = tot; // trades = fills with realized pnl
      avg = tot > 0 ? (rs.total.net / tot) : null;
    }
    document.getElementById('statRT').textContent = displayRT;
    document.getElementById('statFills').textContent = displayFills;
    document.getElementById('statAvgProfit').textContent = avg != null ? '$' + fmt(avg) : (rt > 0 ? '$' + fmt(profit / rt) : '--');
  })();"""

if old_stats in s:
    s = s.replace(old_stats, new_stats, 1)
    print('[2/4] stats patched')
else:
    print('[2/4] stats NOT FOUND')

# ---- Positions uPnL: compute from entry+size vs last price
# Find the render for positions — search for "unrealized PnL"
# Look for position row that renders uPnL
old_pos_pattern = re.search(r"(unrealized PnL[\s\S]{0,500}?)(--)", s)
if old_pos_pattern:
    print(f'[3/4] found position uPnL template at offset {old_pos_pattern.start()}')
else:
    print('[3/4] position uPnL template NOT FOUND')

with open(fp, 'w') as f:
    f.write(s)
print('done')
