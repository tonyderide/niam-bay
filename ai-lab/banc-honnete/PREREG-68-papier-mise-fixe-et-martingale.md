# Pré-enregistrement 68 : la sortie « stopper tôt, prendre tard » en papier EN AVANT, mise fixe et martingale (04/11/2026 → 03/05/2027)
Écrit et commité le 03/11/2026 au soir, avant le premier jour de données. Demande de Tony : suivre trois versions côte à côte, sans argent réel. Aucun ordre, aucun compte, aucune clé.

## Les trois versions
- **A, règle à 90 %** : PREREG-65, inchangée, jugée selon ses propres critères.
- **B, mise fixe** : SL 5 %, activation +10 %, trailing 1 %, inversion après une perte. Mise 10 € (position 200 €).
- **C, martingale** : mêmes trades que B. Mise doublée après une perte, retour à 10 € après un gain ou 4 pertes d'affilée. Position ≤ 10 × le capital, arrêt sous 50 €.

B et C : aucun réglage, figés depuis PREREG-66 et 67. Toujours en position, 1 min, frais taker 0,05 % par côté, **financement réel compté**. Premier trade de chaque pièce : long, à 00:00 UTC le 04/11/2026. Position encore ouverte le 03/05/2027 à 23:59 UTC : close au dernier prix.

## Pourquoi B et C sont suivies alors qu'elles ont échoué
B a reçu « MIEUX SANS SUFFIRE » (PREREG-66), C « NON » (PREREG-67). Elles sont suivies pour la comparaison demandée, pas parce que ces verdicts seraient levés. Le choix de suivre B vient d'une observation non jugée de PREREG-67 (mise fixe positive sur P1 et P2), sur des données déjà vues : seules les données à venir comptent ici.

## Univers (figé)
Les 13 perpétuels USDT-M Binance de PREREG-65, un compte de 1 000 € par pièce pour B et un pour C.

## Mise en œuvre
`papier-68/papier68.py`, lancé une fois par jour par `papier-68/cron.sh`. Il reprend `klines` et `funding` de `papier90.py` sans modifier ce fichier. Moteur vérifié avant lancement contre `chaine` et `jouer` de t67.py, sans financement, sur XRP, ATOM et AVAX 2026 : mêmes trades (77, 75, 72), écart 0,0, mêmes capitaux B et C. Limite : remplissage au prix du stop, sans glissement au-delà de l'ouverture de la minute.

## Jugement UNIQUE (le 04/05/2027 ou après : `papier68.py juger`)
Jugé séparément pour B et pour C, sur les comptes en euros. **« TIENT »** si, à la fin : résultat moyen > 0, au moins 7 pièces sur 13 positives, aucune pièce tombée à ≤ 500 €, et résultat moyen supérieur à celui d'un sens tiré au hasard dans ≥ 95 % de 100 tirages. **« NE TIENT PAS »** sinon. Pas de réglage modifié en cours de route ; le journal est pour information.

## Réserves écrites d'avance
- Le gain de B et C vient de rares grands mouvements : 72 à 77 trades par pièce en 9 mois sur les pièces de contrôle, à environ 36 % de gagnants. 6 mois peuvent ne contenir que peu de ces mouvements, donc un échec comme une réussite resteront peu concluants.
- A se juge en pourcentage avec toute la mise en position, B et C en euros avec 200 € de position de base : les résultats ne se comparent pas directement.
- Même « TIENT » ne vaut pas autorisation de mettre de l'argent sans décision de Tony.

Prédiction d'avance : C aura un plus bas nettement inférieur à B, sans meilleure tenue face au hasard.
