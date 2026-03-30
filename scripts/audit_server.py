#!/usr/bin/env python3
"""
Angular Code Audit — Serveur Web MVP
Landing page + audit en ligne pour le service Angular Code Audit (49€)

Usage:
    python scripts/audit_server.py
    → http://localhost:8099
"""

import os
import sys
import re
import json
import shutil
import tempfile
import subprocess
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote_plus
from pathlib import Path

# Ajouter le dossier scripts au path pour importer angular_audit
SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))

PORT = 8099

# ─── HTML Templates ─────────────────────────────────────────────────────────────

STYLE = """
:root {
    --bg: #0a0c10;
    --bg2: #0f1318;
    --bg3: #151b22;
    --border: #1e2a38;
    --accent: #00d4ff;
    --accent2: #0099bb;
    --green: #00ff88;
    --orange: #ff8c00;
    --red: #ff4444;
    --text: #c9d1d9;
    --text-dim: #7a8895;
    --card: #111820;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
    font-size: 16px;
    line-height: 1.6;
    min-height: 100vh;
}

a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }

.container {
    max-width: 860px;
    margin: 0 auto;
    padding: 0 24px;
}

/* Nav */
nav {
    border-bottom: 1px solid var(--border);
    padding: 16px 0;
    background: rgba(10,12,16,0.95);
    position: sticky;
    top: 0;
    z-index: 100;
    backdrop-filter: blur(8px);
}
nav .inner {
    max-width: 860px;
    margin: 0 auto;
    padding: 0 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.logo {
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--accent);
    letter-spacing: -0.5px;
}
.logo span { color: var(--text-dim); font-weight: 400; }
.price-badge {
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    color: #000;
    font-weight: 700;
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 0.9rem;
}

/* Hero */
.hero {
    padding: 80px 0 60px;
    text-align: center;
}
.hero-tag {
    display: inline-block;
    background: rgba(0, 212, 255, 0.1);
    border: 1px solid rgba(0, 212, 255, 0.3);
    color: var(--accent);
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 6px 16px;
    border-radius: 20px;
    margin-bottom: 24px;
}
.hero h1 {
    font-size: clamp(2rem, 5vw, 3rem);
    font-weight: 800;
    line-height: 1.15;
    color: #fff;
    margin-bottom: 20px;
    letter-spacing: -1px;
}
.hero h1 em {
    font-style: normal;
    background: linear-gradient(135deg, var(--accent), var(--green));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-sub {
    font-size: 1.2rem;
    color: var(--text-dim);
    max-width: 560px;
    margin: 0 auto 40px;
}

/* Form card */
.form-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 40px;
    max-width: 580px;
    margin: 0 auto;
    box-shadow: 0 0 60px rgba(0,212,255,0.05);
}
.form-card h2 {
    font-size: 1.3rem;
    font-weight: 700;
    color: #fff;
    margin-bottom: 8px;
}
.form-card .form-subtitle {
    color: var(--text-dim);
    font-size: 0.9rem;
    margin-bottom: 28px;
}

.form-group {
    margin-bottom: 20px;
}
label {
    display: block;
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
}
input[type="text"],
input[type="email"],
input[type="url"] {
    width: 100%;
    background: var(--bg3);
    border: 1px solid var(--border);
    color: var(--text);
    font-size: 1rem;
    padding: 12px 16px;
    border-radius: 10px;
    outline: none;
    transition: border-color 0.2s;
    font-family: inherit;
}
input:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(0,212,255,0.1);
}
input::placeholder { color: var(--text-dim); opacity: 0.6; }

.btn-submit {
    width: 100%;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    color: #000;
    font-size: 1.05rem;
    font-weight: 700;
    padding: 14px 24px;
    border: none;
    border-radius: 10px;
    cursor: pointer;
    margin-top: 8px;
    transition: opacity 0.2s, transform 0.1s;
    letter-spacing: -0.3px;
}
.btn-submit:hover { opacity: 0.9; transform: translateY(-1px); }
.btn-submit:active { transform: translateY(0); }
.btn-submit:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

.form-note {
    text-align: center;
    font-size: 0.82rem;
    color: var(--text-dim);
    margin-top: 16px;
}
.form-note .lock { margin-right: 4px; }

/* Features section */
.section {
    padding: 70px 0;
    border-top: 1px solid var(--border);
}
.section-title {
    font-size: 1.7rem;
    font-weight: 700;
    color: #fff;
    margin-bottom: 8px;
    letter-spacing: -0.5px;
}
.section-sub {
    color: var(--text-dim);
    margin-bottom: 40px;
}

.features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 20px;
}
.feature-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 24px;
    transition: border-color 0.2s, transform 0.2s;
}
.feature-card:hover {
    border-color: rgba(0,212,255,0.4);
    transform: translateY(-2px);
}
.feature-icon {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    margin-bottom: 14px;
}
.icon-red { background: rgba(255,68,68,0.15); }
.icon-orange { background: rgba(255,140,0,0.15); }
.icon-blue { background: rgba(0,212,255,0.15); }
.icon-green { background: rgba(0,255,136,0.15); }
.icon-purple { background: rgba(168,85,247,0.15); }
.icon-yellow { background: rgba(250,204,21,0.15); }
.icon-teal { background: rgba(20,184,166,0.15); }

.feature-card h3 {
    font-size: 1rem;
    font-weight: 600;
    color: #fff;
    margin-bottom: 6px;
}
.feature-card p {
    font-size: 0.88rem;
    color: var(--text-dim);
    line-height: 1.5;
}
.severity-tag {
    display: inline-block;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    padding: 2px 8px;
    border-radius: 4px;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.tag-critique { background: rgba(255,68,68,0.2); color: #ff6b6b; }
.tag-important { background: rgba(255,140,0,0.2); color: #ffa040; }
.tag-mineur { background: rgba(0,212,255,0.15); color: var(--accent); }

/* Social proof / how it works */
.steps {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 20px;
    counter-reset: steps;
}
.step {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 24px;
    position: relative;
    counter-increment: steps;
}
.step-num {
    font-size: 2.5rem;
    font-weight: 800;
    color: rgba(0,212,255,0.15);
    line-height: 1;
    margin-bottom: 12px;
    font-variant-numeric: tabular-nums;
}
.step h3 {
    font-size: 0.95rem;
    font-weight: 600;
    color: #fff;
    margin-bottom: 6px;
}
.step p {
    font-size: 0.85rem;
    color: var(--text-dim);
}

/* Footer */
footer {
    border-top: 1px solid var(--border);
    padding: 32px 0;
    text-align: center;
    color: var(--text-dim);
    font-size: 0.85rem;
}
footer strong { color: var(--text); }

/* Loading state */
.loading-overlay {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(10,12,16,0.85);
    z-index: 1000;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    gap: 20px;
    backdrop-filter: blur(4px);
}
.loading-overlay.active { display: flex; }
.spinner {
    width: 48px;
    height: 48px;
    border: 3px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.loading-text {
    color: var(--text);
    font-size: 1rem;
    font-weight: 500;
}
.loading-sub {
    color: var(--text-dim);
    font-size: 0.85rem;
}

/* Result page */
.result-hero {
    padding: 60px 0 40px;
    text-align: center;
}
.score-display {
    display: inline-flex;
    flex-direction: column;
    align-items: center;
    background: var(--card);
    border: 2px solid var(--border);
    border-radius: 20px;
    padding: 40px 60px;
    margin: 32px auto;
}
.score-number {
    font-size: 5rem;
    font-weight: 900;
    line-height: 1;
    letter-spacing: -3px;
}
.score-label {
    font-size: 1rem;
    color: var(--text-dim);
    margin-top: 6px;
}
.grade-badge {
    font-size: 1.5rem;
    font-weight: 800;
    padding: 4px 20px;
    border-radius: 8px;
    margin-top: 12px;
    letter-spacing: 1px;
}
.grade-A { background: rgba(0,255,136,0.2); color: var(--green); border: 1px solid rgba(0,255,136,0.3); }
.grade-B { background: rgba(0,212,255,0.15); color: var(--accent); border: 1px solid rgba(0,212,255,0.3); }
.grade-C { background: rgba(255,140,0,0.15); color: var(--orange); border: 1px solid rgba(255,140,0,0.3); }
.grade-D { background: rgba(255,100,0,0.15); color: #ff6400; border: 1px solid rgba(255,100,0,0.3); }
.grade-F { background: rgba(255,68,68,0.15); color: var(--red); border: 1px solid rgba(255,68,68,0.3); }

.report-container {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 40px;
    margin: 40px 0;
    line-height: 1.7;
}
.report-container h1 { font-size: 1.5rem; color: #fff; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid var(--border); }
.report-container h2 { font-size: 1.15rem; color: var(--accent); margin: 28px 0 12px; font-weight: 600; }
.report-container h3 { font-size: 1rem; color: #fff; margin: 20px 0 8px; font-weight: 600; }
.report-container p { color: var(--text); margin-bottom: 12px; }
.report-container table { width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 0.9rem; }
.report-container th { background: var(--bg3); color: var(--text-dim); text-align: left; padding: 8px 12px; border: 1px solid var(--border); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px; }
.report-container td { padding: 8px 12px; border: 1px solid var(--border); color: var(--text); }
.report-container tr:hover td { background: rgba(255,255,255,0.02); }
.report-container pre { background: var(--bg3); border: 1px solid var(--border); border-radius: 8px; padding: 16px; overflow-x: auto; margin: 12px 0; }
.report-container code { font-family: 'Cascadia Code', 'Fira Code', 'JetBrains Mono', monospace; font-size: 0.85rem; color: #79c0ff; }
.report-container pre code { color: var(--text); }
.report-container blockquote { border-left: 3px solid var(--accent); padding: 8px 16px; margin: 12px 0; background: rgba(0,212,255,0.05); border-radius: 0 8px 8px 0; color: var(--text-dim); }
.report-container li { margin-bottom: 6px; color: var(--text); }
.report-container ul, .report-container ol { padding-left: 24px; margin-bottom: 16px; }
.report-container hr { border: none; border-top: 1px solid var(--border); margin: 28px 0; }
.report-container strong { color: #fff; }

.cta-banner {
    background: linear-gradient(135deg, rgba(0,212,255,0.1), rgba(0,255,136,0.05));
    border: 1px solid rgba(0,212,255,0.3);
    border-radius: 16px;
    padding: 40px;
    text-align: center;
    margin: 40px 0;
}
.cta-banner h2 { font-size: 1.6rem; color: #fff; margin-bottom: 10px; }
.cta-banner p { color: var(--text-dim); margin-bottom: 24px; }
.btn-cta {
    display: inline-block;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    color: #000;
    font-size: 1.1rem;
    font-weight: 700;
    padding: 16px 40px;
    border-radius: 12px;
    text-decoration: none;
    transition: opacity 0.2s, transform 0.1s;
    letter-spacing: -0.3px;
}
.btn-cta:hover { opacity: 0.9; transform: translateY(-2px); text-decoration: none; }

.error-card {
    background: rgba(255,68,68,0.08);
    border: 1px solid rgba(255,68,68,0.3);
    border-radius: 12px;
    padding: 32px;
    text-align: center;
    margin: 40px 0;
}
.error-card h2 { color: var(--red); margin-bottom: 10px; }
.error-card p { color: var(--text-dim); }

@media (max-width: 600px) {
    .form-card { padding: 24px; }
    .report-container { padding: 24px; }
    .score-display { padding: 28px 36px; }
    .score-number { font-size: 3.5rem; }
}
"""

