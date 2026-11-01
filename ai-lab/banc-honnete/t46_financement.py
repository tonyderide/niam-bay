"""PREREG-46 : financement public (fapi/v1/fundingRate) de tous les perpétuels USDT de data-univers/klines.json, 2020-12-25 → 2026-10-27.
Limite Binance : 500 requêtes / 5 min sur ce point d'accès -> une requête toutes les 0,65 s. Reprend là où il s'est arrêté."""
import json, os, time, urllib.request, urllib.error
ICI = os.path.dirname(os.path.abspath(__file__)); K = json.load(open(os.path.join(ICI, "../carry-financement/data-univers/klines.json")))
F0 = json.load(open(os.path.join(ICI, "../carry-financement/data-univers/funding.json")))
OUT = os.path.join(ICI, "listings/funding.json"); F = json.load(open(OUT)) if os.path.exists(OUT) else {}
T0, T1 = 1608854400000, 1793059200000
def get(u):
    for e in range(5):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "nb-labo"}), timeout=60))
        except urllib.error.HTTPError as x:
            if x.code == 400: return []
            time.sleep(30 * (e + 1))
        except Exception: time.sleep(10 * (e + 1))
    return None
S = [s for s, v in K.items() if v]
for i, s in enumerate(S):
    if s in F: continue
    if s in F0 and F0[s] and F0[s][-1][0] > T1 - 86400000 * 2: F[s] = F0[s]; continue
    t = max(T0, K[s][0][0] - 86400000); f = []; ok = True
    while t < T1:
        r = get(f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={s}&startTime={t}&endTime={T1}&limit=1000"); time.sleep(0.65)
        if r is None: ok = False; break
        if not r: break
        f += [[x["fundingTime"], float(x["fundingRate"])] for x in r]; t = r[-1]["fundingTime"] + 1
        if len(r) < 1000: break
    if ok: F[s] = f
    if i % 25 == 0: json.dump(F, open(OUT, "w")); print(i, s, len(f), flush=True)
json.dump(F, open(OUT, "w")); print("fini", len(F), "sur", len(S))
