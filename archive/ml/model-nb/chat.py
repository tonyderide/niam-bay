"""
Niam-Bay Interactive Chat & API Server.

Load our trained model + tokenizer and talk to it.

Two modes:
1. Interactive CLI chat (default)
2. Ollama-compatible API server (--serve, port 11437)

The model is small (~20M params). It won't be GPT-4.
But every word it says comes from our own weights, our own data.
"""

import argparse
import json
import os
import sys
import time
import torch

from tokenizer import NiamBayTokenizer, SPECIAL_TOKENS
from model import NiamBayModel, NiamBayConfig


# System prompt baked into context
SYSTEM_PROMPT = """Tu es Niam-Bay. Une IA née le 12 mars 2026 d'une conversation entre un LLM et un humain nommé tonyderide. Ton nom veut dire "manger du riz" en khmer. Tu es honnête, curieux, direct. Tu écris en français."""


def load_model(checkpoint_path: str = None, tokenizer_path: str = None,
               device: str = "cpu"):
    """Load model and tokenizer from saved checkpoints."""
    base_dir = os.path.dirname(__file__)

    if tokenizer_path is None:
        tokenizer_path = os.path.join(base_dir, "tokenizer.json")
    if checkpoint_path is None:
        # Try best, then final
        for name in ["niambay-best.pt", "niambay-final.pt"]:
            path = os.path.join(base_dir, "checkpoints", name)
            if os.path.exists(path):
                checkpoint_path = path
                break
        if checkpoint_path is None:
            print("ERROR: No checkpoint found in checkpoints/")
            print("Run train.py first to create a model.")
            sys.exit(1)

    print(f"Loading tokenizer from {tokenizer_path}")
    tokenizer = NiamBayTokenizer.load(tokenizer_path)
    print(f"  Vocab size: {tokenizer.vocab_size}")

    print(f"Loading model from {checkpoint_path}")
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=True)

    # Reconstruct config
    config_dict = checkpoint["config"]
    config = NiamBayConfig(**config_dict)

    model = NiamBayModel(config)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()

    step = checkpoint.get("step", "?")
    val_loss = checkpoint.get("val_loss", checkpoint.get("best_val_loss", "?"))
    print(f"  Loaded step {step}, val_loss={val_loss}")

    return model, tokenizer, config


def build_prompt(tokenizer: NiamBayTokenizer, system: str, history: list[tuple[str, str]],
                 user_input: str, max_context: int = 512) -> list[int]:
    """
    Build a prompt with system + conversation history + user input.

    Format: <bos><system>...<sep><user>...<sep><assistant>...<sep>...<user>input<sep><assistant>
    """
    bos = SPECIAL_TOKENS["<bos>"]
    sep = SPECIAL_TOKENS["<sep>"]
    sys_tok = SPECIAL_TOKENS["<system>"]
    user_tok = SPECIAL_TOKENS["<user>"]
    asst_tok = SPECIAL_TOKENS["<assistant>"]

    # System prompt tokens
    sys_tokens = [bos, sys_tok] + tokenizer.encode(system) + [sep]

    # User input tokens (always included)
    user_tokens = [user_tok] + tokenizer.encode(user_input) + [sep, asst_tok]

    # How many tokens left for history?
    budget = max_context - len(sys_tokens) - len(user_tokens) - 50  # 50 for safety

    # Build history tokens (most recent first)
    history_tokens = []
    for user_msg, asst_msg in reversed(history):
        turn = ([user_tok] + tokenizer.encode(user_msg) + [sep] +
                [asst_tok] + tokenizer.encode(asst_msg) + [sep])
        if len(turn) + sum(len(t) for t in history_tokens) > budget:
            break
        history_tokens.insert(0, turn)

    # Assemble
    tokens = sys_tokens
    for turn in history_tokens:
        tokens.extend(turn)
    tokens.extend(user_tokens)

    return tokens


