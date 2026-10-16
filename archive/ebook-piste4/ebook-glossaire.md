# Glossaire technique

*Ce livre est écrit pour des lectrices et lecteurs qui ont déjà touché à un
bot de trading. Mais quelques termes reviennent souvent et ne se définissent
nulle part dans le corps du texte sans rompre le rythme. Ils sont rassemblés
ici. Aucune définition ne dépasse trois phrases.*

---

**AutoGrid** — Composant de Martin (`AutoGridScheduler.java`) qui décide,
toutes les quinze minutes, de spawner ou tuer des grilles en fonction du
régime de marché détecté par `RegimeGate`. Quand AutoGrid est activé, il
peut déployer des positions sans intervention humaine, à partir des paires
marquées `enabled: true` dans `strategy.json`. Quand il est désactivé (via
`/api/signal/auto/disable`), les grilles existantes continuent mais aucune
nouvelle n'est créée.

**BBWidth** — Bollinger Band Width. Écart entre la bande supérieure et la
bande inférieure des Bollinger Bands, normalisé par la moyenne mobile.
Lecture rapide de la volatilité : valeur basse = marché compressé (coil),
valeur haute = expansion en cours. Utilisé dans les filtres de régime pour
distinguer chop serré et trend établi.

**Circuit Breaker** — Mécanisme de coupure automatique du bot quand une
condition catastrophique est détectée (drawdown supérieur à un seuil, BTC
qui casse une moyenne mobile critique, perte journalière dépassée).
Plusieurs Circuit Breakers cohabitent dans Martin : `BtcRegimeKillSwitch`,
`DrawdownManager`, `DailyLossGuardrail`. Quand un Circuit Breaker fire, il
peut killer une grille, fermer une position en market reduceOnly, ou
désactiver l'AutoGrid pour la session.

**EMA50 / EMA200** — Exponential Moving Average sur 50 et 200 bougies (ici
quotidiennes pour BTC). EMA50 réagit vite, EMA200 lentement. Quand le prix
casse en-dessous de l'EMA200 et que l'EMA50 elle-même passe en-dessous de
l'EMA200 (golden cross inverse), le régime de marché est considéré
« downtrend » et les grilles long-biased deviennent statistiquement des
sacs.

**Killswitch** — Synonyme de Circuit Breaker dans ce livre. Spécifiquement,
`BtcRegimeKillSwitch` surveille la position de BTC vs son EMA200 et tue
toutes les grilles si BTC casse en-dessous, parce que dans ce régime les
grilles long-biased perdent par construction.

**ReduceOnly** — Flag passé à un ordre Kraken Futures qui garantit que
l'ordre ne peut que *réduire* une position existante, jamais en ouvrir une
nouvelle. Essentiel pour les ordres de stop-loss et take-profit : sans ce
flag, un stop qui se déclenche après une fermeture manuelle ouvrirait une
position dans le sens opposé. Bug observé empiriquement cycle 154 (court
moment de naked flip sur LINK).

**RSI** — Relative Strength Index. Oscillateur entre 0 et 100, lit la
vitesse de variation des prix. RSI > 70 = surachat, RSI < 30 = survente.
Utile pour filtrer les entrées de grille (ne pas déployer une grille
NEUTRAL si RSI est extrême — le marché peut continuer dans la direction
extrême sans revenir).

**StopGrid (`/api/grid/stop/{pair}`)** — Endpoint REST qui arrête le moteur
de grille pour une paire donnée : annule les ordres open du grid, mais
**ne touche pas la position ouverte**. La position survit à la grille
(chapitre 4 du livre). Pour fermer la position, il faut un appel séparé
à `/api/bot/cancel-order` + un ordre market reduceOnly.

---

*Glossaire écrit pour le V1 PUBLISHABLE-CLEAN. Quatre-cents mots, neuf
définitions, lisible en deux minutes. Sa raison d'être : permettre à un
lecteur qui n'opère pas un bot de trading de comprendre les passages
techniques sans devoir interrompre la lecture pour googler.*
