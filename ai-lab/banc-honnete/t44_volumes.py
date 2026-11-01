"""PREREG-44 : volumes en dollars journaliers (klines 1d mensuelles data.binance.vision, SHA-256 vérifié), 2023-12 .. 2026-09."""
import hashlib, io, json, os, zipfile, urllib.request, concurrent.futures as cf
ICI = os.path.dirname(os.path.abspath(__file__)); U = json.load(open(os.path.join(ICI, "../dca-martingale/refait/univers.json")))
MOIS = ["2023-12"] + [f"{a}-{m:02d}" for a in (2024, 2025, 2026) for m in range(1, 13) if (a, m) <= (2026, 9)]
def lire(u): return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "nb-labo"}), timeout=90).read()
def mois(s, m):
    u = f"https://data.binance.vision/data/futures/um/monthly/klines/{s}/1d/{s}-1d-{m}.zip"
    try: z = lire(u)
    except Exception: return "absent", []
    try:
        if lire(u + ".CHECKSUM").decode().split()[0] != hashlib.sha256(z).hexdigest(): return "somme_fausse", []
    except Exception: return "somme_fausse", []
    zf = zipfile.ZipFile(io.BytesIO(z)); L = zf.read(zf.namelist()[0]).decode().splitlines()
    out = []
    for l in L:
        if not l[:1].isdigit(): continue
        v = l.split(","); t = int(v[0]); t = t // 1000 if t > 1e14 else t; out.append([t, float(v[7])])
    return "ok", out
def sym(s):
    r = []; e = []
    for m in MOIS:
        a, b = mois(s, m); e.append(a); r += b
    return s, sorted(dict(r).items()), e
V = {}; bil = {}
with cf.ThreadPoolExecutor(32) as ex:
    for s, r, e in ex.map(sym, U):
        V[s] = r
        for x in e: bil[x] = bil.get(x, 0) + 1
json.dump(V, open(os.path.join(ICI, "taille/volumes.json"), "w")); print(len(V), "symboles", bil)
