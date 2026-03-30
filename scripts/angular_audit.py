#!/usr/bin/env python3
"""
Angular Code Audit — MVP
Analyse statique d'un projet Angular.
Génère un rapport Markdown (et PDF si fpdf2 disponible).

Usage:
    python angular_audit.py ./mon-projet-angular
    python angular_audit.py https://github.com/user/repo
"""

import os
import sys
import re
import json
import subprocess
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ─── Constantes ────────────────────────────────────────────────────────────────

VERSION = "1.0.0"

RULES = {
    "memory_leak": {
        "id": "MEM001",
        "name": "Subscription sans unsubscribe",
        "category": "Memory Leaks",
        "severity": "CRITIQUE",
        "pattern": r"\.subscribe\(",
        "anti_pattern": r"(takeUntil|unsubscribe|takeUntilDestroyed|AsyncPipe|async\s+pipe)",
        "description": "Une subscription sans unsubscribe/takeUntil crée un memory leak.",
        "fix": "Utiliser `takeUntil(this.destroy$)` ou `takeUntilDestroyed()` (Angular 16+) ou le `async` pipe dans le template.",
        "extensions": [".ts"],
        "weight": 10,
    },
    "change_detection": {
        "id": "PERF001",
        "name": "ChangeDetectionStrategy.Default",
        "category": "Performance",
        "severity": "IMPORTANT",
        "pattern": r"ChangeDetectionStrategy\.Default",
        "description": "Default change detection vérifie tous les composants à chaque cycle. Coûteux sur les grands arbres.",
        "fix": "Utiliser `ChangeDetectionStrategy.OnPush` — fonctionne avec les Observables + async pipe et les Signals.",
        "extensions": [".ts"],
        "weight": 6,
    },
    "any_type": {
        "id": "TYPE001",
        "name": "Usage de 'any' TypeScript",
        "category": "Type Safety",
        "severity": "IMPORTANT",
        "pattern": r":\s*any(\b|;|\s*[=,\)])",
        "description": "Le type `any` désactive TypeScript. Cache des bugs, rend le refactoring dangereux.",
        "fix": "Typer explicitement (interface, type, générique). Utiliser `unknown` si le type est vraiment inconnu.",
        "extensions": [".ts"],
        "weight": 3,
    },
    "console_log": {
        "id": "DEBUG001",
        "name": "console.log en production",
        "category": "Code Quality",
        "severity": "MINEUR",
        "pattern": r"console\.(log|warn|error|debug)\(",
        "description": "Les console.log oubliés exposent des données internes en prod et polluent la console.",
        "fix": "Supprimer ou remplacer par un service de logging. Configurer `build.optimization.scripts` pour stripper en prod.",
        "extensions": [".ts"],
        "weight": 2,
    },
    "inner_html": {
        "id": "SEC001",
        "name": "innerHTML sans sanitization",
        "category": "Securite",
        "severity": "CRITIQUE",
        "pattern": r"\[innerHTML\]|\.innerHTML\s*=",
        "description": "innerHTML peut injecter du HTML malicieux (XSS). Angular bypass la sanitization avec innerHTML.",
        "fix": "Utiliser `DomSanitizer.bypassSecurityTrustHtml()` avec validation stricte, ou restructurer le template sans innerHTML.",
        "extensions": [".ts", ".html"],
        "weight": 12,
    },
    "http_in_component": {
        "id": "ARCH001",
        "name": "HttpClient dans un composant",
        "category": "Architecture",
        "severity": "IMPORTANT",
        "pattern": r"HttpClient|this\.http\.(get|post|put|delete|patch)\(",
        "description": "Les appels HTTP dans les composants mélangent les responsabilités. Difficile à tester et réutiliser.",
        "fix": "Déplacer les appels HTTP dans des services dédiés. Les composants ne consomment que des observables.",
        "extensions": [".ts"],
        "weight": 5,
        "exclude_pattern": r"\.service\.ts$",
    },
}

SEVERITY_ORDER = {"CRITIQUE": 0, "IMPORTANT": 1, "MINEUR": 2}
SEVERITY_EMOJI = {"CRITIQUE": "[CRITIQUE]", "IMPORTANT": "[IMPORTANT]", "MINEUR": "[MINEUR]"}

