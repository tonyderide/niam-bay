"""Notation à l'aveugle par Haiku (une paire par appel, sans l'origine), puis le test pré-enregistré."""
import concurrent.futures as cf, json, os, random, re, subprocess
P = json.load(open("pairs_secret.json"))


def note(p):
    q = (f"Deux notions tirées de la mémoire d'un assistant IA personnel (qui aide un développeur, trade un petit compte crypto, écrit un journal) :\n"
         f"A = « {p['a']} »\nB = « {p['b']} »\n"
         "Est-ce que rapprocher A et B suggère une idée nouvelle ET utile (un projet, un outil, une décision) ? "
         "Réponds UNIQUEMENT par un chiffre : 0 (rien), 1 (vague), 2 (oui, une idée concrète).")
    r = subprocess.run(["claude", "-p", q, "--model", "claude-haiku-5-5", "--tools", ""], capture_output=True, text=True,
                       timeout=120, env={**os.environ, "NB_FACTCHECK_CHILD": "1"})
    m = re.search(r"[012]", r.stdout)
    return int(m.group(0)) if m else None


with cf.ThreadPoolExecutor(4) as ex:
    notes = list(ex.map(note, P))
for p, n in zip(P, notes):
    p["haiku"] = n
json.dump(P, open("pairs_secret.json", "w"), indent=1, ensure_ascii=False)
g = [p["haiku"] for p in P if p["origin"] == "graphe" and p["haiku"] is not None]
h = [p["haiku"] for p in P if p["origin"] == "hasard" and p["haiku"] is not None]
diff = sum(g) / len(g) - sum(h) / len(h)
rnd = random.Random(0); pool = g + h; hits = 0
for _ in range(20000):
    rnd.shuffle(pool)
    if sum(pool[:len(g)]) / len(g) - sum(pool[len(g):]) / len(h) >= diff:
        hits += 1
p = hits / 20000
win = diff >= 0.4 and p < 0.05
res = f"Haiku à l'aveugle : graphe {sum(g)/len(g):.2f} vs hasard {sum(h)/len(h):.2f} (écart {diff:+.2f}, p={p:.3f}) → {'LE GRAPHE GAGNE' if win else 'le graphe NE bat PAS le hasard'} selon le critère pré-enregistré"
print(res); open("RESULTATS.md", "a").write(f"- {res}\n")
