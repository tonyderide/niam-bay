#!/usr/bin/env python3
"""
prospect_finder.py — Identifie des candidats pour audit Angular 49€.

Stratégie:
  1. Deux requêtes gh search repos (variées) → ~50 repos candidats
  2. Pour chaque repo, fetch git tree racine (1 API call)
  3. Filtre: ne garde que les repos avec angular.json
  4. Score: solo-user > org, low-stars > populaire, récent > vieux,
     anti-templates (boilerplate/starter/tuto), bonus homepage
  5. Output: scripts/audit-samples/prospects-week1.csv (trié score desc)

Usage:
    python3 scripts/prospect_finder.py

Prérequis:
    gh CLI authentifié (gh auth status)
    Rate limit: ~50 calls (largement sous 5000/h)

Auteur: NiamBay (cycle 17 vacation, 2026-05-07)
"""
import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

OUTPUT = Path(__file__).parent / "audit-samples" / "prospects-week1.csv"

QUERIES = [
    {"q": "angular", "lang": "typescript", "stars": "3..40", "updated": ">2026-01-01", "limit": 30},
    {"q": "angular dashboard", "lang": "typescript", "stars": "1..25", "updated": ">2026-01-01", "limit": 20},
]

TEMPLATE_KEYWORDS = [
    "template", "boilerplate", "starter", "example", "tutorial",
    "course", "demo", "skeleton", "playground", "tuto", "training",
    "udemy", "exercise", "sample", "test-",
]


def gh_search(query, language, stars, updated, limit):
    fields = "fullName,description,stargazersCount,pushedAt,owner,url,defaultBranch,homepage"
    cmd = [
        "gh", "search", "repos", query,
        f"--language={language}",
        f"--stars={stars}",
        f"--updated={updated}",
        f"--limit={limit}",
        f"--json={fields}",
    ]
    return json.loads(subprocess.check_output(cmd, text=True))


def gh_tree(full_name, branch):
    try:
        out = subprocess.check_output(
            ["gh", "api", f"repos/{full_name}/git/trees/{branch}"],
            text=True, stderr=subprocess.DEVNULL,
        )
        return [t["path"] for t in json.loads(out).get("tree", [])]
    except subprocess.CalledProcessError:
        return []


def looks_like_template(full_name, description):
    blob = (full_name + " " + (description or "")).lower()
    return any(kw in blob for kw in TEMPLATE_KEYWORDS)


def days_since(iso_ts):
    dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - dt).days


def score_repo(repo, paths):
    sig = []
    score = 0

    if "angular.json" not in paths:
        return None
    score += 30
    sig.append("angular.json")

    if repo["owner"]["type"] == "User":
        score += 15
        sig.append("solo-user")
    else:
        sig.append("org-NEG")
        score -= 5

    stars = repo["stargazersCount"]
    if stars <= 5:
        score += 18
        sig.append(f"stars-{stars}")
    elif stars <= 15:
        score += 12
        sig.append(f"stars-{stars}")
    elif stars <= 30:
        score += 5
        sig.append(f"stars-{stars}")
    else:
        sig.append(f"stars-{stars}-NEG")

    if looks_like_template(repo["fullName"], repo.get("description")):
        score -= 35
        sig.append("template-NEG")

    if repo.get("homepage"):
        score += 8
        sig.append("homepage")

    days = days_since(repo["pushedAt"])
    if days <= 30:
        score += 10
        sig.append(f"active-{days}d")
    elif days <= 90:
        score += 5
        sig.append(f"recent-{days}d")
    else:
        sig.append(f"stale-{days}d-NEG")

    has_readme = any(p.lower().startswith("readme") for p in paths)
    if has_readme:
        score += 3
        sig.append("readme")

    if "package.json" in paths:
        score += 3
        sig.append("package.json")

    return score, sig


def main():
    seen = set()
    rows = []
    print("→ Lancement gh search (2 requêtes)…")
    for q in QUERIES:
        repos = gh_search(q["q"], q["lang"], q["stars"], q["updated"], q["limit"])
        print(f"  query={q['q']!r}: {len(repos)} repos")
        for r in repos:
            fn = r["fullName"]
            if fn in seen:
                continue
            seen.add(fn)
            paths = gh_tree(fn, r.get("defaultBranch") or "main")
            res = score_repo(r, paths)
            if res is None:
                continue
            score, sig = res
            days = days_since(r["pushedAt"])
            rows.append({
                "score": score,
                "owner_type": r["owner"]["type"],
                "owner": r["owner"]["login"],
                "full_name": fn,
                "stars": r["stargazersCount"],
                "days_since_push": days,
                "homepage": r.get("homepage") or "",
                "description": (r.get("description") or "").replace("\n", " ")[:140],
                "signals": ",".join(sig),
                "repo_url": r["url"],
                "owner_url": r["owner"]["url"],
            })

    rows.sort(key=lambda x: -x["score"])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        print("✗ aucun prospect angular trouvé")
        return
    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\n✓ {len(rows)} prospects qualifiés → {OUTPUT}")
    print("\nTop 5:")
    for r in rows[:5]:
        print(f"  [{r['score']:3d}] {r['full_name']:<45s} ★{r['stars']:<3d} {r['days_since_push']}d  {r['signals']}")


if __name__ == "__main__":
    main()
