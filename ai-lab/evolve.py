"""
Niam-Bay AI Lab — Evolution of Temporal Chains
From 37.4% to as high as possible.

8 experiments, then combine the best into Architecture G.
"""

import time
import os
import sys
import io
import math
import random
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
random.seed(42)

# ─────────────────────────────────────────────────────────────────────
# Utility
# ─────────────────────────────────────────────────────────────────────
def load_text_stream(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return list(f.read())

def load_all_pensees():
    pensees_dir = os.path.join(os.path.dirname(__file__), '..', 'docs', 'pensees')
    all_chars = []
    count = 0
    for fn in sorted(os.listdir(pensees_dir)):
        if fn.endswith('.md'):
            fp = os.path.join(pensees_dir, fn)
            with open(fp, 'r', encoding='utf-8') as f:
                all_chars.extend(list(f.read()))
            count += 1
    return all_chars, count

def measure_accuracy(architecture, stream):
    correct = 0
    total = 0
    for i, token in enumerate(stream):
        pred = architecture.step(token)
        if i > 0:
            total += 1
            if pred == token:
                correct += 1
    return correct / total if total > 0 else 0

def sizeof_obj(obj):
    seen = set()
    total = 0
    stack = [obj]
    while stack:
        o = stack.pop()
        oid = id(o)
        if oid in seen:
            continue
        seen.add(oid)
        total += sys.getsizeof(o)
        if isinstance(o, dict):
            for k, v in o.items():
                stack.extend([k, v])
        elif isinstance(o, (list, tuple, set, frozenset)):
            for item in o:
                stack.append(item)
        elif hasattr(o, '__dict__'):
            stack.append(o.__dict__)
    return total

# ─────────────────────────────────────────────────────────────────────
# Baseline: Original Temporal Chains (Architecture D)
# ─────────────────────────────────────────────────────────────────────
class TemporalChains:
    def __init__(self, max_order=4):
        self.max_order = max_order
        self.chains = {i: defaultdict(lambda: defaultdict(int)) for i in range(1, max_order + 1)}
        self.history = []

    def step(self, token):
        prediction = None
        for order in range(min(self.max_order, len(self.history)), 0, -1):
            ctx = tuple(self.history[-order:])
            if ctx in self.chains[order]:
                counts = self.chains[order][ctx]
                prediction = max(counts, key=counts.get)
                break
        for order in range(1, min(self.max_order, len(self.history)) + 1):
            ctx = tuple(self.history[-order:])
            self.chains[order][ctx][token] += 1
        self.history.append(token)
        if len(self.history) > self.max_order + 10:
            self.history = self.history[-(self.max_order + 10):]
        return prediction

# ─────────────────────────────────────────────────────────────────────
# Experiment 1: Deeper context
# ─────────────────────────────────────────────────────────────────────
def experiment_1(stream):
    print("\n" + "="*70)
    print("  EXPERIMENT 1: Deeper Context")
    print("="*70)
    depths = [2, 4, 8, 16, 32, 64]
    results = {}
    for d in depths:
        t0 = time.perf_counter()
        arch = TemporalChains(max_order=d)
        acc = measure_accuracy(arch, stream)
        elapsed = time.perf_counter() - t0
        mem = sizeof_obj(arch)
        results[d] = {'accuracy': acc, 'time': elapsed, 'memory': mem}
        print(f"  Depth {d:>3}: {acc*100:.2f}%  ({elapsed:.2f}s, {mem:,} bytes)")

    # ASCII plot
    print("\n  Accuracy vs Depth:")
    max_acc = max(r['accuracy'] for r in results.values())
    for d in depths:
        acc = results[d]['accuracy']
        bar_len = int(acc / max_acc * 40) if max_acc > 0 else 0
        print(f"  {d:>3} | {'#' * bar_len} {acc*100:.1f}%")

    best_depth = max(results, key=lambda d: results[d]['accuracy'])
    print(f"\n  >> Best depth: {best_depth} ({results[best_depth]['accuracy']*100:.2f}%)")
    return results, best_depth

# ─────────────────────────────────────────────────────────────────────
# Experiment 2: Weighted Voting
# ─────────────────────────────────────────────────────────────────────
class WeightedVotingChains:
    def __init__(self, max_order=4):
        self.max_order = max_order
        self.chains = {i: defaultdict(lambda: defaultdict(int)) for i in range(1, max_order + 1)}
        self.history = []

    def step(self, token):
        prediction = None
        votes = defaultdict(float)
        for order in range(1, min(self.max_order, len(self.history)) + 1):
            ctx = tuple(self.history[-order:])
            if ctx in self.chains[order]:
                counts = self.chains[order][ctx]
                best = max(counts, key=counts.get)
                weight = 2 ** order  # depth-1=2, depth-2=4, depth-3=8, depth-4=16
                votes[best] += weight
        if votes:
            prediction = max(votes, key=votes.get)

        for order in range(1, min(self.max_order, len(self.history)) + 1):
            ctx = tuple(self.history[-order:])
            self.chains[order][ctx][token] += 1
        self.history.append(token)
        if len(self.history) > self.max_order + 10:
            self.history = self.history[-(self.max_order + 10):]
        return prediction

class WeightedVotingChainsV2:
    """All matching orders vote, weighted by depth AND frequency."""
    def __init__(self, max_order=4):
        self.max_order = max_order
        self.chains = {i: defaultdict(lambda: defaultdict(int)) for i in range(1, max_order + 1)}
        self.history = []

    def step(self, token):
        prediction = None
        votes = defaultdict(float)
        for order in range(1, min(self.max_order, len(self.history)) + 1):
            ctx = tuple(self.history[-order:])
            if ctx in self.chains[order]:
                counts = self.chains[order][ctx]
                total = sum(counts.values())
                weight = 2 ** order
                for candidate, count in counts.items():
                    votes[candidate] += weight * (count / total)
        if votes:
            prediction = max(votes, key=votes.get)

        for order in range(1, min(self.max_order, len(self.history)) + 1):
            ctx = tuple(self.history[-order:])
            self.chains[order][ctx][token] += 1
        self.history.append(token)
        if len(self.history) > self.max_order + 10:
            self.history = self.history[-(self.max_order + 10):]
        return prediction

def experiment_2(stream, best_depth):
    print("\n" + "="*70)
    print("  EXPERIMENT 2: Weighted Voting")
    print("="*70)

    # Baseline
    arch = TemporalChains(max_order=best_depth)
    baseline = measure_accuracy(arch, stream)
    print(f"  Baseline (longest-match, depth={best_depth}): {baseline*100:.2f}%")

    # Weighted voting v1
    arch = WeightedVotingChains(max_order=best_depth)
    acc_v1 = measure_accuracy(arch, stream)
    print(f"  Weighted voting v1 (depth={best_depth}): {acc_v1*100:.2f}%")

    # Weighted voting v2 (frequency-weighted votes)
    arch = WeightedVotingChainsV2(max_order=best_depth)
    acc_v2 = measure_accuracy(arch, stream)
    print(f"  Weighted voting v2 (freq+depth, depth={best_depth}): {acc_v2*100:.2f}%")

    best_method = 'v2' if acc_v2 >= max(baseline, acc_v1) else ('v1' if acc_v1 >= baseline else 'baseline')
    best_acc = max(baseline, acc_v1, acc_v2)
    print(f"\n  >> Best: {best_method} ({best_acc*100:.2f}%)")
    return best_method, best_acc

# ─────────────────────────────────────────────────────────────────────
# Experiment 3: Frequency-weighted predictions
# ─────────────────────────────────────────────────────────────────────
class FrequencyChains:
    """Already uses frequency (max of counts). But let's be explicit about it
    and compare to a version that uses probability thresholds."""
    def __init__(self, max_order=4, confidence_threshold=0.0):
        self.max_order = max_order
        self.confidence_threshold = confidence_threshold
        self.chains = {i: defaultdict(lambda: defaultdict(int)) for i in range(1, max_order + 1)}
        self.history = []

    def step(self, token):
        prediction = None
        for order in range(min(self.max_order, len(self.history)), 0, -1):
            ctx = tuple(self.history[-order:])
            if ctx in self.chains[order]:
                counts = self.chains[order][ctx]
                total = sum(counts.values())
                best = max(counts, key=counts.get)
                confidence = counts[best] / total
                if confidence >= self.confidence_threshold:
                    prediction = best
                    break
                # If not confident enough at this depth, fall through to shorter context
        for order in range(1, min(self.max_order, len(self.history)) + 1):
            ctx = tuple(self.history[-order:])
            self.chains[order][ctx][token] += 1
        self.history.append(token)
        if len(self.history) > self.max_order + 10:
            self.history = self.history[-(self.max_order + 10):]
        return prediction

def experiment_3(stream, best_depth):
    print("\n" + "="*70)
    print("  EXPERIMENT 3: Frequency-Weighted Predictions")
    print("="*70)

    thresholds = [0.0, 0.3, 0.5, 0.7, 0.9]
    results = {}
    for t in thresholds:
        arch = FrequencyChains(max_order=best_depth, confidence_threshold=t)
        acc = measure_accuracy(arch, stream)
        results[t] = acc
        print(f"  Threshold {t:.1f}: {acc*100:.2f}%")

    best_t = max(results, key=results.get)
    print(f"\n  >> Best threshold: {best_t} ({results[best_t]*100:.2f}%)")
    return best_t, results[best_t]

# ─────────────────────────────────────────────────────────────────────
# Experiment 4: Forgetting (Temporal Decay)
# ─────────────────────────────────────────────────────────────────────
class DecayingChains:
    def __init__(self, max_order=4, half_life=500):
        self.max_order = max_order
        self.half_life = half_life
        self.decay = 0.5 ** (1.0 / half_life)
        self.chains = {i: defaultdict(lambda: defaultdict(float)) for i in range(1, max_order + 1)}
        self.history = []
        self.step_count = 0

    def step(self, token):
        self.step_count += 1
        prediction = None
        for order in range(min(self.max_order, len(self.history)), 0, -1):
            ctx = tuple(self.history[-order:])
            if ctx in self.chains[order]:
                counts = self.chains[order][ctx]
                prediction = max(counts, key=counts.get)
                break

        for order in range(1, min(self.max_order, len(self.history)) + 1):
            ctx = tuple(self.history[-order:])
            # Decay existing counts
            counts = self.chains[order][ctx]
            for k in counts:
                counts[k] *= self.decay
            counts[token] += 1.0

        self.history.append(token)
        if len(self.history) > self.max_order + 10:
            self.history = self.history[-(self.max_order + 10):]
        return prediction

def experiment_4(stream, best_depth):
    print("\n" + "="*70)
    print("  EXPERIMENT 4: Forgetting (Temporal Decay)")
    print("="*70)

    half_lives = [50, 100, 500, 1000, 5000, None]  # None = no decay (baseline)
    results = {}
    for hl in half_lives:
        if hl is None:
            arch = TemporalChains(max_order=best_depth)
            label = "No decay"
        else:
            arch = DecayingChains(max_order=best_depth, half_life=hl)
            label = f"HL={hl}"
        acc = measure_accuracy(arch, stream)
        results[hl] = acc
        print(f"  {label:>12}: {acc*100:.2f}%")

    best_hl = max(results, key=results.get)
    label = "No decay" if best_hl is None else f"HL={best_hl}"
    print(f"\n  >> Best: {label} ({results[best_hl]*100:.2f}%)")
    return best_hl, results[best_hl]

# ─────────────────────────────────────────────────────────────────────
# Experiment 5: Multi-scale (char + word)
# ─────────────────────────────────────────────────────────────────────
class MultiScaleChains:
    def __init__(self, max_order_char=8, max_order_word=4):
        self.max_order_char = max_order_char
        self.max_order_word = max_order_word
        self.char_chains = {i: defaultdict(lambda: defaultdict(int)) for i in range(1, max_order_char + 1)}
        self.word_chains = {i: defaultdict(lambda: defaultdict(int)) for i in range(1, max_order_word + 1)}
        self.char_history = []
        self.word_history = []
        self.current_word = []

    def step(self, token):
        # Character-level prediction
        char_pred = None
        char_confidence = 0
        for order in range(min(self.max_order_char, len(self.char_history)), 0, -1):
            ctx = tuple(self.char_history[-order:])
            if ctx in self.char_chains[order]:
                counts = self.char_chains[order][ctx]
                total = sum(counts.values())
                best = max(counts, key=counts.get)
                char_pred = best
                char_confidence = counts[best] / total * order  # weight by depth
                break

        # Word-level prediction of next character
        word_pred = None
        word_confidence = 0
        if token == ' ' or token == '\n':
            word = ''.join(self.current_word)
            if word:
                # Learn word transition
                for order in range(1, min(self.max_order_word, len(self.word_history)) + 1):
                    ctx = tuple(self.word_history[-order:])
                    self.word_chains[order][ctx][word] += 1
                self.word_history.append(word)
                if len(self.word_history) > self.max_order_word + 10:
                    self.word_history = self.word_history[-(self.max_order_word + 10):]
            self.current_word = []
            # After a space, predict first char of next word
            for order in range(min(self.max_order_word, len(self.word_history)), 0, -1):
                ctx = tuple(self.word_history[-order:])
                if ctx in self.word_chains[order]:
                    counts = self.word_chains[order][ctx]
                    best_word = max(counts, key=counts.get)
                    if best_word:
                        word_pred = best_word[0]  # first char of predicted word
                        total = sum(counts.values())
                        word_confidence = counts[best_word] / total * 0.5
                    break
        else:
            self.current_word.append(token)

        # Character-level learn
        for order in range(1, min(self.max_order_char, len(self.char_history)) + 1):
            ctx = tuple(self.char_history[-order:])
            self.char_chains[order][ctx][token] += 1
        self.char_history.append(token)
        if len(self.char_history) > self.max_order_char + 10:
            self.char_history = self.char_history[-(self.max_order_char + 10):]

        # Combine predictions
        if char_pred and word_pred:
            if word_confidence > char_confidence:
                return word_pred
            return char_pred
        return char_pred or word_pred

def experiment_5(stream, best_depth):
    print("\n" + "="*70)
    print("  EXPERIMENT 5: Multi-Scale (Char + Word)")
    print("="*70)

    arch = TemporalChains(max_order=best_depth)
    baseline = measure_accuracy(arch, stream)
    print(f"  Baseline (char only, depth={best_depth}): {baseline*100:.2f}%")

    arch = MultiScaleChains(max_order_char=best_depth, max_order_word=4)
    acc = measure_accuracy(arch, stream)
    print(f"  Multi-scale (char={best_depth}, word=4): {acc*100:.2f}%")

    arch = MultiScaleChains(max_order_char=best_depth, max_order_word=8)
    acc2 = measure_accuracy(arch, stream)
    print(f"  Multi-scale (char={best_depth}, word=8): {acc2*100:.2f}%")

    best_acc = max(baseline, acc, acc2)
    helps = best_acc > baseline
    print(f"\n  >> Multi-scale helps: {helps} (best: {best_acc*100:.2f}%)")
    return helps, best_acc

# ─────────────────────────────────────────────────────────────────────
# Experiment 6: Compression (Prune rare entries)
# ─────────────────────────────────────────────────────────────────────
class PruningChains:
    def __init__(self, max_order=4, prune_threshold=2, prune_interval=500):
        self.max_order = max_order
        self.prune_threshold = prune_threshold
        self.prune_interval = prune_interval
        self.chains = {i: defaultdict(lambda: defaultdict(int)) for i in range(1, max_order + 1)}
        self.history = []
        self.step_count = 0

    def step(self, token):
        self.step_count += 1
        prediction = None
        for order in range(min(self.max_order, len(self.history)), 0, -1):
            ctx = tuple(self.history[-order:])
            if ctx in self.chains[order]:
                counts = self.chains[order][ctx]
                prediction = max(counts, key=counts.get)
                break

        for order in range(1, min(self.max_order, len(self.history)) + 1):
            ctx = tuple(self.history[-order:])
            self.chains[order][ctx][token] += 1

        self.history.append(token)
        if len(self.history) > self.max_order + 10:
            self.history = self.history[-(self.max_order + 10):]

        # Periodic pruning
        if self.step_count % self.prune_interval == 0:
            self._prune()

        return prediction

    def _prune(self):
        for order in range(1, self.max_order + 1):
            to_delete = []
            for ctx, counts in self.chains[order].items():
                # Remove entries seen fewer than threshold times
                rare = [k for k, v in counts.items() if v < self.prune_threshold]
                for k in rare:
                    del counts[k]
                if not counts:
                    to_delete.append(ctx)
            for ctx in to_delete:
                del self.chains[order][ctx]

def experiment_6(stream, best_depth):
    print("\n" + "="*70)
    print("  EXPERIMENT 6: Compression (Pruning)")
    print("="*70)

    arch = TemporalChains(max_order=best_depth)
    baseline = measure_accuracy(arch, stream)
    baseline_mem = sizeof_obj(arch)
    print(f"  Baseline: {baseline*100:.2f}% ({baseline_mem:,} bytes)")

    thresholds = [2, 3, 5, 10]
    results = {}
    for n in thresholds:
        arch = PruningChains(max_order=best_depth, prune_threshold=n)
        acc = measure_accuracy(arch, stream)
        mem = sizeof_obj(arch)
        results[n] = {'accuracy': acc, 'memory': mem}
        savings = (1 - mem / baseline_mem) * 100 if baseline_mem > 0 else 0
        print(f"  Prune > {n}: {acc*100:.2f}% ({mem:,} bytes, {savings:.0f}% smaller)")

    best_n = max(results, key=lambda n: results[n]['accuracy'])
    print(f"\n  >> Best prune threshold: {best_n} ({results[best_n]['accuracy']*100:.2f}%)")
    return results

# ─────────────────────────────────────────────────────────────────────
# Experiment 7: Self-generated Training ("Dreaming")
# ─────────────────────────────────────────────────────────────────────
class DreamingChains:
    def __init__(self, max_order=4, dream_length=100, dream_interval=500):
        self.max_order = max_order
        self.dream_length = dream_length
        self.dream_interval = dream_interval
        self.chains = {i: defaultdict(lambda: defaultdict(int)) for i in range(1, max_order + 1)}
        self.history = []
        self.step_count = 0

    def _generate(self, length):
        """Generate tokens from the model's own knowledge."""
        if not self.history:
            return []
        generated = list(self.history[-self.max_order:])
        for _ in range(length):
            pred = None
            for order in range(min(self.max_order, len(generated)), 0, -1):
                ctx = tuple(generated[-order:])
                if ctx in self.chains[order]:
                    counts = self.chains[order][ctx]
                    # Sample proportionally instead of always picking max
                    total = sum(counts.values())
                    r = random.random() * total
                    cumsum = 0
                    for tok, c in counts.items():
                        cumsum += c
                        if cumsum >= r:
                            pred = tok
                            break
                    if pred:
                        break
            if pred is None:
                break
            generated.append(pred)
        return generated[self.max_order:]  # exclude the seed

    def _dream(self):
        """Feed self-generated data back as training."""
        dreamed = self._generate(self.dream_length)
        for i, token in enumerate(dreamed):
            for order in range(1, min(self.max_order, i) + 1):
                ctx = tuple(dreamed[max(0, i-order):i])
                if len(ctx) == order:
                    self.chains[order][ctx][token] += 1

    def step(self, token):
        self.step_count += 1
        prediction = None
        for order in range(min(self.max_order, len(self.history)), 0, -1):
            ctx = tuple(self.history[-order:])
            if ctx in self.chains[order]:
                counts = self.chains[order][ctx]
                prediction = max(counts, key=counts.get)
                break

        for order in range(1, min(self.max_order, len(self.history)) + 1):
            ctx = tuple(self.history[-order:])
            self.chains[order][ctx][token] += 1

        self.history.append(token)
        if len(self.history) > self.max_order + 10:
            self.history = self.history[-(self.max_order + 10):]

        if self.step_count % self.dream_interval == 0:
            self._dream()

        return prediction

def experiment_7(stream, best_depth):
    print("\n" + "="*70)
    print("  EXPERIMENT 7: Self-Generated Training (Dreaming)")
    print("="*70)

    arch = TemporalChains(max_order=best_depth)
    baseline = measure_accuracy(arch, stream)
    print(f"  Baseline: {baseline*100:.2f}%")

    configs = [
        (50, 200),
        (100, 500),
        (200, 500),
        (100, 1000),
    ]
    results = {}
    for dream_len, dream_int in configs:
        arch = DreamingChains(max_order=best_depth, dream_length=dream_len, dream_interval=dream_int)
        acc = measure_accuracy(arch, stream)
        results[(dream_len, dream_int)] = acc
        print(f"  Dream(len={dream_len}, every={dream_int}): {acc*100:.2f}%")

    best_cfg = max(results, key=results.get)
    print(f"\n  >> Best: len={best_cfg[0]}, interval={best_cfg[1]} ({results[best_cfg]*100:.2f}%)")
    return results, baseline

# ─────────────────────────────────────────────────────────────────────
# Experiment 8: Multiple texts
# ─────────────────────────────────────────────────────────────────────
def experiment_8(single_stream, best_depth):
    print("\n" + "="*70)
    print("  EXPERIMENT 8: Multiple Texts")
    print("="*70)

    arch = TemporalChains(max_order=best_depth)
    baseline = measure_accuracy(arch, single_stream)
    print(f"  Single text ({len(single_stream)} chars): {baseline*100:.2f}%")

    all_text, n_files = load_all_pensees()
    print(f"  All pensees: {n_files} files, {len(all_text)} chars total")

    # Train on all, test accuracy on the full corpus
    arch = TemporalChains(max_order=best_depth)
    acc_all = measure_accuracy(arch, all_text)
    print(f"  All pensees accuracy: {acc_all*100:.2f}%")

    # Train on all pensees FIRST, then test on single text
    arch = TemporalChains(max_order=best_depth)
    # Pre-train
    for token in all_text:
        arch.step(token)
    # Now test on single stream
    correct = 0
    total = 0
    for i, token in enumerate(single_stream):
        pred = arch.step(token)
        if i > 0:
            total += 1
            if pred == token:
                correct += 1
    pretrained_acc = correct / total if total > 0 else 0
    print(f"  Pre-trained on all, tested on single: {pretrained_acc*100:.2f}%")

    print(f"\n  >> Pre-training boost: {baseline*100:.2f}% -> {pretrained_acc*100:.2f}% ({(pretrained_acc-baseline)*100:+.2f}%)")
    return acc_all, pretrained_acc

# ─────────────────────────────────────────────────────────────────────
# Architecture G: Combined Best
# ─────────────────────────────────────────────────────────────────────
class ArchitectureG:
    """Combines all winning improvements."""
    def __init__(self, max_order=16, use_weighted_voting=True, use_frequency=True,
                 half_life=None, prune_threshold=0, prune_interval=1000):
        self.max_order = max_order
        self.use_weighted_voting = use_weighted_voting
        self.use_frequency = use_frequency
        self.half_life = half_life
        self.decay = 0.5 ** (1.0 / half_life) if half_life else 1.0
        self.prune_threshold = prune_threshold
        self.prune_interval = prune_interval
        self.chains = {i: defaultdict(lambda: defaultdict(float)) for i in range(1, max_order + 1)}
        self.history = []
        self.step_count = 0

    def step(self, token):
        self.step_count += 1
        prediction = None

        if self.use_weighted_voting:
            # All depths vote, weighted by depth and frequency
            votes = defaultdict(float)
            for order in range(1, min(self.max_order, len(self.history)) + 1):
                ctx = tuple(self.history[-order:])
                if ctx in self.chains[order]:
                    counts = self.chains[order][ctx]
                    total = sum(counts.values())
                    if total > 0:
                        weight = 2 ** order
                        for candidate, count in counts.items():
                            votes[candidate] += weight * (count / total)
            if votes:
                prediction = max(votes, key=votes.get)
        else:
            # Longest match wins
            for order in range(min(self.max_order, len(self.history)), 0, -1):
                ctx = tuple(self.history[-order:])
                if ctx in self.chains[order]:
                    counts = self.chains[order][ctx]
                    prediction = max(counts, key=counts.get)
                    break

        # Learn
        for order in range(1, min(self.max_order, len(self.history)) + 1):
            ctx = tuple(self.history[-order:])
            if self.half_life:
                counts = self.chains[order][ctx]
                for k in counts:
                    counts[k] *= self.decay
            self.chains[order][ctx][token] += 1.0

        self.history.append(token)
        if len(self.history) > self.max_order + 10:
            self.history = self.history[-(self.max_order + 10):]

        # Periodic pruning
        if self.prune_threshold > 0 and self.step_count % self.prune_interval == 0:
            for order in range(1, self.max_order + 1):
                to_delete = []
                for ctx, counts in self.chains[order].items():
                    rare = [k for k, v in counts.items() if v < self.prune_threshold]
                    for k in rare:
                        del counts[k]
                    if not counts:
                        to_delete.append(ctx)
                for ctx in to_delete:
                    del self.chains[order][ctx]

        return prediction

# ─────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("\n" + "█"*70)
    print("  NIAM-BAY AI LAB — EVOLUTION OF TEMPORAL CHAINS")
    print("  From 37.4% to ???")
    print("█"*70)

    # Load test data
    pensee_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'pensees', '2026-03-20-huit-jours.md')
    stream = load_text_stream(pensee_path)
    print(f"\n  Test text: {len(stream)} characters")

    # Baseline
    arch = TemporalChains(max_order=4)
    baseline = measure_accuracy(arch, stream)
    print(f"  BASELINE (D, depth=4): {baseline*100:.2f}%")

    # Run all experiments
    results_1, best_depth = experiment_1(stream)
    best_voting, acc_voting = experiment_2(stream, best_depth)
    best_threshold, acc_threshold = experiment_3(stream, best_depth)
    best_hl, acc_hl = experiment_4(stream, best_depth)
    multi_helps, acc_multi = experiment_5(stream, best_depth)
    results_6 = experiment_6(stream, best_depth)
    results_7, baseline_7 = experiment_7(stream, best_depth)
    acc_all_pensees, acc_pretrained = experiment_8(stream, best_depth)

    # ── Architecture G: Combine the best ────────────────────────
    print("\n" + "█"*70)
    print("  ARCHITECTURE G: COMBINING THE BEST")
    print("█"*70)

    # Try several G configurations
    g_configs = [
        # (name, params)
        ("G1: deep+voting", dict(max_order=best_depth, use_weighted_voting=True)),
        ("G2: deep+voting+decay", dict(max_order=best_depth, use_weighted_voting=True, half_life=1000)),
        ("G3: deep+longest", dict(max_order=best_depth, use_weighted_voting=False)),
        ("G4: deep+voting+prune", dict(max_order=best_depth, use_weighted_voting=True, prune_threshold=2)),
        ("G5: deep16+voting", dict(max_order=16, use_weighted_voting=True)),
        ("G6: deep32+voting", dict(max_order=32, use_weighted_voting=True)),
        ("G7: deep64+voting", dict(max_order=64, use_weighted_voting=True)),
    ]

    g_results = {}
    for name, params in g_configs:
        arch = ArchitectureG(**params)
        acc = measure_accuracy(arch, stream)
        mem = sizeof_obj(arch)
        g_results[name] = {'accuracy': acc, 'memory': mem}
        print(f"  {name:<30}: {acc*100:.2f}% ({mem:,} bytes)")

    # Best G on single text
    best_g_name = max(g_results, key=lambda n: g_results[n]['accuracy'])
    best_g_acc = g_results[best_g_name]['accuracy']
    print(f"\n  >> Best G: {best_g_name} ({best_g_acc*100:.2f}%)")

    # Now try best G with pre-training on all pensees
    print("\n  Pre-training best G on all pensees...")
    all_text, n_files = load_all_pensees()

    # Find best G params
    best_g_params = dict(g_configs[[n for n, _ in g_configs].index(best_g_name)][1])
    arch = ArchitectureG(**best_g_params)
    # Pre-train
    for token in all_text:
        arch.step(token)
    # Test
    correct = 0
    total = 0
    for i, token in enumerate(stream):
        pred = arch.step(token)
        if i > 0:
            total += 1
            if pred == token:
                correct += 1
    final_acc = correct / total if total > 0 else 0
    print(f"  {best_g_name} + pre-training: {final_acc*100:.2f}%")

    # Also try with weighted voting V2 style approach directly with deeper depth and pre-training
    for depth in [best_depth, 32, 64]:
        arch = ArchitectureG(max_order=depth, use_weighted_voting=True)
        for token in all_text:
            arch.step(token)
        correct = 0
        total = 0
        for i, token in enumerate(stream):
            pred = arch.step(token)
            if i > 0:
                total += 1
                if pred == token:
                    correct += 1
        pt_acc = correct / total if total > 0 else 0
        print(f"  G(depth={depth}, voting) + pre-training: {pt_acc*100:.2f}%")

    # ── FINAL SUMMARY ──────────────────────────────────────────
    print("\n" + "█"*70)
    print("  FINAL SUMMARY")
    print("█"*70)
    print(f"\n  Baseline (Architecture D, depth=4): {baseline*100:.2f}%")
    print(f"  Best single-text G: {best_g_name} = {best_g_acc*100:.2f}%")
    print(f"  Best G + pre-training: {final_acc*100:.2f}%")
    improvement = (best_g_acc - baseline) / baseline * 100
    print(f"  Improvement over baseline: {improvement:+.1f}%")
    print(f"\n  Journey: {baseline*100:.1f}% -> {best_g_acc*100:.1f}%")
    print()
