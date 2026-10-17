"""Mémoire falsifiable : chaque souvenir de NB qui parle du monde porte une sonde, et le monde juge.

Un souvenir n'est pas vrai parce qu'il est écrit. Ici, chaque affirmation vérifiable a une commande et un motif attendu.
`python3 verify.py`          → rapport (docs/memoire-verif.md), code 1 si au moins un souvenir est contredit.
`python3 verify.py --amend`  → pour chaque souvenir contredit, un modèle propose une correction (sans l'appliquer).
"""
import json, os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../.."))
MEM = os.path.expanduser("~/.claude/projects/-home-tony/memory")
REPORT = os.path.join(REPO, "docs/memoire-verif.md")


def run(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        return (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return "TIMEOUT"


def amend(probe, observed):
    path = os.path.join(MEM, probe["memory"] + ".md")
    text = open(path).read() if os.path.exists(path) else "(pas de fichier mémoire)"
    prompt = (f"Un souvenir de NB est contredit par la réalité.\nAffirmation : {probe['claim']}\nCommande : {probe['cmd']}\n"
              f"Attendu (regex) : {probe['expect']}\nObservé : {observed}\n\nFichier mémoire :\n{text[:4000]}\n\n"
              "Propose en 1 à 3 lignes la correction à faire dans le souvenir (ou dis si c'est la sonde qui est fausse). N'invente rien.")
    r = subprocess.run(["claude", "-p", prompt, "--model", "claude-haiku-5-5", "--tools", ""], capture_output=True, text=True, timeout=180)
    return r.stdout.strip()


def main(argv):
    probes = json.load(open(os.path.join(HERE, "probes.json")))
    rows, bad = [], 0
    for p in probes:
        out = run(p["cmd"])
        ok = re.search(p["expect"], out, re.M) is not None
        bad += not ok
        row = {"memory": p["memory"], "claim": p["claim"], "ok": ok, "observed": out[-300:]}
        if not ok and "--amend" in argv:
            row["proposal"] = amend(p, out[-1500:])
        rows.append(row)
    lines = [f"# Vérification de la mémoire de NB ({time.strftime('%F %H:%M')})", "",
             f"{len(rows) - bad}/{len(rows)} souvenirs confirmés par le monde, **{bad} contredits**.", ""]
    for r in rows:
        lines.append(f"- {'✅' if r['ok'] else '❌'} `{r['memory']}` : {r['claim']}")
        if not r["ok"]:
            lines.append(f"  - observé : `{r['observed'].replace(chr(10), ' | ')[:200]}`")
            if r.get("proposal"):
                lines.append("  - correction proposée : " + r["proposal"].replace("\n", " "))
    open(REPORT, "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