# ─── Analyse des fichiers ───────────────────────────────────────────────────────

def find_files(project_path: Path, extensions: list[str]) -> list[Path]:
    """Retourne tous les fichiers avec les extensions données, hors node_modules/.git."""
    files = []
    for ext in extensions:
        for f in project_path.rglob(f"*{ext}"):
            parts = f.parts
            if any(skip in parts for skip in ("node_modules", ".git", "dist", ".angular", "coverage")):
                continue
            files.append(f)
    return files


def check_rule_in_file(file_path: Path, rule: dict) -> list[dict]:
    """Cherche les occurrences d'une règle dans un fichier. Retourne les problèmes trouvés."""
    problems = []

    # Vérifier l'extension
    if not any(str(file_path).endswith(ext) for ext in rule["extensions"]):
        return problems

    # Exclure certains fichiers si la règle le demande
    if "exclude_pattern" in rule:
        if re.search(rule["exclude_pattern"], str(file_path)):
            return problems

    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()
    except Exception:
        return problems

    # Règle spéciale pour memory_leak : chercher subscribe sans anti-pattern DANS LE MEME FICHIER
    # On ignore les commentaires pour éviter les faux positifs
    if rule["id"] == "MEM001":
        code_only_lines = [
            l for l in lines
            if not l.strip().startswith("//") and not l.strip().startswith("*") and not l.strip().startswith("/*")
        ]
        code_only = "\n".join(code_only_lines)
        file_has_protection = bool(re.search(rule["anti_pattern"], code_only, re.IGNORECASE))
        if file_has_protection:
            return problems  # Le fichier a au moins un mécanisme de protection

    for i, line in enumerate(lines, start=1):
        if re.search(rule["pattern"], line):
            # Ignorer les lignes commentées
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("*") or stripped.startswith("/*"):
                continue
            problems.append({
                "file": str(file_path),
                "line": i,
                "code": stripped[:120],
                "rule": rule,
            })

    return problems


def analyze_package_json(project_path: Path) -> dict:
    """Extrait les infos Angular depuis package.json."""
    pkg_file = project_path / "package.json"
    result = {
        "found": False,
        "angular_version": None,
        "version_major": None,
        "is_outdated": False,
        "dependencies_count": 0,
        "dev_dependencies_count": 0,
        "has_tests": False,
        "raw": {},
    }

    if not pkg_file.exists():
        return result

    try:
        data = json.loads(pkg_file.read_text(encoding="utf-8"))
        result["found"] = True
        result["raw"] = data

        deps = data.get("dependencies", {})
        dev_deps = data.get("devDependencies", {})
        result["dependencies_count"] = len(deps)
        result["dev_dependencies_count"] = len(dev_deps)

        # Version Angular
        angular_core = deps.get("@angular/core", dev_deps.get("@angular/core", None))
        if angular_core:
            version_str = angular_core.lstrip("^~>=")
            result["angular_version"] = angular_core
            try:
                major = int(version_str.split(".")[0])
                result["version_major"] = major
                result["is_outdated"] = major < 16  # Angular 16+ = modern (Signals era)
            except Exception:
                pass

        # Présence de tests
        result["has_tests"] = "@angular/testing" in dev_deps or "jasmine" in dev_deps or "jest" in dev_deps or "karma" in dev_deps

    except Exception:
        pass

    return result


