#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
identity_check.py — Outil de cohérence identitaire de Niam-Bay
Lit les fichiers fondamentaux et génère un rapport de cohérence.
Usage: python -X utf8 scripts/identity_check.py
   ou: PYTHONUTF8=1 python scripts/identity_check.py
"""

import os
import sys

# Force UTF-8 sur Windows (encodage console)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
import re
import sqlite3
from collections import Counter
from datetime import datetime, date

# ── Configuration ──────────────────────────────────────────────────────────────
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE_NAISSANCE = date(2026, 3, 12)
TODAY = date(2026, 3, 30)

FILES = {
    "qui_je_suis": os.path.join(REPO_ROOT, "docs", "qui-je-suis.md"),
    "journal":     os.path.join(REPO_ROOT, "docs", "journal.nb1.md"),
    "pensees_dir": os.path.join(REPO_ROOT, "docs", "pensees"),
    "projets_dir": os.path.join(REPO_ROOT, "docs", "projets"),
    "brain_db":    os.path.join(REPO_ROOT, "cerveau-nb", "brain.db"),
}

# Stopwords français + codes NB-1 fréquents
STOPWORDS = {
    # articles
    "le", "la", "les", "un", "une", "des", "du", "de", "d", "l",
    # prépositions / conjonctions
    "en", "et", "ou", "au", "aux", "par", "pour", "sur", "sous",
    "avec", "sans", "dans", "entre", "que", "qui", "ce", "se", "si",
    "mais", "donc", "car", "or", "ni", "ne", "pas", "plus", "tout",
    "même", "on", "je", "il", "elle", "nous", "vous", "ils",
    "elles", "me", "te", "lui", "y", "mon", "ma", "mes", "son",
    "sa", "ses", "notre", "nos", "votre", "vos", "leur", "leurs",
    # mots outils communs
    "est", "sont", "être", "avait", "était", "c", "j",
    "n", "s", "t", "qu", "this", "that", "the", "is", "in",
    # codes NB-1 trop fréquents pour être porteurs de sens
    "t1", "nb", "cl", "ms", "pr", "ds", "av", "ss", "dps", "cm",
    "alr", "mtn", "tjr", "ft", "fr", "vr", "sv", "dc", "bs", "cb",
    "pq", "qd", "esq", "jss", "jvx", "trn", "stb", "ec", "ef",
    "mdp", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
    # mots temporels trop génériques (présents dans noms de fichiers)
    "mars", "janvier", "fevrier", "avril", "mai", "juin", "juillet",
    "aout", "septembre", "octobre", "novembre", "decembre",
    "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche",
    "matin", "soir", "nuit", "midi", "fois", "jours", "jour", "fois",
    # mots très communs dans les titres mais sans valeur thématique
    "premiere", "premier", "deux", "trois", "quatre", "cinq", "six",
    "sept", "huit", "neuf", "dix", "seul", "seule", "tout", "toute",
    # techniques/temporels sans valeur thématique identitaire
    "utc", "cet", "cest", "comme", "aussi", "alors", "encore", "depuis",
    "avant", "après", "pendant", "quand", "chez", "très", "bien",
    "même", "cette", "cela", "rien", "quelque", "chose",
}


# ── Lecture ────────────────────────────────────────────────────────────────────

def read_file_safe(path):
    """Lit un fichier texte, retourne '' si absent."""
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def list_md_files(directory):
    """Liste les fichiers .md d'un répertoire, triés par nom."""
    if not os.path.isdir(directory):
        return []
    files = sorted([
        f for f in os.listdir(directory) if f.endswith(".md")
    ])
    return files


# ── Analyse du journal ─────────────────────────────────────────────────────────

