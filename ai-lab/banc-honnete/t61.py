import json,sys,os,time,urllib.request,datetime as dt
import numpy as np
D=sys.argv[1]; T=['SPY','EFA','IEF','VNQ','DBC','^IRX']
def get(t):
    p=f'{D}/{t}.json'
    if not os.path.exists(p):
        u=f'https://query1.finance.yahoo.com/v8/finance/chart/{t.replace("^","%5E")}?period1=1100000000&period2=1793750000&interval=1d'
        open(p,'wb').write(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=40).read()); time.sleep(1)
    r=json.load(open(p))['chart']['result'][0]; q=r['indicators']
    a=q['adjclose'][0]['adjclose'] if 'adjclose' in q else q['quote'][0]['close']
    m={}
    for ts,v in zip(r['timestamp'],a):
        if v is None: continue
        d=dt.datetime.fromtimestamp(ts,dt.timezone.utc); m[(d.year,d.month)]=(v,d.date())
    return m
M={t:get(t) for t in T}
for t in T:
    k=sorted(M[t]); print(t,'mois',len(k),k[0],'->',k[-1],'dernier jour',M[t][k[-1]][1])
mois=[(y,m) for y in range(2006,2027) for m in range(1,13) if (2006,3)<=(y,m)<=(2026,10)]
A=T[:5]; P={t:np.array([M[t].get(k,(np.nan,))[0] for k in mois],float) for t in A}
for t in A: assert not np.isnan(P[t]).any(),t
irx=np.array([M['^IRX'].get(k,(np.nan,))[0] for k in mois],float); irx=np.where(np.isnan(irx),0,irx)/100/12
R={t:P[t][1:]/P[t][:-1]-1 for t in A}; idx=[i for i,k in enumerate(mois[1:]) if (2007,1)<=k<=(2026,10)]
cash=irx[:-1]  # taux connu en debut de mois
def run(w):
    v=[];pw=None
    for i in idx:
        wi=w(i); c=0 if pw is None else 0.001*sum(abs(wi[t]-pw[t]) for t in A)
        g=sum(wi[t]*R[t][i] for t in A)+(1-sum(wi.values()))*cash[i]
        v.append(g-c); pw={t:wi[t]*(1+R[t][i])/(1+g) for t in A}
    return np.array(v)
def faber(i):
    w={}
    for t in A:
        # P index i = fin du mois precedant le rendement i
        h=P[t][i-9:i+1]; w[t]=0.2 if len(h)==10 and P[t][i]>h.mean() else 0.0
    return w
S={'A':run(lambda i:{t:(1.0 if t=='SPY' else 0.0) for t in A}),'B':run(lambda i:{t:{'SPY':.6,'IEF':.4}.get(t,0.0) for t in A}),'C':run(lambda i:{t:.2 for t in A}),'D':run(faber)}
c=cash[idx]; K=[mois[1:][i] for i in idx]
def st(r,c):
    e=np.cumprod(1+r); dd=(e/np.maximum.accumulate(np.r_[1,e])[1:]-1).min()
    return dict(cagr=e[-1]**(12/len(r))-1,vol=r.std()*12**.5,sharpe=(r-c).mean()/(r-c).std()*12**.5,maxdd=dd,mult=e[-1],neg_years=None)
cut=[i for i,k in enumerate(K) if k[0]<=2016]; cut2=[i for i,k in enumerate(K) if k[0]>2016]
for n,s in S.items():
    print(n,'ALL',{k:round(v,3) for k,v in st(s,c).items() if v is not None}); print('  2007-16',round(st(s[cut],c[cut])['maxdd'],3),round(st(s[cut],c[cut])['cagr'],3),'  2017-26',round(st(s[cut2],c[cut2])['maxdd'],3),round(st(s[cut2],c[cut2])['cagr'],3))
    y={}
    for k,x in zip(K,s): y[k[0]]=y.get(k[0],1)*(1+x)
    print('  annees neg',sum(v<1 for v in y.values()),'pire annee',min(y,key=y.get),round(y[min(y,key=y.get)]-1,3),'2022',round(y[2022]-1,3),'2026',round(y[2026]-1,3))
print('expo moy D',round(np.mean([sum(faber(i).values()) for i in idx]),3))
rng=np.random.default_rng(61); n=len(idx); a,d=S['A']-c,S['D']-c; ob=d.mean()/d.std()-a.mean()/a.std(); ge=0
cen_a,cen_d=a,d
for _ in range(10000):
    st_=rng.integers(0,n,n//12+1); ii=np.concatenate([(np.arange(12)+x)%n for x in st_])[:n]
    x=d[ii].mean()/d[ii].std()-a[ii].mean()/a[ii].std()
    if x-ob>=ob: ge+=1
print('dSharpe annualise',round(ob*12**.5,3),'p',round(ge/10000,4))
