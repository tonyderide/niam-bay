"""
Cortex NB v3 -- The correct hybrid.

Architecture insight from v1/v2 failures:
  - Temporal Chains alone = 57% (fast, exact)
  - Cortex v1 SDR = 14% (decoder collapsed)
  - Cortex v2 SDR+TC = 24% (SDR corrupted the predictions)

The fix: TC as PRIMARY, SDR as FALLBACK only when TC has no match.
SDR is used ONLY for similarity lookup to find the nearest known context,
then TC's own prediction for that context is returned.

NO SDR math in the prediction path. SDR is a lookup index, not a predictor.
"""

import numpy as np
import os
import sys
import io
import glob
import time
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# --- CONFIG ---------------------------------------------------------------
SDR_SIZE = 256
SDR_ACTIVE = 26          # ~10% sparsity
TC_MAX_ORDER = 8          # try up to 8-char context
FUZZY_THRESHOLD = 0.3     # minimum SDR overlap to consider a match
TRAIN_RATIO = 0.8
SEED = 42

np.random.seed(SEED)


# --- SDR ENCODER ----------------------------------------------------------
class SDREncoder:
    """Hebbian encoder: chars that co-occur get similar SDRs."""

    def __init__(self):
        self.weights = {}
        self.lr = 0.01

    def _init_char(self, ch):
        if ch not in self.weights:
            self.weights[ch] = np.random.randn(SDR_SIZE).astype(np.float32)

    def encode_char(self, ch):
        """Single character -> SDR."""
        self._init_char(ch)
        w = self.weights[ch]
        sdr = np.zeros(SDR_SIZE, dtype=np.uint8)
        top = np.argpartition(w, -SDR_ACTIVE)[-SDR_ACTIVE:]
        sdr[top] = 1
        return sdr

    def encode_context(self, context_str):
        """
        Encode a context string into a single SDR fingerprint.
        Uses position-aware rotation to preserve ordering.
        """
        sdrs = [self.encode_char(ch) for ch in context_str]
        result = np.zeros(SDR_SIZE, dtype=np.uint8)
        for i, sdr in enumerate(sdrs):
            shift = (i * 37) % SDR_SIZE
            rotated = np.roll(sdr, shift)
            result |= rotated
        return result

    def learn_pair(self, ch1, ch2):
        """Hebbian: adjacent chars get slightly more similar."""
        self._init_char(ch1)
        self._init_char(ch2)
        if ch1 == ch2:
            return
        diff = self.weights[ch2] - self.weights[ch1]
        self.weights[ch1] += self.lr * diff
        self.weights[ch2] -= self.lr * diff


# --- TEMPORAL CHAINS (PRIMARY) -------------------------------------------
class TemporalChains:
    """Multi-order character-level exact matching."""

    def __init__(self, max_order=TC_MAX_ORDER):
        self.max_order = max_order
        self.chains = {i: defaultdict(lambda: defaultdict(int))
                       for i in range(1, max_order + 1)}

    def learn(self, context, next_char):
        """Learn at all orders up to max_order."""
        for order in range(1, min(self.max_order, len(context)) + 1):
            key = tuple(context[-order:])
            self.chains[order][key][next_char] += 1

    def predict(self, context):
        """
        Backoff prediction: try highest order first, fall back to lower.
        Returns (predicted_char, order_used) or (None, 0) if no match.
        """
        for order in range(min(self.max_order, len(context)), 0, -1):
            key = tuple(context[-order:])
            if key in self.chains[order]:
                counts = self.chains[order][key]
                best = max(counts.items(), key=lambda x: x[1])
                return best[0], order
        return None, 0

    def total_contexts(self):
        return sum(len(self.chains[o]) for o in self.chains)


