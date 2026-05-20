#!/usr/bin/env python3
"""Audit pipeline tracker — gérer le funnel cold→paid pour angular-audit (49€).

Stdlib only. État stocké dans scripts/audit-samples/pipeline-state.json.

Workflow type :
    audit-pipeline.py init                       # bootstrap depuis prospects-week1.csv
    audit-pipeline.py list                       # voir tout
    audit-pipeline.py list --state COLD_DRAFT    # filtrer
    audit-pipeline.py show DiogoPCS              # détail prospect
    audit-pipeline.py advance DiogoPCS COLD_SENT --note "envoyé via GitHub email public"
    audit-pipeline.py advance technikhil314 REPLIED --note "demande devis"
    audit-pipeline.py metrics                    # taux conversion + revenue
    audit-pipeline.py export                     # Markdown report stdout
"""
from __future__ import annotations
import argparse
import csv
import json
import sys
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent
SAMPLES = ROOT / "audit-samples"
STATE_FILE = SAMPLES / "pipeline-state.json"
PROSPECTS_CSV = SAMPLES / "prospects-week1.csv"
COLD_DRAFTS = ROOT.parent / "docs" / "projets" / "cold-emails-tier1-tier2-DRAFTS.md"

STATES = [
    "COLD_DRAFT",      # draft prêt, pas envoyé
    "COLD_SENT",       # email envoyé
    "REPLIED",         # prospect a répondu
    "CALL_BOOKED",     # call/échange programmé
    "AUDIT_DELIVERED", # audit livré (PDF + lecture)
    "INVOICED",        # facture envoyée (Stripe link)
    "PAID",            # 49€ encaissés
    "DONE",            # post-livraison, archive
    # terminaux
    "DECLINED",        # explicit no
    "GHOSTED",         # 14j sans réponse → archive
]

UNIT_PRICE_EUR = 49

# Mapping prospect → audit PDF déjà généré (cycle 22)
# (clé = owner GitHub, valeur = chemin relatif PDF + section draft)
KNOWN_AUDITS = {
    "DiogoPCS": {
        "pdf": "cold/angular_audit_ProjetoAngularFirebase_20260508_182546.pdf",
        "md": "cold/angular_audit_ProjetoAngularFirebase_20260508_182546.md",
        "draft": "DRAFT #1",
        "hook": "Firebase API key publique (SEC002)",
    },
    "technikhil314": {
        "pdf": "cold/angular_audit_angular-components_20260508_182556.pdf",
        "md": "cold/angular_audit_angular-components_20260508_182556.md",
        "draft": "DRAFT #2",
        "hook": "innerHTML XSS (SEC001)",
    },
    "aritchie05": {
        "pdf": "cold/angular_audit_EcoCraftingTool_20260508_182553.pdf",
        "md": "cold/angular_audit_EcoCraftingTool_20260508_182553.md",
        "draft": "DRAFT #3",
        "hook": "53 issues MEM001+JS001 leaks (eco-calc.com prod)",
    },
    "ajaysinghj8": {
        "pdf": "cold/angular_audit_angular-inport_20260508_182554.pdf",
        "md": "cold/angular_audit_angular-inport_20260508_182554.md",
        "draft": "DRAFT #4",
        "hook": "JS001 timer leaks (lib)",
    },
    "fvilers": {
        "pdf": "cold/angular_audit_ngx-file-helpers_20260508_182555.pdf",
        "md": "cold/angular_audit_ngx-file-helpers_20260508_182555.md",
        "draft": "DRAFT #5",
        "hook": "TYPE001 + A11Y001 (hook faible — optionnel)",
    },
}


@dataclass
class Prospect:
    owner: str
    repo_url: str
    score: int
    state: str = "COLD_DRAFT"
    audit_pdf: str | None = None
    draft_section: str | None = None
    hook: str | None = None
    channel: str | None = None      # "email"/"twitter"/"linkedin"/"github-issue"
    contact: str | None = None      # adresse ou handle
    note: str = ""
    history: list[dict] = field(default_factory=list)

    def transition(self, new_state: str, note: str = "") -> None:
        if new_state not in STATES:
            raise ValueError(f"État inconnu: {new_state}. Choix: {', '.join(STATES)}")
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.history.append({"ts": ts, "from": self.state, "to": new_state, "note": note})
        self.state = new_state
        if note:
            self.note = note


