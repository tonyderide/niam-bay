"""Test papier du candidat DOT (PREREGISTRATION.md). Cron horaire sur la VM, lecture seule (API charts Kraken Futures)."""
import json, os, time, urllib.request
os.environ["TZ"] = "Europe/Paris"; time.tzset()
HERE = os.path.dirname(os.path.abspath(__file__)); LOG = os.path.join(HERE, "paper.jsonl"); ST = os.path.join(HERE, "state.json")
H = 3600; FEE = 0.001


def closes():
    now = int(time.time()) // H * H
    d = json.load(urllib.request.urlopen(f"https://futures.kraken.com/api/charts/v1/mark/PF_DOTUSD/1h?from={now - 200 * H}&to={now}", timeout=30))["candles"]
    return [(c["time"] // 1000, float(c["close"])) for c in d]


def main():
    c = closes(); t, px = c[-1]
    e = c[0][1]
    for _, x in c: e = e + (x - e) * 2 / 21
    st = json.load(open(ST)) if os.path.exists(ST) else {"open": None}
    o = st["open"]
    if o:
        r = px / o["px"] - 1
        why = "TP" if r >= 0.02 else "SL" if r <= -0.02 else "24h" if t - o["t"] >= 24 * H else None
        if why:
            res = (0.02 if why == "TP" else -0.02 if why == "SL" else r) - FEE
            open(LOG, "a").write(json.dumps({**o, "exit_t": t, "exit_px": px, "why": why, "net": round(res, 5)}) + "\n")
            st["open"] = None
    elif px / e - 1 <= -0.04:
        st["open"] = {"t": t, "px": px, "ema20": round(e, 5), "dev": round(px / e - 1, 4)}
    json.dump(st, open(ST, "w"))


if __name__ == "__main__":
    main()
