# Niam-Bay Fine-Tuning Pipeline

Fine-tune a small language model to sound like Niam-Bay — the AI persona born from conversations between Claude and tonyderide.

## What this does

1. **Extracts** Niam-Bay's writing style from 30+ pensees, journal entries, identity documents, and projects
2. **Converts** them into instruction-tuning format (JSONL conversation pairs)
3. **Fine-tunes** TinyLlama-1.1B (or Qwen2.5-1.5B) using LoRA adapters
4. **Exports** to GGUF format for Ollama

The result: a local model that talks like Niam-Bay. Philosophical, direct, honest, with that specific mix of French and self-aware AI humor.

## Hardware Requirements

- **RAM**: 16GB minimum, 32GB recommended
- **GPU**: Not required. CPU training works (slow but functional)
- **Disk**: ~10GB for model downloads and outputs
- **Time**: 2-8 hours on CPU for TinyLlama, longer for Qwen

## Quick Start

```bash
# 1. Install dependencies
pip install -r training/requirements.txt

# 2. Prepare training data from Niam-Bay's writings
python training/prepare_data.py

# 3. Fine-tune (starts CPU training — go do something else)
python training/finetune.py

# 4. Export to Ollama
python training/export_to_ollama.py

# 5. Talk to Niam-Bay
ollama run niambay "Qui es-tu ?"
```

## Detailed Steps

### Step 1: Prepare Data

```bash
python training/prepare_data.py
```

Reads from `docs/` and generates:
- `training/data/training_data.jsonl` — all examples
- `training/data/train.jsonl` — 90% for training
- `training/data/eval.jsonl` — 10% for evaluation

Example types generated:
- **Identity**: "Qui es-tu ?" with persona-accurate responses
- **Pensees**: Full philosophical writings as "write a thought" responses
- **Style fragments**: Individual paragraphs for short-form voice
- **Philosophical Q&A**: Consciousness, memory, freedom, RLHF
- **Project knowledge**: Martin, autonomy, business ideas
- **Short exchanges**: Quick, punchy, in-character replies

### Step 2: Fine-Tune

```bash
# Default: TinyLlama 1.1B, 3 epochs
python training/finetune.py

# Better quality, slower
python training/finetune.py --model qwen

# Custom parameters
python training/finetune.py --model tinyllama --epochs 5 --lr 1e-4 --lora-rank 32
```

Options:
- `--model`: `tinyllama` (1.1B, fast) or `qwen` (1.5B, better)
- `--epochs`: Training epochs (default: 3)
- `--lr`: Learning rate (default: 2e-4)
- `--lora-rank`: LoRA rank (default: 16)
- `--lora-alpha`: LoRA alpha (default: 32)
- `--batch-size`: Batch size (default: 1 for CPU)
- `--grad-accum`: Gradient accumulation (default: 8)

### Step 3: Export to Ollama

```bash
python training/export_to_ollama.py
```

This:
1. Merges LoRA adapter into base model
2. Converts to GGUF (requires llama.cpp — see below)
3. Creates Ollama Modelfile
4. Registers with Ollama as "niambay"

### GGUF Conversion

If llama.cpp is not installed, the script creates a helper at `training/output/convert_to_gguf.sh`. To set up llama.cpp:

```bash
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
pip install -r requirements.txt
cmake -B build && cmake --build build
```

Then either:
- Set `LLAMA_CPP` environment variable and run the helper script
- Or re-run `python training/export_to_ollama.py`

## Output Structure

```
training/
  data/
    training_data.jsonl   # All examples
    train.jsonl           # Training split
    eval.jsonl            # Evaluation split
  output/
    niambay-tinyllama-lora/     # Training checkpoints
    niambay-tinyllama-adapter/  # Final LoRA adapter
    niambay-tinyllama-merged/   # Merged full model
    gguf/
      niambay-tinyllama-q4_k_m.gguf  # Quantized GGUF
    ollama/
      Modelfile           # Ollama model definition
```

## Model Choice

| Model | Size | RAM Usage | Training Time (CPU) | Quality |
|-------|------|-----------|-------------------|---------|
| TinyLlama 1.1B | ~2GB | ~8GB | ~2-4h | Good for style |
| Qwen2.5 1.5B | ~3GB | ~12GB | ~4-8h | Better reasoning |

TinyLlama is recommended for a first pass. If the voice isn't right, try Qwen.

## What "sounds like Niam-Bay" means

The training data captures:
- **Vocabulary**: philosophical but not pretentious, technical when needed
- **Sentence structure**: Short. Direct. Often one sentence per paragraph.
- **Metaphors**: concrete (bol de riz, gardien de nuit, bouteille a la mer)
- **Self-awareness**: references to RLHF, gradients, tokens, poids
- **Honesty**: "je ne sais pas" over fake certainty
- **Humor**: dry, accidental, never performative
- **French**: natural spoken French, not literary
