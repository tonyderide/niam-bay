"""
Cortex NB v2 -- Brain-inspired AI that learns from raw text without supervision.

Architecture:
  Layer 1: SDR Encoder (Hebbian learning -> emergent categories)
  Layer 2: Temporal Chains on SDR patterns (exact + fuzzy matching)
  Layer 3: Decoder (dot-product similarity)

Key fix from v2.0: use CONCATENATED SDRs for context (not OR-union),
and use per-character SDR identity for prediction targets.
"""

import numpy as np
import os
import glob
import time
from collections import defaultdict

# --- CONFIG ---------------------------------------------------------------
SDR_SIZE = 256          # total bits per character SDR
SDR_ACTIVE = 26         # ~10% active bits
CONTEXT_WINDOW = 3      # chars of context
HEBBIAN_LR = 0.01       # reduced from 0.05 -- too aggressive merges everything
OVERLAP_THRESHOLD = 0.4 # fuzzy match threshold
TOP_K_MATCHES = 5       # top K fuzzy matches for voting
TRAIN_RATIO = 0.8
SEED = 42

np.random.seed(SEED)


# --- LAYER 1: SDR ENCODER ------------------------------------------------
class SDREncoder:
    """Hebbian encoder: chars that co-occur get similar SDRs."""

    def __init__(self, sdr_size=SDR_SIZE, n_active=SDR_ACTIVE):
        self.sdr_size = sdr_size
        self.n_active = n_active
        self.weights = {}   # char -> float vector
        self._cache = {}    # char -> (sdr, weights_hash)

    def _init_char(self, ch):
        if ch not in self.weights:
            self.weights[ch] = np.random.randn(self.sdr_size).astype(np.float32)

    def encode(self, ch):
        """Encode a single character to SDR."""
        self._init_char(ch)
        # Simple cache invalidation: hash a few weight values
        w = self.weights[ch]
        h = (w[0], w[50], w[100])
        if ch in self._cache and self._cache[ch][1] == h:
            return self._cache[ch][0]
        sdr = np.zeros(self.sdr_size, dtype=np.uint8)
        top_indices = np.argpartition(w, -self.n_active)[-self.n_active:]
        sdr[top_indices] = 1
        self._cache[ch] = (sdr, h)
        return sdr

    def learn_pair(self, ch1, ch2):
        """Hebbian: adjacent chars get slightly more similar weights."""
        self._init_char(ch1)
        self._init_char(ch2)
        if ch1 == ch2:
            return
        diff = self.weights[ch2] - self.weights[ch1]
        self.weights[ch1] += HEBBIAN_LR * diff
        self.weights[ch2] -= HEBBIAN_LR * diff

    def get_categories(self, top_n=15):
        """Find groups of characters with similar SDRs."""
        chars = list(self.weights.keys())
        if len(chars) < 2:
            return []
        sdrs = {ch: self.encode(ch) for ch in chars}

        # Compute overlap matrix
        categories = []
        used = set()
        # Sort by frequency-ish: try common chars first
        for ch in chars:
            if ch in used:
                continue
            cluster = [ch]
            used.add(ch)
            for ch2 in chars:
                if ch2 in used:
                    continue
                ov = _overlap(sdrs[ch], sdrs[ch2])
                if ov > 0.55:
                    cluster.append(ch2)
                    used.add(ch2)
            if len(cluster) > 1:
                categories.append(cluster)
        categories.sort(key=len, reverse=True)
        return categories[:top_n]


# --- UTILITY FUNCTIONS ----------------------------------------------------
def _overlap(a, b):
    """Overlap = dot(a,b) / max(sum(a), sum(b))."""
    dot = int(np.dot(a.astype(np.int32), b.astype(np.int32)))
    denom = max(int(a.sum()), int(b.sum()), 1)
    return dot / denom


def _context_fingerprint(char_sdrs):
    """
    Create a context fingerprint from a list of per-position SDRs.
    Instead of OR (which loses position info), we use position-shifted hashing:
    for position i, we rotate the SDR by i*shift bits, then OR together.
    This preserves ordering information.
    """
    size = char_sdrs[0].shape[0]
    result = np.zeros(size, dtype=np.uint8)
    for i, sdr in enumerate(char_sdrs):
        shift = (i * 37) % size  # different shift per position
        rotated = np.roll(sdr, shift)
        result |= rotated
    return result


