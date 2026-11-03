"""Illustration (non pré-enregistrée) : le même 10/10/2025 sur SOL, avec des sécurités ajoutées une par une."""
import numpy as np, datetime as dt
exec(open("regle_tony.py").read().split("O = {}")[0].replace('BTCUSDT-1m', 'SOLUSDT-1m'))
ms = lambda *x: int(dt.datetime(*x, tzinfo=dt.timezone.utc).timestamp() * 1000)
x = a[(a[:, 0] >= ms(2025, 10, 10, 12)) & (a[:, 0] < ms(2025, 10, 11, 12))]
out = np.empty((len(x) + 1, 4)); n = chaine(x[:, 1], x[:, 2], x[:, 3], x[:, 4], 0.01, 0.005, 0.01, False, out); T = out[:n]
# agitation : amplitude des 15 dernières minutes avant l'entrée
amp = lambda i: (x[max(0, i - 15):i + 1, 2].max() / x[max(0, i - 15):i + 1, 3].min() - 1) if i > 0 else 0
def jouer(mart=True, plafond=99, pause_agitation=False, stop_jour=None):
    cap, mise, pertes, perte_jour = 1000.0, 10.0, 0, 0.0
    for r, sens, i0, i1 in T:
        if pause_agitation and amp(int(i0)) > 0.03: continue          # marché trop agité : on ne trade pas
        if stop_jour is not None and perte_jour <= -stop_jour: break   # limite de perte du jour atteinte
        g = mise * r / 0.01; cap += g; perte_jour = min(0.0, perte_jour + g) if g < 0 else perte_jour + g
        if g > 0 or not mart: mise, pertes = 10.0, 0
        else:
            pertes += 1; mise = 10.0 if pertes >= plafond else mise * 2
        if mise > cap: return cap, "ruiné"
    return cap, "ok"
for nom, kw in (("ta règle telle quelle", {}), ("+ plafond : 3 doublements max", {"plafond": 3}), ("sans martingale (mise fixe 10 €)", {"mart": False}),
                ("+ pause si le prix a bougé de plus de 3 % en 15 min", {"mart": False, "pause_agitation": True}),
                ("martingale + pause agitation", {"pause_agitation": True}), ("martingale + stop si −50 € dans la journée", {"stop_jour": 50})):
    c, e = jouer(**kw); print(f"{nom:55s} capital final {c:7.1f} €  {e}")
