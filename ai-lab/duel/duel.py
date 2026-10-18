"""Duel de prédictions Tony contre NB (approuvé par le conseil le 1017, 7.09). Sans LLM.
- Une question par jour, choisie par une règle fixe (jour pair : direction, jour impair : amplitude), tranchée par le mark Kraken Futures.
- NB pose sa probabilité EN PREMIER, et elle est scellée par un commit git avant que Tony ne réponde.
- Tony répond sur Telegram : /pari 70 (= 70 % que ce soit OUI). /duel affiche les scores.
- Brier Tony / NB / hasard (0,5). Pas de vainqueur annoncé avant 30 questions : la chance domine en dessous.
Usage : duel.py new <p_nb> "<raison>" | tony <p> | resolve | board"""
import json, os, subprocess, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CUR, HIST = os.path.join(HERE, "current.json"), os.path.join(HERE, "history.jsonl")


def mark():
    return float(json.load(urllib.request.urlopen("https://futures.kraken.com/derivatives/api/v3/tickers/PF_XBTUSD", timeout=20))["ticker"]["markPrice"])


def hist_mark(symbol, iso_local):
    """Mark Kraken Futures à l'instant prévu (et pas au moment où le script tourne enfin : le PC peut avoir dormi)."""
    import json as _j, time as _t, urllib.request as _u
    ts = int(_t.mktime(_t.strptime(iso_local[:16], "%Y-%m-%dT%H:%M")))
    d = _j.load(_u.urlopen(f"https://futures.kraken.com/api/charts/v1/mark/{symbol}/1m?from={ts - 120}&to={ts + 120}", timeout=20))["candles"]
    best = min(d, key=lambda c: abs(c["time"] / 1000 - ts))
    return float(best["close"])


def new(p_nb, why):
    if os.path.exists(CUR):
        return "une question est déjà ouverte"
    m, day = mark(), int(time.strftime("%j"))
    q = (f"BTC plus haut dans 24 h qu'à {m:.0f} $ ?" if day % 2 == 0 else f"BTC bougera-t-il de plus de 2 % (dans un sens ou l'autre) en 24 h, depuis {m:.0f} $ ?")
    c = {"q": q, "kind": "dir" if day % 2 == 0 else "amp", "ref": m, "nb_p": p_nb, "nb_why": why, "tony_p": None,
         "made": time.time(), "resolve_at": time.time() + 86400}
    json.dump(c, open(CUR, "w"), indent=1, ensure_ascii=False)
    return q  # le scellé (commit git) est fait côté PC par scripts/vm/sync.sh, qui recopie current.json avant que Tony puisse parier


def tony(p):
    if not os.path.exists(CUR):
        return "pas de question ouverte (NB en pose une chaque soir après 20h)"
    c = json.load(open(CUR))
    if c["tony_p"] is not None:
        return f"déjà parié : {int(c['tony_p'] * 100)} %"
    c["tony_p"] = max(0.0, min(1.0, p)); c["tony_at"] = time.time()
    json.dump(c, open(CUR, "w"), indent=1, ensure_ascii=False)
    return f"noté : toi {int(c['tony_p'] * 100)} %, moi {int(c['nb_p'] * 100)} % (scellé avant toi). Verdict le {time.strftime('%d/%m %H:%M', time.localtime(c['resolve_at']))}."


def resolve():
    if not os.path.exists(CUR):
        return
    c = json.load(open(CUR))
    if time.time() < c["resolve_at"]:
        return
    m = hist_mark("PF_XBTUSD", time.strftime("%Y-%m-%dT%H:%M", time.localtime(c["resolve_at"])))  # prix à l'échéance, même si le PC dormait
    c["outcome"] = (m > c["ref"]) if c["kind"] == "dir" else (abs(m / c["ref"] - 1) > 0.02)
    c["final"] = m
    open(HIST, "a").write(json.dumps(c, ensure_ascii=False) + "\n")
    os.remove(CUR)


def board():
    H = [json.loads(l) for l in open(HIST)] if os.path.exists(HIST) else []
    out = []
    if os.path.exists(CUR):
        c = json.load(open(CUR))
        out.append(f"❓ en cours : {c['q']}\n   moi {int(c['nb_p'] * 100)} % · toi " + (f"{int(c['tony_p'] * 100)} %" if c["tony_p"] is not None else "pas encore → /pari 60"))
    both = [h for h in H if h["tony_p"] is not None]
    if both:
        b = lambda k: sum((h[k] - h["outcome"]) ** 2 for h in both) / len(both)
        hz = sum((0.5 - h["outcome"]) ** 2 for h in both) / len(both)
        out.append(f"🏁 {len(both)} duels : Brier toi {b('tony_p'):.3f} · moi {b('nb_p'):.3f} · hasard {hz:.3f} (plus bas = meilleur)"
                   + ("" if len(both) >= 30 else f" ; pas de vainqueur avant 30 ({30 - len(both)} à faire)"))
    return "\n".join(out) or "aucun duel encore"


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "new": print(new(float(a[1]), a[2]))
    elif a[0] == "tony": print(tony(float(a[1])))
    elif a[0] == "resolve": resolve()
    else: print(board())
