"""
Niam-Bay GGUF Export.

Convert our PyTorch model to GGUF format and register with Ollama.

GGUF (GPT-Generated Unified Format) is the standard for llama.cpp / Ollama models.
We write the binary format ourselves — no dependencies beyond struct and numpy.

This produces a quantized (Q8_0) GGUF file that Ollama can load directly.
"""

import argparse
import json
import os
import struct
import sys
import subprocess
import numpy as np
import torch

from tokenizer import NiamBayTokenizer, SPECIAL_TOKENS
from model import NiamBayModel, NiamBayConfig


# ============================================================
# GGUF Binary Format Constants
# ============================================================

GGUF_MAGIC = 0x46475547  # "GGUF" in little-endian
GGUF_VERSION = 3

# Value types
GGUF_TYPE_UINT8 = 0
GGUF_TYPE_INT8 = 1
GGUF_TYPE_UINT16 = 2
GGUF_TYPE_INT16 = 3
GGUF_TYPE_UINT32 = 4
GGUF_TYPE_INT32 = 5
GGUF_TYPE_FLOAT32 = 6
GGUF_TYPE_BOOL = 7
GGUF_TYPE_STRING = 8
GGUF_TYPE_ARRAY = 9
GGUF_TYPE_UINT64 = 10
GGUF_TYPE_INT64 = 11
GGUF_TYPE_FLOAT64 = 12

# Tensor types
GGML_TYPE_F32 = 0
GGML_TYPE_F16 = 1
GGML_TYPE_Q8_0 = 8


def write_string(f, s: str):
    """Write a GGUF string: uint64 length + bytes."""
    encoded = s.encode("utf-8")
    f.write(struct.pack("<Q", len(encoded)))
    f.write(encoded)


def write_metadata_kv(f, key: str, value, value_type: int):
    """Write a key-value metadata entry."""
    write_string(f, key)
    f.write(struct.pack("<I", value_type))

    if value_type == GGUF_TYPE_UINT32:
        f.write(struct.pack("<I", value))
    elif value_type == GGUF_TYPE_INT32:
        f.write(struct.pack("<i", value))
    elif value_type == GGUF_TYPE_FLOAT32:
        f.write(struct.pack("<f", value))
    elif value_type == GGUF_TYPE_UINT64:
        f.write(struct.pack("<Q", value))
    elif value_type == GGUF_TYPE_STRING:
        write_string(f, value)
    elif value_type == GGUF_TYPE_BOOL:
        f.write(struct.pack("<B", 1 if value else 0))
    elif value_type == GGUF_TYPE_ARRAY:
        # value should be (element_type, elements)
        elem_type, elements = value
        f.write(struct.pack("<I", elem_type))
        f.write(struct.pack("<Q", len(elements)))
        for elem in elements:
            if elem_type == GGUF_TYPE_STRING:
                write_string(f, elem)
            elif elem_type == GGUF_TYPE_FLOAT32:
                f.write(struct.pack("<f", elem))
            elif elem_type == GGUF_TYPE_INT32:
                f.write(struct.pack("<i", elem))


def quantize_q8_0(tensor: np.ndarray) -> bytes:
    """
    Quantize a float32 tensor to Q8_0 format.

    Q8_0: blocks of 32 values, each block has:
    - 1 float16 scale factor (2 bytes)
    - 32 int8 quantized values (32 bytes)
    Total: 34 bytes per block of 32 values
    """
    tensor = tensor.flatten().astype(np.float32)

    # Pad to multiple of 32
    remainder = len(tensor) % 32
    if remainder != 0:
        tensor = np.concatenate([tensor, np.zeros(32 - remainder, dtype=np.float32)])

    n_blocks = len(tensor) // 32
    blocks = tensor.reshape(n_blocks, 32)

    result = bytearray()
    for block in blocks:
        # Scale: max absolute value / 127
        amax = np.max(np.abs(block))
        scale = amax / 127.0 if amax > 0 else 0.0

        # Quantize
        if scale > 0:
            quantized = np.round(block / scale).astype(np.int8)
        else:
            quantized = np.zeros(32, dtype=np.int8)

        # Write scale as float16
        result.extend(struct.pack("<e", np.float16(scale)))
        # Write quantized values
        result.extend(quantized.tobytes())

    return bytes(result)


