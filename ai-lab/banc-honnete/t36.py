"""PREREG-36 : basis trimestriel BTC/ETH tenu jusqu'à livraison (règles : PREREG-36-basis-trimestriel.md, commit 3f42529).
Prix publics Binance seulement (fapi klines des contrats livrés, api/v3 comptant), bougies 1 h, cache dans basis/."""
import datetime as dt, json, os, random, time, urllib.request
ICI = os.path.dirname(os.path.abspath(__file__)); C = os.path.join(ICI, "basis"); os.makedirs(C, exist_ok=True)
H = 3_600_000; FS, FF, MARGE, LIQ, RF = 0.001, 0.0005, 0.5, 1.45, 0.04

def get(url):
    for e in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "nb-labo"}), timeout=30) as r: return json.load(r)
        except Exception as x:
            if e == 4: raise
            time.sleep(3 * (e + 1))

def kl(base, sym, t0, t1):
    f = os.path.join(C, f"{sym}_{t0}_{t1}.json")
    if os.path.exists(f): return json.load(open(f))
    out, t = [], t0
    while t < t1:
        k = get(f"{base}?symbol={sym}&interval=1h&startTime={t}&endTime={t1 - 1}&limit=1000")
        if not k: break
        out += [[int(x[0]), float(x[1]), float(x[2]), float(x[3]), float(x[4])] for x in k]; t = int(k[-1][0]) + H
        time.sleep(0.2)
    json.dump(out, open(f, "w")); return out

def vendredi(an, mois):   # dernier vendredi du mois
    d = dt.date(an, mois + 1, 1) - dt.timedelta(days=1) if mois < 12 else dt.date(an, 12, 31)
    while d.weekday() != 4: d -= dt.timedelta(days=1)
    return d

def ms(d, h=0): return int(dt.datetime(d.year, d.month, d.day, h, tzinfo=dt.timezone.utc).timestamp() * 1000)

L = [vendredi(a, m) for a in range(2020, 2027) for m in (3, 6, 9, 12)]
L = [d for d in L if dt.date(2020, 12, 1) < d <= dt.date(2026, 9, 30)]
R = []
for pc in ("BTC", "ETH"):
    for prev, liv in zip(L, L[1:]):
        sym = f"{pc}USDT_{liv:%y%m%d}"; t0 = ms(prev + dt.timedelta(days=1)); t1 = ms(liv, 8)
        F = kl("https://fapi.binance.com/fapi/v1/klines", sym, ms(prev - dt.timedelta(days=200)) if prev == L[0] else t0, t1)
        F = [x for x in F if x[0] >= min(t0, F[0][0] if F else t0)] if F else F
        if not F or F[-1][0] < t1 - 2 * H: print("absent/incomplet", sym, len(F)); continue
        F = [x for x in F if x[0] >= t0] or F    # entrée au jour qui suit la livraison précédente, ou 1re bougie
        e0 = F[0][0]; S = {x[0]: x for x in kl("https://api.binance.com/api/v3/klines", f"{pc}USDT", e0, t1 + H)}
        F0, S0 = F[0][1], S[e0][1]; force = None
        for x in F:
            if x[2] >= F0 * LIQ: force = x; break
        if force: Fs, Ss, fin = F0 * LIQ, S[force[0]][4], force[0]
        else: Fs, Ss, fin = F[-1][4], S[t1][1], t1
        frais = FS * (S0 + Ss) + FF * (F0 + Fs)
        r = ((F0 - Fs) + (Ss - S0) - frais) / ((1 + MARGE) * S0); j = (fin - e0) / 86_400_000
        hausse = max(x[2] for x in F) / F0 - 1
        R.append(dict(contrat=sym, pc=pc, livraison=str(liv), entree=dt.datetime.utcfromtimestamp(e0 / 1000).strftime("%Y-%m-%d %H"),
                      jours=round(j, 1), basis_entree_an=round((F0 / S0 - 1) * 365 / max(j, 1), 4), r=round(r, 5), r_an=round(r * 365 / j, 4),
                      ecart_reglement=round(Fs / Ss - 1, 5) if not force else None, hausse_max=round(hausse, 3), force=bool(force), F=F, S0=S0, e0=e0, t1=t1))
        print(sym, R[-1]["entree"], R[-1]["jours"], "r", R[-1]["r"], "an", R[-1]["r_an"], "force" if force else "", flush=True)

# témoin : jour d'entrée au hasard dans le trimestre (info)
rng = random.Random(36); tem = []
for _ in range(1000):
    xs = []
    for c in R:
        if c["livraison"] < "2026": continue
        F = c["F"]; k = rng.randrange(0, max(1, len(F) - 24)); x = F[k]
        S = {y[0]: y for y in kl("https://api.binance.com/api/v3/klines", c["contrat"][:7], c["e0"], c["t1"] + H)}
        if x[0] not in S: continue
        F0, S0 = x[1], S[x[0]][1]; Fs, Ss = F[-1][4], S[c["t1"]][1]
        rr = ((F0 - Fs) + (Ss - S0) - FS * (S0 + Ss) - FF * (F0 + Fs)) / ((1 + MARGE) * S0); j = (c["t1"] - x[0]) / 86_400_000
        xs.append(rr * 365 / j)
    tem.append(sum(xs) / len(xs))
for c in R: c.pop("F")
an = {}
for c in R: an.setdefault(c["livraison"][:4], []).append(c["r"])
par_an = {a: round(sum(v) / 2, 5) for a, v in an.items()}   # moitié BTC / moitié ETH : somme des contrats / 2
j26 = [c for c in R if c["livraison"] >= "2026"]
m26 = sum(c["r_an"] for c in j26) / len(j26); mall = sum(c["r_an"] for c in R) / len(R)
v = "GAGNE" if m26 > RF and all(c["r"] > 0 for c in j26) and mall > RF and len(j26) == 6 else "NON DÉMONTRÉ" if sum(c["r"] for c in j26) > 0 else "PERD"
res = dict(contrats=R, par_an=par_an, annualise_moyen_2026=m26, annualise_moyen_tout=mall, n2026=len(j26), positifs_2026=sum(c["r"] > 0 for c in j26),
           forces=sum(c["force"] for c in R), temoin_entree_hasard_2026=dict(moy=sum(tem) / len(tem), p_ge=sum(t >= m26 for t in tem) / len(tem)), verdict=v)
json.dump(res, open(os.path.join(ICI, "t36.json"), "w"), indent=1)
print(json.dumps({k: res[k] for k in res if k != "contrats"}, indent=1))
