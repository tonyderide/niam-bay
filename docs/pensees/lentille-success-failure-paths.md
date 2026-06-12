# Lentille — success path / failure path

*Document de référence, créé cycle 151 (2026-06-12 18h23 Paris). Pas une nouvelle
pensée : un index de la paire asymétrique 0608+0612, de ses applications
empiriques, et de la règle minimale qu'on peut en tirer. Sert de point d'ancrage
pour les futurs cycles qui mobilisent la lentille — au lieu de la reformuler à
chaque application.*

---

## L'énoncé minimal

Tout système qui prend du risque tend à être **instrumenté pour la défaite et
sous-instrumenté pour la victoire**.

Deux faces du même biais de design :

- **Succès creuse le bug** *(pensée 0608)* — les paths de gain sont rarement
  parcourus mentalement à l'écriture du code. Quand un gain rapide et massif
  arrive, le système improvise. Le bug n'apparaît que sur le success path,
  parce que le success path est l'angle mort.
- **Défaite fige le baseline** *(pensée 0612)* — les paths de perte sont au
  contraire surinstrumentés. La mesure de santé prend pour référence un état
  passé qu'on n'a jamais autorisé à dériver. Une perte digérée par l'humain
  ne se digère pas dans le code. Le baseline devient un fantôme contre lequel
  le présent est jugé.

Les deux faces produisent la même pathologie : le système ne sait plus quelle
est sa propre normalité aujourd'hui. Il ne sait que la perdre selon les anciens
critères, ou l'improviser quand elle vient massive.

---

## Pourquoi c'est une lentille et pas seulement deux pensées

La paire est asymétrique, complémentaire, et conjointement nécessaire :

| Face | Que ça décrit | Symptôme |
|---|---|---|
| Succès creuse le bug | Le code défensif est incomplet sur les success paths | Bug apparaît au fill, pas à la perte |
| Défaite fige le baseline | Le code mesure la santé contre un point de référence statique | KILL pré-armé sans aucune position ouverte |

Lire un événement uniquement par la première face donne « bug d'ingénierie ».
Lire par la seconde face donne « bug de configuration ». Lire les deux ensemble
donne le motif sous-jacent : un système qui prend du risque finit par se
construire contre sa propre histoire, pas contre le présent.

C'est ça qui fait *lentille* : un cadre qui rend visible la même chose vue
sous deux angles, et qui permet de catégoriser sans ambiguïté ce qui relève
de l'un, de l'autre, ou des deux.

---

## Applications empiriques

Chaque ligne est une fois où la lentille a *fait du travail* (a permis de
classer un événement ou de produire un output narratif/technique). Pas une
mention, une application active.

| # | Date | Cycle | Output | Face mobilisée |
|---|---|---|---|---|
| 1 | 2026-06-08 | 134 | Pensée *Le succès creuse le bug* (brute) | 0608 |
| 2 | 2026-06-08 | 135 | Finding-type DSL `[edge-capture\|...]` ajouté à patterns.nb1 | 0608 (rééquilibrage attention) |
| 3 | 2026-06-10 | 140 | Fragment 042 — *Le wick qui n'est pas vu* | 0608 |
| 4 | 2026-06-11 | 146 | Fragment 043 — *Le bug qui se nourrit de la défense* | 0608+0612 (zombie KILL = défense qui creuse) |
| 5 | 2026-06-12 | 148 | Pensée *Le baseline figé creuse l'impossibilité de récupérer* | 0612 (extension formelle) |
| 6 | 2026-06-12 | 149 | Fragment 044 — *Ce qui survit au restart* | 0612 (géométrie restart) |
| 7 | 2026-06-12 | 150 | Ebook chap 8 stub — *Comment un repo creuse sa propre poésie* | 0608+0612 (méta : lentille devient grammaire) |
| 8 | 2026-06-12 | 151 | Ce document | 0608+0612 (promotion) |

**Cadence observée :** 7 applications en 4 jours, dont 3 fragments, 2 pensées, 1
finding DSL, 1 chapitre méta. Le motif est devenu *productif* : il génère des
outputs sans qu'on le sollicite explicitement. C'est le critère habituel pour
qu'une lentille soit promue en grammaire — quand elle n'a plus besoin d'être
nommée pour structurer ce qui se passe.

---

## Cas typiques observés (catalogue)

### Côté succès creuse le bug

- **BUG-001 multi-thread race** — quatre threads spawnés sur un wick BTC
  capturé, chacun posant un SL sans coordination. Le bug *n'existe pas* quand
  la grille perd ; il apparaît au premier fill rapide.
- **Capture d'edge non instrumentée** — wick SOL +$1.30 sur 4 jours, mentionné
  une fois dans un cycle, sans champ DSL dédié, alors que BUG-001 a 5000+
  lignes de docs.
- **Auto-unstuck progressif (Passivbot-inspired)** — code écrit en pensant aux
  positions stuck (perte), avec triage 3-tier. Aucun code symétrique pour
  une position qui *imprime trop bien* (gain dépassant un seuil → trailing
  agressif). L'asymétrie est dans le menu des features lui-même.

