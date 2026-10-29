"""Refait à neuf (29/10 après-midi) : univers reconstruit SANS la liste du carry, directement depuis l'index de data.binance.vision.
Coté au 01/01/2024 = une archive 1 h existe pour 2023-12 ET pour 2024-01 (contrat USDT, perpétuel : pas de suffixe _AAMMJJ)."""
import json, re, urllib.request, concurrent.futures as cf
B = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
def lister(prefix):
    out, marque = [], ""
    while True:
        x = urllib.request.urlopen(f"{B}?delimiter=/&prefix={prefix}&marker={marque}", timeout=60).read().decode()
        out += re.findall(r"<Prefix>([^<]+)</Prefix>", x)[1:] if not marque else re.findall(r"<Prefix>([^<]+)</Prefix>", x)[1:]
        if "<IsTruncated>true" not in x: return out
        marque = re.findall(r"<NextMarker>([^<]+)</NextMarker>", x)[0]
syms = sorted({p.rstrip("/").split("/")[-1] for p in lister("data/futures/um/monthly/klines/")})
syms = [s for s in syms if s.endswith("USDT") and "_" not in s]
def existe(s, m):
    try: return urllib.request.urlopen(urllib.request.Request(f"https://data.binance.vision/data/futures/um/monthly/klines/{s}/1h/{s}-1h-{m}.zip", method="HEAD"), timeout=30).status == 200
    except Exception: return False
with cf.ThreadPoolExecutor(16) as ex: ok = list(ex.map(lambda s: existe(s, "2023-12") and existe(s, "2024-01"), syms))
U = [s for s, o in zip(syms, ok) if o]
print(len(syms), "symboles USDT perpétuels dans l'index ;", len(U), "cotés au 01/01/2024")
json.dump(U, open("univers.json", "w"))