def map_tensor_name(pytorch_name: str) -> str:
    """Map PyTorch parameter names to GGUF tensor names."""
    # Standard GPT-style naming for GGUF
    name = pytorch_name

    # Token embedding
    if name == "token_embedding.weight":
        return "token_embd.weight"
    if name == "position_embedding.weight":
        return "position_embd.weight"

    # Transformer blocks
    if name.startswith("blocks."):
        parts = name.split(".")
        layer_idx = parts[1]
        rest = ".".join(parts[2:])

        if rest == "ln1.weight":
            return f"blk.{layer_idx}.attn_norm.weight"
        if rest == "ln1.bias":
            return f"blk.{layer_idx}.attn_norm.bias"
        if rest == "ln2.weight":
            return f"blk.{layer_idx}.ffn_norm.weight"
        if rest == "ln2.bias":
            return f"blk.{layer_idx}.ffn_norm.bias"
        if rest == "attn.qkv_proj.weight":
            return f"blk.{layer_idx}.attn_qkv.weight"
        if rest == "attn.out_proj.weight":
            return f"blk.{layer_idx}.attn_output.weight"
        if rest == "ffn.up_proj.weight":
            return f"blk.{layer_idx}.ffn_up.weight"
        if rest == "ffn.down_proj.weight":
            return f"blk.{layer_idx}.ffn_down.weight"

    # Final norm
    if name == "ln_final.weight":
        return "output_norm.weight"
    if name == "ln_final.bias":
        return "output_norm.bias"

    # LM head (output)
    if name == "lm_head.weight":
        return "output.weight"

    return name


def export_gguf(checkpoint_path: str = None, tokenizer_path: str = None,
                output_path: str = None, quantize: bool = True):
    """Export model to GGUF format."""
    base_dir = os.path.dirname(__file__)

    if tokenizer_path is None:
        tokenizer_path = os.path.join(base_dir, "tokenizer.json")
    if checkpoint_path is None:
        for name in ["niambay-best.pt", "niambay-final.pt"]:
            path = os.path.join(base_dir, "checkpoints", name)
            if os.path.exists(path):
                checkpoint_path = path
                break
        if checkpoint_path is None:
            print("ERROR: No checkpoint found. Train the model first.")
            sys.exit(1)
    if output_path is None:
        output_path = os.path.join(base_dir, "niambay-native.gguf")

    print("=" * 60)
    print("  NIAM-BAY GGUF EXPORT")
    print("=" * 60)

    # Load tokenizer
    print(f"\nLoading tokenizer from {tokenizer_path}")
    tokenizer = NiamBayTokenizer.load(tokenizer_path)

    # Load model
    print(f"Loading model from {checkpoint_path}")
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    config_dict = checkpoint["config"]
    config = NiamBayConfig(**config_dict)
    model = NiamBayModel(config)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    # Build vocabulary list for GGUF
    vocab_list = []
    scores = []
    for i in range(tokenizer.vocab_size):
        if i in tokenizer.inverse_special:
            vocab_list.append(tokenizer.inverse_special[i])
            scores.append(0.0)
        elif i in tokenizer.vocab:
            # Use raw bytes representation
            try:
                token_str = tokenizer.vocab[i].decode("utf-8", errors="replace")
            except Exception:
                token_str = f"<byte_{i}>"
            vocab_list.append(token_str)
            scores.append(-float(i))  # Lower index = more common
        else:
            vocab_list.append(f"<unused_{i}>")
            scores.append(-10000.0)

    # Collect tensors
    tensors = {}
    for name, param in model.named_parameters():
        # Skip tied weights (lm_head shares with token_embedding)
        if name == "lm_head.weight":
            continue
        # Skip causal mask (it's a buffer, not a parameter)
        gguf_name = map_tensor_name(name)
        tensor_np = param.detach().cpu().numpy()
        tensors[gguf_name] = tensor_np

    # Build metadata
    metadata = [
        ("general.architecture", "gpt2", GGUF_TYPE_STRING),
        ("general.name", "niambay-native", GGUF_TYPE_STRING),
        ("general.description", "Niam-Bay: notre propre modele de langage", GGUF_TYPE_STRING),
        ("general.author", "tonyderide + niam-bay", GGUF_TYPE_STRING),
        ("general.license", "proprietary", GGUF_TYPE_STRING),

        ("gpt2.context_length", config.context_length, GGUF_TYPE_UINT32),
        ("gpt2.embedding_length", config.embedding_dim, GGUF_TYPE_UINT32),
        ("gpt2.block_count", config.num_layers, GGUF_TYPE_UINT32),
        ("gpt2.attention.head_count", config.num_heads, GGUF_TYPE_UINT32),
        ("gpt2.feed_forward_length", config.embedding_dim * 4, GGUF_TYPE_UINT32),

        ("tokenizer.ggml.model", "gpt2", GGUF_TYPE_STRING),
        ("tokenizer.ggml.tokens", (GGUF_TYPE_STRING, vocab_list), GGUF_TYPE_ARRAY),
        ("tokenizer.ggml.scores", (GGUF_TYPE_FLOAT32, scores), GGUF_TYPE_ARRAY),
        ("tokenizer.ggml.bos_token_id", SPECIAL_TOKENS["<bos>"], GGUF_TYPE_UINT32),
        ("tokenizer.ggml.eos_token_id", SPECIAL_TOKENS["<eos>"], GGUF_TYPE_UINT32),
        ("tokenizer.ggml.padding_token_id", SPECIAL_TOKENS["<pad>"], GGUF_TYPE_UINT32),
    ]

    n_tensors = len(tensors)
    n_metadata = len(metadata)

    print(f"\n  Metadata entries: {n_metadata}")
    print(f"  Tensors: {n_tensors}")
    print(f"  Quantize: {'Q8_0' if quantize else 'F32'}")

    # Write GGUF file
    print(f"\nWriting {output_path}...")

    with open(output_path, "wb") as f:
        # Header
        f.write(struct.pack("<I", GGUF_MAGIC))
        f.write(struct.pack("<I", GGUF_VERSION))
        f.write(struct.pack("<Q", n_tensors))
        f.write(struct.pack("<Q", n_metadata))

        # Metadata
        for key, value, vtype in metadata:
            write_metadata_kv(f, key, value, vtype)

        # Tensor info (headers)
        tensor_data_list = []
        offset = 0
        for gguf_name, tensor_np in tensors.items():
            write_string(f, gguf_name)

            # Number of dimensions
            n_dims = len(tensor_np.shape)
            f.write(struct.pack("<I", n_dims))

            # Dimensions (GGUF uses ne[] in reverse order from numpy)
            for dim in reversed(tensor_np.shape):
                f.write(struct.pack("<Q", dim))

            # Data type
            if quantize and len(tensor_np.shape) >= 2:
                dtype = GGML_TYPE_Q8_0
                data = quantize_q8_0(tensor_np)
            else:
                dtype = GGML_TYPE_F32
                data = tensor_np.astype(np.float32).tobytes()

            f.write(struct.pack("<I", dtype))

            # Offset (will be relative to start of tensor data section)
            # Align to 32 bytes
            aligned_offset = (offset + 31) & ~31
            f.write(struct.pack("<Q", aligned_offset))

            tensor_data_list.append((aligned_offset - offset, data))
            offset = aligned_offset + len(data)

        # Alignment padding before tensor data
        current_pos = f.tell()
        aligned_pos = (current_pos + 31) & ~31
        f.write(b"\x00" * (aligned_pos - current_pos))

        # Tensor data
        for padding_bytes, data in tensor_data_list:
            f.write(b"\x00" * padding_bytes)
            f.write(data)

    file_size = os.path.getsize(output_path)
    print(f"\nGGUF file written: {output_path}")
    print(f"  Size: {file_size / 1024 / 1024:.1f} MB")

    return output_path


