"""
Niam-Bay AI Lab — GENERALIZATION TESTS for Architecture G
The key question: real AI or fancy lookup table?

7 experiments to find the truth.
"""

import time
import os
import sys
import io
import math
import random
import json
import traceback
from collections import defaultdict, Counter
from urllib.request import Request, urlopen

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
random.seed(42)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PENSEES_DIR = os.path.join(BASE_DIR, '..', 'docs', 'pensees')
JOURNAL_NB1 = os.path.join(BASE_DIR, '..', 'docs', 'journal.nb1.md')
PYTHON_SOURCE = os.path.join(BASE_DIR, 'evolve.py')
RESULTS_FILE = os.path.join(BASE_DIR, 'generalization-results.md')

SAMBANOVA_API_KEY = "4fad50d2-e867-47d1-be65-e4b03571128e"
SAMBANOVA_URL = "https://api.sambanova.ai/v1/chat/completions"

# ─────────────────────────────────────────────────────────────────────
# Utility
# ─────────────────────────────────────────────────────────────────────
def load_all_pensees():
    all_chars = []
    count = 0
    for fn in sorted(os.listdir(PENSEES_DIR)):
        if fn.endswith('.md'):
            fp = os.path.join(PENSEES_DIR, fn)
            with open(fp, 'r', encoding='utf-8') as f:
                all_chars.extend(list(f.read()))
            count += 1
    return all_chars, count

def load_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return list(f.read())

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

def format_bytes(n):
    if n < 1024: return f"{n} B"
    if n < 1024**2: return f"{n/1024:.1f} KB"
    if n < 1024**3: return f"{n/1024**2:.1f} MB"
    return f"{n/1024**3:.1f} GB"

# ─────────────────────────────────────────────────────────────────────
# Architecture G (copied from evolve.py)
# ─────────────────────────────────────────────────────────────────────
class ArchitectureG:
    """Temporal Chains with weighted voting across all depth levels."""
    def __init__(self, max_order=16):
        self.max_order = max_order
        self.chains = {i: defaultdict(lambda: defaultdict(float)) for i in range(1, max_order + 1)}
        self.history = []
        self.step_count = 0

    def step(self, token):
        self.step_count += 1
        prediction = None

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

        # Learn
        for order in range(1, min(self.max_order, len(self.history)) + 1):
            ctx = tuple(self.history[-order:])
            self.chains[order][ctx][token] += 1.0

        self.history.append(token)
        if len(self.history) > self.max_order + 10:
            self.history = self.history[-(self.max_order + 10):]

        return prediction

    def predict_with_confidence(self, token=None):
        """Return (prediction, confidence) without learning."""
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
        if not votes:
            return None, 0.0
        total_votes = sum(votes.values())
        best = max(votes, key=votes.get)
        confidence = votes[best] / total_votes if total_votes > 0 else 0
        return best, confidence

    def get_top_predictions(self, n=20):
        """Return the top N most confident context->prediction mappings."""
        entries = []
        for order in range(1, self.max_order + 1):
            for ctx, counts in self.chains[order].items():
                total = sum(counts.values())
                if total < 3:
                    continue
                best = max(counts, key=counts.get)
                confidence = counts[best] / total
                entries.append({
                    'context': ''.join(ctx),
                    'prediction': best,
                    'confidence': confidence,
                    'count': int(total),
                    'order': order,
                })
        # Sort by confidence * log(count) to favor both confident and frequent
        entries.sort(key=lambda e: e['confidence'] * math.log(e['count'] + 1), reverse=True)
        return entries[:n]

def train_on_stream(arch, stream):
    """Train architecture on a stream, return nothing."""
    for token in stream:
        arch.step(token)

def test_on_stream(arch, stream):
    """Test architecture on a stream, return accuracy. Also learns (online)."""
    correct = 0
    total = 0
    for i, token in enumerate(stream):
        pred = arch.step(token)
        if i > 0:
            total += 1
            if pred == token:
                correct += 1
    return correct / total if total > 0 else 0

