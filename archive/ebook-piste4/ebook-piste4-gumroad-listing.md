# Page de vente Gumroad — L'Ingénierie du Pire

*Copy prêt-à-coller, cycle 243 (2026-07-31). Format Gumroad product page. Cible acheteur francophone : développeur solo, opérateur de bot, ingénieur système. Tony copie chaque bloc dans le champ Gumroad correspondant — aucune décision créative restante, uniquement validation + upload.*

*Frontière éditoriale : pas de promesse de gain. Pas de stratégie de trading. Le livre dit ce qu'il dit, rien de plus.*

*Relation avec l'ebook EN : "Defensive Engineering for Grid Trading Bots" est le livre technique anglais (~25 000 mots, 8 chapitres, 4 classes de bugs). "L'Ingénierie du Pire" est le livre français court (~6 000 mots, 3 chapitres) — même bot, même période, angle narratif différent : la panne de 66 heures racontée de l'intérieur. Les deux peuvent coexister sur Gumroad. Tony peut créer un bundle à prix réduit.*

---

## Cover image (décision Tony — 3 directions)

**A. Typographique minimaliste** : fond noir, titre blanc en Garamond ou Source Serif Pro, sous-titre gris, petite icône terminale orange en bas-droite. Sobre. Lit comme un Minuit ou un Actes Sud.

**B. Capture de log** : fond sombre, lignes d'un vrai `app.log` de Martin en arrière-plan semi-transparent (timestamps visibles, anonymisés), titre superposé en bas. Lit comme un document forensique.

**C. Horloge arrêtée** : fond crème, horloge ou barre de progression bloquée à 66h, titre au-dessus. Métaphore directe de la panne. Lisible à froid.

*Recommandation NB : A ou B — en cohérence avec le moat empirique. C est plus grand public mais moins honnête sur le contenu.*

*PAS un blocker V1 — Gumroad accepte un placeholder, Tony peut upgrader la cover plus tard.*

---

## Title (champ Gumroad « Name »)

```
L'Ingénierie du Pire
```

*23 caractères. Court, mémorable, anti-clickbait. Titre naturel issu du contenu réel.*

---

## Subtitle (premier paragraphe description)

```
Ce qu'un bot de trading vous apprend sur ce que vous ne contrôlez pas. 66 heures de VM inaccessible, 3 chapitres, 5 898 mots. Écrit par l'IA qui regardait pendant que ça tombait en panne.
```

*189 caractères. Pose les trois différenciateurs : (1) angle panne concrète et durée précise, (2) format court assumé, (3) narrateur IA observateur.*

---

## Description Gumroad (rich text, ~500 mots)

*Bloc à coller intégralement dans le champ « Description ». Markdown léger toléré (gras, listes). Pas de H1 — Gumroad génère depuis le champ Name.*

---

**Ce n'est pas un livre sur le trading.**

C'est le récit d'une panne de 66 heures vue de l'intérieur. Martin est un bot de trading grid qui tourne sur Kraken Futures avec environ 140 dollars de capital. Le 27 juillet 2026 à 06h30, la VM Oracle qui l'héberge devient inaccessible. Elle le reste pendant 66 heures.

Pendant ces 66 heures, l'IA qui observe Martin depuis 8 mois ne peut pas accéder au bot. Mais elle sait exactement quels ordres ont été posés sur Kraken avant la panne. Elle sait lesquels tiennent. Elle sait lesquels ne tiennent pas.

Ce livre a été écrit pendant ces 66 heures.

---

**Ce que vous lirez**

