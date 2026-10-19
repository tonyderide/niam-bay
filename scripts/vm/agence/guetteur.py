#!/usr/bin/env python3
"""Le guetteur de l'agence (1019). Sans IA, sur la VM, toutes les 5 min. Il ne réveille l'agence que s'il y a une raison, et UNE seule raison par réveil.
Raisons : danger compte | le marché change de nature | une expérience arrive à son verdict | revue du dimanche. (« Tony la convoque » passe par /agence.)
Chaque raison a un délai de garde (pas de réveil en boucle). Sortie : ~/nb/agence/reveils.jsonl, lu par l'agence (mode recherche seule)."""
import json, os, re, time, urllib.request
os.environ["TZ"] = "Europe/Paris"; time.tzset()
NB = os.path.expanduser("~/nb"); D = os.path.join(NB, "agence"); os.makedirs(D, exist_ok=True)
OUT, ST = os.path.join(D, "reveils.jsonl"), os.path.join(D, "guetteur_state.json")
H = 3600
COOLDOWN = {"danger": 1 * H, "marche": 6 * H, "verdict": 24 * H, "dimanche": 6 * 86400}


def btc():
    now = int(time.time()) // H * H
    d = json.load(urllib.request.urlopen(f"https://futures.kraken.com/api/charts/v1/mark/PF_XBTUSD/1h?from={now - 260 * H}&to={now}", timeout=30))["candles"]
    return [float(c["close"]) for c in d], [float(c["high"]) - float(c["low"]) for c in d]


def raisons(st):
    out = []
    log = open(os.path.expanduser("~/et/et.log")).read().splitlines()[-40:]
    txt = "\n".join(log)
    if "CRITICAL" in "\n".join(log[-6:]): out.append(("danger", "exchange-truth signale un CRITICAL (stop absent ou compte non protégé)"))
    cush = re.findall(r"cushion ([0-9.]+)", txt)
    if cush and float(cush[-1]) < 0.10: out.append(("danger", f"coussin de marge {cush[-1]} $ < 0,10 $"))
    npos = re.findall(r"(\d+) positions", txt)
    if npos:
        if st.get("npos") is not None and int(npos[-1]) != st["npos"]: out.append(("danger", f"nombre de positions changé : {st['npos']} → {npos[-1]}"))
        st["npos"] = int(npos[-1])
    c, rng = btc()
    r1, r24 = c[-1] / c[-2] - 1, c[-1] / c[-25] - 1
    if abs(r1) > 0.03: out.append(("marche", f"BTC {r1*100:+.1f} % en 1 h"))
    if abs(r24) > 0.06: out.append(("marche", f"BTC {r24*100:+.1f} % en 24 h"))
    e = c[0]
    for x in c: e = e + (x - e) * 2 / 201
    side = "dessus" if c[-1] > e else "dessous"
    if st.get("ema200_side") and side != st["ema200_side"]: out.append(("marche", f"BTC passe au-{side} de son EMA200 ({e:.0f})"))
    st["ema200_side"] = side
    med = sorted(rng[:-24])[len(rng[:-24]) // 2]; vol = sum(rng[-24:]) / 24
    if vol > 2 * med: out.append(("marche", f"volatilité ×{vol/med:.1f} par rapport à la normale"))
    p = os.path.join(NB, "papier-dot/paper.jsonl")
    n = sum(1 for _ in open(p)) if os.path.exists(p) else 0
    if n >= 30 or (n >= 10 and st.get("papier_alerte") is None):
        out.append(("verdict", f"test papier DOT : {n} paris, l'heure du verdict ou du seuil d'arrêt")); st["papier_alerte"] = n
    tw = os.path.join(NB, "jumeau/test_log.jsonl")
    if os.path.exists(tw) and sum(1 for _ in open(tw)) >= 168 and not st.get("jumeau_fini"):
        out.append(("verdict", "le jumeau a ses 168 h : verdict pré-enregistré à lire")); st["jumeau_fini"] = True
    if time.strftime("%F") >= "2026-10-31" and not st.get("calib_fini"):
        out.append(("verdict", "fin du test de calibration dir24h (31/10)")); st["calib_fini"] = True
    lt = time.localtime()
    if lt.tm_wday == 6 and lt.tm_hour == 20: out.append(("dimanche", "revue courte de la semaine (Haiku)"))
    return out


def main():
    st = json.load(open(ST)) if os.path.exists(ST) else {}
    last = st.setdefault("last", {}); now = time.time(); fired = []
    for kind, why in raisons(st):
        if now - last.get(kind, 0) >= COOLDOWN[kind]:
            last[kind] = now; fired.append({"t": time.strftime("%F %H:%M"), "type": kind, "raison": why, "mode": "recherche seule", "traite": False})
            break  # une seule raison par réveil
    for f in fired:
        open(OUT, "a").write(json.dumps(f, ensure_ascii=False) + "\n")
    json.dump(st, open(ST, "w"))
    if fired: print(fired[0])


if __name__ == "__main__":
    main()
