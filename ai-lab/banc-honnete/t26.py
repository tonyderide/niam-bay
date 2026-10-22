"""PREREG-11 (avec les précisions du 22/10) : déséquilibre du carnet d'ordres BTC, horizon 10 s."""
import json, os, random
F = os.path.expanduser("~/.cache/banc-honnete/carnet/PF_XBTUSD-20261021.jsonl")
THETAS = (0.3, 0.5, 0.7, 0.9); H = 10; HMAX = 14; OPT, REAL = 0.0004, 0.0007; NT = 500

S = [json.loads(l) for l in open(F)]
T = [s["t"] for s in S]; MID = [(s["b"][0][0] + s["a"][0][0]) / 2 for s in S]
BID = [s["b"][0][0] for s in S]; ASK = [s["a"][0][0] for s in S]
def imb(s):
    b = sum(q for p, q in s["b"][:5]); a = sum(q for p, q in s["a"][:5]); return (b - a) / (b + a)
I = [imb(s) for s in S]; n = len(S)
gap = [False] + [T[k] - T[k - 1] > 4 for k in range(1, n)]
same = [0] * n                                   # longueur de la série d'instantanés identiques finissant en k
for k in range(1, n): same[k] = same[k - 1] + 1 if S[k]["b"] == S[k - 1]["b"] and S[k]["a"] == S[k - 1]["a"] else 0
mi = (T[0] + T[-1]) / 2; cut = next(k for k in range(n) if T[k] >= mi)


def sortie(i):
    j = i + 1
    while j < n and T[j] < T[i] + H: j += 1
    return j if j < n and T[j] <= T[i] + HMAX else None


def suspect(i, j): return any(gap[k] for k in range(i + 1, j + 1)) or max(same[i:j + 1]) > 3


def strat(a, b, th):
    """[(i, j, sens, mouvement brut)] ; un seul trade à la fois."""
    out = []; excl = ann = 0; i = a
    while i < b:
        if abs(I[i]) > th:
            j = sortie(i)
            if j is None or j >= b: ann += 1; i += 1; continue
            if suspect(i, j): excl += 1; i += 1; continue
            sens = 1 if I[i] > 0 else -1; out.append((i, j, sens, MID[j] / MID[i] - 1)); i = j; continue
        i += 1
    return out, excl, ann


def net(tr, c): return sum(s * m - c for i, j, s, m in tr)


print(f"{n} instantanés, {T[-1]-T[0]:.0f} s ; coupure à l'instantané {cut} ; écarts > 4 s : {sum(gap)} ; séries identiques > 3 : {sum(x > 3 for x in same)}")
best = None
for th in THETAS:
    tr, ex, an = strat(0, cut, th); g = net(tr, OPT)
    print(f"1re moitié θ={th} : {len(tr)} trades, net {100*g:+.2f} % (0,04 %) | exclus {ex}, annulés {an}")
    if len(tr) >= 200 and (best is None or g > best[1]): best = (th, g)
for nom, (a, b) in (("1re moitié", (0, cut)), ("2de moitié", (cut, n))):
    mv = [abs(MID[sortie(i)] / MID[i] - 1) for i in range(a, b) if sortie(i) is not None and sortie(i) < b]
    print(f"plafond du devin {nom} : |mouvement 10 s| moyen {1e4*sum(mv)/len(mv):.2f} pb → devin net {1e4*(sum(mv)/len(mv)-OPT):+.2f} pb/trade")
if best is None: print("aucun θ ne fait ≥ 200 trades sur la 1re moitié : verdict argent non évaluable"); th = None
else: th = best[0]; print(f"θ figé = {th}")

if th is not None:
    tr, ex, an = strat(cut, n, th); g, g7 = net(tr, OPT), net(tr, REAL); rnd = random.Random(11)
    J = sorted(sum(rnd.choice((1, -1)) * m - OPT for i, j, s, m in tr) for _ in range(NT))
    rang = sum(x < g for x in J) / NT
    print(f"\n2de moitié θ={th} : {len(tr)} trades | net {100*g:+.2f} % à 0,04 % ; {100*g7:+.2f} % à 0,07 % | témoin méd {100*J[NT//2]:+.2f} % p95 {100*J[int(.95*NT)]:+.2f} % | rang {rang:.1%} | exclus {ex}, annulés {an}")
    print("VERDICT ARGENT :", "GAGNE" if g > 0 and rang > 0.95 and len(tr) >= 200 else "NON DÉMONTRÉ")
    nz = [(s, m) for i, j, s, m in tr if m != 0]; hit = sum((s > 0) == (m > 0) for s, m in nz) / len(nz)
    JH = sorted(sum((rnd.choice((1, -1)) > 0) == (m > 0) for s, m in nz) / len(nz) for _ in range(NT))
    print(f"VERDICT SENS (sans argent) : bon sens {hit:.1%} sur {len(nz)} trades à mouvement non nul | témoin méd {JH[NT//2]:.1%} p95 {JH[int(.95*NT)]:.1%} → "
          + ("PRÉDIT LE SENS" if hit > JH[int(.95 * NT)] else "NON DÉMONTRÉ"))
    print(f"   gain brut moyen {1e4*sum(s*m for i,j,s,m in tr)/len(tr):+.2f} pb/trade (avant frais)")
    # infos
    pool = [i for i in range(cut, n) if sortie(i) is not None and sortie(i) < n and not suspect(i, sortie(i))]
    JR = sorted(sum(rnd.choice((1, -1)) * (MID[sortie(i)] / MID[i] - 1) - OPT for i in rnd.sample(pool, len(tr))) for _ in range(200))
    print(f"[info] témoin à instants au hasard : méd {100*JR[100]:+.2f} %")
    rem = []
    for i, j, s, m in tr:
        if s > 0 and min(BID[i + 1:j + 1]) < BID[i]: rem.append(MID[j] / BID[i] - 1 - OPT)
        if s < 0 and max(ASK[i + 1:j + 1]) > ASK[i]: rem.append(1 - MID[j] / ASK[i] - OPT)
    print(f"[info] maker « réaliste » (ordre touché par un prix plus bas/haut dans les 10 s) : {len(rem)}/{len(tr)} exécutés, net {100*sum(rem):+.2f} % ({1e4*sum(rem)/max(1,len(rem)):+.2f} pb/trade)")
