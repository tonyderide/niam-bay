# Cortex NB v2 -- Results

**Date**: 2026-03-24 03:04

## Architecture

- **Layer 1**: SDR Encoder (Hebbian, 256 bits, ~10% active)
- **Layer 2**: Temporal Memory on position-aware SDR fingerprints
- **Layer 3**: Direct char prediction (no SDR decoder -- avoids collapse)
- Context window: 3 chars
- Fuzzy threshold: 0.4
- Hebbian LR: 0.01

## Data

- Total: 214349 chars from pensees
- Train: 171479 chars (80%)
- Test: 42870 chars (20%)
- Sampled test: 5359 predictions

## Results

| Metric | Temporal Chains | Cortex v2 |
|--------|----------------|-----------|
| Accuracy (sampled) | 46.4% | 24.3% |
| Train time | 0.1s | 13.2s |
| Unique contexts | 9557 | 2854 |

**Delta: -22.1% -- Winner: Temporal Chains**

## Breakdown

- Exact matches: 5265 (1287 correct = 24.4%)
- Fuzzy matches: 94 (16 correct = 17.0%)
- Failed: 0

Exact accuracy: 24.4%
Fuzzy accuracy: 17.0%

## Emergent Categories

  1. [#, SPC, C, e, q, u, j, v, o, i, s, NL, *, 2, 0, -, 1, h, T, —, N, a, m, y, p, r, t, g, c, n, l, d, ., ', :, ", D, A, à, L, é, b, f, è, M, ê, P, ,, k, x, E, I, J, (, /, 8]
  2. [6, 3, U, S, )]
  3. [4, 5]

## Example Predictions

```
  'vol' -> Cortex:' '    (exact) | TC:'u' OK | actual:'u'
  'lut' -> Cortex:' '    (exact) | TC:'i' OK | actual:'i'
  'ode' -> Cortex:' '    (exact) | TC:' '    | actual:'l'
  '202' -> Cortex:'6' OK (exact) | TC:'6' OK | actual:'6'
  'l'e' -> Cortex:'s'    (exact) | TC:'s'    | actual:'c'
  '\n\n-' -> Cortex:'-' OK (exact) | TC:'-' OK | actual:'-'
  ' re' -> Cortex:' '    (exact) | TC:'s'    | actual:'v'
  'ise' -> Cortex:' ' OK (exact) | TC:' ' OK | actual:' '
  ' le' -> Cortex:' '    (exact) | TC:' '    | actual:'s'
  '--\n' -> Cortex:'\n' OK (exact) | TC:'\n' OK | actual:'\n'
  ' l'' -> Cortex:' '    (exact) | TC:'a'    | actual:'I'
  ' ma' -> Cortex:' '    (exact) | TC:'r' OK | actual:'r'
  'bi.' -> Cortex:' '    (exact) | TC:' '    | actual:'n'
  'nt ' -> Cortex:'d'    (exact) | TC:'d'    | actual:'l'
  'des' -> Cortex:' ' OK (exact) | TC:' ' OK | actual:' '
  'w (' -> Cortex:'k'    (fuzzy) | TC:' '    | actual:'P'
  'fai' -> Cortex:' '    (exact) | TC:'t' OK | actual:'t'
  'pro' -> Cortex:' '    (exact) | TC:'d'    | actual:'c'
  ' mo' -> Cortex:' '    (exact) | TC:'i'    | actual:'d'
  'e d' -> Cortex:'e' OK (exact) | TC:'e' OK | actual:'e'
```

## Analysis

Temporal Chains still wins. Analysis:

The SDR fingerprint approach collapses the 9500+ unique char trigrams
into fewer SDR patterns. This compression may lose discriminative power.

Key insight: the OR-union fingerprint, even with position shifts,
still has high collision rate. Different trigrams map to the same SDR.
This HURTS exact matching (lumps distinct contexts together) and
fuzzy matching becomes irrelevant because most things are already
'matched' via collision.

### What would actually work

The fundamental problem: SDR union-fingerprints are lossy for short sequences.
Temporal Chains on raw chars already capture character-level patterns perfectly.

Where SDR could win:
1. **Longer contexts** (10+ chars) where exact trigram matching fails
2. **Cross-language generalization** where similar phonetics map to similar SDRs
3. **Hierarchical prediction** -- SDR categories predict word-level patterns,
   TC handles char-level

## Honest Post-Mortem

### Why the encoder "works" but the system doesn't

The SDR encoder DOES learn categories -- characters that appear together get
similar representations. But for next-character prediction, this is actually
harmful at short context windows:

- "vol" and "col" and "sol" get SIMILAR SDR fingerprints (shared letters)
- But their predictions differ: "u" vs "l" vs "u" vs "i" etc.
- SDR compression merges these into one pattern, then the majority vote
  picks the wrong one

Temporal Chains keep them separate because they use EXACT character identity.
The 9557 unique trigrams are 9557 distinct predictions. SDR crushes these
to 2854, losing 70% of discriminative power.

### The fuzzy matching paradox

Fuzzy matching was supposed to help: "if I've never seen this exact context,
find something similar." But:
- Only 94 out of 5359 test cases needed fuzzy (1.8%)
- Because the SDR fingerprints are SO coarse, almost everything "exact matches"
  something (even if it's the wrong something)
- Fuzzy accuracy (17%) is even WORSE than exact (24.4%)

### What v3 should try

The combination idea is sound, but the architecture needs flipping:
- **Use TC as the primary predictor** (it's fast and accurate)
- **Use SDR only as FALLBACK** when TC has no exact match
- This way SDR handles the ~15% of cases where TC fails (unknown trigrams),
  and TC handles the 85% where exact matching is superior

That hybrid would be: TC accuracy on known contexts + SDR fuzzy on unknown.
Expected: ~48-50% (TC's 46% + some fuzzy gains on the 54% TC misses).
