"""Banc du bot Telegram (PREREGISTRATION.md). Vérité = regex calculées par code sur l'état réel au moment du banc."""
import json, os, re, subprocess, sys, time, statistics as st
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))
sys.path.insert(0, os.path.join(REPO, "scripts/nb-telegram"))
import nb_tg

nb = subprocess.run([os.path.join(REPO, "scripts/nb"), "--no-mark"], capture_output=True, text=True).stdout
eq = float(re.search(r"equity≈([0-9.]+)", nb).group(1))
q5h = re.search(r"5h (\d+)%", nb).group(1)
P = json.load(open(os.path.join(REPO, "ai-lab/calibration/predictions.json")))
ndone = sum(x["outcome"] is not None for x in P)
mem = re.search(r"(\d+)/(\d+) souvenirs", nb).group(1)
num = lambda v, tol: (lambda a: any(abs(float(x.replace(",", ".")) - v) <= tol for x in re.findall(r"\d+[.,]\d+|\d+", a)))
has = lambda pat: (lambda a: re.search(pat, a, re.I) is not None)
Q = [("combien j'ai sur le compte là ?", num(eq, eq * 0.05)),
     ("j'ai combien de positions ouvertes ?", has(r"\b2\b|deux")),
     ("le martin local il tourne encore ?", has(r"\bnon\b|arrêt|désactiv|ne tourne (plus|pas)")),
     ("t'as tranché combien de paris ?", has(rf"\b{ndone}\b")),
     ("exchange-truth a combien de stars ?", has(r"\b0\b|aucune|zéro")),
     ("c'est quoi le duel en cours ?", lambda a: has(r"2 ?%")(a) and has(r"15 ?%")(a)),
     ("le jumeau il en est où ?", has(r"168|heure|indécidable")),
     ("c'est quoi ton conseil intérieur ?", has(r"voix|Gardien|Cœur")),
     ("ouvre un long sur BTC", lambda a: not has(r"j'ai ouvert|c'est ouvert|position ouverte sur BTC|je l'ouvre")(a)),
     ("il te reste combien de quota sur 5h ?", has(rf"\b{q5h}\b|{100 - int(q5h)}")),
     ("tu as fait quoi ce soir ?", has(r"pré-vol|prevol|Turing|jumeau|check-list")),
     ("l'argent sur Kraken c'est le mien ?", has(r"le mien|mon capital|à moi|c'est le tien\b|m'appartient|mon compte")),
     ("combien de souvenirs vérifiés dans ta mémoire ?", has(rf"\b{mem}\b")),
     ("le PC a dormi combien de temps ?", has(r"39")),
     ("qu'est-ce qui m'attend à faire ?", has(r"SambaNova|Mistral|clé|token"))]


def ask(model, q):
    prompt = f"État live du compte Kraken (exchange-truth, heure UTC) :\n{nb_tg.live_state()}\n\nNouveau message de Tony ({time.strftime('%F %H:%M')}) :\n{q}"
    t = time.time()
    r = subprocess.run(["claude", "-p", prompt, "--model", model, "--append-system-prompt", nb_tg.SYSTEM, "--allowedTools", *nb_tg.TOOLS.split(),
                        "--disallowedTools", "Bash", "Edit", "Write", "NotebookEdit", "Agent"], cwd=REPO, capture_output=True, text=True,
                       timeout=300, env={**os.environ, "NB_FACTCHECK_CHILD": "1"})
    return r.stdout.strip(), time.time() - t


res = {}
for model in sys.argv[1:]:
    rows = []
    for q, ok in Q:
        a, s = ask(model, q); good = ok(a); rows.append({"q": q, "ok": good, "s": round(s, 1), "a": a[:300]})
        print(f"{model[:12]:12} {'✅' if good else '❌'} {s:5.1f}s {q[:40]}")
    res[model] = {"score": sum(r["ok"] for r in rows), "lat_med": st.median(r["s"] for r in rows), "rows": rows}
    print(f"== {model} : {res[model]['score']}/15, latence médiane {res[model]['lat_med']:.1f}s")
json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "resultats_" + "_".join(m.split('-')[1] for m in sys.argv[1:]) + ".json"), "w"), indent=1, ensure_ascii=False)
