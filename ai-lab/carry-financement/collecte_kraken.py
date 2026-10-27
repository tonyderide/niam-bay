"""Télécharge financement horaire et bougies 1 h de Kraken Futures (API publique) -> data-kraken/*.json"""
import calendar, json, time, urllib.request, os
SYM = ["PF_XBTUSD","PF_DOTUSD","PF_SOLUSD","PF_LINKUSD","PF_ADAUSD","PF_ETHUSD","PF_XRPUSD","PF_LTCUSD","PF_BNBUSD","PF_DOGEUSD","PF_AVAXUSD"]
get = lambda u: json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "nb"}), timeout=30))
for s in SYM:
    f = get(f"https://futures.kraken.com/derivatives/api/v4/historicalfundingrates?symbol={s}")["rates"]
    fr = [[calendar.timegm(time.strptime(r["timestamp"], "%Y-%m-%dT%H:%M:%SZ")) * 1000, r["relativeFundingRate"]] for r in f]
    t0 = fr[0][0] // 1000 - 8 * 86400; t1 = int(time.time()); k = {}
    t = t0
    while t < t1:
        r = get(f"https://futures.kraken.com/api/charts/v1/trade/{s}/1h?from={t}&to={min(t + 2000*3600, t1)}")
        for c in r.get("candles", []): k[c["time"]] = float(c["close"])
        t += 2000 * 3600; time.sleep(0.3)
    json.dump({"f": fr, "k": sorted(k.items())}, open(f"data-kraken/{s}.json", "w"))
    print(s, len(fr), "financements depuis", time.strftime("%F", time.gmtime(fr[0][0] / 1000)), len(k), "bougies", flush=True)
