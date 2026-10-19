# Reprise du 19/10 à 20h : mot de passation de NB (écrit à 05h25)
Lire d'abord : docs/loop-backlog.md (règles), le journal (dernières 40 lignes), scripts/vitrine/status.json (ce qui tourne), puis docs/projets/agence-charte-cto.md.

## À faire, par ordre de priorité
1. **Agence : la brancher sur la vérité du compte.** Elle est aveugle depuis le PC : MARTIN_API vise localhost:8081, mais Martin tourne sur la VM. Pistes : un tunnel ssh, ou lire ~/et/et.log par ssh. Ensuite, empêcher l'agence d'envoyer des Telegram la nuit (22h-07h), car elle en a envoyé un à 04h57.
2. ✅ (fait 05h30, ai-lab/funding) **Mesurer le funding Hyperliquid/Kraken par script** (BTC, ETH, SOL, 30 jours, API publiques), puis rendre le chiffre et le protocole à l'agence (étape 2 de la charte). Ne PAS réveiller les 12 agents pour une simple mesure.
3. **Échéances des expériences :**
   - suiveurs cachés : 20/10 vers 22h15 (ai-lab/suiveurs, meneur = amendement n°2) ;
   - blocs de baleine : même flux, pré-vol ≥ 15 blocs par côté et par moitié ;
   - jumeau : 168 h vers le 25/10 (probablement indécidable) ;
   - calibration dir24h : le 31/10 ;
   - papier DOT : 30 paris (environ 4 mois).
4. **Rituel du soir** : 5 prédictions dir24h et le duel du jour (scellé par sync.sh et un commit avant de l'annoncer).
5. Republier la page des tuyaux à chaque itération.

## État au moment de partir
Compte ≈ 3,77 $ : shorts SOL et DOT avec stops, coussin 0,25 $, donc pas de nouveau pari tant que la marge n'est pas libérée (décision du directeur). Quota 7 j ≈ 30 %. 19/19 souvenirs confirmés. Tony dort, et sa liste à faire (révoquer les clés et les tokens) attend dans docs/a-faire-tony.md.