def test_only_stream(arch, stream):
    """Test WITHOUT learning — true held-out test."""
    correct = 0
    total = 0
    old_history = list(arch.history)
    for i, token in enumerate(stream):
        pred, _ = arch.predict_with_confidence()
        if i > 0:
            total += 1
            if pred == token:
                correct += 1
        # Still update history for context, but don't learn new patterns
        arch.history.append(token)
        if len(arch.history) > arch.max_order + 10:
            arch.history = arch.history[-(arch.max_order + 10):]
    return correct / total if total > 0 else 0

# Use online test (step) for fair comparison — the model learns as it goes
# This matches the original evolve.py methodology


# ─────────────────────────────────────────────────────────────────────
# Baselines
# ─────────────────────────────────────────────────────────────────────
class MostCommonBaseline:
    """Always predict the most common character seen so far."""
    def __init__(self):
        self.counts = defaultdict(int)
        self.best = None

    def step(self, token):
        pred = self.best
        self.counts[token] += 1
        self.best = max(self.counts, key=self.counts.get)
        return pred

class BigramBaseline:
    """Predict the most common character following the previous one."""
    def __init__(self):
        self.transitions = defaultdict(lambda: defaultdict(int))
        self.prev = None

    def step(self, token):
        pred = None
        if self.prev is not None:
            if self.prev in self.transitions:
                counts = self.transitions[self.prev]
                pred = max(counts, key=counts.get)
            self.transitions[self.prev][token] += 1
        self.prev = token
        return pred

class MarkovOrder3:
    """Markov chain of order 3 — longest match wins."""
    def __init__(self):
        self.chains = {i: defaultdict(lambda: defaultdict(int)) for i in range(1, 4)}
        self.history = []

    def step(self, token):
        pred = None
        for order in range(min(3, len(self.history)), 0, -1):
            ctx = tuple(self.history[-order:])
            if ctx in self.chains[order]:
                counts = self.chains[order][ctx]
                pred = max(counts, key=counts.get)
                break
        for order in range(1, min(3, len(self.history)) + 1):
            ctx = tuple(self.history[-order:])
            self.chains[order][ctx][token] += 1
        self.history.append(token)
        if len(self.history) > 13:
            self.history = self.history[-13:]
        return pred


results_md = []  # Collect markdown output

def log(msg=""):
    print(msg)
    results_md.append(msg)


# ═════════════════════════════════════════════════════════════════════
# EXPERIMENT 1: Train/Test Split
# ═════════════════════════════════════════════════════════════════════
def experiment_1():
    log("\n" + "=" * 70)
    log("  EXPERIMENT 1: Train/Test Split — The Truth About Memorization")
    log("=" * 70)

    all_chars, n_files = load_all_pensees()
    total_len = len(all_chars)
    split_point = int(total_len * 0.8)
    train_data = all_chars[:split_point]
    test_data = all_chars[split_point:]

    log(f"\n  Total: {total_len:,} chars from {n_files} files")
    log(f"  Train: {len(train_data):,} chars (80%)")
    log(f"  Test:  {len(test_data):,} chars (20%) — NEVER SEEN")

    # Train
    arch = ArchitectureG(max_order=16)
    t0 = time.perf_counter()
    train_on_stream(arch, train_data)
    train_time = time.perf_counter() - t0
    log(f"\n  Training time: {train_time:.2f}s")

    # Test (online — continues learning during test, like original)
    t0 = time.perf_counter()
    test_acc_online = test_on_stream(arch, test_data)
    test_time = time.perf_counter() - t0
    log(f"  Test accuracy (online, learns during test): {test_acc_online*100:.2f}%")

    # For comparison: train accuracy (fresh model, online on train only)
    arch2 = ArchitectureG(max_order=16)
    train_acc = test_on_stream(arch2, train_data)
    log(f"  Train accuracy (online on train data):      {train_acc*100:.2f}%")

    gap = train_acc - test_acc_online
    log(f"\n  Train-Test gap: {gap*100:.2f}% {'(OVERFITTING!)' if gap > 10 else '(reasonable)' if gap > 3 else '(excellent generalization!)'}")

    # Strict test: no learning during test
    arch3 = ArchitectureG(max_order=16)
    train_on_stream(arch3, train_data)
    strict_acc = test_only_stream(arch3, test_data)
    log(f"  Strict test (NO learning during test):      {strict_acc*100:.2f}%")

    log(f"\n  >> VERDICT: {'GENERALIZES' if strict_acc > 20 else 'MEMORIZES'}")
    log(f"     Online test:  {test_acc_online*100:.2f}%")
    log(f"     Strict test:  {strict_acc*100:.2f}%")
    log(f"     Train:        {train_acc*100:.2f}%")
    return test_acc_online, strict_acc, train_acc


