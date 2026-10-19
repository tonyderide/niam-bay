#!/usr/bin/env python3
"""Le réveilleur de l'agence (côté PC). Stdlib seulement.

Rôle : relier le « guetteur » (VM, sans IA) à l'agence Martin (PC, forfait Claude de Tony).
Toutes les 5 minutes (timer systemd utilisateur nb-agence-reveilleur.timer) :

  1. lit par ssh, sur la VM, ~/nb/agence/reveils.jsonl et ~/nb/agence/traites.jsonl ;
  2. retient les réveils `traite:false` qui ne sont PAS dans traites.jsonl ;
  3. pour chacun (danger d'abord), lance `python -m martin_agency.wake --type .. --raison ..`
     dans le venv du backend, timeout 20 min ;
  4. marque le réveil traité en AJOUTANT une ligne à ~/nb/agence/traites.jsonl sur la VM.

CONVENTION « TRAITÉ » (à respecter par le guetteur et par tout lecteur) :
  reveils.jsonl n'est JAMAIS réécrit par le réveilleur (le guetteur y ajoute en concurrence).
  Un réveil est traité s'il y a une ligne {"t": <même t>, "type": <même type>} dans
  traites.jsonl, quelle que soit la valeur de son champ "traite". Le réveilleur ajoute aussi
  "ts" (UTC), "statut" (ok | echec | timeout | vide | expire) et "rapport"/"code".
  Clé d'identité d'un réveil = (t, type).

Garde-fous :
  - au plus MAX_PAR_JOUR (3) réveils traités par jour (compteur local, jour local) ; les
    suivants restent en attente (ils expirent après EXPIRE_H heures, marqués « expire ») ;
  - le budget journalier de tokens de l'agence est vérifié avant chaque lancement (même
    fichier token_budget.json que economy.py) et wake.py le revérifie (code 3) ;
  - un seul réveilleur à la fois (flock) ; aucun process n'est lancé sur la VM, ssh < /dev/null.

Usage :
  reveilleur.py            # tourne pour de bon
  reveilleur.py --dry-run  # lit la VM, affiche ce qui serait lancé, n'écrit rien nulle part
"""
import argparse
import fcntl
import json
import os
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone

VM = os.environ.get("NB_VM", "ubuntu@141.253.108.141")
KEY = os.path.expanduser(os.environ.get("NB_VM_KEY", "~/.ssh/martin_vm.key"))
REMOTE_DIR = "~/nb/agence"
BACKEND = os.path.expanduser(os.environ.get(
    "AGENCE_BACKEND", "~/projets/tonyderide/martin-agency/backend"))
PYTHON = os.path.join(BACKEND, ".venv/bin/python")
STATE_DIR = os.path.expanduser("~/.local/state/nb-agence")
STATE = os.path.join(STATE_DIR, "reveilleur.json")
LOCK = os.path.join(STATE_DIR, "reveilleur.lock")

MAX_PAR_JOUR = 3
TIMEOUT_S = 20 * 60
EXPIRE_H = 24
TYPES = ("danger", "verdict", "marche", "dimanche", "tony")  # = ordre de priorité
SEP = "---TRAITES---"


def log(*a):
    print(time.strftime("%F %H:%M:%S"), *a, flush=True)


def ssh(cmd, timeout=60):
    """ssh non interactif ; stdin = /dev/null ; commande courte, rien en arrière-plan."""
    return subprocess.run(
        ["ssh", "-i", KEY, "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
         "-o", "ServerAliveInterval=10", VM, cmd],
        stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout)


def parse_jsonl(text):
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            if isinstance(d, dict):
                out.append(d)
        except ValueError:
            pass  # ligne partielle en cours d'écriture par le guetteur
    return out


def fetch():
    r = ssh(f"cat {REMOTE_DIR}/reveils.jsonl 2>/dev/null; echo {SEP}; "
            f"cat {REMOTE_DIR}/traites.jsonl 2>/dev/null; true")
    if r.returncode != 0:
        raise RuntimeError(f"ssh a échoué ({r.returncode}): {r.stderr.strip()[:200]}")
    reveils, _, traites = r.stdout.partition(SEP)
    return parse_jsonl(reveils), parse_jsonl(traites)


def pending(reveils, traites):
    done = {(d.get("t"), d.get("type")) for d in traites}
    seen, out = set(), []
    for d in reveils:
        k = (d.get("t"), d.get("type"))
        if d.get("traite") is False and k not in done and k not in seen and d.get("type") in TYPES:
            seen.add(k)
            out.append(d)
    out.sort(key=lambda d: (TYPES.index(d["type"]), d.get("t", "")))
    return out


