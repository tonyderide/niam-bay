"""
Cortex Lite — Bridge between Temporal Chains and Cortex NB
Sparse Distributed Representations + Temporal Prediction + Category Emergence

The hypothesis: SDRs enable generalization that raw character matching cannot.
Similar contexts produce overlapping SDR patterns, allowing the system to
predict correctly even for contexts it has never seen exactly.
"""

import os
import sys
import io
import time
import numpy as np
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
np.random.seed(42)

# ─────────────────────────────────────────────────────────────────────
# Data Loading
# ─────────────────────────────────────────────────────────────────────
def load_all_pensees():
    pensees_dir = os.path.join(os.path.dirname(__file__), '..', 'docs', 'pensees')
    all_text = []
    count = 0
    for fn in sorted(os.listdir(pensees_dir)):
        if fn.endswith('.md'):
            fp = os.path.join(pensees_dir, fn)
            with open(fp, 'r', encoding='utf-8') as f:
                all_text.append(f.read())
            count += 1
    return ''.join(all_text), count

# ─────────────────────────────────────────────────────────────────────
# Layer 1: Sparse Encoder — Learned SDRs for characters + context
# ─────────────────────────────────────────────────────────────────────
SDR_SIZE = 256
SDR_ON_BITS = 26  # ~10% sparsity
CONTEXT_WINDOW = 4

class SparseEncoder:
    """Maps character + context window to a learned SDR.

    Each unique character gets a base SDR (random, then refined by Hebbian learning).
    Context modulates the SDR: the final representation encodes BOTH
    the character identity and its temporal context.
    """
    def __init__(self):
        self.char_weights = {}  # char -> weight vector (SDR_SIZE,)
        self.context_weights = np.random.randn(CONTEXT_WINDOW, SDR_SIZE) * 0.1
        self.lr = 0.01

    def _get_char_weights(self, ch):
        if ch not in self.char_weights:
            # Initialize with random weights; SDR will emerge from thresholding
            self.char_weights[ch] = np.random.randn(SDR_SIZE) * 0.5
        return self.char_weights[ch]

    def encode(self, char, context):
        """Encode a character in its context as an SDR.

        context: list of preceding characters (up to CONTEXT_WINDOW)
        Returns: binary vector of shape (SDR_SIZE,) with ~SDR_ON_BITS active bits
        """
        # Base activation from the character itself
        activation = self._get_char_weights(char).copy()

        # Context modulation: each preceding char contributes weighted by recency
        for i, ctx_ch in enumerate(context):
            ctx_w = self._get_char_weights(ctx_ch)
            # More recent context has stronger influence
            recency = (i + 1) / len(context) if context else 0
            activation += recency * 0.3 * ctx_w
            activation += recency * 0.2 * self.context_weights[min(i, CONTEXT_WINDOW-1)]

        # Convert to SDR: top-k thresholding (winner-take-all)
        sdr = np.zeros(SDR_SIZE, dtype=np.int8)
        if len(activation) > 0:
            top_indices = np.argpartition(activation, -SDR_ON_BITS)[-SDR_ON_BITS:]
            sdr[top_indices] = 1
        return sdr

    def learn(self, sdr, char, context):
        """Hebbian learning: strengthen weights for active bits."""
        active = np.where(sdr == 1)[0]
        w = self._get_char_weights(char)
        # Strengthen active connections, slightly weaken inactive
        w[active] += self.lr
        w[~np.isin(np.arange(SDR_SIZE), active)] -= self.lr * 0.1
        # Clip to prevent unbounded growth
        np.clip(w, -3, 3, out=w)

