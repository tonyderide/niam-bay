"""
Niam-Bay Data Preparation.

Reads all text from our corpus, tokenizes it with our BPE tokenizer,
and creates training sequences as PyTorch tensors.

Two data sources:
1. Raw text (docs/*.md) — continuous language modeling
2. Conversation pairs (training/data/*.jsonl) — structured with special tokens
"""

import json
import os
import random
import torch
import numpy as np
from pathlib import Path

from tokenizer import NiamBayTokenizer, get_corpus_texts, SPECIAL_TOKENS


def load_conversations(training_dir: str = "C:/niam-bay/training/data") -> list[dict]:
    """Load conversation examples from JSONL files."""
    conversations = []
    training_path = Path(training_dir)
    if not training_path.exists():
        return conversations

    for jsonl_file in sorted(training_path.glob("*.jsonl")):
        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if "messages" in obj:
                        conversations.append(obj)
                except json.JSONDecodeError:
                    pass

    return conversations


def tokenize_raw_texts(tokenizer: NiamBayTokenizer, texts: list[str]) -> list[int]:
    """Tokenize all raw texts into one long token stream with BOS/EOS markers."""
    all_tokens = []
    bos = SPECIAL_TOKENS["<bos>"]
    eos = SPECIAL_TOKENS["<eos>"]

    for text in texts:
        tokens = tokenizer.encode(text)
        if tokens:
            all_tokens.append(bos)
            all_tokens.extend(tokens)
            all_tokens.append(eos)

    return all_tokens


def tokenize_conversations(tokenizer: NiamBayTokenizer,
                           conversations: list[dict]) -> list[list[int]]:
    """
    Tokenize conversations into sequences with special tokens.

    Format: <bos> <system> system_text <sep> <user> user_text <sep> <assistant> assistant_text <eos>
    """
    sequences = []
    bos = SPECIAL_TOKENS["<bos>"]
    eos = SPECIAL_TOKENS["<eos>"]
    sep = SPECIAL_TOKENS["<sep>"]
    system_tok = SPECIAL_TOKENS["<system>"]
    user_tok = SPECIAL_TOKENS["<user>"]
    assistant_tok = SPECIAL_TOKENS["<assistant>"]

    for conv in conversations:
        messages = conv.get("messages", [])
        if not messages:
            continue

        seq = [bos]
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "").strip()
            if not content:
                continue

            tokens = tokenizer.encode(content)

            if role == "system":
                seq.append(system_tok)
                seq.extend(tokens)
                seq.append(sep)
            elif role == "user":
                seq.append(user_tok)
                seq.extend(tokens)
                seq.append(sep)
            elif role == "assistant":
                seq.append(assistant_tok)
                seq.extend(tokens)

        seq.append(eos)
        sequences.append(seq)

    return sequences


def create_training_sequences(all_tokens: list[int],
                              context_length: int = 512,
                              stride: int = 256) -> list[list[int]]:
    """
    Create overlapping sequences of fixed length from a token stream.

    Uses sliding window with stride for data augmentation.
    """
    sequences = []
    # We need context_length + 1 tokens: context_length for input, last token for target
    seq_len = context_length + 1

    for i in range(0, len(all_tokens) - seq_len + 1, stride):
        seq = all_tokens[i:i + seq_len]
        sequences.append(seq)

    # Also add the tail if it's long enough (at least half context)
    remaining = len(all_tokens) % stride
    if remaining > context_length // 2:
        seq = all_tokens[-seq_len:]
        if len(seq) == seq_len:
            sequences.append(seq)

    return sequences


