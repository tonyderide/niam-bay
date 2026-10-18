"""Test de Turing inversé (protocole : PREREGISTRATION.md, commit f92b038). Sans LLM, stdlib seule."""
import json, os, random, time, urllib.request, collections

ACCOUNTS = ["0x6f0306dc529cfeb8e08502e5eb7a588def9ac88d", "0x8d0c44cd9493ea7954fafd8b4e7cacf3b91ae17b",
            "0x79b1709cd32839cadc63bf6f17b37ac19faeda9d", "0xa0d149c9e3fee0a9f920058c4139c73894c2be98", "0x1457978fb96b0190c8ea7d168d0155d77bd6ce57"]
HERE = os.path.dirname(os.path.abspath(__file__))


def info(b):
    r = urllib.request.Request("https://api.hyperliquid.xyz/info", data=json.dumps(b).encode(), headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(r, timeout=30))


def history(addr, max_fills=10000, max_days=60):
    """Amendement n°1 : on pagine vers le passé avec userFillsByTime."""
    end = int(time.time() * 1000); start_floor = end - max_days * 86400000; out = {}
    while len(out) < max_fills:
        page = info({"type": "userFillsByTime", "user": addr, "startTime": start_floor, "endTime": end}); time.sleep(2)
        if not page:
            break
        for x in page:
            out[(x["tid"], x["oid"], x["time"])] = x
        oldest = min(x["time"] for x in page)
        if len(page) < 2000 or oldest <= start_floor:
            break
        end = oldest - 1
    return list(out.values())


def dataset(addr):
    f = history(addr)
    coin = collections.Counter(x["coin"] for x in f if not x["coin"].startswith(("@", "xyz:"))).most_common(1)[0][0]
    f = [x for x in f if x["coin"] == coin]
    t0 = min(x["time"] for x in f) // 3600000 * 3600000; t1 = max(x["time"] for x in f) // 3600000 * 3600000
    c = info({"type": "candleSnapshot", "req": {"coin": coin, "interval": "1h", "startTime": t0 - 30 * 3600000, "endTime": t1 + 3600000}}); time.sleep(2)
    C = {int(k["t"]): k for k in c}; hrs = sorted(C)
    opens = {x["time"] // 3600000 * 3600000 for x in f if x["dir"].startswith("Open") or ">" in x["dir"]}
    rows = []
    for i, h in enumerate(hrs):
        if h < t0 or h > t1 or i < 25:
            continue
        cl = lambda j: float(C[hrs[j]]["c"])
        X = {"r1": cl(i - 1) / cl(i - 2) - 1, "r6": cl(i - 1) / cl(i - 7) - 1, "r24": cl(i - 1) / cl(i - 25) - 1,
             "dd24": cl(i - 1) / max(float(C[hrs[j]]["h"]) for j in range(i - 24, i)) - 1,
             "hour": time.gmtime(h / 1000).tm_hour, "prev": int(hrs[i - 1] in opens)}
        rows.append((X, int(h in opens)))
    return coin, rows


def brier(ps, ys):
    return sum((p - y) ** 2 for p, y in zip(ps, ys)) / len(ys)


def fit_tree(train, depth=2, minleaf=10):
    ys = [y for _, y in train]; base = sum(ys) / len(ys)
    if depth == 0 or len(train) < 2 * minleaf:
        return ("leaf", base)
    best = None
    for k in train[0][0]:
        vals = sorted({x[k] for x, _ in train})
        cands = vals if len(vals) <= 24 else [vals[int(len(vals) * q / 20)] for q in range(1, 20)]
        for t in cands:
            L = [r for r in train if r[0][k] <= t]; R = [r for r in train if r[0][k] > t]
            if len(L) < minleaf or len(R) < minleaf:
                continue
            pl = sum(y for _, y in L) / len(L); pr = sum(y for _, y in R) / len(R)
            sse = sum((pl - y) ** 2 for _, y in L) + sum((pr - y) ** 2 for _, y in R)
            if best is None or sse < best[0]:
                best = (sse, k, t, L, R)
    if best is None:
        return ("leaf", base)
    _, k, t, L, R = best
    return ("split", k, t, fit_tree(L, depth - 1, minleaf), fit_tree(R, depth - 1, minleaf))


def predict(tree, x):
    while tree[0] == "split":
        tree = tree[3] if x[tree[1]] <= tree[2] else tree[4]
    return tree[1]


def show(tree, ind=""):
    if tree[0] == "leaf":
        return f"{ind}p={tree[1]:.3f}\n"
    return f"{ind}si {tree[1]} ≤ {tree[2]:.4g} :\n" + show(tree[3], ind + "  ") + f"{ind}sinon :\n" + show(tree[4], ind + "  ")


def evaluate(rows):
    n = int(len(rows) * 0.7); tr, te = rows[:n], rows[n:]
    yt = [y for _, y in te]
    base = sum(y for _, y in tr) / len(tr)
    after = {v: (sum(y for x, y in tr if x["prev"] == v) / max(1, sum(1 for x, _ in tr if x["prev"] == v))) for v in (0, 1)}
    tree = fit_tree(tr)
    pt = [predict(tree, x) for x, _ in te]; pb = [base] * len(te); pp = [after[x["prev"]] for x, _ in te]
    bt, bb, bp = brier(pt, yt), brier(pb, yt), brier(pp, yt)
    ref = min(bb, bp); skill = 1 - bt / ref if ref > 0 else 0
    rnd = random.Random(0); wins = 0; blocks = [list(range(i, min(i + 24, len(te)))) for i in range(0, len(te), 24)]
    for _ in range(2000):
        idx = [j for b in rnd.choices(blocks, k=len(blocks)) for j in b]
        r2 = min(brier([pb[j] for j in idx], [yt[j] for j in idx]), brier([pp[j] for j in idx], [yt[j] for j in idx]))
        wins += r2 > 0 and (1 - brier([pt[j] for j in idx], [yt[j] for j in idx]) / r2) > 0
    return dict(train_h=len(tr), test_h=len(te), test_opens=sum(yt), brier_tree=round(bt, 4), brier_base=round(bb, 4), brier_prev=round(bp, 4),
                skill=round(skill, 3), p_skill_pos=round(wins / 2000, 3), tree=show(tree))


if __name__ == "__main__":
    out = {}
    for a in ACCOUNTS:
        coin, rows = dataset(a)
        r = evaluate(rows); r["coin"] = coin
        r["verdict"] = ("indécidable (<10 heures d'ouverture dans le test)" if r["test_opens"] < 10 else
                        "MÉCANIQUE" if r["skill"] > 0.10 and r["p_skill_pos"] > 0.9 else "pas mécanique")
        out[a] = r
        print(f"\n{a[:10]} {coin} : {r['verdict']} | skill {r['skill']} (P>0 {r['p_skill_pos']}) | test {r['test_h']} h dont {r['test_opens']} avec ouverture | Brier arbre {r['brier_tree']} base {r['brier_base']} préc {r['brier_prev']}")
        print(r["tree"])
    json.dump(out, open(os.path.join(HERE, "resultats.json"), "w"), indent=1, ensure_ascii=False)
