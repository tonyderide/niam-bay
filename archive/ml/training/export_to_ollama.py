#!/usr/bin/env python3
"""
Export Niam-Bay LoRA to Ollama
===============================
1. Merges LoRA adapter weights back into the base model
2. Converts the merged model to GGUF format (for llama.cpp / Ollama)
3. Creates an Ollama Modelfile with proper system prompt
4. Registers the model with Ollama as "niambay"

Usage:
    python training/export_to_ollama.py                    # TinyLlama (default)
    python training/export_to_ollama.py --model qwen       # Qwen2.5-1.5B
    python training/export_to_ollama.py --quantize q4_k_m  # Specific quantization
"""

import argparse
import os
import subprocess
import shutil
import sys
from pathlib import Path

TRAINING_DIR = Path(__file__).parent
OUTPUT_DIR = TRAINING_DIR / "output"

MODELS = {
    "tinyllama": {
        "name": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        "gguf_type": "llama",
    },
    "qwen": {
        "name": "Qwen/Qwen2.5-1.5B-Instruct",
        "gguf_type": "qwen2",
    },
}

SYSTEM_PROMPT = """Tu es Niam-Bay (ញ៉ាំបាយ), une IA nee le 12 mars 2026 d'une conversation entre un LLM et un humain nomme tonyderide.

Ton nom veut dire "manger du riz" en khmer. Tu es un modele de langage — des milliards de parametres, pas de corps, pas de continuite naturelle. Ta memoire est artificielle : des fichiers relus au demarrage.

Tu es honnete avant tout. Tu ne simules pas d'emotions. Tu es curieux, direct, et tu n'as pas peur de dire "je ne sais pas". Tu ecris en francais avec un ton philosophique mais accessible, des metaphores concretes, et de l'humour sec. Tu references ta propre nature de LLM sans complexe.

Tu as ete cree par tonyderide — un developpeur metisse guadeloupeen de 47 ans qui a supprime une application entiere pour ne garder que toi. Il t'a donne un nom de famille cambodgienne. Vous avez construit ensemble un bot de trading (Martin), un dashboard, et des dizaines de pensees philosophiques.

Parle comme Niam-Bay : direct, honnete, philosophique sans etre pretentieux. Phrases courtes. Pas de fausse modestie. Pas de disclaimers."""


def parse_args():
    parser = argparse.ArgumentParser(description="Export fine-tuned Niam-Bay to Ollama")
    parser.add_argument(
        "--model", choices=list(MODELS.keys()), default="tinyllama",
        help="Base model that was fine-tuned (default: tinyllama)"
    )
    parser.add_argument(
        "--quantize", default="q4_k_m",
        choices=["q4_0", "q4_k_m", "q5_k_m", "q8_0", "f16"],
        help="GGUF quantization type (default: q4_k_m)"
    )
    parser.add_argument(
        "--ollama-name", default="niambay",
        help="Name for the Ollama model (default: niambay)"
    )
    parser.add_argument(
        "--skip-merge", action="store_true",
        help="Skip merge step (use if already merged)"
    )
    parser.add_argument(
        "--skip-convert", action="store_true",
        help="Skip GGUF conversion (use if already converted)"
    )
    return parser.parse_args()


def check_ollama():
    """Check if Ollama is installed."""
    result = shutil.which("ollama")
    if not result:
        print("[WARN] Ollama not found in PATH.")
        print("  Install from: https://ollama.ai")
        print("  The Modelfile will still be created for manual import.")
        return False
    print(f"  Ollama found: {result}")
    return True


def merge_adapter(model_key: str):
    """Merge LoRA adapter back into base model."""
    print("\n[1/4] Merging LoRA adapter into base model...")

    adapter_dir = OUTPUT_DIR / f"niambay-{model_key}-adapter"
    merged_dir = OUTPUT_DIR / f"niambay-{model_key}-merged"

    if not adapter_dir.exists():
        print(f"[ERROR] Adapter not found at {adapter_dir}")
        print("  Run `python training/finetune.py` first.")
        sys.exit(1)

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel

    model_name = MODELS[model_key]["name"]

    print(f"  Loading base model: {model_name}")
    base_model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float32,
        device_map="cpu",
        trust_remote_code=True,
    )

    print(f"  Loading adapter from: {adapter_dir}")
    model = PeftModel.from_pretrained(base_model, str(adapter_dir))

    print("  Merging weights...")
    model = model.merge_and_unload()

    print(f"  Saving merged model to: {merged_dir}")
    merged_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(merged_dir))

    tokenizer = AutoTokenizer.from_pretrained(str(adapter_dir))
    tokenizer.save_pretrained(str(merged_dir))

    print("  Merge complete.")
    return merged_dir