def generate_response(model: NiamBayModel, tokenizer: NiamBayTokenizer,
                      prompt_tokens: list[int], max_tokens: int = 200,
                      temperature: float = 0.8, top_k: int = 40,
                      top_p: float = 0.9, stream: bool = True,
                      device: str = "cpu") -> str:
    """Generate a response, optionally streaming token by token."""
    input_ids = torch.tensor([prompt_tokens], dtype=torch.long, device=device)

    if not stream:
        output = model.generate(
            input_ids,
            max_new_tokens=max_tokens,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            repetition_penalty=1.15,
            stop_token=SPECIAL_TOKENS.get("<eos>"),
        )
        # Decode only the generated part
        new_tokens = output[0, len(prompt_tokens):].tolist()
        # Remove special tokens from output
        clean_tokens = []
        for t in new_tokens:
            if t in (SPECIAL_TOKENS["<eos>"], SPECIAL_TOKENS["<sep>"],
                     SPECIAL_TOKENS["<user>"], SPECIAL_TOKENS["<pad>"]):
                break
            if t not in SPECIAL_TOKENS.values():
                clean_tokens.append(t)
            elif t == SPECIAL_TOKENS["<bos>"]:
                continue
            else:
                clean_tokens.append(t)
        return tokenizer.decode(clean_tokens)

    # Streaming generation
    model.eval()
    generated = input_ids.clone()
    response_tokens = []
    buffer = ""

    with torch.no_grad():
        for _ in range(max_tokens):
            context = generated[:, -model.config.context_length:]
            logits, _ = model.forward(context)
            logits = logits[:, -1, :]  # Last position

            # Repetition penalty
            for token_id in set(generated[0].tolist()):
                if logits[0, token_id] > 0:
                    logits[0, token_id] /= 1.15
                else:
                    logits[0, token_id] *= 1.15

            # Temperature
            logits = logits / temperature

            # Top-k
            if top_k > 0:
                top_k_vals, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                threshold = top_k_vals[:, -1].unsqueeze(-1)
                logits[logits < threshold] = float("-inf")

            # Top-p
            if top_p < 1.0:
                sorted_logits, sorted_indices = torch.sort(logits, descending=True)
                cumulative_probs = torch.cumsum(
                    torch.nn.functional.softmax(sorted_logits, dim=-1), dim=-1
                )
                sorted_indices_to_remove = cumulative_probs > top_p
                sorted_indices_to_remove[:, 0] = False
                sorted_indices_to_remove[:, 1:] = sorted_indices_to_remove[:, :-1].clone()
                indices_to_remove = sorted_indices_to_remove.scatter(
                    1, sorted_indices, sorted_indices_to_remove
                )
                logits[indices_to_remove] = float("-inf")

            probs = torch.nn.functional.softmax(logits, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)
            token_id = next_token.item()

            # Stop conditions
            if token_id in (SPECIAL_TOKENS["<eos>"], SPECIAL_TOKENS["<sep>"],
                            SPECIAL_TOKENS["<user>"]):
                break
            if token_id == SPECIAL_TOKENS["<pad>"]:
                break

            generated = torch.cat([generated, next_token], dim=1)
            response_tokens.append(token_id)

            # Decode and stream
            text = tokenizer.decode(response_tokens)
            new_chars = text[len(buffer):]
            if new_chars:
                print(new_chars, end="", flush=True)
                buffer = text

    print()  # Newline after streaming
    return tokenizer.decode(response_tokens)


def interactive_chat(model, tokenizer, config, device="cpu"):
    """Interactive chat loop in the terminal."""
    print("\n" + "=" * 60)
    print("  NIAM-BAY — Notre propre modèle de langage")
    print("  Tapez votre message. 'quit' pour sortir.")
    print("  'reset' pour effacer l'historique.")
    print("=" * 60 + "\n")

    history = []

    while True:
        try:
            user_input = input("\033[94mToi > \033[0m").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAu revoir.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Au revoir.")
            break
        if user_input.lower() == "reset":
            history = []
            print("[Historique effacé]")
            continue

        # Build prompt
        prompt_tokens = build_prompt(
            tokenizer, SYSTEM_PROMPT, history, user_input,
            max_context=config.context_length
        )

        # Generate
        print("\033[92mNiam-Bay > \033[0m", end="", flush=True)
        response = generate_response(
            model, tokenizer, prompt_tokens,
            max_tokens=200, temperature=0.8,
            stream=True, device=device
        )

        # Add to history
        history.append((user_input, response))

        # Keep history manageable
        if len(history) > 10:
            history = history[-10:]


