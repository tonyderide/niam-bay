"""Info PREREG-27 : témoin décalé « strict » (les positions décalées sur un contrat absent ce jour-là sont retirées)."""
import os, io, contextlib, builtins, random, importlib.util
os.environ["NT"] = "0"; os.environ["SORTIE"] = "/dev/null"
spec = importlib.util.spec_from_file_location("u", "etude_univers.py"); U = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()): spec.loader.exec_module(U)
bp, bf, fr, _, _ = U.evalue(U.W); net = bp + bf - fr
rnd = random.Random(27); plus = 0; NT = 1000
for _ in range(NT):
    k = rnd.randint(30, U.N - 30); Wk = U.W[k:] + U.W[:k]
    Wk = [{s: v for s, v in w.items() if U.jours[i] in U.C.get(s, {})} for i, w in enumerate(Wk)]
    a, b, c, _, _ = U.evalue(Wk); plus += (a + b - c) >= net
print(f"témoin strict : p = {(plus+1)/(NT+1):.4f} (règle net {100*net:+.1f} %)")
