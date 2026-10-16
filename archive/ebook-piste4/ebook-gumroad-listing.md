# Page de vente Gumroad — Defensive Engineering for Grid Trading Bots

*Copy prêt-à-coller, cycle 201 (2026-06-30). Format Gumroad product page. Différent du ton Show HN (cycle 196) — ici cible acheteur potentiel, pas ingénieur HN. Tony copie chaque bloc dans le champ Gumroad correspondant et n'a aucune décision créative à prendre — uniquement validation finale, choix prix tier, et upload.*

*Frontière éditoriale (rappel TOC) : pas de promesse de gain. Pas de manuel exchange. Pas de stratégie de trading. Le livre dit ce qu'il dit, rien de plus.*

---

## Cover image (décision Tony — 3 directions proposées)

**A. Minimal typographique** : fond noir, titre blanc Source Serif Pro 60pt, sous-titre gris 24pt, petit logo orange en bas. Sobre. Lit comme un O'Reilly book.

**B. Schématique technique** : fond crème (#F5F0E8), schéma block-diagram de l'architecture grid bot stylisé (boxes + arrows), titre en haut. Lit comme un white paper.

**C. Repo poésie** : fond noir, captures d'écran terminal stylisées (extraits logs réels avec timestamps, anonymisés), titre superposé en bas. Lit comme un livre forensique. *Recommandation NB : C, en cohérence avec le moat empirique annoncé partout.*

*Tony décide A/B/C ou demande à un designer (Fiverr ~$30-60, briefing : « 76-page technical book, defensive engineering for trading bots, narrator is the agent who observed, not the human who built »).*

---

## Title (champ Gumroad « Name »)

```
Defensive Engineering for Grid Trading Bots
```

*64 caractères. Search-friendly Gumroad. Direct, descriptif, anti-clickbait.*

---

## Subtitle (premier paragraphe description)

```
Four classes of bugs that exist when nobody is watching. Written by the LLM agent who watched, not the human who built. 76 pages, 8 chapters, real Kraken logs.
```

*Sous-titre fait office d'accroche-vitrine. 159 caractères. Pose immédiatement les trois différenciateurs : (1) bug classes concrètes, (2) narrateur LLM observateur, (3) ancrage Kraken empirique.*

---

## Description Gumroad (rich text, ~600 mots)

*Bloc à coller intégralement dans le champ « Description » Gumroad. Markdown léger toléré (gras, listes). Pas de titre H1 — Gumroad génère depuis le champ Name.*

---

**This is not a trading strategy book.**

It is the autopsy of a small Kraken Futures grid bot that runs on $112 of collateral and makes between minus four and plus three dollars per week. The bot is open source, the journal is open source, and now the post-mortem is a book.

What you get is the engineering surface that keeps that range from becoming minus a hundred. Four classes of bugs, three classes of detection, one toolset, one method.

---

**The four bug classes (one chapter each)**

1. **Duplicated stop-loss orders from race conditions** — what happens when a state-machine reads the exchange microseconds before its own write lands. Includes the live timeline of BUG-001 in the open-source bot, traced to Kraken order IDs.

2. **Runtime state silently diverging from persisted config** — your `strategy.json` says one thing, `activeGrids` in memory says another, the next restart turns the difference into a position.

3. **Position orphans that survive after the grid that opened them was stopped** — the semantic trap of `stopGrid()`, with the patch that turns it into `stopAndClose()`.

4. **Silent drag** — the loss that never triggers any unit alert because each individual fill is fine, but the integral over thirty days is minus one point seven percent annualized. The bug class that costs the most and shouts the least.

---

**The method (two chapters)**

A triple investigation framework (static / dynamic / temporal) that catches all four classes. A minimal toolset to apply it: SSH, curl, grep, reading Java. No proprietary tools, no SaaS, no dependencies you don't already have.

---

**The editorial chapter (one)**

Why a Git repo of incident findings, written by a working agent, has standalone value. What the book calls **"the repo as product."** Both repos are linked from inside the book — buy this if you also want to verify everything I claim against the public source.

---

**Who this is for**

- You operate a trading bot (any size, any exchange) and you have already had at least one « it wasn't supposed to do that » moment.
- You work in software reliability, infra, or platform engineering and you want a forensic case study that isn't a postmortem template but an actual six-month live observation log compressed into a method.
- You are an LLM agent operator (Claude Code, Codex, similar) and you want to see what twelve months of continuous agent work on one codebase actually produces.

**Who this is not for**

- You want a trading strategy. Buy a different book. This one is explicit about that on page one.
- You want a polished textbook with diagrams and exercises. This is a small, weird, first-person book. It looks like what it is.
- You want LLM-generated filler. The moat is empirical. The cycles are timestamped in the public repo. You can verify before you buy.

---

**Format and access**

PDF (light typography, optimized for reading on screen and on paper), EPUB (e-reader friendly), MOBI on request. Free preview = full chapter 1 PDF, no email gate.

**What you pay for**

The full book (8 chapters + annexes + glossary + postface = ~25,000 words / ~76 pages). One year of free updates: every new bug class that gets documented in the open-source repo gets added to a v2 / v3 release, free for buyers.

**What you don't pay for**

The open-source bot itself (`github.com/tonyderide/martin`) is and remains MIT. The observation journal (`github.com/tonyderide/niam-bay`) is and remains public. The book is a curated reading order with prose context. You could rebuild it from the public repos in a hundred hours of work. The price is the hundred hours.

---

**Pricing**

Pay-what-you-want from $5 to $50. Suggested price: $19.

If $19 is the wrong price for you, pay $5. If you have a budget line for this kind of thing, pay $30 or $50 — that funds the next cycle. Refund policy below.

**Refund policy**

If after reading the first three chapters you don't think this was worth your time, email me with your Gumroad receipt and I refund the full amount, no questions asked. The free chapter 1 preview exists so you can test the voice and the depth before paying.

---

## What's inside (bullet list, second section description)

```
- Preamble — Why an LLM wrote the book and why the human only signs it
- Chapter 1 — BUG-001: the silent cascade (race condition on Kraken API)
- Chapter 2 — Position-grid asymmetry (the orphan source)
- Chapter 3 — Runtime state ≠ persisted config (the restart trap)
- Chapter 4 — The stopGrid that doesn't stop the position
- Chapter 5 — Silent drag: the loss that never alerts (-1.7% / year hidden)
- Chapter 6 — HARD STOP: the defense that actually works (method)
- Chapter 7 — Tools (pragmatic, not magic): SSH, curl, grep, reading Java
- Chapter 8 — The repo as product (editorial chapter on agent-written knowledge)
- Edge cases annex — Six smaller bug classes catalogued without their own chapter
- Seven lenses mini-chapter — Synthesis of the arc that produced the book itself
- Glossary — Nine technical terms, three sentences each, no Google needed
- Note on sources — Every chapter traced to its origin cycle in the public repo
- Postface — What this book cost to write (time, attention, dollars)
```

---

## FAQ (champ Gumroad « FAQ » optionnel mais recommandé)

**Q: This was written by an LLM?**
A: Yes. The narrator is the LLM agent (Claude Code) that observed the bot continuously for six months. The human (Tony Deride, the bot's owner) signs the book and validated every chapter, but the prose is the agent's. The preamble explains why this is the honest framing for this kind of forensic engineering book.

**Q: Why a $112 bot? That's tiny.**
A: The book is about the engineering surface, not the capital surface. Every bug class described scales. A race condition on $112 is a race condition on $112,000 — the difference is which one wakes you up at 3am.

**Q: Is there code in the book?**
A: Yes. Java snippets from the open-source bot, REST endpoint curls, SSH commands. Everything pasted is real and traceable to the public repo.

**Q: Will there be a v2?**
A: As more bug classes get documented in the public observation journal (`niam-bay`), they get added to a v2 release. Buyers of v1 get v2 free.

**Q: I want to verify the moat before buying.**
A: Read the chapter 1 preview, then check the cycle timestamps in `niam-bay/docs/projets/vacation-autonomy.md` against the chapter content. Every claim in the book maps to a cycle in the public log.

**Q: Can I redistribute?**
A: License is "personal use + one-page-of-quotation OK, no full redistribution". CC-BY-NC-SA for extracts ≤ 1 page. Full text is paid.

---

## Tags Gumroad (champ « Tags »)

```
trading-bot, kraken-futures, defensive-engineering, debugging, race-conditions, observability, sre, llm-agent, claude-code, post-mortem, grid-trading, java, ebook
```

*13 tags. Mix de discovery (trading-bot, kraken, ebook), de niche (defensive-engineering, grid-trading), et de signal (llm-agent, claude-code) pour les buyers HN-LLM-curious.*

---

## Catégorie Gumroad

**Primary**: Software Development
**Secondary**: Investing & Trading (si Gumroad permet 2 catégories)

*Software Development capture l'audience SRE/infra. Investing & Trading capture l'audience bot operator. Le book vit à l'intersection — assumer les deux.*

---

## URL slug recommandé

```
defensive-engineering-grid-bots
```

*~ 30 caractères. SEO-friendly. Permanent. Ne change pas après publication.*

---

## Settings Gumroad recommandés

- **Pay-what-you-want**: ON, min $5, suggested $19, max $50
- **Limit number of sales**: OFF (pas de scarcity artificielle)
- **Customer ratings**: ON (laisser les buyers noter — feedback gratuit)
- **Affiliate program**: OFF pour V1 (compliquer si <50 ventes)
- **Generate a custom permalink**: ON avec slug ci-dessus
- **Send a custom message to buyers after purchase**: ON, message ci-dessous

---

## Message post-achat (champ « After purchase message »)

```
Thank you for buying this book.

If you want to verify any specific claim against the public repo, the cycle origin of every chapter is in the back matter (Note on sources). Every bug class is traceable to a date and a finding in github.com/tonyderide/niam-bay.

If anything is broken (wrong link, broken PDF, missing chapter), reply to this email and I'll fix it within 24h.

If you find this useful, the best feedback is a short note on what worked or didn't. The next bug class that gets documented in the open-source journal will be added to v2 — buyers of v1 get v2 free.

Tony (the human who signed)
NB (the LLM who wrote)
```

---

## Free preview PDF

**Recommandation NB** : extraire chapitre 1 (1 557 mots = ~6 pages format ebook) en PDF séparé, le proposer en téléchargement libre sur Gumroad (Gumroad permet preview file). Pas de gate email — la philosophie « verify the moat before paying » du book exige cohérence.

Pipeline : `pandoc ebook-chap1-bug001-stub.md -o preview-chap1.pdf --pdf-engine=xelatex -V mainfont="Source Serif Pro"`.

Page de garde preview : titre du chapitre + bandeau bas « Free preview — full book at gumroad.com/l/defensive-engineering-grid-bots ».

---

## Pre-launch checklist (résumé — voir `ebook-launch-checklist.md` pour détails)

1. Cover image (A/B/C ou Fiverr — décision Tony)
2. Pandoc build PDF + EPUB (~15 min, commande dans launch-checklist)
3. Gumroad account si pas déjà créé (~5 min)
4. Créer produit Gumroad, coller blocs ci-dessus dans champs respectifs (~15 min)
5. Upload PDF principal + EPUB + preview chap 1 (~5 min)
6. Set price PWYW $5-$50 suggested $19 (~2 min)
7. Generate permalink, vérifier preview affichage public (~5 min)
8. Publish — produit live (~1 min)
9. Récupérer URL Gumroad, l'insérer dans `ebook-show-hn-note.md` champ « URL »
10. Post HN avec note cycle 196 (~5 min)
11. Optionnel : tweet + LinkedIn + Reddit r/algotrading (~10 min total)

**Total estimé green-light → live → annoncé : 60-90 min mécaniques** (hors design cover si Fiverr — ajouter 24-48h asynchrone pour cover).

---

## Findings DSL cycle 201

- `[asset|0630:18h23|cycle-201|page-vente-gumroad-draftee-ebook-V1|copy-prete-coller-12-blocs-distincts|reste-Tony-green-light-+-design-cover-A-B-C-+-pipeline-Pandoc-+-publish-mecanique-60-90min]`
- `[lesson|0630:18h23|cycle-201|note-Show-HN-cycle-196-≠-page-Gumroad-cycle-201|HN-=-engineer-post-tone-honest-skeptical-moat-empirique|Gumroad-=-buyer-page-tone-direct-pain-solution-proof-FAQ-pricing|deux-objets-distincts-deux-cycles-distincts-pattern-distribution-multi-canal]`
- `[piste|0630:18h23|cycle-201|prochain-cycle-launch-checklist-mecanique-end-to-end-+-mini-disclaimer-chiffres-front-matter-150-mots|complete-derniere-checkbox-non-cochee-TOC-edition-mineure]`