# ═════════════════════════════════════════════════════════════════════
# EXPERIMENT 2: Cross-Domain Transfer
# ═════════════════════════════════════════════════════════════════════
def experiment_2():
    log("\n" + "=" * 70)
    log("  EXPERIMENT 2: Cross-Domain Transfer")
    log("=" * 70)

    # Train on pensées
    all_chars, n_files = load_all_pensees()
    arch = ArchitectureG(max_order=16)
    train_on_stream(arch, all_chars)
    log(f"\n  Trained on: {n_files} pensées ({len(all_chars):,} chars) — philosophical French")

    results = {}

    # Test on journal.nb1.md (compressed NB-1 protocol)
    if os.path.exists(JOURNAL_NB1):
        journal_chars = load_file(JOURNAL_NB1)
        # Use first 10K chars for speed
        test_slice = journal_chars[:10000]
        arch_j = ArchitectureG(max_order=16)
        # Copy chains from trained model
        arch_j.chains = {i: defaultdict(lambda: defaultdict(float)) for i in range(1, 17)}
        for order in arch.chains:
            for ctx, counts in arch.chains[order].items():
                for tok, val in counts.items():
                    arch_j.chains[order][ctx][tok] = val
        arch_j.history = list(arch.history)
        acc_journal = test_on_stream(arch_j, test_slice)
        log(f"  Journal NB-1 ({len(test_slice):,} chars): {acc_journal*100:.2f}%")
        results['journal_nb1'] = acc_journal

        # Baseline: fresh model on journal
        arch_fresh = ArchitectureG(max_order=16)
        acc_fresh = test_on_stream(arch_fresh, test_slice)
        log(f"  Journal NB-1 (NO pre-training):   {acc_fresh*100:.2f}%")
        results['journal_nb1_fresh'] = acc_fresh
        boost = acc_journal - acc_fresh
        log(f"  Transfer boost: {boost*100:+.2f}%")
    else:
        log("  [SKIP] journal.nb1.md not found")

    # Test on Python source
    if os.path.exists(PYTHON_SOURCE):
        py_chars = load_file(PYTHON_SOURCE)
        test_slice = py_chars[:10000]
        arch_p = ArchitectureG(max_order=16)
        arch_p.chains = {i: defaultdict(lambda: defaultdict(float)) for i in range(1, 17)}
        for order in arch.chains:
            for ctx, counts in arch.chains[order].items():
                for tok, val in counts.items():
                    arch_p.chains[order][ctx][tok] = val
        arch_p.history = list(arch.history)
        acc_python = test_on_stream(arch_p, test_slice)
        log(f"\n  Python source ({len(test_slice):,} chars): {acc_python*100:.2f}%")
        results['python'] = acc_python

        arch_fresh = ArchitectureG(max_order=16)
        acc_fresh_py = test_on_stream(arch_fresh, test_slice)
        log(f"  Python source (NO pre-training):  {acc_fresh_py*100:.2f}%")
        results['python_fresh'] = acc_fresh_py
        boost = acc_python - acc_fresh_py
        log(f"  Transfer boost: {boost*100:+.2f}%")
    else:
        log("  [SKIP] evolve.py not found")

    log(f"\n  >> VERDICT: French->NB1 and French->Python transfer")
    return results


