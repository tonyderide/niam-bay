"""PREREG-53 : liste de tous les symboles du comptant (data.binance.vision), bougies 1d mensuelles vérifiées SHA-256, paires USDT, exclusions."""
import hashlib, io, json, os, re, urllib.request, zipfile, concurrent.futures as cf
ICI = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(ICI, "comptant")
get = lambda u: urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "nb-labo"}), timeout=90).read()
EXCL_BASE = {"USDC","BUSD","TUSD","PAX","USDP","FDUSD","DAI","USDS","EUR","GBP","AUD","TRY","BRL","RUB","UAH","NGN","ZAR","BIDR","IDRT","PLN","RON","ARS",
             "JPY","MXN","COP","CZK","AEUR","EURI","XUSD","USD1","BFUSD","RLUSD","PYUSD","USDE","USDSB","SUSD","UST","USTC"}
f = os.path.join(OUT, "symboles.json")
if not os.path.exists(f):
    S, marq = [], ""
    while True:
        x = get("https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?prefix=data/spot/monthly/klines/&delimiter=/" + (f"&marker={marq}" if marq else "")).decode()
        S += re.findall(r"<Prefix>data/spot/monthly/klines/([^/]+)/</Prefix>", x)
        if "<IsTruncated>true" not in x: break
        marq = re.findall(r"<NextMarker>([^<]+)", x)[0]
    json.dump(sorted(set(S)), open(f, "w"))
S = json.load(open(f)); U = []; excl = {"levier": 0, "stable": 0}
for s in S:
    if not s.endswith("USDT"): continue
    b = s[:-4]
    if re.search(r"(UP|DOWN|BULL|BEAR)$", b) and len(b) > 4: excl["levier"] += 1; continue
    if b in EXCL_BASE: excl["stable"] += 1; continue
    U.append(s)
print(len(S), "symboles,", len(U), "paires USDT gardées, exclues :", excl, flush=True)
MOIS = [f"{a}-{m:02d}" for a in range(2017, 2027) for m in range(1, 13) if (2017, 8) <= (a, m) <= (2026, 9)]
def mois(s, m):
    u = f"https://data.binance.vision/data/spot/monthly/klines/{s}/1d/{s}-1d-{m}.zip"
    try: z = get(u)
    except Exception: return "absent", []
    try:
        if get(u + ".CHECKSUM").decode().split()[0] != hashlib.sha256(z).hexdigest(): return "somme_fausse", []
    except Exception: return "somme_fausse", []
    zf = zipfile.ZipFile(io.BytesIO(z)); r = []
    for l in zf.read(zf.namelist()[0]).decode().splitlines():
        if not l[:1].isdigit(): continue
        v = l.split(","); t = int(v[0]); t = t // 1000 if t > 1e14 else t; r.append([t, float(v[1]), float(v[4])])
    return "ok", r
def sym(s):
    r, e = [], {}
    for m in MOIS:
        a, b = mois(s, m); e[a] = e.get(a, 0) + 1; r += b
    return s, sorted({x[0]: x for x in r}.values()), e
K = {}; bil = {}
with cf.ThreadPoolExecutor(48) as ex:
    for s, r, e in ex.map(sym, U):
        K[s] = r
        for a, n in e.items(): bil[a] = bil.get(a, 0) + n
json.dump(K, open(os.path.join(OUT, "klines.json"), "w")); json.dump(dict(gardees=len(U), exclues=excl, archives=bil), open(os.path.join(OUT, "bilan.json"), "w"))
print("archives", bil)
