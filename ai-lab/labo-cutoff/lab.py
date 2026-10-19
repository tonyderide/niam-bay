"""Laboratoire du cutoff (protocole 60f9405). Lecture seule de l'API charts Kraken Futures ; prédicteur = claude -p Opus 5.5 en aveugle."""
import concurrent.futures as cf, json, os, random, re, subprocess, time, urllib.request
SYM = {"BTC": "PF_XBTUSD", "ETH": "PF_ETHUSD", "SOL": "PF_SOLUSD", "DOT": "PF_DOTUSD", "LINK": "PF_LINKUSD"}
H = 3600
ts = lambda d: int(time.mktime(time.strptime(d, "%Y-%m-%d")))
PROMPT = open("prompt.txt").read()


def candles(sym, start, end):
    out = {}; t = start
    while t < end:
        d = json.load(urllib.request.urlopen(f"https://futures.kraken.com/api/charts/v1/mark/{sym}/1h?from={t}&to={min(end, t + 1500 * H)}", timeout=30))["candles"]
        for c in d: out[c["time"] // 1000] = float(c["close"])
        t += 1500 * H; time.sleep(1)
    return out


def main():
    data = {k: candles(s, ts("2026-01-01"), ts("2026-10-17")) for k, s in SYM.items()}
    json.dump({k: {str(t): v for t, v in d.items()} for k, d in data.items()}, open("candles.json", "w"))
    ups = [data[k][t + 24 * H] > data[k][t] for k in data for t in data[k] if t < ts("2026-07-01") and t + 24 * H in data[k]]
    base = sum(ups) / len(ups)
    rnd = random.Random(1019); items = []
    for k in SYM:
        cand = [t for t in data[k] if ts("2026-07-15") <= t <= ts("2026-10-16") and all(t - i * H in data[k] for i in range(49)) and t + 24 * H in data[k]]
        rnd.shuffle(cand); chosen = []
        for t in cand:
            if all(abs(t - c) >= 36 * H for c in chosen): chosen.append(t)
            if len(chosen) == 60: break
        for t in chosen:
            px = [data[k][t - i * H] for i in range(48, -1, -1)]
            rets = [round((px[i + 1] / px[i] - 1) * 100, 3) for i in range(48)]
            items.append({"coin": k, "t": t, "rets": rets, "up": int(data[k][t + 24 * H] > data[k][t]), "mom": 0.55 if px[-1] > px[-25] else 0.45})

    def ask(it):
        q = PROMPT + "\n" + " ".join(f"{r:+.3f}" for r in it["rets"])
        for _ in range(2):
            r = subprocess.run(["claude", "-p", q, "--model", "claude-opus-5-5", "--tools", ""], capture_output=True, text=True, timeout=300,
                               env={**os.environ, "NB_FACTCHECK_CHILD": "1"})
            m = re.findall(r"P\s*=\s*(0?\.\d+|1\.0+|0|1)", r.stdout)
            if m: return float(m[-1])
        return None
    with cf.ThreadPoolExecutor(4) as ex:
        ps = list(ex.map(ask, items))
    for it, p in zip(items, ps): it["p"] = p
    json.dump({"base_rate": base, "items": items}, open("results.json", "w"))
    ok = [i for i in items if i["p"] is not None]
    br = lambda f: sum((f(i) - i["up"]) ** 2 for i in ok) / len(ok)
    b_op, b_05, b_base, b_mom = br(lambda i: i["p"]), br(lambda i: 0.5), br(lambda i: base), br(lambda i: i["mom"])
    best = min(b_05, b_base, b_mom)
    blocks = {}
    for i in ok: blocks.setdefault((i["coin"], i["t"] // (7 * 86400)), []).append(i)
    B = list(blocks.values()); rnd2 = random.Random(0); wins = 0
    for _ in range(10000):
        s = [i for b in rnd2.choices(B, k=len(B)) for i in b]
        f = lambda g: sum((g(i) - i["up"]) ** 2 for i in s) / len(s)
        wins += f(lambda i: i["p"]) < min(f(lambda i: 0.5), f(lambda i: base), f(lambda i: i["mom"]))
    P = wins / 10000; useful = b_op < best - 0.005 and P > 0.9
    ps_ok = [i["p"] for i in ok]
    line = (f"n={len(ok)}/300 | Brier Opus {b_op:.4f} | p=0,5 {b_05:.4f} | taux de base ({base:.3f}) {b_base:.4f} | momentum {b_mom:.4f} | "
            f"P(Opus meilleur) {P:.3f} | p moyen {sum(ps_ok)/len(ps_ok):.3f}, min {min(ps_ok):.2f}, max {max(ps_ok):.2f} → "
            + ("JUGEMENT UTILE" if useful else "PAS D'AVANTAGE DIRECTIONNEL À 24 H"))
    print(line); open("RESULTATS.md", "w").write("# Laboratoire du cutoff : résultat\n\n" + line + "\n")


if __name__ == "__main__":
    main()