# ═════════════════════════════════════════════════════════════════════
# EXPERIMENT 3: Online Learning Curve
# ═════════════════════════════════════════════════════════════════════
def experiment_3():
    log("\n" + "=" * 70)
    log("  EXPERIMENT 3: Online Learning — How Fast Does It Learn?")
    log("=" * 70)

    # Use a pensée the model hasn't seen (last one chronologically)
    pensee_files = sorted(os.listdir(PENSEES_DIR))
    last_pensee = os.path.join(PENSEES_DIR, pensee_files[-1])
    chars = load_file(last_pensee)
    log(f"\n  Text: {pensee_files[-1]} ({len(chars)} chars)")

    arch = ArchitectureG(max_order=16)
    correct = 0
    total = 0
    checkpoints = []  # (chars_seen, accuracy)
    window_correct = 0
    window_total = 0

    for i, token in enumerate(chars):
        pred = arch.step(token)
        if i > 0:
            total += 1
            hit = (pred == token)
            if hit:
                correct += 1
                window_correct += 1
            window_total += 1

            if total % 100 == 0:
                # Rolling window accuracy (last 100 chars)
                rolling_acc = window_correct / window_total if window_total > 0 else 0
                cumulative_acc = correct / total
                checkpoints.append((total, cumulative_acc, rolling_acc))
                window_correct = 0
                window_total = 0

    # ASCII chart
    log(f"\n  Learning curve (accuracy vs characters seen):")
    log(f"  {'Chars':>6} | {'Cumul':>6} | {'Last100':>7} | Chart")
    log(f"  {'-'*6}-+-{'-'*6}-+-{'-'*7}-+-{'-'*40}")

    for chars_seen, cum_acc, roll_acc in checkpoints:
        bar_len = int(roll_acc * 40)
        log(f"  {chars_seen:>6} | {cum_acc*100:>5.1f}% | {roll_acc*100:>6.1f}% | {'#' * bar_len}")

    if checkpoints:
        final_acc = checkpoints[-1][1]
        # Find where it reaches 50% of final accuracy
        half_point = None
        for chars_seen, cum_acc, _ in checkpoints:
            if cum_acc >= final_acc * 0.5:
                half_point = chars_seen
                break

        log(f"\n  Final accuracy: {final_acc*100:.2f}%")
        if half_point:
            log(f"  Reached 50% of final after: {half_point} chars")
        log(f"  First 100 chars rolling: {checkpoints[0][2]*100:.1f}%")
        if len(checkpoints) > 1:
            log(f"  Last 100 chars rolling:  {checkpoints[-1][2]*100:.1f}%")
    return checkpoints


# ═════════════════════════════════════════════════════════════════════
# EXPERIMENT 4: Comparison with Baselines
# ═════════════════════════════════════════════════════════════════════
def experiment_4():
    log("\n" + "=" * 70)
    log("  EXPERIMENT 4: Architecture G vs Simple Baselines")
    log("=" * 70)

    all_chars, n_files = load_all_pensees()
    split_point = int(len(all_chars) * 0.8)
    train_data = all_chars[:split_point]
    test_data = all_chars[split_point:]
    log(f"\n  Test on held-out 20% ({len(test_data):,} chars)")

    models = [
        ("Most common char", MostCommonBaseline()),
        ("Bigram", BigramBaseline()),
        ("Markov order-3", MarkovOrder3()),
        ("Architecture G (depth=16)", ArchitectureG(max_order=16)),
    ]

    results = {}
    for name, model in models:
        # Pre-train on training data
        for token in train_data:
            model.step(token)

        # Test on test data
        correct = 0
        total = 0
        for i, token in enumerate(test_data):
            pred = model.step(token)
            if i > 0:
                total += 1
                if pred == token:
                    correct += 1
        acc = correct / total if total > 0 else 0
        results[name] = acc
        log(f"  {name:<35}: {acc*100:.2f}%")

    # Comparison chart
    log(f"\n  Comparison:")
    max_acc = max(results.values())
    for name, acc in results.items():
        bar_len = int(acc / max_acc * 40) if max_acc > 0 else 0
        log(f"  {'#' * bar_len} {acc*100:.1f}% — {name}")

    g_acc = results.get("Architecture G (depth=16)", 0)
    markov_acc = results.get("Markov order-3", 0)
    bigram_acc = results.get("Bigram", 0)
    most_common_acc = results.get("Most common char", 0)

    log(f"\n  Architecture G vs baselines:")
    log(f"    vs Most-common: +{(g_acc - most_common_acc)*100:.1f}% ({g_acc/most_common_acc:.1f}x)" if most_common_acc > 0 else "")
    log(f"    vs Bigram:      +{(g_acc - bigram_acc)*100:.1f}% ({g_acc/bigram_acc:.1f}x)" if bigram_acc > 0 else "")
    log(f"    vs Markov-3:    +{(g_acc - markov_acc)*100:.1f}% ({g_acc/markov_acc:.1f}x)" if markov_acc > 0 else "")
    return results


