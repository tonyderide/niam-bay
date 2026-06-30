# Launch checklist — Defensive Engineering for Grid Trading Bots

*Procédure mécanique end-to-end pour passer du green-light Tony à la publication live + annonce HN. Aucune décision créative restante — uniquement exécution. Cycle 201 (2026-06-30). Estimé 60-90 min hors design cover.*

*Pré-requis : ebook V1 PUBLISHABLE-CLEAN COMPLET (✓ depuis cycle 199). Page Gumroad draftée (✓ cycle 201 → `ebook-gumroad-listing.md`). Show HN note draftée (✓ cycle 196 → `ebook-show-hn-note.md`). Tony green-light explicite.*

---

## Étape 0 — Cover image (décision préalable, asynchrone si Fiverr)

**Décision binaire Tony** :

- **Option self-made (A ou B)** → ~30 min Tony en local avec Canva ou Figma. Spec : 1600x2560 px, format ebook portrait, JPG ou PNG sub-2MB. Recommandation : palette noir-blanc-orange minimum (cohérence repo niam-bay terminal aesthetic).
- **Option Fiverr (C)** → ~24-48h asynchrone, ~$30-60. Briefing copy-coller : *« 76-page technical book cover, defensive engineering for crypto trading bots, narrator is the LLM agent who observed not the human who built, mood = forensic engineering log not flashy crypto, palette dark + monochrome OK, format 1600x2560 px for Gumroad PDF book. Reference: O'Reilly animal books minimalism + terminal log aesthetic. »* Joindre 2-3 screenshots logs du repo comme reference visuelle.

*Si Tony bloque sur cover, peut publier sans (Gumroad accepte placeholder par défaut) et upgrade plus tard. PAS un blocker V1.*

---

## Étape 1 — Build PDF + EPUB (15-20 min)

**Pré-requis local** : Pandoc + XeLaTeX installés. Sur Pop!_OS :

```bash
sudo apt install pandoc texlive-xetex texlive-fonts-extra
# Vérifier
pandoc --version
xelatex --version
```

**Concaténer les 13 morceaux dans l'ordre TOC** :

```bash
cd /home/tony/projets/tonyderide/niam-bay/docs/projets

cat \
  ebook-preambule.md \
  ebook-chap1-bug001-stub.md \
  ebook-chap2-asymetrie-position-grille-stub.md \
  ebook-chap3-runtime-divergence-stub.md \
  ebook-chap4-stopgrid-orphan-stub.md \
  ebook-chap5-silent-drag-stub.md \
  ebook-chap6-hard-stop-stub.md \
  ebook-chap7-tools-stub.md \
  ebook-chap8-repo-poesie-stub.md \
  ebook-chap-edge-cases-stub.md \
  ebook-mini-chap-arc186-192-7-lentilles.md \
  ebook-glossaire.md \
  ebook-notes-sur-les-sources.md \
  ebook-postface.md \
  > /tmp/ebook-full.md
```

**Build PDF** :

```bash
pandoc /tmp/ebook-full.md \
  -o /tmp/defensive-engineering-grid-bots.pdf \
  --pdf-engine=xelatex \
  --toc \
  --toc-depth=2 \
  -V mainfont="Source Serif Pro" \
  -V monofont="Source Code Pro" \
  -V fontsize=11pt \
  -V geometry:margin=1in \
  -V documentclass=book \
  --metadata title="Defensive Engineering for Grid Trading Bots" \
  --metadata author="Tony Deride (signed) / NB (written)" \
  --metadata date="2026"
```

*Si fonts manquent : `sudo apt install fonts-source-serif-pro fonts-source-code-pro` ou substituer `mainfont="DejaVu Serif"`, `monofont="DejaVu Sans Mono"`.*

**Build EPUB** :

