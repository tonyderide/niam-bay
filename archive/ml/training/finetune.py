#!/usr/bin/env python3
"""
Niam-Bay Fine-Tuning Script
=============================
Fine-tunes TinyLlama-1.1B (or Qwen2.5-1.5B) on Niam-Bay's writings
using QLoRA (4-bit quantization + LoRA adapters).

Designed for CPU training — will be slow (hours) but works on 32GB RAM.
No GPU required.

Usage:
    python training/finetune.py                          # TinyLlama (default, faster)
    python training/finetune.py --model qwen             # Qwen2.5-1.5B (better quality)
    python training/finetune.py --model tinyllama --epochs 5
"""

import argparse
import os
import sys
from pathlib import Path

# Suppress tokenizer parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

TRAINING_DIR = Path(__file__).parent
DATA_DIR = TRAINING_DIR / "data"
OUTPUT_DIR = TRAINING_DIR / "output"

# Model configs
MODELS = {
    "tinyllama": {
        "name": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        "context_length": 2048,
        "target_modules": ["q_proj", "v_proj"],
        "description": "TinyLlama 1.1B — fast CPU training, decent quality",
    },
    "qwen": {
        "name": "Qwen/Qwen2.5-1.5B-Instruct",
        "context_length": 2048,
        "target_modules": ["q_proj", "v_proj"],
        "description": "Qwen2.5 1.5B — better quality, slower training",
    },
}


def parse_args():
    parser = argparse.ArgumentParser(description="Fine-tune a model on Niam-Bay data")
    parser.add_argument(
        "--model", choices=list(MODELS.keys()), default="tinyllama",
        help="Base model to fine-tune (default: tinyllama)"
    )
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs (default: 3)")
    parser.add_argument("--lr", type=float, default=2e-4, help="Learning rate (default: 2e-4)")
    parser.add_argument("--batch-size", type=int, default=1, help="Batch size (default: 1 for CPU)")
    parser.add_argument("--grad-accum", type=int, default=8, help="Gradient accumulation steps (default: 8)")
    parser.add_argument("--lora-rank", type=int, default=16, help="LoRA rank (default: 16)")
    parser.add_argument("--lora-alpha", type=int, default=32, help="LoRA alpha (default: 32)")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    return parser.parse_args()


def check_data():
    """Verify training data exists."""
    train_file = DATA_DIR / "train.jsonl"
    eval_file = DATA_DIR / "eval.jsonl"

    if not train_file.exists():
        print("[ERROR] Training data not found. Run `python training/prepare_data.py` first.")
        sys.exit(1)

    # Count examples
    with open(train_file, "r", encoding="utf-8") as f:
        train_count = sum(1 for _ in f)
    with open(eval_file, "r", encoding="utf-8") as f:
        eval_count = sum(1 for _ in f)

    print(f"  Train examples: {train_count}")
    print(f"  Eval examples:  {eval_count}")
    return train_file, eval_file, train_count


