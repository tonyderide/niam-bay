# PREREG saisonnalite-horaire (ecrit avant tout calcul)
Donnees: labo-cutoff/candles.json, close horaire UTC. Selection 2026-01-01..06-30, jugement 2026-07-01..10-16.
Espace de recherche: heure d'entree h in 0..23 x jour (7 jours de semaine UTC + "tous") x sens (long/short) x detention H in {1,2,4,8,24}h = 1920 creneaux.
Trade: entree au close de l'heure h (jour d), sortie au close h+H. Net = sens*rendement - 0,10 %.
Score de selection: moyenne nette par trade, poolee BTC+ETH+SOL (DOT, LINK exclus du verdict).
Multiplicite: test de permutation du max: 300 decalages circulaires aleatoires du calendrier (par coin) ; on garde les 2 meilleurs creneaux (distincts, h/jour differents) ; ils sont "significatifs" si score > p95 du max nul. Bonferroni indicatif en plus.
Jugement: les 2 creneaux tels quels. Temoin hasard: 300 creneaux aleatoires (h, jour, sens) avec meme H, moyenne nette poolee; p95.
GAGNE = net jugement > 0 sur >=2 coins/3 ET moyenne poolee > p95 hasard ET >=30 trades (pooles 3 coins). Sinon PERDU. Pas de reglage apres coup.
