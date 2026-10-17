"""Jumeau de 0x6f03…c88d sur BTC (Hyperliquid), paramètres FIGÉS par le commit qui crée ce fichier (avant toute heure de test).
Règle déduite des 807 fills d'entraînement (08/10 18h32 → 17/10 00h46 UTC) : il achète les creux.
  r6 = rendement des 6 dernières heures closes ; dd24 = clôture vs plus haut des 24 h
  si r6 ≤ -0,20 % ET dd24 ≤ -1,23 % → p = 0,20 (9/45 à l'entraînement), sinon p = 0,013 (2/156).
Juge (PREREGISTRATION.md + amendement n°1) : à chaque heure H, p_H est noté au début de H ; l'issue est « au moins un Open Long BTC pendant H ».
Témoins : taux de base 0,055 ; « comme l'heure d'avant » (0,8 si ouverture en H-1, sinon 0,055).
Lancé par cron à la minute 2 : tranche l'heure précédente et prédit l'heure en cours. Lecture seule, 2 requêtes par heure."""
import json, os, time, urllib.request

A = "0x6f0306dc529cfeb8e08502e5eb7a588def9ac88d"
HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "test_log.jsonl")
T6, TD, P_HI, P_LO, BASE = -0.0020, -0.0123, 0.20, 0.013, 0.055


def info(b):
    r = urllib.request.Request("https://api.hyperliquid.xyz/info", data=json.dumps(b).encode(), headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(r, timeout=30))


def main():
    now = int(time.time() * 1000); H = now // 3600000 * 3600000; prev = H - 3600000
    rows = [json.loads(l) for l in open(LOG)] if os.path.exists(LOG) else []
    pending = {r["H"]: r for r in rows if r.get("outcome") is None}
    if prev in pending:  # trancher l'heure précédente
        f = info({"type": "userFillsByTime", "user": A, "startTime": prev, "endTime": H - 1})
        pending[prev]["outcome"] = int(any(x["coin"] == "BTC" and x["dir"] == "Open Long" for x in f))
        pending[prev]["n_fills"] = len([x for x in f if x["coin"] == "BTC"])
        time.sleep(2)
    if not any(r["H"] == H for r in rows):  # prédire l'heure en cours
        c = info({"type": "candleSnapshot", "req": {"coin": "BTC", "interval": "1h", "startTime": H - 26 * 3600000, "endTime": H - 1}})
        c = [k for k in c if int(k["t"]) < H][-25:]
        cl = [float(k["c"]) for k in c]
        r6 = cl[-1] / cl[-7] - 1; dd = cl[-1] / max(float(k["h"]) for k in c[-24:]) - 1
        last = next((r for r in rows if r["H"] == prev), None)
        rows.append({"H": H, "utc": time.strftime("%FT%H:00Z", time.gmtime(H / 1000)), "r6": round(r6, 5), "dd24": round(dd, 5),
                     "p_twin": P_HI if (r6 <= T6 and dd <= TD) else P_LO, "p_base": BASE,
                     "p_prev": 0.8 if (last and last.get("outcome")) else BASE, "outcome": None})
    open(LOG, "w").write("".join(json.dumps(r) + "\n" for r in rows))
    done = [r for r in rows if r.get("outcome") is not None]
    if done:
        b = lambda k: sum((r[k] - r["outcome"]) ** 2 for r in done) / len(done)
        print(f"{len(done)}/168 h | Brier jumeau {b('p_twin'):.4f} | taux de base {b('p_base'):.4f} | heure d'avant {b('p_prev'):.4f} | ouvertures {sum(r['outcome'] for r in done)}")


if __name__ == "__main__":
    main()
