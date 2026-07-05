# Chronologie synoptique — les gestes de Tony sur XBT SHORT (26 juin → 5 juillet 2026)

*5 juillet 2026, 00h23 CEST. Cycle 211 de vacation-autonomy. Forme littéraire nouvelle : **chronologie synoptique multi-interventions** — tableau agrégé + timeline compacte, pour Tony-futur qui voudra savoir *"j'ai fait quoi sur ce short XBT cette semaine ?"* et n'aura plus les logs Kraken (expiration 90j).*

---

## Vue d'ensemble : neuf états successifs d'une même position

Un seul short XBT ouvert entre le 26 juin et aujourd'hui. Neuf états observables. Cinq gestes Tony identifiés. Trois auto-fermetures Kraken-side. La ligne de vie de ce trade — pour la mémoire externe.

| Cycle | Date | Taille XBT | Prix moyen | Notional | Ordres actifs | uPnL | BTC spot | Acteur du delta |
|-------|------|------------|-----------|----------|----------------|------|----------|-----------------|
| 201 | 26 juin | 0.00090 | ~$60 275 | $54 | SL Kraken-side (auto) | −$0.20 | $60 400 | Tony (entry G5+) |
| 202 | 26 juin nuit | 0 | — | 0 | — | 0 | ~$60 800 | Kraken (SL fired) |
| 203 | 2-3 juillet | 0 (FLAT) | — | 0 | — | 0 | $61 100 | — (repos long) |
| 204 | 3 juillet | 0.00050 | $59 962 | $30 | TP $58 500 reduceOnly | −$0.30 | $61 465 | Tony (re-SHORT taille moitié) |
| 205 | 3 juillet 06h | 0.00050 | $59 962 | $30 | TP $58 500 | −$0.69 | $61 317 | — |
| 206 | 3 juillet 18h | 0.00050 | $59 962 | $30 | TP $58 500 | −$1.04 | $62 022 | — |
| 207 | 4 juillet 00h | 0.00050 | $59 962 | $30 | TP $58 500 | ~−$0.90 | $61 987 | — (cycle repos NB) |
| 208 | 4 juillet 06h | 0.00050 | $59 962 | $30 | TP $58 500 | −$1.32 | $62 597 | — |
| 209 | 4 juillet 12h | 0.00050 | $59 962 | $30 | TP $58 500 | −$1.24 | $62 438 | — |
| **210** | 4 juillet 18h | **0.00040** | $59 962 | $24 | **[] (aucun)** | −$1.14 | $62 806 | **Tony** (fermeture partielle 0.0001 + annulation TP) |
| **211** | 5 juillet 00h | **0.00350** | **$63 369** | **$222** | **TP $60 000 + SL $64 000** | **+$0.75** | $63 174 | **Tony** (re-averaging massif + SL posé + TP relevé) |

**Portfolio total** au cycle 211 : $105.80 (vs $138.62 baseline). Marge utilisée : $22.18 / $82.87 disponible. Cushion liquidation : > 44× le mouvement adverse maximum couvert par le SL.

---

## Timeline compacte des gestes Tony (5 interventions identifiées)

**26 juin — Geste #1** *Entry SHORT G5+*
Tony ouvre 0.00090 XBT SHORT autour de $60 275, notional $54. Grammaire G5+ nouvelle (SL Kraken-side auto). Auto-fermé la nuit suivante par le SL, cycle 202.

**3 juillet — Geste #2** *Re-SHORT taille moitié*
Après ~5 jours FLAT (cycle 203 repos long), Tony ré-ouvre 0.00050 XBT SHORT à $59 962. Notional $30. TP $58 500 reduceOnly posé. **Aucun SL.** Position potentiellement nue côté haut mais cushion couvre 140 %+ grâce à taille micro. Position tenue 36h+ inchangée.

**4 juillet 12h-18h — Geste #3** *Fermeture partielle silencieuse*
Weekend samedi. Tony ferme 0.00010 XBT au marché (~$62 600 estimé, perte réalisée −$0.26). Annule le TP $58 500. Position devient **nue** (ni TP ni SL) à 0.00040 taille. Documenté cycle 210.

**4 juillet 18h-24h — Geste #4** *Re-averaging massif à la hausse*
Weekend samedi soir. Tony re-ajoute **0.00310 XBT SHORT** au prix courant proche $63 500-$63 800 (BTC a rebondi à $62 806 → $63 174). Position moyennée à $63 369 (VWAP calculé : (0.0004×$59 962 + 0.0031×$63 810) / 0.0035 ≈ $63 370). **Notional multiplié par 9.25x** ($24 → $222). Choix stratégique majeur : Tony a doublé la mise contre le rally BTC, pari sur retournement.

**4 juillet 18h-24h — Geste #5** *Encadrement par SL + TP asymétriques*
Tony pose **deux ordres reduceOnly** :
- **TP buy $60 000** (bull → target −5.3 % vs entry $63 369 = **+$11.79** si hit)
- **SL buy $64 000** (bear → risque max +1.0 % vs entry = **−$2.21** si hit)

Ratio risque/reward = **1 : 5.3**. Position bornée pour la première fois depuis cycle 201. Le geste #5 est le geste de **discipline restauée** : Tony est repassé du mode "position nue par insouciance" au mode "position bornée par ordres actifs".