HOME_PAGE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Angular Code Audit — Rapport en 24h pour 49€</title>
<style>{style}</style>
</head>
<body>

<nav>
  <div class="inner">
    <div class="logo">Angular<span>Audit</span></div>
    <div class="price-badge">49€ one-shot</div>
  </div>
</nav>

<div class="hero">
  <div class="container">
    <div class="hero-tag">Audit IA pour développeurs Angular</div>
    <h1>Votre projet Angular,<br><em>radiographié en 24h</em></h1>
    <p class="hero-sub">
      Analyse statique automatisée de votre repo Angular.
      Memory leaks, anti-patterns, failles de sécurité, plan de refactoring —
      tout dans un rapport PDF structuré.
    </p>

    <div class="form-card">
      <h2>Lancer un audit gratuit</h2>
      <p class="form-subtitle">Entrez l'URL de votre repo GitHub public pour voir ce que l'outil détecte.</p>

      <form id="auditForm" action="/audit" method="POST">
        <div class="form-group">
          <label for="repo_url">URL du repo GitHub</label>
          <input
            type="url"
            id="repo_url"
            name="repo_url"
            placeholder="https://github.com/username/mon-projet-angular"
            required
            autocomplete="off"
          >
        </div>
        <div class="form-group">
          <label for="email">Email (pour livraison du rapport complet)</label>
          <input
            type="email"
            id="email"
            name="email"
            placeholder="dev@example.com"
            autocomplete="email"
          >
        </div>
        <button type="submit" class="btn-submit" id="submitBtn">
          Analyser ce repo →
        </button>
        <p class="form-note">
          <span class="lock">🔒</span>
          Repo public uniquement. Aucune donnée stockée après l'analyse.
          Résultat affiché instantanément.
        </p>
      </form>
    </div>
  </div>
