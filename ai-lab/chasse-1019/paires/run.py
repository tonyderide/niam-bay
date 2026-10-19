import json,math,random,itertools
d=json.load(open('/home/tony/projets/tonyderide/niam-bay/ai-lab/labo-cutoff/candles.json'))
ts=sorted(int(t) for t in d['BTC'])
P={k:[d[k][str(t)] for t in ts] for k in d}
def T(s):
    import datetime;return int(datetime.datetime.strptime(s,'%Y-%m-%d').replace(tzinfo=datetime.timezone.utc).timestamp())
S0,S1,J0,J1=T('2026-01-01'),T('2026-07-01'),T('2026-07-01'),T('2026-10-17')
pairs=[('ETH','BTC'),('SOL','ETH'),('LINK','DOT')]
X={p:[math.log(a/b) for a,b in zip(P[p[0]],P[p[1]])] for p in pairs}
def run(x,W,a,b,H,c,lo,hi):
    n=len(x);z=[float('nan')]*n
    cs=[0.0];c2=[0.0]
    for v in x:cs.append(cs[-1]+v);c2.append(c2[-1]+v*v)
    for i in range(W-1,n):
        m=(cs[i+1]-cs[i+1-W])/W;var=(c2[i+1]-c2[i+1-W])/W-m*m
        z[i]=(x[i]-m)/math.sqrt(var) if var>1e-18 else float('nan')
    tr=[]
    idx=[j for j,t in enumerate(ts) if lo<=t<hi];i=idx[0];end=idx[-1]
    while i<end-1:
        if z[i]==z[i] and abs(z[i])>a:
            side=-1 if z[i]>0 else 1;e=i+1;ex=e
            for k in range(e,min(e+H,end)+1):
                ex=k
                if abs(z[k])<b or abs(z[k])>c:break
            tr.append((e,ex-e,side*(x[ex]-x[e])-0.002));i=ex+1
        else:i+=1
    return tr
grid=list(itertools.product([48,168],[1.5,2,2.5],[0,0.5],[24,72]))
res=[]
for g in grid:
    W,a,b,H=g;res.append((sum(t[2] for p in pairs for t in run(X[p],W,a,b,H,4,S0,S1)),g))
res.sort(reverse=True);print(res[:3]);W,a,b,H=best=res[0][1]
net={};cnt={};durs={}
for p in pairs:
    t=run(X[p],W,a,b,H,4,J0,J1);net[p]=sum(q[2] for q in t);cnt[p]=len(t);durs[p]=[q[1] for q in t]
    print(p,cnt[p],round(net[p]*100,2),'%')
tot=sum(net.values());N=sum(cnt.values())
random.seed(1);idx=[j for j,t in enumerate(ts) if J0<=t<J1];sim=[]
for _ in range(500):
    s=0
    for p in pairs:
        x=X[p]
        for _ in range(cnt[p]):
            e=random.choice(idx[:-80]);dd=random.choice(durs[p]);s+=random.choice([-1,1])*(x[e+dd]-x[e])-0.002
    sim.append(s)
sim.sort();p95=sim[int(0.95*len(sim))]
print('best',best,'tot%',round(tot*100,2),'N',N,'p95%',round(p95*100,2),'mean rand%',round(sum(sim)/len(sim)*100,2))
print('pairs>0',sum(v>0 for v in net.values()),'GAGNE',sum(v>0 for v in net.values())>=2 and tot>p95 and N>=30)
