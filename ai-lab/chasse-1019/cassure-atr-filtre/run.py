import json,urllib.request,random,statistics,itertools,os,calendar,datetime
D=os.path.dirname(os.path.abspath(__file__))
def ts(s): return calendar.timegm(datetime.date.fromisoformat(s).timetuple())
def fetch(sym,res,a,b):
    out=[];cur=a;step=5000*(900 if res=='15m' else 86400)
    while cur<b:
        e=min(cur+step,b)
        u=f"https://futures.kraken.com/api/charts/v1/trade/{sym}/{res}?from={cur}&to={e}"
        d=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'x'}),timeout=60))
        out+=d['candles'];cur=e+1
    m={}
    for c in out: m[c['time']//1000]=(float(c['open']),float(c['high']),float(c['low']),float(c['close']))
    return [(t,)+m[t] for t in sorted(m)]
A=ts('2025-08-01');B=ts('2026-10-17');S0=ts('2026-01-01');S1=ts('2026-07-01');J1=B
data={}
for s in ['PF_XBTUSD','PF_ETHUSD','PF_SOLUSD']:
    fn=f'{D}/{s}.json'
    if os.path.exists(fn): data[s]=json.load(open(fn))
    else:
        data[s]={'15m':fetch(s,'15m',A,B),'1d':fetch(s,'1d',A,B)};json.dump(data[s],open(fn,'w'))
def ema(x,n):
    a=2/(n+1);o=[];v=x[0]
    for y in x: v=a*y+(1-a)*v;o.append(v)
    return o
def prep(s):
    c15=data[s]['15m'];d=data[s]['1d']
    dc=[x[4] for x in d];de=ema(dc,50)
    trend={}  # day start ts -> +1/-1 using previous completed day
    for i in range(51,len(d)):
        p=i-1;trend[d[i][0]]=1 if dc[p]>de[p] else -1
    n=len(c15);cl=[x[4] for x in c15]
    tr=[c15[0][2]-c15[0][3]]+[max(c15[i][2]-c15[i][3],abs(c15[i][2]-cl[i-1]),abs(c15[i][3]-cl[i-1])) for i in range(1,n)]
    atr=[None]*n;sm=0
    for i in range(n):
        sm+=tr[i]
        if i>=20:sm-=tr[i-20]
        if i>=19:atr[i]=sm/20
    em=ema(cl,20)
    tre=[trend.get(x[0]-x[0]%86400) for x in c15]
    return c15,atr,em,tre
P={s:prep(s) for s in data}
FEE=0.001
def exit_trade(c15,i,dr,a0,k,H):
    # entry at open of bar i
    n=len(c15);e=c15[i][1];ext=e;j=i
    stop=e-dr*k*a0
    while True:
        o,h,l,c=c15[j][1:]
        if dr==1:
            if l<=stop: x=min(o,stop) if j>i else stop;return j,dr*(x-e)/e-FEE
        else:
            if h>=stop: x=max(o,stop) if j>i else stop;return j,dr*(x-e)/e-FEE
        if j-i+1>=H or j==n-1: return j,dr*(c-e)/e-FEE
        ext=max(ext,c) if dr==1 else min(ext,c)
        stop=ext-dr*k*a0 if dr==1 else ext+k*a0 if False else (ext-k*a0 if dr==1 else ext+k*a0)
        j+=1
def run(s,m,k,H,t0,t1):
    c15,atr,em,tre=P[s];n=len(c15);tr=[];i=1
    while i<n-1:
        t=c15[i][0]
        if t>=t1:break
        if t>=t0 and atr[i] and tre[i]:
            up=em[i]+m*atr[i];lo=em[i]-m*atr[i];cl=c15[i][4];dr=0
            if cl>up and tre[i]==1:dr=1
            elif cl<lo and tre[i]==-1:dr=-1
            if dr:
                j,r=exit_trade(c15,i+1,dr,atr[i],k,H);tr.append(r);i=j+1;continue
        i+=1
    return tr
grid=list(itertools.product([1.5,2,2.5],[2,3],[16,48,96]))
res=[]
for g in grid:
    per=[run(s,*g,S0,S1) for s in data]
    res.append((sum(map(sum,per)),sum(map(len,per)),g))
res.sort(reverse=True)
for r in res: print('SEL',r)
best=[r for r in res if r[1]>=30][0][2];print('BEST',best)
m,k,H=best
jt={s:run(s,m,k,H,S1,J1) for s in data}
for s in jt:print('JUG',s,len(jt[s]),round(sum(jt[s]),4),round(statistics.mean(jt[s]),5) if jt[s] else 0)
tot=sum(map(sum,jt.values()));N=sum(map(len,jt.values()));pos=sum(1 for s in jt if sum(jt[s])>0)
print('JUG total',N,round(tot,4),'coins>0',pos)
random.seed(1019);sims=[]
for _ in range(300):
    t=0
    for s in data:
        c15,atr,em,tre=P[s];n=len(c15);cand=[i for i in range(1,n-1) if c15[i][0]>=S1 and c15[i][0]<J1 and atr[i] and tre[i]]
        for _ in range(len(jt[s])):
            i=random.choice(cand);t+=exit_trade(c15,i+1,tre[i],atr[i],k,H)[1]
    sims.append(t)
sims.sort();p95=sims[int(0.95*len(sims))-1];print('RANDOM mean',round(statistics.mean(sims),4),'p95',round(p95,4))
print('VERDICT','GAGNE' if (pos>=2 and tot>p95 and N>=30) else 'PERD')