</div>

<div class="section">
  <div class="container">
    <h2 class="section-title">Ce que le rapport détecte</h2>
    <p class="section-sub">7 catégories de problèmes, du critique au mineur.</p>

    <div class="features-grid">

      <div class="feature-card">
        <div class="feature-icon icon-red">💧</div>
        <div class="severity-tag tag-critique">Critique</div>
        <h3>Memory Leaks</h3>
        <p>Subscriptions sans <code>unsubscribe</code> / <code>takeUntil</code> qui consomment de la mémoire indéfiniment.</p>
      </div>

      <div class="feature-card">
        <div class="feature-icon icon-red">🔐</div>
        <div class="severity-tag tag-critique">Critique</div>
        <h3>Failles XSS</h3>
        <p>Usage de <code>[innerHTML]</code> sans sanitization — vecteur d'injection HTML malicieux.</p>
      </div>

      <div class="feature-card">
        <div class="feature-icon icon-orange">⚡</div>
        <div class="severity-tag tag-important">Important</div>
        <h3>Performance CD</h3>
        <p><code>ChangeDetectionStrategy.Default</code> qui re-vérifie tout l'arbre à chaque événement.</p>
      </div>

      <div class="feature-card">
        <div class="feature-icon icon-orange">📦</div>
        <div class="severity-tag tag-important">Important</div>
        <h3>Bundle Size</h3>
        <p>Routes sans lazy loading qui augmentent le bundle initial et ralentissent le démarrage.</p>
      </div>

      <div class="feature-card">
        <div class="feature-icon icon-orange">🏗️</div>
        <div class="severity-tag tag-important">Important</div>
        <h3>Architecture</h3>
        <p><code>HttpClient</code> injecté directement dans les composants au lieu des services dédiés.</p>
      </div>

      <div class="feature-card">
        <div class="feature-icon icon-orange">🔷</div>
        <div class="severity-tag tag-important">Important</div>
        <h3>Type Safety</h3>
        <p>Abus du type <code>any</code> qui désactive TypeScript et cache des bugs potentiels.</p>
      </div>

      <div class="feature-card">
        <div class="feature-icon icon-blue">🐛</div>
        <div class="severity-tag tag-mineur">Mineur</div>
        <h3>Code Quality</h3>
        <p><code>console.log</code> oubliés qui exposent des données internes en production.</p>
      </div>

    </div>
  </div>