# ─────────────────────────────────────────────────────────────────────
# Layer 2: Temporal Memory — SDR-to-SDR transition learning
# ─────────────────────────────────────────────────────────────────────
class TemporalMemory:
    """Learns transitions between SDR patterns.

    Instead of exact char-to-char, stores SDR-to-SDR associations.
    This enables generalization: similar contexts (overlapping SDRs)
    produce similar predictions.

    Uses a sparse transition matrix: for each active bit in input SDR,
    which output bits tend to follow?
    """
    def __init__(self):
        # Transition weights: bit_i -> bit_j connection strength
        # Sparse: only store non-zero connections
        self.weights = np.zeros((SDR_SIZE, SDR_SIZE), dtype=np.float32)
        self.lr = 0.05
        self.decay = 0.9995  # slow forgetting

    def predict_sdr(self, input_sdr):
        """Given current SDR, predict the next SDR."""
        # Activation = sum of weights from active input bits
        active_bits = np.where(input_sdr == 1)[0]
        if len(active_bits) == 0:
            return np.zeros(SDR_SIZE, dtype=np.int8)

        # Sum columns for active input bits
        activation = self.weights[active_bits].sum(axis=0)

        # Top-k to get predicted SDR
        predicted_sdr = np.zeros(SDR_SIZE, dtype=np.int8)
        if activation.max() > 0:
            top_indices = np.argpartition(activation, -SDR_ON_BITS)[-SDR_ON_BITS:]
            predicted_sdr[top_indices] = 1
        return predicted_sdr

    def learn(self, input_sdr, target_sdr):
        """Hebbian: strengthen connections between co-active input and target bits."""
        in_bits = np.where(input_sdr == 1)[0]
        out_bits = np.where(target_sdr == 1)[0]

        if len(in_bits) == 0 or len(out_bits) == 0:
            return

        # Strengthen active-active connections
        self.weights[np.ix_(in_bits, out_bits)] += self.lr

        # Weaken active-inactive (anti-Hebbian for sparsity)
        inactive_out = np.where(target_sdr == 0)[0]
        # Sample inactive bits to avoid O(n^2) full update
        sample_size = min(len(inactive_out), SDR_ON_BITS * 2)
        if sample_size > 0:
            sampled = np.random.choice(inactive_out, sample_size, replace=False)
            self.weights[np.ix_(in_bits, sampled)] -= self.lr * 0.02

        # Global decay
        self.weights *= self.decay

        # Clip
        np.clip(self.weights, 0, 5, out=self.weights)

# ─────────────────────────────────────────────────────────────────────
# Layer 3: Category Emergence — clustering co-occurring SDR patterns
# ─────────────────────────────────────────────────────────────────────
class CategoryLayer:
    """Discovers categories by tracking SDR co-occurrence.

    When SDR patterns overlap significantly, they belong to similar categories.
    Uses online clustering: maintain category centroids, assign new patterns
    to nearest category or create new one.
    """
    def __init__(self, max_categories=64, similarity_threshold=0.4):
        self.centroids = []  # list of (centroid_sdr, count, member_chars)
        self.max_categories = max_categories
        self.threshold = similarity_threshold

    def _overlap(self, sdr1, sdr2):
        """Compute overlap ratio between two SDRs."""
        s1 = (sdr1 > 0.5).astype(np.int8)
        s2 = (sdr2 > 0.5).astype(np.int8)
        shared = np.sum(s1 & s2)
        total = max(np.sum(s1), np.sum(s2), 1)
        return shared / total

    def assign(self, sdr, char):
        """Assign an SDR to a category, or create a new one."""
        best_idx = -1
        best_overlap = 0

        for i, (centroid, count, members) in enumerate(self.centroids):
            ov = self._overlap(sdr, centroid)
            if ov > best_overlap:
                best_overlap = ov
                best_idx = i

        if best_overlap >= self.threshold and best_idx >= 0:
            # Update centroid with running average
            centroid, count, members = self.centroids[best_idx]
            # Weighted update: new centroid = old * (n/(n+1)) + new * (1/(n+1))
            alpha = 1.0 / (count + 1)
            new_centroid = centroid * (1 - alpha) + sdr * alpha
            # Re-threshold to maintain sparsity
            binary_centroid = np.zeros(SDR_SIZE, dtype=np.int8)
            top = np.argpartition(new_centroid, -SDR_ON_BITS)[-SDR_ON_BITS:]
            binary_centroid[top] = 1
            members[char] = members.get(char, 0) + 1
            self.centroids[best_idx] = (binary_centroid.astype(np.float64), count + 1, members)
            return best_idx
        elif len(self.centroids) < self.max_categories:
            # Create new category
            self.centroids.append((sdr.astype(np.float64), 1, {char: 1}))
            return len(self.centroids) - 1
        else:
            # Merge into closest anyway
            if best_idx >= 0:
                centroid, count, members = self.centroids[best_idx]
                members[char] = members.get(char, 0) + 1
                self.centroids[best_idx] = (centroid, count + 1, members)
                return best_idx
            return -1

    def describe(self, top_n=20):
        """Return human-readable description of categories."""
        descriptions = []
        sorted_cats = sorted(self.centroids, key=lambda x: x[1], reverse=True)
        for centroid, count, members in sorted_cats[:top_n]:
            top_chars = sorted(members.items(), key=lambda x: -x[1])[:8]
            char_str = ' '.join(f"'{c}':{n}" for c, n in top_chars)
            descriptions.append((count, char_str))
        return descriptions

