import json,random,calendar
SYMS=["PF_XBTUSD","PF_ETHUSD","PF_SOLUSD"];FEE=0.001;SL=0.001
def ts(y,m,d): return calendar.timegm((y,m,d,0,0,0))
SEL=(ts(2026,1,1),ts(2026,7,1));JUG=(ts(2026,7,1),ts(2026,10,17))
def load(s):
    d=json.load(open(s+".json"));g={}
    for t,v in d.items():
        g.setdefault(int(t)//180,[]).append((int(t),v))
    B=[]
    for k in sorted(g):
        l=sorted(g[k]);o=l[0][1][0];h=max(x[1][1] for x in l);lo=min(x[1][2] for x in l);c=l[-1][1][3];vol=sum(x[1][4] for x in l)
        B.append((k*180,o,h,lo,c,vol))
    return B
def prep(B):
    n=len(B);ema=[0]*n;vw=[0]*n;day=[0]*n;dopen=[0]*n;first=[0]*n
    a=2/10;e=B[0][4];pv=pq=0;cd=None;do=0;fi=0
    for i,(t,o,h,l,c,v) in enumerate(B):
        e=c*a+e*(1-a) if i else c;ema[i]=e
        dd=t//86400
        if dd!=cd: cd=dd;pv=pq=0;do=o;fi=i
        tp=(h+l+c)/3;pv+=tp*v;pq+=v;vw[i]=pv/pq if pq>0 else tp
        day[i]=dd;dopen[i]=do;first[i]=fi
    return ema,vw,day,dopen,first
def run(B,P,X,rng):
    ema,vw,day,dopen,first=P;n=len(B);tr=[];pos=0;ent=0;ei=0
    sig=[0]*n
    for i in range(1,n):
        if day[i]!=day[i-1] or i-first[i]<3: continue
        p=ema[i-1]-vw[i-1];q=ema[i]-vw[i]
        if p<=0<q: sig[i]=1
        elif p>=0>q: sig[i]=-1
    for i in range(n):
        t,o,h,l,c,v=B[i]
        if not(rng[0]<=t<rng[1]): 
            if pos: 
                pass
            continue
        if i and sig[i-1] and day[i]==day[i-1]:
            s=sig[i-1]
            if pos and pos!=s:
                tr.append((i-ei,pos*(o/ent-1)-FEE,ei));pos=0
            if not pos:
                r=c_prev=B[i-1][4]/dopen[i-1]-1
                if abs(r)>X and (r>0)==(s>0):
                    pos=s;ent=o;ei=i
        if pos:
            slp=ent*(1-SL) if pos>0 else ent*(1+SL)
            if (pos>0 and l<=slp) or (pos<0 and h>=slp):
                tr.append((i-ei+1,pos*(slp/ent-1)-FEE,ei));pos=0
            elif i+1>=n or day[i+1]!=day[i]:
                tr.append((i-ei+1,pos*(c/ent-1)-FEE,ei));pos=0
    return tr
def stats(tr):
    if not tr: return (0,0,0,0,0)
    r=[x[1] for x in tr];cum=pk=dd=0
    for x in r: cum+=x;pk=max(pk,cum);dd=min(dd,cum-pk)
    return (len(r),100*sum(1 for x in r if x>0)/len(r),100*sum(r)/len(r),100*sum(r),100*dd)
def placebo(B,tr,rng,N=300,seed=1):
    R=random.Random(seed);idx=[i for i,b in enumerate(B) if rng[0]<=b[0]<rng[1]];lo,hi=idx[0],idx[-1];out=[]
    for _ in range(N):
        tot=0
        for d,_,_ in tr:
            i=R.randint(lo,hi-d);s=R.choice((1,-1));o=B[i][1];slp=o*(1-SL*s);ex=None
            for j in range(i,i+d):
                if (s>0 and B[j][3]<=slp) or (s<0 and B[j][2]>=slp): ex=slp;break
            if ex is None: ex=B[i+d-1][4]
            tot+=s*(ex/o-1)-FEE
        out.append(tot)
    out.sort();return out
if __name__=="__main__":
    D={s:load(s) for s in SYMS};PP={s:prep(D[s]) for s in SYMS}
    print("SELECTION")
    best=None
    for X in [0.003,0.005,0.0075,0.01,0.015,0.02]:
        tot=0;nt=0;row=[]
        for s in SYMS:
            st=stats(run(D[s],PP[s],X,SEL));tot+=st[3];nt+=st[0];row.append("%d/%.0f%%/%+.2f"%(st[0],st[1],st[3]))
        print(X,nt,"%+.1f"%tot,row)
        if nt>=60 and (best is None or tot>best[1]): best=(X,tot)
    X=best[0] if best else None;print("X chosen",X)
    X0=0
    print("(ref sans filtre, selection)",[ "%d/%+.1f"%(stats(run(D[s],PP[s],0,SEL))[0],stats(run(D[s],PP[s],0,SEL))[3]) for s in SYMS])
    print("JUGEMENT X=",X)
    for s in SYMS:
        tr=run(D[s],PP[s],X,JUG);st=stats(tr)
        pl=placebo(D[s],tr,JUG) if tr else [0];p95=pl[int(.95*len(pl))-1]*100
        print(s,"trades %d gagn %.0f%% moy %+.3f%% total %+.1f%% creux %.1f%% | p95 hasard %+.1f%% med %+.1f%%"%(st+(p95,pl[len(pl)//2]*100)))
        st0=stats(run(D[s],PP[s],0,JUG));print("   ref sans filtre jugement: %d trades total %+.1f%%"%(st0[0],st0[3]))