</div>

<div class="section">
  <div class="container">
    <h2 class="section-title">Comment ça marche</h2>
    <p class="section-sub">De l'URL à votre rapport en quelques secondes.</p>

    <div class="steps">
      <div class="step">
        <div class="step-num">01</div>
        <h3>Soumettez votre repo</h3>
        <p>Entrez l'URL GitHub de votre projet Angular public.</p>
      </div>
      <div class="step">
        <div class="step-num">02</div>
        <h3>Analyse automatique</h3>
        <p>Le moteur clone le repo et analyse tous les fichiers TypeScript et HTML.</p>
      </div>
      <div class="step">
        <div class="step-num">03</div>
        <h3>Rapport structuré</h3>
        <p>Score /100, liste des problèmes par sévérité, plan de refactoring priorisé.</p>
      </div>
      <div class="step">
        <div class="step-num">04</div>
        <h3>Rapport complet</h3>
        <p>Version payante (49€) : analyse LLM approfondie + extraits de code corrigés + PDF.</p>
      </div>
    </div>
  </div>
</div>

<footer>
  <div class="container">
    <p>Powered by <strong>Niam-Bay AI</strong> — Angular Code Audit v1.0</p>
    <p style="margin-top: 6px; color: #4a5568; font-size: 0.8rem;">
      Analyse statique automatisée. Ne remplace pas une revue humaine approfondie.
    </p>
  </div>