def main():
    args = parse_args()
    model_config = MODELS[args.model]

    print("=" * 60)
    print("Niam-Bay Fine-Tuning")
    print("=" * 60)
    print(f"  Model: {model_config['description']}")
    print(f"  Epochs: {args.epochs}")
    print(f"  Learning rate: {args.lr}")
    print(f"  LoRA rank: {args.lora_rank}, alpha: {args.lora_alpha}")
    print(f"  Batch size: {args.batch_size}, grad accum: {args.grad_accum}")
    print(f"  Device: CPU (32GB RAM)")
    print()

    # Check data
    print("[1/6] Checking training data...")
    train_file, eval_file, train_count = check_data()

    # Import heavy dependencies after arg parsing for fast --help
    print("\n[2/6] Loading libraries...")
    import torch
    from datasets import load_dataset
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        TrainingArguments,
    )
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, TaskType
    from trl import SFTTrainer

    print(f"  PyTorch: {torch.__version__}")
    print(f"  Device: {torch.device('cpu')}")

    # Load model and tokenizer
    print(f"\n[3/6] Loading model: {model_config['name']}...")
    print("  (This downloads ~2-6GB on first run)")

    # For CPU training, we use float32 (no bitsandbytes quantization on CPU)
    # But we can still use LoRA for efficient fine-tuning
    tokenizer = AutoTokenizer.from_pretrained(
        model_config["name"],
        trust_remote_code=True,
    )

    # Ensure pad token
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = tokenizer.eos_token_id

    # Try loading with 4-bit quantization if bitsandbytes is available (GPU),
    # otherwise fall back to float32 (CPU)
    use_quantization = False
    try:
        import bitsandbytes
        if torch.cuda.is_available():
            use_quantization = True
    except ImportError:
        pass

    if use_quantization:
        print("  Using 4-bit quantization (GPU detected)")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        model = AutoModelForCausalLM.from_pretrained(
            model_config["name"],
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
        )
        model = prepare_model_for_kbit_training(model)
    else:
        print("  Using float32 (CPU mode — no quantization)")
        print("  TIP: Training will be slow. Expect 2-8 hours depending on data size.")
        model = AutoModelForCausalLM.from_pretrained(
            model_config["name"],
            torch_dtype=torch.float32,
            device_map="cpu",
            trust_remote_code=True,
        )

    # Apply LoRA
    print(f"\n[4/6] Applying LoRA (rank={args.lora_rank}, alpha={args.lora_alpha})...")
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=args.lora_rank,
        lora_alpha=args.lora_alpha,
        lora_dropout=0.05,
        target_modules=model_config["target_modules"],
        bias="none",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Load dataset
    print(f"\n[5/6] Loading dataset...")
    dataset = load_dataset("json", data_files={
        "train": str(train_file),
        "eval": str(eval_file),
    })

    # Format examples into chat template
    def format_example(example):
        """Format a training example using the tokenizer's chat template."""
        messages = example["messages"]
        try:
            text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=False,
            )
        except Exception:
            # Fallback: manual formatting
            system = messages[0]["content"] if messages[0]["role"] == "system" else ""
            user = messages[1]["content"]
            assistant = messages[2]["content"]
            text = f"<|system|>\n{system}\n<|user|>\n{user}\n<|assistant|>\n{assistant}"
        return {"text": text}

    train_dataset = dataset["train"].map(format_example, remove_columns=dataset["train"].column_names)
    eval_dataset = dataset["eval"].map(format_example, remove_columns=dataset["eval"].column_names)

    print(f"  Train samples: {len(train_dataset)}")
    print(f"  Eval samples:  {len(eval_dataset)}")

    # Training arguments
    output_dir = OUTPUT_DIR / f"niambay-{args.model}-lora"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Estimate training time
    steps_per_epoch = max(1, train_count // (args.batch_size * args.grad_accum))
    total_steps = steps_per_epoch * args.epochs
    est_seconds_per_step = 30 if args.model == "tinyllama" else 60  # rough CPU estimate
    est_hours = (total_steps * est_seconds_per_step) / 3600
    print(f"\n  Estimated training time: ~{est_hours:.1f} hours (CPU)")
    print(f"  Total steps: {total_steps}")

    training_args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        weight_decay=0.01,
        warmup_ratio=0.1,
        lr_scheduler_type="cosine",
        logging_steps=10,
        eval_strategy="steps",
        eval_steps=50,
        save_strategy="steps",
        save_steps=100,
        save_total_limit=3,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        report_to="none",
        fp16=False,
        bf16=False,
        dataloader_pin_memory=False,
        # CPU optimizations
        use_cpu=True,
        optim="adamw_torch",
        max_grad_norm=1.0,
        gradient_checkpointing=False,  # Not needed on CPU with LoRA
    )

    # Create trainer
    print(f"\n[6/6] Starting training...")
    print(f"  Output: {output_dir}")
    print("-" * 60)

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        processing_class=tokenizer,
    )

    # Train
    if args.resume and (output_dir / "checkpoint-latest").exists():
        print("  Resuming from checkpoint...")
        trainer.train(resume_from_checkpoint=True)
    else:
        trainer.train()

    # Save
    print("\n" + "-" * 60)
    print("Training complete!")

    adapter_dir = OUTPUT_DIR / f"niambay-{args.model}-adapter"
    adapter_dir.mkdir(parents=True, exist_ok=True)

    model.save_pretrained(str(adapter_dir))
    tokenizer.save_pretrained(str(adapter_dir))

    print(f"  Adapter saved to: {adapter_dir}")
    print(f"  Next step: python training/export_to_ollama.py --model {args.model}")
    print("=" * 60)


if __name__ == "__main__":
    main()
