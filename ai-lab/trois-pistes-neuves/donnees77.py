"""PREREG-77 : données publiques (data.binance.vision, contrats perpétuels USDT-M). Aucun compte, aucune clé.
- BTC 1 min (archives mensuelles klines) -> ~/.cache/banc-honnete/m1-binance/BTC.npy (même format que les autres : t, o, h, l, c)
- « metrics » quotidiens à 5 min (positions ouvertes, ratios long/short) -> ~/.cache/banc-honnete/metrics-77/<PIECE>.npy
  grille de 5 min depuis le 01/11/2023 00:00 UTC ; colonnes : oi, oi_valeur, top_comptes, top_positions, ls_comptes, taker ; NaN si absent.
Sommes SHA-256 vérifiées. Usage : python -I donnees77.py"""
import os, io, sys, zipfile, hashlib, urllib.request, urllib.error, datetime as dt, time, concurrent.futures as cf
import numpy as np

CACHE = os.path.expanduser("~/.cache/banc-honnete"); Z = f"{CACHE}/zips-77"
BASE = "https://data.binance.vision/data/futures/um"
PIECES = ["SOL", "LINK", "ADA", "DOT", "ATOM", "AVAX", "BCH", "BNB", "XRP", "LTC", "DOGE", "BTC"]
J0 = dt.date(2023, 11, 1); J1 = dt.date(2026, 9, 30)           # metrics
T0M = int(dt.datetime(2023, 11, 1, tzinfo=dt.timezone.utc).timestamp())
T0P = int(dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc).timestamp()) * 1000
NMIN = 1004 * 1440


def get(u):
    for k in range(5):
        try:
            return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "python-urllib"}), timeout=60).read()
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            time.sleep(2 + 3 * k)
        except Exception:
            time.sleep(2 + 3 * k)
    raise RuntimeError("échec " + u)


def archive(rel):
    """télécharge (ou relit) une archive et vérifie sa somme ; None si elle n'existe pas chez Binance"""
    p = f"{Z}/{rel.replace('/', '_')}"
    if os.path.exists(p): return open(p, "rb").read()
    if os.path.exists(p + ".absent"): return None
    b = get(f"{BASE}/{rel}")
    if b is None:
        open(p + ".absent", "w").close(); return None
    s = get(f"{BASE}/{rel}.CHECKSUM")
    if s is None or hashlib.sha256(b).hexdigest() != s.decode().split()[0]:
        raise RuntimeError("somme fausse " + rel)
    open(p + ".tmp", "wb").write(b); os.replace(p + ".tmp", p); return b


def csv(b):
    z = zipfile.ZipFile(io.BytesIO(b)); return z.read(z.namelist()[0]).decode().splitlines()


def klines(sym, mois):
    a = np.full((NMIN, 5), np.nan); a[:, 0] = T0P + 60000 * np.arange(NMIN)
    for m in mois:
        b = archive(f"monthly/klines/{sym}/1m/{sym}-1m-{m}.zip")
        if b is None: raise RuntimeError("mois absent " + m)
        for l in csv(b):
            if not l[:1].isdigit(): continue
            x = l.split(","); t = int(x[0]); t = t // 1000 if t > 10 ** 14 else t
            i = (t - T0P) // 60000
            if 0 <= i < NMIN: a[i, 1:] = [float(x[1]), float(x[2]), float(x[3]), float(x[4])]
    return a


def metrics(sym):
    nj = (J1 - J0).days + 1; a = np.full((nj * 288, 6), np.nan); absents = 0
    jours = [J0 + dt.timedelta(days=k) for k in range(nj)]
    with cf.ThreadPoolExecutor(12) as ex:
        res = list(ex.map(lambda d: archive(f"daily/metrics/{sym}USDT/{sym}USDT-metrics-{d}.zip"), jours))
    for b in res:
        if b is None: absents += 1; continue
        for l in csv(b):
            if not l[:1].isdigit(): continue
            x = l.split(",")
            t = int(dt.datetime.strptime(x[0][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=dt.timezone.utc).timestamp())
            k = (t - T0M) // 300
            if 0 <= k < len(a):
                a[k] = [float(v.strip('"')) if v.strip('"') not in ("", "null") else np.nan for v in (x[2], x[3], x[4], x[5], x[6], x[7])]
    return a, absents


if __name__ == "__main__":
    os.makedirs(Z, exist_ok=True); os.makedirs(f"{CACHE}/metrics-77", exist_ok=True)
    mois = [f"{y}-{m:02d}" for y in (2024, 2025, 2026) for m in range(1, 13) if (y, m) <= (2026, 9)]
    a = klines("BTCUSDT", mois); trous = int(np.isnan(a[:, 4]).sum())
    for i in np.nonzero(np.isnan(a[:, 4]))[0]: a[i, 1:] = a[i - 1, 4]
    np.save(f"{CACHE}/m1-binance/BTC.npy", a); print("BTC 1 min :", a.shape, "minutes manquantes bouchées :", trous, flush=True)
    # les fichiers déjà là viennent-ils bien de la même source ? (SOL, mars 2024)
    s = klines("SOLUSDT", ["2024-03"]); ref = np.load(f"{CACHE}/m1-binance/SOL.npy"); ok = ~np.isnan(s[:, 4])
    print("contrôle de source SOL 2024-03 : minutes", int(ok.sum()), "écart max", float(np.abs(s[ok, 1:] - ref[ok, 1:]).max()), flush=True)
    for p in PIECES:
        m, ab = metrics(p); np.save(f"{CACHE}/metrics-77/{p}.npy", m)
        print(p, "metrics :", m.shape, "jours absents", ab, "| oi présent %.2f %% | ls_comptes présent %.2f %%" % (100 * np.mean(~np.isnan(m[:, 0])), 100 * np.mean(~np.isnan(m[:, 4]))), flush=True)