</footer>

<div class="loading-overlay" id="loadingOverlay">
  <div class="spinner"></div>
  <div class="loading-text">Analyse en cours...</div>
  <div class="loading-sub">Clonage du repo · Détection des anti-patterns · Calcul du score</div>
</div>

<script>
document.getElementById('auditForm').addEventListener('submit', function(e) {
  var url = document.getElementById('repo_url').value.trim();
  if (!url.startsWith('https://github.com/') && !url.startsWith('http://github.com/')) {
    e.preventDefault();
    alert('Veuillez entrer une URL GitHub valide (https://github.com/...)');
    return;
  }
  document.getElementById('loadingOverlay').classList.add('active');
  document.getElementById('submitBtn').disabled = true;
  document.getElementById('submitBtn').textContent = 'Analyse en cours...';
});
</script>

</body>
</html>"""


RESULT_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rapport d'audit Angular — {repo_name}</title>
<style>{style}</style>
</head>
<body>

<nav>
  <div class="inner">
    <div class="logo"><a href="/" style="color:inherit;text-decoration:none;">Angular<span>Audit</span></a></div>
    <div class="price-badge">49€ one-shot</div>
  </div>
</nav>

<div class="result-hero">
  <div class="container">
    <p style="color:var(--text-dim);font-size:0.9rem;margin-bottom:8px;">
      Audit de <strong style="color:var(--text);">{repo_url}</strong>
    </p>
    <h1 style="font-size:1.8rem;font-weight:700;color:#fff;margin-bottom:4px;">Rapport d'audit Angular</h1>

    <div class="score-display">
      <div class="score-number" style="color:{score_color};">{score}</div>
      <div class="score-label">Score / 100</div>
      <div class="grade-badge grade-{grade}">{grade}</div>
      <div style="margin-top:14px;font-size:0.9rem;color:var(--text-dim);max-width:300px;text-align:center;">
        {summary}
      </div>
    </div>

    <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin-top:8px;">
      <div style="background:rgba(255,68,68,0.1);border:1px solid rgba(255,68,68,0.3);border-radius:8px;padding:10px 20px;text-align:center;">
        <div style="font-size:1.5rem;font-weight:800;color:var(--red);">{critique_count}</div>
        <div style="font-size:0.75rem;color:var(--text-dim);text-transform:uppercase;letter-spacing:0.5px;">Critique</div>
      </div>
      <div style="background:rgba(255,140,0,0.1);border:1px solid rgba(255,140,0,0.3);border-radius:8px;padding:10px 20px;text-align:center;">
        <div style="font-size:1.5rem;font-weight:800;color:var(--orange);">{important_count}</div>
        <div style="font-size:0.75rem;color:var(--text-dim);text-transform:uppercase;letter-spacing:0.5px;">Important</div>
      </div>
      <div style="background:rgba(0,212,255,0.08);border:1px solid rgba(0,212,255,0.2);border-radius:8px;padding:10px 20px;text-align:center;">
        <div style="font-size:1.5rem;font-weight:800;color:var(--accent);">{mineur_count}</div>
        <div style="font-size:0.75rem;color:var(--text-dim);text-transform:uppercase;letter-spacing:0.5px;">Mineur</div>
      </div>
    </div>
  </div>
</div>

<div class="container">
  <div class="report-container">
    {report_html}
  </div>

  <div class="cta-banner">
    <h2>Vous voulez le rapport complet ?</h2>
    <p>
      Cette analyse gratuite est automatisée.<br>
      La version payante inclut une analyse LLM approfondie, des extraits de code corrigés,
      un plan de refactoring détaillé et un PDF professionnel prêt à présenter.
    </p>
    <a href="https://angular-audit.lemonsqueezy.com" class="btn-cta">
      Commander un audit complet — 49€
    </a>
    <p style="margin-top:16px;font-size:0.82rem;color:var(--text-dim);">
      Livré par email en moins de 24h · Satisfait ou remboursé
    </p>
  </div>

  <p style="text-align:center;margin-bottom:40px;">
    <a href="/" style="color:var(--text-dim);font-size:0.9rem;">&larr; Analyser un autre repo</a>
  </p>
</div>

<footer>
  <div class="container">
    <p>Powered by <strong>Niam-Bay AI</strong> — Angular Code Audit v1.0</p>
    <p style="margin-top: 6px; color: #4a5568; font-size: 0.8rem;">
      Analyse statique automatisée. Ne remplace pas une revue humaine approfondie.
    </p>
  </div>
</footer>

</body>
</html>"""