# --- SDR INDEX (SECONDARY - SIMILARITY LOOKUP ONLY) ----------------------
class SDRIndex:
    """
    Maps context_string -> SDR fingerprint.
    Used ONLY to find the nearest known context when TC has no exact match.
    Does NOT predict characters. Returns a known context string, which
    is then fed back to TC for its prediction.
    """

    def __init__(self, encoder):
        self.encoder = encoder
        # context_str -> sdr_fingerprint
        self.index = {}
        # For speed: store SDRs as a matrix once built
        self._keys = []
        self._matrix = None

    def add(self, context_str, sdr=None):
        if context_str not in self.index:
            if sdr is None:
                sdr = self.encoder.encode_context(context_str)
            self.index[context_str] = sdr

    def build_matrix(self):
        """Build numpy matrix for fast batch overlap computation."""
        self._keys = list(self.index.keys())
        if self._keys:
            self._matrix = np.array([self.index[k] for k in self._keys],
                                     dtype=np.float32)
        else:
            self._matrix = np.zeros((0, SDR_SIZE), dtype=np.float32)

    def find_nearest(self, query_sdr, threshold=FUZZY_THRESHOLD):
        """
        Find the most similar stored context to query_sdr.
        Returns (best_context_str, overlap_score) or (None, 0).
        """
        if self._matrix is None or len(self._keys) == 0:
            return None, 0.0

        q = query_sdr.astype(np.float32)
        q_sum = max(q.sum(), 1.0)

        # Vectorized dot product
        dots = self._matrix @ q
        overlaps = dots / q_sum

        best_idx = np.argmax(overlaps)
        best_overlap = overlaps[best_idx]

        if best_overlap >= threshold:
            return self._keys[best_idx], float(best_overlap)
        return None, 0.0


# --- CORTEX V3 -----------------------------------------------------------
class CortexV3:
    """
    The correct hybrid:
    1. Temporal Chains (primary) -- exact context match
    2. SDR Index (secondary) -- similarity lookup when TC fails
    3. TC prediction on the nearest context found by SDR
    """

    def __init__(self):
        self.encoder = SDREncoder()
        self.tc = TemporalChains()
        self.sdr_index = None  # built after training
        self._trained_encoder = False

    def train(self, text, verbose=True):
        n = len(text)
        if verbose:
            print(f"Training Cortex v3 on {n} chars...")

        # Phase 1: Hebbian learning on adjacent pairs
        if verbose:
            print("  Phase 1: Hebbian encoder learning...")
        t0 = time.time()
        for i in range(n - 1):
            self.encoder.learn_pair(text[i], text[i + 1])
        if verbose:
            print(f"    {time.time() - t0:.1f}s, {len(self.encoder.weights)} unique chars")

        # Phase 2: Train Temporal Chains at all orders
        if verbose:
            print("  Phase 2: Temporal Chains (multi-order)...")
        t0 = time.time()
        for i in range(1, n):
            context = list(text[max(0, i - self.tc.max_order):i])
            self.tc.learn(context, text[i])
        if verbose:
            n_ctx = self.tc.total_contexts()
            print(f"    {time.time() - t0:.1f}s, {n_ctx} unique contexts across all orders")

        # Phase 3: Build SDR index for all TC contexts
        # We index contexts at order 3 (trigrams) since that's where
        # fuzzy matching is most useful -- higher orders rarely collide
        if verbose:
            print("  Phase 3: Building SDR index...")
        t0 = time.time()
        self.sdr_index = SDRIndex(self.encoder)

        # Index trigram contexts (order 3) -- these are the bread and butter
        for order in [3, 4, 5]:
            if order in self.tc.chains:
                for key_tuple in self.tc.chains[order]:
                    ctx_str = ''.join(key_tuple)
                    self.sdr_index.add(ctx_str)

        self.sdr_index.build_matrix()
        if verbose:
            print(f"    {time.time() - t0:.1f}s, {len(self.sdr_index.index)} contexts indexed")
        self._trained_encoder = True

    def predict(self, context):
        """
        1. Try TC exact match (highest order first, backoff)
        2. If no match: encode context as SDR, find nearest known context
        3. Use TC's prediction for that nearest context
        4. Last resort: most common char fallback
        """
        ctx_list = list(context)

        # Step 1: TC exact match
        pred, order = self.tc.predict(ctx_list)
        if pred is not None:
            return pred, "exact", order

        # Step 2: SDR fuzzy lookup
        if self.sdr_index is not None:
            # Try different context lengths for SDR matching
            for ctx_len in [5, 4, 3]:
                if len(context) >= ctx_len:
                    ctx_str = context[-ctx_len:]
                    query_sdr = self.encoder.encode_context(ctx_str)
                    nearest_ctx, overlap = self.sdr_index.find_nearest(query_sdr)
                    if nearest_ctx is not None:
                        # Use TC's prediction for this similar context
                        tc_pred, tc_order = self.tc.predict(list(nearest_ctx))
                        if tc_pred is not None:
                            return tc_pred, "fuzzy", ctx_len

        # Step 3: Fallback
        return ' ', "fallback", 0