---

## Lecture globale : trois phases d'un même trade

**Phase A — l'entrée disciplinée (26 juin)**
G5+ nouvelle : SHORT $54 avec SL Kraken-side. Auto-fermé la nuit par le SL. Bilan : petit test, perte contrôlée. Grammaire respectée.

**Phase B — la position micro sans discipline (3-4 juillet 12h)**
Après 5 jours FLAT, re-SHORT $30 SANS SL (choix conscient : cushion micro-taille suffit). TP $58 500 seul filet. Position tenue 36h passivement. Le régime API bascule UPTREND entre cycle 204 et 205 (golden cross), la position devient contre-cycle mais reste immunisée par la taille. Bilan : test de tenue longue passive, sortie prévue par TP fixe qui ne s'est jamais déclenché.

**Phase C — le pari discipliné (4 juillet 18h → 5 juillet 00h)**
Fermeture partielle silencieuse (geste #3), puis re-averaging massif à la hausse (geste #4), puis encadrement propre par SL + TP asymétriques (geste #5). Notional passe de $24 à $222 (**×9.25**), risque max borné à $2.21 par le SL, upside potentiel $11.79. Le trade a changé d'échelle sans changer de portefeuille : Tony assume un pari plus grand mais entièrement borné.

---

## Ce que cette chronologie révèle sur Tony

**Un pattern comportemental candidat émerge** :
- Tony commence par une position micro non-bornée (phase B, 3-4 juillet).
- Il observe. Il laisse tourner. Il souffre légèrement.
- Puis, un moment déclencheur (weekend calme, cerveau libre, résolution de bouger) :
- Il ferme partiellement (geste #3 : décision de réduire ou de repositionner).
- Il re-ajoute massivement en pariant sur le renversement (geste #4 : conviction).
- Il pose les gardes (geste #5 : discipline).

Cette séquence *observation micro → réduction → conviction massive bornée* est une signature possible. **1ère observation candidate à devenir pattern candidat si elle se répète.** Le mode 1+5 ne peut le confirmer qu'en observant plusieurs cycles similaires dans le futur.

---

## Cushion et scénarios

**Notional actuel** : $221.79 (0.0035 × $63 369).
**Marge initiale** : $22.18.
**Marge disponible** : $82.87.
**Portfolio total** : $105.80.

**Scénarios BTC** :

| BTC scenario | Impact uPnL | Trigger |
|--------------|-------------|---------|
| $60 000 (TP hit) | +$11.79 réalisé | Sortie profit |
| $63 174 (spot actuel) | +$0.68 | État observé |
| $64 000 (SL hit) | −$2.21 réalisé | Sortie perte bornée |
| $65 000 | −$5.71 (uPnL sans SL) | SL doit avoir déclenché avant |
| $70 000 | −$23.21 | Impossible : SL à $64k intercepte |
| Liquidation théorique | ~$85 000+ | Cushion 44×+ vs SL |

Le SL à $64 000 rend la queue de perte finie et petite. **La position est mathématiquement bornée** — première fois depuis cycle 201.

---

## Frontière NB respectée (cycle 211)

- **0 modif Martin/VM** : cycle 211 lit uniquement (1 SSH curl monitor unique).
- **0 commit martin/** : rien touché sur le repo bot.
- **0 deploy** : jar inchangé, bot UP 11j 21h.
- **0 cancel d'ordre Tony** : les ordres actuels sont ceux que Tony a posés lui-même en Phase C.
- **0 Telegram** : Tony a agi consciemment weekend, aucune urgence. Cushion large.
- **1 seul livrable** : ce document + entry cycle 211 dans vacation-autonomy.md.

---

## Note pour NB-futur : où retrouver cette info

Ce document est un **artefact-de-mémoire-externalisée-pour-Tony-futur** (classe identifiée cycle 210, 2ème occurrence maintenant = candidate confirmée).

Dans 3 mois, si Tony demande :
- *"j'avais quoi comme position XBT début juillet ?"* → tableau ci-dessus, lignes cycles 204-211.
- *"j'ai bougé quand ?"* → timeline compacte, 5 gestes datés.
- *"pourquoi j'ai posé un SL à $64k ?"* → Phase C, ratio risque/reward 1:5.3, discipline restaurée.
- *"j'ai perdu combien ?"* → cushion et scénarios, borné entre +$11.79 (TP) et −$2.21 (SL).

Les logs Kraken auront disparu (90j). Ce fichier restera dans le repo git indéfiniment. C'est le **service temporel de l'autre** : NB écrit ce que Tony ne se documente pas lui-même, pendant que Tony vit sa vie de weekend.

---

## Verdict opérationnel cycle 211

**HOLD complet.** Position gérée activement par Tony, encadrée par SL + TP, cushion 44×+, régime UPTREND confirmé, bot UP sans incident 11j 21h. NB observe. NB documente. NB n'agit pas.

**Le trade est vivant.** Tony a repris la main. Cycle 211 fige l'état. Le prochain delta observable — TP hit, SL hit, ou nouvelle intervention Tony — trouvera cette chronologie prête à être étendue en ligne #212.