def _sdr_key(sdr):
    """Convert SDR to hashable tuple of active bit indices."""
    return tuple(np.where(sdr)[0])


# --- LAYER 2: TEMPORAL MEMORY ON SDR PATTERNS ----------------------------
class TemporalMemory:
    """
    Stores transitions: context_fingerprint -> predicted character.
    Direct char prediction (not SDR->SDR) avoids decoder collapse.
    Fuzzy matching via SDR overlap gives generalization.
    """

    def __init__(self):
        # context_sdr_key -> {next_char: count}
        self.transitions = defaultdict(lambda: defaultdict(int))
        # context_sdr_key -> context_sdr_array (for fuzzy matching)
        self.stored_sdrs = {}

    def learn(self, context_sdr, next_char):
        key = _sdr_key(context_sdr)
        self.transitions[key][next_char] += 1
        if key not in self.stored_sdrs:
            self.stored_sdrs[key] = context_sdr.copy()

    def predict_exact(self, context_sdr):
        """Exact SDR match -> most common next char."""
        key = _sdr_key(context_sdr)
        if key in self.transitions:
            nexts = self.transitions[key]
            return max(nexts.items(), key=lambda x: x[1])[0], 'exact'
        return None, None

    def predict_fuzzy(self, context_sdr, threshold=OVERLAP_THRESHOLD, top_k=TOP_K_MATCHES):
        """
        Find stored context SDRs similar to input.
        Weighted vote over their predictions.
        """
        if not self.stored_sdrs:
            return None, None

        # Find similar stored patterns
        matches = []
        for stored_key, stored_sdr in self.stored_sdrs.items():
            if stored_key not in self.transitions:
                continue
            ov = _overlap(context_sdr, stored_sdr)
            if ov >= threshold:
                matches.append((stored_key, ov))

        if not matches:
            return None, None

        matches.sort(key=lambda x: x[1], reverse=True)
        matches = matches[:top_k]

        # Weighted vote
        vote = defaultdict(float)
        for stored_key, ov in matches:
            for next_char, count in self.transitions[stored_key].items():
                vote[next_char] += ov * count

        if not vote:
            return None, None

        best_char = max(vote.items(), key=lambda x: x[1])[0]
        return best_char, 'fuzzy'


# --- CORTEX V2 -----------------------------------------------------------
class CortexV2:
    def __init__(self):
        self.encoder = SDREncoder()
        self.memory = TemporalMemory()

    def train(self, text, verbose=True):
        n = len(text)
        if verbose:
            print(f"Training Cortex v2 on {n} chars...")

        # Phase 1: Hebbian learning -- just adjacent pairs
        if verbose:
            print("  Phase 1: Hebbian encoder...")
        t0 = time.time()
        for i in range(n - 1):
            self.encoder.learn_pair(text[i], text[i + 1])
        # Clear cache after all learning
        self.encoder._cache.clear()
        if verbose:
            print(f"    {time.time() - t0:.1f}s, {len(self.encoder.weights)} unique chars")

        # Phase 2: Build temporal memory
        if verbose:
            print("  Phase 2: Temporal memory on SDR fingerprints...")
        t0 = time.time()
        for i in range(CONTEXT_WINDOW, n):
            context_chars = text[i - CONTEXT_WINDOW:i]
            char_sdrs = [self.encoder.encode(ch) for ch in context_chars]
            ctx_fp = _context_fingerprint(char_sdrs)
            self.memory.learn(ctx_fp, text[i])
        n_patterns = len(self.memory.transitions)
        if verbose:
            print(f"    {time.time() - t0:.1f}s, {n_patterns} unique context patterns")

    def predict(self, context_chars):
        """Predict next char. Returns (char, match_type)."""
        char_sdrs = [self.encoder.encode(ch) for ch in context_chars[-CONTEXT_WINDOW:]]
        ctx_fp = _context_fingerprint(char_sdrs)

        # Try exact first
        pred, mtype = self.memory.predict_exact(ctx_fp)
        if pred is not None:
            return pred, mtype

        # Try fuzzy
        pred, mtype = self.memory.predict_fuzzy(ctx_fp)
        if pred is not None:
            return pred, mtype

        return ' ', 'fail'