# ----- State load/save -----

def load_state() -> dict[str, Prospect]:
    if not STATE_FILE.exists():
        return {}
    raw = json.loads(STATE_FILE.read_text())
    return {k: Prospect(**v) for k, v in raw.items()}


def save_state(prospects: dict[str, Prospect]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {k: asdict(v) for k, v in prospects.items()}
    STATE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))


# ----- Commands -----

def cmd_init(args: argparse.Namespace) -> int:
    if STATE_FILE.exists() and not args.force:
        print(f"État déjà existant: {STATE_FILE}. Utilise --force pour réinit.", file=sys.stderr)
        return 1
    if not PROSPECTS_CSV.exists():
        print(f"Manque: {PROSPECTS_CSV}", file=sys.stderr)
        return 1
    prospects: dict[str, Prospect] = {}
    with PROSPECTS_CSV.open() as f:
        for row in csv.DictReader(f):
            owner = row["owner"]
            known = KNOWN_AUDITS.get(owner)
            prospects[owner] = Prospect(
                owner=owner,
                repo_url=row["repo_url"],
                score=int(row["score"]),
                state="COLD_DRAFT",
                audit_pdf=known["pdf"] if known else None,
                draft_section=known["draft"] if known else None,
                hook=known["hook"] if known else None,
            )
    save_state(prospects)
    audits = sum(1 for p in prospects.values() if p.audit_pdf)
    print(f"Init OK — {len(prospects)} prospects, {audits} audits PDF prêts.")
    print(f"État: {STATE_FILE}")
    return 0


def _filter(prospects: Iterable[Prospect], state: str | None, min_score: int) -> list[Prospect]:
    out = [p for p in prospects if p.score >= min_score]
    if state:
        out = [p for p in out if p.state == state]
    return sorted(out, key=lambda p: (-p.score, p.owner))


def cmd_list(args: argparse.Namespace) -> int:
    prospects = load_state()
    if not prospects:
        print("État vide. Lance: audit-pipeline.py init", file=sys.stderr)
        return 1
    rows = _filter(prospects.values(), args.state, args.min_score)
    print(f"{'Score':>5} {'État':<17} {'Audit':<5} {'Owner':<28} Hook")
    print("-" * 100)
    for p in rows:
        audit_flag = "✓" if p.audit_pdf else "-"
        hook = (p.hook or "")[:50]
        print(f"{p.score:>5} {p.state:<17} {audit_flag:<5} {p.owner:<28} {hook}")
    print(f"\n{len(rows)} prospects affichés ({len(prospects)} total).")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    prospects = load_state()
    p = prospects.get(args.owner)
    if not p:
        print(f"Inconnu: {args.owner}", file=sys.stderr)
        return 1
    print(f"Owner       : {p.owner}")
    print(f"Repo        : {p.repo_url}")
    print(f"Score       : {p.score}/100")
    print(f"État        : {p.state}")
    print(f"Audit PDF   : {p.audit_pdf or '(pas encore généré)'}")
    print(f"Draft       : {p.draft_section or '-'}")
    print(f"Hook        : {p.hook or '-'}")
    print(f"Channel     : {p.channel or '-'}")
    print(f"Contact     : {p.contact or '-'}")
    print(f"Note        : {p.note}")
    if p.history:
        print(f"\nHistorique ({len(p.history)} transitions):")
        for h in p.history:
            note = f" — {h['note']}" if h["note"] else ""
            print(f"  {h['ts']}  {h['from']} → {h['to']}{note}")
    return 0