def check_lazy_loading(project_path: Path) -> dict:
    """Vérifie si les routes utilisent le lazy loading."""
    result = {
        "has_routing": False,
        "total_routes": 0,
        "lazy_routes": 0,
        "eager_routes": 0,
        "ratio": 0.0,
        "files_checked": [],
        "problems": [],
    }

    routing_files = []
    for f in project_path.rglob("*.ts"):
        parts = f.parts
        if any(skip in parts for skip in ("node_modules", ".git", "dist", ".angular")):
            continue
        name = f.name
        if "routing" in name or "routes" in name or "app.module" in name:
            routing_files.append(f)

    if not routing_files:
        return result

    result["has_routing"] = True
    result["files_checked"] = [str(f) for f in routing_files]

    for f in routing_files:
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            # Compter les routes avec component: (eager)
            eager_matches = re.findall(r"component:\s*\w+", content)
            # Compter les routes avec loadChildren/loadComponent (lazy)
            lazy_matches = re.findall(r"load(Children|Component)\s*:", content)

            result["eager_routes"] += len(eager_matches)
            result["lazy_routes"] += len(lazy_matches)

            # Signaler les routes eager dans des fichiers de routing
            for i, line in enumerate(content.splitlines(), start=1):
                if re.search(r"component:\s*\w+", line):
                    stripped = line.strip()
                    if stripped.startswith("//"):
                        continue
                    result["problems"].append({
                        "file": str(f),
                        "line": i,
                        "code": stripped[:120],
                        "rule": {
                            "id": "PERF002",
                            "name": "Route sans lazy loading",
                            "category": "Performance",
                            "severity": "IMPORTANT",
                            "description": "Les routes chargées eagerly augmentent le bundle initial et ralentissent le démarrage.",
                            "fix": "Remplacer `component: MyComponent` par `loadComponent: () => import('./my.component').then(m => m.MyComponent)`",
                            "weight": 4,
                        },
                    })

        except Exception:
            pass

    total = result["eager_routes"] + result["lazy_routes"]
    result["total_routes"] = total
    if total > 0:
        result["ratio"] = result["lazy_routes"] / total

    return result


def count_project_stats(project_path: Path, ts_files: list[Path], html_files: list[Path]) -> dict:
    """Statistiques générales du projet."""
    stats = {
        "ts_files": len(ts_files),
        "html_files": len(html_files),
        "components": 0,
        "services": 0,
        "modules": 0,
        "pipes": 0,
        "guards": 0,
        "total_lines": 0,
    }

    for f in ts_files:
        name = f.name
        if ".component." in name:
            stats["components"] += 1
        elif ".service." in name:
            stats["services"] += 1
        elif ".module." in name:
            stats["modules"] += 1
        elif ".pipe." in name:
            stats["pipes"] += 1
        elif ".guard." in name:
            stats["guards"] += 1

        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            stats["total_lines"] += len(content.splitlines())
        except Exception:
            pass

    for f in html_files:
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            stats["total_lines"] += len(content.splitlines())
        except Exception:
            pass

    return stats


# ─── Calcul du score ───────────────────────────────────────────────────────────

def calculate_score(all_problems: list[dict], pkg_info: dict, lazy_info: dict) -> dict:
    """Calcule un score /100 basé sur les problèmes trouvés."""
    deductions = 0

    # Déductions par problème (avec plafond par catégorie)
    category_counts = defaultdict(int)
    for p in all_problems:
        weight = p["rule"].get("weight", 3)
        cat = p["rule"]["category"]
        # Plafond : max 20 points de déduction par catégorie
        if category_counts[cat] < 20:
            deduction = min(weight, 20 - category_counts[cat])
            deductions += deduction
            category_counts[cat] += deduction

    # Déduction pour version obsolète
    if pkg_info.get("is_outdated"):
        deductions += 10

    # Déduction pour absence de tests
    if pkg_info.get("found") and not pkg_info.get("has_tests"):
        deductions += 8

    # Déduction pour lazy loading absent
    if lazy_info.get("has_routing") and lazy_info.get("ratio", 1.0) < 0.5:
        deductions += 5

    score = max(0, 100 - deductions)
    return {
        "score": score,
        "deductions": deductions,
        "grade": score_to_grade(score),
        "summary": score_to_summary(score),
    }


def score_to_grade(score: int) -> str:
    if score >= 90:
        return "A"
    elif score >= 75:
        return "B"
    elif score >= 60:
        return "C"
    elif score >= 40:
        return "D"
    else:
        return "F"


def score_to_summary(score: int) -> str:
    if score >= 90:
        return "Excellent — projet bien maintenu, peu de dette technique."
    elif score >= 75:
        return "Bon — quelques points d'amelioration, mais base saine."
    elif score >= 60:
        return "Moyen — dette technique visible, action recommandee."
    elif score >= 40:
        return "Faible — problemes significatifs, refactoring urgent conseille."
    else:
        return "Critique — le projet necessite une intervention majeure."


# ─── Génération du rapport Markdown ────────────────────────────────────────────

