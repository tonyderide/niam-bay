"""
First-HOUR-only ORB at US open (Tony refinement).
US cash open = 14:30 UTC (13:30 during US DST, but we use 14:30 fixed; both tested below).
Opening range = first W minutes. Then trade the breakout but EXIT at open+60min (stay intraday,
inside the first hour only). 5-minute data for precision. Costs included.
"""
import time, requests, pandas as pd, numpy as np
SYMBOL="BTCUSDT"; INTERVAL="5m"; MONTHS=12; COST=0.0006

def fetch(sym,itv,s,e):
    out=[];url="https://api.binance.com/api/v3/klines";cur=s
    while cur<e:
        b=requests.get(url,params={"symbol":sym,"interval":itv,"startTime":cur,"endTime":e,"limit":1000},timeout=20).json()
        if not b:break
        out+=b;cur=b[-1][0]+1
        if len(b)<1000:break
        time.sleep(0.12)
    return out

end=int(time.time()*1000);start=end-MONTHS*30*24*60*60*1000
print(f"Fetching {SYMBOL} {INTERVAL} ~{MONTHS}mo ...")
raw=fetch(SYMBOL,INTERVAL,start,end)
df=pd.DataFrame(raw,columns=["openTime","open","high","low","close","v","ct","qav","t","tb","tbq","ig"])
for c in["open","high","low","close"]:df[c]=df[c].astype(float)
df["ts"]=pd.to_datetime(df["openTime"],unit="ms",utc=True)
df=df[["ts","open","high","low","close"]].set_index("ts").sort_index()
print(f"{len(df)} candles {df.index[0]} -> {df.index[-1]}\n")

def run(open_h,open_m,win_min,strat):
    """strat: 'breakout' or 'follow'. Exit at open+60min (first hour only)."""
    days=pd.unique(df.index.date);tr=[]
    for d in days:
        t0=pd.Timestamp(d,tz="UTC")+pd.Timedelta(hours=open_h,minutes=open_m)
        win=df.loc[t0:t0+pd.Timedelta(minutes=win_min)-pd.Timedelta(seconds=1)]
        if len(win)<win_min//5:continue
        hi=win["high"].max();lo=win["low"].min()
        fo=win["open"].iloc[0];fc=win["close"].iloc[-1]
        path=df.loc[t0+pd.Timedelta(minutes=win_min): t0+pd.Timedelta(minutes=60)]
        if len(path)<1:continue
        exit_px=path["close"].iloc[-1]
        if strat=="follow":
            sig=np.sign(fc-fo)
            if sig==0:continue
            entry=path["open"].iloc[0]
            tr.append(sig*(exit_px-entry)/entry - COST)
        else: # breakout, enter at level
            ret=None
            for _,c in path.iterrows():
                hh=c["high"]>=hi;ll=c["low"]<=lo
                if hh and not ll: ret=(exit_px-hi)/hi;break
                if ll and not hh: ret=(lo-exit_px)/lo;break
                if hh and ll: ret=0.0;break
            if ret is None:continue
            tr.append(ret-COST)
    s=pd.Series(tr)
    if len(s)==0:return None
    return dict(n=len(s),hit=float((s>0).mean()),mean=float(s.mean()),cum=float(s.sum()))

print("FIRST-HOUR-ONLY at US open (exit = open+60min, cost 0.06% incl):")
print(f"{'open':>7}{'win':>5}{'strat':>10}{'N':>6}{'hit%':>8}{'mean%':>9}{'cum%':>9}")
for oh,om,lbl in [(14,30,"14:30"),(13,30,"13:30")]:
    for w in [15,30]:
        for strat in ["breakout","follow"]:
            r=run(oh,om,w,strat)
            if r:print(f"{lbl:>7}{w:>5}{strat:>10}{r['n']:>6}{r['hit']*100:>7.1f}{r['mean']*100:>9.3f}{r['cum']*100:>9.1f}")
    print("-"*54)

# monthly for US 14:30, 30m range, breakout
print("\nMONTHLY — 14:30 open, 30m range, breakout, first hour:")
days=pd.unique(df.index.date);months={}
for d in days:
    t0=pd.Timestamp(d,tz="UTC")+pd.Timedelta(hours=14,minutes=30)
    win=df.loc[t0:t0+pd.Timedelta(minutes=30)-pd.Timedelta(seconds=1)]
    if len(win)<6:continue
    hi=win["high"].max();lo=win["low"].min()
    path=df.loc[t0+pd.Timedelta(minutes=30):t0+pd.Timedelta(minutes=60)]
    if len(path)<1:continue
    exit_px=path["close"].iloc[-1];ret=None
    for _,c in path.iterrows():
        hh=c["high"]>=hi;ll=c["low"]<=lo
        if hh and not ll:ret=(exit_px-hi)/hi;break
        if ll and not hh:ret=(lo-exit_px)/lo;break
        if hh and ll:ret=0.0;break
    if ret is None:continue
    mk=f"{d.year}-{d.month:02d}";months.setdefault(mk,[]).append(ret-COST)
for mk in sorted(months):
    s=pd.Series(months[mk]);print(f"  {mk} N={len(s):>2} hit={(s>0).mean()*100:5.1f}% cum={s.sum()*100:+6.2f}%")