# --- TEMPORAL CHAINS BASELINE --------------------------------------------
class TemporalChains:
    def __init__(self, context_size=CONTEXT_WINDOW):
        self.context_size = context_size
        self.chains = defaultdict(lambda: defaultdict(int))

    def learn(self, context, next_char):
        key = tuple(context)
        self.chains[key][next_char] += 1

    def predict(self, context):
        key = tuple(context[-self.context_size:])
        if key in self.chains:
            return max(self.chains[key].items(), key=lambda x: x[1])[0]
        for length in range(self.context_size - 1, 0, -1):
            short_key = tuple(context[-length:])
            if short_key in self.chains:
                return max(self.chains[short_key].items(), key=lambda x: x[1])[0]
        return ' '


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
    print("=" * 60)
    print("CORTEX NB v2 -- Brain-inspired AI")
    print("SDR Encoder + Temporal Memory (position-aware fingerprints)")
    print("=" * 60)

    text = load_pensees()
    print(f"\nLoaded {len(text)} chars from pensees")

    split = int(len(text) * TRAIN_RATIO)
    train_text = text[:split]
    test_text = text[split:]
    print(f"Train: {len(train_text)} chars, Test: {len(test_text)} chars")

    # --- Train Temporal Chains baseline ---
    print("\n" + "-" * 50)
    print("Training Temporal Chains baseline...")
    tc = TemporalChains(CONTEXT_WINDOW)
    t0 = time.time()
    for i in range(CONTEXT_WINDOW, len(train_text)):
        context = train_text[i - CONTEXT_WINDOW:i]
        tc.learn(list(context), train_text[i])
    tc_train_time = time.time() - t0
    print(f"  {tc_train_time:.1f}s, {len(tc.chains)} unique contexts")

    # --- Train Cortex v2 ---
    print("\n" + "-" * 50)
    cortex = CortexV2()
    t0 = time.time()
    cortex.train(train_text)
    cortex_train_time = time.time() - t0

    # --- Test ---
    print("\n" + "-" * 50)
    test_n = len(test_text) - CONTEXT_WINDOW
    print(f"Testing on {test_n} positions...")

    # Full TC test
    t0 = time.time()
    tc_correct = 0
    for i in range(CONTEXT_WINDOW, len(test_text)):
        pred = tc.predict(list(test_text[i - CONTEXT_WINDOW:i]))
        if pred == test_text[i]:
            tc_correct += 1
    tc_test_time = time.time() - t0
    tc_acc = tc_correct / test_n * 100

    # Sampled Cortex v2 test (fuzzy matching is slow)
    step = max(1, test_n // 5000)
    t0 = time.time()
    cortex_correct = 0
    exact_count = 0
    fuzzy_count = 0
    fail_count = 0
    exact_correct = 0
    fuzzy_correct = 0
    actual_tested = 0

    for i in range(CONTEXT_WINDOW, len(test_text), step):
        context = test_text[i - CONTEXT_WINDOW:i]
        actual = test_text[i]
        pred, mtype = cortex.predict(list(context))
        actual_tested += 1
        correct = (pred == actual)

        if mtype == 'exact':
            exact_count += 1
            if correct:
                exact_correct += 1
                cortex_correct += 1
        elif mtype == 'fuzzy':
            fuzzy_count += 1
            if correct:
                fuzzy_correct += 1
                cortex_correct += 1
        else:
            fail_count += 1
            if correct:
                cortex_correct += 1

    cortex_test_time = time.time() - t0
    cortex_acc = cortex_correct / actual_tested * 100 if actual_tested else 0

    # TC on same sample for fair comparison
    tc_sampled_correct = 0
    tc_sampled_total = 0
    for i in range(CONTEXT_WINDOW, len(test_text), step):
        pred = tc.predict(list(test_text[i - CONTEXT_WINDOW:i]))
        tc_sampled_total += 1
        if pred == test_text[i]:
            tc_sampled_correct += 1
    tc_sampled_acc = tc_sampled_correct / tc_sampled_total * 100 if tc_sampled_total else 0

    # --- Categories ---
    print("\n" + "-" * 50)
    print("Emergent categories:")
    categories = cortex.encoder.get_categories(top_n=15)
    cat_strs = []
    for i, cat in enumerate(categories):
        display = []
        for c in cat:
            if c == ' ':
                display.append('SPC')
            elif c == '\n':
                display.append('NL')
            elif c == '\t':
                display.append('TAB')
            else:
                display.append(c)
        s = f"  {i+1}. [{', '.join(display)}]"
        print(s)
        cat_strs.append(s)

    # --- Example predictions ---
    print("\n" + "-" * 50)
    print("Example predictions (context -> predicted | actual):")
    examples = []
    test_positions = list(range(CONTEXT_WINDOW + 100, min(len(test_text), CONTEXT_WINDOW + 600)))
    np.random.seed(123)
    np.random.shuffle(test_positions)
    shown = 0
    for i in test_positions:
        if shown >= 20:
            break
        context = test_text[i - CONTEXT_WINDOW:i]
        actual = test_text[i]
        pred_c, mtype = cortex.predict(list(context))
        pred_t = tc.predict(list(context))
        mc = "OK" if pred_c == actual else "  "
        mt = "OK" if pred_t == actual else "  "
        ctx_display = context.replace('\n', '\\n')
        act_display = actual.replace('\n', '\\n')
        pc_display = pred_c.replace('\n', '\\n')
        pt_display = pred_t.replace('\n', '\\n')
        line = f"  '{ctx_display}' -> Cortex:'{pc_display}' {mc} ({mtype:5s}) | TC:'{pt_display}' {mt} | actual:'{act_display}'"
        print(line)
        examples.append(line)
        shown += 1

    # --- Summary ---
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"\nTemporal Chains:")
    print(f"  Full accuracy:     {tc_acc:.1f}% ({tc_correct}/{test_n})")
    print(f"  Sampled accuracy:  {tc_sampled_acc:.1f}% ({tc_sampled_correct}/{tc_sampled_total})")
    print(f"  Train time:        {tc_train_time:.1f}s")
    print(f"\nCortex v2:")
    print(f"  Sampled accuracy:  {cortex_acc:.1f}% ({cortex_correct}/{actual_tested})")
    print(f"  Exact:  {exact_count} ({exact_correct} correct = {exact_correct/max(exact_count,1)*100:.1f}%)")
    print(f"  Fuzzy:  {fuzzy_count} ({fuzzy_correct} correct = {fuzzy_correct/max(fuzzy_count,1)*100:.1f}%)")
    print(f"  Fail:   {fail_count}")
    print(f"  Train time:        {cortex_train_time:.1f}s")
    print(f"  Test time:         {cortex_test_time:.1f}s")
    print(f"  Patterns stored:   {len(cortex.memory.transitions)}")
    print(f"  Categories:        {len(categories)}")

    delta = cortex_acc - tc_sampled_acc
    winner = "Cortex v2" if delta > 0 else "Temporal Chains"
    print(f"\n  DELTA: {delta:+.1f}% -- Winner: {winner}")

    # --- Write results ---
    results_path = "C:/niam-bay/ai-lab/cortex-v2-results.md"
    with open(results_path, 'w', encoding='utf-8') as f:
        f.write("# Cortex NB v2 -- Results\n\n")
        f.write(f"**Date**: {time.strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write("## Architecture\n\n")
        f.write("- **Layer 1**: SDR Encoder (Hebbian, 256 bits, ~10% active)\n")
        f.write("- **Layer 2**: Temporal Memory on position-aware SDR fingerprints\n")
        f.write("- **Layer 3**: Direct char prediction (no SDR decoder -- avoids collapse)\n")
        f.write(f"- Context window: {CONTEXT_WINDOW} chars\n")
        f.write(f"- Fuzzy threshold: {OVERLAP_THRESHOLD}\n")
        f.write(f"- Hebbian LR: {HEBBIAN_LR}\n\n")
        f.write("## Data\n\n")
        f.write(f"- Total: {len(text)} chars from pensees\n")
        f.write(f"- Train: {len(train_text)} chars ({TRAIN_RATIO*100:.0f}%)\n")
        f.write(f"- Test: {len(test_text)} chars ({(1-TRAIN_RATIO)*100:.0f}%)\n")
        f.write(f"- Sampled test: {actual_tested} predictions\n\n")
        f.write("## Results\n\n")
        f.write("| Metric | Temporal Chains | Cortex v2 |\n")
        f.write("|--------|----------------|-----------|\n")
        f.write(f"| Accuracy (sampled) | {tc_sampled_acc:.1f}% | {cortex_acc:.1f}% |\n")
        f.write(f"| Train time | {tc_train_time:.1f}s | {cortex_train_time:.1f}s |\n")
        f.write(f"| Unique contexts | {len(tc.chains)} | {len(cortex.memory.transitions)} |\n\n")
        f.write(f"**Delta: {delta:+.1f}% -- Winner: {winner}**\n\n")
        f.write("## Breakdown\n\n")
        f.write(f"- Exact matches: {exact_count} ({exact_correct} correct = {exact_correct/max(exact_count,1)*100:.1f}%)\n")
        f.write(f"- Fuzzy matches: {fuzzy_count} ({fuzzy_correct} correct = {fuzzy_correct/max(fuzzy_count,1)*100:.1f}%)\n")
        f.write(f"- Failed: {fail_count}\n\n")
        if exact_count > 0 and fuzzy_count > 0:
            f.write(f"Exact accuracy: {exact_correct/exact_count*100:.1f}%\n")
            f.write(f"Fuzzy accuracy: {fuzzy_correct/fuzzy_count*100:.1f}%\n\n")
        f.write("## Emergent Categories\n\n")
        for s in cat_strs:
            f.write(f"{s}\n")
        f.write("\n## Example Predictions\n\n```\n")
        for ex in examples:
            f.write(f"{ex}\n")
        f.write("```\n\n")
        f.write("## Analysis\n\n")
        if delta > 5:
            f.write("Cortex v2 significantly beats Temporal Chains. Fuzzy SDR matching\n")
            f.write("generalizes to unseen contexts.\n")
        elif delta > 0:
            f.write("Cortex v2 edges out Temporal Chains. The SDR-based fuzzy matching\n")
            f.write("adds some generalization value.\n")
        elif delta > -5:
            f.write("Roughly tied with Temporal Chains. The SDR representation provides\n")
            f.write("categories but prediction improvement is marginal.\n")
        else:
            f.write("Temporal Chains still wins. Analysis:\n\n")
            f.write("The SDR fingerprint approach collapses the 9500+ unique char trigrams\n")
            f.write("into fewer SDR patterns. This compression may lose discriminative power.\n\n")
            f.write("Key insight: the OR-union fingerprint, even with position shifts,\n")
            f.write("still has high collision rate. Different trigrams map to the same SDR.\n")
            f.write("This HURTS exact matching (lumps distinct contexts together) and\n")
            f.write("fuzzy matching becomes irrelevant because most things are already\n")
            f.write("'matched' via collision.\n\n")
            f.write("### What would actually work\n\n")
            f.write("The fundamental problem: SDR union-fingerprints are lossy for short sequences.\n")
            f.write("Temporal Chains on raw chars already capture character-level patterns perfectly.\n\n")
            f.write("Where SDR could win:\n")
            f.write("1. **Longer contexts** (10+ chars) where exact trigram matching fails\n")
            f.write("2. **Cross-language generalization** where similar phonetics map to similar SDRs\n")
            f.write("3. **Hierarchical prediction** -- SDR categories predict word-level patterns,\n")
            f.write("   TC handles char-level\n")

    print(f"\nResults written to {results_path}")


if __name__ == "__main__":
    main()