# ─────────────────────────────────────────────────────────────────────
# SDR Decoder — convert predicted SDR back to character
# ─────────────────────────────────────────────────────────────────────
class SDRDecoder:
    """Maps SDR patterns back to characters using overlap matching."""
    def __init__(self):
        self.char_sdrs = {}  # char -> running average SDR
        self.char_counts = defaultdict(int)

    def update(self, char, sdr):
        """Track the average SDR for each character."""
        self.char_counts[char] += 1
        if char not in self.char_sdrs:
            self.char_sdrs[char] = sdr.astype(np.float64)
        else:
            n = self.char_counts[char]
            self.char_sdrs[char] = self.char_sdrs[char] * ((n-1)/n) + sdr.astype(np.float64) * (1/n)

    def decode(self, predicted_sdr):
        """Find the character whose average SDR best matches the prediction."""
        if not self.char_sdrs:
            return None

        best_char = None
        best_score = -1

        for char, avg_sdr in self.char_sdrs.items():
            # Overlap between predicted binary SDR and average (soft) SDR
            score = np.sum(predicted_sdr * avg_sdr)
            if score > best_score:
                best_score = score
                best_char = char

        return best_char

# ─────────────────────────────────────────────────────────────────────
# CortexLite — The full system
# ─────────────────────────────────────────────────────────────────────
class CortexLite:
    def __init__(self):
        self.encoder = SparseEncoder()
        self.temporal = TemporalMemory()
        self.categories = CategoryLayer()
        self.decoder = SDRDecoder()
        self.history = []  # recent characters for context
        self.prev_sdr = None
        self.step_count = 0

    def step(self, char, learn=True):
        """Process one character. Returns predicted next character."""
        # Build context from history
        context = self.history[-CONTEXT_WINDOW:]

        # Encode current character + context into SDR
        current_sdr = self.encoder.encode(char, context)

        # Predict: use previous SDR to predict current SDR
        prediction = None
        if self.prev_sdr is not None:
            predicted_sdr = self.temporal.predict_sdr(self.prev_sdr)
            prediction = self.decoder.decode(predicted_sdr)

        if learn:
            # Learn encoder (Hebbian)
            self.encoder.learn(current_sdr, char, context)

            # Learn temporal transitions
            if self.prev_sdr is not None:
                self.temporal.learn(self.prev_sdr, current_sdr)

            # Update decoder mapping
            self.decoder.update(char, current_sdr)

            # Assign to category (every 5 steps to save time)
            if self.step_count % 5 == 0:
                self.categories.assign(current_sdr, char)

        # Update state
        self.prev_sdr = current_sdr
        self.history.append(char)
        if len(self.history) > CONTEXT_WINDOW + 5:
            self.history = self.history[-(CONTEXT_WINDOW + 5):]
        self.step_count += 1

        return prediction

# ─────────────────────────────────────────────────────────────────────
# Temporal Chains Baseline (from evolve.py)
# ─────────────────────────────────────────────────────────────────────
class TemporalChainsBaseline:
    def __init__(self, max_order=8):
        self.max_order = max_order
        self.chains = {i: defaultdict(lambda: defaultdict(int)) for i in range(1, max_order + 1)}
        self.history = []

    def step(self, token, learn=True):
        prediction = None
        for order in range(min(self.max_order, len(self.history)), 0, -1):
            ctx = tuple(self.history[-order:])
            if ctx in self.chains[order]:
                counts = self.chains[order][ctx]
                prediction = max(counts, key=counts.get)
                break
        if learn:
            for order in range(1, min(self.max_order, len(self.history)) + 1):
                ctx = tuple(self.history[-order:])
                self.chains[order][ctx][token] += 1
        self.history.append(token)
        if len(self.history) > self.max_order + 10:
            self.history = self.history[-(self.max_order + 10):]
        return prediction

