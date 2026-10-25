"""Liste les `except` qui avalent une erreur sans rien journaliser (pass / continue / sleep seuls)."""
import ast, sys, pathlib
for racine in sys.argv[1:]:
    for f in sorted(pathlib.Path(racine).rglob("*.py")):
        if any(p in f.parts for p in ("__pycache__", ".venv", "node_modules")): continue
        try: t = ast.parse(f.read_text(errors="replace"))
        except Exception as e: print(f"{f}: illisible ({e.__class__.__name__})"); continue
        for n in ast.walk(t):
            if isinstance(n, ast.ExceptHandler) and (n.type is None or getattr(n.type, "id", "") in ("Exception", "BaseException")):
                def muet(b):
                    if isinstance(b, (ast.Pass, ast.Continue)): return True
                    return isinstance(b, ast.Expr) and isinstance(b.value, ast.Call) and getattr(b.value.func, "attr", "") == "sleep"
                if all(muet(b) for b in n.body): print(f"{f}:{n.lineno}")
