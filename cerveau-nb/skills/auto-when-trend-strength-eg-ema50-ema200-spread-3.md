---
activations: 0
created: '2026-05-12'
last_used: null
name: auto-when-trend-strength-eg-ema50-ema200-spread-3
session_origin: null
source: suboptimal
status: draft
type: auto-skill
---

When trend strength (e.g., EMA50-EMA200 spread > 3% from close) > threshold AND auto-unstuck has fired lvl2+, pause the grid (no new buy entries) until trend weakens. Let auto-unstuck and SL do their job without DCA fighting them.

**Contexte :** Grid neutral with DCA in strong-trend-down: each level fill increases position, auto-unstuck trim 25% partially, then next buy level fills lower, position grows again. Net: position keeps growing during downtrend until hard stop fires at maxLoss capital.
**Cause :** Auto-unstuck handles individual price drops but doesn't pause the grid. DCA keeps adding while trim removes — net effect is position re-grows during baisse. Hard stop is the only real firewall.
**Noeuds liés :** martin, grid-trading, auto-unstuck, trend-pause, DCA-pattern
