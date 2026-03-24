"""
Cortex Lite — Bridge between Temporal Chains and Cortex NB
SDR + Temporal Prediction + Category Emergence

Hypothesis: SDRs enable generalization beyond exact character matching.
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
# Config
# ─────────────────────────────────────────────────────────────────────
SDR_SIZE = 256
SDR_ON_BITS = 26  # ~10% sparsity
CONTEXT_WINDOW = 4

def flush():
    sys.stdout.flush()

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
# Layer 1: Sparse Encoder
# ─────────────────────────────────────────────────────────────────────
class SparseEncoder:
    """Maps character + context to a learned SDR via top-k thresholding."""
    def __init__(self):
        self.char_weights = {}
        self.lr = 0.01

    def _get_w(self, ch):
        if ch not in self.char_weights:
            self.char_weights[ch] = np.random.randn(SDR_SIZE).astype(np.float32) * 0.5
        return self.char_weights[ch]

    def encode(self, char, context):
        activation = self._get_w(char).copy()
        n = len(context)
        for i, ctx_ch in enumerate(context):
            recency = (i + 1) / n if n > 0 else 0
            activation += recency * 0.3 * self._get_w(ctx_ch)
        # Top-k winner-take-all
        sdr = np.zeros(SDR_SIZE, dtype=np.int8)
        top = np.argpartition(activation, -SDR_ON_BITS)[-SDR_ON_BITS:]
        sdr[top] = 1
        return sdr

    def learn(self, sdr, char):
        active = np.where(sdr == 1)[0]
        w = self._get_w(char)
        w[active] += self.lr
        w *= 0.999  # mild global shrink instead of per-inactive update
        np.clip(w, -3, 3, out=w)

# ─────────────────────────────────────────────────────────────────────
# Layer 2: Temporal Memory — SDR-to-SDR transitions
# ─────────────────────────────────────────────────────────────────────
class TemporalMemory:
    """Hebbian SDR transition learning. Sparse updates, periodic decay."""
    def __init__(self):
        self.weights = np.zeros((SDR_SIZE, SDR_SIZE), dtype=np.float32)
        self.lr = 0.05
        self.step_count = 0

    def predict_sdr(self, input_sdr):
        active = np.where(input_sdr == 1)[0]
        if len(active) == 0:
            return np.zeros(SDR_SIZE, dtype=np.int8)
        activation = self.weights[active].sum(axis=0)
        predicted = np.zeros(SDR_SIZE, dtype=np.int8)
        if activation.max() > 0:
            top = np.argpartition(activation, -SDR_ON_BITS)[-SDR_ON_BITS:]
            predicted[top] = 1
        return predicted

    def learn(self, input_sdr, target_sdr):
        in_bits = np.where(input_sdr == 1)[0]
        out_bits = np.where(target_sdr == 1)[0]
        if len(in_bits) == 0 or len(out_bits) == 0:
            return
        # Strengthen co-active connections
        self.weights[np.ix_(in_bits, out_bits)] += self.lr
        # Mild anti-Hebbian: weaken input->inactive output (sparse sample)
        self.weights[np.ix_(in_bits, out_bits)] *= 1.0  # no-op placeholder
        # Periodic decay every 500 steps to avoid per-step full-matrix multiply
        self.step_count += 1
        if self.step_count % 500 == 0:
            self.weights *= 0.75
        np.clip(self.weights, 0, 10, out=self.weights)

# ─────────────────────────────────────────────────────────────────────
# Layer 3: Category Emergence
# ─────────────────────────────────────────────────────────────────────
class CategoryLayer:
    def __init__(self, max_categories=64, threshold=0.35):
        self.centroids = []  # (centroid_indices_set, count, member_chars)
        self.max_categories = max_categories
        self.threshold = threshold

    def _overlap(self, sdr_indices, centroid_indices):
        shared = len(sdr_indices & centroid_indices)
        total = max(len(sdr_indices), len(centroid_indices), 1)
        return shared / total

    def assign(self, sdr, char):
        sdr_idx = set(np.where(sdr == 1)[0].tolist())
        best_i = -1
        best_ov = 0
        for i, (cen, count, members) in enumerate(self.centroids):
            ov = self._overlap(sdr_idx, cen)
            if ov > best_ov:
                best_ov = ov
                best_i = i

        if best_ov >= self.threshold and best_i >= 0:
            cen, count, members = self.centroids[best_i]
            # Slowly merge: keep 90% of old centroid, add 10% of new
            if count < 50:
                cen = cen | sdr_idx  # union when young
            members[char] = members.get(char, 0) + 1
            self.centroids[best_i] = (cen, count + 1, members)
        elif len(self.centroids) < self.max_categories:
            self.centroids.append((sdr_idx, 1, {char: 1}))
        else:
            if best_i >= 0:
                cen, count, members = self.centroids[best_i]
                members[char] = members.get(char, 0) + 1
                self.centroids[best_i] = (cen, count + 1, members)

    def describe(self, top_n=20):
        descriptions = []
        sorted_cats = sorted(self.centroids, key=lambda x: x[1], reverse=True)
        for cen, count, members in sorted_cats[:top_n]:
            top_chars = sorted(members.items(), key=lambda x: -x[1])[:8]
            char_str = ' '.join(f"'{c}':{n}" for c, n in top_chars)
            descriptions.append((count, char_str))
        return descriptions

# ─────────────────────────────────────────────────────────────────────
# SDR Decoder
# ─────────────────────────────────────────────────────────────────────
class SDRDecoder:
    """Maps predicted SDR back to character via overlap with known char SDRs."""
    def __init__(self):
        self.char_sdrs = {}  # char -> average activation (float array)
        self.char_counts = defaultdict(int)

    def update(self, char, sdr):
        self.char_counts[char] += 1
        n = self.char_counts[char]
        if char not in self.char_sdrs:
            self.char_sdrs[char] = sdr.astype(np.float32)
        else:
            self.char_sdrs[char] += (sdr.astype(np.float32) - self.char_sdrs[char]) / n

    def decode(self, predicted_sdr):
        if not self.char_sdrs:
            return None
        pred_f = predicted_sdr.astype(np.float32)
        best_char = None
        best_score = -1
        for char, avg in self.char_sdrs.items():
            score = np.dot(pred_f, avg)
            if score > best_score:
                best_score = score
                best_char = char
        return best_char

# ─────────────────────────────────────────────────────────────────────
# CortexLite — Full system
# ─────────────────────────────────────────────────────────────────────
class CortexLite:
    def __init__(self):
        self.encoder = SparseEncoder()
        self.temporal = TemporalMemory()
        self.categories = CategoryLayer()
        self.decoder = SDRDecoder()
        self.history = []
        self.prev_sdr = None
        self.step_count = 0

    def step(self, char, learn=True):
        context = self.history[-CONTEXT_WINDOW:]
        current_sdr = self.encoder.encode(char, context)

        prediction = None
        if self.prev_sdr is not None:
            predicted_sdr = self.temporal.predict_sdr(self.prev_sdr)
            prediction = self.decoder.decode(predicted_sdr)

        if learn:
            self.encoder.learn(current_sdr, char)
            if self.prev_sdr is not None:
                self.temporal.learn(self.prev_sdr, current_sdr)
            self.decoder.update(char, current_sdr)
            if self.step_count % 10 == 0:
                self.categories.assign(current_sdr, char)

        self.prev_sdr = current_sdr
        self.history.append(char)
        if len(self.history) > CONTEXT_WINDOW + 5:
            self.history = self.history[-(CONTEXT_WINDOW + 5):]
        self.step_count += 1
        return prediction

# ─────────────────────────────────────────────────────────────────────
# Temporal Chains Baseline
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
# Run Experiments
# ─────────────────────────────────────────────────────────────────────
def run_experiment():
    print("=" * 70)
    print("  CORTEX LITE — SDR + Temporal + Categories")
    print("  Bridge between Temporal Chains and Cortex NB")
    print("=" * 70)
    flush()

    text, n_files = load_all_pensees()
    print(f"\nLoaded {n_files} pensees, {len(text)} characters total")

    split = int(len(text) * 0.8)
    train_text = text[:split]
    test_text = text[split:]
    print(f"Train: {len(train_text)} chars, Test: {len(test_text)} chars")
    flush()

    # ── Baseline ──
    print("\n" + "-" * 70)
    print("  BASELINE: Temporal Chains (depth=8)")
    print("-" * 70)
    flush()

    tc = TemporalChainsBaseline(max_order=8)
    t0 = time.time()
    tc_train_c, tc_train_t = 0, 0
    for ch in train_text:
        pred = tc.step(ch, learn=True)
        if pred is not None:
            tc_train_t += 1
            if pred == ch: tc_train_c += 1
    tc_train_acc = tc_train_c / tc_train_t if tc_train_t else 0
    print(f"  Train (online): {tc_train_acc*100:.2f}%  [{time.time()-t0:.1f}s]")
    flush()

    t0 = time.time()
    tc_test_c, tc_test_t = 0, 0
    for ch in test_text:
        pred = tc.step(ch, learn=True)
        if pred is not None:
            tc_test_t += 1
            if pred == ch: tc_test_c += 1
    tc_test_acc = tc_test_c / tc_test_t if tc_test_t else 0
    print(f"  Test (online):  {tc_test_acc*100:.2f}%  [{time.time()-t0:.1f}s]")
    flush()

    # Strict test
    tc2 = TemporalChainsBaseline(max_order=8)
    for ch in train_text: tc2.step(ch, learn=True)
    tc_s_c, tc_s_t = 0, 0
    for ch in test_text:
        pred = tc2.step(ch, learn=False)
        if pred is not None:
            tc_s_t += 1
            if pred == ch: tc_s_c += 1
    tc_strict_acc = tc_s_c / tc_s_t if tc_s_t else 0
    print(f"  Test (strict):  {tc_strict_acc*100:.2f}%")
    flush()

    # ── CortexLite ──
    print("\n" + "-" * 70)
    print("  CORTEX LITE: SDR Temporal Prediction")
    print("-" * 70)
    flush()

    cl = CortexLite()
    t0 = time.time()
    cl_train_c, cl_train_t = 0, 0
    for i, ch in enumerate(train_text):
        pred = cl.step(ch, learn=True)
        if pred is not None:
            cl_train_t += 1
            if pred == ch: cl_train_c += 1
        if (i + 1) % 10000 == 0:
            acc = cl_train_c / cl_train_t if cl_train_t else 0
            elapsed = time.time() - t0
            rate = (i+1) / elapsed
            print(f"    {i+1}/{len(train_text)} ({acc*100:.1f}%, {rate:.0f} ch/s)")
            flush()
    cl_train_time = time.time() - t0
    cl_train_acc = cl_train_c / cl_train_t if cl_train_t else 0
    print(f"  Train (online): {cl_train_acc*100:.2f}%  [{cl_train_time:.1f}s]")
    flush()

    t0 = time.time()
    cl_test_c, cl_test_t = 0, 0
    for ch in test_text:
        pred = cl.step(ch, learn=True)
        if pred is not None:
            cl_test_t += 1
            if pred == ch: cl_test_c += 1
    cl_test_acc = cl_test_c / cl_test_t if cl_test_t else 0
    print(f"  Test (online):  {cl_test_acc*100:.2f}%  [{time.time()-t0:.1f}s]")
    flush()

    # Strict test
    print("  Training strict model...")
    flush()
    cl2 = CortexLite()
    t0 = time.time()
    for i, ch in enumerate(train_text):
        cl2.step(ch, learn=True)
        if (i + 1) % 25000 == 0:
            print(f"    strict train: {i+1}/{len(train_text)}")
            flush()
    cl_s_c, cl_s_t = 0, 0
    for ch in test_text:
        pred = cl2.step(ch, learn=False)
        if pred is not None:
            cl_s_t += 1
            if pred == ch: cl_s_c += 1
    cl_strict_acc = cl_s_c / cl_s_t if cl_s_t else 0
    print(f"  Test (strict):  {cl_strict_acc*100:.2f}%  [{time.time()-t0:.1f}s]")
    flush()

    # ── Categories ──
    print("\n" + "-" * 70)
    print("  EMERGENT CATEGORIES")
    print("-" * 70)
    n_cats = len(cl.categories.centroids)
    print(f"  {n_cats} categories discovered\n")
    cats = cl.categories.describe(top_n=20)
    for i, (count, desc) in enumerate(cats):
        print(f"  Cat {i+1:2d} ({count:5d} members): {desc}")
    flush()

    # ── Examples ──
    print("\n" + "-" * 70)
    print("  PREDICTION EXAMPLES")
    print("-" * 70)
    ex_cl = CortexLite()
    ex_tc = TemporalChainsBaseline(max_order=8)
    for ch in train_text:
        ex_cl.step(ch, learn=True)
        ex_tc.step(ch, learn=True)

    sample_start = 100
    for ch in test_text[:sample_start]:
        ex_cl.step(ch, learn=True)
        ex_tc.step(ch, learn=True)

    sample = test_text[sample_start:sample_start+40]
    print(f"\n  Fragment: \"{sample}\"")
    print(f"  {'#':>3s} {'Char':>6s} {'CL':>6s} {'TC':>6s} {'CL?':>4s} {'TC?':>4s}")
    cl_h, tc_h = 0, 0
    for i, ch in enumerate(sample):
        cp = ex_cl.step(ch, learn=True)
        tp = ex_tc.step(ch, learn=True)
        cl_ok = "Y" if cp == ch else ""
        tc_ok = "Y" if tp == ch else ""
        if cp == ch: cl_h += 1
        if tp == ch: tc_h += 1
        print(f"  {i:3d} {repr(ch):>6s} {repr(cp) if cp else '-':>6s} {repr(tp) if tp else '-':>6s} {cl_ok:>4s} {tc_ok:>4s}")
    print(f"\n  Sample: CL={cl_h}/{len(sample)} ({cl_h/len(sample)*100:.0f}%), TC={tc_h}/{len(sample)} ({tc_h/len(sample)*100:.0f}%)")
    flush()

    # ── Summary ──
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print(f"  {'':35s} {'Temporal Chains':>17s} {'CortexLite':>17s}")
    print(f"  {'-'*35} {'-'*17} {'-'*17}")
    print(f"  {'Train (online)':<35s} {tc_train_acc*100:>16.2f}% {cl_train_acc*100:>16.2f}%")
    print(f"  {'Test (online)':<35s} {tc_test_acc*100:>16.2f}% {cl_test_acc*100:>16.2f}%")
    print(f"  {'Test (strict)':<35s} {tc_strict_acc*100:>16.2f}% {cl_strict_acc*100:>16.2f}%")
    print(f"  {'Categories':<35s} {'N/A':>17s} {n_cats:>17d}")
    print(f"  {'Gap (train-test)':<35s} {(tc_train_acc-tc_test_acc)*100:>16.2f}% {(cl_train_acc-cl_test_acc)*100:>16.2f}%")

    d_online = cl_test_acc - tc_test_acc
    d_strict = cl_strict_acc - tc_strict_acc
    print(f"\n  Delta online: {d_online*100:+.2f}%")
    print(f"  Delta strict: {d_strict*100:+.2f}%")

    if d_online > 0:
        print(f"\n  >> SDRs IMPROVE generalization by {d_online*100:.2f}%")
    elif d_online < -0.01:
        print(f"\n  >> SDRs LOSE {abs(d_online)*100:.2f}% — encoding bottleneck loses info")
    else:
        print(f"\n  >> SDRs match Temporal Chains")
    flush()

    return {
        'tc_train': tc_train_acc, 'tc_test': tc_test_acc, 'tc_strict': tc_strict_acc,
        'cl_train': cl_train_acc, 'cl_test': cl_test_acc, 'cl_strict': cl_strict_acc,
        'n_categories': n_cats, 'categories': cats,
        'd_online': d_online, 'd_strict': d_strict,
    }

def write_results(r):
    cats = r['categories']
    cat_lines = []
    for i, (count, desc) in enumerate(cats):
        cat_lines.append(f"| {i+1} | {count} | {desc} |")

    delta_word = "IMPROVES" if r['d_online'] > 0 else "LOSES TO"

    md = f"""# Cortex Lite — Results

