# Pré-enregistrement 29 : existe-t-il une martingale gagnante TOUS les mois ?
Écrit le 29/10/2026 à 21h1x (heure du commit), avant tout calcul de cette étude. Les bougies sont celles de PREREG-24 refait, déjà téléchargées et vérifiées SHA-256 ; aucune simulation mois par mois n'a encore été faite. Demande de Tony : « vérifie encore la martingale pour en trouver une gagnante à tous les coups en faisant des tests sur chaque mois ».

Déjà vu (famille « martingale » du registre) : martingale-verif.md (22/10, stop-et-retournement de Martin : aucun réglage gagnant durable), PREREG-24 (bot DCA : PERD), PREREG-28 A-D (SL fixe puis trailing, règle de Tony : PERD ; meilleur des 6 084 réglages BTC ne tient pas sur ETH/SOL). Cette étude change la question : non plus « gagne-t-elle en moyenne ? » mais « peut-on trouver un réglage positif **chaque mois** ? ».

## Ce que dit la théorie, avant les données
Une mise qui dépend des résultats passés ne change pas l'espérance d'un jeu sans avantage (théorème d'arrêt optionnel). Elle change la **forme** : beaucoup de petits gains, de rares grosses pertes. Une part de mois positifs élevée est donc possible même sans avantage ; la question honnête est double : (1) la part de mois positifs tient-elle hors échantillon, et (2) est-elle meilleure que sur des prix sans tendance (témoin hasard) ?

## Données
- **Choix et jugement 2026 :** BTCUSDT, ETHUSDT, SOLUSDT perpétuels Binance, bougies **1 min**, 01/2024 → 09/2026 (coupe à 48 h figées : couper(a, 2880)). Le 1 min est la résolution la plus fine disponible, donc la plus juste pour la martingale.
- **Autres pièces, jamais utilisées pour le choix :** les 250 autres perpétuels USDT de l'univers PREREG-24 refait, bougies **1 h**, 01/2024 → 09/2026, chacune coupée à son retrait (couper(a, 48)). Un mois-pièce compte s'il contient au moins 168 bougies (une semaine) ; le mois du retrait compte, sortie au dernier prix connu.

## Cadre commun à toutes les familles
- Capital **1 000 €** remis à 1 000 € au **début de chaque mois calendaire** (UTC). Toute position ouverte est fermée à la clôture de la dernière bougie du mois. Le résultat du mois = capital final − 1 000 €.
- Rapporté aussi **en continu** : 1 000 € au 01/01/2024, sans remise, jusqu'au 30/09/2026 (capital final, pire baisse depuis un sommet, ruine).
- Toujours en position (sauf la grille DCA, qui enchaîne ses cycles) : un trade s'ouvre à l'ouverture de la bougie qui suit la sortie précédente.
- **Frais :** entrée au marché taker 0,05 % ; SL et trailing = ordres stop au marché, taker 0,05 % ; **TP = ordre limite, maker 0,02 %, rempli dès que le prix le touche** (hypothèse favorable) ; ordres de sécurité DCA = limites, maker 0,02 %.
- **Mise** = ce qu'on perd si le SL est touché (hors frais). Position = mise / SL. **Levier max 10× :** si la position dépasse 10 × le capital du moment, elle est ramenée à ce maximum. **Ruine** si le capital tombe sous 50 € : on s'arrête pour le mois (ou pour toujours en continu).
- **Ordre dans une bougie (pessimiste) :** si une bougie touche à la fois le TP et le SL, c'est le SL. Si l'ouverture est déjà au-delà du SL (ou du TP), sortie à l'ouverture. Contrôle : sur les autres pièces (1 h), on calcule aussi la version optimiste (bougie ambiguë = TP) ; les deux sont rapportées. Sur BTC/ETH/SOL, le réglage figé est rejoué en 1 h pour mesurer l'effet de la résolution.

## Familles testées (toutes rapportées)
Sens pour les familles 1 à 5 : **long fixe**, **short fixe**, **inversé après une perte**, **inversé après chaque trade**. Pas SL x ∈ {0,5 ; 1 ; 2 ; 3 ; 5 ; 8} % ; TP = r × x avec r ∈ {1 (symétrique) ; 0,5 (TP à la moitié du SL, plus de trades gagnants)}. Mise de base b ∈ {1 ; 2 ; 5 ; 10 ; 20} €.
1. **Doublement classique** : perte → mise × m, gain → mise de base. m ∈ {2 ; « récupération exacte » (la mise suivante est calculée pour qu'un gain rembourse toutes les pertes de la série, frais compris, plus une mise de base)} ; plafond k ∈ {3 ; 5 ; 8 ; ∞} pertes d'affilée, après quoi on encaisse et on revient à la base. 1 920 réglages.
2. **d'Alembert** : unités u (mise = u × b) ; perte → u + 1, gain → u − 1 (min 1) ; plafond u ≤ {10 ; ∞}. 480 réglages.
3. **Fibonacci** : mise = F(j) × b (1, 1, 2, 3, 5, 8…) ; perte → j + 1, gain → j − 2 (min 0) ; plafond j ≤ {6 ; 10 ; ∞} puis retour à 0. 720 réglages.
4. **Labouchère** : liste initiale {[1, 2, 3] ; [1, 1, 1, 1]} (en unités b) ; mise = premier + dernier ; gain → on les raye ; perte → on ajoute la mise à la fin ; liste vide → nouvelle liste. Plafond : liste de plus de L ∈ {10 ; 20 ; ∞} nombres → on abandonne et on repart. 1 440 réglages.
5. **Anti-martingale (Paroli)** : gain → mise × 2, perte → base ; après k ∈ {2 ; 3 ; 4} gains d'affilée → base. 720 réglages.
6. **Grille DCA à ordres de sécurité** (règle exacte de PREREG-24, long, taille ×2 par palier, trailing, SL après le dernier OS) : les 72 réglages de PREREG-24 (d, TP, t, N, s). Capital réservé = 1 000 € (sans levier ; le signe du résultat ne dépend pas de l'échelle).
7. **Règle de Tony** : SL s, trailing t activé à +a, **inversion après une perte**, martingale. (s, a, t) ∈ s {1 ; 2 ; 3 ; 5} % × a {0,5 ; 1 ; 2} % × t {0,5 ; 1} % avec t ≤ a (20 triplets, dont la règle exacte 1 % / +1 % / 0,5 %) ; multiplicateur m ∈ {1 ; 1,5 ; 2 ; 3}, plafond k ∈ {2 ; 4 ; 6 ; ∞}, base {2 ; 5 ; 10} € (m = 1 sans plafond). 780 réglages. (Contient la combinaison figée de PREREG-28 C.)

## Choix du réglage (un par famille)
Sur **2024-2025 seulement**, BTC + ETH + SOL en 1 min : 72 mois-pièces. Score = **part des mois-pièces au résultat > 0** (un mois à 0 € ne compte pas comme positif). Départage : résultat mensuel moyen le plus élevé. Candidats : réglages au résultat mensuel moyen > 0 en 2024-2025 (sinon on prend quand même le meilleur score et on le signale). C'est le choix le plus favorable possible à la martingale, et il est figé avant de regarder 2026 et les autres pièces.

## Jugement (une seule fois, réglage figé)
- (J1) BTC + ETH + SOL, 01 → 09/2026 : 27 mois-pièces.
- (J2) Les 250 autres pièces, 1 h, tous les mois 01/2024 → 09/2026.
- **Témoin hasard :** sur J1, les minutes de chaque mois sont mélangées (formes de bougies gardées, ordre tiré au hasard, prix recollés : même volatilité, plus de tendance), 30 mélanges par mois-pièce. Rapporté : part de mois positifs et résultat moyen sur le hasard ; p = part des mélanges dont le résultat moyen ≥ le vrai.

## Verdict pré-écrit (par famille, puis global)
- **« Gagnante à tous les coups » VRAI** si : 27/27 mois positifs en J1 **et** au moins 95 % de mois-pièces positifs en J2 (version pessimiste) **et** aucune ruine. Sinon **FAUX**.
- **Avantage réel :** GAGNE si résultat mensuel moyen > 0 en J1 et en J2 et p < 0,05 contre le hasard ; NON DÉMONTRÉ si > 0 sans le reste ; PERD sinon.
- **Global :** il existe une martingale gagnante tous les mois si au moins une famille est VRAI. Avec 7 familles et ~6 100 réglages, un VRAI isolé sera revérifié (bug, 1 h optimiste, hasard) avant d'être cru.
- Rapporté pour chaque famille : réglage figé, part de mois positifs 2024-2025 / 2026 / autres pièces, pire mois, résultat cumulé, ruines ; tableau mois par mois (01/2024 → 09/2026) pour les 2-3 réglages les plus prometteurs.

## Relecture d'équité (avant calcul)
- Mêmes frais partout ; le témoin hasard les paie aussi.
- Hypothèses favorables à la martingale : TP en maker rempli au simple toucher, choix du meilleur réglage parmi ~6 100, choix sur la résolution la plus fine (1 min), remise du capital chaque mois (une ruine ne coûte qu'un mois), levier jusqu'à 10×.
- Biais défavorables connus et contrôlés : bougie ambiguë = SL (rare en 1 min ; version optimiste rapportée pour le 1 h) ; fermeture forcée en fin de mois (exigée par la question « chaque mois »).
- Le critère « positif chaque mois » ne récompense pas « ne rien faire » : 0 € n'est pas positif.