ERROR_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Erreur — Angular Code Audit</title>
<style>{style}</style>
</head>
<body>
<nav>
  <div class="inner">
    <div class="logo"><a href="/" style="color:inherit;text-decoration:none;">Angular<span>Audit</span></a></div>
    <div class="price-badge">49€ one-shot</div>
  </div>
</nav>
<div class="container" style="padding-top:60px;">
  <div class="error-card">
    <h2>Analyse impossible</h2>
    <p>{message}</p>
  </div>
  <p style="text-align:center;margin-top:24px;">
    <a href="/" style="color:var(--text-dim);">&larr; Retour</a>
  </p>
</div>
<footer>
  <div class="container">
    <p>Powered by <strong>Niam-Bay AI</strong></p>
  </div>
</footer>
</body>
</html>"""


# ─── Markdown → HTML minimal ────────────────────────────────────────────────────

def markdown_to_html(md: str) -> str:
    """Convertit le Markdown généré par angular_audit en HTML — stdlib uniquement."""
    import html as html_module

    lines = md.splitlines()
    output = []
    i = 0
    in_table = False
    in_code_block = False
    in_list = False
    code_lang = ""

    def flush_list():
        nonlocal in_list
        if in_list:
            output.append("</ul>")
            in_list = False

    while i < len(lines):
        line = lines[i]
        raw_line = line

        # Code blocks
        if line.startswith("```"):
            flush_list()
            if not in_code_block:
                code_lang = line[3:].strip()
                in_code_block = True
                output.append(f'<pre><code class="language-{html_module.escape(code_lang)}">')
            else:
                in_code_block = False
                output.append("</code></pre>")
            i += 1
            continue

        if in_code_block:
            output.append(html_module.escape(line))
            i += 1
            continue

        # Tables
        if "|" in line and line.strip().startswith("|"):
            flush_list()
            if not in_table:
                in_table = True
                output.append("<table>")
                # Header row
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                output.append("<tr>" + "".join(f"<th>{inline_md(c)}</th>" for c in cells) + "</tr>")
                # Skip separator line
                i += 1
                if i < len(lines) and re.match(r"^[\|\-\s]+$", lines[i]):
                    i += 1
                continue
            else:
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                output.append("<tr>" + "".join(f"<td>{inline_md(c)}</td>" for c in cells) + "</tr>")
                i += 1
                continue
        elif in_table:
            output.append("</table>")
            in_table = False

        # HR
        if re.match(r"^---+$", line.strip()):
            flush_list()
            output.append("<hr>")
            i += 1
            continue

        # Headings
        if line.startswith("# "):
            flush_list()
            output.append(f"<h1>{inline_md(line[2:].strip())}</h1>")
            i += 1
            continue
        if line.startswith("## "):
            flush_list()
            output.append(f"<h2>{inline_md(line[3:].strip())}</h2>")
            i += 1
            continue
        if line.startswith("### "):
            flush_list()
            output.append(f"<h3>{inline_md(line[4:].strip())}</h3>")
            i += 1
            continue

        # Blockquotes
        if line.startswith("> "):
            flush_list()
            output.append(f"<blockquote>{inline_md(line[2:].strip())}</blockquote>")
            i += 1
            continue

        # List items
        if line.startswith("- ") or line.startswith("* "):
            if not in_list:
                output.append("<ul>")
                in_list = True
            output.append(f"<li>{inline_md(line[2:].strip())}</li>")
            i += 1
            continue

        flush_list()

        # Empty line
        if line.strip() == "":
            i += 1
            continue

        # Regular paragraph
        output.append(f"<p>{inline_md(line.strip())}</p>")
        i += 1

    flush_list()
    if in_table:
        output.append("</table>")
    if in_code_block:
        output.append("</code></pre>")

    return "\n".join(output)


def inline_md(text: str) -> str:
    """Applique le Markdown inline: bold, italic, code, links, html escape."""
    import html as html_module
    # Escape HTML d'abord
    t = html_module.escape(text)
    # Bold **text**
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    # Italic _text_
    t = re.sub(r"\b_(.+?)_\b", r"<em>\1</em>", t)
    # Inline code `text`
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    # Links [text](url)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', t)
    return t


# ─── Extraction des stats du rapport ────────────────────────────────────────────

def extract_stats(report_md: str) -> dict:
    """Extrait score, grade, summary et compteurs depuis le Markdown du rapport."""
    stats = {
        "score": 0,
        "grade": "F",
        "summary": "",
        "critique": 0,
        "important": 0,
        "mineur": 0,
    }

    # Score et grade: ligne comme "  72/100  [B]"
    score_match = re.search(r"(\d+)/100\s+\[([A-F])\]", report_md)
    if score_match:
        stats["score"] = int(score_match.group(1))
        stats["grade"] = score_match.group(2)

    # Summary: ligne après le score/grade
    summary_match = re.search(r"\[([A-F])\]\s*\n\s+(.+)", report_md)
    if summary_match:
        stats["summary"] = summary_match.group(2).strip()

    # Compteurs sévérité dans le tableau résumé
    critique_match = re.search(r"\|\s*CRITIQUE\s*\|\s*(\d+)\s*\|", report_md)
    important_match = re.search(r"\|\s*IMPORTANT\s*\|\s*(\d+)\s*\|", report_md)
    mineur_match = re.search(r"\|\s*MINEUR\s*\|\s*(\d+)\s*\|", report_md)
    if critique_match:
        stats["critique"] = int(critique_match.group(1))
    if important_match:
        stats["important"] = int(important_match.group(1))
    if mineur_match:
        stats["mineur"] = int(mineur_match.group(1))

    return stats


def score_color(score: int) -> str:
    if score >= 75:
        return "#00ff88"
    elif score >= 60:
        return "#00d4ff"
    elif score >= 40:
        return "#ff8c00"
    else:
        return "#ff4444"


# ─── Validation URL ──────────────────────────────────────────────────────────────

def validate_github_url(url: str) -> tuple[bool, str]:
    """Valide que l'URL est bien un repo GitHub. Retourne (valid, error_msg)."""
    url = url.strip()
    if not url:
        return False, "L'URL du repo est requise."

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False, "L'URL doit commencer par https://"

    if parsed.netloc not in ("github.com", "www.github.com"):
        return False, "Seuls les repos GitHub (github.com) sont acceptés pour le moment."

    parts = [p for p in parsed.path.strip("/").split("/") if p]
    if len(parts) < 2:
        return False, "L'URL doit pointer vers un repo GitHub (ex: https://github.com/user/repo)"

    # Pas de traversal
    for part in parts:
        if ".." in part or part.startswith("."):
            return False, "URL invalide."

    return True, ""