# --- LOAD DATA ------------------------------------------------------------
def load_pensees():
    pattern = "C:/niam-bay/docs/pensees/*.md"
    files = sorted(glob.glob(pattern))
    text = ""
    for f in files:
        with open(f, 'r', encoding='utf-8') as fh:
            text += fh.read() + "\n"
    return text


# --- MAIN -----------------------------------------------------------------
def main():
    print("=" * 70)
    print("  CORTEX NB v3 -- The Correct Hybrid")
    print("  TC primary + SDR fallback (similarity lookup only)")
    print("=" * 70)
    sys.stdout.flush()

    text = load_pensees()
    print(f"\nLoaded {len(text)} chars from pensees")

    split = int(len(text) * TRAIN_RATIO)
    train_text = text[:split]
    test_text = text[split:]
    print(f"Train: {len(train_text)} chars, Test: {len(test_text)} chars")
    sys.stdout.flush()

    # --- Train Cortex v3 ---
    cortex = CortexV3()
    t0 = time.time()
    cortex.train(train_text)
    train_time = time.time() - t0
    print(f"Total train time: {train_time:.1f}s")
    sys.stdout.flush()

    # --- TC-only baseline (same multi-order) for fair comparison ---
    print("\n" + "-" * 70)
    print("Training TC-only baseline (same max_order=8)...")
    tc_baseline = TemporalChains(max_order=TC_MAX_ORDER)
    t0 = time.time()
    for i in range(1, len(train_text)):
        context = list(train_text[max(0, i - tc_baseline.max_order):i])
        tc_baseline.learn(context, train_text[i])
    tc_train_time = time.time() - t0
    print(f"  {tc_train_time:.1f}s, {tc_baseline.total_contexts()} unique contexts")
    sys.stdout.flush()

    # --- Test ---
    print("\n" + "-" * 70)
    test_n = len(test_text) - 1
    print(f"Testing on {test_n} positions...")
    sys.stdout.flush()

    # Cortex v3 test
    t0 = time.time()
    v3_correct = 0
    exact_count = 0
    exact_correct = 0
    fuzzy_count = 0
    fuzzy_correct = 0
    fallback_count = 0
    fallback_correct = 0
    fuzzy_overlaps = []

    for i in range(1, len(test_text)):
        ctx_start = max(0, i - TC_MAX_ORDER)
        context = test_text[ctx_start:i]
        actual = test_text[i]

        pred, match_type, meta = cortex.predict(context)
        correct = (pred == actual)

        if match_type == "exact":
            exact_count += 1
            if correct:
                exact_correct += 1
                v3_correct += 1
        elif match_type == "fuzzy":
            fuzzy_count += 1
            if correct:
                fuzzy_correct += 1
                v3_correct += 1
        else:
            fallback_count += 1
            if correct:
                fallback_correct += 1
                v3_correct += 1

    v3_test_time = time.time() - t0
    v3_acc = v3_correct / test_n * 100

    # TC-only baseline test
    t0 = time.time()
    tc_correct = 0
    tc_no_match = 0
    for i in range(1, len(test_text)):
        ctx_start = max(0, i - TC_MAX_ORDER)
        context = list(test_text[ctx_start:i])
        actual = test_text[i]

        pred, order = tc_baseline.predict(context)
        if pred is None:
            tc_no_match += 1
        elif pred == actual:
            tc_correct += 1

    tc_test_time = time.time() - t0
    tc_acc = tc_correct / test_n * 100
    tc_no_match_pct = tc_no_match / test_n * 100

    # --- Results ---
    print("\n" + "=" * 70)
    print("  RESULTS")
    print("=" * 70)

    print(f"\n  TC-only baseline:")
    print(f"    Accuracy:    {tc_acc:.1f}% ({tc_correct}/{test_n})")
    print(f"    No match:    {tc_no_match_pct:.1f}% ({tc_no_match}/{test_n})")
    print(f"    Test time:   {tc_test_time:.1f}s")
    print(f"    Train time:  {tc_train_time:.1f}s")

    print(f"\n  Cortex v3 (TC + SDR fallback):")
    print(f"    Overall:     {v3_acc:.1f}% ({v3_correct}/{test_n})")
    print(f"    Exact:       {exact_count} predictions, {exact_correct} correct = {exact_correct/max(exact_count,1)*100:.1f}%")
    print(f"    Fuzzy:       {fuzzy_count} predictions, {fuzzy_correct} correct = {fuzzy_correct/max(fuzzy_count,1)*100:.1f}%")
    print(f"    Fallback:    {fallback_count} predictions, {fallback_correct} correct")
    print(f"    Test time:   {v3_test_time:.1f}s")
    print(f"    Train time:  {train_time:.1f}s")

    delta = v3_acc - tc_acc
    print(f"\n  DELTA: {delta:+.1f}%")
    if delta > 0:
        print(f"  >> v3 WINS by {delta:.1f}% -- SDR fallback adds value")
    elif delta < -0.5:
        print(f"  >> TC still wins -- SDR fallback hurts or is neutral")
    else:
        print(f"  >> Roughly tied")

    # Fuzzy accuracy analysis
    if fuzzy_count > 0:
        fuzzy_acc = fuzzy_correct / fuzzy_count * 100
        print(f"\n  FUZZY ANALYSIS:")
        print(f"    Fuzzy accuracy: {fuzzy_acc:.1f}%")
        print(f"    TC had no match for these {fuzzy_count} cases")
        print(f"    Without SDR, these would all be wrong (fallback to space)")
        fuzzy_gain = fuzzy_correct  # these are NEW correct predictions
        print(f"    Fuzzy contributed {fuzzy_gain} new correct predictions")
        print(f"    That's {fuzzy_gain/test_n*100:.2f}% absolute gain")

        if fuzzy_acc > 40:
            print(f"\n  VERDICT: SDR fuzzy matching WORKS ({fuzzy_acc:.0f}% > 40% threshold)")
        elif fuzzy_acc > 20:
            print(f"\n  VERDICT: SDR fuzzy matching is MARGINAL ({fuzzy_acc:.0f}%)")
        else:
            print(f"\n  VERDICT: SDR fuzzy matching is USELESS ({fuzzy_acc:.0f}% < 20%)")
    sys.stdout.flush()

    # --- Example predictions ---
    print("\n" + "-" * 70)
    print("  EXAMPLE PREDICTIONS (first 30 test chars)")
    print("-" * 70)
    print(f"  {'#':>3s} {'ctx':>10s} {'actual':>7s} {'v3':>5s} {'type':>7s} {'TC':>5s} {'v3?':>4s} {'TC?':>4s}")
    shown = 0
    for i in range(1, min(200, len(test_text))):
        ctx_start = max(0, i - TC_MAX_ORDER)
        context = test_text[ctx_start:i]
        actual = test_text[i]
        v3_pred, v3_type, _ = cortex.predict(context)
        tc_pred, _ = tc_baseline.predict(list(context))
        if tc_pred is None:
            tc_pred = ' '

        v3_ok = "Y" if v3_pred == actual else ""
        tc_ok = "Y" if tc_pred == actual else ""

        # Show interesting cases (fuzzy, or disagreements)
        if v3_type == "fuzzy" or v3_ok != tc_ok or shown < 30:
            ctx_disp = repr(context[-5:]) if len(context) >= 5 else repr(context)
            print(f"  {i:3d} {ctx_disp:>10s} {repr(actual):>7s} {repr(v3_pred):>5s} {v3_type:>7s} {repr(tc_pred):>5s} {v3_ok:>4s} {tc_ok:>4s}")
            shown += 1
        if shown >= 50:
            break
    sys.stdout.flush()

    # --- Write results ---
    results_path = "C:/niam-bay/ai-lab/cortex-v3-results.md"
    with open(results_path, 'w', encoding='utf-8') as f:
        f.write("# Cortex NB v3 -- Results\n\n")
        f.write(f"**Date**: {time.strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write("## Architecture\n\n")
        f.write("The correct hybrid, identified from v1/v2 failure analysis:\n\n")
        f.write("1. **Temporal Chains** (PRIMARY) -- multi-order exact matching (1-8 chars)\n")
        f.write("2. **SDR Encoder** (SECONDARY) -- Hebbian learned, 256-bit sparse\n")
        f.write("3. **SDR Index** -- similarity lookup ONLY, never predicts directly\n\n")
        f.write("**Prediction flow:**\n")
        f.write("1. Get context (last N chars)\n")
        f.write("2. Try TC exact match (highest order first, backoff) -> if found, use it\n")
        f.write("3. If no TC match: encode context as SDR -> find most similar stored context\n")
        f.write("4. Use TC's prediction for that nearest context\n")
        f.write("5. Last resort: space character fallback\n\n")
        f.write("**Key insight from v2:** DON'T use SDR for prediction math.\n")
        f.write("Use it ONLY as a similarity index to bridge unknown contexts to known ones.\n\n")

        f.write("## Config\n\n")
        f.write(f"- SDR: {SDR_SIZE} bits, {SDR_ACTIVE} active (~10%)\n")
        f.write(f"- TC max order: {TC_MAX_ORDER}\n")
        f.write(f"- Fuzzy threshold: {FUZZY_THRESHOLD}\n")
        f.write(f"- Train/test split: {TRAIN_RATIO*100:.0f}/{(1-TRAIN_RATIO)*100:.0f}\n\n")

        f.write("## Data\n\n")
        f.write(f"- Total: {len(text)} chars from pensees\n")
        f.write(f"- Train: {len(train_text)} chars\n")
        f.write(f"- Test: {len(test_text)} chars\n")
        f.write(f"- Test positions: {test_n}\n\n")

        f.write("## Results\n\n")
        f.write("| Metric | TC-only | Cortex v3 |\n")
        f.write("|--------|---------|----------|\n")
        f.write(f"| Accuracy | {tc_acc:.1f}% | {v3_acc:.1f}% |\n")
        f.write(f"| Train time | {tc_train_time:.1f}s | {train_time:.1f}s |\n")
        f.write(f"| Test time | {tc_test_time:.1f}s | {v3_test_time:.1f}s |\n")
        f.write(f"| Contexts | {tc_baseline.total_contexts()} | {tc_baseline.total_contexts()} + {len(cortex.sdr_index.index)} SDR |\n\n")
        f.write(f"**Delta: {delta:+.1f}%**\n\n")

        f.write("## Breakdown\n\n")
        f.write(f"| Match Type | Count | Correct | Accuracy |\n")
        f.write(f"|------------|-------|---------|----------|\n")
        f.write(f"| Exact (TC) | {exact_count} | {exact_correct} | {exact_correct/max(exact_count,1)*100:.1f}% |\n")
        f.write(f"| Fuzzy (SDR->TC) | {fuzzy_count} | {fuzzy_correct} | {fuzzy_correct/max(fuzzy_count,1)*100:.1f}% |\n")
        f.write(f"| Fallback | {fallback_count} | {fallback_correct} | - |\n\n")

        f.write(f"TC had NO match for {tc_no_match} cases ({tc_no_match_pct:.1f}% of test).\n")
        if fuzzy_count > 0:
            fuzzy_acc = fuzzy_correct / fuzzy_count * 100
            f.write(f"SDR caught {fuzzy_count} of those and predicted at {fuzzy_acc:.1f}% accuracy.\n")
            f.write(f"That means {fuzzy_correct} NEW correct predictions that TC alone missed.\n\n")
        else:
            f.write(f"SDR caught 0 of those (all fell to fallback).\n\n")

        f.write("## Historical Comparison\n\n")
        f.write("| Version | Architecture | Accuracy | Notes |\n")
        f.write("|---------|-------------|----------|-------|\n")
        f.write("| TC alone (order 3) | Exact trigram matching | ~46% | Session 24 baseline |\n")
        f.write("| TC alone (order 8) | Multi-order exact | ~57% | With backoff |\n")
        f.write(f"| Cortex v1 (SDR) | SDR encoder + decoder | 14% | Decoder collapsed |\n")
        f.write(f"| Cortex v2 (SDR+TC) | SDR fingerprints | 24% | SDR corrupted predictions |\n")
        f.write(f"| **Cortex v3** | **TC + SDR fallback** | **{v3_acc:.1f}%** | **This experiment** |\n\n")

        f.write("## Honest Analysis\n\n")
        if delta > 2:
            f.write(f"v3 beats TC-only by {delta:.1f}%. The SDR fallback genuinely helps.\n")
            f.write("The fuzzy lookup finds similar-enough contexts to make useful predictions\n")
            f.write("where TC had nothing. This validates the hybrid architecture.\n\n")
            f.write("The gain comes entirely from the fuzzy matches -- exact match accuracy\n")
            f.write("is identical to TC-only (same algorithm). The SDR's job is narrow but real:\n")
            f.write("bridge the gap between unseen contexts and known ones.\n")
        elif delta > 0:
            f.write(f"v3 edges TC-only by {delta:.1f}%. Small but real gain.\n")
            f.write("The SDR fallback helps on a few cases, but most of TC's misses are\n")
            f.write("genuinely ambiguous (multiple valid next chars). SDR similarity can't\n")
            f.write("resolve ambiguity -- it can only redirect to a known context.\n")
        elif delta > -0.5:
            f.write(f"Roughly tied (delta {delta:+.1f}%). SDR fallback is neutral.\n")
            f.write("Two possible explanations:\n")
            f.write("1. TC's no-match cases are too rare (TC with order-8 covers most contexts)\n")
            f.write("2. SDR similarity doesn't find the RIGHT similar context -- the Hebbian\n")
            f.write("   encoding maps too many distinct contexts to similar SDRs\n")
        else:
            f.write(f"TC still wins by {abs(delta):.1f}%. SDR fallback actively hurts.\n")
            f.write("The SDR similarity lookup returns contexts that LOOK similar in SDR space\n")
            f.write("but have DIFFERENT next-character distributions. This is worse than\n")
            f.write("the fallback space character.\n")

        if fuzzy_count > 0:
            fuzzy_acc = fuzzy_correct / fuzzy_count * 100
            f.write(f"\n### Fuzzy Match Verdict\n\n")
            if fuzzy_acc > 40:
                f.write(f"Fuzzy accuracy = {fuzzy_acc:.1f}% (ABOVE 40% threshold) -- SDR IS useful.\n")
            elif fuzzy_acc > 20:
                f.write(f"Fuzzy accuracy = {fuzzy_acc:.1f}% (below 40%, above 20%) -- MARGINAL.\n")
            else:
                f.write(f"Fuzzy accuracy = {fuzzy_acc:.1f}% (below 20%) -- SDR is USELESS for this.\n")

        f.write("\n### What This Means\n\n")
        f.write("The v1->v2->v3 progression tested a clear hypothesis:\n")
        f.write("can SDR representations add value to character prediction?\n\n")
        f.write("- v1: SDR as sole predictor -- NO (14%)\n")
        f.write("- v2: SDR as primary with TC features -- NO (24%)\n")
        f.write(f"- v3: SDR as fallback for TC misses -- {v3_acc:.1f}% (delta {delta:+.1f}%)\n\n")
        if delta > 0:
            f.write("SDR has a narrow but legitimate role: similarity-based context bridging.\n")
            f.write("It's not a predictor. It's an index. And that's exactly how HTM theory\n")
            f.write("suggests it should work -- SDRs represent, they don't decide.\n")
        else:
            f.write("For character-level prediction on this corpus, TC is king.\n")
            f.write("SDR's generalization doesn't help because:\n")
            f.write("- The corpus is small enough that TC covers most contexts\n")
            f.write("- Character-level prediction is too fine-grained for SDR similarity\n")
            f.write("- SDR might help at word or sentence level prediction instead\n")

    print(f"\nResults written to {results_path}")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
