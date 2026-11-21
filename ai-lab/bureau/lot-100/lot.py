"""Juge les 100 idées de idees.json avec le cœur du bureau (bureau.evaluer, règle inchangée). Reprenable.
python3 lot.py verifier | juger"""
import json, os, sys, multiprocessing as mp
ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(ICI))
import bureau
OUT = os.path.join(ICI, "resultats.jsonl")

def un(spec):
    data, per = bureau.donnees(spec)
    v, raisons, det = bureau.evaluer(spec, data, per)
    for d in det: d.pop("par_marche", None)
    return {"id": spec["id"], "nom": spec["nom"], "verdict": v, "raisons": raisons, "det": det}

if __name__ == "__main__":
    idees = json.load(open(os.path.join(ICI, "idees.json")))
    if sys.argv[1] == "verifier":
        for s in idees: print(s["id"], bureau.verifier(s)[:80].replace("\n", " "))
        sys.exit()
    fait = {json.loads(l)["id"] for l in open(OUT)} if os.path.exists(OUT) else set()
    todo = [s for s in idees if s["id"] not in fait]
    for s in todo: bureau.donnees(s)  # téléchargements d'abord, un par un
    with mp.Pool(2) as p, open(OUT, "a") as f:
        for r in p.imap_unordered(un, todo):
            f.write(json.dumps(r, ensure_ascii=False) + "\n"); f.flush()
            print(r["id"], r["verdict"], [round(d["somme"] * 100, 1) for d in r["det"]], [round(d["rang"]) for d in r["det"]], flush=True)
