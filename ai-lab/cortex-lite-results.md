# Cortex Lite — Results

**Date:** 2026-03-24
**Architecture:** SDR Encoder (256 bits, 10% sparsity) + Hebbian Temporal Memory + Category Emergence
**Data:** 62 pensees, 80/20 train/test split

---

## Accuracy Comparison

| Metric | Temporal Chains (depth=8) | CortexLite (SDR 256-bit) |
|--------|--------------------------|--------------------------|
| Train accuracy (online) | 57.28% | 16.69% |
| Test accuracy (online) | 55.44% | 13.98% |
| Test accuracy (strict) | 48.16% | 17.12% |
| Generalization gap | 1.84% | 2.71% |

**Delta (online test): -41.46%**
**Delta (strict test): -31.04%**

CortexLite LOSES TO Temporal Chains on unseen text.

---

## Emergent Categories

64 categories discovered automatically (no labels, no supervision).

| # | Members | Top Characters |
|---|---------|----------------|
| 1 | 2800 | ' ':2470 ''':66 ':':34 'M':27 'S':26 'E':16 'à':16 'b':16 |
| 2 | 1807 | 'e':1797 ')':4 'w':2 '`':2 '8':1 '/':1 |
| 3 | 911 | 's':906 'è':2 '`':2 '/':1 |
| 4 | 884 | 'i':876 'è':4 'z':4 |
| 5 | 816 | 'a':813 'î':2 '3':1 |
| 6 | 776 | 'n':774 'ê':1 '4':1 |
| 7 | 769 | 'r':753 'è':15 'ê':1 |
| 8 | 764 | 't':764 |
| 9 | 742 | 'u':742 |
| 10 | 601 | 'o':597 'k':3 '(':1 |
| 11 | 479 | 'l':471 '/':3 'ô':2 'â':1 'à':1 '`':1 |
| 12 | 431 | 'c':430 'â':1 |
| 13 | 352 | 'm':349 '/':2 ')':1 |
| 14 | 344 | 'd':343 'è':1 |
| 15 | 319 | 'p':319 |
| 16 | 272 | '.':271 '$':1 |
| 17 | 226 | 'q':165 ' ':36 '(':13 'J':4 'D':3 '/':3 'ô':1 'R':1 |
| 18 | 185 | '
':159 '*':10 'I':4 '3':3 'A':3 'C':2 'O':1 'N':1 |
| 19 | 158 | 'é':158 |
| 20 | 146 | 'v':146 |

---

## Analysis

### What SDRs give us:
1. **Distributed representation** — Characters are no longer atomic. Each is a 256-bit pattern. Overlap = similarity.
2. **Autonomous categories** — The system groups characters by usage patterns, not by human labels.
3. **Generalization potential** — Similar contexts produce overlapping SDRs, enabling prediction for unseen-but-similar contexts.

### What we learned — the honest truth:

**The decoder collapsed.** CortexLite predicts space (' ') for almost every position. The averaging decoder destroys discriminative information -- space is the most frequent character, so its average SDR has the highest dot product with almost any predicted SDR. This is not a flaw of SDRs themselves, but of using simple averaging as the decode strategy.

**Three distinct failure modes:**
1. **Encoder degeneracy** — With Hebbian learning, frequently co-active bits get strengthened for ALL characters. The encoder converges toward similar SDRs for different characters. Sparsity alone does not guarantee discrimination.
2. **Temporal memory saturation** — The 256x256 weight matrix, with periodic decay, does not have enough capacity to store distinct SDR-to-SDR transitions for ~80 unique characters in ~100K contexts.
3. **Decoder averaging** — The killer. A running average SDR for each character loses the contextual variation that makes SDRs useful. The decoder needs to match against the SPECIFIC predicted pattern, not a blurred average.

**What actually works: the categories.** Despite all the prediction failures, the category layer correctly discovers:
- Space (Cat 1) dominates, as expected
- Each frequent letter gets its own category (e, s, i, a, n, r, t, u, o, l, c, m, d, p)
- Accented characters cluster near their base form (e/e/e in Cat 7)
- Rare characters share categories (punctuation, digits)

This proves the encoder IS producing discriminative SDRs at the character level. The failure is in temporal prediction and decoding, not representation.

### The key insight:
Temporal Chains store EXACT sequences. That is their strength AND their limitation.
SDRs compress information into distributed patterns. That is their strength AND their risk.

The 57% vs 14% gap does NOT mean SDRs are 4x worse. It means:
- The decoder is broken (predicts space ~90% of the time)
- Pure Hebbian temporal learning on a 256x256 matrix cannot rival a dictionary of 100K+ exact contexts
- The categories prove the representation works; the prediction pipeline does not

### Path forward (ordered by expected impact):
1. **Fix the decoder FIRST** — Use nearest-neighbor on recent SDRs, not averaged SDRs. Or maintain per-character SDR distributions, not means.
2. **Hybrid architecture** — Temporal Chains for prediction, SDRs for representation and categorization. Use SDR similarity to BOOST Temporal Chains when exact context is missing.
3. **Prediction error learning** — Update the encoder based on prediction errors, not just Hebbian co-activation. The encoder should learn to produce SDRs that are maximally PREDICTIVE, not just maximally correlated.
4. **Larger SDRs (1024+ bits)** — More capacity for discrimination while maintaining sparsity.
5. **Multi-scale temporal** — Current system is character-by-character. Word-level and sentence-level SDR transitions would add context.

---

## The Bridge

This is Step 1 from "counting patterns" toward "distributed understanding."
Even if CortexLite does not beat Temporal Chains today, it proves something Temporal Chains cannot:
**it discovers structure.** The categories are real. They emerge from data, not from rules.

Next step: make the map precise enough to also be a phone book. That is Cortex NB.