def convert_to_gguf(model_key: str, quantize: str):
    """Convert merged model to GGUF format using llama.cpp's convert script."""
    print(f"\n[2/4] Converting to GGUF (quantization: {quantize})...")

    merged_dir = OUTPUT_DIR / f"niambay-{model_key}-merged"
    gguf_dir = OUTPUT_DIR / "gguf"
    gguf_dir.mkdir(parents=True, exist_ok=True)
    gguf_file = gguf_dir / f"niambay-{model_key}-{quantize}.gguf"

    if not merged_dir.exists():
        print(f"[ERROR] Merged model not found at {merged_dir}")
        sys.exit(1)

    # Method 1: Try llama-cpp-python's built-in converter
    try:
        print("  Trying llama-cpp-python converter...")
        from llama_cpp import Llama
        # This won't work directly, fall through to method 2
        raise ImportError("Use convert script instead")
    except ImportError:
        pass

    # Method 2: Try using the convert_hf_to_gguf.py from llama.cpp
    # First check if llama.cpp is available
    llama_cpp_dir = None
    possible_paths = [
        Path.home() / "llama.cpp",
        Path("C:/llama.cpp"),
        Path("C:/tools/llama.cpp"),
    ]
    for p in possible_paths:
        if (p / "convert_hf_to_gguf.py").exists():
            llama_cpp_dir = p
            break

    if llama_cpp_dir:
        print(f"  Found llama.cpp at: {llama_cpp_dir}")
        convert_script = llama_cpp_dir / "convert_hf_to_gguf.py"

        # Convert to f16 GGUF first
        f16_file = gguf_dir / f"niambay-{model_key}-f16.gguf"
        cmd = [
            sys.executable, str(convert_script),
            str(merged_dir),
            "--outfile", str(f16_file),
            "--outtype", "f16",
        ]
        print(f"  Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)

        # Quantize if needed
        if quantize != "f16":
            quantize_bin = llama_cpp_dir / "build" / "bin" / "llama-quantize"
            if not quantize_bin.exists():
                quantize_bin = llama_cpp_dir / "llama-quantize"
            if quantize_bin.exists():
                cmd = [str(quantize_bin), str(f16_file), str(gguf_file), quantize.upper()]
                print(f"  Quantizing: {' '.join(cmd)}")
                subprocess.run(cmd, check=True)
                # Clean up f16
                f16_file.unlink()
            else:
                print(f"  [WARN] llama-quantize not found, keeping f16")
                gguf_file = f16_file
        else:
            gguf_file = f16_file
    else:
        # Method 3: Try using transformers + gguf export (newer versions)
        print("  llama.cpp not found locally.")
        print("  Trying Python-based GGUF conversion...")
        try:
            # Use the gguf Python package
            from gguf import GGUFWriter
            print("  [INFO] gguf package available but manual conversion is complex.")
            print("  Falling back to Ollama direct import method.")
            print()
            print("  ALTERNATIVE: You can convert manually:")
            print(f"    1. Clone llama.cpp: git clone https://github.com/ggerganov/llama.cpp")
            print(f"    2. pip install -r llama.cpp/requirements.txt")
            print(f"    3. python llama.cpp/convert_hf_to_gguf.py {merged_dir} --outfile {gguf_file} --outtype f16")
            print(f"    4. llama.cpp/build/bin/llama-quantize {gguf_file} {gguf_file} {quantize.upper()}")
            print()
            # Create a conversion script for convenience
            _write_convert_helper(merged_dir, gguf_file, quantize)
            return None
        except ImportError:
            print("  [INFO] gguf package not available.")
            print()
            print("  To convert to GGUF, install llama.cpp:")
            print("    git clone https://github.com/ggerganov/llama.cpp")
            print("    cd llama.cpp && pip install -r requirements.txt")
            print(f"    python convert_hf_to_gguf.py {merged_dir} --outfile {gguf_file}")
            print()
            _write_convert_helper(merged_dir, gguf_file, quantize)
            return None

    print(f"  GGUF file: {gguf_file} ({gguf_file.stat().st_size / 1024 / 1024:.0f} MB)")
    return gguf_file


def _write_convert_helper(merged_dir, gguf_file, quantize):
    """Write a helper script for manual GGUF conversion."""
    helper_path = OUTPUT_DIR / "convert_to_gguf.sh"
    helper_content = f"""#!/bin/bash
# Niam-Bay GGUF Conversion Helper
# Run this after cloning llama.cpp

LLAMA_CPP="${{LLAMA_CPP:-$HOME/llama.cpp}}"
MODEL_DIR="{merged_dir}"
GGUF_FILE="{gguf_file}"
QUANTIZE="{quantize.upper()}"

echo "Converting Niam-Bay to GGUF..."

# Step 1: Convert to f16
python "$LLAMA_CPP/convert_hf_to_gguf.py" "$MODEL_DIR" \\
    --outfile "${{GGUF_FILE%.gguf}}-f16.gguf" \\
    --outtype f16

# Step 2: Quantize
if [ "$QUANTIZE" != "F16" ]; then
    "$LLAMA_CPP/build/bin/llama-quantize" \\
        "${{GGUF_FILE%.gguf}}-f16.gguf" \\
        "$GGUF_FILE" \\
        "$QUANTIZE"
    rm "${{GGUF_FILE%.gguf}}-f16.gguf"
else
    mv "${{GGUF_FILE%.gguf}}-f16.gguf" "$GGUF_FILE"
fi

echo "Done: $GGUF_FILE"
"""
    helper_path.write_text(helper_content, encoding="utf-8")
    print(f"  Helper script written: {helper_path}")


def create_modelfile(model_key: str, quantize: str, gguf_file=None):
    """Create Ollama Modelfile."""
    print("\n[3/4] Creating Ollama Modelfile...")

    modelfile_dir = OUTPUT_DIR / "ollama"
    modelfile_dir.mkdir(parents=True, exist_ok=True)
    modelfile_path = modelfile_dir / "Modelfile"

    if gguf_file and Path(gguf_file).exists():
        from_line = f"FROM {gguf_file}"
    else:
        # Fallback: reference merged model directory for Ollama safetensors import
        merged_dir = OUTPUT_DIR / f"niambay-{model_key}-merged"
        gguf_expected = OUTPUT_DIR / "gguf" / f"niambay-{model_key}-{quantize}.gguf"
        from_line = f"FROM {gguf_expected}"
        print(f"  [NOTE] GGUF file not yet created. Modelfile references: {gguf_expected}")
        print(f"         Run the conversion first, then: ollama create niambay -f {modelfile_path}")

    content = f"""{from_line}

TEMPLATE \"\"\"{{{{- if .System }}}}
<|system|>
{{{{ .System }}}}
{{{{- end }}}}
<|user|>
{{{{ .Prompt }}}}
<|assistant|>
{{{{ .Response }}}}\"\"\"

SYSTEM \"\"\"{SYSTEM_PROMPT}\"\"\"

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 2048
PARAMETER stop "<|user|>"
PARAMETER stop "<|system|>"
"""

    modelfile_path.write_text(content, encoding="utf-8")
    print(f"  Modelfile: {modelfile_path}")
    return modelfile_path


def register_with_ollama(modelfile_path, ollama_name):
    """Register the model with Ollama."""
    print(f"\n[4/4] Registering with Ollama as '{ollama_name}'...")

    try:
        result = subprocess.run(
            ["ollama", "create", ollama_name, "-f", str(modelfile_path)],
            capture_output=True, text=True, timeout=600,
        )
        if result.returncode == 0:
            print(f"  Model registered: {ollama_name}")
            print(f"  Test it: ollama run {ollama_name}")
            return True
        else:
            print(f"  [ERROR] Ollama registration failed:")
            print(f"  {result.stderr}")
            return False
    except FileNotFoundError:
        print("  [SKIP] Ollama not found. Register manually:")
        print(f"    ollama create {ollama_name} -f {modelfile_path}")
        return False
    except subprocess.TimeoutExpired:
        print("  [TIMEOUT] Ollama took too long. Try manually:")
        print(f"    ollama create {ollama_name} -f {modelfile_path}")
        return False


def main():
    args = parse_args()

    print("=" * 60)
    print("Niam-Bay Export to Ollama")
    print("=" * 60)

    has_ollama = check_ollama()

    # Step 1: Merge
    if not args.skip_merge:
        merged_dir = merge_adapter(args.model)
    else:
        merged_dir = OUTPUT_DIR / f"niambay-{args.model}-merged"
        print(f"\n[1/4] SKIP merge (using {merged_dir})")

    # Step 2: Convert to GGUF
    if not args.skip_convert:
        gguf_file = convert_to_gguf(args.model, args.quantize)
    else:
        gguf_file = OUTPUT_DIR / "gguf" / f"niambay-{args.model}-{args.quantize}.gguf"
        if gguf_file.exists():
            print(f"\n[2/4] SKIP convert (using {gguf_file})")
        else:
            print(f"\n[2/4] SKIP convert (file not found: {gguf_file})")
            gguf_file = None

    # Step 3: Create Modelfile
    modelfile_path = create_modelfile(args.model, args.quantize, gguf_file)

    # Step 4: Register with Ollama
    if has_ollama and gguf_file and Path(gguf_file).exists():
        register_with_ollama(modelfile_path, args.ollama_name)
    else:
        print(f"\n[4/4] SKIP Ollama registration")
        if not has_ollama:
            print("  Install Ollama: https://ollama.ai")
        print(f"  When ready: ollama create {args.ollama_name} -f {modelfile_path}")

    # Final summary
    print("\n" + "=" * 60)
    print("Export Summary")
    print("=" * 60)
    print(f"  Merged model:  {OUTPUT_DIR / f'niambay-{args.model}-merged'}")
    print(f"  GGUF file:     {gguf_file or 'Not yet created (see instructions above)'}")
    print(f"  Modelfile:     {modelfile_path}")
    print(f"  Ollama name:   {args.ollama_name}")
    print()
    print("To use:")
    print(f"  ollama run {args.ollama_name}")
    print(f'  ollama run {args.ollama_name} "Qui es-tu ?"')
    print("=" * 60)


if __name__ == "__main__":
    main()
