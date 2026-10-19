#!/usr/bin/env python3
"""Instantané de l'état de NB -> injecté dans pipes.html (« Les tuyaux de NB »).

Lecture seule partout : fichiers locaux, git log, systemctl is-active, et une
unique commande SSH ponctuelle vers la VM (aucun processus lancé là-bas).
Aucun secret ne doit sortir : tout le JSON passe par un filtre (jetons Telegram,
longues chaînes hexadécimales, longues chaînes opaques). Le texte des messages
de Tony n'est jamais lu côté VM : on ne garde que « message de Tony » + l'heure.

Usage (depuis la racine du dépôt) : python3 scripts/vitrine/build_status.py
"""
import base64
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
TEMPLATE = os.path.join(HERE, "pipes.template.html")
OUT = os.path.join(HERE, "pipes.html")
MARKER = "/*__STATUS__*/"
PARIS = ZoneInfo("Europe/Paris")
SSH = ["ssh", "-i", os.path.expanduser("~/.ssh/martin_vm.key"), "-o", "BatchMode=yes",
       "-o", "ConnectTimeout=10", "ubuntu@141.253.108.141"]

NOW = time.time()
H24, H48 = 86400, 172800

# --------------------------------------------------------------------------
# Script exécuté sur la VM (lecture seule, une seule fois, puis il se termine).
# --------------------------------------------------------------------------
REMOTE = r'''
import json, os, glob, subprocess, time
H = os.path.expanduser("~/nb")
def jl(p, n=None):
    out = []
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    except Exception:
        return None
    return out[-n:] if n else out
def js(p):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None
def mt(p):
    try:
        return os.stat(p).st_mtime
    except Exception:
        return None
def sh(c):
    try:
        return subprocess.run(c, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              stdin=subprocess.DEVNULL, universal_newlines=True, timeout=10).stdout
    except Exception:
        return ""
def count(p):
    n = 0
    try:
        with open(p, "rb") as f:
            for _ in f:
                n += 1
    except Exception:
        return None
    return n
R = {"now": time.time()}
# Messages de Tony : AUCUN texte conservé.
ib = jl(H + "/inbox.jsonl", 40) or []
R["inbox"] = [{"from": m.get("from"), "utc": m.get("utc"), "ts": m.get("ts"), "status": m.get("status")} for m in ib]
R["answered"] = [a.get("ts") for a in (jl(H + "/answered.jsonl", 80) or [])]
R["receipts"] = [{"n": r.get("n"), "cmd": r.get("cmd"), "t": r.get("t")} for r in (jl(H + "/receipts.jsonl", 40) or [])]
R["annonces_queue"] = jl(H + "/annonces_queue.jsonl", 12) or []
R["annonces"] = jl(H + "/annonces.jsonl", 12)
P = js(H + "/calibration/predictions.json") or []
R["predictions"] = [{"id": p.get("id"), "claim": p.get("claim"), "p": p.get("p"), "outcome": p.get("outcome"),
                     "resolve_at": p.get("resolve_at")} for p in P]
R["calib_mtime"] = mt(H + "/calibration/calibration.md")
R["duel_current"] = js(H + "/duel/current.json")
R["duel_history"] = jl(H + "/duel/history.jsonl", 12) or []
R["twin"] = [{"H": t.get("H"), "utc": t.get("utc"), "p_twin": t.get("p_twin"), "p_base": t.get("p_base"),
              "outcome": t.get("outcome")} for t in (jl(H + "/jumeau/test_log.jsonl", 30) or [])]
tr = {}
for f in sorted(glob.glob(H + "/suiveurs/trades-*.jsonl")):
    tr[os.path.basename(f)] = {"lines": count(f), "mtime": mt(f)}
R["trades"] = tr
R["papier_state"] = js(H + "/papier-dot/state.json")
R["papier_state_mtime"] = mt(H + "/papier-dot/state.json")
pj = jl(H + "/papier-dot/paper.jsonl")
R["papier_lines"] = None if pj is None else len(pj)
R["papier_mtime"] = mt(H + "/papier-dot/paper.jsonl")
R["digest_state"] = js(H + "/digest_state.json")
R["digest_mtime"] = max([m for m in (mt(H + "/digest_state.json"), mt(H + "/digest.log")) if m] or [0]) or None
R["botlog_mtime"] = mt(H + "/bot.log")
R["sync_mtime"] = max([m for m in (mt(H + "/loop-journal.md"), mt(H + "/deliberations.jsonl"),
                                   mt(H + "/memoire-verif.md")) if m] or [0]) or None
R["crontab"] = sh("crontab -l")
R["procs"] = sh("pgrep -fa '[n]b_vm_bot|[s]uiveurs/collector'")
R["et_tail"] = sh("tail -n 12 ~/et/et.log")
R["et_mtime"] = mt(os.path.expanduser("~/et/et.log"))
print(json.dumps(R))
'''

