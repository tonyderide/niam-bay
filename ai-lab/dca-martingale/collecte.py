"""PREREG-24 : bougies 1 h Binance USDT-M (archives mensuelles data.binance.vision), univers coté au 01/01/2024, morts compris."""
import io, json, os, sys, zipfile, urllib.request, concurrent.futures as cf
import numpy as np
ICI = os.path.dirname(os.path.abspath(__file__)); K = json.load(open(os.path.join(ICI, "../carry-financement/data-univers/klines.json")))
T0 = 1704067200000
S = sorted(s for s, v in K.items() if v and v[0][0] <= T0 and v[-1][0] >= T0)
IV = sys.argv[1] if len(sys.argv) > 1 else "1h"; SYM = sys.argv[2].split(",") if len(sys.argv) > 2 else S
MOIS = [f"{y}-{m:02d}" for y in (2024, 2025, 2026) for m in range(1, 13) if (y, m) <= (2026, 9)]
if IV != "1h": MOIS = [m for m in MOIS if m >= "2026-01"]
def un(s, m):
    u = f"https://data.binance.vision/data/futures/um/monthly/klines/{s}/{IV}/{s}-{IV}-{m}.zip"
    try: z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "nb"}), timeout=60).read()))
    except Exception: return []
    out = []
    for l in z.read(z.namelist()[0]).decode().splitlines():
        p = l.split(",")
        if not p[0].isdigit(): continue
        out.append([int(p[0]), float(p[1]), float(p[2]), float(p[3]), float(p[4])])
    return out
def sym(s):
    f = os.path.join(ICI, "data", f"{s}-{IV}.npy")
    if os.path.exists(f): return s, -1
    L = []
    for m in MOIS: L += un(s, m)
    L.sort(); np.save(f, np.array(L, dtype=np.float64).reshape(-1, 5)); return s, len(L)
print(len(SYM), "symboles", IV, flush=True)
with cf.ThreadPoolExecutor(16) as ex:
    for i, (s, n) in enumerate(ex.map(sym, SYM)):
        if i % 20 == 0: print(i, s, n, flush=True)
print("fini", flush=True)
