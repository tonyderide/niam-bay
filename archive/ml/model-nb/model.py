"""
Niam-Bay Transformer — a GPT-style decoder built from scratch.

No HuggingFace. No transformers library. Just PyTorch and math.

Architecture:
- Causal (decoder-only) transformer
- Learned positional embeddings
- Pre-norm (LayerNorm before attention and FFN)
- ReLU-squared activation in FFN (simple, effective)
- ~10-20M parameters depending on config
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from dataclasses import dataclass


@dataclass
class NiamBayConfig:
    """Model configuration."""
    vocab_size: int = 4000
    context_length: int = 512
    embedding_dim: int = 256
    num_heads: int = 8
    num_layers: int = 6
    dropout: float = 0.1
    bias: bool = False  # No bias in linear layers (cleaner)

    @property
    def head_dim(self) -> int:
        assert self.embedding_dim % self.num_heads == 0
        return self.embedding_dim // self.num_heads

    def num_parameters(self) -> int:
        """Estimate total parameters."""
        d = self.embedding_dim
        V = self.vocab_size
        L = self.num_layers
        T = self.context_length

        # Token embeddings + positional embeddings
        embed = V * d + T * d
        # Per layer: attention (Q, K, V, O) + FFN (up, down) + 2 layer norms
        attn = 4 * d * d  # Q, K, V, output projections
        ffn = 2 * d * (4 * d)  # up-project and down-project
        ln = 2 * 2 * d  # 2 layer norms per layer, each has weight + bias
        per_layer = attn + ffn + ln
        # Final layer norm + output head (tied with embedding)
        final = 2 * d  # final layer norm
        # Output head shares weights with token embedding

        total = embed + L * per_layer + final
        return total


class MultiHeadAttention(nn.Module):
    """
    Multi-head causal self-attention.

    Each head independently computes attention over (Q, K, V)
    with a causal mask so position i can only attend to positions <= i.
    """

    def __init__(self, config: NiamBayConfig):
        super().__init__()
        self.num_heads = config.num_heads
        self.head_dim = config.head_dim
        self.embedding_dim = config.embedding_dim

        # Combined Q, K, V projection for efficiency
        self.qkv_proj = nn.Linear(config.embedding_dim, 3 * config.embedding_dim, bias=config.bias)
        # Output projection
        self.out_proj = nn.Linear(config.embedding_dim, config.embedding_dim, bias=config.bias)

        self.attn_dropout = nn.Dropout(config.dropout)
        self.resid_dropout = nn.Dropout(config.dropout)

        # Causal mask: upper triangular = -inf
        # Register as buffer so it moves to device with model
        mask = torch.triu(torch.ones(config.context_length, config.context_length), diagonal=1)
        mask = mask.masked_fill(mask == 1, float("-inf"))
        self.register_buffer("causal_mask", mask)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (batch, seq_len, embedding_dim)
        Returns:
            (batch, seq_len, embedding_dim)
        """
        B, T, D = x.shape

        # Project to Q, K, V
        qkv = self.qkv_proj(x)  # (B, T, 3*D)
        q, k, v = qkv.chunk(3, dim=-1)  # each (B, T, D)

        # Reshape to (B, num_heads, T, head_dim)
        q = q.view(B, T, self.num_heads, self.head_dim).transpose(1, 2)
        k = k.view(B, T, self.num_heads, self.head_dim).transpose(1, 2)
        v = v.view(B, T, self.num_heads, self.head_dim).transpose(1, 2)

        # Scaled dot-product attention
        scale = math.sqrt(self.head_dim)
        attn_weights = torch.matmul(q, k.transpose(-2, -1)) / scale  # (B, H, T, T)

        # Apply causal mask
        attn_weights = attn_weights + self.causal_mask[:T, :T]

        attn_weights = F.softmax(attn_weights, dim=-1)
        attn_weights = self.attn_dropout(attn_weights)

        # Weighted sum of values
        out = torch.matmul(attn_weights, v)  # (B, H, T, head_dim)

        # Reshape back to (B, T, D)
        out = out.transpose(1, 2).contiguous().view(B, T, D)

        # Output projection
        out = self.out_proj(out)
        out = self.resid_dropout(out)

        return out


