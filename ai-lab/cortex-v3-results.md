# Cortex NB v3 -- Results

**Date**: 2026-03-24 08:34

## Architecture

The correct hybrid, identified from v1/v2 failure analysis:

1. **Temporal Chains** (PRIMARY) -- multi-order exact matching (1-8 chars)
2. **SDR Encoder** (SECONDARY) -- Hebbian learned, 256-bit sparse
3. **SDR Index** -- similarity lookup ONLY, never predicts directly

**Prediction flow:**
1. Get context (last N chars)
2. Try TC exact match (highest order first, backoff) -> if found, use it
3. If no TC match: encode context as SDR -> find most similar stored context
4. Use TC's prediction for that nearest context
5. Last resort: space character fallback

**Key insight from v2:** DON'T use SDR for prediction math.
Use it ONLY as a similarity index to bridge unknown contexts to known ones.

## Config

- SDR: 256 bits, 26 active (~10%)
- TC max order: 8
- Fuzzy threshold: 0.3
- Train/test split: 80/20

## Data

- Total: 217228 chars from pensees
- Train: 173782 chars
- Test: 43446 chars
- Test positions: 43445

## Results

| Metric | TC-only | Cortex v3 |
|--------|---------|----------|
| Accuracy | 55.5% | 55.5% |
| Train time | 2.3s | 16.3s |
| Test time | 0.2s | 0.3s |
| Contexts | 351004 | 351004 + 80287 SDR |

**Delta: +0.0%**

## Breakdown

| Match Type | Count | Correct | Accuracy |
|------------|-------|---------|----------|
| Exact (TC) | 43428 | 24120 | 55.5% |
| Fuzzy (SDR->TC) | 17 | 0 | 0.0% |
| Fallback | 0 | 0 | - |

TC had NO match for 17 cases (0.0% of test).
SDR caught 17 of those and predicted at 0.0% accuracy.
That means 0 NEW correct predictions that TC alone missed.

## Historical Comparison

| Version | Architecture | Accuracy | Notes |
|---------|-------------|----------|-------|
| TC alone (order 3) | Exact trigram matching | ~46% | Session 24 baseline |
| TC alone (order 8) | Multi-order exact | ~57% | With backoff |
| Cortex v1 (SDR) | SDR encoder + decoder | 14% | Decoder collapsed |
| Cortex v2 (SDR+TC) | SDR fingerprints | 24% | SDR corrupted predictions |
| **Cortex v3** | **TC + SDR fallback** | **55.5%** | **This experiment** |

## Honest Analysis

Roughly tied (delta +0.0%). SDR fallback is neutral.
Two possible explanations:
1. TC's no-match cases are too rare (TC with order-8 covers most contexts)
2. SDR similarity doesn't find the RIGHT similar context -- the Hebbian
   encoding maps too many distinct contexts to similar SDRs

### Fuzzy Match Verdict

Fuzzy accuracy = 0.0% (below 20%) -- SDR is USELESS for this.

### What This Means

The v1->v2->v3 progression tested a clear hypothesis:
can SDR representations add value to character prediction?

- v1: SDR as sole predictor -- NO (14%)
- v2: SDR as primary with TC features -- NO (24%)
- v3: SDR as fallback for TC misses -- 55.5% (delta +0.0%)

For character-level prediction on this corpus, TC is king.
SDR's generalization doesn't help because:
- The corpus is small enough that TC covers most contexts
- Character-level prediction is too fine-grained for SDR similarity
- SDR might help at word or sentence level prediction instead
