"""Télécharge les bougies 1 min Kraken Futures (API publique, lecture seule, 1 requête / ~0,3 s) du 01/01/2024 au 17/10/2026,
dans le cache du banc : ~/.cache/banc-honnete/PF_<SYM>USD_1m_2024-01-01.pkl = (timestamps, [(o,h,l,c,v)…])."""
import json, os, pickle, sys, time, urllib.request
CACHE = os.path.expanduser("~/.cache/banc-honnete"); a, b = 1704067200, 1792195200
for m in sys.argv[1:]:
    f = f"{CACHE}/PF_{m}USD_1m_2024-01-01.pkl"
    if os.path.exists(f): print(m, "déjà là"); continue
    out = {}; t = a
    while t < b:
        for _ in range(8):
            try:
                d = json.load(urllib.request.urlopen(f"https://futures.kraken.com/api/charts/v1/trade/PF_{m}USD/1m?from={t}&to={min(b, t + 1800 * 60)}", timeout=60))["candles"]; break
            except Exception: time.sleep(3)
        for c in d: out[c["time"] // 1000] = tuple(float(c[x]) for x in ("open", "high", "low", "close", "volume"))
        t += 1800 * 60; time.sleep(0.25)
    T = sorted(out); pickle.dump((T, [out[x] for x in T]), open(f, "wb")); print(m, len(T), "bougies", flush=True)
