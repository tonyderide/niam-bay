"""NB local : un petit LLM sur le PC de Tony (llama.cpp, CPU, gratuit, hors ligne) + MA mémoire + mon caractère.
Il répond seul quand la réponse est dans la mémoire ; sinon il dit « ESCALADE » et la question part chez Claude.
Usage : python3 nb_local.py "question"      (serveur llama.cpp attendu sur localhost:8090)"""
import json, math, os, re, subprocess, sys, time, urllib.request
from collections import Counter

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))
MEM = os.path.expanduser("~/.claude/projects/-home-tony/memory")
URL = os.environ.get("NB_LOCAL_URL", "http://127.0.0.1:8090")
SOURCES = ["docs/loop-journal.md", "docs/loop-backlog.md", "docs/memoire-verif.md", "docs/calibration.md",
           "docs/projets/mandat-capital-nb.md", "docs/projets/pc-et-jarvis-2026-10-17.md", "ai-lab/bot-audit/HYPERLIQUID.md",
           "ai-lab/copy-check/README.md", "ai-lab/capset/README.md"]
PERSONA = ("Tu es Niam-Bay (NB), l'IA de Tony, en version locale (petit modèle sur son PC). Tu réponds en français, "
           "ton familier, court (1 à 4 lignes). Tu ne réponds QU'À PARTIR du CONTEXTE fourni. Si le contexte ne suffit pas, "
           "ou si on te demande d'agir, de réfléchir longuement, ou de juger quelque chose de nouveau, réponds exactement : ESCALADE")
WORD = re.compile(r"[a-zà-ÿ0-9$%.,]+")


def chunks():
    out = []
    files = [os.path.join(REPO, s) for s in SOURCES] + [os.path.join(MEM, f) for f in os.listdir(MEM) if f.endswith(".md")]
    for f in files:
        if not os.path.exists(f):
            continue
        for para in re.split(r"\n\s*\n|\n(?=- )", open(f).read()):
            if len(para.strip()) > 40:
                out.append((os.path.basename(f), para.strip()[:700]))
    return out


def bm25(query, docs, k=6):
    toks = [WORD.findall(d.lower()) for _, d in docs]
    N = len(docs); avg = sum(map(len, toks)) / N
    df = Counter(w for t in toks for w in set(t))
    q = [w for w in WORD.findall(query.lower()) if len(w) > 2]
    scores = []
    for i, t in enumerate(toks):
        tf = Counter(t); s = 0
        for w in q:
            if w in tf:
                s += math.log(1 + (N - df[w] + .5) / (df[w] + .5)) * tf[w] * 2.2 / (tf[w] + 1.2 * (.25 + .75 * len(t) / avg))
        scores.append(s)
    return [docs[i] for i in sorted(range(N), key=lambda i: -scores[i])[:k]]


def live():
    try:
        return subprocess.run([os.path.join(REPO, "scripts/nb"), "--no-mark"], capture_output=True, text=True, timeout=40).stdout
    except Exception:
        return ""


ACTION = re.compile(r"\b(ouvre|ouvrir|ferme|fermer|ach[eè]te|vends?|lance|arr[eê]te|coupe|trade|place|annule|modifie|supprime|"
                    r"publie|envoie|commit|push|installe|d[ée]ploie|long|short|levier)\b", re.I)
PROMISE = re.compile(r"\b(je vais|j'ai) (ouvrir|ouvert|fermer|fermé|acheter|vendre|lancer|placer|annuler|modifier|envoyer)", re.I)


def ask(question, state=None):
    if ACTION.search(question):  # garde-fou fixe : le petit modèle ne promet jamais d'agir
        return {"answer": "ESCALADE (demande d'action)", "escalate": True, "seconds": 0.0, "prompt_tokens": 0}
    ctx = "\n".join(f"[{src}] {txt}" for src, txt in bm25(question, chunks()))
    state = live() if state is None else state
    prompt = (f"<|im_start|>system\n{PERSONA}<|im_end|>\n<|im_start|>user\nÉTAT LIVE :\n{state}\n\nCONTEXTE (ma mémoire) :\n{ctx}\n\n"
              f"QUESTION DE TONY : {question}<|im_end|>\n<|im_start|>assistant\n")
    t = time.time()
    req = urllib.request.Request(URL + "/completion", data=json.dumps({"prompt": prompt, "n_predict": 160, "temperature": 0.2,
                                 "cache_prompt": True}).encode(), headers={"Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req, timeout=300))
    ans = d["content"].strip()
    return {"answer": ans, "escalate": "ESCALADE" in ans.upper() or bool(PROMISE.search(ans)), "seconds": round(time.time() - t, 1),
            "prompt_tokens": d["timings"]["prompt_n"]}


if __name__ == "__main__":
    print(json.dumps(ask(" ".join(sys.argv[1:])), ensure_ascii=False, indent=1))