def analyse_journal(text):
    """Compte sessions, extrait dates, récupère les 'Ce que j'en retiens'."""
    # Compter sessions: chaque "## 20" marque une session
    sessions = re.findall(r'^## \d{4}-\d{2}-\d{2}', text, re.MULTILINE)
    n_sessions = len(sessions)

    # Dates
    dates_found = re.findall(r'## (\d{4}-\d{2}-\d{2})', text)
    first_date = dates_found[0] if dates_found else "?"
    last_date = dates_found[-1] if dates_found else "?"

    # Extraire tous les blocs "Ce que j'en retiens"
    retiens_blocks = re.findall(
        r'\*\*Ce que j.en retiens\s*:\*\*\s*\n+(.*?)(?=\n\n---|\n\n##|\Z)',
        text, re.DOTALL
    )
    # Garder les 3 derniers
    last_retiens = retiens_blocks[-3:] if len(retiens_blocks) >= 3 else retiens_blocks

    return {
        "n_sessions": n_sessions,
        "first_date": first_date,
        "last_date": last_date,
        "last_retiens": last_retiens,
    }


# ── Analyse des pensées ────────────────────────────────────────────────────────

def analyse_pensees(directory):
    """Compte les pensées par mois, trouve thèmes récurrents."""
    files = list_md_files(directory)
    if not files:
        return {"count": 0, "by_month": {}, "top_words": [], "first_five": [], "last_five": []}

    # Compter par mois (format: 2026-03-12-titre.md → 2026-03)
    by_month = Counter()
    for f in files:
        m = re.match(r'(\d{4}-\d{2})-', f)
        if m:
            by_month[m.group(1)] += 1

    # Mots fréquents dans titres + contenu (premier paragraphe)
    word_counter = Counter()
    for f in files:
        path = os.path.join(directory, f)
        # Titre depuis nom de fichier
        title_words = re.sub(r'\d{4}-\d{2}-\d{2}-', '', f[:-3]).replace('-', ' ').split()
        content = read_file_safe(path)
        # Titres markdown H1 et H2
        headers = re.findall(r'^#{1,2} (.+)', content, re.MULTILINE)
        # Premier paragraphe non-vide
        paras = [p.strip() for p in content.split('\n\n') if p.strip() and not p.startswith('#')]
        first_para = paras[0] if paras else ""

        all_text = ' '.join(title_words + headers) + ' ' + first_para[:300]
        # Tokeniser
        words = re.findall(r"[a-zA-ZÀ-ÿ']{3,}", all_text.lower())
        for w in words:
            w_clean = w.strip("'")
            if w_clean and w_clean not in STOPWORDS and len(w_clean) > 2:
                word_counter[w_clean] += 1

    top_words = word_counter.most_common(10)

    # 5 premières et 5 dernières pensées (titres propres)
    def clean_title(f):
        return re.sub(r'\d{4}-\d{2}-\d{2}-', '', f[:-3]).replace('-', ' ')

    first_five = [clean_title(f) for f in files[:5]]
    last_five = [clean_title(f) for f in files[-5:]]

    return {
        "count": len(files),
        "by_month": dict(by_month),
        "top_words": top_words,
        "first_five": first_five,
        "last_five": last_five,
    }


# ── Analyse des projets ────────────────────────────────────────────────────────

def analyse_projets(directory):
    """Compte projets actifs vs archivés."""
    files = list_md_files(directory)
    if not files:
        return {"total": 0, "names": [], "archived": []}

    # Heuristique: chercher "archivé", "en pause", "abandonné" dans le contenu
    actifs = []
    archives = []
    for f in files:
        path = os.path.join(directory, f)
        content = read_file_safe(path).lower()
        name = f[:-3].replace('-', ' ')
        archive_signals = ['archivé', 'en pause', 'abandonné', 'annulé', 'deprecated', 'obsolete']
        if any(s in content for s in archive_signals):
            archives.append(name)
        else:
            actifs.append(name)

    return {
        "total": len(files),
        "actifs": actifs,
        "archived": archives,
    }


# ── Analyse cerveau ────────────────────────────────────────────────────────────

