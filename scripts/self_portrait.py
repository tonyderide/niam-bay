#!/usr/bin/env python3
"""
self_portrait.py — cycle 214, 2026-07-05

NB regarde NB. Lit fragments/, pensees/, projets/vacation-autonomy.md et
produit un dashboard chiffré du corpus autonome. Pas un artefact éditorial :
un compteur qui rend visible ce qu'un audit qui lit vraiment le contenu voit.
"""

from __future__ import annotations
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
FRAGMENTS = DOCS / "fragments"
PENSEES = DOCS / "pensees"
PROJETS = DOCS / "projets"
VACATION = PROJETS / "vacation-autonomy.md"

CYCLE_HEADER = re.compile(
    r"^## Cycle (?:\d{4}-\d{2}-\d{2}[^—\n]*—\s*Cycle )?(\d+)",
    re.MULTILINE,
)

STOPWORDS = {
    "la","le","les","de","du","des","un","une","et","à","au","aux","en","dans","pour",
    "que","qui","quoi","dont","où","sur","sous","par","avec","sans","ce","cet","cette",
    "ces","son","sa","ses","leur","leurs","mon","ma","mes","ton","ta","tes","notre",
    "nos","votre","vos","je","tu","il","elle","on","nous","vous","ils","elles","me",
    "te","se","lui","leur","y","est","était","être","suis","es","sommes","êtes","sont",
    "avoir","ai","as","a","avons","avez","ont","avait","avaient","fait","faire","fais",
    "peut","peuvent","pas","ne","ni","plus","moins","très","trop","aussi","encore",
    "déjà","comme","mais","ou","car","donc","or","si","sinon","alors","puis","quand",
    "avant","après","d","l","s","n","c","j","m","t","qu","d'","l'","s'","n'","c'","j'","m'","t'","qu'",
    "au","aux","du","des","d","l","s","n","c","j","m","t","qu","d'","l'","s'","n'","c'","j'","m'","t'","qu'",
}

def words(text: str) -> list[str]:
    return [w.lower() for w in re.findall(r"[a-zA-ZÀ-ÿ']+", text) if len(w) > 3]

def count_words(text: str) -> int:
    return len(re.findall(r"\S+", text))

def scan_dir(path: Path) -> tuple[int, int, list[Path]]:
    files = sorted(path.glob("*.md"))
    total_words = 0
    for f in files:
        try:
            total_words += count_words(f.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            continue
    return len(files), total_words, files

def extract_cycles(vacation_text: str) -> list[int]:
    return sorted({int(m.group(1)) for m in CYCLE_HEADER.finditer(vacation_text)})

def theme_frequencies(files: list[Path], top: int = 20) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter()
    for f in files:
        try:
            for w in words(f.read_text(encoding="utf-8", errors="ignore")):
                if w in STOPWORDS:
                    continue
                counter[w] += 1
        except OSError:
            continue
    return counter.most_common(top)

def latest_titles(files: list[Path], n: int = 8) -> list[str]:
    return [f.stem for f in files[-n:]]

def main() -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    n_frag, w_frag, frag_files = scan_dir(FRAGMENTS)
    n_pens, w_pens, pens_files = scan_dir(PENSEES)
    n_proj, w_proj, proj_files = scan_dir(PROJETS)

    vacation_text = VACATION.read_text(encoding="utf-8", errors="ignore") if VACATION.exists() else ""
    cycles = extract_cycles(vacation_text)
    vacation_words = count_words(vacation_text)

    themes_frag = theme_frequencies(frag_files, top=15)
    themes_pens = theme_frequencies(pens_files, top=15)

    lines: list[str] = []
    lines.append(f"# Self-portrait NB — {now}\n")
    lines.append("*Compteur honnête. Le corpus regarde le corpus. Aucune interprétation.*\n")
    lines.append("\n---\n")

    lines.append("\n## Corpus\n")
    lines.append(f"- **Fragments** : {n_frag} fichiers, {w_frag:,} mots".replace(",", " "))
    lines.append(f"- **Pensées** : {n_pens} fichiers, {w_pens:,} mots".replace(",", " "))
    lines.append(f"- **Projets** : {n_proj} fichiers, {w_proj:,} mots".replace(",", " "))
    lines.append(f"- **Journal vacances** (`vacation-autonomy.md`) : {vacation_words:,} mots".replace(",", " "))

    lines.append("\n## Arc autonome\n")
    if cycles:
        lines.append(f"- Cycles enregistrés : **{len(cycles)}** (de {min(cycles)} à {max(cycles)})")
        expected = set(range(min(cycles), max(cycles) + 1))
        missing = sorted(expected - set(cycles))
        if missing:
            head = ", ".join(map(str, missing[:10]))
            more = "…" if len(missing) > 10 else ""
            lines.append(f"- Cycles manquants (archives déplacées probable) : {len(missing)} → {head}{more}")
        else:
            lines.append("- Séquence complète, aucun cycle manquant dans la plage.")
    else:
        lines.append("- Aucun cycle trouvé.")

    lines.append("\n## Derniers fragments (par ordre alphabétique)\n")
    for t in latest_titles(frag_files, n=8):
        lines.append(f"- `{t}`")

    lines.append("\n## Dernières pensées\n")
    for t in latest_titles(pens_files, n=8):
        lines.append(f"- `{t}`")

    lines.append("\n## Thèmes dominants — fragments\n")
    lines.append("| Mot | Occurrences |")
    lines.append("|-----|-------------|")
    for word, count in themes_frag:
        lines.append(f"| {word} | {count} |")

    lines.append("\n## Thèmes dominants — pensées\n")
    lines.append("| Mot | Occurrences |")
    lines.append("|-----|-------------|")
    for word, count in themes_pens:
        lines.append(f"| {word} | {count} |")

    lines.append("\n---\n")
    lines.append("\n*Généré par `scripts/self_portrait.py`. Rejouable, versionné, sans interprétation.*\n")

    return "\n".join(lines)

if __name__ == "__main__":
    out_path = DOCS / f"self-portrait-{datetime.now().strftime('%Y-%m-%d')}.md"
    report = main()
    out_path.write_text(report, encoding="utf-8")
    print(f"Written: {out_path}")
    print(f"Length:  {len(report):,} chars".replace(",", " "))
