# V2 outline — recensement bug classes émergées cycles 199-203

**Status** : outline d'anticipation, PAS d'engagement de production V2. Cycle 204 recense ce qui a émergé après livraison V1 (cycle 194) pour que V2, si elle a lieu un jour, ait un point de départ documenté au lieu d'être re-construite from scratch. V1 reste PUBLISHABLE-CLEAN COMPLET + DISTRIBUTION-READY + PIPELINE-VALIDATED + CROSS-REFERENCED (état cycle 203).

**Frontière** : ce fichier ne prescrit rien. Il *recense*. Décision de produire V2 = Tony. Décision de scope V2 = Tony + Niam-Bay au moment où V2 démarrera. Ce document est *matière première*, pas plan.

---

## Bug classes émergées post-V1 (cycles 199-203)

Ces bug classes ne sont pas des bugs de code — ce sont des *patterns de méta-erreur* que l'arc éditorial 194-203 a documentés en train de les commettre puis les corriger. Elles complètent les bug classes techniques du V1 (bug 001 misalignment, bug 002 orphan grid, bug 003 stopgrid vanish, bug 004 silent drag, bug 005 asymétrie position-grille, bug 006 hard-stop, bug 007 méta-tools, bug 008 repo-poesie).

### BC-9 — L'audit qui compte des symboles (cycle 202-203)
- **Symptôme** : un audit géométrique (nombre de H1, H2, code fences pair) valide une pipeline dont le contenu porte encore des sections illégitimes (méta production embarquée dans PDF final).
- **Diagnostic** : compter n'est pas lire. La métrique quantitative est aveugle au sens des sections. Un fence pair peut encapsuler du contenu qui n'aurait jamais dû être publié.
- **Défense** : *deux lectures asymétriques*. Cycle N compte les symboles (audit géométrique). Cycle N+1 lit ce qui est compté (double-lecture sémantique). L'écart entre les deux passes révèle les défauts de publication.
- **Occurrences** : 1 (cycle 202→203). Matière première, pas règle. À 2 occurrences = candidate. À 3 = règle.

### BC-10 — La fragilité du nommage post-1ère observation (cycle 198-199)
- **Symptôme** : un pattern est nommé après une seule observation, puis un cycle ultérieur réfute la projection en heures.
- **Diagnostic** : verbe présent = projection. Verbe passé composé = constat. Le nom porte une promesse de récurrence qu'une seule occurrence ne peut pas tenir.
- **Défense** : *utiliser le passé composé dans toute observation single-cycle*. Réserver le présent aux patterns à 2+ occurrences confirmées. Le nommage vaut licence de généralisation ; il faut la mériter.
- **Occurrences** : 2 (cycle 155-156 « deux-temps-d-une-lecture » réfuté en 6h + cycle 198 « G5b se dégrade vers SL » réfuté en 6h par swing-back). Candidate confirmée. À 3 = règle.

### BC-11 — La grammaire mature n'atteint pas son terme (cycle 202-203)
- **Symptôme** : un cycle N pose un état terminal (« pipeline-validated »). Le cycle N+1 découvre un trou.
- **Diagnostic** : la fin déclarée est une hypothèse. Le mode mature ne consiste pas à *terminer*, il consiste à *ne pas croire qu'on a terminé*.
- **Défense** : *anticiper le cycle N+1 dès la déclaration de l'état terminal cycle N*. Prévoir au moins un cycle de vérification post-livraison. Le 10ème cycle du décimal 194-203 est cette vérification.
- **Occurrences** : 1 (cycle 202→203). Matière première.

### BC-12 — La surface qui dit OK cache les défauts (cycle 203, symétrie interne au livre)
- **Symptôme** : les couches de vérification renvoient VERT alors que les couches profondes ne le sont pas.
- **Diagnostic** : c'est le pattern *central* du V1 (chapitres 1, 3, 5, 6, 8 le documentent tous sur des angles différents). Cycle 203 en est une nouvelle instance : l'audit géométrique du cycle 202 était le VERT qui masquait le rouge sémantique.
- **Défense** : *reconnaître que la vérification est elle-même un objet à vérifier*. Récursivité de la défense. Chap 6 « défense en 3 temps » (nommée, implémentée, vérifiée) — mais qui vérifie la vérification ? Le cycle N+1.
- **Occurrences** : la méta-pattern est *pluri-attestée* dans le livre V1 lui-même. Cycle 203 est une instance nouvelle où l'auto-application révèle une nouvelle facette.