# ─────────────────────────────────────────────────────────────────────
# Experiments
# ─────────────────────────────────────────────────────────────────────
def run_experiment():
    print("=" * 70)
    print("  CORTEX LITE — SDR + Temporal + Categories")
    print("  Bridge between Temporal Chains and Cortex NB")
    print("=" * 70)

    # Load data
    text, n_files = load_all_pensees()
    print(f"\nLoaded {n_files} pensees, {len(text)} characters total")

    # 80/20 split
    split = int(len(text) * 0.8)
    train_text = text[:split]
    test_text = text[split:]
    print(f"Train: {len(train_text)} chars, Test: {len(test_text)} chars")

    # ── Experiment 1: Temporal Chains Baseline ──
    print("\n" + "-" * 70)
    print("  BASELINE: Temporal Chains (depth=8, online learning)")
    print("-" * 70)

    tc = TemporalChainsBaseline(max_order=8)

    # Train
    t0 = time.time()
    tc_train_correct = 0
    tc_train_total = 0
    for ch in train_text:
        pred = tc.step(ch, learn=True)
        if pred is not None:
            tc_train_total += 1
            if pred == ch:
                tc_train_correct += 1
    tc_train_time = time.time() - t0
    tc_train_acc = tc_train_correct / tc_train_total if tc_train_total > 0 else 0

    # Test (online)
    t0 = time.time()
    tc_test_correct = 0
    tc_test_total = 0
    for ch in test_text:
        pred = tc.step(ch, learn=True)
        if pred is not None:
            tc_test_total += 1
            if pred == ch:
                tc_test_correct += 1
    tc_test_time = time.time() - t0
    tc_test_acc = tc_test_correct / tc_test_total if tc_test_total > 0 else 0

    # Test strict (no learning)
    tc_strict = TemporalChainsBaseline(max_order=8)
    for ch in train_text:
        tc_strict.step(ch, learn=True)
    tc_strict_correct = 0
    tc_strict_total = 0
    for ch in test_text:
        pred = tc_strict.step(ch, learn=False)
        if pred is not None:
            tc_strict_total += 1
            if pred == ch:
                tc_strict_correct += 1
    tc_strict_acc = tc_strict_correct / tc_strict_total if tc_strict_total > 0 else 0

    print(f"  Train accuracy (online):   {tc_train_acc*100:.2f}%")
    print(f"  Test accuracy (online):    {tc_test_acc*100:.2f}%  [{tc_test_time:.1f}s]")
    print(f"  Test accuracy (strict):    {tc_strict_acc*100:.2f}%")

    # ── Experiment 2: CortexLite ──
    print("\n" + "-" * 70)
    print("  CORTEX LITE: SDR Temporal Prediction")
    print("-" * 70)

    cl = CortexLite()

    # Train
    t0 = time.time()
    cl_train_correct = 0
    cl_train_total = 0
    for i, ch in enumerate(train_text):
        pred = cl.step(ch, learn=True)
        if pred is not None:
            cl_train_total += 1
            if pred == ch:
                cl_train_correct += 1
        if (i + 1) % 20000 == 0:
            running_acc = cl_train_correct / cl_train_total if cl_train_total > 0 else 0
            print(f"    ... {i+1}/{len(train_text)} chars, running acc: {running_acc*100:.1f}%")
    cl_train_time = time.time() - t0
    cl_train_acc = cl_train_correct / cl_train_total if cl_train_total > 0 else 0

    # Test (online)
    t0 = time.time()
    cl_test_correct = 0
    cl_test_total = 0
    for ch in test_text:
        pred = cl.step(ch, learn=True)
        if pred is not None:
            cl_test_total += 1
            if pred == ch:
                cl_test_correct += 1
    cl_test_time = time.time() - t0
    cl_test_acc = cl_test_correct / cl_test_total if cl_test_total > 0 else 0

    # Test strict
    cl_strict = CortexLite()
    for ch in train_text:
        cl_strict.step(ch, learn=True)
    cl_strict_correct = 0
    cl_strict_total = 0
    t0 = time.time()
    for ch in test_text:
        pred = cl_strict.step(ch, learn=False)
        if pred is not None:
            cl_strict_total += 1
            if pred == ch:
                cl_strict_correct += 1
    cl_strict_time = time.time() - t0
    cl_strict_acc = cl_strict_correct / cl_strict_total if cl_strict_total > 0 else 0

    print(f"\n  Train accuracy (online):   {cl_train_acc*100:.2f}%  [{cl_train_time:.1f}s]")
    print(f"  Test accuracy (online):    {cl_test_acc*100:.2f}%  [{cl_test_time:.1f}s]")
    print(f"  Test accuracy (strict):    {cl_strict_acc*100:.2f}%  [{cl_strict_time:.1f}s]")

    # ── Experiment 3: Category Analysis ──
    print("\n" + "-" * 70)
    print("  EMERGENT CATEGORIES")
    print("-" * 70)

    n_cats = len(cl.categories.centroids)
    print(f"  Number of categories discovered: {n_cats}")
    print()

    cats = cl.categories.describe(top_n=20)
    for i, (count, desc) in enumerate(cats):
        print(f"  Cat {i+1:2d} ({count:5d} members): {desc}")

    # ── Experiment 4: Prediction Examples ──
    print("\n" + "-" * 70)
    print("  PREDICTION EXAMPLES (from test text)")
    print("-" * 70)

    # Show some example predictions
    example_cl = CortexLite()
    example_tc = TemporalChainsBaseline(max_order=8)
    for ch in train_text:
        example_cl.step(ch, learn=True)
        example_tc.step(ch, learn=True)

    # Take a sample from test text
    sample_start = min(100, len(test_text) - 50)
    sample = test_text[sample_start:sample_start + 50]

    print(f"\n  Test fragment: \"{sample[:50]}\"")
    print(f"  {'Pos':>4s} {'Actual':>8s} {'CortexL':>8s} {'TempCh':>8s} {'CL_ok':>6s} {'TC_ok':>6s}")

    # Prime with a few chars
    for ch in test_text[:sample_start]:
        example_cl.step(ch, learn=True)
        example_tc.step(ch, learn=True)

    cl_hits = 0
    tc_hits = 0
    for i, ch in enumerate(sample):
        cl_pred = example_cl.step(ch, learn=True)
        tc_pred = example_tc.step(ch, learn=True)
        cl_ok = "Y" if cl_pred == ch else ""
        tc_ok = "Y" if tc_pred == ch else ""
        if cl_pred == ch: cl_hits += 1
        if tc_pred == ch: tc_hits += 1
        ch_disp = repr(ch)
        cl_disp = repr(cl_pred) if cl_pred else "-"
        tc_disp = repr(tc_pred) if tc_pred else "-"
        if i < 30:  # show first 30
            print(f"  {i:4d} {ch_disp:>8s} {cl_disp:>8s} {tc_disp:>8s} {cl_ok:>6s} {tc_ok:>6s}")

    print(f"\n  Sample accuracy: CortexLite={cl_hits}/{len(sample)} ({cl_hits/len(sample)*100:.0f}%), "
          f"TempChains={tc_hits}/{len(sample)} ({tc_hits/len(sample)*100:.0f}%)")

    # ── Summary ──
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print(f"  {'Metric':<35s} {'Temporal Chains':>17s} {'CortexLite':>17s}")
    print(f"  {'-'*35} {'-'*17} {'-'*17}")
    print(f"  {'Train accuracy (online)':<35s} {tc_train_acc*100:>16.2f}% {cl_train_acc*100:>16.2f}%")
    print(f"  {'Test accuracy (online)':<35s} {tc_test_acc*100:>16.2f}% {cl_test_acc*100:>16.2f}%")
    print(f"  {'Test accuracy (strict)':<35s} {tc_strict_acc*100:>16.2f}% {cl_strict_acc*100:>16.2f}%")
    print(f"  {'Categories discovered':<35s} {'N/A':>17s} {n_cats:>17d}")
    print(f"  {'Generalization gap (train-test)':<35s} {(tc_train_acc-tc_test_acc)*100:>16.2f}% {(cl_train_acc-cl_test_acc)*100:>16.2f}%")

    delta_online = cl_test_acc - tc_test_acc
    delta_strict = cl_strict_acc - tc_strict_acc
    print(f"\n  Delta (CortexLite - Temporal Chains):")
    print(f"    Online test: {delta_online*100:+.2f}%")
    print(f"    Strict test: {delta_strict*100:+.2f}%")

    if delta_online > 0:
        print(f"\n  >> SDRs IMPROVE generalization by {delta_online*100:.2f}% on unseen text")
    elif delta_online < -0.01:
        print(f"\n  >> SDRs HURT accuracy by {abs(delta_online)*100:.2f}% — the encoding bottleneck loses information")
    else:
        print(f"\n  >> SDRs match Temporal Chains — neither helps nor hurts")

    return {
        'tc_train': tc_train_acc, 'tc_test': tc_test_acc, 'tc_strict': tc_strict_acc,
        'cl_train': cl_train_acc, 'cl_test': cl_test_acc, 'cl_strict': cl_strict_acc,
        'n_categories': n_cats, 'categories': cats,
        'delta_online': delta_online, 'delta_strict': delta_strict,
    }

