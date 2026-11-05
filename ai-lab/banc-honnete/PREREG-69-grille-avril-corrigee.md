# Pré-enregistrement 69 : la grille d'avril (« Compounder »), telle que voulue puis corrigée
Écrit et commité le 05/11/2026, avant tout calcul. Demande de Tony : « retrouve comment on tradait en permanence, refais le même en corrigeant les erreurs ».

## Ce qui tournait (Martin, commit 0caa1f4, config du 05/04/2026)
4 grilles neutres SOL, LINK, ADA, DOT ; écart 1,2 % ; 5 niveaux à P − 1,5 e, P − 0,5 e (achats), P + 0,5 e, P + 1,5 e, P + 2,5 e (ventes) ; levier 5, soit un notionnel par niveau égal au capital de la paire ; recentrage quand le prix sort de P ± 2 e, l'inventaire restant ouvert. Résultat réel du compte du 11/02 au 30/06/2026 : environ −4 $ (frais 56 $ > gain brut 52 $).
Défauts trouvés dans le code : ordres de reprise sautés quand ils tombaient sur un niveau voisin ; stop de perte calculé sur un gain théorique, et qui annulait le stop Kraken en se déclenchant ; pas de dédoublonnage (position ADA à 9,9 fois la taille prévue) ; ordres disparus comptés comme exécutés.

## Versions (aucun réglage, tout est figé ici)
- **A, telle que voulue** : la grille ci-dessus avec les ordres de reprise toujours posés (achat exécuté à L → vente à L + e de même taille, et inversement), recentrage avec inventaire conservé, aucune protection. Paire liquidée si son capital tombe à 0.
- **B, corrigée** : A plus trois corrections. (1) Plafond d'inventaire : aucun ordre qui ferait dépasser 5 × le capital en position nette. (2) Stop réel : perte de 15 % du capital de la grille (réalisé + latent, au prix) → tout est clos au marché, pause 24 h, redémarrage au prix du moment. (3) Arrêt définitif de la paire sous 60 % du capital de départ (le « killPct 40 » de la config, enfin branché). Taille des niveaux recalculée sur le capital à chaque redémarrage.
- **C, corrigée avec le filtre de régime d'avril** : B, et la grille ne démarre que si ADX(14) < 40 et largeur de Bollinger(20, 2) < 4 % sur les bougies 15 min closes ; hors de ce régime, plus d'ordre d'ouverture, les ordres de fermeture restent, et la grille s'arrête une fois à plat.

## Exécution simulée (prudente)
Bougies 1 min Binance. Un ordre limite n'est exécuté que si le prix le dépasse strictement, à son prix ; un ordre de reprise n'est actif qu'à la minute suivante ; chemin dans la minute : ouverture → bas → haut → clôture si la bougie est verte, ouverture → haut → bas → clôture sinon. Frais 0,02 % sur les ordres limites, 0,05 % sur les clôtures au marché. Stop exécuté à son seuil, ou à l'ouverture si elle est déjà au-delà. Financement non compté.

## Données et verdict
1 000 € par paire, P1 = 01/02/2024 → 31/12/2025, P2 = 01/01 → 30/09/2026. Verdict sur SOL, LINK, ADA, DOT. Les 7 autres pièces du banc (XRP, DOGE, AVAX, LTC, BNB, BCH, ATOM) sont rapportées pour information.
**« TIENT »**, pour chaque version, si sur P1 ET P2 : résultat du portefeuille > 0, au moins 3 paires sur 4 positives, aucune paire liquidée ni arrêtée définitivement, baisse maximale du portefeuille moins forte que −30 %. **« NON »** sinon. Rapportés pour information : départs de 3 mois chaque mois (part en perte), gain avant frais, frais, avril 2026 seul.

Prédiction d'avance : A est liquidée sur au moins une paire en P1 (tendances de 2024-25) ; B et C perdent peu mais perdent, les frais dépassant le gain des allers-retours, comme dans le compte réel et dans PREREG-12 (grille BTC 0,6 % : ÉCHEC).

## Résultat (05/11/2026 — t69.py, t69.json). 1 000 € par paire, 4 paires
| | P1 (02/2024 → 12/2025) | P2 (01 → 09/2026) | Avril 2026 seul |
|---|---|---|---|
| A, voulue | −4 000 € : les 4 paires liquidées (les 7 autres aussi) | −4 000 €, idem | **+3 612 €** |
| B, corrigée | −1 934 € : les 4 paires arrêtées à 60 % après 4 stops | −1 933 €, idem | +1 705 € |
| C, corrigée + régime | −297 €, 2/4 positives, LINK arrêtée, baisse −17,5 % | −754 €, 0/4 positives, baisse −24,5 % | +226 € |

**VERDICT (pré-enregistré) : « NON » pour A, B et C.** Prédiction confirmée pour A ; B et C perdent plus que prévu. Gain avant frais négatif partout sur P1 et P2 : ce ne sont pas les frais qui tuent cette grille, ce sont les tendances. Avec un notionnel de 5 × le capital, 3 % de mouvement contre l'inventaire font 15 % de perte.
Avril 2026 explique le souvenir : un mois en fourchette (DOT entre 1,14 et 1,36, environ 170 allers-retours) où la grille voulue double le capital. Le Martin réel n'a pas eu ce gain parce que ses ordres de reprise étaient sautés. Sur 3 mois pris au hasard, A est à −4 000 € en médiane.
Contrôles avant calcul : dents de scie synthétiques (environ 12 € par aller-retour, frais 0,20 € par ordre exécuté) et baisse continue (A liquidée, B arrêtée après 4 stops). Une erreur trouvée après le premier calcul et corrigée avant ce tableau : le dernier jour de chaque période valait 0 dans la courbe, d'où une baisse de −100 % ; les verdicts n'en dépendaient pas.