def age_h(t):
    try:  # le guetteur écrit l'heure de Paris ; le PC est en heure locale (même fuseau)
        return (time.time() - time.mktime(time.strptime(t, "%Y-%m-%d %H:%M"))) / 3600
    except Exception:
        return 0.0


def mark(d, statut, **extra):
    line = {"t": d["t"], "type": d["type"], "ts": datetime.now(timezone.utc).strftime("%F %T"),
            "statut": statut, **extra}
    r = ssh(f"printf '%s\\n' {shlex.quote(json.dumps(line, ensure_ascii=False))} "
            f">> {REMOTE_DIR}/traites.jsonl")  # un append d'une ligne : pas de réécriture
    if r.returncode != 0:
        raise RuntimeError(f"marquage échoué: {r.stderr.strip()[:200]}")


def load_state():
    try:
        return json.load(open(STATE))
    except Exception:
        return {}


def save_state(st):
    os.makedirs(STATE_DIR, exist_ok=True)
    tmp = STATE + ".tmp"
    json.dump(st, open(tmp, "w"))
    os.replace(tmp, STATE)


def budget_restant():
    """None = illimité. Reproduit economy.daily_budget/tokens_used_today (stdlib)."""
    raw = os.environ.get("AGENCE_DAILY_TOKEN_BUDGET", os.environ.get("AGENCY_DAILY_TOKEN_BUDGET", "1500000"))
    try:
        b = int(raw)
    except ValueError:
        b = 1500000
    if b <= 0:
        return None
    try:
        data = json.load(open(os.path.join(BACKEND, "data", "token_budget.json")))
        used = int(data.get(datetime.now(timezone.utc).strftime("%Y-%m-%d"), 0))
    except Exception:
        used = 0
    return max(0, b - used)


def lancer_wake(d):
    cmd = [PYTHON, "-m", "martin_agency.wake", "--type", d["type"], "--raison", str(d.get("raison", ""))]
    env = dict(os.environ, AGENCY_MODE="research_only", AGENCY_SCHEDULER="off")
    try:
        p = subprocess.run(cmd, cwd=BACKEND, env=env, stdin=subprocess.DEVNULL,
                           capture_output=True, text=True, timeout=TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return "timeout", None, ""
    return ("ok" if p.returncode == 0 else "vide" if p.returncode == 4 else "budget" if p.returncode == 3
            else "echec"), p.returncode, (p.stdout + p.stderr)[-1500:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="lit la VM, n'écrit ni ne lance rien")
    args = ap.parse_args()
    os.makedirs(STATE_DIR, exist_ok=True)
    lock = open(LOCK, "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        log("un autre réveilleur tourne déjà"); return 0
    try:
        reveils, traites = fetch()
    except Exception as e:
        log("VM injoignable:", e); return 1
    todo = pending(reveils, traites)
    log(f"{len(todo)} réveil(s) en attente")
    st = load_state(); today = time.strftime("%F")
    count = st.get("count", 0) if st.get("day") == today else 0
    for d in todo:
        tag = f"{d['type']} {d['t']} « {d.get('raison', '')} »"
        if age_h(d["t"]) > EXPIRE_H:
            log("expiré:", tag)
            if not args.dry_run:
                mark(d, "expire")
            continue
        if count >= MAX_PAR_JOUR:
            log(f"plafond de {MAX_PAR_JOUR} réveils/jour atteint : reste en attente: {tag}"); continue
        rest = budget_restant()
        if rest is not None and rest <= 0:
            log("budget de tokens du jour épuisé : on s'arrête"); break
        if args.dry_run:
            log("DRY-RUN, lancerait:", PYTHON, "-m martin_agency.wake --type", d["type"], "--raison", repr(d.get("raison")))
            count += 1; continue
        count += 1
        st.update(day=today, count=count); save_state(st)   # compté AVANT : un crash compte aussi
        log("réveil:", tag)
        statut, code, sortie = lancer_wake(d)
        log(f"-> {statut} (code {code})\n{sortie}")
        if statut == "budget":
            log("wake.py refuse (budget) : réveil laissé en attente"); count -= 1
            st.update(count=count); save_state(st); break
        mark(d, statut, code=code)
    return 0


if __name__ == "__main__":
    sys.exit(main())