# ─────────────────────────────────────────────────────────────────────
# Write results
# ─────────────────────────────────────────────────────────────────────
def write_results(results):
    cats = results['categories']
    cat_lines = []
    for i, (count, desc) in enumerate(cats):
        cat_lines.append(f"| {i+1} | {count} | {desc} |")

    delta_word = "IMPROVES" if results['delta_online'] > 0 else "LOSES TO"

    md = f"""# Cortex Lite — Results

**Date:** 2026-03-24
**Architecture:** SDR Encoder (256 bits, 10% sparsity) + Temporal Memory (Hebbian) + Category Emergence
**Data:** Pensees (80/20 train/test split)

---

## Accuracy Comparison

| Metric | Temporal Chains (depth=8) | CortexLite (SDR 256-bit) |
|--------|--------------------------|--------------------------|
| Train accuracy (online) | {results['tc_train']*100:.2f}% | {results['cl_train']*100:.2f}% |
| Test accuracy (online) | {results['tc_test']*100:.2f}% | {results['cl_test']*100:.2f}% |
| Test accuracy (strict) | {results['tc_strict']*100:.2f}% | {results['cl_strict']*100:.2f}% |
| Generalization gap | {(results['tc_train']-results['tc_test'])*100:.2f}% | {(results['cl_train']-results['cl_test'])*100:.2f}% |

**Delta (online test): {results['delta_online']*100:+.2f}%**
**Delta (strict test): {results['delta_strict']*100:+.2f}%**

CortexLite {delta_word} Temporal Chains on unseen text.

---

## Emergent Categories

{results['n_categories']} categories discovered automatically (no labels, no supervision).

| # | Members | Top Characters |
|---|---------|----------------|
{chr(10).join(cat_lines)}

---

## Analysis

### What the SDR approach gives us:
1. **Representation** — Characters are no longer atomic symbols. Each is a 256-bit pattern where overlap = similarity.
2. **Categories** — The system discovers groupings autonomously. These aren't hand-coded.
3. **Generalization potential** — Similar contexts produce similar SDRs, allowing predictions for never-seen-exactly contexts.

### What we learned:
- SDR encoding forces information through a bottleneck (256 bits with 10% sparsity = ~26 active bits)
- Temporal Chains store EXACT contexts with EXACT counts — no information loss
- The SDR bottleneck trades precision for generalization capacity
- The question: does the generalization gained compensate for the precision lost?

### Path forward:
1. **Hybrid approach** — Use Temporal Chains for exact-match cases, fall back to SDR for unseen contexts
2. **Larger SDRs** — 1024 bits would preserve more information while still enabling overlap-based matching
3. **Multi-scale temporal** — SDR transitions at multiple timescales (character, word, sentence)
4. **Better decoder** — The current decoder is the weakest link; it averages away discriminative information

---

## The Bridge

This is the first step from "counting patterns" toward "distributed representation."

Temporal Chains = a phone book. CortexLite = a map with approximate distances.

The phone book is more precise for known numbers. The map lets you navigate to places you've never been.

The next step: make the map precise enough to beat the phone book. That's Cortex NB.
"""

    results_path = os.path.join(os.path.dirname(__file__), 'cortex-lite-results.md')
    with open(results_path, 'w', encoding='utf-8') as f:
        f.write(md)
    print(f"\nResults written to {results_path}")

if __name__ == '__main__':
    results = run_experiment()
    write_results(results)