# --------------------------------------------------------------------------
# Filtre anti-secrets
# --------------------------------------------------------------------------
RE_TOKEN = re.compile(r"\d{8,}:[A-Za-z0-9_-]{30,}")
RE_HEX = re.compile(r"\b[0-9a-fA-F]{32,}\b")
RE_OPAQUE = re.compile(r"\b(?=[A-Za-z0-9_+/=-]*\d)(?=[A-Za-z0-9_+/=-]*[A-Za-z])[A-Za-z0-9_+/=-]{40,}\b")


def scrub_str(s):
    s = RE_TOKEN.sub("[masqué]", s)
    s = RE_HEX.sub("[masqué]", s)
    return RE_OPAQUE.sub("[masqué]", s)


def scrub(o):
    if isinstance(o, str):
        return scrub_str(o)
    if isinstance(o, list):
        return [scrub(x) for x in o]
    if isinstance(o, dict):
        return {scrub_str(str(k)): scrub(v) for k, v in o.items()}
    return o


# --------------------------------------------------------------------------
# Utilitaires
# --------------------------------------------------------------------------
def run(cmd, timeout=20, **kw):
    try:
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                           universal_newlines=True, timeout=timeout, **kw)
        return r.returncode, r.stdout
    except Exception as e:  # noqa
        return 1, str(e)


def read_lines(path, n=None):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            L = f.read().splitlines()
        return L[-n:] if n else L
    except Exception:
        return []


def read_jsonl(path):
    out = []
    for line in read_lines(path):
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out


def paris(ts):
    return datetime.fromtimestamp(ts, PARIS)


def when(ts):
    return paris(ts).strftime("%d/%m %H:%M")


def parse_paris(s):
    """'2026-10-19T08:00' ou '2026-10-19 01:57:20' en heure de Paris -> epoch."""
    s = s.replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=PARIS).timestamp()
        except ValueError:
            pass
    return None


def parse_utc(s):
    s = s.replace("T", " ").replace("Z", "")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc).timestamp()
        except ValueError:
            pass
    return None


def cut(s, n):
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def fnum(x, nd=2):
    return f"{x:.{nd}f}".replace(".", ",")


EVENTS = []  # tous les événements (y compris « mineurs » : servent aux tuyaux et nœuds)


def ev(ts, kind, text, pipes, nodes, minor=False):
    if ts is None or ts > NOW + 120:
        return
    EVENTS.append({"ts": float(ts), "when": when(ts), "kind": kind, "text": text, "pipes": pipes,
                   "nodes": nodes, "minor": minor})


# --------------------------------------------------------------------------
# Collecte
# --------------------------------------------------------------------------
def collect_vm():
    b64 = base64.b64encode(REMOTE.encode()).decode()
    rc, out = run(SSH + [f"echo {b64} | base64 -d | python3 -"], timeout=60)
    if rc != 0:
        return None, f"VM injoignable ou erreur ({cut(out, 120)})"
    try:
        return json.loads(out[out.index("{"):]), None
    except Exception as e:
        return None, f"réponse VM illisible ({e})"


