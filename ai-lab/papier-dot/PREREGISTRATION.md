# Test sur papier du candidat DOT : pré-enregistrement (2026-10-19 ~02h55, avant la 1re heure)
Règle FIGÉE, venue de l'usine (PREREG-USINE.md) : à chaque heure pleine, si le mark DOT (PF_DOTUSD) est à 4 % ou plus SOUS son EMA20 horaire et qu'aucun pari papier n'est ouvert, on ouvre un LONG papier au mark. Sortie : TP +2 %, SL −2 %, ou au bout de 24 h. Frais : 0,10 % aller-retour. **Aucun ordre réel.**
- Fréquence attendue : environ 8 paris par mois (29 en 3,5 mois sur juillet-octobre).
- **Critère** (après 30 paris, environ 4 mois) : gain net moyen > 0 ET P(> 0) > 0,95 au bootstrap. Sinon, le candidat est écarté et je l'écris.
- Arrêt anticipé : si les 10 premiers paris font une moyenne < −1 %, on arrête et c'est écrit.
- Rappel honnête : ce candidat est le meilleur de 31 584 stratégies et il a raté le critère d'un cheveu (P = 0,93). La chance est l'explication la plus probable.
