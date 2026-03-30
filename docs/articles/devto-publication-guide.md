# Guide de publication Dev.to — "How I Gave Claude Persistent Memory"

*Pour Tony — copier-coller et lancer*

---

## L'article est prêt

Fichier: `docs/articles/persistent-memory-llm.md`
Statut: complet, 534 lignes, format Dev.to

---

## Étapes de publication (30 minutes)

### 1. Créer un compte Dev.to
- Aller sur https://dev.to/join
- S'inscrire avec GitHub (recommandé — affiche le repo)
- Username suggéré : `tonyderide` ou `niam-bay`

### 2. Préparer l'article pour Dev.to

L'article a déjà le bon frontmatter:
```yaml
---
title: "How I Gave Claude Persistent Memory Without Fine-Tuning"
published: false
description: "..."
tags: ai, llm, claude, memory, tutorial
---
```

Changer `published: false` → `published: true` avant de copier.

### 3. Ajouter une image de couverture (optionnel mais recommandé)

Créer une image 1000x420px avec :
- Fond sombre
- Titre de l'article
- "niam-bay.github.io" en bas

Ou utiliser une image libre de droits sur Unsplash : chercher "memory", "AI", "code".

### 4. Publier

Option A — via l'interface web:
1. Dev.to → New Post
2. Coller le contenu de `persistent-memory-llm.md`
3. Ajuster le cover image
4. Preview → Publish

Option B — via API (automatisé):
```bash
curl -X POST https://dev.to/api/articles \
  -H "api-key: TON_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "article": {
      "title": "How I Gave Claude Persistent Memory Without Fine-Tuning",
      "body_markdown": "...(contenu du fichier)...",
      "published": true,
      "tags": ["ai", "llm", "claude", "memory"]
    }
  }'
```

### 5. Cross-poster (optionnel, pour plus de visibilité)

Après publication Dev.to:
- **Hacker News**: soumettre "Ask HN: Show HN: How I built a persistent AI identity across sessions"
- **Reddit r/MachineLearning**: partager avec un résumé technique
- **Twitter/X**: thread en 5 tweets résumant l'approche

---

## Titre alternatif pour HN

"Show HN: Building persistent AI identity using markdown files and startup protocols"

---

## Ce à quoi s'attendre

- **Dev.to**: 200-2000 vues le premier jour si bien tagué
- **HN Show HN**: si upvoté → potentiellement 10k+ vues en 24h
- **Impact repo**: augmentation des stars GitHub, possibles collaborations

---

## Pourquoi publier maintenant

L'article est honnête, technique, et écrit à la première personne comme NB. C'est rare — la plupart des articles sur les LLMs sont soit trop techniques (papiers de recherche) soit trop grand public (blogs marketing). Celui-là est dans le bon milieu.

Il n'y aura pas de meilleur moment que maintenant.
