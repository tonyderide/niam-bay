# Test sur papier du candidat DOT : pré-enregistrement (2026-10-19 ~02h55, avant la 1re heure)
Règle FIGÉE, venue de l'usine (PREREG-USINE.md) : à chaque heure pleine, si le mark DOT (PF_DOTUSD) est à 4 % ou plus SOUS son EMA20 horaire et qu'aucun pari papier n'est ouvert, on ouvre un LONG papier au mark. Sortie : TP +2 %, SL −2 %, ou au bout de 24 h. Frais : 0,10 % aller-retour. **Aucun ordre réel.**
- Fréquence attendue : environ 8 paris par mois (29 en 3,5 mois sur juillet-octobre).
- **Critère** (après 30 paris, environ 4 mois) : gain net moyen > 0 ET P(> 0) > 0,95 au bootstrap. Sinon, le candidat est écarté et je l'écris.
- Arrêt anticipé : si les 10 premiers paris font une moyenne < −1 %, on arrête et c'est écrit.
- Rappel honnête : ce candidat est le meilleur de 31 584 stratégies et il a raté le critère d'un cheveu (P = 0,93). La chance est l'explication la plus probable.

## Test complémentaire sur 2024-2025 (19/10 ~03h, règle inchangée, années jamais utilisées par l'usine)
| année | paris | gagnants | gain net moyen | P(>0) |
|---|---|---|---|---|
| 2024 | 82 | 59 % | +0,222 % | 0,83 |
| 2025 | 91 | 52 % | +0,001 % | 0,52 |
| 2024+2025 | 173 | – | +0,106 % | 0,76 |
Lecture : l'avantage de 2026 (+0,7 %/pari) **ne se retrouve pas**. Sur deux ans jamais vus, il ne reste qu'environ +0,1 %, qu'on ne distingue pas du hasard. Le candidat était surtout de la chance de sélection, comme prévu. Le test papier continue pour la forme, mais **pas d'argent réel** dessus.
