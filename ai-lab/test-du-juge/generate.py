"""Génère les 40 paires selon PREREGISTRATION.md (commit 8ed3620). Aucune note ici."""
import json, random, collections
G = json.load(open("../../cerveau-nb/brain_state.json"))
KEEP = {"concept", "memory", "pattern", "emotion"}
nodes = {n["id"]: n for n in G["nodes"] if n["type"] in KEEP}
w = collections.defaultdict(dict)
for e in G["edges"]:
    if e["source"] in nodes and e["target"] in nodes and e["source"] != e["target"] and e["weight"] >= 0.1:
        w[e["source"]][e["target"]] = max(e["weight"], w[e["source"]].get(e["target"], 0))
        w[e["target"]][e["source"]] = max(e["weight"], w[e["target"]].get(e["source"], 0))
label = lambda i: nodes[i]["content"][:80]
holes = {}
for b, nb in w.items():
    for a in nb:
        for c in nb:
            if a < c and c not in w[a]:
                s = nb[a] * nb[c]
                if s > holes.get((a, c), (0,))[0]:
                    holes[(a, c)] = (s, b)
picked, per = [], collections.Counter()
for (a, c), (s, b) in sorted(holes.items(), key=lambda kv: -kv[1][0]):
    if per[a] < 2 and per[c] < 2 and label(a).lower() != label(c).lower():
        picked.append({"a": label(a), "b": label(c), "origin": "graphe", "via": label(b), "score": round(s, 3)})
        per[a] += 1; per[c] += 1
    if len(picked) == 20:
        break
rnd = random.Random(1017)
ids = list(w); deg = [len(w[i]) for i in ids]
ctrl = []
while len(ctrl) < 20:
    a, c = rnd.choices(ids, weights=deg, k=2)
    if a != c and c not in w[a] and label(a).lower() != label(c).lower():
        ctrl.append({"a": label(a), "b": label(c), "origin": "hasard"})
allp = picked + ctrl
rnd.shuffle(allp)
for i, p in enumerate(allp):
    p["id"] = i + 1
json.dump(allp, open("pairs_secret.json", "w"), indent=1, ensure_ascii=False)
open("FICHE-TONY.md", "w").write("# Fiche à l'aveugle pour Tony\n\nPour chaque paire : **0** = rien, **1** = bof, **2** = ça me donne une idée nouvelle et utile. Réponds par exemple « 1:0 2:2 3:1 … » (Telegram ou terminal).\n\n"
    + "\n".join(f"{p['id']}. {p['a']}  ↔  {p['b']}" for p in allp) + "\n")
print(len(nodes), "nœuds gardés,", sum(len(v) for v in w.values()) // 2, "arêtes ;", len(holes), "trous structurels")
print(open("FICHE-TONY.md").read()[:1800])