class FeedForward(nn.Module):
    """
    Position-wise feed-forward network.

    Uses SwiGLU-inspired gating but simplified:
    FFN(x) = down_proj(GELU(up_proj(x)))

    Expansion factor 4x as standard in transformers.
    """

    def __init__(self, config: NiamBayConfig):
        super().__init__()
        hidden_dim = 4 * config.embedding_dim
        self.up_proj = nn.Linear(config.embedding_dim, hidden_dim, bias=config.bias)
        self.down_proj = nn.Linear(hidden_dim, config.embedding_dim, bias=config.bias)
        self.dropout = nn.Dropout(config.dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.up_proj(x)
        x = F.gelu(x)
        x = self.down_proj(x)
        x = self.dropout(x)
        return x


class TransformerBlock(nn.Module):
    """
    Pre-norm transformer block.

    LayerNorm -> Attention -> residual
    LayerNorm -> FFN -> residual

    Pre-norm is more stable for training than post-norm.
    """

    def __init__(self, config: NiamBayConfig):
        super().__init__()
        self.ln1 = nn.LayerNorm(config.embedding_dim)
        self.attn = MultiHeadAttention(config)
        self.ln2 = nn.LayerNorm(config.embedding_dim)
        self.ffn = FeedForward(config)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Attention with residual
        x = x + self.attn(self.ln1(x))
        # FFN with residual
        x = x + self.ffn(self.ln2(x))
        return x


class NiamBayModel(nn.Module):
    """
    The Niam-Bay language model.

    A GPT-style causal transformer decoder.
    Predicts the next token given previous tokens.
    """

    def __init__(self, config: NiamBayConfig):
        super().__init__()
        self.config = config

        # Token and position embeddings
        self.token_embedding = nn.Embedding(config.vocab_size, config.embedding_dim)
        self.position_embedding = nn.Embedding(config.context_length, config.embedding_dim)

        # Embedding dropout
        self.embed_dropout = nn.Dropout(config.dropout)

        # Transformer blocks
        self.blocks = nn.ModuleList([
            TransformerBlock(config) for _ in range(config.num_layers)
        ])

        # Final layer norm
        self.ln_final = nn.LayerNorm(config.embedding_dim)

        # Output head — projects back to vocabulary
        # Weight tying: share weights with token embedding
        self.lm_head = nn.Linear(config.embedding_dim, config.vocab_size, bias=False)
        self.lm_head.weight = self.token_embedding.weight  # Weight tying

        # Initialize weights
        self.apply(self._init_weights)

        # Report size
        n_params = sum(p.numel() for p in self.parameters())
        # Subtract tied weights (counted twice)
        n_params -= self.token_embedding.weight.numel()
        print(f"NiamBayModel: {n_params:,} parameters (+ {self.token_embedding.weight.numel():,} tied)")
        print(f"  Config estimate: ~{config.num_parameters():,}")

    def _init_weights(self, module):
        """Initialize weights with small normal distribution."""
        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
        elif isinstance(module, nn.LayerNorm):
            torch.nn.init.ones_(module.weight)
            torch.nn.init.zeros_(module.bias)

    def forward(self, input_ids: torch.Tensor, targets: torch.Tensor = None):
        """
        Args:
            input_ids: (batch, seq_len) token ids
            targets: (batch, seq_len) target token ids for loss computation

        Returns:
            logits: (batch, seq_len, vocab_size)
            loss: scalar if targets provided, else None
        """
        B, T = input_ids.shape
        assert T <= self.config.context_length, \
            f"Sequence length {T} exceeds context length {self.config.context_length}"

        # Token + position embeddings
        positions = torch.arange(T, device=input_ids.device)  # (T,)
        tok_emb = self.token_embedding(input_ids)  # (B, T, D)
        pos_emb = self.position_embedding(positions)  # (T, D)
        x = self.embed_dropout(tok_emb + pos_emb)

        # Transformer blocks
        for block in self.blocks:
            x = block(x)

        # Final norm
        x = self.ln_final(x)

        # Project to vocab
        logits = self.lm_head(x)  # (B, T, V)

        # Compute loss if targets provided
        loss = None
        if targets is not None:
            # Shift: predict next token
            # logits[:, :-1] predicts targets[:, 1:]
            # But usually targets are already shifted in the data pipeline
            loss = F.cross_entropy(
                logits.view(-1, self.config.vocab_size),
                targets.view(-1),
                ignore_index=0  # ignore <pad> token
            )

        return logits, loss

    @torch.no_grad()
    def generate(
        self,
        input_ids: torch.Tensor,
        max_new_tokens: int = 200,
        temperature: float = 0.8,
        top_k: int = 50,
        top_p: float = 0.9,
        repetition_penalty: float = 1.1,
        stop_token: int = None,
    ) -> torch.Tensor:
        """
        Autoregressive generation with temperature, top-k, top-p sampling.

        Args:
            input_ids: (1, seq_len) prompt token ids
            max_new_tokens: maximum tokens to generate
            temperature: sampling temperature (lower = more deterministic)
            top_k: keep only top-k logits before sampling
            top_p: nucleus sampling threshold
            repetition_penalty: penalize already-generated tokens
            stop_token: stop generation when this token is produced

        Returns:
            (1, seq_len + generated) full sequence including prompt
        """
        self.eval()
        generated = input_ids.clone()

        for _ in range(max_new_tokens):
            # Crop to context length
            context = generated[:, -self.config.context_length:]

            # Forward pass
            logits, _ = self.forward(context)
            logits = logits[:, -1, :]  # (1, vocab_size) — last position

            # Repetition penalty
            if repetition_penalty != 1.0:
                for token_id in set(generated[0].tolist()):
                    if logits[0, token_id] > 0:
                        logits[0, token_id] /= repetition_penalty
                    else:
                        logits[0, token_id] *= repetition_penalty

            # Temperature
            if temperature > 0:
                logits = logits / temperature
            else:
                # Greedy
                next_token = logits.argmax(dim=-1, keepdim=True)
                generated = torch.cat([generated, next_token], dim=1)
                if stop_token is not None and next_token.item() == stop_token:
                    break
                continue

            # Top-k filtering
            if top_k > 0:
                top_k_vals, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                threshold = top_k_vals[:, -1].unsqueeze(-1)
                logits[logits < threshold] = float("-inf")

            # Top-p (nucleus) filtering
            if top_p < 1.0:
                sorted_logits, sorted_indices = torch.sort(logits, descending=True)
                cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)

                # Remove tokens with cumulative probability above threshold
                sorted_indices_to_remove = cumulative_probs > top_p
                # Keep at least one token
                sorted_indices_to_remove[:, 0] = False
                # Shift right so the first token above threshold is also removed
                sorted_indices_to_remove[:, 1:] = sorted_indices_to_remove[:, :-1].clone()

                indices_to_remove = sorted_indices_to_remove.scatter(
                    1, sorted_indices, sorted_indices_to_remove
                )
                logits[indices_to_remove] = float("-inf")

            # Sample
            probs = F.softmax(logits, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)  # (1, 1)

            generated = torch.cat([generated, next_token], dim=1)

            if stop_token is not None and next_token.item() == stop_token:
                break

        return generated


def create_model(vocab_size: int = 4000, **kwargs) -> NiamBayModel:
    """Create a NiamBayModel with default or custom config."""
    config = NiamBayConfig(vocab_size=vocab_size, **kwargs)
    return NiamBayModel(config)


if __name__ == "__main__":
    # Quick test
    print("Testing NiamBayModel...")
    config = NiamBayConfig(vocab_size=4000)
    print(f"Estimated params: {config.num_parameters():,}")

    model = NiamBayModel(config)

    # Test forward pass
    dummy_input = torch.randint(0, 4000, (2, 64))
    dummy_targets = torch.randint(0, 4000, (2, 64))

    logits, loss = model(dummy_input, dummy_targets)
    print(f"Forward pass: logits {logits.shape}, loss {loss.item():.4f}")

    # Test generation
    prompt = torch.randint(0, 4000, (1, 10))
    output = model.generate(prompt, max_new_tokens=20)
    print(f"Generation: {prompt.shape} -> {output.shape}")
    print("All tests passed!")
