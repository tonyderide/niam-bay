import json,random,itertools
d=json.load(open('/home/tony/projets/tonyderide/niam-bay/ai-lab/labo-cutoff/candles.json'))
S0,S1,J0,J1=1767225600,1782777600,1782864000,1792195200  # 2026-01-01, 06-30(23h end), 07-01, 10-16 end
FEE=0.001
def prep(c):
    ts=sorted(d[c],key=int); p=[float(d[c][t]) for t in ts]; ts=[int(t) for t in ts]
    n=len(p); rsi=[None]*n; ema=[None]*n
    g=l=0
    for i in range(1,n):
        ch=p[i]-p[i-1]; u=max(ch,0); w=max(-ch,0)
        if i<=14:
            g+=u/14; l+=w/14
        else:
            g=(g*13+u)/14; l=(l*13+w)/14
        if i>=14: rsi[i]=100 if l==0 else 100-100/(1+g/l)
    e=p[0]
    for i in range(n):
        e=p[i]*2/201+e*(1-2/201) if i else p[0]; ema[i]=e if i>=199 else None
    return ts,p,rsi,ema
D={c:prep(c) for c in ['BTC','ETH','SOL']}
def sim_exit(p,i,dirn,H,SL,rsi=None):
    # entry at close i; returns (exit idx, net ret)
    e=p[i]
    for k in range(i+1,min(i+H,len(p)-1)+1):
        r=dirn*(p[k]/e-1)
        if r<=-SL: return k,r-FEE
        if rsi is not None and rsi[k] is not None and ((dirn==1 and rsi[k]>=50) or (dirn==-1 and rsi[k]<=50)): return k,r-FEE
        if k==i+H: return k,r-FEE
    return k,dirn*(p[k]/e-1)-FEE
def run(c,L,H,SL,a,b):
    ts,p,rsi,ema=D[c]; out=[]; i=0; n=len(p)
    while i<n-2:
        if ts[i]>=a and ts[i+1]<=b and rsi[i] is not None and ema[i] is not None:
            dr=0
            if rsi[i]<L and p[i]>ema[i]: dr=1
            elif rsi[i]>100-L and p[i]<ema[i]: dr=-1
            if dr:
                j=i+1; k,r=sim_exit(p,j,dr,H,SL,rsi); out.append(r); i=k; continue
        i+=1
    return out
grid=list(itertools.product([20,25],[12,24,48,72],[0.02,0.04]))
res=[]
for L,H,SL in grid:
    t=[run(c,L,H,SL,S0,S1) for c in D]; res.append((sum(map(sum,t)),sum(map(len,t)),(L,H,SL)))
res.sort(reverse=True)
for r in res: print('SEL',r)
L,H,SL=res[0][2]; print('CHOIX',L,H,SL)
random.seed(1019)
win=0;tot=0
for c in D:
    r=run(c,L,H,SL,J0,J1); s=sum(r); n=len(r)
    ts,p,_,_=D[c]; idx=[i for i in range(len(p)-H-2) if J0<=ts[i] and ts[i+1]<=J1]
    sims=sorted(sum(sim_exit(p,i+1,random.choice([1,-1]),H,SL)[1] for i in random.sample(idx,n)) for _ in range(300)) if n else [0]
    p95=sims[int(0.95*len(sims))-1]; 
    ok=s>0 and s>p95; win+=ok; tot+=n
    print('JUG',c,'n',n,'net%.2f%%'%(s*100),'moy%.3f%%'%(s/max(n,1)*100),'winrate%.0f%%'%(100*sum(x>0 for x in r)/max(n,1)),'p95hasard%.2f%%'%(p95*100),'ok',ok)
print('coins ok',win,'trades',tot,'VERDICT','GAGNE' if win>=2 and tot>=30 else 'PERD')
print('--- diagnostic (hors prereg)')
for c in D:
    ts,p,rsi,ema=D[c]
    print(c,'RSI<25 total',sum(1 for x in rsi if x and x<25),'RSI>75',sum(1 for x in rsi if x and x>75),'<25&>EMA',sum(1 for i,x in enumerate(rsi) if x and ema[i] and x<25 and p[i]>ema[i]),'>75&<EMA',sum(1 for i,x in enumerate(rsi) if x and ema[i] and x>75 and p[i]<ema[i]))
for c in D: print('L25 H24 SL4 jug',c,[round(sum(run(c,25,24,0.04,J0,J1))*100,2),len(run(c,25,24,0.04,J0,J1))])
