"""Registre des pré-enregistrements : docs/registre-verdicts.json (verdict + citation exacte relevés à la main) + date du premier commit.
python3 scripts/registre_prereg.py  -> docs/registre-prereg.md ; signale tout PREREG sans entrée, et toute citation qui n'est plus dans sa source."""
import collections, glob, json, os, subprocess
R0 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = {x["fichier"]: x for x in json.load(open(os.path.join(R0, "docs", "registre-verdicts.json")))}
def date(f):
    r = subprocess.run(["git", "log", "--diff-filter=A", "--format=%cs", "--", f], cwd=R0, capture_output=True, text=True).stdout.split()
    return r[-1] if r else "non commité"
def titre(f):
    for l in open(os.path.join(R0, f), errors="ignore"):
        if l.startswith("#"): return l.strip("# \n").replace("|", "/")[:95]
F = sorted(os.path.relpath(f, R0) for f in glob.glob(os.path.join(R0, "ai-lab", "**", "PREREG*.md"), recursive=True))
manque = [f for f in F if f not in V]
abime = [f for f, x in V.items() if x["citation"] and x["citation"] not in open(os.path.join(R0, x["source"]), errors="ignore").read()]
rows = sorted((date(f), f) for f in F if f in V)
c = collections.Counter(V[f]["verdict"] for _, f in rows)
L = ["# Registre des pré-enregistrements", "",
     "Lire aussi `registre-meta.md` : combien de ces « démontré » le hasard donnerait seul. Chaque ligne : la date du premier commit du pré-enregistrement (la preuve qu'il existait avant les données), le verdict, et la phrase exacte de la source. Généré par `scripts/registre_prereg.py` à partir de `docs/registre-verdicts.json`.", "",
     "**Bilan : " + " · ".join(f"{k} {v}" for k, v in c.most_common()) + f"** (sur {len(rows)}).", ""]
if manque: L += ["⚠️ Pré-enregistrements sans verdict relevé : " + ", ".join(manque), ""]
if abime: L += ["⚠️ Citations qui ne sont plus dans leur source : " + ", ".join(abime), ""]
L += ["| Date | Pré-enregistrement | Verdict | En bref |", "|---|---|---|---|"]
for d, f in rows:
    x = V[f]; L.append(f"| {d} | [{titre(f)}](../{f}) | **{x['verdict']}** | {x['resume'].replace('|', '/')} ([source](../{x['source']})) |")
open(os.path.join(R0, "docs", "registre-prereg.md"), "w").write("\n".join(L) + "\n")
print(L[4]); print("manquants", len(manque), "citations abîmées", len(abime))
