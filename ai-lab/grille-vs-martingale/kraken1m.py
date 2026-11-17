"""PREREG-76 : bougies 1 min Kraken Futures (API publique des graphiques, sans clé) pour le contrôle de fidélité.
Usage : python kraken1m.py DOSSIER 2026-11-01 2026-11-17"""
import sys, json, time, urllib.request, datetime as dt
import numpy as np
D, d0, d1 = sys.argv[1], sys.argv[2], sys.argv[3]
s = lambda x: int(dt.datetime.fromisoformat(x).replace(tzinfo=dt.timezone.utc).timestamp())
for c in ("SOL", "LINK", "ADA", "DOT", "DOGE"):
    a, f, fin = {}, s(d0), s(d1)
    while f < fin:
        u = f"https://futures.kraken.com/api/charts/v1/trade/PF_{c}USD/1m?from={f}&to={min(f + 86400, fin)}"
        r = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "python"}), timeout=30))
        for k in r["candles"]:
            a[int(k["time"])] = [float(k["time"]), float(k["open"]), float(k["high"]), float(k["low"]), float(k["close"])]
        f += 86400; time.sleep(0.3)
    x = np.array([a[k] for k in sorted(a)])
    # minutes sans échange : bougie plate au dernier cours (grille de temps complète)
    t = np.arange(x[0, 0], x[-1, 0] + 1, 60000.0); y = np.zeros((len(t), 5)); y[:, 0] = t
    j = np.searchsorted(x[:, 0], t, side="right") - 1; ex = x[j, 0] == t
    y[ex, 1:] = x[j[ex], 1:]; y[~ex, 1:] = x[j[~ex], 4][:, None]
    np.save(f"{D}/{c}.npy", y); print(c, len(x), "bougies,", int((~ex).sum()), "minutes vides comblées", flush=True)