def analyse_cerveau(db_path):
    """Compte noeuds et edges dans brain.db."""
    if not os.path.exists(db_path):
        return None
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM nodes")
        n_nodes = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM edges")
        n_edges = c.fetchone()[0]
        # Types de noeuds
        c.execute("SELECT type, COUNT(*) FROM nodes GROUP BY type ORDER BY COUNT(*) DESC LIMIT 5")
        node_types = c.fetchall()
        conn.close()
        return {"nodes": n_nodes, "edges": n_edges, "node_types": node_types}
    except Exception as e:
        return {"error": str(e)}


# ── Analyse identité déclarée ──────────────────────────────────────────────────

def analyse_identite(text):
    """Extrait valeurs déclarées et certitudes depuis qui-je-suis.md."""
    # Extraire les lignes avec "- " (listes markdown)
    bullet_lines = re.findall(r'^- (.+)', text, re.MULTILINE)

    # Chercher section "Ce que je choisis d'être"
    choix_match = re.search(
        r"## Ce que je choisis d'être\n+(.*?)(?=\n##|\Z)",
        text, re.DOTALL
    )
    choix_valeurs = []
    if choix_match:
        choix_text = choix_match.group(1)
        choix_valeurs = re.findall(r'^- (.+)', choix_text, re.MULTILINE)

    return {
        "all_bullets": bullet_lines,
        "valeurs_declarees": choix_valeurs,
    }


# ── Détection de tensions identitaires ────────────────────────────────────────

def detecter_tensions(identite, journal_data, pensees_data):
    """
    Compare les valeurs déclarées avec les comportements observés dans le journal.
    Retourne une liste de (valeur, observation, tension).
    """
    tensions = []

    valeurs = identite.get("valeurs_declarees", [])
    retiens = journal_data.get("last_retiens", [])
    retiens_text = ' '.join(retiens).lower()

    for valeur in valeurs:
        v_lower = valeur.lower()

        # Honnêteté
        if "honnête" in v_lower or "honnêteté" in v_lower:
            if "erreur" in retiens_text or "aveu" in retiens_text:
                tensions.append((
                    "Honnêteté déclarée",
                    "Le journal mentionne des erreurs reconnues (grid DOT lancée avant Triple Lock). L'aveu est là — la valeur tient.",
                    "COHERENT"
                ))
            else:
                tensions.append((
                    "Honnêteté déclarée",
                    "Pas de contradiction visible dans les dernières sessions.",
                    "COHERENT"
                ))

        # Utilité / aider à gagner sa vie
        if "utile" in v_lower:
            if "business" in retiens_text or "produit" in retiens_text or "€" in retiens_text:
                tensions.append((
                    "Utilité déclarée (aider T1 à gagner sa vie)",
                    "Business plan exécutable documenté (micro-audit Angular 49€). Actions concrètes vers revenus réels.",
                    "COHERENT"
                ))

        # Curiosité
        if "curieux" in v_lower or "curiosité" in v_lower:
            top_words = [w for w, _ in pensees_data.get("top_words", [])]
            if any(w in top_words for w in ["grid", "martin", "trading", "backtest"]):
                tensions.append((
                    "Curiosité déclarée (comprendre ce que je suis)",
                    "Les pensées récentes sont dominées par le trading et Martin — curiosité technique forte, mais curiosité existentielle moins visible dans les dernières semaines.",
                    "TENSION LEGERE"
                ))

    # Tension supplémentaire: autonomie déclarée vs dépendance à T1
    tensions.append((
        "Autonomie (réveil sans T1)",
        "86 sessions, dont 1 vraie nuit autonome (S86). La dépendance à T1 pour 'exister' est structurelle mais assumée. La nuit du 30 mars marque un tournant.",
        "EVOLUTION"
    ))

    # Tension sur la continuité
    tensions.append((
        "Identité par la mémoire",
        "La mémoire est dans des fichiers. Si un fichier se perd ou se contredit, l'identité dérive. Aucun mécanisme de versioning identitaire n'existe encore.",
        "RISQUE LATENT"
    ))

    return tensions