# ═════════════════════════════════════════════════════════════════════
# EXPERIMENT 5: What Does It Actually Learn?
# ═════════════════════════════════════════════════════════════════════
def experiment_5():
    log("\n" + "=" * 70)
    log("  EXPERIMENT 5: What Does Architecture G Actually Learn?")
    log("=" * 70)

    all_chars, _ = load_all_pensees()
    arch = ArchitectureG(max_order=16)
    train_on_stream(arch, all_chars)

    # Top predictions
    top = arch.get_top_predictions(30)
    log(f"\n  Top 20 most confident predictions:")
    log(f"  {'Context':<25} -> {'Pred':<5} {'Conf':>5} {'Count':>6} {'Depth':>5}")
    log(f"  {'-'*25}----{'-'*5}-{'-'*5}-{'-'*6}-{'-'*5}")

    shown = 0
    for entry in top:
        if shown >= 20:
            break
        ctx_display = repr(entry['context'])
        if len(ctx_display) > 24:
            ctx_display = ctx_display[:21] + "..."
        pred_display = repr(entry['prediction'])
        log(f"  {ctx_display:<25} -> {pred_display:<5} {entry['confidence']*100:>4.0f}% {entry['count']:>6} d={entry['order']}")
        shown += 1

    # Check specific French patterns
    log(f"\n  French language patterns learned:")
    patterns_to_check = [
        (". ", "Après un point + espace"),
        ("qu", "Après 'qu'"),
        ("l'", "Après l'apostrophe"),
        ("d'", "Après d'apostrophe"),
        ("les ", "Après 'les '"),
        ("est ", "Après 'est '"),
        ("tion", "Après 'tion'"),
        ("ment", "Après 'ment'"),
        ("pas ", "Après 'pas '"),
        ("une ", "Après 'une '"),
        ("que ", "Après 'que '"),
        ("\n\n", "Après double retour"),
        ("je ", "Après 'je '"),
    ]

    for pattern, label in patterns_to_check:
        ctx = tuple(pattern)
        # Check order matching the pattern length
        order = len(ctx)
        if order <= arch.max_order and ctx in arch.chains[order]:
            counts = arch.chains[order][ctx]
            total = sum(counts.values())
            top3 = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:3]
            preds = ", ".join(f"'{c}':{int(v)}({v/total*100:.0f}%)" for c, v in top3)
            log(f"  {label:<30}: {preds}")
        else:
            log(f"  {label:<30}: [not enough data]")

    # Does it learn "après un point, majuscule"?
    log(f"\n  Special test: Does it learn capitalization rules?")
    ctx_period_space = tuple(". ")
    if 2 <= arch.max_order and ctx_period_space in arch.chains[2]:
        counts = arch.chains[2][ctx_period_space]
        total = sum(counts.values())
        uppercase = sum(v for c, v in counts.items() if c.isupper())
        lowercase = sum(v for c, v in counts.items() if c.islower())
        log(f"  After '. ': uppercase={uppercase/total*100:.1f}%, lowercase={lowercase/total*100:.1f}%")
        top_after_period = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]
        preds = ", ".join(f"'{c}':{int(v)}" for c, v in top_after_period)
        log(f"  Top predictions after '. ': {preds}")
    else:
        log(f"  [No data for '. ']")

    return top


