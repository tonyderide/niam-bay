#!/usr/bin/env python3
"""Preuve brute pour la vérification humaine : 1ʳᵉ parenthèse du lead, lignes de date de l'infobox, déclarations P569/P570
de Wikidata (avec précision et rang), et catégories. Je juge moi-même chaque cas à partir de ça."""
import re, sys, time
from check import get, lead_text, wikitext_and_qid, category_years
for t in sys.argv[1:]:
    time.sleep(2)
    wt, qid = wikitext_and_qid(t); lead = lead_text(t)
    m = re.search(r"\(([^()]{6,160})\)", lead)
    print(f"== {t} ({qid})\n  lead : ({m.group(1) if m else '?'})")
    for l in re.findall(r"\|\s*(?:birth|death)_date\s*=\s*([^\n]{0,80})", wt): print("  infobox :", l)
    e = get(f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json")["entities"][qid]["claims"]
    for p in ("P569", "P570"):
        for c in e.get(p, []):
            v = c["mainsnak"].get("datavalue", {}).get("value", {}); print(f"  wikidata {p} : {v.get('time')} prec={v.get('precision')} rang={c['rank']}")
    print("  catégories :", category_years(t))
