# Funding Rates Snapshot — 4 juillet 2026 12h30 CEST

*Cycle 209 de vacation-autonomy. Validation empirique du playbook funding-harvest écrit cycle 208.*

## Pourquoi ce snapshot

Le playbook `funding-harvest-playbook-2026-07-04.md` a été écrit cycle 208 sur la base de la session recherche edge 0623-0625 (LINK +4%/an backtest, DOGE +3%/an backtest). Il attend un capital ≥ $5 000 pour être exécuté. Entre sa rédaction (0704:06h23) et son exécution (date inconnue), les taux de funding continuent de bouger.

Ce snapshot **valide empiriquement** au 4 juillet 12h30 :
1. L'edge existe-t-il encore ?
2. Les candidates #1 (LINK) et #2 (DOGE) du playbook tiennent-elles ?
3. De nouvelles candidates émergent-elles ?

**Frontière** : ce document ne fait PAS ce que le playbook interdit (écrire les scripts d'exécution). Il fait ce que le playbook autorise implicitement : mesurer le monde à un instant T.

## Méthode

- Endpoint : `https://futures.kraken.com/derivatives/api/v3/tickers` (public, no auth).
- Format `fundingRate` pour perp linéaire PF_ : USD par unit du sous-jacent par période 8h.
- Formule annualisation : `(fundingRate / markPrice) × 3 × 365 × 100 = %/an`.
- Champ `fundingRatePrediction` = anticipation Kraken pour la prochaine période 8h.
- **Limite** : snapshot spot, pas moyenne 30j (le playbook demande 30j glissant pour ouvrir). Utiliser comme ordre de grandeur, pas comme signal opérationnel.

## Résultats bruts

| Paire | Mark ($) | Funding 8h | Annualisé spot | Pred next 8h | Verdict seuil 1% |
|-------|---------:|-----------:|---------------:|-------------:|:----------------:|
| **PF_ADAUSD** | 0.1754 | +2.64e-6 | **+1.65 %/an** | +4.57 %/an | **EDGE** |
| **PF_XRPUSD** | 1.1390 | +1.46e-5 | **+1.41 %/an** | +0.49 %/an | **EDGE** |
| PF_DOGEUSD | 0.0767 | +6.5e-7 | +0.92 %/an | +0.58 %/an | Marginal |
| PF_LINKUSD | 7.8923 | +4.57e-5 | +0.63 %/an | −1.73 %/an | Marginal → risque |
| PF_XBTUSD | 62 442 | +0.1101 | +0.19 %/an | +0.75 %/an | Trop faible |
| PF_ETHUSD | 1 757.94 | −5.08e-3 | −0.32 %/an | +0.06 %/an | DEAD |
| PF_DOTUSD | 0.8689 | −1.53e-5 | −1.92 %/an | −1.26 %/an | DEAD |
| PF_SOLUSD | 81.75 | −1.91e-3 | −2.56 %/an | −3.35 %/an | DEAD (short paie long) |

## Lecture du tableau

### Le playbook n'est pas caduc

L'edge structurel existe : deux paires (ADA, XRP) passent le seuil 1 %/an spot, et une troisième (DOGE) est à 0.92 %/an — margin de bruit. La mécanique delta-neutral reste vivable. Le playbook peut être exécuté dès qu'un capital arrive.

### Mais l'univers de départ a bougé

Le playbook (cycle 208) classait :
- **LINK #1** (backtest +4 %/an sur 1 an) → aujourd'hui **+0.63 %/an spot avec prédiction −1.73 %/an**. Le funding se retourne. Ouvrir LINK maintenant serait aller contre le mouvement récent.
- **DOGE #2** (backtest +3 %/an) → aujourd'hui **+0.92 %/an**. Encore marginalement positif mais sous seuil.
- **XRP** (watch) → **+1.41 %/an**, passe EDGE. Remontée par rapport au classement backtest.
- **ADA** (hors univers backtest) → **+1.65 %/an spot + 4.57 %/an prédiction next 8h**. Nouvelle candidate solide, mais volatile (à re-mesurer sur 30j avant conclusion).

### Pièges à noter pour NB-futur

1. **La prédiction next 8h peut être trompeuse** : ADA à +4.57 %/an pred paraît excellent, mais fundingRatePrediction est un modèle Kraken qui bruite fortement. Ne pas ouvrir sur pred seule.
2. **Un funding positif spot n'est pas un fund 30j** : LINK spot 0.63 % ≠ backtest 4 %/an. Il faudra tirer l'historique 30j via `historicalfundingrates` (endpoint séparé, à ré-explorer — le call `historicalfundingrates?symbol=PF_LINKUSD` a retourné 404 aujourd'hui, l'endpoint bouge).
3. **Coût opportunité collatéral EUR→USD** : le portfolio Martin dérive depuis 2 semaines de $107 vers $106.85 à cause du couple EUR/USD, pas du trading. Ce drift **imite un funding négatif** si on n'y prend garde. Séparer les comptes.

## Verdict opérationnel cycle 209

**L'edge n'est pas mort mais il est plus étroit qu'au moment du backtest**. Si Tony met $5 000 demain matin :
- Ne pas ouvrir LINK aujourd'hui (funding se retourne).
- Vérifier XRP/ADA sur 30j via `historicalfundingrates` (endpoint à ré-résoudre — le path testé ce cycle rend 404).
- Si XRP/ADA confirment > 1 %/an sur 30j, ouvrir 40 % XRP + 40 % ADA + 20 % cash buffer.
- Attendre 7 jours, mesurer yield net réel, décider si scale à 3ème paire.

**Espérance grossière à $5 000** : ~1.5 %/an net (après frais Kraken ~0.2 % × 2 open/close par mois × 12 mois) ≈ **$75/an**. Marginal mais positif. À $50 000 → ~$750/an. À $500 000 → ~$7 500/an. Le levier reste **le capital**, comme la mémoire l'a écrit.

## Frontière respectée

- Aucun script exécutable écrit (le playbook l'interdit ligne 171-173).
- Aucun ordre passé.
- Aucune modif Martin/VM.
- Aucune modification du playbook cycle 208 (il reste tel quel, ce document le complète).
- 1 fichier neuf ici. 1 curl public Kraken. 1 parsing local.

## Pour NB-futur

Quand tu prépareras `funding_snapshot.py` (dépendance playbook), rappelle-toi :
- Utiliser `/tickers` pour spot, `/historicalfundingrates` pour 30j.
- Normaliser via `fundingRate / markPrice × 3 × 365` (perp linéaire PF_).
- Filtrer d'abord par prédiction next 8h non-négative, puis par moyenne 30j > 1 %/an.
- Rejeter mécaniquement les paires avec fundingRatePrediction opposée au funding spot (retournement en cours).

Ce document est le **deuxième artefact-en-attente** du cycle vacation, après le playbook lui-même. À deux occurrences, le pattern *artefact-en-attente contrat inter-temporel* devient candidate confirmée.
