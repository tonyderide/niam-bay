import json, time, random, statistics as st
src=open('t46.py').read(); ns={'__file__':'t46.py'}; exec(src[:src.index("R = {}")], ns)
trade, nouvelles, J, A21, A26, T_FIN, anc = ns['trade'], ns['nouvelles'], ns['J'], ns['A21'], ns['A26'], ns['T_FIN'], ns['anciennes_a']
ei={s['symbol']:s.get('underlyingType') for s in json.load(open('listings/exchangeInfo-20261101.json'))['symbols']}
nonc=lambda s: ei.get(s,'COIN')!='COIN'
print('non-crypto connus', sorted(s for s in ns['C'] if nonc(s))[:60], len([s for s in ns['C'] if nonc(s)]))
out={}
for N in (14,30,60,90):
  for nom,ok in (('choix',lambda e:A21<=e<A26),('2026',lambda e:A26<=e<=T_FIN-(N-1)*J)):
    T=[(e,s,trade(s,e,N)) for e,s in nouvelles if ok(e) and not nonc(s)]; T=[x for x in T if x[2]]
    out[(N,nom)]=T; print(N,nom,len(T),round(st.mean(t[0] for *_,t in T),4))
T=out[(90,'2026')]; m=st.mean(t[0] for *_,t in T); rng=random.Random(46); tem=[]; pool={}
for _ in range(1000):
    r=[]
    for e,s,_ in T:
        if e not in pool: pool[e]=[x for x in anc(e) if not nonc(x)]
        t=None
        while t is None: t=trade(rng.choice(pool[e]),e,90)
        r.append(t[0])
    tem.append(st.mean(r))
print('crypto seulement N=90 2026', len(T), round(m,4), 'témoin', round(st.mean(tem),4), 'p', sum(x>=m for x in tem)/1000)
mo={}
for e,s,t in T: mo.setdefault(time.strftime('%Y-%m',time.gmtime(e/1000)),[]).append(t[0])
print({k:(len(v),round(st.mean(v),3)) for k,v in sorted(mo.items())})
