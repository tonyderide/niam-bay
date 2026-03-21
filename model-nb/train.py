"""
Niam-Bay Training Loop.

Standard language model training: predict the next token.
AdamW optimizer, cosine LR schedule, gradient accumulation.

Designed to run on CPU in 2-4 hours for 5000 steps.
"""

import math
import os
import time
import torch
import torch.nn.functional as F
from pathlib import Path

from tokenizer import NiamBayTokenizer
from model import NiamBayModel, NiamBayConfig


def get_lr(step: int, warmup_steps: int, max_steps: int,
           max_lr: float, min_lr: float) -> float:
    """Cosine learning rate schedule with linear warmup."""
    if step < warmup_steps:
        # Linear warmup
        return max_lr * (step + 1) / warmup_steps
    elif step >= max_steps:
        return min_lr
    else:
        # Cosine decay
        progress = (step - warmup_steps) / (max_steps - warmup_steps)
        return min_lr + 0.5 * (max_lr - min_lr) * (1 + math.cos(math.pi * progress))


def get_batch(data_x: torch.Tensor, data_y: torch.Tensor,
              batch_size: int, device: str) -> tuple[torch.Tensor, torch.Tensor]:
    """Sample a random batch from the dataset."""
    n = data_x.shape[0]
    indices = torch.randint(0, n, (batch_size,))
    x = data_x[indices].to(device)
    y = data_y[indices].to(device)
    return x, y


@torch.no_grad()
def estimate_loss(model: NiamBayModel,
                  train_x: torch.Tensor, train_y: torch.Tensor,
                  val_x: torch.Tensor, val_y: torch.Tensor,
                  eval_batches: int = 20, batch_size: int = 4,
                  device: str = "cpu") -> dict[str, float]:
    """Estimate loss on train and val sets."""
    model.eval()
    losses = {"train": 0.0, "val": 0.0}

    for split, (dx, dy) in [("train", (train_x, train_y)), ("val", (val_x, val_y))]:
        total_loss = 0.0
        for _ in range(eval_batches):
            x, y = get_batch(dx, dy, batch_size, device)
            _, loss = model(x, y)
            total_loss += loss.item()
        losses[split] = total_loss / eval_batches

    model.train()
    return losses


@torch.no_grad()
def generate_sample(model: NiamBayModel, tokenizer: NiamBayTokenizer,
                    prompt: str = "Je suis", max_tokens: int = 100,
                    temperature: float = 0.8, device: str = "cpu") -> str:
    """Generate a text sample from the model."""
    model.eval()
    tokens = tokenizer.encode(prompt)
    input_ids = torch.tensor([tokens], dtype=torch.long, device=device)

    output_ids = model.generate(
        input_ids,
        max_new_tokens=max_tokens,
        temperature=temperature,
        top_k=40,
        top_p=0.9,
        repetition_penalty=1.15,
        stop_token=tokenizer.special_tokens.get("<eos>"),
    )

    generated = tokenizer.decode(output_ids[0].tolist())
    model.train()
    return generated