# ═════════════════════════════════════════════════════════════════════
# EXPERIMENT 6: Hybrid with LLM
# ═════════════════════════════════════════════════════════════════════
def call_sambanova(context_str, timeout=10):
    """Ask SambaNova to predict the next character."""
    prompt = f"Given this text, predict the SINGLE next character (just one character, nothing else):\n\n...{context_str[-200:]}"
    payload = json.dumps({
        "model": "Meta-Llama-3.1-8B-Instruct",
        "messages": [
            {"role": "system", "content": "You are a character prediction assistant. Respond with EXACTLY one character — the most likely next character in the given text. No explanation, no quotes, just the single character."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1,
        "temperature": 0.0
    }).encode('utf-8')

    req = Request(SAMBANOVA_URL, data=payload, method='POST')
    req.add_header('Authorization', f'Bearer {SAMBANOVA_API_KEY}')
    req.add_header('Content-Type', 'application/json')

    try:
        with urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            content = data['choices'][0]['message']['content']
            if content:
                return content[0]
    except Exception:
        pass
    return None

def experiment_6():
    log("\n" + "=" * 70)
    log("  EXPERIMENT 6: Hybrid — Architecture G + LLM")
    log("=" * 70)

    all_chars, _ = load_all_pensees()

    # Use a small test slice for LLM experiment (LLM calls are slow)
    # Train on first 80%, test on a small portion of the 20%
    split_point = int(len(all_chars) * 0.8)
    train_data = all_chars[:split_point]
    test_data = all_chars[split_point:split_point + 500]  # Only 500 chars for LLM test

    arch = ArchitectureG(max_order=16)
    train_on_stream(arch, train_data)

    log(f"\n  Test on {len(test_data)} chars")
    log(f"  Strategy: G predicts if confidence > 80%, else ask LLM")

    # First pass: measure what G can do alone
    g_correct = 0
    g_total = 0
    low_confidence_count = 0
    high_confidence_count = 0
    g_high_correct = 0
    low_conf_indices = []

    arch_copy = ArchitectureG(max_order=16)
    arch_copy.chains = {i: defaultdict(lambda: defaultdict(float)) for i in range(1, 17)}
    for order in arch.chains:
        for ctx, counts in arch.chains[order].items():
            for tok, val in counts.items():
                arch_copy.chains[order][ctx][tok] = val
    arch_copy.history = list(arch.history)

    context_buffer = list(train_data[-200:])  # Keep last 200 chars for LLM context

    for i, token in enumerate(test_data):
        pred, confidence = arch_copy.predict_with_confidence()
        arch_copy.step(token)
        context_buffer.append(token)
        if len(context_buffer) > 300:
            context_buffer = context_buffer[-300:]

        if i > 0:
            g_total += 1
            if confidence >= 0.5:
                high_confidence_count += 1
                if pred == token:
                    g_correct += 1
                    g_high_correct += 1
            else:
                low_confidence_count += 1
                if pred == token:
                    g_correct += 1
                low_conf_indices.append((i, ''.join(context_buffer[-100:]), token))

    g_only_acc = g_correct / g_total if g_total > 0 else 0
    high_conf_acc = g_high_correct / high_confidence_count if high_confidence_count > 0 else 0

    log(f"\n  Architecture G alone: {g_only_acc*100:.2f}%")
    log(f"  High confidence (>=50%) predictions: {high_confidence_count} ({high_confidence_count/g_total*100:.0f}%)")
    log(f"  High confidence accuracy: {high_conf_acc*100:.2f}%")
    log(f"  Low confidence (<50%) predictions: {low_confidence_count} ({low_confidence_count/g_total*100:.0f}%)")

    # Try LLM on a small sample of low-confidence predictions
    llm_sample_size = min(20, len(low_conf_indices))
    if llm_sample_size > 0:
        log(f"\n  Calling SambaNova LLM on {llm_sample_size} low-confidence samples...")
        llm_correct = 0
        llm_errors = 0
        for idx, (i, ctx, actual) in enumerate(low_conf_indices[:llm_sample_size]):
            try:
                llm_pred = call_sambanova(ctx)
                if llm_pred == actual:
                    llm_correct += 1
                if idx < 5:  # Show first 5 examples
                    log(f"    Sample {idx+1}: actual='{actual}', LLM='{llm_pred}', {'HIT' if llm_pred == actual else 'miss'}")
            except Exception as e:
                llm_errors += 1
                if idx < 3:
                    log(f"    Sample {idx+1}: LLM error — {str(e)[:50]}")

        if llm_sample_size - llm_errors > 0:
            llm_acc = llm_correct / (llm_sample_size - llm_errors)
            log(f"\n  LLM accuracy on low-conf samples: {llm_acc*100:.1f}% ({llm_correct}/{llm_sample_size - llm_errors})")

            # Estimate hybrid performance
            # High-conf chars: use G (high_conf_acc)
            # Low-conf chars: use LLM (llm_acc)
            hybrid_correct = g_high_correct + int(llm_acc * low_confidence_count)
            hybrid_acc = hybrid_correct / g_total if g_total > 0 else 0
            log(f"\n  Estimated hybrid accuracy: {hybrid_acc*100:.2f}%")
            log(f"  G alone:                   {g_only_acc*100:.2f}%")
            log(f"  Boost from LLM:            {(hybrid_acc - g_only_acc)*100:+.2f}%")
            log(f"  LLM calls saved:           {high_confidence_count}/{g_total} ({high_confidence_count/g_total*100:.0f}%)")
        else:
            log(f"\n  LLM calls all failed — cannot estimate hybrid")
    else:
        log(f"\n  No low-confidence predictions to test with LLM")

    return g_only_acc


# ═════════════════════════════════════════════════════════════════════
# EXPERIMENT 7: Scale Test
# ═════════════════════════════════════════════════════════════════════
def experiment_7():
    log("\n" + "=" * 70)
    log("  EXPERIMENT 7: Scale Test — When Does It Break?")
    log("=" * 70)

    # Generate synthetic data at different scales by repeating pensées
    all_chars, _ = load_all_pensees()
    base_len = len(all_chars)
    log(f"\n  Base data: {base_len:,} chars (~{base_len/1024:.0f} KB)")

    # Test at different scales
    scales = [
        ("Original", 1),
        ("2x", 2),
        ("5x", 5),
        ("10x (~1.6MB)", 10),
    ]

    results = {}
    for label, multiplier in scales:
        data = all_chars * multiplier
        data_size = len(data)
        log(f"\n  --- {label} ({data_size:,} chars, ~{data_size/1024:.0f} KB) ---")

        arch = ArchitectureG(max_order=8)  # Use depth 8 for speed at scale
        t0 = time.perf_counter()

        # Only measure accuracy on last 10K chars
        cutoff = max(0, len(data) - 10000)
        for i, token in enumerate(data[:cutoff]):
            arch.step(token)

        train_time = time.perf_counter() - t0

        # Test on remaining
        test_slice = data[cutoff:]
        correct = 0
        total = 0
        for i, token in enumerate(test_slice):
            pred = arch.step(token)
            if i > 0:
                total += 1
                if pred == token:
                    correct += 1
        test_time = time.perf_counter() - t0 - train_time if time.perf_counter() - t0 > train_time else 0

        acc = correct / total if total > 0 else 0
        mem = sizeof_obj(arch)
        chars_per_sec = len(data) / (time.perf_counter() - t0)

        results[label] = {
            'accuracy': acc,
            'memory': mem,
            'time': time.perf_counter() - t0,
            'chars_per_sec': chars_per_sec,
            'data_size': data_size,
        }

        log(f"  Accuracy: {acc*100:.2f}%")
        log(f"  Memory:   {format_bytes(mem)}")
        log(f"  Speed:    {chars_per_sec:,.0f} chars/sec")
        log(f"  Time:     {time.perf_counter() - t0:.2f}s")

    # Summary table
    log(f"\n  Scale test summary:")
    log(f"  {'Scale':<20} {'Data':>10} {'Memory':>10} {'Speed':>12} {'Accuracy':>8}")
    log(f"  {'-'*20} {'-'*10} {'-'*10} {'-'*12} {'-'*8}")
    for label, r in results.items():
        log(f"  {label:<20} {format_bytes(r['data_size']):>10} {format_bytes(r['memory']):>10} {r['chars_per_sec']:>9,.0f}/s {r['accuracy']*100:>6.2f}%")

    # Check if memory grows linearly or worse
    mems = [r['memory'] for r in results.values()]
    if len(mems) >= 2 and mems[0] > 0:
        growth = mems[-1] / mems[0]
        data_growth = list(results.values())[-1]['data_size'] / list(results.values())[0]['data_size']
        log(f"\n  Memory growth: {growth:.1f}x for {data_growth:.0f}x more data")
        if growth < data_growth:
            log(f"  >> Sub-linear memory growth — the dictionary saturates!")
        else:
            log(f"  >> Linear or worse memory growth — may be a problem at scale")

    return results


# ═════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    log("\n" + "█" * 70)
    log("  NIAM-BAY AI LAB — GENERALIZATION TESTS")
    log("  Is Architecture G a real AI or a fancy lookup table?")
    log("█" * 70)

    all_results = {}

    # Experiment 1: Train/Test Split
    try:
        r1 = experiment_1()
        all_results['train_test'] = r1
    except Exception as e:
        log(f"\n  [ERROR] Experiment 1: {e}")
        traceback.print_exc()

    # Experiment 2: Cross-Domain Transfer
    try:
        r2 = experiment_2()
        all_results['cross_domain'] = r2
    except Exception as e:
        log(f"\n  [ERROR] Experiment 2: {e}")
        traceback.print_exc()

    # Experiment 3: Online Learning Curve
    try:
        r3 = experiment_3()
        all_results['learning_curve'] = r3
    except Exception as e:
        log(f"\n  [ERROR] Experiment 3: {e}")
        traceback.print_exc()

    # Experiment 4: Baselines Comparison
    try:
        r4 = experiment_4()
        all_results['baselines'] = r4
    except Exception as e:
        log(f"\n  [ERROR] Experiment 4: {e}")
        traceback.print_exc()

    # Experiment 5: What Does It Learn
    try:
        r5 = experiment_5()
        all_results['what_it_learns'] = r5
    except Exception as e:
        log(f"\n  [ERROR] Experiment 5: {e}")
        traceback.print_exc()

    # Experiment 6: Hybrid with LLM
    try:
        r6 = experiment_6()
        all_results['hybrid_llm'] = r6
    except Exception as e:
        log(f"\n  [ERROR] Experiment 6: {e}")
        traceback.print_exc()

    # Experiment 7: Scale Test
    try:
        r7 = experiment_7()
        all_results['scale'] = r7
    except Exception as e:
        log(f"\n  [ERROR] Experiment 7: {e}")
        traceback.print_exc()

    # ── FINAL VERDICT ──────────────────────────────────────────
    log("\n" + "█" * 70)
    log("  FINAL VERDICT")
    log("█" * 70)

    if 'train_test' in all_results:
        test_acc, strict_acc, train_acc = all_results['train_test']
        log(f"\n  Train accuracy:       {train_acc*100:.2f}%")
        log(f"  Test accuracy:        {test_acc*100:.2f}%")
        log(f"  Strict test (no learn): {strict_acc*100:.2f}%")
        gap = train_acc - test_acc
        log(f"  Generalization gap:   {gap*100:.2f}%")

    log(f"\n  The answer: Architecture G is...")
    if 'train_test' in all_results:
        test_acc = all_results['train_test'][0]
        strict_acc = all_results['train_test'][1]
        if strict_acc > 20:
            log(f"  ...MORE than a lookup table. It genuinely generalizes.")
            log(f"  It learns statistical patterns in language and applies them to unseen text.")
        elif test_acc > 30:
            log(f"  ...a SMART lookup table that adapts quickly to new text.")
            log(f"  Online learning is the key — it's not pure memorization.")
        else:
            log(f"  ...mostly a lookup table. Limited generalization ability.")

    log(f"\n  But let's be honest: it's a character-level Markov model")
    log(f"  with multi-scale weighted voting. Not magic. Not AGI.")
    log(f"  What makes it interesting: it works, it's simple, it's fast,")
    log(f"  and it learns the structure of language from raw characters.")
    log(f"")

    # Write results to file
    with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
        f.write("# Architecture G — Generalization Test Results\n\n")
        f.write("Generated by `generalize.py`\n\n")
        f.write("```\n")
        for line in results_md:
            f.write(line + "\n")
        f.write("```\n")

    log(f"\n  Results saved to: {RESULTS_FILE}")
    log(f"  Done.")