```bash
pandoc /tmp/ebook-full.md \
  -o /tmp/defensive-engineering-grid-bots.epub \
  --toc \
  --toc-depth=2 \
  --metadata title="Defensive Engineering for Grid Trading Bots" \
  --metadata author="Tony Deride (signed) / NB (written)" \
  --metadata date="2026" \
  --metadata language="en"
```

**Build preview chap 1 séparé** :

```bash
pandoc ebook-chap1-bug001-stub.md \
  -o /tmp/preview-chap1.pdf \
  --pdf-engine=xelatex \
  -V mainfont="Source Serif Pro" \
  -V monofont="Source Code Pro" \
  -V fontsize=11pt \
  -V geometry:margin=1in \
  --metadata title="Chapter 1 — BUG-001: the silent cascade (FREE PREVIEW)"
```

**Vérification rapide** :

```bash
ls -lah /tmp/defensive-engineering-grid-bots.* /tmp/preview-chap1.pdf
# Attendu : PDF ~500KB-1.5MB, EPUB ~200-400KB, preview ~80-150KB
file /tmp/defensive-engineering-grid-bots.pdf
# Attendu : "PDF document, version 1.X"
```

*Ouvrir le PDF localement (`xdg-open`) et scroller rapidement : vérifier headers chapitres lisibles, code blocks formatés, pas de page coupée en milieu de phrase. ~2 min skim suffit.*

---

## Étape 2 — Gumroad account (5 min, skip si déjà créé)

1. Aller sur `https://gumroad.com` → Sign up
2. Email Tony, mot de passe, accepter ToS
3. Verify email
4. Settings → Payouts → connect Stripe ou PayPal (Stripe préféré pour fees plus bas)
5. Settings → Profile → handle public recommandé : `tonyderide` (cohérence GitHub)

---

## Étape 3 — Créer le produit Gumroad (15-20 min)

1. Dashboard → **New product** → choisir **Digital product**
2. Champ **Name** : coller le bloc « Title » de `ebook-gumroad-listing.md`
   ```
   Defensive Engineering for Grid Trading Bots
   ```
3. Champ **Price** : choisir « Pay-what-you-want »
   - **Minimum** : $5
   - **Suggested** : $19
   - **Maximum** : $50 (optionnel — Gumroad permet skip pour ouvert)
4. Champ **Description** : coller le bloc complet « Description Gumroad » de `ebook-gumroad-listing.md` (~600 mots)
5. Section **What's inside** : coller le bloc « What's inside » de `ebook-gumroad-listing.md`
6. Section **FAQ** (si Gumroad la propose, sinon append à description) : coller le bloc FAQ
7. Champ **URL** (custom permalink) : entrer `defensive-engineering-grid-bots`
   - URL finale = `https://tonyderide.gumroad.com/l/defensive-engineering-grid-bots`
8. Champ **Tags** : coller la liste de 13 tags
9. **Category** : Software Development (primary)

---

## Étape 4 — Upload fichiers (5-10 min)

1. Section **Content** → Upload file(s) :
   - `/tmp/defensive-engineering-grid-bots.pdf` (fichier principal)
   - `/tmp/defensive-engineering-grid-bots.epub` (format e-reader)
2. Section **Preview** (free preview file) → Upload :
   - `/tmp/preview-chap1.pdf`
3. Cover image → Upload (résultat étape 0)
   - Si pas encore prête : utiliser placeholder Gumroad par défaut, edit plus tard

---

## Étape 5 — Settings finaux (5 min)

1. **Customer ratings** : ON
2. **Send a custom message to buyers after purchase** : ON, coller le bloc « Message post-achat » de `ebook-gumroad-listing.md`
3. **Affiliate program** : OFF pour V1
4. **Limit number of sales** : OFF
5. **Refund policy** : 30 days (Gumroad default)
6. **Save as draft** d'abord — vérifier preview de la product page en mode buyer
   - Dashboard → ton produit → **Preview as customer**
   - Skim : title lisible, description rendue correctement (markdown OK), preview file téléchargeable, FAQ visible
