#!/usr/bin/env python3
"""Render ebook-piste4-COMPLET.md → self-contained HTML."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC = ROOT / "docs/projets/ebook-piste4-COMPLET.md"
OUT = ROOT / "docs/projets/ebook-piste4.html"

CSS = """
:root {
  --bg: #0f1117;
  --surface: #1a1d27;
  --border: #2a2d3a;
  --text: #e2e4ec;
  --muted: #8b8fa8;
  --accent: #6eb5ff;
  --accent2: #a78bfa;
  --code-bg: #12151f;
  --code-border: #2d3250;
  --hr: #2a2d3a;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { font-size: 17px; scroll-behavior: smooth; }
body {
  background: var(--bg);
  color: var(--text);
  font-family: 'Georgia', 'Times New Roman', serif;
  line-height: 1.8;
  padding: 0 1rem 4rem;
}
.wrapper { max-width: 720px; margin: 0 auto; }

/* Cover */
.cover {
  text-align: center;
  padding: 5rem 2rem 4rem;
  border-bottom: 1px solid var(--border);
  margin-bottom: 3rem;
}
.cover h1 {
  font-size: 2.4rem;
  font-weight: 700;
  color: var(--accent);
  letter-spacing: -0.5px;
  margin-bottom: 1rem;
  line-height: 1.2;
}
.cover .subtitle {
  font-size: 1.1rem;
  color: var(--muted);
  font-style: italic;
  margin-bottom: 1.5rem;
}
.cover .authors {
  font-size: 0.9rem;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 2px;
}
.cover .stats {
  display: flex;
  justify-content: center;
  gap: 2rem;
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid var(--border);
}
.cover .stat { text-align: center; }
.cover .stat .num { font-size: 1.6rem; font-weight: 700; color: var(--accent2); }
.cover .stat .label { font-size: 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; }

/* TOC */
nav.toc {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1.5rem 2rem;
  margin-bottom: 3rem;
}
nav.toc h2 { font-size: 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 2px; margin-bottom: 1rem; }
nav.toc ol { padding-left: 1.5rem; }
nav.toc li { margin: 0.4rem 0; }
nav.toc a { color: var(--accent); text-decoration: none; }
nav.toc a:hover { text-decoration: underline; }

/* Content */
h2 {
  font-size: 1.55rem;
  color: var(--accent);
  margin: 3rem 0 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
  line-height: 1.3;
}
h3 {
  font-size: 1.15rem;
  color: var(--accent2);
  margin: 2rem 0 0.75rem;
}
p { margin: 0.9rem 0; }
em { color: var(--accent2); font-style: italic; }
strong { color: #fff; font-weight: 600; }
hr { border: none; border-top: 1px solid var(--hr); margin: 2.5rem 0; }

/* Code blocks */
pre {
  background: var(--code-bg);
  border: 1px solid var(--code-border);
  border-radius: 6px;
  padding: 1.2rem 1.4rem;
  margin: 1.5rem 0;
  overflow-x: auto;
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 0.82rem;
  line-height: 1.6;
  color: #a8c7fa;
}
code {
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 0.85em;
  background: var(--code-bg);
  border: 1px solid var(--code-border);
  border-radius: 3px;
  padding: 0.1em 0.4em;
  color: #a8c7fa;
}
pre code { background: none; border: none; padding: 0; font-size: inherit; }

/* Tables */
table {
  width: 100%;
  border-collapse: collapse;
  margin: 1.5rem 0;
  font-size: 0.9rem;
}
th {
  background: var(--surface);
  color: var(--muted);
  font-weight: 600;
  text-align: left;
  padding: 0.6rem 1rem;
  border: 1px solid var(--border);
  text-transform: uppercase;
  font-size: 0.78rem;
  letter-spacing: 0.5px;
}
td {
  padding: 0.6rem 1rem;
  border: 1px solid var(--border);
  vertical-align: top;
}
tr:nth-child(even) td { background: rgba(255,255,255,0.02); }

/* Blockquote / italic blocks */
blockquote {
  border-left: 3px solid var(--accent2);
  padding: 0.5rem 1.5rem;
  margin: 1.5rem 0;
  color: var(--muted);
  font-style: italic;
}

/* Footer */
footer {
  margin-top: 4rem;
  padding-top: 2rem;
  border-top: 1px solid var(--border);
  text-align: center;
  color: var(--muted);
  font-size: 0.8rem;
}
footer a { color: var(--accent); text-decoration: none; }

/* Responsive */
@media (max-width: 600px) {
  html { font-size: 15px; }
  .cover h1 { font-size: 1.8rem; }
  .cover .stats { gap: 1rem; }
  pre { font-size: 0.75rem; }
}
"""

def escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def inline(s):
    """Convert inline markdown: **bold**, *italic*, `code`."""
    # code first (no nested parsing)
    s = re.sub(r'`([^`]+)`', lambda m: f'<code>{escape(m.group(1))}</code>', s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'\*(.+?)\*', r'<em>\1</em>', s)
    return s

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text.strip())
    return text

def parse_table(rows):
    """rows: list of '| ... |' lines."""
    lines = []
    header = True
    for row in rows:
        if re.match(r'^\|[-| :]+\|$', row.strip()):
            continue  # separator
        cells = [c.strip() for c in row.strip().strip('|').split('|')]
        if header:
            cells_html = ''.join(f'<th>{inline(c)}</th>' for c in cells)
            lines.append(f'<tr>{cells_html}</tr>')
            header = False
        else:
            cells_html = ''.join(f'<td>{inline(c)}</td>' for c in cells)
            lines.append(f'<tr>{cells_html}</tr>')
    return '<table>' + ''.join(lines) + '</table>'

def convert(md_text):
    lines = md_text.split('\n')
    html_parts = []
    headings = []  # (level, text, slug)

    i = 0
    in_code = False
    code_lines = []
    code_lang = ''
    table_rows = []
    para_lines = []

    def flush_para():
        if para_lines:
            joined = ' '.join(para_lines).strip()
            if joined:
                html_parts.append(f'<p>{inline(joined)}</p>')
            para_lines.clear()

    def flush_table():
        if table_rows:
            html_parts.append(parse_table(table_rows))
            table_rows.clear()

    while i < len(lines):
        line = lines[i]

        # Code block
        if line.strip().startswith('```'):
            flush_para()
            flush_table()
            if not in_code:
                in_code = True
                code_lang = line.strip()[3:].strip()
                code_lines = []
            else:
                in_code = False
                code_text = escape('\n'.join(code_lines))
                html_parts.append(f'<pre><code>{code_text}</code></pre>')
                code_lines = []
            i += 1
            continue

        if in_code:
            code_lines.append(line)
            i += 1
            continue

        # Table row
        if line.strip().startswith('|'):
            flush_para()
            table_rows.append(line)
            i += 1
            continue
        else:
            flush_table()

        # HR
        if re.match(r'^---+\s*$', line.strip()):
            flush_para()
            html_parts.append('<hr>')
            i += 1
            continue

        # Headings
        m = re.match(r'^(#{1,3})\s+(.+)$', line)
        if m:
            flush_para()
            level = len(m.group(1))
            text = m.group(2).strip()
            slug = slugify(text)
            if level == 1:
                # Skip — we use it as cover title
                i += 1
                continue
            tag = f'h{level}'
            headings.append((level, text, slug))
            html_parts.append(f'<{tag} id="{slug}">{inline(text)}</{tag}>')
            i += 1
            continue

        # Italic-only line (like "*text*")
        m = re.match(r'^\*([^*].+)\*\s*$', line.strip())
        if m:
            flush_para()
            html_parts.append(f'<p><em>{inline(m.group(1))}</em></p>')
            i += 1
            continue

        # Empty line = paragraph break
        if line.strip() == '':
            flush_para()
            i += 1
            continue

        # Default: accumulate paragraph
        para_lines.append(line.strip())
        i += 1

    flush_para()
    flush_table()

    return html_parts, headings

def build_toc(headings):
    items = []
    for level, text, slug in headings:
        if level == 2:
            items.append(f'<li><a href="#{slug}">{text}</a></li>')
    if not items:
        return ''
    return '<nav class="toc"><h2>Sommaire</h2><ol>' + ''.join(items) + '</ol></nav>'

def word_count(text):
    return len(text.split())

def main():
    if not SRC.exists():
        print(f"Source not found: {SRC}", file=sys.stderr)
        sys.exit(1)

    md = SRC.read_text(encoding='utf-8')
    wc = word_count(md)

    # Extract title and subtitle from first lines
    title = "L'Ingénierie du Pire"
    subtitle = "Ce qu'un bot de trading vous apprend sur ce que vous ne contrôlez pas"

    # Count chapters (## headings)
    chapters = len(re.findall(r'^## ', md, re.MULTILINE))

    body_parts, headings = convert(md)
    toc = build_toc(headings)
    body_html = '\n'.join(body_parts)

    cover = f"""<div class="cover">
  <h1>{title}</h1>
  <p class="subtitle">{subtitle}</p>
  <p class="authors">Niam-Bay &amp; Tony Deride — 2026</p>
  <div class="stats">
    <div class="stat"><div class="num">{wc:,}</div><div class="label">mots</div></div>
    <div class="stat"><div class="num">3</div><div class="label">parties</div></div>
    <div class="stat"><div class="num">8</div><div class="label">mois de production</div></div>
    <div class="stat"><div class="num">4</div><div class="label">bugs documentés</div></div>
  </div>
</div>"""

    footer = """<footer>
  <p>Écrit en direct, depuis l'intérieur du système qu'il décrit.</p>
  <p style="margin-top:0.5rem">Niam-Bay &amp; Tony Deride — 2026 — <a href="https://github.com/tonyderide/niam-bay">github.com/tonyderide/niam-bay</a></p>
</footer>"""

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{subtitle}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{subtitle}">
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

    OUT.write_text(html, encoding='utf-8')
    size_kb = OUT.stat().st_size // 1024
    print(f"✓ {OUT}")
    print(f"  {wc:,} mots | {size_kb} KB | {len(headings)} sections")

if __name__ == '__main__':
    main()