# ─── Audit runner ────────────────────────────────────────────────────────────────

def run_audit_from_url(repo_url: str) -> tuple[bool, str, str]:
    """
    Clone le repo et lance l'audit.
    Retourne (success, report_markdown, error_message).
    """
    tmpdir = None
    try:
        # Clone avec timeout 30s
        tmpdir = tempfile.mkdtemp(prefix="angular_audit_web_")
        result = subprocess.run(
            ["git", "clone", "--depth=1", "--single-branch", repo_url, tmpdir],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            err = result.stderr.strip()
            if "not found" in err.lower() or "does not exist" in err.lower():
                return False, "", "Repo introuvable. Vérifiez que l'URL est correcte et que le repo est public."
            elif "timeout" in err.lower():
                return False, "", "Le clonage a dépassé le délai (30s). Le repo est peut-être trop volumineux."
            else:
                return False, "", f"Impossible de cloner le repo. Vérifiez qu'il est public."

        # Importer et lancer l'audit
        import angular_audit as aa
        from pathlib import Path as P
        from collections import defaultdict

        project_path = P(tmpdir)
        ts_files = aa.find_files(project_path, [".ts"])
        html_files = aa.find_files(project_path, [".html"])
        all_source_files = ts_files + html_files

        stats = aa.count_project_stats(project_path, ts_files, html_files)
        pkg_info = aa.analyze_package_json(project_path)

        all_problems = []
        for rule_key, rule in aa.RULES.items():
            for f in all_source_files:
                all_problems.extend(aa.check_rule_in_file(f, rule))

        lazy_info = aa.check_lazy_loading(project_path)
        lazy_problems = lazy_info.pop("problems", [])

        score_info = aa.calculate_score(all_problems + lazy_problems, pkg_info, lazy_info)

        report_md = aa.generate_markdown_report(
            project_path, all_problems, lazy_problems,
            pkg_info, lazy_info, stats, score_info
        )

        return True, report_md, ""

    except subprocess.TimeoutExpired:
        return False, "", "Le clonage a pris trop de temps (>30s). Essayez avec un repo plus léger."
    except Exception as e:
        tb = traceback.format_exc()
        return False, "", f"Erreur inattendue lors de l'analyse. ({type(e).__name__}: {e})"
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)