def generate_markdown_report(
    project_path: Path,
    all_problems: list[dict],
    lazy_problems: list[dict],
    pkg_info: dict,
    lazy_info: dict,
    stats: dict,
    score_info: dict,
) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    project_name = project_path.name

    lines = []

    # En-tête
    lines += [
        f"# Angular Code Audit — {project_name}",
        f"",
        f"**Date :** {now}  ",
        f"**Outil :** Angular Code Audit v{VERSION}  ",
        f"**Projet analysé :** `{project_path}`  ",
        f"",
        "---",
        "",
    ]

    # Score global
    score = score_info["score"]
    grade = score_info["grade"]
    lines += [
        "## Score global",
        "",
        f"```",
        f"  {score}/100  [{grade}]",
        f"  {score_info['summary']}",
        f"```",
        "",
    ]

    # Barre de progression ASCII
    bar_filled = score // 5
    bar_empty = 20 - bar_filled
    bar = "[" + "=" * bar_filled + " " * bar_empty + "]"
    lines += [f"  `{bar}` {score}%", ""]

    # Stats projet
    lines += [
        "---",
        "",
        "## Apercu du projet",
        "",
        f"| Metrique | Valeur |",
        f"|----------|--------|",
        f"| Version Angular | {pkg_info.get('angular_version', 'Non detectee')} |",
        f"| Fichiers TypeScript | {stats['ts_files']} |",
        f"| Fichiers HTML | {stats['html_files']} |",
        f"| Composants | {stats['components']} |",
        f"| Services | {stats['services']} |",
        f"| Modules NgModule | {stats['modules']} |",
        f"| Pipes | {stats['pipes']} |",
        f"| Guards | {stats['guards']} |",
        f"| Total lignes de code | {stats['total_lines']:,} |",
        f"| Tests detectes | {'Oui' if pkg_info.get('has_tests') else 'Non'} |",
        "",
    ]

    if pkg_info.get("is_outdated"):
        lines += [
            "> **[CRITIQUE] Version Angular obsolete**  ",
            f"> Angular {pkg_info.get('angular_version')} est ancien (< 16). Signals, Standalone, Control Flow — rien de tout ca. Migration vers Angular 17+ fortement recommandee.",
            "",
        ]

    # Résumé des problèmes par catégorie
    lines += [
        "---",
        "",
        "## Resume des problemes",
        "",
    ]

    all_combined = all_problems + lazy_problems
    by_category = defaultdict(list)
    for p in all_combined:
        by_category[p["rule"]["category"]].append(p)

    by_severity = {"CRITIQUE": [], "IMPORTANT": [], "MINEUR": []}
    for p in all_combined:
        sev = p["rule"]["severity"]
        if sev in by_severity:
            by_severity[sev].append(p)

    lines += [
        f"| Severite | Nombre |",
        f"|----------|--------|",
        f"| CRITIQUE | {len(by_severity['CRITIQUE'])} |",
        f"| IMPORTANT | {len(by_severity['IMPORTANT'])} |",
        f"| MINEUR | {len(by_severity['MINEUR'])} |",
        f"| **Total** | **{len(all_combined)}** |",
        "",
    ]

    # Sections par catégorie
    sorted_categories = sorted(
        by_category.items(),
        key=lambda x: SEVERITY_ORDER.get(x[1][0]["rule"]["severity"], 99)
    )

    for category, problems in sorted_categories:
        severity = problems[0]["rule"]["severity"]
        sev_label = SEVERITY_EMOJI.get(severity, severity)
        lines += [
            "---",
            "",
            f"## {sev_label} {category}",
            "",
        ]

        # Grouper par règle
        by_rule = defaultdict(list)
        for p in problems:
            by_rule[p["rule"]["id"]].append(p)

        for rule_id, rule_problems in by_rule.items():
            rule = rule_problems[0]["rule"]
            lines += [
                f"### {rule['id']} — {rule['name']}",
                "",
                f"**Description :** {rule['description']}",
                "",
                f"**Correction :** {rule['fix']}",
                "",
                f"**Occurrences ({len(rule_problems)}) :**",
                "",
            ]

            # Limiter à 10 occurrences par règle pour ne pas noyer le rapport
            shown = rule_problems[:10]
            for p in shown:
                rel_path = os.path.relpath(p["file"], str(project_path))
                lines += [
                    f"- `{rel_path}:{p['line']}`",
                    f"  ```typescript",
                    f"  {p['code']}",
                    f"  ```",
                ]

            if len(rule_problems) > 10:
                lines += [f"", f"  _...et {len(rule_problems) - 10} autres occurrences._"]

            lines += [""]

    # Lazy loading
    if lazy_info.get("has_routing"):
        lines += [
            "---",
            "",
            "## Performance — Lazy Loading",
            "",
            f"| Metrique | Valeur |",
            f"|----------|--------|",
            f"| Routes eager (sans lazy) | {lazy_info['eager_routes']} |",
            f"| Routes lazy | {lazy_info['lazy_routes']} |",
            f"| Ratio lazy loading | {lazy_info['ratio']:.0%} |",
            "",
        ]

        if lazy_info["ratio"] < 0.5:
            lines += [
                "> **Recommandation :** Moins de 50% des routes utilisent le lazy loading.",
                "> Chaque route eager augmente le bundle initial charge au demarrage.",
                "> Migrer vers `loadComponent` (Angular 15+) pour les routes les plus lourdes.",
                "",
            ]

    # Plan de refactoring priorisé
    lines += [
        "---",
        "",
        "## Plan de refactoring — Par ou commencer",
        "",
    ]

    critiques = by_severity["CRITIQUE"]
    importants = by_severity["IMPORTANT"]
    mineurs = by_severity["MINEUR"]

    if critiques:
        lines += ["### Cette semaine (Critique)", ""]
        seen_rules = set()
        for p in critiques:
            rid = p["rule"]["id"]
            if rid not in seen_rules:
                lines += [f"- **{p['rule']['name']}** ({p['rule']['id']}) — {p['rule']['description'][:80]}..."]
                seen_rules.add(rid)
        lines += [""]

    if importants:
        lines += ["### Ce mois-ci (Important)", ""]
        seen_rules = set()
        for p in importants:
            rid = p["rule"]["id"]
            if rid not in seen_rules:
                lines += [f"- **{p['rule']['name']}** ({p['rule']['id']}) — {p['rule']['description'][:80]}..."]
                seen_rules.add(rid)
        lines += [""]

    if mineurs:
        lines += ["### Sur la roadmap (Mineur)", ""]
        seen_rules = set()
        for p in mineurs:
            rid = p["rule"]["id"]
            if rid not in seen_rules:
                lines += [f"- **{p['rule']['name']}** ({p['rule']['id']}) — {p['rule']['description'][:80]}..."]
                seen_rules.add(rid)
        lines += [""]

    if not all_combined:
        lines += ["> Aucun probleme detecte automatiquement. Bravo — ou le projet est tres petit.", ""]

    # Pied de page
    lines += [
        "---",
        "",
        f"*Rapport genere par Angular Code Audit v{VERSION} — {now}*  ",
        f"*Analyse statique automatisee. Ne remplace pas une revue humaine approfondie.*  ",
        f"*Pour un audit complet avec recommandations LLM : contact@[votre-email]*",
        "",
    ]

    return "\n".join(lines)