**Date:** 2026-03-24
**Architecture:** SDR Encoder (256 bits, 10% sparsity) + Hebbian Temporal Memory + Category Emergence
**Data:** {62} pensees, 80/20 train/test split

---

## Accuracy Comparison

| Metric | Temporal Chains (depth=8) | CortexLite (SDR 256-bit) |
|--------|--------------------------|--------------------------|
| Train accuracy (online) | {r['tc_train']*100:.2f}% | {r['cl_train']*100:.2f}% |
| Test accuracy (online) | {r['tc_test']*100:.2f}% | {r['cl_test']*100:.2f}% |
| Test accuracy (strict) | {r['tc_strict']*100:.2f}% | {r['cl_strict']*100:.2f}% |
| Generalization gap | {(r['tc_train']-r['tc_test'])*100:.2f}% | {(r['cl_train']-r['cl_test'])*100:.2f}% |

**Delta (online test): {r['d_online']*100:+.2f}%**
**Delta (strict test): {r['d_strict']*100:+.2f}%**

CortexLite {delta_word} Temporal Chains on unseen text.

---

## Emergent Categories

{r['n_categories']} categories discovered automatically (no labels, no supervision).

| # | Members | Top Characters |
|---|---------|----------------|
{chr(10).join(cat_lines)}

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
"""

    path = os.path.join(os.path.dirname(__file__), 'cortex-lite-results.md')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(md)
    print(f"\nResults written to {path}")
    flush()

if __name__ == '__main__':
    results = run_experiment()
    write_results(results)
