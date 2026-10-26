"""Télécharge bougies 1 h et financement Binance USDT-M (API publique) -> data/*.json"""
import json, os, time, urllib.request
SYM = ["BTCUSDT","DOTUSDT","SOLUSDT","LINKUSDT","ADAUSDT","ETHUSDT","XRPUSDT","LTCUSDT","BNBUSDT","DOGEUSDT","AVAXUSDT"]
T0 = 1601510400000 - 200*3600*1000   # 2020-10-01 moins 200 h pour l'EMA
T1 = 1793055600000                  # 2026-10-25 23:00 UTC
get = lambda u: json.load(urllib.request.urlopen(u, timeout=30))
os.makedirs("data", exist_ok=True)
for s in SYM:
    if os.path.exists(f"data/{s}.json"): continue
    k, t = [], T0
    while t <= T1:
        r = get(f"https://fapi.binance.com/fapi/v1/klines?symbol={s}&interval=1h&startTime={t}&endTime={T1}&limit=1500")
        if not r: break
        k += [[x[0], float(x[4])] for x in r]; t = r[-1][0] + 3600000; time.sleep(0.15)
    f, t = [], T0
    while t <= T1:
        r = get(f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={s}&startTime={t}&endTime={T1}&limit=1000")
        if not r: break
        f += [[x["fundingTime"], float(x["fundingRate"])] for x in r]; t = r[-1]["fundingTime"] + 1; time.sleep(0.15)
    json.dump({"k": k, "f": f}, open(f"data/{s}.json", "w"))
    print(s, len(k), "bougies", len(f), "financements", time.strftime("%H:%M:%S"), flush=True)
