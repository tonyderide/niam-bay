"""Réplication lait 2000-2014 (PREREG.md) : code de l'étude lait n°2 inchangé, seules les dates changent."""
import json, os, random, sys, threading
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "etude-lait"))
import etude as E  # noqa: E402
ICI = os.path.dirname(os.path.abspath(__file__))
E.CORPUS = os.path.join(ICI, "corpus.json"); os.environ.setdefault("RESULTAT", "../etude-lait-replication/RESULTAT.md"); os.environ.setdefault("N_ETUDE", "3000")
E.REQUETE = E.REQUETE.replace('"2015"[dp]', '"2000"[dp]').replace('"2026"[dp]', '"2014"[dp]')
assert '"2000"[dp] : "2014"[dp]' in E.REQUETE

def classer6():
    A = json.load(open(E.CORPUS)); v = threading.Lock()
    def un(a, cle="classe"):
        c = None
        for _ in range(3):
            try: c = E.claude(E.CONSIGNE.replace("{titre}", a["titre"]).replace("{resume}", a["resume"][:6000])); break
            except Exception: pass
        with v:
            a[cle] = c; json.dump(A, open(E.CORPUS, "w"), ensure_ascii=False, indent=1); print(a["pmid"], cle, c, flush=True)
    with ThreadPoolExecutor(6) as ex: list(ex.map(un, [a for a in A if not a.get("classe")]))
    with ThreadPoolExecutor(6) as ex: list(ex.map(lambda a: un(a, "classe2"), random.Random(22).sample(A, min(15, len(A)))))

if __name__ == "__main__":
    {"collecte": E.collecte, "classer6": classer6, "juger": E.juger}[sys.argv[1]]()

# Filtre « santé / consommation » de l'étude 2 (retrouvé dans la session du 25/10 22h41, information seulement)
import re
SANTE = re.compile(r'intake|consumption|supplement|diet|risk|health|disease|mortality|cancer|bone|fracture|cardio|diabet|obes|weight|growth|blood pressure|cholesterol|cognit|muscle|sarcopen|depress|anxiety|acne|inflamm|metabol', re.I)
HORS = re.compile(r'contamina|aflatoxin|residue|antibiotic resist|mastitis|cattle|cow[s]? (welfare|health)|bovine (health|disease)|processing|pasteuri|high-pressure|shelf|detection|adulterat|prevalence of .* in (raw )?milk|feed|herd|farm', re.I)
ORGANISMES = [m for m in E.LAITIER if m != "dairy"]