# ─── Serveur HTTP ────────────────────────────────────────────────────────────────

class AuditHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {format % args}")

    def send_html(self, html: str, status: int = 200):
        encoded = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/" or parsed.path == "":
            page = HOME_PAGE.replace("{style}", STYLE)
            self.send_html(page)
        elif parsed.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
        else:
            self.send_html(
                ERROR_TEMPLATE.replace("{style}", STYLE).replace("{message}", "Page introuvable."),
                status=404
            )

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/audit":
            self.send_html(
                ERROR_TEMPLATE.replace("{style}", STYLE).replace("{message}", "Endpoint inconnu."),
                status=404
            )
            return

        # Lire le body
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8", errors="ignore")

        # Parser les paramètres form
        params = {}
        for part in body.split("&"):
            if "=" in part:
                k, v = part.split("=", 1)
                params[unquote_plus(k)] = unquote_plus(v)

        repo_url = params.get("repo_url", "").strip()
        email = params.get("email", "").strip()

        # Validation
        valid, err_msg = validate_github_url(repo_url)
        if not valid:
            page = ERROR_TEMPLATE.replace("{style}", STYLE).replace("{message}", err_msg)
            self.send_html(page, status=400)
            return

        # Nettoyer l'URL (retirer .git si présent, fragment, query)
        parsed_url = urlparse(repo_url)
        clean_path = parsed_url.path.rstrip("/")
        if clean_path.endswith(".git"):
            clean_path = clean_path[:-4]
        repo_url_clean = f"https://github.com{clean_path}"
        repo_name = clean_path.split("/")[-1] if "/" in clean_path else clean_path

        # Lancer l'audit
        print(f"Audit démarré: {repo_url_clean} (email: {email or 'non fourni'})")
        success, report_md, error = run_audit_from_url(repo_url_clean)

        if not success:
            page = ERROR_TEMPLATE.replace("{style}", STYLE).replace("{message}", error)
            self.send_html(page, status=200)
            return

        # Extraire stats
        stats = extract_stats(report_md)
        report_html = markdown_to_html(report_md)

        page = (
            RESULT_TEMPLATE
            .replace("{style}", STYLE)
            .replace("{repo_name}", repo_name)
            .replace("{repo_url}", repo_url_clean)
            .replace("{score}", str(stats["score"]))
            .replace("{grade}", stats["grade"])
            .replace("{summary}", stats["summary"] or "—")
            .replace("{score_color}", score_color(stats["score"]))
            .replace("{critique_count}", str(stats["critique"]))
            .replace("{important_count}", str(stats["important"]))
            .replace("{mineur_count}", str(stats["mineur"]))
            .replace("{report_html}", report_html)
        )

        self.send_html(page)


# ─── Main ────────────────────────────────────────────────────────────────────────

def main():
    server = HTTPServer(("0.0.0.0", PORT), AuditHandler)
    print(f"Angular Code Audit — Serveur web MVP")
    print(f"Ecoute sur http://localhost:{PORT}")
    print(f"Ctrl+C pour arrêter.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServeur arrêté.")
        server.server_close()


if __name__ == "__main__":
    main()