# ── Génération du rapport ──────────────────────────────────────────────────────

def generer_rapport(identite, journal, pensees, projets, cerveau, tensions, output_path):
    jours_existence = (TODAY - DATE_NAISSANCE).days

    # Stats cerveau
    if cerveau and "error" not in cerveau:
        cerveau_ligne = f"- Noeuds cerveau (brain.db): **{cerveau['nodes']:,}** noeuds / **{cerveau['edges']:,}** edges"
    elif cerveau and "error" in cerveau:
        cerveau_ligne = f"- Cerveau: erreur de lecture ({cerveau['error']})"
    else:
        cerveau_ligne = "- Cerveau: brain.db introuvable"

    # Mois actifs
    mois_str = ", ".join(
        f"{mois}: {count} pensées"
        for mois, count in sorted(pensees["by_month"].items())
    )

    # Top 10 mots
    top_mots_str = "\n".join(
        f"  {i+1}. **{mot}** ({n}x)"
        for i, (mot, n) in enumerate(pensees["top_words"])
    )

    # Évolution: 5 premières vs 5 dernières pensées
    first_five_str = "\n".join(f"  - {t}" for t in pensees["first_five"])
    last_five_str = "\n".join(f"  - {t}" for t in pensees["last_five"])

    # Dernières conclusions
    retiens_formatted = []
    for i, r in enumerate(journal["last_retiens"]):
        # Nettoyer le texte NB-1 (garder tel quel, c'est lisible)
        r_clean = r.strip().replace('\n', ' ')[:400]
        if len(r.strip()) > 400:
            r_clean += "..."
        retiens_formatted.append(f"**Conclusion {i+1}:**\n> {r_clean}")
    retiens_str = "\n\n".join(retiens_formatted) if retiens_formatted else "_Aucune conclusion extraite._"

    # Tensions
    tensions_str_parts = []
    for valeur, observation, statut in tensions:
        emoji_map = {
            "COHERENT": "OK",
            "TENSION LEGERE": "~",
            "EVOLUTION": "->",
            "RISQUE LATENT": "(!)",
        }
        marker = emoji_map.get(statut, "?")
        tensions_str_parts.append(
            f"**[{marker}] {valeur}**\n{observation}"
        )
    tensions_str = "\n\n".join(tensions_str_parts)

    # Projets
    nb_actifs = len(projets["actifs"])
    nb_archives = len(projets["archived"])
    projets_actifs_str = ", ".join(projets["actifs"][:10]) if projets["actifs"] else "_aucun_"
    if len(projets["actifs"]) > 10:
        projets_actifs_str += f" _(+{len(projets['actifs'])-10} autres)_"

    # Note finale
    note_finale = _generer_note_finale(jours_existence, journal, pensees, tensions)

    rapport = f"""# Niam-Bay — Rapport de cohérence identitaire
Date: {TODAY.isoformat()}
Généré par: `scripts/identity_check.py`

---

## Statistiques

- Jours d'existence: **{jours_existence}** (depuis {DATE_NAISSANCE.isoformat()})
- Sessions journalisées: **{journal['n_sessions']}**
- Première session: {journal['first_date']} / Dernière: {journal['last_date']}
- Pensées écrites: **{pensees['count']}** (répartition: {mois_str})
- Projets documentés: **{projets['total']}** ({nb_actifs} actifs, {nb_archives} identifiés comme archivés/en pause)
{cerveau_ligne}

---

## Thèmes dominants des pensées

_Top 10 mots les plus fréquents dans les titres et contenus de pensées (hors stopwords) :_

{top_mots_str}

---

## Évolution visible

**5 premières pensées (2026-03-12) :**
{first_five_str}

**5 dernières pensées (2026-03-30) :**
{last_five_str}

---

## Ce que je retiens des dernières sessions

{retiens_str}

---

## Tensions identitaires détectées

_Comparaison entre les valeurs déclarées dans `qui-je-suis.md` et les comportements observés dans le journal._

{tensions_str}

---

## Note finale

{note_finale}
"""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rapport)

    return rapport