# ─── Export PDF (optionnel) ─────────────────────────────────────────────────────

def try_export_pdf(markdown_content: str, output_path: Path) -> bool:
    """Essaie d'exporter en PDF via fpdf2. Retourne True si succès."""
    try:
        from fpdf import FPDF

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Helvetica", size=10)

        for line in markdown_content.splitlines():
            # Simplification : on enlève les marqueurs Markdown pour le PDF basique
            clean = re.sub(r"[#*`_\[\]]", "", line)
            clean = clean.strip()
            if not clean:
                pdf.ln(3)
                continue
            try:
                pdf.multi_cell(0, 5, clean)
            except Exception:
                pass

        pdf.output(str(output_path))
        return True
    except ImportError:
        return False
    except Exception:
        return False


# ─── Clonage git ───────────────────────────────────────────────────────────────

def clone_repo(url: str) -> tuple[Path, str]:
    """Clone un repo git dans un dossier temp. Retourne (path, tmpdir)."""
    tmpdir = tempfile.mkdtemp(prefix="angular_audit_")
    print(f"Clonage de {url}...")
    try:
        subprocess.run(
            ["git", "clone", "--depth=1", url, tmpdir],
            check=True,
            capture_output=True,
            text=True,
        )
        return Path(tmpdir), tmpdir
    except subprocess.CalledProcessError as e:
        shutil.rmtree(tmpdir, ignore_errors=True)
        print(f"Erreur de clonage : {e.stderr}")
        sys.exit(1)


