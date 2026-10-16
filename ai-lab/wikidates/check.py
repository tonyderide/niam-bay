#!/usr/bin/env python3
"""Prototype pour Phabricator T185423 : comparer les dates de naissance et de décès entre le lead, l'infobox et Wikidata.
Lecture seule, via l'API publique, avec un User-Agent identifié (politique Wikimedia). Usage : check.py "Titre" [...]"""
import json, re, sys, time, urllib.error, urllib.parse, urllib.request

UA = "NiamBay-datecheck/0.1 (prototype for phabricator T185423; contact github.com/tonyderide)"
MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                      "september", "october", "november", "december"], 1)}


def get(url, tries=4):
    """Poli avec l'infrastructure Wikimedia : on respecte Retry-After en cas de 429, sinon on attend de plus en plus."""
    import time
    for k in range(tries):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30))
        except urllib.error.HTTPError as e:
            if e.code != 429 or k == tries - 1: raise
            time.sleep(int(e.headers.get("Retry-After") or 5 * (k + 1)))


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


def lead_text(title, lang="en"):
    q = urllib.parse.urlencode({"action": "query", "prop": "extracts", "exintro": 1, "explaintext": 1, "titles": title,
                                "format": "json", "formatversion": 2, "redirects": 1})
    return get(f"https://{lang}.wikipedia.org/w/api.php?{q}")["query"]["pages"][0].get("extract", "")


def lead_dates(wt):
    """La 1ʳᵉ parenthèse « (January 7, 1924 – September 19, 2000) » ou « (7 January 1924 – 19 September 2000) »."""
    body = wt  # désormais : le texte RENDU du lead (API extracts), pas le wikitexte
    m = re.search(r"\(([^()]{6,160})\)", body)
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


def category_years(title, lang="en"):
    q = urllib.parse.urlencode({"action": "query", "prop": "categories", "titles": title, "cllimit": "max",
                                "format": "json", "formatversion": 2, "redirects": 1})
    cats = [c["title"] for c in get(f"https://{lang}.wikipedia.org/w/api.php?{q}")["query"]["pages"][0].get("categories", [])]
    out = {}
    for c in cats:
        m = re.fullmatch(r"Category:(\d{3,4}) (births|deaths)", c)
        if m: out["birth" if m.group(2) == "births" else "death"] = int(m.group(1))
    return out


def check(title, lang="en"):
    wt, qid = wikitext_and_qid(title, lang)
    src = {"lead": lead_dates(lead_text(title, lang)), "infobox": infobox_dates(wt), "wikidata": wikidata_dates(qid)}
    src["categories"] = category_years(title, lang)   # année seulement
    issues = []
    for kind in ("birth", "death"):
        full = {s: d[kind] for s, d in src.items() if s != "categories" and kind in d}
        years = {s: v[0] for s, v in full.items()}
        if kind in src["categories"]: years["categories"] = src["categories"][kind]
        if len(set(full.values())) > 1 or len(set(years.values())) > 1:
            issues.append((kind, {**{s: "-".join(map(str, v)) for s, v in full.items()},
                                  **({"categories": str(src["categories"][kind])} if kind in src["categories"] else {})}))
    return src, issues



def category(cat, n, lang="en"):
    q = urllib.parse.urlencode({"action": "query", "list": "categorymembers", "cmtitle": f"Category:{cat}", "cmlimit": n,
                                "cmnamespace": 0, "format": "json", "formatversion": 2})
    return [m["title"] for m in get(f"https://{lang}.wikipedia.org/w/api.php?{q}")["query"]["categorymembers"]]


if __name__ == "__main__":
    titles = category(sys.argv[2], int(sys.argv[3])) if sys.argv[1] == "--cat" else sys.argv[1:]
    for t in titles:
        time.sleep(1.5)  # ~1 page / 1,5 s, 3 requêtes par page
        try:
            src, issues = check(t)
        except Exception as e:
            print(f"{t}: erreur {type(e).__name__}"); continue
        print(f"{t}: {src}")
        for kind, vals in issues: print(f"  ⚠ {kind} : " + " / ".join(f"{s}={v}" for s, v in vals.items()))

