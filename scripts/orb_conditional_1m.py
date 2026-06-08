"""
Tony's exact claim, tested at 1-minute (near-tick) resolution:
  Take HIGH and LOW of the first candle at US open. Watch which level breaks FIRST.
  high breaks first -> "UP day"; low breaks first -> "DOWN day".
  CLAIM: knowing which broke first tells you the day's trend.

We measure the CONDITIONAL probability the day actually follows:
  P(session closes above breakout | high broke first)   [continuation]
  P(session closes below breakout | low broke first)
  + directional accuracy vs day-open.
1m data makes "which broke first" precise. Session close = open+6.5h (21:00 UTC).
"""
import time, requests, pandas as pd, numpy as np
SYMBOL="BTCUSDT"; INTERVAL="1m"; MONTHS=12

def fetch(sym,itv,s,e):
    out=[];url="https://api.binance.com/api/v3/klines";cur=s
    while cur<e:
        b=requests.get(url,params={"symbol":sym,"interval":itv,"startTime":cur,"endTime":e,"limit":1000},timeout=20).json()
        if not b:break
        out+=b;cur=b[-1][0]+1
        if len(b)<1000:break
        time.sleep(0.06)
    return out

end=int(time.time()*1000);start=end-MONTHS*30*24*60*60*1000
print(f"Fetching {SYMBOL} 1m ~{MONTHS}mo (large) ...")
raw=fetch(SYMBOL,INTERVAL,start,end)
df=pd.DataFrame(raw,columns=["openTime","open","high","low","close","v","ct","qav","t","tb","tbq","ig"])
for c in["open","high","low","close"]:df[c]=df[c].astype(float)
df["ts"]=pd.to_datetime(df["openTime"],unit="ms",utc=True)
df=df[["ts","open","high","low","close"]].set_index("ts").sort_index()
print(f"{len(df)} 1m candles {df.index[0]} -> {df.index[-1]}\n")

def conditional(open_h,open_m,win_min,horizon_h=6.5):
    days=pd.unique(df.index.date)
    up_first=0; up_cont=0; up_diropen=0
    dn_first=0; dn_cont=0; dn_diropen=0
    no_break=0; same_min=0; tot=0
    for d in days:
        t0=pd.Timestamp(d,tz="UTC")+pd.Timedelta(hours=open_h,minutes=open_m)
        win=df.loc[t0:t0+pd.Timedelta(minutes=win_min)-pd.Timedelta(seconds=1)]
        if len(win)<win_min*0.6:continue
        hi=win["high"].max();lo=win["low"].min();dopen=win["open"].iloc[0]
        path=df.loc[t0+pd.Timedelta(minutes=win_min):t0+pd.Timedelta(hours=horizon_h)]
        if len(path)<2:continue
        tot+=1; close=path["close"].iloc[-1]
        broke=None
        for _,c in path.iterrows():
            hh=c["high"]>=hi; ll=c["low"]<=lo
            if hh and ll: broke="same"; break      # same 1m bar -> ambiguous even near-tick
            if hh: broke="up"; break
            if ll: broke="down"; break
        if broke is None: no_break+=1; continue
        if broke=="same": same_min+=1; continue
        if broke=="up":
            up_first+=1
            if close>hi: up_cont+=1
            if close>dopen: up_diropen+=1
        else:
            dn_first+=1
            if close<lo: dn_cont+=1
            if close<dopen: dn_diropen+=1
    return dict(tot=tot,no_break=no_break,same=same_min,
        up_first=up_first,up_cont=up_cont,up_diropen=up_diropen,
        dn_first=dn_first,dn_cont=dn_cont,dn_diropen=dn_diropen)

def pct(a,b): return f"{(100*a/b):.1f}%" if b else "n/a"

for win in [1,5,15,30]:
    r=conditional(14,30,win)
    print(f"=== US open 14:30 UTC, first candle = {win}m, near-tick(1m) break detection ===")
    print(f"  days tested: {r['tot']} | never broke range: {r['no_break']} | ambiguous same-minute: {r['same']}")
    print(f"  HIGH broke first: {r['up_first']} days")
    print(f"     -> closed ABOVE breakout (continuation): {pct(r['up_cont'],r['up_first'])}")
    print(f"     -> closed above day-open (direction):    {pct(r['up_diropen'],r['up_first'])}")
    print(f"  LOW broke first: {r['dn_first']} days")
    print(f"     -> closed BELOW breakout (continuation): {pct(r['dn_cont'],r['dn_first'])}")
    print(f"     -> closed below day-open (direction):    {pct(r['dn_diropen'],r['dn_first'])}")
    cont=r['up_cont']+r['dn_cont']; ndir=r['up_first']+r['dn_first']
    diro=r['up_diropen']+r['dn_diropen']
    print(f"  COMBINED continuation accuracy: {pct(cont,ndir)}  (need >>50% for an edge)")
    print(f"  COMBINED directional accuracy:  {pct(diro,ndir)}")
    print()
