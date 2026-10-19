# PREREG funding-extreme (écrit avant tout calcul)
Données: bougies Kraken Futures 1h (PF_XBTUSD, PF_ETHUSD, PF_SOLUSD); funding Hyperliquid horaire (BTC, ETH, SOL).
Sélection 2026-01-01→2026-06-30 ; jugement 2026-07-01→2026-10-16 (UTC), paramètres figés.
Signal: à l'heure h, funding HL de l'heure h. Extrême haut si > percentile P de la sélection (par coin), extrême bas si < percentile (100-P).
Grille: P ∈ {90,95,98}; N (durée) ∈ {4,8,24} h; sens ∈ {contrarien (haut→short, bas→long), suivi (haut→long, bas→short)}.
Entrée à l'open de la bougie suivante, sortie à l'open N bougies plus tard; pas de nouvelle entrée tant qu'une position du coin est ouverte. Frais 0,10 % aller-retour.
Choix: on teste les deux sens, on ne garde qu'UNE config (P,N,sens) = meilleur net total sur sélection (3 coins cumulés), avec ≥30 trades en sélection. Figée ensuite.
Témoin: 500 tirages; mêmes N, même nombre de trades par coin, instants aléatoires dans la période de jugement, sens aléatoire; statistique = net total (somme sur 3 coins); p95 de la distribution.
GAGNE = net jugement > 0 sur ≥2 coins/3 ET net total > p95 hasard ET ≥30 trades au jugement. Sinon PERD.