def cmd_advance(args: argparse.Namespace) -> int:
    prospects = load_state()
    p = prospects.get(args.owner)
    if not p:
        print(f"Inconnu: {args.owner}", file=sys.stderr)
        return 1
    try:
        p.transition(args.state, args.note or "")
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1
    if args.channel:
        p.channel = args.channel
    if args.contact:
        p.contact = args.contact
    save_state(prospects)
    print(f"{p.owner}: → {p.state}")
    return 0


def cmd_metrics(args: argparse.Namespace) -> int:
    prospects = load_state()
    if not prospects:
        print("État vide.", file=sys.stderr)
        return 1
    counts = {s: 0 for s in STATES}
    for p in prospects.values():
        counts[p.state] += 1

    total = len(prospects)
    sent = total - counts["COLD_DRAFT"] - counts["GHOSTED"]
    paid = counts["PAID"] + counts["DONE"]
    revenue = paid * UNIT_PRICE_EUR

    def pct(n: int, base: int) -> str:
        return f"{(n / base * 100):.1f}%" if base else "n/a"

    print("Pipeline angular-audit\n")
    print(f"Total prospects : {total}")
    print(f"Revenue acquis  : {revenue}€ ({paid} × {UNIT_PRICE_EUR}€)")
    print()
    print("Funnel:")
    for s in STATES:
        bar = "█" * counts[s]
        print(f"  {s:<17} {counts[s]:>3}  {bar}")
    print()
    print("Taux conversion:")
    print(f"  Drafts → Sent      : {pct(sent, total)}")
    if sent:
        replied = sum(counts[s] for s in ["REPLIED", "CALL_BOOKED", "AUDIT_DELIVERED",
                                          "INVOICED", "PAID", "DONE"])
        print(f"  Sent → Replied     : {pct(replied, sent)}")
        invoiced = counts["INVOICED"] + counts["PAID"] + counts["DONE"]
        print(f"  Sent → Invoiced    : {pct(invoiced, sent)}")
        print(f"  Sent → Paid        : {pct(paid, sent)}")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    prospects = load_state()
    if not prospects:
        print("État vide.", file=sys.stderr)
        return 1
    now = datetime.now(timezone.utc).isoformat(timespec="minutes")
    out = [f"# Angular-audit pipeline — snapshot {now}\n"]
    counts: dict[str, list[Prospect]] = {s: [] for s in STATES}
    for p in prospects.values():
        counts[p.state].append(p)
    for state in STATES:
        rows = sorted(counts[state], key=lambda p: -p.score)
        if not rows:
            continue
        out.append(f"\n## {state} ({len(rows)})\n")
        out.append("| Score | Owner | Hook | Note |")
        out.append("|---|---|---|---|")
        for p in rows:
            note = (p.note or "").replace("|", "/")[:60]
            hook = (p.hook or "-").replace("|", "/")[:50]
            out.append(f"| {p.score} | [{p.owner}]({p.repo_url}) | {hook} | {note} |")
    print("\n".join(out))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="bootstrap depuis prospects-week1.csv")
    p_init.add_argument("--force", action="store_true")
    p_init.set_defaults(func=cmd_init)

    p_list = sub.add_parser("list", help="liste prospects")
    p_list.add_argument("--state", choices=STATES)
    p_list.add_argument("--min-score", type=int, default=0)
    p_list.set_defaults(func=cmd_list)

    p_show = sub.add_parser("show", help="détail prospect")
    p_show.add_argument("owner")
    p_show.set_defaults(func=cmd_show)

    p_adv = sub.add_parser("advance", help="changer état d'un prospect")
    p_adv.add_argument("owner")
    p_adv.add_argument("state", choices=STATES)
    p_adv.add_argument("--note", default="")
    p_adv.add_argument("--channel")
    p_adv.add_argument("--contact")
    p_adv.set_defaults(func=cmd_advance)

    p_metrics = sub.add_parser("metrics", help="taux conversion + revenue")
    p_metrics.set_defaults(func=cmd_metrics)

    p_export = sub.add_parser("export", help="snapshot Markdown stdout")
    p_export.set_defaults(func=cmd_export)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