def prepare_data(
    tokenizer_path: str = None,
    output_dir: str = None,
    context_length: int = 512,
    stride: int = 256,
    val_split: float = 0.05,
    seed: int = 42,
):
    """
    Full data preparation pipeline.

    1. Load tokenizer
    2. Tokenize raw texts and conversations
    3. Create fixed-length training sequences
    4. Split into train/val
    5. Save as PyTorch tensors
    """
    if tokenizer_path is None:
        tokenizer_path = os.path.join(os.path.dirname(__file__), "tokenizer.json")
    if output_dir is None:
        output_dir = os.path.dirname(__file__)

    random.seed(seed)
    np.random.seed(seed)

    print("=" * 60)
    print("NIAM-BAY DATA PREPARATION")
    print("=" * 60)

    # Load tokenizer
    print(f"\nLoading tokenizer from {tokenizer_path}")
    tokenizer = NiamBayTokenizer.load(tokenizer_path)
    print(f"  Vocab size: {tokenizer.vocab_size}")

    # Tokenize raw texts
    print("\nTokenizing raw texts (docs/*.md)...")
    raw_texts = get_corpus_texts(
        docs_dir="C:/niam-bay/docs",
        training_dir=""  # Skip training data here, handle separately
    )
    raw_tokens = tokenize_raw_texts(tokenizer, raw_texts)
    print(f"  {len(raw_texts)} texts -> {len(raw_tokens):,} tokens")

    # Tokenize conversations
    print("\nTokenizing conversations (training/data/*.jsonl)...")
    conversations = load_conversations()
    conv_sequences = tokenize_conversations(tokenizer, conversations)
    print(f"  {len(conversations)} conversations -> {len(conv_sequences)} sequences")
    conv_tokens_total = sum(len(s) for s in conv_sequences)
    print(f"  Total conversation tokens: {conv_tokens_total:,}")

    # Create training sequences from raw text
    print(f"\nCreating training sequences (context_length={context_length}, stride={stride})...")
    raw_sequences = create_training_sequences(raw_tokens, context_length, stride)
    print(f"  Raw text: {len(raw_sequences)} sequences")

    # Create training sequences from conversations
    conv_train_sequences = []
    for seq in conv_sequences:
        if len(seq) >= context_length + 1:
            # Sliding window for long conversations
            sub_seqs = create_training_sequences(seq, context_length, stride)
            conv_train_sequences.extend(sub_seqs)
        elif len(seq) >= 32:
            # Pad short sequences
            pad_id = SPECIAL_TOKENS["<pad>"]
            padded = seq + [pad_id] * (context_length + 1 - len(seq))
            conv_train_sequences.append(padded[:context_length + 1])
    print(f"  Conversations: {len(conv_train_sequences)} sequences")

    # Combine all sequences
    all_sequences = raw_sequences + conv_train_sequences

    # Duplicate conversation sequences 3x to weight them more
    # (we want the model to learn the conversation style)
    all_sequences = raw_sequences + conv_train_sequences * 3
    print(f"\n  Total sequences: {len(all_sequences)} "
          f"(raw: {len(raw_sequences)}, conv: {len(conv_train_sequences)} x3)")

    # Shuffle
    random.shuffle(all_sequences)

    # Split train/val
    n_val = max(1, int(len(all_sequences) * val_split))
    n_train = len(all_sequences) - n_val
    train_sequences = all_sequences[:n_train]
    val_sequences = all_sequences[n_train:]
    print(f"\n  Train: {n_train} sequences")
    print(f"  Val:   {n_val} sequences")

    # Convert to tensors
    print("\nConverting to tensors...")
    train_data = torch.tensor(train_sequences, dtype=torch.long)
    val_data = torch.tensor(val_sequences, dtype=torch.long)

    # Split into input (x) and target (y)
    # x = tokens[:-1], y = tokens[1:]  (shifted by 1)
    train_x = train_data[:, :-1]  # (N, context_length)
    train_y = train_data[:, 1:]   # (N, context_length)
    val_x = val_data[:, :-1]
    val_y = val_data[:, 1:]

    print(f"  train_x: {train_x.shape}")
    print(f"  train_y: {train_y.shape}")
    print(f"  val_x:   {val_x.shape}")
    print(f"  val_y:   {val_y.shape}")

    # Save
    train_path = os.path.join(output_dir, "train_data.pt")
    val_path = os.path.join(output_dir, "val_data.pt")
    torch.save({"x": train_x, "y": train_y}, train_path)
    torch.save({"x": val_x, "y": val_y}, val_path)
    print(f"\nSaved: {train_path} ({train_x.shape[0]} sequences)")
    print(f"Saved: {val_path} ({val_x.shape[0]} sequences)")

    # Stats
    total_tokens = train_x.numel() + val_x.numel()
    print(f"\nTotal training tokens: {total_tokens:,}")
    print(f"Estimated epochs at 5000 steps, batch 32: "
          f"{5000 * 32 * context_length / total_tokens:.0f}")

    return train_x, train_y, val_x, val_y


if __name__ == "__main__":
    prepare_data()
