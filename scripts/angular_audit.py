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

VERSION = "1.4.0"

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
    "ngfor_no_trackby": {
        "id": "PERF003",
        "name": "*ngFor sans trackBy",
        "category": "Performance",
        "severity": "IMPORTANT",
        "pattern": r"\*ngFor\s*=\s*[\"'](?:(?!trackBy).)*\blet\b(?:(?!trackBy).)*[\"']",
        "description": "*ngFor sans trackBy force Angular à recréer tout le DOM à chaque détection de changement. Sur une liste de 100+ items qui change fréquemment, c'est un gros frein perf.",
        "fix": "Ajouter `; trackBy: trackByFn` dans le *ngFor, et définir `trackByFn(index, item) { return item.id; }` dans le composant. Sur Angular 17+, utiliser le new control flow `@for` avec `track item.id`.",
        "extensions": [".html"],
        "weight": 4,
    },
    "hardcoded_url": {
        "id": "ARCH002",
        "name": "URL hardcodée dans le code",
        "category": "Architecture",
        "severity": "IMPORTANT",
        "pattern": r"['\"`](https?://(?!localhost|127\.0\.0\.1|0\.0\.0\.0)[^'\"`\s)]+)['\"`]",
        "description": "Une URL hardcodée empêche de switcher entre dev/staging/prod sans rebuilder. Force un commit pour changer un endpoint. Mauvaise pratique multi-environnements.",
        "fix": "Déplacer l'URL dans `src/environments/environment.ts` et `environment.prod.ts`. Utiliser `environment.apiUrl` dans le code.",
        "extensions": [".ts"],
        "weight": 4,
        "exclude_pattern": r"\.spec\.ts$|environment(\.\w+)?\.ts$",
    },
    "deep_angular_import": {
        "id": "ARCH003",
        "name": "Import profond @angular",
        "category": "Architecture",
        "severity": "MINEUR",
        "pattern": r"from\s+['\"]@angular/[^'\"]+/(src|esm\d+|fesm\d+|bundles)/",
        "description": "Les deep imports vers `@angular/.../src/...` cassent à chaque mise à jour Angular et accèdent à des APIs internes non garanties.",
        "fix": "Importer uniquement depuis le point d'entrée public : `from '@angular/core'`, `from '@angular/router'`, etc. Si tu as besoin d'une API interne, c'est probablement le signe qu'il faut une autre approche.",
        "extensions": [".ts"],
        "weight": 3,
    },
    "img_no_alt": {
        "id": "A11Y001",
        "name": "Image sans attribut alt",
        "category": "Accessibilite",
        "severity": "IMPORTANT",
        "pattern": r"<img\b(?:(?!alt\s*=)[^>])*/?>",
        "description": "Une balise <img> sans attribut alt est invisible aux lecteurs d'écran et pénalise le SEO. Erreur a11y la plus commune.",
        "fix": "Ajouter `alt=\"description courte\"` (ou `alt=\"\"` pour les images purement décoratives). Pour les images dynamiques, binder `[alt]=\"item.label\"`.",
        "extensions": [".html"],
        "weight": 4,
    },
    "click_on_non_interactive": {
        "id": "A11Y002",
        "name": "Click sur element non-interactif",
        "category": "Accessibilite",
        "severity": "IMPORTANT",
        "pattern": r"<(?:div|span)\b(?![^>]*\b(?:role|tabindex)\s*=)[^>]*\(click\)\s*=",
        "description": "Un (click) sur un <div> ou <span> sans role ni tabindex est inaccessible au clavier et aux lecteurs d'écran. L'utilisateur ne peut pas activer l'action sans souris.",
        "fix": "Soit utiliser un vrai <button> (ou <a> si c'est une navigation), soit ajouter `role=\"button\" tabindex=\"0\"` + handler `(keydown.enter)` et `(keydown.space)`.",
        "extensions": [".html"],
        "weight": 4,
    },
    "skipped_tests": {
        "id": "TEST001",
        "name": "Test skippe ou focus",
        "category": "Code Quality",
        "severity": "MINEUR",
        "pattern": r"\b(?:xit|fit|fdescribe|xdescribe)\s*\(|\b(?:it|describe)\.(?:skip|only)\s*\(",
        "description": "Un `xit`, `fit`, `it.skip` ou `describe.only` oublié signifie qu'une partie de la suite de tests est désactivée ou que la CI ne passe que sur un sous-ensemble. Risque de régression silencieuse.",
        "fix": "Soit corriger et réactiver le test (`xit` → `it`), soit supprimer la suite si elle n'est plus pertinente. Le focus (`fit`, `describe.only`) doit toujours être retiré avant commit.",
        "extensions": [".ts"],
        "weight": 2,
        "exclude_pattern": r"node_modules",
    },
    "hardcoded_secret": {
        "id": "SEC002",
        "name": "Cle API ou secret hardcode",
        "category": "Securite",
        "severity": "CRITIQUE",
        "pattern": r"(?i)(?:api[_-]?key|secret|token|password|access[_-]?key|bearer)\s*[:=]\s*['\"`](?:sk-|sk_|pk_|ghp_|xoxb-|AIza|eyJ)[A-Za-z0-9_\-\.]{15,}['\"`]|['\"`]sk-[A-Za-z0-9]{20,}['\"`]|['\"`](?:ghp|gho|ghu|ghs)_[A-Za-z0-9]{30,}['\"`]",
        "description": "Une cle API, token ou secret hardcode dans le code source est expose des qu'il est commit. Toute personne ayant acces au repo (ou au bundle prod) peut l'extraire et abuser des credentials. Cas reel : OpenAI revoque automatiquement les sk-... detectees sur GitHub public.",
        "fix": "Stocker dans `src/environments/environment.ts` (ignore par .gitignore) ou via variables d'env injectees au build (`ng build --configuration=production` + `fileReplacements`). Pour les secrets serveur, ne jamais les inclure cote client : passer par un backend proxy. Si la cle a deja ete commit, il faut la revoquer immediatement (rotate) puis purger l'historique git.",
        "extensions": [".ts", ".js", ".html", ".json"],
        "weight": 12,
        "exclude_pattern": r"\.spec\.ts$|node_modules|\.example\.|\.template\.",
    },
    "timer_leak": {
        "id": "JS001",
        "name": "setTimeout/setInterval sans cleanup",
        "category": "Memory Leaks",
        "severity": "IMPORTANT",
        "pattern": r"\b(?:setTimeout|setInterval)\s*\(",
        "anti_pattern": r"\b(?:clearTimeout|clearInterval|takeUntilDestroyed|takeUntil|ngOnDestroy)\b",
        "description": "Un `setTimeout` ou surtout `setInterval` lance dans un composant qui n'est jamais clear continue a tourner apres la destruction du composant. Sur une SPA Angular, accumuler des intervalles oublies = memory leak progressif + appels reseau fantomes. Different de RxJS subscriptions (gere par MEM001).",
        "fix": "Garder la reference (`this.timerId = setTimeout(...)`) et appeler `clearTimeout(this.timerId)` dans `ngOnDestroy()`. Ou mieux : utiliser `interval(N).pipe(takeUntilDestroyed())` (Angular 16+) qui s'auto-nettoie.",
        "extensions": [".ts"],
        "weight": 6,
        "exclude_pattern": r"\.spec\.ts$",
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

    # Generic anti_pattern: si la règle a un anti_pattern, on cherche une protection
    # au niveau fichier. Si trouvée, on n'émet aucun problème pour ce fichier.
    # Cas usage : MEM001 (subscribe sans takeUntil), JS001 (setTimeout sans clearTimeout).
    if "anti_pattern" in rule:
        code_only_lines = [
            l for l in lines
            if not l.strip().startswith("//") and not l.strip().startswith("*") and not l.strip().startswith("/*")
        ]
        code_only = "\n".join(code_only_lines)
        file_has_protection = bool(re.search(rule["anti_pattern"], code_only, re.IGNORECASE))
        if file_has_protection:
            return problems

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

# Palette (RGB tuples) — must match the markdown report visual cues
_COLORS = {
    "ink":        (31, 41, 55),
    "muted":      (107, 114, 128),
    "rule_line":  (229, 231, 235),
    "panel_bg":   (243, 244, 246),
    "code_bg":    (249, 250, 251),
    "white":      (255, 255, 255),
    "critique":   (220, 38, 38),
    "important":  (234, 88, 12),
    "mineur":     (107, 114, 128),
    "score_good": (5, 150, 105),
    "score_ok":   (202, 138, 4),
    "score_bad":  (220, 38, 38),
    "accent":     (37, 99, 235),
}

_GRADE_COLOR = {
    "A": "score_good", "B": "score_good",
    "C": "score_ok",   "D": "score_ok",
    "F": "score_bad",
}


def _ascii(text: str) -> str:
    """fpdf2 with built-in fonts is latin-1 — strip what it cannot encode."""
    if text is None:
        return ""
    return (text
            .replace("—", "-").replace("–", "-")
            .replace("'", "'").replace("'", "'")
            .replace(""", '"').replace(""", '"')
            .replace("…", "...")
            .encode("latin-1", "replace").decode("latin-1"))


def try_export_pdf(
    output_path: Path,
    project_path: Path,
    all_problems: list[dict],
    lazy_problems: list[dict],
    pkg_info: dict,
    lazy_info: dict,
    stats: dict,
    score_info: dict,
) -> bool:
    """Generate a styled PDF audit report. Returns True on success, False if fpdf2 missing."""
    try:
        from fpdf import FPDF
    except ImportError:
        return False

    try:
        class AuditPDF(FPDF):
            def __init__(self, project_name: str):
                super().__init__()
                self.project_name = project_name
                self._on_cover = True

            def header(self):
                if self._on_cover:
                    return
                self.set_y(8)
                self.set_font("Helvetica", "", 8)
                self.set_text_color(*_COLORS["muted"])
                self.cell(0, 5, _ascii(f"Angular Code Audit  -  {self.project_name}"), align="L")
                self.set_x(-30)
                self.cell(20, 5, _ascii(f"page {self.page_no()}"), align="R")
                self.set_draw_color(*_COLORS["rule_line"])
                self.set_line_width(0.2)
                self.line(15, 16, 195, 16)
                self.set_y(22)
                self.set_text_color(*_COLORS["ink"])

            def footer(self):
                if self._on_cover:
                    return
                self.set_y(-15)
                self.set_font("Helvetica", "I", 7)
                self.set_text_color(*_COLORS["muted"])
                self.cell(0, 5, _ascii(f"Generated by Angular Code Audit v{VERSION}  -  niam-bay"), align="C")

        project_name = project_path.name
        pdf = AuditPDF(project_name)
        pdf.set_auto_page_break(auto=True, margin=20)

        # ---- Cover page ---------------------------------------------------
        pdf.add_page()
        pdf._on_cover = True

        pdf.set_fill_color(*_COLORS["panel_bg"])
        pdf.rect(0, 0, 210, 297, "F")

        pdf.set_y(40)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*_COLORS["accent"])
        pdf.cell(0, 6, _ascii(f"ANGULAR CODE AUDIT  v{VERSION}"), align="C")

        pdf.set_y(60)
        pdf.set_font("Helvetica", "B", 28)
        pdf.set_text_color(*_COLORS["ink"])
        pdf.cell(0, 14, _ascii(project_name), align="C")

        pdf.set_y(78)
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(*_COLORS["muted"])
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        pdf.cell(0, 6, _ascii(f"Audit date  -  {date_str}"), align="C")
        if pkg_info.get("angular_version"):
            pdf.set_y(85)
            pdf.cell(0, 6, _ascii(f"Angular {pkg_info['angular_version']}  -  {stats['ts_files']} TS files  -  {stats['total_lines']:,} LOC"), align="C")

        # Score badge
        score = score_info["score"]
        grade = score_info["grade"]
        badge_color = _COLORS[_GRADE_COLOR.get(grade, "score_ok")]

        box_x, box_y, box_w, box_h = 65, 110, 80, 60
        pdf.set_fill_color(*badge_color)
        pdf.rect(box_x, box_y, box_w, box_h, "F")

        pdf.set_text_color(*_COLORS["white"])
        pdf.set_font("Helvetica", "B", 48)
        pdf.set_xy(box_x, box_y + 8)
        pdf.cell(box_w, 22, _ascii(f"{score}/100"), align="C")

        pdf.set_font("Helvetica", "B", 22)
        pdf.set_xy(box_x, box_y + 32)
        pdf.cell(box_w, 14, _ascii(f"Grade {grade}"), align="C")

        # Tagline below badge
        pdf.set_xy(15, box_y + box_h + 12)
        pdf.set_font("Helvetica", "I", 11)
        pdf.set_text_color(*_COLORS["muted"])
        pdf.cell(0, 6, _ascii(score_info["summary"]), align="C")

        # Severity counts (cover summary)
        all_combined = all_problems + lazy_problems
        by_sev = {"CRITIQUE": 0, "IMPORTANT": 0, "MINEUR": 0}
        for p in all_combined:
            sev = p["rule"]["severity"]
            if sev in by_sev:
                by_sev[sev] += 1

        pdf.set_y(220)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*_COLORS["ink"])
        pdf.cell(0, 6, _ascii(f"{len(all_combined)} issues detected"), align="C")

        sev_y = 232
        sev_x = 35
        sev_w = 45
        for label, key, count in (
            ("CRITICAL", "critique", by_sev["CRITIQUE"]),
            ("IMPORTANT", "important", by_sev["IMPORTANT"]),
            ("MINOR", "mineur", by_sev["MINEUR"]),
        ):
            pdf.set_fill_color(*_COLORS[key])
            pdf.rect(sev_x, sev_y, sev_w, 18, "F")
            pdf.set_text_color(*_COLORS["white"])
            pdf.set_font("Helvetica", "B", 16)
            pdf.set_xy(sev_x, sev_y + 1)
            pdf.cell(sev_w, 9, str(count), align="C")
            pdf.set_font("Helvetica", "", 8)
            pdf.set_xy(sev_x, sev_y + 9)
            pdf.cell(sev_w, 6, _ascii(label), align="C")
            sev_x += 50

        # Cover footer
        pdf.set_y(275)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(*_COLORS["muted"])
        pdf.cell(0, 5, _ascii("Static analysis report  -  Generated by niam-bay"), align="C")

        # ---- Body pages ---------------------------------------------------
        pdf.add_page()
        pdf._on_cover = False

        def h1(text: str):
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 16)
            pdf.set_text_color(*_COLORS["ink"])
            pdf.cell(0, 9, _ascii(text))
            pdf.ln(10)

        def h2(text: str, color_key: str = "ink"):
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(*_COLORS[color_key])
            pdf.cell(0, 7, _ascii(text))
            pdf.ln(8)
            pdf.set_text_color(*_COLORS["ink"])

        def h3(text: str):
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(*_COLORS["ink"])
            pdf.multi_cell(0, 6, _ascii(text))
            pdf.ln(1)

        def body(text: str):
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(*_COLORS["ink"])
            pdf.multi_cell(0, 5, _ascii(text))

        def muted(text: str, italic: bool = False):
            pdf.set_font("Helvetica", "I" if italic else "", 9)
            pdf.set_text_color(*_COLORS["muted"])
            pdf.multi_cell(0, 5, _ascii(text))
            pdf.set_text_color(*_COLORS["ink"])

        def reset_x():
            pdf.set_x(pdf.l_margin)

        def severity_badge(severity: str):
            key = {"CRITIQUE": "critique", "IMPORTANT": "important", "MINEUR": "mineur"}.get(severity, "muted")
            label = {"CRITIQUE": "CRITICAL", "IMPORTANT": "IMPORTANT", "MINEUR": "MINOR"}.get(severity, severity)
            reset_x()
            x = pdf.get_x()
            y = pdf.get_y()
            w = 26
            pdf.set_fill_color(*_COLORS[key])
            pdf.set_text_color(*_COLORS["white"])
            pdf.set_font("Helvetica", "B", 8)
            pdf.rect(x, y, w, 5, "F")
            pdf.set_xy(x + 1, y + 0.3)
            pdf.cell(w - 2, 4.5, _ascii(label), align="C")
            # leave cursor on the same line, just past the badge — caller decides next move
            pdf.set_xy(x + w + 3, y)
            pdf.set_text_color(*_COLORS["ink"])

        def code_line(text: str):
            text = _ascii(text).rstrip()
            if not text:
                return
            # Courier 8pt fits ~95 chars across the 180mm content width. Cap at 100 to be safe.
            if len(text) > 100:
                text = text[:97] + "..."
            reset_x()
            pdf.set_font("Courier", "", 8)
            pdf.set_text_color(*_COLORS["ink"])
            pdf.set_fill_color(*_COLORS["code_bg"])
            pdf.multi_cell(180, 4.5, text, fill=True)

        def fix_box(text: str):
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*_COLORS["accent"])
            pdf.cell(20, 5, _ascii("Fix:"))
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*_COLORS["ink"])
            pdf.multi_cell(0, 5, _ascii(text))

        def kv_table(rows: list[tuple[str, str]]):
            label_w = 70
            value_w = 180 - label_w  # page width minus margins
            for label, value in rows:
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(*_COLORS["muted"])
                pdf.cell(label_w, 6, _ascii(label), border="B")
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(*_COLORS["ink"])
                pdf.cell(value_w, 6, _ascii(value), border="B")
                pdf.ln(6)

        # Project overview
        h1("Project overview")
        kv_table([
            ("Angular version", str(pkg_info.get("angular_version", "Not detected"))),
            ("TypeScript files", str(stats["ts_files"])),
            ("HTML templates", str(stats["html_files"])),
            ("Components / Services / Modules", f"{stats['components']} / {stats['services']} / {stats['modules']}"),
            ("Pipes / Guards", f"{stats['pipes']} / {stats['guards']}"),
            ("Total lines of code", f"{stats['total_lines']:,}"),
            ("Tests detected", "Yes" if pkg_info.get("has_tests") else "No"),
        ])

        if pkg_info.get("is_outdated"):
            pdf.ln(2)
            pdf.set_fill_color(*_COLORS["panel_bg"])
            pdf.set_text_color(*_COLORS["critique"])
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(0, 6, _ascii(f"  Outdated Angular version: {pkg_info.get('angular_version')} (< 16)"), fill=True)
            pdf.ln(6)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*_COLORS["ink"])
            pdf.set_fill_color(*_COLORS["panel_bg"])
            pdf.multi_cell(
                0, 5,
                _ascii("  No Signals, no Standalone, no Control Flow. Migrating to Angular 17+ is strongly recommended."),
                fill=True,
            )

        # Severity summary
        pdf.ln(4)
        h1("Severity summary")
        total = len(all_combined) or 1
        bar_y = pdf.get_y()
        bar_x = 15
        bar_w = 180
        bar_h = 8
        critique_w = bar_w * by_sev["CRITIQUE"] / total
        important_w = bar_w * by_sev["IMPORTANT"] / total
        mineur_w = bar_w * by_sev["MINEUR"] / total

        pdf.set_fill_color(*_COLORS["rule_line"])
        pdf.rect(bar_x, bar_y, bar_w, bar_h, "F")

        x = bar_x
        if critique_w > 0:
            pdf.set_fill_color(*_COLORS["critique"])
            pdf.rect(x, bar_y, critique_w, bar_h, "F")
            x += critique_w
        if important_w > 0:
            pdf.set_fill_color(*_COLORS["important"])
            pdf.rect(x, bar_y, important_w, bar_h, "F")
            x += important_w
        if mineur_w > 0:
            pdf.set_fill_color(*_COLORS["mineur"])
            pdf.rect(x, bar_y, mineur_w, bar_h, "F")

        pdf.set_y(bar_y + bar_h + 4)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*_COLORS["ink"])
        pdf.cell(60, 5, _ascii(f"Critical: {by_sev['CRITIQUE']}"))
        pdf.cell(60, 5, _ascii(f"Important: {by_sev['IMPORTANT']}"))
        pdf.cell(60, 5, _ascii(f"Minor: {by_sev['MINEUR']}"))
        pdf.ln(8)

        # Issues by category, ordered by severity
        if all_combined:
            h1("Issues detail")

            by_category = defaultdict(list)
            for p in all_combined:
                by_category[p["rule"]["category"]].append(p)

            sorted_categories = sorted(
                by_category.items(),
                key=lambda x: SEVERITY_ORDER.get(x[1][0]["rule"]["severity"], 99),
            )

            for category, problems in sorted_categories:
                severity = problems[0]["rule"]["severity"]
                color_key = {"CRITIQUE": "critique", "IMPORTANT": "important", "MINEUR": "mineur"}.get(severity, "ink")
                h2(category, color_key=color_key)

                by_rule = defaultdict(list)
                for p in problems:
                    by_rule[p["rule"]["id"]].append(p)

                for rule_id, rule_problems in by_rule.items():
                    rule = rule_problems[0]["rule"]
                    severity_badge(rule["severity"])
                    pdf.set_font("Helvetica", "B", 11)
                    pdf.set_text_color(*_COLORS["ink"])
                    pdf.cell(0, 5, _ascii(f"{rule['id']}  {rule['name']}  ({len(rule_problems)})"))
                    pdf.ln(7)

                    muted(rule["description"], italic=True)
                    pdf.ln(1)
                    fix_box(rule["fix"])
                    pdf.ln(2)

                    pdf.set_font("Helvetica", "B", 8)
                    pdf.set_text_color(*_COLORS["muted"])
                    pdf.cell(0, 4, _ascii("OCCURRENCES"))
                    pdf.ln(5)

                    shown = rule_problems[:8]
                    for p in shown:
                        rel_path = os.path.relpath(p["file"], str(project_path))
                        location = f"{rel_path}:{p['line']}"
                        reset_x()
                        pdf.set_font("Helvetica", "B", 8)
                        pdf.set_text_color(*_COLORS["accent"])
                        pdf.multi_cell(180, 4.5, _ascii(location))
                        snippet = p.get("code", "").strip()
                        if snippet:
                            code_line(f"  {snippet}")
                        pdf.ln(0.5)

                    if len(rule_problems) > 8:
                        muted(f"... and {len(rule_problems) - 8} more occurrence(s).", italic=True)

                    pdf.ln(3)
                    pdf.set_draw_color(*_COLORS["rule_line"])
                    pdf.set_line_width(0.15)
                    cur_y = pdf.get_y()
                    pdf.line(15, cur_y, 195, cur_y)
                    pdf.ln(4)
        else:
            h1("No issues detected")
            muted(
                "The audit found no issues across the configured rules. "
                "Either the project is clean or it is too small for this analysis to be meaningful.",
                italic=True,
            )

        # Lazy loading section
        if lazy_info.get("has_routing"):
            h1("Lazy loading")
            kv_table([
                ("Eager routes (no lazy)", str(lazy_info["eager_routes"])),
                ("Lazy routes", str(lazy_info["lazy_routes"])),
                ("Lazy loading ratio", f"{lazy_info['ratio']:.0%}"),
            ])
            if lazy_info["ratio"] < 0.5:
                pdf.ln(1)
                muted(
                    "Less than 50% of routes use lazy loading. Each eager route adds to the initial bundle. "
                    "Migrate to loadComponent (Angular 15+) for the heaviest routes first.",
                    italic=True,
                )
            pdf.ln(3)

        # Refactoring plan
        critiques = [p for p in all_combined if p["rule"]["severity"] == "CRITIQUE"]
        importants = [p for p in all_combined if p["rule"]["severity"] == "IMPORTANT"]
        mineurs = [p for p in all_combined if p["rule"]["severity"] == "MINEUR"]

        if critiques or importants or mineurs:
            h1("Refactoring plan")

            def plan_block(title: str, items: list[dict], color_key: str):
                if not items:
                    return
                h2(title, color_key=color_key)
                seen = set()
                for p in items:
                    rid = p["rule"]["id"]
                    if rid in seen:
                        continue
                    seen.add(rid)
                    pdf.set_font("Helvetica", "B", 9)
                    pdf.cell(0, 5, _ascii(f"  - {p['rule']['name']}  ({rid})"))
                    pdf.ln(5)
                    desc = p["rule"]["description"]
                    if len(desc) > 130:
                        desc = desc[:127] + "..."
                    muted(f"    {desc}", italic=False)
                    pdf.ln(0.5)
                pdf.ln(2)

            plan_block("This week  -  Critical", critiques, "critique")
            plan_block("This month  -  Important", importants, "important")
            plan_block("On the roadmap  -  Minor", mineurs, "mineur")

        # Closing note
        pdf.ln(4)
        pdf.set_draw_color(*_COLORS["rule_line"])
        pdf.set_line_width(0.2)
        cur_y = pdf.get_y()
        pdf.line(15, cur_y, 195, cur_y)
        pdf.ln(3)
        muted(
            "This report is produced by automated static analysis. "
            "It does not replace a thorough manual review by an experienced Angular developer.",
            italic=True,
        )

        pdf.output(str(output_path))
        return True
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

    # Tentative PDF (rendu structure, ne consomme pas le markdown)
    pdf_path = output_dir / f"{report_name}.pdf"
    if try_export_pdf(
        pdf_path, project_path, all_problems, lazy_problems,
        pkg_info, lazy_info, stats, score_info,
    ):
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