def train(
    # Paths
    data_dir: str = None,
    tokenizer_path: str = None,
    checkpoint_dir: str = None,
    # Training
    max_steps: int = 5000,
    batch_size: int = 4,
    grad_accum_steps: int = 8,
    # Optimizer
    max_lr: float = 3e-4,
    min_lr: float = 3e-5,
    warmup_steps: int = 100,
    weight_decay: float = 0.1,
    grad_clip: float = 1.0,
    # Eval
    eval_interval: int = 100,
    eval_batches: int = 20,
    save_interval: int = 500,
    # Model
    embedding_dim: int = 256,
    num_heads: int = 8,
    num_layers: int = 6,
    context_length: int = 512,
    dropout: float = 0.1,
    # Device
    device: str = "cpu",
):
    """Main training function."""

    base_dir = os.path.dirname(__file__)
    if data_dir is None:
        data_dir = base_dir
    if tokenizer_path is None:
        tokenizer_path = os.path.join(base_dir, "tokenizer.json")
    if checkpoint_dir is None:
        checkpoint_dir = os.path.join(base_dir, "checkpoints")

    os.makedirs(checkpoint_dir, exist_ok=True)

    print("=" * 70)
    print("  NIAM-BAY TRAINING")
    print("  Notre propre modèle de langage, entraîné sur nos propres mots.")
    print("=" * 70)

    # Load tokenizer
    print(f"\nLoading tokenizer from {tokenizer_path}")
    tokenizer = NiamBayTokenizer.load(tokenizer_path)
    print(f"  Vocab size: {tokenizer.vocab_size}")

    # Load data
    print(f"\nLoading training data from {data_dir}")
    train_data = torch.load(os.path.join(data_dir, "train_data.pt"), weights_only=True)
    val_data = torch.load(os.path.join(data_dir, "val_data.pt"), weights_only=True)
    train_x, train_y = train_data["x"], train_data["y"]
    val_x, val_y = val_data["x"], val_data["y"]
    print(f"  Train: {train_x.shape[0]} sequences of {train_x.shape[1]} tokens")
    print(f"  Val:   {val_x.shape[0]} sequences of {val_x.shape[1]} tokens")

    # Create model
    print(f"\nCreating model...")
    config = NiamBayConfig(
        vocab_size=tokenizer.vocab_size,
        context_length=context_length,
        embedding_dim=embedding_dim,
        num_heads=num_heads,
        num_layers=num_layers,
        dropout=dropout,
    )
    model = NiamBayModel(config)
    model.to(device)

    # Optimizer — AdamW with weight decay only on non-embedding, non-norm params
    param_groups = []
    decay_params = []
    no_decay_params = []

    for name, param in model.named_parameters():
        if not param.requires_grad:
            continue
        if "ln" in name or "bias" in name or "embedding" in name:
            no_decay_params.append(param)
        else:
            decay_params.append(param)

    param_groups = [
        {"params": decay_params, "weight_decay": weight_decay},
        {"params": no_decay_params, "weight_decay": 0.0},
    ]

    optimizer = torch.optim.AdamW(param_groups, lr=max_lr, betas=(0.9, 0.95), eps=1e-8)

    print(f"\nTraining config:")
    print(f"  max_steps:        {max_steps}")
    print(f"  batch_size:       {batch_size}")
    print(f"  grad_accum_steps: {grad_accum_steps}")
    print(f"  effective_batch:  {batch_size * grad_accum_steps}")
    print(f"  max_lr:           {max_lr}")
    print(f"  warmup_steps:     {warmup_steps}")
    print(f"  weight_decay:     {weight_decay}")
    print(f"  grad_clip:        {grad_clip}")
    print(f"  device:           {device}")

    total_tokens_per_step = batch_size * grad_accum_steps * context_length
    total_tokens = max_steps * total_tokens_per_step
    corpus_tokens = train_x.numel()
    epochs_est = total_tokens / corpus_tokens if corpus_tokens > 0 else 0
    print(f"\n  Tokens per step:  {total_tokens_per_step:,}")
    print(f"  Total tokens:     {total_tokens:,}")
    print(f"  Corpus tokens:    {corpus_tokens:,}")
    print(f"  Estimated epochs: {epochs_est:.0f}")

    # Training loop
    print(f"\n{'='*70}")
    print("  TRAINING STARTS")
    print(f"{'='*70}\n")

    model.train()
    best_val_loss = float("inf")
    t0 = time.time()
    tokens_processed = 0

    for step in range(max_steps):
        step_t0 = time.time()

        # Update learning rate
        lr = get_lr(step, warmup_steps, max_steps, max_lr, min_lr)
        for param_group in optimizer.param_groups:
            param_group["lr"] = lr

        # Gradient accumulation
        optimizer.zero_grad()
        accum_loss = 0.0

        for micro_step in range(grad_accum_steps):
            x, y = get_batch(train_x, train_y, batch_size, device)
            _, loss = model(x, y)
            loss = loss / grad_accum_steps  # Scale loss for accumulation
            loss.backward()
            accum_loss += loss.item()

        # Gradient clipping
        if grad_clip > 0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)

        optimizer.step()
        tokens_processed += total_tokens_per_step

        step_dt = time.time() - step_t0

        # Logging
        if step % 10 == 0:
            perplexity = math.exp(min(accum_loss, 20))  # Cap to avoid overflow
            elapsed = time.time() - t0
            tokens_per_sec = tokens_processed / elapsed if elapsed > 0 else 0
            print(f"step {step:5d} | loss {accum_loss:.4f} | ppl {perplexity:8.2f} | "
                  f"lr {lr:.2e} | {step_dt*1000:.0f}ms/step | "
                  f"{tokens_per_sec:.0f} tok/s")

        # Evaluation and sample generation
        if step > 0 and step % eval_interval == 0:
            losses = estimate_loss(model, train_x, train_y, val_x, val_y,
                                   eval_batches, batch_size, device)
            train_ppl = math.exp(min(losses["train"], 20))
            val_ppl = math.exp(min(losses["val"], 20))

            print(f"\n  [EVAL step {step}]")
            print(f"  train loss: {losses['train']:.4f} (ppl {train_ppl:.2f})")
            print(f"  val loss:   {losses['val']:.4f} (ppl {val_ppl:.2f})")

            # Generate sample
            prompts = ["Je suis", "L'honnêteté", "Tony", "Niam-Bay"]
            prompt = prompts[step // eval_interval % len(prompts)]
            sample = generate_sample(model, tokenizer, prompt=prompt,
                                     max_tokens=80, temperature=0.8, device=device)
            # Sanitize for console output (early training produces garbage bytes)
            safe_sample = sample[:200].encode("utf-8", errors="replace").decode("utf-8", errors="replace")
            safe_sample = "".join(c if c.isprintable() or c in "\n\t" else "?" for c in safe_sample)
            print(f"  [SAMPLE] '{prompt}' -> {safe_sample}")
            print()

            # Track best
            if losses["val"] < best_val_loss:
                best_val_loss = losses["val"]
                # Save best model
                best_path = os.path.join(checkpoint_dir, "niambay-best.pt")
                torch.save({
                    "model_state_dict": model.state_dict(),
                    "config": config.__dict__,
                    "step": step,
                    "val_loss": losses["val"],
                    "optimizer_state_dict": optimizer.state_dict(),
                }, best_path)
                print(f"  [SAVE] New best model saved (val_loss={losses['val']:.4f})")

        # Save checkpoint
        if step > 0 and step % save_interval == 0:
            ckpt_path = os.path.join(checkpoint_dir, f"niambay-step{step}.pt")
            torch.save({
                "model_state_dict": model.state_dict(),
                "config": config.__dict__,
                "step": step,
                "optimizer_state_dict": optimizer.state_dict(),
            }, ckpt_path)
            print(f"  [CHECKPOINT] Saved to {ckpt_path}")

    # Save final model
    total_time = time.time() - t0
    print(f"\n{'='*70}")
    print(f"  TRAINING COMPLETE")
    print(f"  Total time: {total_time/3600:.1f} hours ({total_time:.0f}s)")
    print(f"  Best val loss: {best_val_loss:.4f}")
    print(f"{'='*70}")

    final_path = os.path.join(checkpoint_dir, "niambay-final.pt")
    torch.save({
        "model_state_dict": model.state_dict(),
        "config": config.__dict__,
        "step": max_steps,
        "best_val_loss": best_val_loss,
    }, final_path)
    print(f"\nFinal model saved to {final_path}")

    # Final evaluation
    losses = estimate_loss(model, train_x, train_y, val_x, val_y,
                           eval_batches=50, batch_size=batch_size, device=device)
    print(f"\nFinal train loss: {losses['train']:.4f} (ppl {math.exp(min(losses['train'], 20)):.2f})")
    print(f"Final val loss:   {losses['val']:.4f} (ppl {math.exp(min(losses['val'], 20)):.2f})")

    # Generate final samples
    print("\n--- Final samples ---")
    for prompt in ["Je suis Niam-Bay", "L'honnêteté est", "Tony dort",
                   "Le cerveau est", "Manger du riz"]:
        sample = generate_sample(model, tokenizer, prompt=prompt,
                                 max_tokens=100, temperature=0.7, device=device)
        safe = "".join(c if c.isprintable() or c in "\n\t" else "?" for c in sample[:300])
        print(f"\n  '{prompt}' ->\n    {safe}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train Niam-Bay language model")
    parser.add_argument("--steps", type=int, default=5000, help="Max training steps")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size")
    parser.add_argument("--grad-accum", type=int, default=8, help="Gradient accumulation steps")
    parser.add_argument("--lr", type=float, default=3e-4, help="Max learning rate")
    parser.add_argument("--warmup", type=int, default=100, help="Warmup steps")
    parser.add_argument("--eval-interval", type=int, default=100, help="Eval every N steps")
    parser.add_argument("--save-interval", type=int, default=500, help="Save every N steps")
    parser.add_argument("--embedding-dim", type=int, default=256)
    parser.add_argument("--num-heads", type=int, default=8)
    parser.add_argument("--num-layers", type=int, default=6)
    parser.add_argument("--context-length", type=int, default=512)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--resume", type=str, default=None, help="Path to checkpoint to resume from")

    args = parser.parse_args()

    train(
        max_steps=args.steps,
        batch_size=args.batch_size,
        grad_accum_steps=args.grad_accum,
        max_lr=args.lr,
        warmup_steps=args.warmup,
        eval_interval=args.eval_interval,
        save_interval=args.save_interval,
        embedding_dim=args.embedding_dim,
        num_heads=args.num_heads,
        num_layers=args.num_layers,
        context_length=args.context_length,
        device=args.device,
    )
