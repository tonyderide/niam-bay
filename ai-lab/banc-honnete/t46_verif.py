import json, time, statistics as st, urllib.request, sys
sys.argv=['x']; src=open('t46.py').read(); ns={'__file__':'t46.py'}
exec(src[:src.index("R = {}")], ns)
trade, nouvelles, J, A26, T_FIN, C = ns['trade'], ns['nouvelles'], ns['J'], ns['A26'], ns['T_FIN'], ns['C']
T=[(e,s,trade(s,e,90)) for e,s in nouvelles if A26<=e<=T_FIN-89*J]; T=[x for x in T if x[2]]
m={}
for e,s,t in T: m.setdefault(time.strftime('%Y-%m',time.gmtime(e/1000)),[]).append(t[0])
print({k:(len(v),round(st.mean(v),3)) for k,v in sorted(m.items())})
T.sort(key=lambda x:x[2][0]); print('pires',[(s,time.strftime('%m-%d',time.gmtime(e/1000)),round(t[0],2)) for e,s,t in T[:5]]); print('meilleurs',[(s,round(t[0],2)) for e,s,t in T[-5:]])
# vérification indépendante d'un trade via l'API
e,s,t=T[len(T)//2]; k=json.load(urllib.request.urlopen(f"https://fapi.binance.com/fapi/v1/klines?symbol={s}&interval=1d&startTime={e}&limit=90"))
print(s, 'mon entrée', C[s][e][0], 'api', float(k[0][1]), 'ma sortie', C[s][e+89*J][1], 'api', float(k[-1][4]), 'brut', round(t[1],4), 'api', round(-(float(k[-1][4])/float(k[0][1])-1),4))
# sans plancher / sans les 10 meilleurs
r=[t[0] for _,_,t in T]; print('moy', round(st.mean(r),4), 'sans 10 meilleurs', round(st.mean(sorted(r)[:-10]),4), 'mois positifs', sum(st.mean(v)>0 for v in m.values()),'/',len(m))
