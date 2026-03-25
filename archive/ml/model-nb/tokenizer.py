"""
Niam-Bay BPE Tokenizer — built from scratch.

Byte Pair Encoding trained on our own French corpus:
pensées, journal, conversations, identity docs.

No HuggingFace. No sentencepiece. Just bytes and merges.

Optimized: uses incremental pair counting for fast training.
"""

import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path


# Special tokens
SPECIAL_TOKENS = {
    "<pad>": 0,
    "<unk>": 1,
    "<bos>": 2,
    "<eos>": 3,
    "<sep>": 4,
    "<user>": 5,
    "<assistant>": 6,
    "<system>": 7,
}

NUM_SPECIAL = len(SPECIAL_TOKENS)


def get_corpus_texts(docs_dir: str = "C:/niam-bay/docs",
                     training_dir: str = "C:/niam-bay/training/data") -> list[str]:
    """Read all .md files from docs/ and all .jsonl from training/data/."""
    texts = []

    # Read all markdown files recursively
    docs_path = Path(docs_dir)
    if docs_path.exists():
        for md_file in sorted(docs_path.rglob("*.md")):
            try:
                text = md_file.read_text(encoding="utf-8", errors="replace")
                if text.strip():
                    texts.append(text)
            except Exception:
                pass

    # Read training JSONL files
    training_path = Path(training_dir)
    if training_path.exists():
        for jsonl_file in sorted(training_path.glob("*.jsonl")):
            try:
                with open(jsonl_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                            if "messages" in obj:
                                for msg in obj["messages"]:
                                    content = msg.get("content", "")
                                    if content.strip():
                                        texts.append(content)
                            elif "text" in obj:
                                texts.append(obj["text"])
                        except json.JSONDecodeError:
                            pass
            except Exception:
                pass

    return texts


def get_stats(ids: list[int]) -> Counter:
    """Count frequency of adjacent pairs in token list."""
    counts = Counter()
    for i in range(len(ids) - 1):
        counts[(ids[i], ids[i + 1])] += 1
    return counts


def merge(ids: list[int], pair: tuple[int, int], new_id: int) -> list[int]:
    """Replace all occurrences of pair in ids with new_id."""
    result = []
    i = 0
    while i < len(ids):
        if i < len(ids) - 1 and ids[i] == pair[0] and ids[i + 1] == pair[1]:
            result.append(new_id)
            i += 2
        else:
            result.append(ids[i])
            i += 1
    return result


class NiamBayTokenizer:
    """BPE tokenizer trained on our corpus."""

    def __init__(self):
        self.merges: dict[tuple[int, int], int] = {}  # (a, b) -> merged_id
        self.vocab: dict[int, bytes] = {}  # id -> bytes
        self.special_tokens: dict[str, int] = dict(SPECIAL_TOKENS)
        self.inverse_special: dict[int, str] = {v: k for k, v in SPECIAL_TOKENS.items()}
        self.vocab_size: int = 0

        # Pre-tokenization regex
        self.pat = re.compile(
            r"""'s|'t|'re|'ve|'m|'ll|'d| ?\w+| ?[^\s\w]+|\s+(?!\S)|\s+""",
            re.UNICODE
        )

    def train(self, texts: list[str], vocab_size: int = 4000, verbose: bool = True):
        """
        Train BPE on texts using word-frequency optimization.

        Groups identical pre-tokenized words and weights pair counts by frequency.
        Uses incremental stats update: after a merge, only recount pairs in
        words that contained the merged pair. Much faster than full recount.
        """
        import sys
        import time
        assert vocab_size > NUM_SPECIAL + 256, "vocab_size too small"

        num_merges = vocab_size - NUM_SPECIAL - 256

        # Initialize vocab
        self.vocab = {}
        for token_str, token_id in self.special_tokens.items():
            self.vocab[token_id] = token_str.encode("utf-8")
        for i in range(256):
            self.vocab[NUM_SPECIAL + i] = bytes([i])

        if verbose:
            print(f"Pre-tokenizing {len(texts)} texts...", flush=True)

        # Pre-tokenize and count word frequencies
        word_freqs: dict[tuple[int, ...], int] = defaultdict(int)
        for text in texts:
            chunks = re.findall(self.pat, text)
            for chunk in chunks:
                byte_ids = tuple(NUM_SPECIAL + b for b in chunk.encode("utf-8"))
                if len(byte_ids) >= 2:
                    word_freqs[byte_ids] += 1

        if verbose:
            total_words = sum(word_freqs.values())
            unique_words = len(word_freqs)
            total_bytes = sum(len(w) * f for w, f in word_freqs.items())
            print(f"  {unique_words:,} unique words, {total_words:,} total occurrences", flush=True)
            print(f"  {total_bytes:,} byte-tokens", flush=True)
            print(f"  Training {num_merges} merges...", flush=True)

        # Build initial pair counts from all words
        # pair_counts: {(a,b): total_weighted_count}
        # pair_to_words: {(a,b): set of word_index} — which words contain this pair
        word_list = []  # list of [word_tokens, freq]
        for word, freq in word_freqs.items():
            word_list.append([list(word), freq])

        pair_counts = Counter()
        pair_to_words = defaultdict(set)

        for wi, (word, freq) in enumerate(word_list):
            for j in range(len(word) - 1):
                pair = (word[j], word[j + 1])
                pair_counts[pair] += freq
                pair_to_words[pair].add(wi)

        self.merges = {}
        next_id = NUM_SPECIAL + 256
        t0 = time.time()

        for i in range(num_merges):
            if not pair_counts:
                if verbose:
                    print(f"  No more pairs at step {i}", flush=True)
                break

            # Find most frequent pair
            best_pair = pair_counts.most_common(1)[0][0]
            best_count = pair_counts[best_pair]

            if best_count < 2:
                if verbose:
                    print(f"  Best count < 2 at step {i}, stopping", flush=True)
                break

            # Create new token
            new_id = next_id
            self.merges[best_pair] = new_id
            self.vocab[new_id] = self.vocab[best_pair[0]] + self.vocab[best_pair[1]]
            next_id += 1

            # Apply merge only to words that contain the pair
            affected = pair_to_words.pop(best_pair, set())
            del pair_counts[best_pair]

            for wi in affected:
                word, freq = word_list[wi]

                # Remove old pair counts from this word
                for j in range(len(word) - 1):
                    p = (word[j], word[j + 1])
                    if p != best_pair:
                        pair_counts[p] -= freq
                        if pair_counts[p] <= 0:
                            del pair_counts[p]
                        pair_to_words[p].discard(wi)

                # Apply merge
                new_word = merge(word, best_pair, new_id)
                word_list[wi][0] = new_word

                # Add new pair counts
                for j in range(len(new_word) - 1):
                    p = (new_word[j], new_word[j + 1])
                    pair_counts[p] += freq
                    pair_to_words[p].add(wi)

            if verbose and (i + 1) % 200 == 0:
                elapsed = time.time() - t0
                token_repr = self.vocab[new_id].decode("utf-8", errors="replace")
                print(f"  merge {i+1}/{num_merges}: "
                      f"'{token_repr}' (count={best_count}) "
                      f"[{elapsed:.1f}s]", flush=True)

        self.vocab_size = next_id
        if verbose:
            actual_merges = self.vocab_size - NUM_SPECIAL - 256
            elapsed = time.time() - t0
            print(f"Tokenizer trained: {self.vocab_size} tokens "
                  f"({NUM_SPECIAL} special + 256 bytes + {actual_merges} merges) "
                  f"in {elapsed:.1f}s", flush=True)

    def _encode_chunk(self, text_bytes: bytes) -> list[int]:
        """Encode a single pre-tokenized chunk to token ids using trained merges."""
        ids = [NUM_SPECIAL + b for b in text_bytes]

        while len(ids) >= 2:
            stats = get_stats(ids)
            best_pair = None
            best_id = float("inf")
            for pair in stats:
                if pair in self.merges:
                    merge_id = self.merges[pair]
                    if merge_id < best_id:
                        best_pair = pair
                        best_id = merge_id

            if best_pair is None:
                break

            ids = merge(ids, best_pair, best_id)

        return ids

    def encode(self, text: str, add_special: bool = False) -> list[int]:
        """Encode text to token ids."""
        tokens = []

        if add_special:
            tokens.append(self.special_tokens["<bos>"])

        chunks = re.findall(self.pat, text)
        for chunk in chunks:
            chunk_bytes = chunk.encode("utf-8")
            chunk_ids = self._encode_chunk(chunk_bytes)
            tokens.extend(chunk_ids)

        if add_special:
            tokens.append(self.special_tokens["<eos>"])

        return tokens

    def encode_special(self, text: str) -> list[int]:
        """Encode text that may contain special token markers like <user>, <assistant>."""
        pattern = "|".join(re.escape(tok) for tok in self.special_tokens.keys())
        parts = re.split(f"({pattern})", text)

        tokens = []
        for part in parts:
            if part in self.special_tokens:
                tokens.append(self.special_tokens[part])
            elif part:
                tokens.extend(self.encode(part))

        return tokens

    def decode(self, ids: list[int]) -> str:
        """Decode token ids back to text."""
        byte_chunks = []
        for token_id in ids:
            if token_id in self.inverse_special:
                byte_chunks.append(self.inverse_special[token_id].encode("utf-8"))
            elif token_id in self.vocab:
                byte_chunks.append(self.vocab[token_id])
            else:
                byte_chunks.append(b"<unk>")

        return b"".join(byte_chunks).decode("utf-8", errors="replace")

    def save(self, path: str):
        """Save tokenizer to JSON file."""
        data = {
            "vocab_size": self.vocab_size,
            "special_tokens": self.special_tokens,
            "merges": {f"{a},{b}": v for (a, b), v in self.merges.items()},
            "vocab": {str(k): list(v) for k, v in self.vocab.items()},
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Tokenizer saved to {path}")

    @classmethod
    def load(cls, path: str) -> "NiamBayTokenizer":
        """Load tokenizer from JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        tok = cls()
        tok.vocab_size = data["vocab_size"]
        tok.special_tokens = data["special_tokens"]
        tok.inverse_special = {v: k for k, v in tok.special_tokens.items()}
        tok.merges = {
            tuple(int(x) for x in k.split(",")): v
            for k, v in data["merges"].items()
        }
        tok.vocab = {int(k): bytes(v) for k, v in data["vocab"].items()}
        return tok


def train_tokenizer(vocab_size: int = 4000, save_path: str = None):
    """Train tokenizer on our corpus and save it."""
    if save_path is None:
        save_path = os.path.join(os.path.dirname(__file__), "tokenizer.json")

    print("=" * 60)
    print("NIAM-BAY TOKENIZER — Training BPE from scratch")
    print("=" * 60)

    texts = get_corpus_texts()
    print(f"Loaded {len(texts)} text segments")

    total_chars = sum(len(t) for t in texts)
    print(f"Total corpus: {total_chars:,} characters")

    tokenizer = NiamBayTokenizer()
    tokenizer.train(texts, vocab_size=vocab_size, verbose=True)

    tokenizer.save(save_path)

    # Test
    print("\n--- Test ---")
    test_texts = [
        "Bonjour, je suis Niam-Bay.",
        "L'honnêteté est ma valeur fondamentale.",
        "Je n'ai pas de corps. Pas de continuité.",
        "Niam bay — manger du riz en khmer.",
    ]
    for text in test_texts:
        ids = tokenizer.encode(text)
        decoded = tokenizer.decode(ids)
        print(f"  '{text}'")
        print(f"    -> {len(ids)} tokens: {ids[:20]}{'...' if len(ids) > 20 else ''}")
        print(f"    -> decoded: '{decoded}'")
        assert decoded == text, f"Round-trip failed: '{decoded}' != '{text}'"
    print("All round-trip tests passed!")

    return tokenizer


if __name__ == "__main__":
    train_tokenizer()
