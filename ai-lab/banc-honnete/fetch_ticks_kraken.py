"""Transactions BTC/USD au comptant Kraken (API publique Trades) entre deux dates, en JSONL, reprise possible."""
import json, os, sys, time, urllib.request
pair, a, b, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
since = a * 10**9
if os.path.exists(out) and os.path.getsize(out):
    with open(out, "rb") as f:
        f.seek(-400, 2); since = int(json.loads(f.read().splitlines()[-1])["timestamp"] * 10**9) + 1
with open(out, "a") as f:
    while True:
        for k in range(10):
            try:
                d = json.load(urllib.request.urlopen(f"https://api.kraken.com/0/public/Trades?pair={pair}&since={since}&count=1000", timeout=30)); break
            except Exception: time.sleep(5 * (k + 1))
        if d.get("error"): print(d["error"], flush=True); time.sleep(10); continue
        r = d["result"]; tr = next(v for k_, v in r.items() if k_ != "last")
        for p, v, t, s, ty, *_ in tr:
            if float(t) >= b: print("fini", flush=True); sys.exit(0)
            f.write(json.dumps({"price": float(p), "volume": float(v), "timestamp": float(t), "side": s, "type": ty}) + "\n")
        f.flush(); nxt = int(r["last"])
        if nxt == since or not tr: time.sleep(5); continue
        since = nxt; time.sleep(1.0)
