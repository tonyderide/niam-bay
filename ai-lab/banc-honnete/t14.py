"""Vérification de la martingale de Martin (MartingaleEngine) : TP / SL fixes, perte -> mise x2 et sens inversé, gain -> mise initiale.
Paramètres = exemples du code (BotConfig) : TP 1,5 %, SL 1,0 %, 4 doublements max. BTC 15 min, 2024-01 -> 2026-10.
Exécution prudente : si une bougie touche TP et SL, on compte le SL. Frais taker 0,05 % par côté sur la mise."""
import calendar, pickle, time, sys
ts = lambda d: calendar.timegm(time.strptime(d, "%Y-%m-%d"))
T, C = pickle.load(open("/home/tony/.cache/banc-honnete/PF_XBTUSD_15m_2023-11-01.pkl", "rb"))
TP, SL, NMAX, FEE = [float(x) for x in sys.argv[1:4]] + [0.0005] if len(sys.argv) > 3 else (0.015, 0.010, 4, 0.0005)
NMAX = int(NMAX)
i = next(k for k, t in enumerate(T) if t >= ts("2024-01-01")); fin = len(T) - 1
eq = 0.0; mise = 1.0; d = 0; sens = 1; courbe = []; series_perdues = 0; trades = 0
while i < fin:
    e = C[i][0]; tp = e * (1 + TP * sens); sl = e * (1 - SL * sens); j = i
    while j < fin:
        h, l = C[j][1], C[j][2]
        touche_sl = (l <= sl) if sens > 0 else (h >= sl); touche_tp = (h >= tp) if sens > 0 else (l <= tp)
        if touche_sl: r = -SL; break
        if touche_tp: r = TP; break
        j += 1
    else: break
    eq += mise * (r - 2 * FEE); trades += 1; courbe.append((T[j], eq))
    if r > 0: mise = 1.0; d = 0                        # gain : retour à la mise de départ, même sens (Martin : nextDirection, ici on garde le sens)
    elif d >= NMAX: series_perdues += 1; mise = 1.0; d = 0   # plafond atteint : série abandonnée, perte encaissée
    else: mise *= 2; d += 1; sens = -sens
    i = j + 1
pic = 0; dd = 0
for _, x in courbe: pic = max(pic, x); dd = max(dd, pic - x)
print(f"TP {TP:.1%} SL {SL:.1%} doublements {NMAX} | {trades} trades | séries perdues (5 pertes de suite) : {series_perdues}")
print(f"Résultat total : {eq:+.2f} x la position de départ | pire chute : {dd:.2f} x | une série perdue coûte {sum(2**k for k in range(NMAX+1))*SL:.2f} x (+ frais)")
# fenêtres de 3 mois glissantes, départ chaque semaine
W = 91 * 86400; pos = tot = 0; k0 = 0
t = courbe[0][0]
while t + W <= courbe[-1][0]:
    a = next(x for tt, x in reversed(courbe) if tt <= t) if courbe[0][0] <= t else 0
    b = next(x for tt, x in reversed(courbe) if tt <= t + W)
    pos += b > a; tot += 1; t += 7 * 86400
print(f"Fenêtres de 3 mois : {pos}/{tot} positives ({pos/tot:.0%})")
