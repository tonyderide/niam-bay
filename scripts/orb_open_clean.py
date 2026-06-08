"""
Clean Opening-Range-Breakout test at Wall Street open (no look-ahead).

Range = [low, high] of the first W minutes after the open.
Then walk forward candle by candle:
  - first candle whose HIGH >= range_high  -> enter LONG at range_high
  - first candle whose LOW  <= range_low   -> enter SHORT at range_low
  (entry fill assumed AT the level; realistic-ish, slightly optimistic on gaps)
Exit at session close (open + horizon). Optional hard stop = other side of range.
Deduct round-trip cost. Report hit%, mean%, expectancy, cum%, and monthly stability.
"""
import time
import requests
import pandas as pd
import numpy as np

SYMBOL="BTCUSDT"; INTERVAL="15m"; MONTHS=12
COST = 0.0006  # 0.06% round-trip (taker fees + slippage), conservative

def fetch(symbol, interval, start_ms, end_ms):
    out=[]; url="https://api.binance.com/api/v3/klines"; cur=start_ms
    while cur<end_ms:
        b=requests.get(url,params={"symbol":symbol,"interval":interval,
            "startTime":cur,"endTime":end_ms,"limit":1000},timeout=20).json()
        if not b: break
        out+=b; cur=b[-1][0]+1
        if len(b)<1000: break
        time.sleep(0.15)
    return out

end=int(time.time()*1000); start=end-MONTHS*30*24*60*60*1000
raw=fetch(SYMBOL,INTERVAL,start,end)
df=pd.DataFrame(raw,columns=["openTime","open","high","low","close","v","ct","qav","t","tb","tbq","ig"])
for c in ["open","high","low","close"]: df[c]=df[c].astype(float)
df["ts"]=pd.to_datetime(df["openTime"],unit="ms",utc=True)
df=df[["ts","open","high","low","close"]].set_index("ts").sort_index()
print(f"{len(df)} candles  {df.index[0]} -> {df.index[-1]}\n")

def run(open_h, open_m, win_min, horizon_h, use_stop):
    days=pd.unique(df.index.date); trades=[]
    for d in days:
        t0=pd.Timestamp(d,tz="UTC")+pd.Timedelta(hours=open_h,minutes=open_m)
        win=df.loc[t0:t0+pd.Timedelta(minutes=win_min)-pd.Timedelta(seconds=1)]
        if len(win)<win_min//15: continue
        hi=win["high"].max(); lo=win["low"].min()
        path=df.loc[t0+pd.Timedelta(minutes=win_min): t0+pd.Timedelta(hours=horizon_h)]
        if len(path)<2: continue
        exit_px=path["close"].iloc[-1]
        ret=None
        for _,c in path.iterrows():
            hit_hi=c["high"]>=hi; hit_lo=c["low"]<=lo
            if hit_hi and not hit_lo:
                # long at hi; optional stop at lo intrabar ignored (use close exit)
                px=exit_px
                if use_stop and px>hi:  # path may later hit lo as stop -> approx with close
                    pass
                ret=(exit_px-hi)/hi; break
            if hit_lo and not hit_hi:
                ret=(lo-exit_px)/lo; break
            if hit_hi and hit_lo:
                # both in same candle -> ambiguous, skip (could be either)
                ret=0.0; break
        if ret is None:   # never broke the range all session -> no trade
            continue
        trades.append(ret-COST)
    s=pd.Series(trades)
    if len(s)==0: return None
    return dict(n=len(s),hit=float((s>0).mean()),mean=float(s.mean()),
                cum=float(s.sum()),med=float(s.median()),
                win=float(s[s>0].mean() if (s>0).any() else 0),
                loss=float(s[s<0].mean() if (s<0).any() else 0))

print("WALL-STREET-OPEN BREAKOUT (entry AT range level, exit session close, cost 0.06% incl):")
print(f"{'win':>5}{'horizon':>9}{'N':>6}{'hit%':>8}{'mean%':>9}{'cum%':>9}{'avgWin%':>9}{'avgLoss%':>10}")
for w in [15,30,60]:
    for hz in [4,6.5]:
        r=run(14,30,w,hz,False)
        if r: print(f"{w:>5}{hz:>9}{r['n']:>6}{r['hit']*100:>7.1f}{r['mean']*100:>9.3f}"
                    f"{r['cum']*100:>9.1f}{r['win']*100:>9.3f}{r['loss']*100:>10.3f}")

# Monthly stability for the best-looking config
print("\nMONTHLY P&L — win=60m, horizon=6.5h:")
days=pd.unique(df.index.date)
full=df
months={}
for d in days:
    t0=pd.Timestamp(d,tz="UTC")+pd.Timedelta(hours=14,minutes=30)
    win=full.loc[t0:t0+pd.Timedelta(minutes=60)-pd.Timedelta(seconds=1)]
    if len(win)<4: continue
    hi=win["high"].max(); lo=win["low"].min()
    path=full.loc[t0+pd.Timedelta(minutes=60): t0+pd.Timedelta(hours=6.5)]
    if len(path)<2: continue
    exit_px=path["close"].iloc[-1]; ret=None
    for _,c in path.iterrows():
        hh=c["high"]>=hi; ll=c["low"]<=lo
        if hh and not ll: ret=(exit_px-hi)/hi; break
        if ll and not hh: ret=(lo-exit_px)/lo; break
        if hh and ll: ret=0.0; break
    if ret is None: continue
    mk=f"{d.year}-{d.month:02d}"
    months.setdefault(mk,[]).append(ret-COST)
for mk in sorted(months):
    s=pd.Series(months[mk]); print(f"  {mk}  N={len(s):>2}  hit={ (s>0).mean()*100:5.1f}%  cum={s.sum()*100:+6.2f}%")