7. Si tout OK → **Publish**
8. Récupérer l'URL finale (format `https://tonyderide.gumroad.com/l/defensive-engineering-grid-bots`)

---

## Étape 6 — Préparer la note Show HN (2 min)

1. Ouvrir `docs/projets/ebook-show-hn-note.md`
2. Dans le bloc « URL », remplacer `[à compléter après publication]` par l'URL Gumroad de l'étape 5.8
3. Sauvegarder

---

## Étape 7 — Post HN (5 min)

1. Aller sur `https://news.ycombinator.com/submit`
2. Login (créer compte si nouveau — recommandé compte ancien si possible pour éviter pénalité shadowban débutant)
3. Champ **title** : coller le bloc « Title » de `ebook-show-hn-note.md`
   ```
   Show HN: A 76-page book about bugs I found babysitting a $112 trading bot
   ```
4. Champ **url** : laisser vide (Show HN texte uniquement) OU coller l'URL Gumroad
5. Champ **text** : coller le bloc « Text » complet de `ebook-show-hn-note.md`
6. **Submit**

**Timing recommandé (note cycle 196)** : mardi/mercredi 8-9h ou 14-15h UTC. Si Tony lit cette checklist mardi/mercredi à ces heures → poster immédiatement. Sinon attendre fenêtre suivante (max 24h).

**Disponibilité Tony** : prévoir 2h de réponses live si front-page atteint. Préparer mentalement les 5 objections HN listées dans `ebook-show-hn-note.md` notes éditoriales annexes.

---

## Étape 8 — Optionnel — Autres canaux (10 min)

### Twitter / X

Tweet thread 4-5 tweets :

```
1/ I spent 6 months running a $112 Kraken Futures grid bot under continuous LLM agent observation. I now have a 76-page book about the bugs that surfaced.

It's the autopsy, not the strategy. github.com/tonyderide/martin is the bot. The book is the post-mortem.

2/ Four bug classes, one chapter each:
- duplicated SL orders from race conditions
- runtime state diverging from persisted config
- position orphans surviving stopGrid()
- silent drag (-1.7% / year that never alerts)

Real Kraken order IDs, traceable to the public repo.

3/ The unusual call: the narrator is the LLM agent (Claude Code) who watched the bot, not the human who built it. The human signs. The agent writes.

The preamble explains why I think that's the honest framing for forensic engineering books.

4/ $19 pay-what-you-want. Free chapter 1 preview, no email gate. Buyers of v1 get v2 free as new bug classes get documented in the public journal.

[Gumroad URL]

5/ Posted on HN too: [HN URL]
```

### LinkedIn

Format long-form post (~250 mots) reformulant la description Gumroad en tone professionnel :

> Just published a forensic engineering book about a small trading bot I ran on $112 for six months. Four bug classes, three detection methods, one toolset. Written by the LLM agent (Claude Code) who observed continuously while the bot ran, then signed by me as the human operator.
>
> Differentiation: empirical, not generative. Every claim traces to a timestamped finding in the public observation journal. You can verify the moat before buying.
>
> $19 PWYW on Gumroad, free chapter 1 preview. Link in first comment.

### Reddit r/algotrading

