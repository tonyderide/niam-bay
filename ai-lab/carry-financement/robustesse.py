"""Contrôles d'information (ne changent pas le verdict de PREREG-25) : décalage d'un jour, autres fenêtres, sans la meilleure crypto, sans 2021."""
import importlib.util, sys, io, contextlib, time
spec = importlib.util.spec_from_file_location("e", "etude.py"); E = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()):
    import builtins; o = builtins.open
    builtins.open = lambda f, m="r", *a, **k: io.StringIO() if f == "RESULTAT.md" else o(f, m, *a, **k)
    spec.loader.exec_module(E); builtins.open = o
J = E.J
def poids(fen, retard, exclus=()):
    W = []
    for d in E.jours:
        ok = [s for s in E.SYM if s not in exclus and d in E.prix[s] and d + J in E.prix[s]]
        sig = sorted(ok, key=lambda s: E.somme_fin(s, d - (fen + retard) * J, d - retard * J, False))
        w = {s: 0.0 for s in E.SYM}
        if len(ok) >= 6:
            for s in sig[:3]: w[s] = 1/3
            for s in sig[-3:]: w[s] = -1/3
        W.append(w)
    return W
def net(W, garde=lambda d: True):
    bp, bf, fr, par, serie = E.evalue(W)
    return sum(v for d, v in zip(E.jours, serie) if garde(d)), bp, bf, fr
for nom, W in [("règle (7 j)", E.W), ("signal retardé d'1 jour", poids(7, 1)), ("signal retardé de 3 jours", poids(7, 3)),
               ("fenêtre 3 j", poids(3, 0)), ("fenêtre 14 j", poids(14, 0)), ("sans SOL", poids(7, 0, ("SOLUSDT",))),
               ("sans SOL, DOGE, BNB", poids(7, 0, ("SOLUSDT", "DOGEUSDT", "BNBUSDT")))]:
    n, bp, bf, fr = net(W); print(f"{nom:26s} net {100*n:+7.1f} %  (prix {100*bp:+.1f}, fin {100*bf:+.1f}, frais {100*fr:.1f})")
n, *_ = net(E.W, lambda d: time.gmtime(d/1000).tm_year != 2021); print(f"{'sans 2021':26s} net {100*n:+7.1f} %")
n, *_ = net(E.W, lambda d: time.gmtime(d/1000).tm_year >= 2023); print(f"{'depuis 2023':26s} net {100*n:+7.1f} %")
