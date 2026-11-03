"""Refait à neuf : téléchargement indépendant (nouveau dossier), somme SHA-256 de chaque archive vérifiée contre le .CHECKSUM de Binance.
python telecharger.py 1h            -> 2024-01 .. 2026-09, tout l'univers
python telecharger.py 5m BTCUSDT,ETHUSDT,SOLUSDT  -> 2026-01 .. 2026-09"""
import hashlib, io, json, os, sys, zipfile, urllib.request, concurrent.futures as cf
import numpy as np
IV = sys.argv[1]; SYM = sys.argv[2].split(",") if len(sys.argv) > 2 else json.load(open("univers.json"))
MOIS = [f"{a}-{m:02d}" for a in (2024, 2025, 2026) for m in range(1, 13) if (a, m) <= (2026, 9) and (IV in ("1h", "1m") or a == 2026)]
os.makedirs("donnees", exist_ok=True); bilan = {"absent": 0, "somme_fausse": 0, "ok": 0}
def lire(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "nb-refait"}), timeout=90).read()
def mois(s, m):
    u = f"https://data.binance.vision/data/futures/um/monthly/klines/{s}/{IV}/{s}-{IV}-{m}.zip"
    try: z = lire(u)
    except Exception: return "absent", None
    try:
        if lire(u + ".CHECKSUM").decode().split()[0] != hashlib.sha256(z).hexdigest(): return "somme_fausse", None
    except Exception: return "somme_fausse", None
    lignes = zipfile.ZipFile(io.BytesIO(z)).read(zipfile.ZipFile(io.BytesIO(z)).namelist()[0]).decode().splitlines()
    rows = [[float(v) for v in l.split(",")[:5]] for l in lignes if l[:1].isdigit()]
    a = np.array(rows).reshape(-1, 5)
    a[a[:, 0] > 1e14, 0] //= 1000   # horodatage en microsecondes -> millisecondes
    return "ok", a
def symbole(s):
    f = f"donnees/{s}-{IV}.npy"
    if os.path.exists(f): return s, "déjà"
    morceaux, etats = [], []
    for m in MOIS:
        e, a = mois(s, m); etats.append(e)
        if a is not None: morceaux.append(a)
    a = np.concatenate(morceaux) if morceaux else np.zeros((0, 5))
    a = a[np.argsort(a[:, 0], kind="stable")]; a = a[np.r_[True, np.diff(a[:, 0]) > 0]] if len(a) else a  # doublons retirés
    np.save(f, a); return s, etats
with cf.ThreadPoolExecutor(40) as ex:
    for s, etats in ex.map(symbole, SYM):
        if etats != "déjà":
            for e in etats: bilan[e] += 1
print(IV, len(SYM), "symboles ; archives :", bilan)