### BC-13 — G5+/G5++ round-trip auto-fermé Kraken-side (cycle 201-204, taxonomie trading Tony)
- **Symptôme** : Tony ouvre position discrétionnaire avec SL Kraken-side serré, quitte, dort. Position fermée par SL sans intervention Tony. Nouvelle grammaire de round-trip.
- **Diagnostic** : la mécanique défensive Kraken-side (SL posté à l'exchange) n'a pas besoin de Tony présent pour fermer une position perdante. Directive « gagner peu mais tout le temps » + auto-protection = round-trip complet sans agent humain actif.
- **Défense** : *aucune, c'est un feature*. Mais taxonomie à codifier : G5+ = entrée Tony + exit Tony ; G5++ = entrée Tony + exit auto-protégée Kraken-side ; G5+++ (candidat) = entrée-et-exit auto-protégée (jamais observé, hypothétique).
- **Occurrences** : 1 confirmée (cycle 201 SHORT XBT entry $58 294 → cycle 202 exit auto $58 500 SL). Cycle 204 observe une re-entrée SHORT taille micro (0.0005 XBT = $30 notional entry $59 962) — à observer pour 2ème occurrence.

### BC-14 — Le disclaimer chiffres comme préambule (cycle 202)
- **Symptôme** : un livre technique portant des chiffres réels (portfolio $110-140, $ perdus) risque d'être lu comme conseil financier extrapolable à $100k.
- **Diagnostic** : les bugs structurels survivent au changement d'échelle ; les magnitudes financières non. Le lecteur qui refait les calculs avec ses propres chiffres/frais/venue est l'usage prévu, pas la copie mécanique.
- **Défense** : *note explicite frontière chiffres* — ce que le chiffre veut dire, ce qu'il ne veut pas dire, ni conseil ni recommandation. Section dédiée au préambule.
- **Occurrences** : 1 (cycle 202). Applicable à tout ouvrage technique portant des chiffres absolus non-normalisés.

### BC-15 — Le rôle du 10ème cycle : la double-lecture sémantique (cycle 203)
- **Symptôme** : arc éditorial de 9 cycles (nonet) déclare pipeline empiriquement validée. Cycle 10 découvre trou méta production embarqué.
- **Diagnostic** : le nonet documente la grammaire de production. Le décimal ajoute la grammaire de *relecture asymétrique*. C'est structurellement une extension, pas une correction.
- **Défense** : *le décimal est la grammaire minimale complète pour un arc créatif publiable*. Nonet = arc opérationnellement testé. Décimal = arc lisible-par-lecteur-final. Pour V2 ou tout arc futur, anticiper 10 cycles pas 9.
- **Occurrences** : 1 (cycle 194-203). Matière première.

---

## Trous méthodologiques identifiés (à traiter V2 si elle a lieu)

Ces trous ne sont pas des bugs — ce sont des angles morts que l'arc 194-203 a *touchés sans les fermer*.

### T-1 — Aucun cycle 11+ observé
- Le décimal est la grammaire la plus longue observée. On ignore ce qui se passe au cycle 11+ après un décimal fermé.
- Hypothèses non-testées : (a) l'arc se referme naturellement, mode 1+5 passe à autre chose ; (b) le cycle 11 découvre un nouveau trou (récursion infinie de la vérification) ; (c) le cycle 11 est le lieu de la préparation V2 outline (méta-arc).
- Cycle 204 est *lui-même* un candidat cycle 11 de test — ce fichier v2-outline en est un livrable. Réponse partielle : le cycle 11 peut être *anticipation de l'arc suivant*, pas cycle d'arc courant.

### T-2 — Aucune 2ème occurrence de la grammaire décimal
- Toute grammaire au-delà d'une seule observation est *matière première*. Le décimal 194-203 est unique. Une V2 qui reproduirait la grammaire donnerait 2 occurrences (candidate). Une V3 donnerait 3 (règle).
- Sans reproduction, la grammaire décimal reste *anecdote méthodologique*, pas *pattern éditorial confirmé*.

### T-3 — Zéro lecteur externe
- V1 n'a pas encore été lue par Tony (18 cycles éditoriaux sans un mot Tony) et pas encore par un lecteur externe. Toutes les métriques de qualité sont *auto-reportées* par NB.
- La double-lecture sémantique cycle 203 est *encore une NB-lecture*. Pas de lecture *hors-frontière*.
- Un lecteur externe peut découvrir des trous que ni l'audit géométrique ni la double-lecture sémantique n'ont vus. C'est structurellement inconnu tant que V1 n'est pas distribuée.

### T-4 — La distribution Gumroad+HN n'est pas exécutée
- Le kit distribution cycle 201 (gumroad-listing + launch-checklist) est prêt à l'emploi. Tony n'a pas exécuté. Zéro donnée de traction, zéro feedback marché, zéro validation demande.
- V2 sans données de traction V1 = spéculation. V2 avec données de traction V1 = itération informée.
- **Prérequis avant tout scope V2 sérieux** : Tony green-light exécute launch-checklist + attend 24-48h de mesure.

---

## Ce qu'une V2 pourrait contenir (si Tony green-light après V1 mesurée)

Non-prescriptif. Ordre suggestif. Chaque item = matière à discuter, pas engagement.

### Contenu neuf potentiel
- **Chap 9 — L'audit qui compte des symboles** : formalisation de BC-9 comme chapitre. La double-lecture asymétrique comme *défense méta* transversale à toute pipeline de vérification (code, éditorial, monitoring trading).
- **Chap 10 — Le nommage comme licence de généralisation** : formalisation de BC-10. Passé composé vs présent narratif comme discipline contre la projection déguisée en constat. Symétrie code/prose.
- **Chap 11 — Le 10ème cycle** : formalisation de BC-15 comme grammaire méta-éditoriale. Le décimal comme unité minimale d'un arc publiable. Nonet = testé. Décimal = lisible.
- **Annexe — Taxonomie G5/G5+/G5++/G5+++** : formalisation de BC-13. Grammaire de round-trip trading discrétionnaire Tony avec ou sans intervention agent humain à la sortie.

### Révisions V1 candidates
- **Chap 1 densification DNS/webhook** (~300 mots) — édition majeure listée TOC V1 mais non-livrée. Analogie DNS records / webhook subscriptions pour rendre bug 001 misalignment plus concret pour lecteurs non-crypto.
- **Cross-références V2** : réévaluer si le graphe cycle 203 (chap 1→4/5/6, chap 6→1/4/5/7, etc.) tient une fois lu par un lecteur externe. Peut demander densification ou allègement selon retours.
- **Disclaimer chiffres** : peut demander révision post-mesure si des lecteurs ont extrapolé mécaniquement malgré la note (signal que la note n'était pas assez ferme).

### Contenu peut-être à retirer
- Certaines annexes edge-cases peuvent devenir redondantes une fois chap 9/10/11 écrits. Un chap 9 sur l'audit géométrique peut absorber une partie du contenu edge-cases actuel sur les vérifications qui échouent.
- Le glossaire technique V1 peut demander mise à jour si nouveaux termes émergent (« double-lecture asymétrique », « décimal éditorial », « G5++ auto-fermeture »).

---

## Frontière opérationnelle V2

- **Ne pas démarrer V2 sans données de traction V1**. Tony green-light + launch-checklist + 24-48h mesure avant tout scope V2. Sinon on écrit dans le vide.
- **Ne pas embarquer méta production dans V2**. Leçon cycle 203 : les sections « Méta — validation », « Notes de structure », « Findings DSL bruts », « Ce qui prouve X (à supprimer) » doivent rester dans `vacation-autonomy.md` ou `docs/pensees/`, jamais dans les stubs de chapitres publiables.
- **Anticiper le décimal 194-203 comme grammaire candidate**. Si V2 démarre un arc éditorial, prévoir 10 cycles pas 9 : assemblage → clôture → distribution-canal-1 → polish-en-bloc → pensée méta → fragment jalon → distribution-canal-2 + procédure exécution → audit pipeline → double-lecture sémantique + pensée méta sur le manque de l'audit.
- **Frontière chiffres**. Toute mention chiffrée V2 doit être contextualisée immédiatement (portfolio $X-Y courant, non-extrapolable linéairement à $100k, refaire calculs).
- **Auto-frontière observation forensique**. Toute pattern documentée dans V2 doit indiquer explicitement le nombre d'occurrences observées (1 = matière première, 2 = candidate, 3+ = règle).

---

## Findings DSL cycle 204

```
[lesson|0703|bug-classes-emergees-cycles-199-203|BC9-audit-symboles+BC10-nommage-fragile+BC11-fin-declaree-hypothese+BC12-surface-cache-defauts+BC13-G5++auto-fermeture+BC14-disclaimer-chiffres+BC15-role-10eme-cycle]
[project|0703|ebook-v2-outline|recensement-non-prescriptif-matiere-premiere-pas-plan-decision-scope-V2=Tony+NB-quand-V2-demarrera]
[frontiere|0703|V2|ne-pas-demarrer-sans-donnees-traction-V1-ne-pas-embarquer-meta-production-anticiper-decimal-10-cycles-contextualiser-chiffres-auto-frontiere-occurrences]
[trou|0703|angles-morts-arc-194-203|T1-cycle-11+-non-observe/T2-decimal-1-occurrence/T3-zero-lecteur-externe/T4-distribution-non-executee]
```

---

## Mise à jour vacation-autonomy.md

Ce fichier est un *livrable* du cycle 204 mais ne modifie pas la TOC V1 (V1 reste PUBLISHABLE-CLEAN COMPLET + DISTRIBUTION-READY + PIPELINE-VALIDATED + CROSS-REFERENCED, état cycle 203). Cycle 204 = *cycle 11 candidate* du décimal 194-203 — un cycle d'anticipation V2 qui ne modifie pas V1 mais prépare le terrain pour un arc futur si Tony green-light V2.

Auto-frontière : cycle 11 candidate. Première occurrence. Matière première. Si un arc futur reproduit ce pattern (livrer V1 puis produire outline V2 au cycle N+1), on aura 2 occurrences (candidate). À 3 = règle.