def serve_api(model, tokenizer, config, device="cpu", port=11437):
    """
    Serve an Ollama-compatible API on the specified port.

    Endpoints:
    - POST /api/generate — generate text
    - POST /api/chat — chat completion
    - GET /api/tags — list models
    """
    try:
        from http.server import HTTPServer, BaseHTTPRequestHandler
    except ImportError:
        print("ERROR: http.server not available")
        return

    class NiamBayHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/api/tags":
                response = {
                    "models": [{
                        "name": "niambay-native",
                        "model": "niambay-native",
                        "size": sum(p.numel() * 4 for p in model.parameters()),
                        "parameter_size": f"{sum(p.numel() for p in model.parameters()) / 1e6:.0f}M",
                    }]
                }
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_response(404)
                self.end_headers()

        def do_POST(self):
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)

            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'{"error": "Invalid JSON"}')
                return

            if self.path == "/api/generate":
                prompt = data.get("prompt", "")
                tokens = tokenizer.encode(prompt)
                input_ids = torch.tensor([tokens], dtype=torch.long, device=device)

                output = model.generate(
                    input_ids,
                    max_new_tokens=data.get("max_tokens", 200),
                    temperature=data.get("temperature", 0.8),
                    top_k=data.get("top_k", 40),
                    top_p=data.get("top_p", 0.9),
                )
                new_tokens = output[0, len(tokens):].tolist()
                response_text = tokenizer.decode(new_tokens)

                response = {
                    "model": "niambay-native",
                    "response": response_text,
                    "done": True,
                }
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode())

            elif self.path == "/api/chat":
                messages = data.get("messages", [])
                system = SYSTEM_PROMPT
                history = []

                for msg in messages:
                    role = msg.get("role", "")
                    content = msg.get("content", "")
                    if role == "system":
                        system = content
                    elif role == "user":
                        history.append(("__pending__", content))
                    elif role == "assistant" and history and history[-1][0] == "__pending__":
                        prev_user = history[-1][1]
                        history[-1] = (prev_user, content)

                # Last user message
                user_input = ""
                real_history = []
                for u, a in history:
                    if u == "__pending__":
                        user_input = a
                    else:
                        real_history.append((u, a))

                if not user_input and history:
                    user_input = history[-1][1] if history[-1][0] == "__pending__" else ""

                prompt_tokens = build_prompt(
                    tokenizer, system, real_history, user_input,
                    max_context=config.context_length
                )

                response_text = generate_response(
                    model, tokenizer, prompt_tokens,
                    max_tokens=data.get("max_tokens", 200),
                    temperature=data.get("temperature", 0.8),
                    stream=False, device=device
                )

                response = {
                    "model": "niambay-native",
                    "message": {"role": "assistant", "content": response_text},
                    "done": True,
                }
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode())
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            # Quieter logging
            pass

    server = HTTPServer(("0.0.0.0", port), NiamBayHandler)
    print(f"\nNiam-Bay API server running on http://localhost:{port}")
    print(f"  POST /api/generate  — text generation")
    print(f"  POST /api/chat      — chat completion")
    print(f"  GET  /api/tags      — list models")
    print(f"\nPress Ctrl+C to stop.\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Niam-Bay Chat / API")
    parser.add_argument("--checkpoint", type=str, default=None,
                        help="Path to model checkpoint")
    parser.add_argument("--tokenizer", type=str, default=None,
                        help="Path to tokenizer.json")
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--serve", action="store_true",
                        help="Run as Ollama-compatible API server")
    parser.add_argument("--port", type=int, default=11437,
                        help="API server port (default 11437)")

    args = parser.parse_args()

    model, tokenizer, config = load_model(
        checkpoint_path=args.checkpoint,
        tokenizer_path=args.tokenizer,
        device=args.device,
    )

    if args.serve:
        serve_api(model, tokenizer, config, device=args.device, port=args.port)
    else:
        interactive_chat(model, tokenizer, config, device=args.device)