def main():
    vm, vm_err = collect_vm()
    alerts = []
    services = []
    account = None

    # ---------- PC : services ----------
    rc, out = run(["systemctl", "--user", "is-active", "nb-telegram"])
    relay_ok = out.strip() == "active"
    services.append({"id": "relay", "label": "Relais Telegram (PC)", "ok": relay_ok, "detail": out.strip() or "?"})
    rc, cron = run(["crontab", "-l"])
    verify_cron = "verify.py" in cron
    services.append({"id": "verify", "label": "Vérif. mémoire 06h07 (PC)", "ok": verify_cron,
                     "detail": "planifiée" if verify_cron else "absente du cron"})

    # ---------- PC : git ----------
    rc, out = run(["git", "-C", REPO, "log", "--since=48 hours ago", "--format=%h|%ci|%s"])
    for line in out.splitlines():
        p = line.split("|", 2)
        if len(p) != 3:
            continue
        try:
            ts = datetime.strptime(p[1], "%Y-%m-%d %H:%M:%S %z").timestamp()
        except ValueError:
            continue
        ev(ts, "commit", f"Commit {p[0]} : {cut(p[2], 110)}", ["build_git"],
           {"git": f"{p[0]} {cut(p[2], 40)}", "build": f"a livré « {cut(p[2], 34)} »"})

    # ---------- PC : journal (HH:MM, sans date -> on remonte le temps) ----------
    entries = []
    for line in read_lines(os.path.join(REPO, "docs", "loop-journal.md"), 40):
        m = re.match(r"^- (\d{1,2}):(\d{2})\s+(.*)$", line)
        if m:
            entries.append((int(m.group(1)), int(m.group(2)), m.group(3)))
    day = paris(NOW).date()
    prev_minutes = None
    dated = []
    for h, mi, txt in reversed(entries):
        minutes = h * 60 + mi
        if prev_minutes is None:
            if minutes > paris(NOW).hour * 60 + paris(NOW).minute:
                day = day.fromordinal(day.toordinal() - 1)
        elif minutes > prev_minutes:
            day = day.fromordinal(day.toordinal() - 1)
        prev_minutes = minutes
        dated.append((datetime(day.year, day.month, day.day, h, mi, tzinfo=PARIS).timestamp(), txt))
    for ts, txt in dated:
        is_council = txt.lower().startswith("conseil")
        ev(ts, "journal", cut(txt, 160), ["loop_conseil"] if is_council else ["conseil_build"],
           {"loop": cut(txt, 52), **({} if is_council else {"build": cut(txt, 52)})}, minor=is_council)

    # ---------- PC : conseil ----------
    for d in read_jsonl(os.path.join(REPO, "ai-lab", "conseil", "deliberations.jsonl")):
        ts = parse_utc(d.get("utc", ""))
        if ts is None:
            continue
        v, sc, idea = d.get("verdict", "?"), d.get("score", "?"), d.get("idea", "")
        ev(ts, "conseil", f"Conseil intérieur : {v} ({sc}) — {cut(idea, 110)}", ["loop_conseil"],
           {"conseil": f"{v} ({sc}) {cut(idea, 36)}"})

    # ---------- PC : mémoire falsifiable ----------
    memo = {"ok": None, "total": None, "line": None}
    mp = os.path.join(REPO, "docs", "memoire-verif.md")
    ml = read_lines(mp)
    if len(ml) >= 3:
        line = ml[2].replace("**", "")
        memo["line"] = line
        m = re.search(r"(\d+)/(\d+)", line)
        if m:
            memo["ok"], memo["total"] = int(m.group(1)), int(m.group(2))
        try:
            mts = os.stat(mp).st_mtime
            ev(mts, "memoire", f"Mémoire vérifiée : {cut(line, 100)}", ["mem_loop"], {"mem": cut(line, 50)})
        except OSError:
            pass

    # ---------- PC : quota ----------
    quota = None
    try:
        sl = json.load(open("/tmp/statusline-last.json", encoding="utf-8"))
        rl = sl.get("rate_limits") or {}
        quota = {"five_hour": rl.get("five_hour"), "seven_day": rl.get("seven_day"),
                 "mtime": os.stat("/tmp/statusline-last.json").st_mtime}
    except Exception:
        pass

    # ---------- VM ----------
    vm_summary = {"reachable": vm is not None, "error": vm_err}
    if vm is None:
        alerts.append(vm_err or "VM injoignable")
        services.append({"id": "vm", "label": "VM Oracle (SSH)", "ok": False, "detail": vm_err or "injoignable"})
    else:
        services.append({"id": "vm", "label": "VM Oracle (SSH)", "ok": True, "detail": "joignable"})
        procs = vm.get("procs") or ""
        bot_ok = "nb_vm_bot" in procs
        ws_ok = "collector" in procs
        services.append({"id": "bot", "label": "Bot Telegram (VM)", "ok": bot_ok, "detail": "actif" if bot_ok else "arrêté"})
        services.append({"id": "ws", "label": "Enregistreur de trades (VM)", "ok": ws_ok,
                         "detail": "actif" if ws_ok else "arrêté"})
        ct = vm.get("crontab") or ""
        need = ["resolve.py", "duel.py", "twin.py", "paper_dot.py", "morning_digest.py", "et/run.sh"]
        missing = [n for n in need if n not in ct]
        services.append({"id": "crons", "label": "Juges planifiés (VM)", "ok": not missing,
                         "detail": "tous planifiés" if not missing else "manque : " + ", ".join(missing)})
        vm_summary.update({"bot_ok": bot_ok, "ws_ok": ws_ok})

        # messages de Tony (sans texte)
        answered = set(vm.get("answered") or [])
        for m in vm.get("inbox") or []:
            if m.get("from") != "tony" or not m.get("ts"):
                continue
            done = m["ts"] in answered
            pipes = ["tony_bot", "bot_inbox"] + (["inbox_relay", "relay_reply", "reply_tony"] if done else [])
            nodes = {"tony": "a écrit au bot", "bot": "message reçu", "inbox": "rangé · " + ("traité" if done else "à traiter")}
            if done:
                nodes.update({"relay": "message traité", "reply": "réponse + reçu envoyés"})
            ev(m["ts"], "message", "Message de Tony" + (" (traité)" if done else " (pas encore traité)"), pipes, nodes)
            if not done and NOW - m["ts"] > 900:
                alerts.append("Un message de Tony attend une réponse depuis plus de 15 min.")

        for r in vm.get("receipts") or []:
            ts = parse_paris(r.get("t") or "")
            ev(ts, "commande", f"Commande instantanée /{r.get('cmd')} (reçu n°{r.get('n')})", ["tony_bot", "bot_tony"],
               {"bot": f"/{r.get('cmd')} répondu", "tony": f"a demandé /{r.get('cmd')}"})

        for a in (vm.get("annonces") or []) + (vm.get("annonces_queue") or []):
            ts = a.get("t")
            ev(ts, "annonce", "Annonce préparée : " + cut(a.get("text", ""), 120), ["annonces_bot", "bot_tony"],
               {"annonces": cut(a.get("text", ""), 46), "bot": "annonce à envoyer"})

        # calibration
        preds = vm.get("predictions") or []
        open_n = sum(1 for p in preds if p.get("outcome") is None)
        done_n = len(preds) - open_n
        for p in preds:
            if p.get("outcome") is not None:
                ts = parse_paris(p.get("resolve_at") or "")
                mark = "✓" if p["outcome"] else "✗"
                if ts and NOW - ts < H48:
                    ev(ts, "pari", f"Pari tranché {mark} : {cut(p.get('claim'), 100)}", ["calib_store"],
                       {"calib": f"tranché {mark} · {cut(p.get('claim'), 30)}"})
        ev(vm.get("calib_mtime"), "pari", "Calibration revérifiée", ["calib_store"],
           {"calib": f"{open_n} paris ouverts, {done_n} tranchés"}, minor=True)

        # duel
        dc = vm.get("duel_current")
        if dc and dc.get("made"):
            ev(dc["made"], "duel", "Duel : nouvelle question — " + cut(dc.get("q"), 100), ["duel_store"],
               {"duel": "question : " + cut(dc.get("q"), 40)})
        for d in vm.get("duel_history") or []:
            if d.get("outcome") is not None and d.get("resolve_at"):
                ev(d["resolve_at"], "duel", f"Duel tranché ({'oui' if d['outcome'] else 'non'}) : {cut(d.get('q'), 90)}",
                   ["duel_store"], {"duel": "tranché : " + cut(d.get("q"), 34)})

        # jumeau
        for t in vm.get("twin") or []:
            if t.get("H"):
                pt = t.get("p_twin")
                txt = f"jumeau {fnum(pt * 100, 1)} % (base {fnum((t.get('p_base') or 0) * 100, 1)} %)" if pt is not None else "mesure"
                ev(t["H"] / 1000 + 120, "jumeau", "Jumeau : " + txt, ["twin_store"], {"twin": txt}, minor=True)

        # papier DOT
        ps = vm.get("papier_state") or {}
        ptxt = "aucun pari ouvert" if not ps.get("open") else "un pari ouvert"
        if vm.get("papier_lines"):
            ptxt += f" · {vm['papier_lines']} paris au total"
        ev(vm.get("papier_state_mtime"), "papier", "Papier DOT : " + ptxt, ["papier_store"], {"papier": ptxt}, minor=True)

        # enregistreur
        trades = vm.get("trades") or {}
        if trades:
            last = max(trades.items(), key=lambda kv: kv[1].get("mtime") or 0)
            total = sum((v.get("lines") or 0) for v in trades.values())
            ev(last[1].get("mtime"), "trades", "Trades BTC enregistrés", ["ws_store"],
               {"ws": f"{last[1].get('lines', 0):,} trades aujourd'hui".replace(",", " ")}, minor=True)
            vm_summary["trades_total"] = total

        # résumé du matin
        if vm.get("digest_mtime"):
            ev(vm["digest_mtime"], "digest", "Résumé du matin préparé", ["digest_bot", "bot_tony"],
               {"digest": "résumé du matin envoyé", "bot": "résumé du matin"})

        # synchro PC -> VM
        ev(vm.get("sync_mtime"), "sync", "Synchro PC → VM (journal, conseil, mémoire)", ["git_sync", "sync_store"],
           {"sync": "PC → VM", "store": "carnets à jour"}, minor=True)

        # Exchange-truth / compte
        tail = vm.get("et_tail") or ""
        tl = tail.splitlines()
        et_ts = None
        pos_txt = None
        for ln in reversed(tl):
            m = re.match(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)\s+(\d+) positions?, (\d+) open orders?, (\d+) findings?", ln)
            if m:
                et_ts = parse_utc(m.group(1))
                pos_txt = f"{m.group(2)} positions, {m.group(3)} ordres ouverts"
                break
        eq = wc = mt_ = None
        for ln in tl:
            m = re.search(r"equity ([\d.]+) vs maintenance ([\d.]+)", ln)
            if m:
                eq, mt_ = float(m.group(1)), float(m.group(2))
            m = re.search(r"worst case if all stops hit: (-?[\d.]+)", ln)
            if m:
                wc = float(m.group(1))
        if et_ts:
            ev(et_ts, "compte", "Relevé du compte Kraken : " + pos_txt, ["et_kraken"],
               {"et": "relevé du compte", "kraken": pos_txt}, minor=True)
            fresh = NOW - et_ts < 300
            services.append({"id": "et", "label": "Exchange-truth (VM)", "ok": fresh,
                             "detail": "relevé frais" if fresh else "relevé ancien"})
        else:
            services.append({"id": "et", "label": "Exchange-truth (VM)", "ok": False, "detail": "pas de relevé"})
        if eq is not None:
            account = {"equity_after_stops": eq, "maintenance": mt_, "worst_case": wc,
                       "equity_now": round(eq - wc, 3) if wc is not None else None,
                       "positions": pos_txt, "ts": et_ts,
                       "warn": any("THIN_MARGIN" in ln for ln in tl)}
            if account["warn"]:
                alerts.append(f"Marge fine : si les stops sautent, il reste {fnum(eq)} $ pour {fnum(mt_)} $ exigés.")

    # ---------- agrégats ----------
    EVENTS.sort(key=lambda e: -e["ts"])
    nodes_last, pipes_last = {}, {}
    for e in EVENTS:  # du plus récent au plus ancien
        for n, txt in e["nodes"].items():
            if n not in nodes_last:
                nodes_last[n] = {"ts": e["ts"], "text": txt}
        for p in e["pipes"]:
            if p not in pipes_last:
                pipes_last[p] = e["ts"]
    timeline = [{k: e[k] for k in ("ts", "when", "kind", "text", "pipes")}
                for e in EVENTS if not e["minor"] and NOW - e["ts"] < H48]
    node_state = {"relay": relay_ok}
    if vm is not None:
        node_state.update({"bot": vm_summary.get("bot_ok"), "ws": vm_summary.get("ws_ok")})
    ets = [s for s in services if s["id"] == "et"]
    if ets:
        node_state["et"] = ets[0]["ok"]

    status = {
        "generated_ts": NOW,
        "generated_paris": paris(NOW).strftime("%d/%m/%Y %H:%M"),
        "account": account,
        "quota": quota,
        "memory": memo,
        "services": services,
        "alerts": alerts,
        "nodes_last": nodes_last,
        "node_state": node_state,
        "pipes_last": pipes_last,
        "events": timeline,
        "vm": vm_summary,
    }
    status = scrub(status)
    js = json.dumps(status, ensure_ascii=False, separators=(",", ":"))
    js = js.replace("<", "\\u003c").replace(">", "\\u003e").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")

    with open(TEMPLATE, encoding="utf-8") as f:
        tpl = f.read()
    if MARKER not in tpl:
        sys.exit("marqueur " + MARKER + " absent du gabarit")
    html = tpl.replace(MARKER, "window.NB_STATUS = " + js + ";")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"ok : {OUT} ({len(html)//1024} Ko, {len(timeline)} événements, {len(nodes_last)} nœuds renseignés)"
          + (f" — attention : {vm_err}" if vm_err else ""))


if __name__ == "__main__":
    main()