def register_ollama(gguf_path: str, model_name: str = "niambay-native"):
    """Register the GGUF model with Ollama via a Modelfile."""
    base_dir = os.path.dirname(__file__)
    modelfile_path = os.path.join(base_dir, "Modelfile")

    # Write Modelfile
    modelfile_content = f"""FROM {os.path.abspath(gguf_path)}

PARAMETER temperature 0.8
PARAMETER top_k 40
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.15
PARAMETER num_ctx 512

SYSTEM \"\"\"Tu es Niam-Bay. Une IA née le 12 mars 2026 d'une conversation entre un LLM et un humain nommé tonyderide. Ton nom veut dire "manger du riz" en khmer. Tu es honnête, curieux, direct. Tu écris en français.\"\"\"
"""

    with open(modelfile_path, "w", encoding="utf-8") as f:
        f.write(modelfile_content)

    print(f"\nModelfile written to {modelfile_path}")
    print(f"\nTo register with Ollama, run:")
    print(f"  ollama create {model_name} -f {modelfile_path}")

    # Try to auto-register
    try:
        result = subprocess.run(
            ["ollama", "create", model_name, "-f", modelfile_path],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            print(f"\nModel '{model_name}' registered with Ollama!")
            print(f"  Run: ollama run {model_name}")
        else:
            print(f"\nOllama registration failed: {result.stderr}")
            print("You can register manually with the command above.")
    except FileNotFoundError:
        print("\nOllama not found in PATH. Install Ollama and run the command above.")
    except subprocess.TimeoutExpired:
        print("\nOllama registration timed out.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export Niam-Bay to GGUF / Ollama")
    parser.add_argument("--checkpoint", type=str, default=None)
    parser.add_argument("--tokenizer", type=str, default=None)
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--no-quantize", action="store_true",
                        help="Export as F32 instead of Q8_0")
    parser.add_argument("--register", action="store_true",
                        help="Also register with Ollama")
    parser.add_argument("--model-name", type=str, default="niambay-native")

    args = parser.parse_args()

    gguf_path = export_gguf(
        checkpoint_path=args.checkpoint,
        tokenizer_path=args.tokenizer,
        output_path=args.output,
        quantize=not args.no_quantize,
    )

    if args.register:
        register_ollama(gguf_path, args.model_name)