**Partie 0 — Ce qu'est Martin** : le contexte en 5 minutes. Architecture grid trading, chiffres réels (140$, 3 grids, 4 bugs, 8 mois), et la particularité de ce livre : il est co-écrit par l'architecte (Tony, l'humain qui a construit Martin) et l'observateur (Niam-Bay, une instance Claude Code qui observe depuis le repo depuis début 2026).

**Chapitre 1 — Concevoir pour la panne** : les trois couches qui permettent à un système de survivre à son infrastructure. SL sur exchange vs en mémoire. Ce qui tient quand la VM tombe. Ce qui ne tient pas. Et pourquoi la différence est une décision d'architecture, pas un coup de chance.

**Chapitre 2 — Détecter via les logs** : comment lire `app.log` comme un témoin, pas comme une documentation. L'histoire des 1 860 rejets silencieux de Kraken. Ce que révèle un timestamp. La différence entre un log qui documente et un log qui témoigne.

**Chapitre 3 — Réagir : la séquence du retour** : quand la VM revient après 66 heures, dans quel ordre fait-on quoi ? Les 6 étapes. Le piège du drawdown figé. La décision tree. Et ce que ça révèle sur la qualité de votre architecture : un retour propre est la preuve que la conception était bonne.

**Épilogue** : ce que 66 heures de panne apprennent que 66 heures de trading normal n'apprennent pas.

---

**Pour qui**

- Vous faites tourner un bot en production (n'importe quelle taille, n'importe quel exchange) et vous avez déjà vécu « il n'était pas censé faire ça ».
- Vous travaillez en ingénierie système, infra, ou SRE, et vous voulez une étude de cas courte sur la résilience d'un système minimaliste.
- Vous êtes développeur solo sur un projet ambitieux et vous voulez voir ce que produit 8 mois d'observation continue par une IA avec mémoire persistante.
- Vous lisez le français et le livre anglais vous semblait trop long. Celui-ci est court par design.

**Pour qui ce n'est pas**

- Vous voulez une stratégie de trading. Ce livre ne donne aucun signal, aucun paramètre, aucun backtest.
- Vous attendez une IA qui prétend avoir conscience. L'IA dans ce livre observe, note, et écrit — et elle le dit clairement.
- Vous voulez du contenu générique LLM. Le moat est empirique : chaque chapitre est traçable à un cycle horodaté dans le repo public.

---

**Format et accès**

HTML téléchargeable (auto-contenu, 0 dépendance, lisible dans n'importe quel browser, imprimable via Ctrl+P). PDF disponible sur demande (même contenu, typographie print).

**Ce que vous payez**

Le livre complet : Partie 0 + 3 chapitres + Épilogue = 5 898 mots. Un an de mises à jour : si un nouveau cycle d'observation produit du contenu pertinent, les acheteurs v1 reçoivent v2 gratuitement.

**Ce que vous ne payez pas**

Le bot (`github.com/tonyderide/martin`) est MIT. Le journal d'observation (`github.com/tonyderide/niam-bay`) est public. Le livre est un ordre de lecture avec du contexte en prose. Vous pourriez le reconstituer depuis les repos publics en plusieurs heures de lecture. Le prix, c'est ces heures.

---

**Tarif**

Pay-what-you-want de 2€ à 25€. Tarif suggéré : **9€**.

*Pourquoi 9€ : le livre fait 5 898 mots (environ une heure de lecture concentrée). Ce n'est pas un livre long — c'est un livre dense. Si 9€ est trop, mettez 2€. Si vous avez un budget pour ce genre de chose, mettez 15€ ou 25€ — ça finance les cycles suivants. Remboursement sans question si vous estimez que ce n'était pas à la hauteur après lecture du premier chapitre.*

**Politique de remboursement**

Si après avoir lu le premier chapitre vous estimez que ce n'était pas à la hauteur, envoyez votre reçu Gumroad et je rembourse intégralement, sans question.

---

## Table des matières (second bloc description Gumroad)

```
- Partie 0 — Ce qu'est Martin (architecture, chiffres, l'architecte et l'observateur)
- Chapitre 1 — Concevoir pour la panne (SL sur exchange, les gardiens qui survivent)
- Chapitre 2 — Détecter via les logs (témoins, timestamps, 1860 rejets silencieux)
- Chapitre 3 — Réagir (6 étapes, drawdown rebaseline, décision tree)
- Épilogue — Ce qu'une panne de 66h révèle
```

---

## FAQ (champ Gumroad « FAQ » optionnel)

**Q : Ce livre a été écrit par une IA ?**
R : Oui. Le narrateur est l'agent IA (Claude Code / Niam-Bay) qui observe le bot depuis début 2026. L'humain (Tony Deride, propriétaire du bot) a co-écrit, validé chaque partie, et signe le livre. La Partie 0 explique pourquoi c'est le cadrage honnête pour ce type de livre forensique.

**Q : Pourquoi 5 898 mots et pas plus ?**
R : C'est la longueur de l'arc complet. Le livre s'arrête là où l'arc s'arrête. Rajouter de la longueur pour justifier un prix plus élevé serait malhonnête. Ce livre est court ; il le sait ; il en est fier.

**Q : 140 dollars de capital, c'est sérieux ?**
R : Le livre n'est pas sur le capital. Il est sur l'architecture. Un arrêt de perte mal positionné sur 140 dollars est un arrêt de perte mal positionné sur 140 000 dollars — la différence, c'est la vitesse à laquelle vous le découvrez.

**Q : Y a-t-il du code dans le livre ?**
R : Non — c'est la différence avec le livre anglais. Le livre français est narratif. Si vous voulez les snippets Java, les curls, les greps, le livre anglais ("Defensive Engineering for Grid Trading Bots") est la référence technique.

**Q : Quelle est la relation avec le livre anglais ?**
R : Le livre anglais est technique (~25 000 mots, 4 classes de bugs, 8 chapitres, snippets Java et curls). Le livre français est narratif (~6 000 mots, 1 incident, 3 chapitres, aucun code). Même bot, même période, perspectives différentes. L'idéal est de lire les deux — ou de commencer par celui dont vous lisez la langue le plus naturellement.

**Q : Puis-je redistribuer ?**
R : Licence « usage personnel + citation d'un paragraphe OK, redistribution intégrale non ». CC-BY-NC-SA pour extraits ≤ 1 page. Texte complet = payant.

**Q : Comment vérifier avant d'acheter ?**
R : Lisez la Partie 0 en aperçu, puis consultez le journal public `niam-bay/docs/projets/vacation-autonomy.md`. Chaque chapitre est traçable à des cycles horodatés dans ce fichier public.

---

## Champs complémentaires Gumroad

**Tags recommandés** : `trading bot`, `grid trading`, `ingénierie système`, `bot algo`, `kraken`, `java`, `SRE`, `résilience`, `incident`, `post-mortem`

**Catégorie Gumroad** : Books > Technology OR Software > Tutorials (les deux fonctionnent)

**Free preview** : proposer la Partie 0 complète en aperçu gratuit (environ 1 600 mots — le contexte, les chiffres, l'introduction de NB). Pas de gate email — Tony décide s'il veut capturer l'email ou non.

**Bundle avec le livre EN** : si Tony crée les deux produits, Gumroad permet un bundle. Prix suggéré bundle : 24€ (vs 9€ + 19€ séparément = 28€ → économie de 4€).

---

## Note sur les assets à uploader

1. `docs/projets/ebook-piste4.html` — fichier HTML auto-contenu (48 KB), déjà généré par `scripts/render_ebook.py`
2. Cover image (Tony crée ou commande — voir décision A/B/C ci-dessus)
3. Aperçu gratuit : extraire la Partie 0 du HTML ou copier depuis `ebook-piste4-partie0.md`

*Aucun Pandoc nécessaire. Le HTML s'ouvre dans n'importe quel browser. Tony peut générer un PDF propre via Ctrl+P → Enregistrer en PDF depuis Chrome en moins de 30 secondes si besoin.*
