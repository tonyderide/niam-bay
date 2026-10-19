import json,urllib.request,time,calendar,sys
t0=calendar.timegm((2026,1,1,0,0,0)); t1=calendar.timegm((2026,10,17,0,0,0))
for sym in ["PF_XBTUSD","PF_ETHUSD","PF_SOLUSD"]:
    out={};t=t0
    while t<t1:
        e=min(t+2000*60-1,t1)
        u=f"https://futures.kraken.com/api/charts/v1/trade/{sym}/1m?from={t}&to={e}"
        for k in range(4):
            try:
                d=json.load(urllib.request.urlopen(u,timeout=30));break
            except Exception as ex: time.sleep(2)
        for c in d.get("candles",[]): out[c["time"]//1000]=[float(c[x]) for x in("open","high","low","close","volume")]
        t=e+1
    json.dump(out,open(f"{sym}.json","w"));print(sym,len(out),file=sys.stderr)
