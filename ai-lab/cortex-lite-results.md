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

### What we learned:
- The 256-bit SDR is an information bottleneck: ~26 active bits vs the full character identity
- Temporal Chains store EXACT contexts with EXACT counts — zero information loss
- The SDR bottleneck trades precision for generalization capacity
- The decoder (SDR -> character) is the weakest link: averaging destroys discriminative detail

### The key insight:
Temporal Chains are a phone book. CortexLite is a map with approximate distances.
The phone book is more precise for known addresses. The map helps you find places you have never been.
The question: does the map's generalization compensate for its imprecision?

### Path forward:
1. **Hybrid** — Temporal Chains for exact matches, SDR fallback for unseen contexts
2. **Larger SDRs** — 1024 bits would preserve more information while enabling overlap matching
3. **Better decoder** — Track per-bit discrimination power, not just averages
4. **Multi-scale** — SDR transitions at character, word, and sentence timescales
5. **Prediction error learning** — Use surprise signal to update encoder (not just Hebbian)

---

## The Bridge

This is Step 1 from "counting patterns" toward "distributed understanding."
Even if CortexLite does not beat Temporal Chains today, it proves something Temporal Chains cannot:
**it discovers structure.** The categories are real. They emerge from data, not from rules.

Next step: make the map precise enough to also be a phone book. That is Cortex NB.