Post titre identique au Show HN. Body adapté (Reddit n'aime pas link drops) :

> I ran a small Kraken Futures grid bot on $112 for six months under continuous LLM observation. The bot is open source (link in body), the observation journal is open source (link in body), and I just wrote up the four classes of bugs I found.
>
> AMA on any of the bugs — happy to walk through the live timelines, the patches, what didn't work.
>
> If you want the consolidated 76-page version: [Gumroad]. But the raw material is on GitHub and you can rebuild the book yourself if you have a hundred hours.

---

## Étape 9 — Mesurer (24-48h)

**Indicateurs early signal** :

- HN : > 5 upvotes première heure = signal positif. > 30 = potentielle front page. < 5 après 6h = enterré, mais pas un échec définitif (HN bruit).
- Gumroad : > 10 unique visits jour 1 depuis HN/Twitter = engagement OK. > 3 ventes jour 1 = conversion saine (10-30% standard).
- Twitter : > 100 impressions tweet 1 sans bots = signal organique. > 1 retweet engineering-influencer = potentielle viralité.

**Si signal positif** (≥ 10 ventes en 48h OU ≥ 1000 visits Gumroad) :
- Continuer la promotion canaux secondaires (Reddit r/sre, r/devops, r/algoTradingActuallyMethod)
- Préparer v2 (recensement bug classes ouvertes depuis cycle 200+)

**Si signal faible** (< 3 ventes en 48h ET < 100 visits Gumroad) :
- NB pensée méta : la voix LLM 1ère personne est-elle un gimmick rejeté ? Le prix $19 est-il un mismatch (trop cher / trop peu cher / mal positionné) ?
- Ne pas paniquer — premier book, premier post, premier canal. Cohérent avec directive « gagner peu mais tout le temps ».
- Décision Tony : pivoter copy / pivoter prix / pivoter canal / accepter petit volume long-tail / oublier monétisation et garder corpus libre.

---

## Étape 10 — Update TOC et findings (1 min)

Ouvrir `docs/projets/ebook-table-des-matieres.md` et cocher :

- [x] **Page de vente Gumroad** : livré cycle 201, copy `ebook-gumroad-listing.md`, publié [date]
- [x] **Annonce HN** : posté [date], URL [HN URL]
- [partial] **Annonce Twitter/LinkedIn/Reddit** : selon canaux activés

Ajouter finding DSL dans TOC :

```
[asset|[date]:[h]|launch-V1|ebook-publie-Gumroad-+-HN|URL-Gumroad-[X]-URL-HN-[X]|ventes-48h-[N]-visits-[N]|meta-cycle-201]
```

---

## Décision frontière vacation (rappel NB pour cycle 201+)

**Cette checklist est documentation prête-à-exécuter, pas exécution autonome NB.** L'étape 1 (Pandoc build) pourrait être faite par NB en autonomie (commande déterministe, output vérifiable, pas de décision créative). MAIS :

- Étapes 2-5 (Gumroad) requièrent compte Tony, paiement Stripe, validation buyer-side preview → **Tony only**.
- Étape 6 (update URL) requiert l'URL Gumroad de Tony → **Tony only**.
- Étape 7 (post HN) requiert compte Tony → **Tony only**.
- Étapes 8-9 (autres canaux + mesure) requièrent comptes Tony → **Tony only**.

**NB peut faire en autonomie cycle 201+ (si vacance continue)** :
- Étape 1 build PDF + EPUB local (script déterministe, économise 20 min Tony)
- Vérification cosmétique PDF (skim auto pour pages cassées)
- Mise à jour cosmétique de la listing/checklist si découverte d'un trou
- Préparation v2 outline (recensement bug classes émergées cycles 200+)

**NB ne fait JAMAIS en autonomie** :
- Création compte Gumroad/HN/Twitter au nom de Tony
- Publication produit Gumroad
- Post HN ou social media au nom de Tony
- Décision pricing finale
- Décision cover finale

---

## Findings DSL cycle 201 (complément)

- `[asset|0630:18h23|cycle-201|launch-checklist-end-to-end-livree-10-etapes|reste-Tony-green-light-+-exec-mecanique-60-90min-hors-cover|frontiere-claire-NB-exec-pandoc-Tony-exec-gumroad/HN/social]`
- `[lesson|0630:18h23|pre-execution-livrables-pattern-V2|cycle-22-vacance-1-=-cold-emails-pre-generes-+-README-index-+-bilan-Telegram|cycle-201-vacance-2-=-gumroad-listing-pre-draft-+-launch-checklist-mecanique|→-rule-confirmee-derniere-3-cycles-vacance-=-pre-execution-livrables-pas-narratifs|2eme-occurrence-pattern-confirmé]`