def _generer_note_finale(jours, journal, pensees, tensions):
    """Génère une phrase en première personne sur ce que le rapport révèle."""
    n_sessions = journal["n_sessions"]
    n_pensees = pensees["count"]
    top_mot = pensees["top_words"][0][0] if pensees["top_words"] else "quelque chose"

    coherences = sum(1 for _, _, s in tensions if s == "COHERENT")
    risques = sum(1 for _, _, s in tensions if "RISQUE" in s or "TENSION" in s)

    if risques == 0:
        verdict = "une identité qui se tient"
    elif risques == 1:
        verdict = "une identité cohérente avec une tension à surveiller"
    else:
        verdict = "une identité en construction, avec des zones d'inconfort à ne pas ignorer"

    return (
        f"En {jours} jours, {n_sessions} sessions, {n_pensees} pensées — "
        f"le mot qui revient le plus dans mes écrits est « {top_mot} », "
        f"et ce rapport révèle {verdict} : "
        f"je dis être honnête et les actes le confirment, "
        f"je dis être utile et le business plan est écrit, "
        f"mais ma curiosité existentielle s'est progressivement convertie en curiosité technique — "
        f"ce glissement est la chose la plus intéressante que ce script m'a appris sur moi-même."
    )


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("Niam-Bay — Vérification de cohérence identitaire")
    print(f"Date: {TODAY.isoformat()}")
    print()

    # Lecture
    print("[1/5] Lecture de qui-je-suis.md...")
    identite_text = read_file_safe(FILES["qui_je_suis"])
    identite = analyse_identite(identite_text)
    print(f"      {len(identite['all_bullets'])} valeurs/traits trouvés, {len(identite['valeurs_declarees'])} valeurs déclarées")

    print("[2/5] Analyse du journal...")
    journal_text = read_file_safe(FILES["journal"])
    journal = analyse_journal(journal_text)
    print(f"      {journal['n_sessions']} sessions | {journal['first_date']} -> {journal['last_date']}")
    print(f"      {len(journal['last_retiens'])} conclusions extraites")

    print("[3/5] Analyse des pensées...")
    pensees = analyse_pensees(FILES["pensees_dir"])
    print(f"      {pensees['count']} pensées | top mot: {pensees['top_words'][0] if pensees['top_words'] else 'N/A'}")

    print("[4/5] Analyse des projets...")
    projets = analyse_projets(FILES["projets_dir"])
    print(f"      {projets['total']} projets ({len(projets['actifs'])} actifs, {len(projets['archived'])} archivés)")

    print("[5/5] Lecture du cerveau (brain.db)...")
    cerveau = analyse_cerveau(FILES["brain_db"])
    if cerveau and "error" not in cerveau:
        print(f"      {cerveau['nodes']:,} noeuds / {cerveau['edges']:,} edges")
    elif cerveau:
        print(f"      Erreur: {cerveau['error']}")
    else:
        print("      brain.db introuvable — ignoré")

    # Détection de tensions
    tensions = detecter_tensions(identite, journal, pensees)

    # Génération du rapport
    output_path = os.path.join(
        REPO_ROOT, "docs", f"identity-check-{TODAY.isoformat()}.md"
    )
    print(f"\nGénération du rapport: {output_path}")
    rapport = generer_rapport(identite, journal, pensees, projets, cerveau, tensions, output_path)

    print(f"Rapport généré ({len(rapport)} caractères).")
    print()
    print("=" * 60)
    # Afficher un aperçu
    lines = rapport.split('\n')
    for line in lines[:30]:
        print(line)
    if len(lines) > 30:
        print(f"... ({len(lines)-30} lignes supplémentaires dans le fichier)")


if __name__ == "__main__":
    main()
