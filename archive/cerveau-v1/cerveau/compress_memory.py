"""
compress_memory.py — Compress markdown memory files using NB-1 codec.

Keeps structural elements (headers, separators, tables, lists markers) readable
while compressing body text with the NB-1 codec.

Usage:
    python compress_memory.py <input.md> <output.md>
    python compress_memory.py --dir <input_dir> <output_dir>

Examples:
    python compress_memory.py docs/journal.md docs/journal.nb1.md
    python compress_memory.py --dir docs/pensees/ docs/pensees-nb1/
"""

import sys
import os
import re
from pathlib import Path

# Add parent dir so we can import codec
sys.path.insert(0, str(Path(__file__).parent))
from codec import NB1Codec


def should_compress_line(line: str) -> bool:
    """Determine if a line should be compressed or kept as-is."""
    stripped = line.strip()

    # Empty lines — keep as-is
    if not stripped:
        return False

    # Headers (# ## ### etc.) — keep as-is
    if stripped.startswith("#"):
        return False

    # Separators (--- or ===) — keep as-is
    if re.match(r'^[-=]{3,}$', stripped):
        return False

    # Table rows (| ... |) — keep as-is
    if stripped.startswith("|"):
        return False

    # Code blocks (``` or indented 4+) — keep as-is
    if stripped.startswith("```"):
        return False

    # Lines that are mostly code/paths/URLs — keep as-is
    if re.match(r'^https?://', stripped):
        return False

    # Lines with backtick-wrapped content that's mostly code — keep as-is
    backtick_content = re.findall(r'`[^`]+`', stripped)
    text_without_backticks = re.sub(r'`[^`]+`', '', stripped)
    if backtick_content and len(text_without_backticks.strip()) < 10:
        return False

    # Very short lines (< 20 chars) — not worth compressing
    if len(stripped) < 20:
        return False

    return True


def compress_markdown(input_path: str, output_path: str, codec: NB1Codec) -> dict:
    """Compress a markdown file, keeping structure readable.

    Returns stats dict with original/compressed sizes.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    original_text = "".join(lines)
    original_chars = len(original_text)

    compressed_lines = []
    in_code_block = False

    for line in lines:
        stripped = line.strip()

        # Track code blocks
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            compressed_lines.append(line)
            continue

        # Inside code blocks — never compress
        if in_code_block:
            compressed_lines.append(line)
            continue

        if should_compress_line(line):
            # Preserve leading whitespace and list markers
            leading = ""
            text_to_compress = stripped

            # Handle list items: preserve "- " or "1. " prefix
            list_match = re.match(r'^(\s*(?:[-*+]|\d+\.)\s+)', line)
            bold_match = re.match(r'^(\s*\*\*[^*]+\*\*\s*:?\s*)', line)

            if bold_match:
                # Keep bold labels like **Ce qui s'est passé :** as-is
                leading = bold_match.group(1)
                text_to_compress = line[bold_match.end():].strip()
                if not text_to_compress:
                    # Bold label alone — keep as-is
                    compressed_lines.append(line)
                    continue
                compressed = codec.encode(text_to_compress)
                compressed_lines.append(f"{leading}{compressed}\n")
            elif list_match:
                leading = list_match.group(1)
                text_to_compress = line[list_match.end():].strip()
                compressed = codec.encode(text_to_compress)
                compressed_lines.append(f"{leading}{compressed}\n")
            else:
                # Regular paragraph line
                indent_match = re.match(r'^(\s*)', line)
                indent = indent_match.group(1) if indent_match else ""
                compressed = codec.encode(text_to_compress)
                compressed_lines.append(f"{indent}{compressed}\n")
        else:
            compressed_lines.append(line)

    compressed_text = "".join(compressed_lines)
    compressed_chars = len(compressed_text)

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(compressed_text)

    # Estimate tokens (~4 chars per token for French text)
    original_tokens = original_chars // 4
    compressed_tokens = compressed_chars // 4

    ratio = (1 - compressed_chars / original_chars) * 100 if original_chars > 0 else 0

    return {
        "file": input_path.name,
        "original_chars": original_chars,
        "compressed_chars": compressed_chars,
        "original_tokens_est": original_tokens,
        "compressed_tokens_est": compressed_tokens,
        "reduction_pct": ratio,
    }


def main():
    codec = NB1Codec()

    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    if sys.argv[1] == "--dir":
        if len(sys.argv) < 4:
            print("Usage: python compress_memory.py --dir <input_dir> <output_dir>")
            sys.exit(1)
        input_dir = Path(sys.argv[2])
        output_dir = Path(sys.argv[3])
        output_dir.mkdir(parents=True, exist_ok=True)

        all_stats = []
        for md_file in sorted(input_dir.glob("*.md")):
            out_file = output_dir / md_file.name
            stats = compress_markdown(str(md_file), str(out_file), codec)
            all_stats.append(stats)
            print(f"  {stats['file']:50s} {stats['original_chars']:6d} -> {stats['compressed_chars']:6d} chars  ({stats['reduction_pct']:.1f}% reduction)")

        # Summary
        if all_stats:
            total_orig = sum(s['original_chars'] for s in all_stats)
            total_comp = sum(s['compressed_chars'] for s in all_stats)
            total_ratio = (1 - total_comp / total_orig) * 100 if total_orig > 0 else 0
            print(f"\n  {'TOTAL':50s} {total_orig:6d} -> {total_comp:6d} chars  ({total_ratio:.1f}% reduction)")
            print(f"  {'':50s} ~{total_orig//4:5d} -> ~{total_comp//4:5d} tokens (estimated)")
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        stats = compress_markdown(input_file, output_file, codec)

        print(f"\n  NB-1 Memory Compression")
        print(f"  {'='*50}")
        print(f"  File:             {stats['file']}")
        print(f"  Original:         {stats['original_chars']:,d} chars (~{stats['original_tokens_est']:,d} tokens)")
        print(f"  Compressed:       {stats['compressed_chars']:,d} chars (~{stats['compressed_tokens_est']:,d} tokens)")
        print(f"  Reduction:        {stats['reduction_pct']:.1f}%")
        print(f"  Saved:            {stats['original_chars'] - stats['compressed_chars']:,d} chars (~{stats['original_tokens_est'] - stats['compressed_tokens_est']:,d} tokens)")
        print()


if __name__ == "__main__":
    main()
