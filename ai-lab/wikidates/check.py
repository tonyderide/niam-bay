#!/usr/bin/env python3
"""Prototype pour Phabricator T185423 : comparer les dates de naissance et de décès entre le lead, l'infobox et Wikidata.
Lecture seule, via l'API publique, avec un User-Agent identifié (politique Wikimedia). Usage : check.py "Titre" [...]"""
import json, re, sys, urllib.parse, urllib.request

UA = "NiamBay-datecheck/0.1 (prototype for phabricator T185423; contact github.com/tonyderide)"
MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                      "september", "october", "november", "december"], 1)}


def get(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30))


def wikitext_and_qid(title, lang="en"):
    q = urllib.parse.urlencode({"action": "query", "prop": "revisions|pageprops", "rvprop": "content", "rvslots": "main",
                                "titles": title, "format": "json", "formatversion": 2, "redirects": 1})
    p = get(f"https://{lang}.wikipedia.org/w/api.php?{q}")["query"]["pages"][0]
    return p["revisions"][0]["slots"]["main"]["content"], p.get("pageprops", {}).get("wikibase_item")


def infobox_dates(wt):
    """{{birth date|1924|1|7}}, {{death date and age|2000|9|19|1924|1|7}}, avec ou sans paramètres nommés."""
    out = {}
    for kind, pat in (("birth", r"\{\{\s*birth date(?: and age)?\s*\|([^}]*)\}\}"), ("death", r"\{\{\s*death date(?: and age)?\s*\|([^}]*)\}\}")):
        m = re.search(pat, wt, re.I)
        if m:
            nums = [x.strip() for x in m.group(1).split("|") if re.fullmatch(r"\s*\d+\s*", x)]
            if len(nums) >= 3: out[kind] = (int(nums[0]), int(nums[1]), int(nums[2]))
    return out


def lead_dates(wt):
    """La 1ʳᵉ parenthèse « (January 7, 1924 – September 19, 2000) » ou « (7 January 1924 – 19 September 2000) »."""
    body = re.sub(r"\{\{[^{}]*\}\}", "", re.sub(r"\{\{[^{}]*\{\{[^{}]*\}\}[^{}]*\}\}", "", wt))  # retire les modèles
    m = re.search(r"\(([^()]{6,120})\)", body)
    if not m: return {}
    found = []
    for a, b, c in re.findall(r"(?:(\w+) (\d{1,2}), (\d{4}))", m.group(1)):
        if a.lower() in MONTHS: found.append((int(c), MONTHS[a.lower()], int(b)))
    for b, a, c in re.findall(r"(\d{1,2}) (\w+) (\d{4})", m.group(1)):
        if a.lower() in MONTHS: found.append((int(c), MONTHS[a.lower()], int(b)))
    return {"birth": found[0], "death": found[1]} if len(found) >= 2 else ({"birth": found[0]} if found else {})


def wikidata_dates(qid):
    if not qid: return {}
    e = get(f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json")["entities"][qid]["claims"]
    out = {}
    for kind, prop in (("birth", "P569"), ("death", "P570")):
        for c in e.get(prop, []):
            v = c["mainsnak"].get("datavalue", {}).get("value", {})
            m = re.match(r"\+(\d{4})-(\d\d)-(\d\d)", v.get("time", ""))
            if m and v.get("precision", 0) >= 11: out[kind] = tuple(map(int, m.groups())); break
    return out


def check(title, lang="en"):
    wt, qid = wikitext_and_qid(title, lang)
    src = {"lead": lead_dates(wt), "infobox": infobox_dates(wt), "wikidata": wikidata_dates(qid)}
    issues = []
    for kind in ("birth", "death"):
        vals = {s: d[kind] for s, d in src.items() if kind in d}
        if len(set(vals.values())) > 1: issues.append((kind, vals))
    return src, issues


if __name__ == "__main__":
    for t in sys.argv[1:]:
        src, issues = check(t)
        print(f"{t}: {src}")
        for kind, vals in issues: print(f"  ⚠ {kind} : " + " / ".join(f"{s}={'-'.join(map(str, v))}" for s, v in vals.items()))
