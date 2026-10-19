"""Second avis v0 (protocole 3edda19) : extrait les affirmations d'un texte et vérifie ce qui se vérifie mécaniquement.
- calc : Haiku traduit l'affirmation en UNE expression booléenne arithmétique ; elle est évaluée par un évaluateur AST FERMÉ (aucun code exécuté).
- code : Haiku extrait (dépôt, chemin, symbole optionnel) ; vérifié par l'API GitHub publique, en lecture seule.
- autre : « invérifiable » en v0. Jamais ✓ ni ✗ inventés.
Usage : python3 verif.py "texte"   |   from verif import check_claims"""
import ast, base64, json, operator as op, os, re, subprocess, sys, urllib.request

OPS = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv, ast.Pow: op.pow, ast.Mod: op.mod, ast.FloorDiv: op.floordiv,
       ast.USub: op.neg, ast.UAdd: op.pos, ast.Eq: lambda a, b: abs(a - b) <= 1e-9 * max(1, abs(a), abs(b)), ast.NotEq: lambda a, b: abs(a - b) > 1e-9 * max(1, abs(a), abs(b)), ast.Lt: op.lt, ast.LtE: op.le, ast.Gt: op.gt, ast.GtE: op.ge}
FUN = {"abs": abs, "round": round, "min": min, "max": max, "sqrt": lambda x: x ** 0.5}


def safe_eval(expr):
    def ev(n):
        if isinstance(n, ast.Expression): return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)): return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in OPS:
            if isinstance(n.op, ast.Pow) and abs(ev(n.right)) > 10000: raise ValueError("exposant trop grand")
            return OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in OPS: return OPS[type(n.op)](ev(n.operand))
        if isinstance(n, ast.Compare) and len(n.ops) == 1 and type(n.ops[0]) in OPS: return OPS[type(n.ops[0])](ev(n.left), ev(n.comparators[0]))
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in FUN and not n.keywords:
            return FUN[n.func.id](*[ev(a) for a in n.args])
        if isinstance(n, ast.BoolOp):
            vals = [ev(v) for v in n.values]; return all(vals) if isinstance(n.op, ast.And) else any(vals)
        raise ValueError(f"élément interdit : {type(n).__name__}")
    return ev(ast.parse(expr, mode="eval"))


def gh_file(repo, path):
    try:
        d = json.load(urllib.request.urlopen(f"https://api.github.com/repos/{repo}/contents/{path}", timeout=20))
        return base64.b64decode(d["content"]).decode("utf-8", "replace") if d.get("encoding") == "base64" else ""
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def extract(text):
    prompt = ("Extrais chaque affirmation vérifiable de ce texte. Réponds UNIQUEMENT par une liste JSON d'objets :\n"
              '{"claim": "...", "kind": "calc" | "code" | "other", "expr": "<si calc : UNE expression Python booléenne, uniquement nombres, + - * / ** % // comparaisons, abs round min max sqrt, qui vaut True ssi l\'affirmation est vraie>", '
              '"repo": "<si code : propriétaire/dépôt>", "path": "<si code : chemin du fichier>", "symbol": "<si code : texte qui doit apparaître dans le fichier, ou vide pour la simple existence>"}\n'
              "« calc » = une affirmation purement arithmétique. « code » = l'existence d'un fichier ou d'un symbole dans un dépôt GitHub nommé. Tout le reste = « other ».\n\nTEXTE :\n" + text)
    r = subprocess.run(["claude", "-p", prompt, "--model", "claude-haiku-5-5", "--tools", ""], capture_output=True, text=True,
                       timeout=120, env={**os.environ, "NB_FACTCHECK_CHILD": "1"})
    m = re.search(r"\[.*\]", r.stdout, re.S)
    return json.loads(m.group(0)) if m else []


def check(c):
    k = c.get("kind")
    try:
        if k == "calc" and c.get("expr"):
            v = safe_eval(c["expr"])
            return ("✓" if v is True else "✗" if v is False else "?"), f"calcul : {c['expr']} → {v}"
        if k == "code" and c.get("repo") and c.get("path"):
            content = gh_file(c["repo"], c["path"])
            if content is None:
                return "✗", f"{c['repo']}/{c['path']} n'existe pas (GitHub 404)"
            sym = (c.get("symbol") or "").strip()
            if not sym:
                return "✓", f"{c['repo']}/{c['path']} existe"
            pats = [sym] + ([f"def {sym}", f"class {sym}"] if re.fullmatch(r"\w+", sym) else [])
            hit = any(p in content for p in pats)
            return ("✓" if hit else "✗"), f"« {sym} » {'trouvé' if hit else 'absent'} dans {c['path']}"
    except Exception as e:
        return "?", f"invérifiable ({type(e).__name__}: {str(e)[:80]})"
    if k == "other":  # v1 (banc web f050c08 : 0 faux ✓, 0 faux ✗, 6/10 vrais confirmés)
        try:
            from web import check_web
            return check_web(c.get("claim", ""))
        except Exception as e:
            return "?", f"invérifiable ({type(e).__name__})"
    return "?", "invérifiable"


def check_claims(text):
    return [(c.get("claim", ""),) + check(c) for c in extract(text)]


if __name__ == "__main__":
    for claim, mark, why in check_claims(" ".join(sys.argv[1:])):
        print(f"{mark} {claim}\n   {why}")