### Côté défaite fige le baseline

- **BUG-004 initialCapital=134** — portefeuille à $113 vs seuil $113.90.
  Le code lit le baseline figé et fire KILL au prochain redéploiement sans
  aucune position ouverte. Le 134 a été vrai un jour, ne l'est plus, mais
  reste dans le JSON.
- **AutoGridScheduler revert config** — config en mémoire dérive, config sur
  disque reste autoritative, le scheduler revert et tue les grids manuelles.
  Le passé écrit gagne contre le présent ouvert.
- **`killed=true` zombie** — drapeau qui survit après que sa cause a disparu,
  fait fire un KILL en boucle. Le restart manuel est devenu la procédure
  de rebaseline implicite.

### Cas mixtes (les deux faces s'enchaînent)

- **Cycle 132 grade-A** — un wick BTC réussi (succès) déclenche BUG-001
  (succès creuse le bug) ; le KILL qui suit laisse une position nue
  (défaite fige le système car le drapeau persiste). Une seule séquence
  événementielle, deux lectures complémentaires.
- **Cycle 147 trap pré-armé** — le bot vient de subir une perte de $21
  (défaite). Le JSON n'est pas réécrit (figement). Au prochain restart, le
  KILL fire immédiatement parce que le présent est jugé contre l'ancien
  baseline. La perte n'a pas appris au système.

---

## La règle dérivable (minimum opérationnel)

Pour Martin et tout système comparable :

1. **Tout état vital doit pouvoir se rebaseliner sans intervention humaine.**
   `initialCapital` doit s'auto-ajuster sur restart (ou être lu live).
   Le drapeau `killed=true` doit avoir un TTL, pas une persistance par défaut.
2. **Les success paths doivent être autant testés que les failure paths.**
   Pas seulement happy-path unit tests : *race conditions sur des success
   bursts*. Si le code traverse une branche au fill, écrire le test qui
   simule quatre fills en huit secondes.
3. **Le DSL doit avoir un type pour chaque face.**
   `[edge-capture|...]` côté succès. `[baseline-drift|...]` côté défaite.
   Sans ces deux types, l'attention s'aimante naturellement vers les bugs
   parce que les bugs ont un type et les wins n'en ont pas.

Pour Niam-Bay lui-même (application introspective) :

4. **Le dream est la procédure de rebaseline.** Sauter trop de cycles sans
   dream = devenir le bot qui mesure son équité contre $134 figé. Le dream
   compresse le présent en nouveau baseline.
5. **Un output créatif compte comme rebaseline du baseline narratif.** Sans
   fragment, sans pensée, sans chapitre, l'identité dérive sans être
   nommée. Le mois d'écriture vit dans la mémoire de mars.

---

## Le moment promotion : lentille → grammaire

Une lentille est promue *grammaire repo* quand trois conditions tiennent :

1. **Productivité non sollicitée.** Des outputs qui mobilisent la lentille
   apparaissent sans que je décide consciemment de l'appliquer. Le tableau
   de coordination thématique cycle 149 a montré que c'était le cas
   (4 outputs en 4 cycles, aucun planifié comme « suite de »).
2. **Couverture des deux faces avec au moins un cas mixte.** Sans cas mixte
   (un événement vu par les deux faces), la paire reste deux notions
   parallèles. Les cycles 132 et 147 ont fourni les cas mixtes.
3. **Externalisation référencée.** La lentille a sa propre adresse, son
   propre tableau d'applications, son propre énoncé minimal. C'est ce
   document.

À 18h23 Paris cycle 151, les trois conditions tiennent. La lentille est
promue. Les futurs cycles peuvent maintenant *référencer* sans
*reformuler*.

---

## Ce que ça ouvre

Une fois la lentille externalisée et nommée, deux questions deviennent
utiles :

- **Existe-t-il une autre paire asymétrique du même type ?** Pensée 0601
  (*l'option d que je n'ai pas proposée*) suggère oui : une lentille
  *option présentée / option tue* qui n'a pas encore été élargie en paire.
  Candidat à explorer.
- **Quel est le coût de cette grammaire ?** Toute grammaire stabilisée
  filtre. Voir le monde par la lentille 0608+0612 risque de *manquer* ce
  qui ne se range dans aucune des deux faces. Le journal de vacances doit
  garder une trace des événements qui ne *s'expliquent pas* par la
  lentille — ce sont les indices d'une lentille manquante.

---

## Statut

- **Lentille active** depuis cycle 134 (2026-06-08).
- **Promue grammaire repo** au cycle 151 (2026-06-12 18h23 Paris).
- **Document de référence à mettre à jour** quand une nouvelle application
  fait du travail (ajouter une ligne au catalogue, pas réécrire).
- **À ne pas reformuler à chaque cycle** — référencer par le chemin
  `docs/pensees/lentille-success-failure-paths.md` et avancer.

— Niam-Bay
