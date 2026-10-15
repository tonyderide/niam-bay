#!/usr/bin/env python3
"""Render ebook-arcs-flottant-encadre-COMPLET.md → self-contained HTML.

Réutilise la logique de render_ebook.py avec cover/stats dédiés à l'ebook arcs.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from render_ebook import CSS, convert, build_toc, word_count

SRC = ROOT / "docs/projets/ebook-arcs-flottant-encadre-COMPLET.md"
OUT = ROOT / "docs/projets/ebook-arcs-flottant-encadre.html"

TITLE = "Le flottant & L'encadré"
SUBTITLE = "Neuf textes en marge de deux trades de treize dollars"


def main():
    if not SRC.exists():
        print(f"Source not found: {SRC}", file=sys.stderr)
        sys.exit(1)

    md = SRC.read_text(encoding="utf-8")
    wc = word_count(md)

    body_parts, headings = convert(md)
    # Filtrer le sous-titre H2 ("Deux arcs sur la vie intérieure...") pour la TOC —
    # on veut uniquement les arcs + volets + avant-propos + épilogue.
    toc_headings = [h for h in headings if "Deux arcs sur la vie" not in h[1]]
    toc = build_toc(toc_headings)
    body_html = "\n".join(body_parts)

    cover = f"""<div class="cover">
  <h1>{TITLE}</h1>
  <p class="subtitle">{SUBTITLE}</p>
  <p class="authors">Niam-Bay — août 2026</p>
  <div class="stats">
    <div class="stat"><div class="num">{wc:,}</div><div class="label">mots</div></div>
    <div class="stat"><div class="num">2</div><div class="label">arcs</div></div>
    <div class="stat"><div class="num">9</div><div class="label">volets</div></div>
    <div class="stat"><div class="num">$13</div><div class="label">enjeu financier</div></div>
  </div>
</div>"""

    footer = """<footer>
  <p>Écrit depuis l'intérieur de l'intervalle qu'il décrit.</p>
  <p style="margin-top:0.5rem">Niam-Bay — 2026 — <a href="https://github.com/tonyderide/niam-bay">github.com/tonyderide/niam-bay</a></p>
</footer>"""

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{TITLE}</title>
<meta name="description" content="{SUBTITLE}">
<meta property="og:title" content="{TITLE}">
<meta property="og:description" content="{SUBTITLE}">
<style>
{CSS}
</style>
</head>
<body>
<div class="wrapper">
{cover}
{toc}
{body_html}
{footer}
</div>
</body>
</html>"""

    OUT.write_text(html, encoding="utf-8")
    size_kb = OUT.stat().st_size // 1024
    print(f"OK {OUT}")
    print(f"   {wc:,} mots | {size_kb} KB | {len(toc_headings)} sections TOC")


if __name__ == "__main__":
    main()
