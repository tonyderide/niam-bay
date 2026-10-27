"""PREREG-27 : liste de tous les perpétuels USDT-M (morts compris), bougies journalières de chacun, puis financement des sélectionnés."""
import json, os, re, time, urllib.request
get = lambda u: urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "nb"}), timeout=60).read()
DOS = "data-univers"
if not os.path.exists(f"{DOS}/symboles.json"):
    S, marq = [], ""
    while True:
        x = get("https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?prefix=data/futures/um/monthly/klines/&delimiter=/" + (f"&marker={marq}" if marq else "")).decode()
        S += re.findall(r"<Prefix>data/futures/um/monthly/klines/([^/]+)/</Prefix>", x)
        if "<IsTruncated>true" not in x: break
        marq = re.findall(r"<NextMarker>([^<]+)", x)[0]
    json.dump(sorted(set(S)), open(f"{DOS}/symboles.json", "w"))
S = [s for s in json.load(open(f"{DOS}/symboles.json")) if s.endswith("USDT") and "_" not in s]
print(len(S), "symboles USDT", flush=True)
T0, T1 = 1598918400000, 1793059200000  # 2020-09-01 → 2026-10-27
K = json.load(open(f"{DOS}/klines.json")) if os.path.exists(f"{DOS}/klines.json") else {}
for i, s in enumerate(S):
    if s in K: continue
    k, t = [], T0
    while t < T1:
        try: r = json.loads(get(f"https://fapi.binance.com/fapi/v1/klines?symbol={s}&interval=1d&startTime={t}&endTime={T1}&limit=1500"))
        except Exception as e: r = []
        if not isinstance(r, list) or not r: break
        k += [[x[0], float(x[1]), float(x[4]), float(x[7])] for x in r]  # ouverture, open, close, volume quote
        t = r[-1][0] + 86400000; time.sleep(0.08)
    K[s] = k
    if i % 50 == 0: json.dump(K, open(f"{DOS}/klines.json", "w")); print(i, s, len(k), flush=True)
json.dump(K, open(f"{DOS}/klines.json", "w")); print("klines ok", sum(1 for v in K.values() if v), "avec données")