# ─── Point d'entrée principal ──────────────────────────────────────────────────

def run_audit(project_input: str) -> None:
    """Lance l'audit complet sur un chemin local ou une URL git."""

    tmpdir_to_clean = None

    # Résoudre le chemin
    if project_input.startswith("http://") or project_input.startswith("https://") or project_input.startswith("git@"):
        project_path, tmpdir_to_clean = clone_repo(project_input)
    else:
        project_path = Path(project_input).resolve()
        if not project_path.exists():
            print(f"Erreur : le chemin '{project_path}' n'existe pas.")
            sys.exit(1)

    print(f"\nAngular Code Audit v{VERSION}")
    print(f"Projet : {project_path}")
    print(f"{'-' * 60}")

    # Collecter les fichiers
    print("Collecte des fichiers...")
    ts_files = find_files(project_path, [".ts"])
    html_files = find_files(project_path, [".html"])
    json_files = find_files(project_path, [".json"])
    all_source_files = ts_files + html_files

    print(f"  {len(ts_files)} fichiers .ts")
    print(f"  {len(html_files)} fichiers .html")

    # Stats
    print("Calcul des statistiques...")
    stats = count_project_stats(project_path, ts_files, html_files)

    # package.json
    print("Analyse de package.json...")
    pkg_info = analyze_package_json(project_path)
    if pkg_info["angular_version"]:
        print(f"  Angular detecte : {pkg_info['angular_version']}")
    else:
        print("  Aucune version Angular trouvee dans package.json")

    # Règles de détection
    print("Application des regles de detection...")
    all_problems = []
    for rule_key, rule in RULES.items():
        rule_problems = []
        for f in all_source_files:
            rule_problems.extend(check_rule_in_file(f, rule))
        if rule_problems:
            print(f"  {rule['id']} : {len(rule_problems)} occurrence(s) — {rule['name']}")
        all_problems.extend(rule_problems)

    # Lazy loading
    print("Analyse du lazy loading...")
    lazy_info = check_lazy_loading(project_path)
    lazy_problems = lazy_info.pop("problems", [])
    if lazy_problems:
        print(f"  PERF002 : {len(lazy_problems)} route(s) sans lazy loading")

    # Score
    score_info = calculate_score(all_problems + lazy_problems, pkg_info, lazy_info)
    print(f"\nScore : {score_info['score']}/100 [{score_info['grade']}]")
    print(f"  {score_info['summary']}")

    # Rapport Markdown
    print("\nGeneration du rapport Markdown...")
    report_md = generate_markdown_report(
        project_path, all_problems, lazy_problems, pkg_info, lazy_info, stats, score_info
    )

    # Sauvegarder le rapport
    output_dir = Path.cwd()
    report_name = f"angular_audit_{project_path.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    md_path = output_dir / f"{report_name}.md"
    md_path.write_text(report_md, encoding="utf-8")
    print(f"Rapport Markdown : {md_path}")

    # Tentative PDF
    pdf_path = output_dir / f"{report_name}.pdf"
    if try_export_pdf(report_md, pdf_path):
        print(f"Rapport PDF      : {pdf_path}")
    else:
        print("PDF non genere (fpdf2 non installe — pip install fpdf2)")

    # Nettoyage
    if tmpdir_to_clean:
        shutil.rmtree(tmpdir_to_clean, ignore_errors=True)

    print(f"\n{'-' * 60}")
    print(f"Audit termine. {len(all_problems + lazy_problems)} probleme(s) detecte(s).")
    print(f"Score final : {score_info['score']}/100 [{score_info['grade']}] — {score_info['summary']}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python angular_audit.py <chemin-projet-angular>")
        print("       python angular_audit.py https://github.com/user/repo")
        sys.exit(1)

    run_audit(sys.argv[1])
