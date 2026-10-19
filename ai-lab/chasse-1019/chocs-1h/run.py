import json,random,statistics as st,itertools,calendar,datetime
d=json.load(open('/home/tony/projets/tonyderide/niam-bay/ai-lab/labo-cutoff/candles.json'))
COINS=['BTC','ETH','SOL'];FEE=0.001
T=lambda s:calendar.timegm(datetime.datetime.strptime(s,'%Y-%m-%d').timetuple())
S0,S1,J0,J1=T('2026-01-01'),T('2026-07-01'),T('2026-07-01'),T('2026-10-17')
data={}
for c in COINS:
    ks=sorted(d[c],key=int);data[c]=([int(k) for k in ks],[d[c][k] for k in ks])
def prep(c):
    ts,p=data[c];n=len(p);r=[0]+[p[i]/p[i-1]-1 for i in range(1,n)]
    sd=[None]*n
    for i in range(169,n):
        w=r[i-168:i];sd[i]=st.pstdev(w)
    return ts,p,r,sd
P={c:prep(c) for c in COINS}
def trade(p,e,H,side,sl=None,tp=None):
    n=len(p)
    x=min(e+H,n-1)
    if sl or tp:
        for j in range(e+1,x+1):
            ret=side*(p[j]/p[e]-1)
            if sl and ret<=-sl: return j,ret-FEE
            if tp and ret>=tp: return j,ret-FEE
    return x,side*(p[x]/p[e]-1)-FEE
def run(c,lo,hi,k,H,sens,sl=None,tp=None):
    ts,p,r,sd=P[c];out=[];free=0
    for t in range(169,len(p)-2):
        if not(lo<=ts[t]<hi) or t+1<free: continue
        if abs(r[t])>k*sd[t]:
            side=(1 if r[t]>0 else -1)*(1 if sens=='suite' else -1)
            x,net=trade(p,t+1,H,side,sl,tp);out.append(net);free=x
    return out
def tot(lo,hi,*a,**kw):
    res={c:run(c,lo,hi,*a,**kw) for c in COINS};return res
def s(res):return sum(sum(v) for v in res.values())
best=None
for k,H,sens in itertools.product([2,3,4,5],[1,2,3,6,12,24],['suite','retour']):
    r=tot(S0,S1,k,H,sens);n=sum(len(v) for v in r.values())
    if n>=30 and (best is None or s(r)>best[0]):best=(s(r),k,H,sens,n)
print('SEL best',best);_,k,H,sens,_=best
bv=None
for sl,tp in itertools.product([.005,.01,.02,.03],[.005,.01,.02,.03,.05]):
    r=tot(S0,S1,k,H,sens,sl,tp);n=sum(len(v) for v in r.values())
    if n>=30 and (bv is None or s(r)>bv[0]):bv=(s(r),sl,tp,n)
print('SEL var',bv);_,sl,tp,_=bv
def report(name,kw):
    r=tot(J0,J1,k,H,sens,**kw);cnt={c:len(r[c]) for c in COINS}
    nets={c:round(sum(r[c])*100,2) for c in COINS};tt=s(r)
    random.seed(7);ds=[]
    for _ in range(300):
        tot_=0
        for c in COINS:
            ts,p,_r,_s=P[c];idx=[t for t in range(169,len(p)-2) if J0<=ts[t]<J1]
            for _i in range(cnt[c]):
                t=random.choice(idx);tot_+=trade(p,t+1,H,random.choice([1,-1]),kw.get('sl'),kw.get('tp'))[1]
        ds.append(tot_)
    ds.sort();p95=ds[int(.95*300)-1]
    pos=sum(1 for c in COINS if nets[c]>0);ntr=sum(cnt.values())
    print(name,'trades',cnt,'net%/coin',nets,'pool%',round(tt*100,2),'p95%',round(p95*100,2),'hasard moy%',round(sum(ds)/300*100,2),
      'VERDICT','GAGNE' if pos>=2 and tt>p95 and ntr>=30 else 'PERDU')
report('base',{});report('SLTP',{'sl':sl,'tp':tp})
