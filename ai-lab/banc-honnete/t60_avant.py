"""PREREG-60, vérification après verdict : la pièce avait-elle déjà monté avant l'ouverture du perpétuel ? Et l'effet tient-il sans les pièces qui ont le plus monté ?"""
import os, random, statistics as st
src = open("t60.py").read(); ns = {"__file__": os.path.abspath("t60.py")}; exec(src[:src.index("res = dict(")], ns)
S, EV, J, pool, mesure, bilan = ns["S"], ns["EV"], ns["J"], ns["pool"], ns["mesure"], ns["bilan"]
def avant(s, e):
    a = e - 31 * J
    return S[s][e - J][1] / S[s][a][0] - 1 if a in S[s] and e - J in S[s] else None
r_ev = [(x, avant(x[1], x[0])) for x in EV]; r_ev = [(x, v) for x, v in r_ev if v is not None]
rng = random.Random(61); tem = []
for (e, s, _), _ in r_ev:
    for _ in range(20):
        c = rng.choice(pool(e, s)); v = avant(c, e)
        if v is not None: tem.append(v)
print("hausse des 30 jours avant l'ouverture : événements moyenne", round(st.mean(v for _, v in r_ev), 4), "médiane", round(st.median(v for _, v in r_ev), 4),
      "| pièces anciennes même date moyenne", round(st.mean(tem), 4), "médiane", round(st.median(tem), 4))
med = st.median(v for _, v in r_ev); bas = [x for x, v in r_ev if v <= med]
print("moitié des événements à la plus faible hausse préalable :", bilan(bas, 62))
