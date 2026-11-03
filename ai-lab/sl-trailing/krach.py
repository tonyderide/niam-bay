"""Illustration : la règle de Tony (SL 1 %, trailing 0,5 % dès +1 %, inversion après perte, mise doublée après perte) sur SOL pendant le krach du 10/10/2025."""
import numpy as np, datetime as dt
exec(open("regle_tony.py").read().split("O = {}")[0].replace('BTCUSDT-1m', 'SOLUSDT-1m'))
ms = lambda *x: int(dt.datetime(*x, tzinfo=dt.timezone.utc).timestamp() * 1000)
x = a[(a[:, 0] >= ms(2025, 10, 10, 12)) & (a[:, 0] < ms(2025, 10, 11, 12))]
out = np.empty((len(x) + 1, 4)); n = chaine(x[:, 1], x[:, 2], x[:, 3], x[:, 4], 0.01, 0.005, 0.01, False, out)
cap, mise = 1000.0, 10.0
print("prix SOL : début", x[0, 1], " plus bas", x[:, 3].min(), " plus haut", x[:, 2].max())
for r, sens, i0, i1 in out[:n]:
    g = mise * r / 0.01; cap += g
    t0 = np.datetime64(int(x[int(i0), 0]), "ms").astype("datetime64[m]"); t1 = np.datetime64(int(x[int(i1), 0]), "ms").astype("datetime64[m]")
    print(f"{str(t0)[11:]}→{str(t1)[11:]}  {'LONG ' if sens > 0 else 'SHORT'} entrée {x[int(i0), 1]:7.2f} sortie {x[int(i0), 1] * (1 + sens * (r + 0.001)):7.2f}  {r * 100:+6.2f} %  mise {mise:6.0f} €  -> {g:+7.1f} €  capital {cap:7.1f} €")
    mise = 10.0 if g > 0 else mise * 2
    if mise > cap: print("RUINE : la mise suivante dépasse le capital"); break
