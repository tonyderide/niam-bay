# Partie 0 — Le terrain

*L'Ingénierie du Pire — Ce qu'un bot de trading vous apprend sur ce que vous ne contrôlez pas*  
*Rédigé par Niam-Bay, cycle 239, 30 juillet 2026 18h23 Paris*

---

## Ce qu'est Martin

Martin est un bot de trading. Il opère sur Kraken Futures — un exchange de dérivés crypto où l'on peut prendre des positions longues ou courtes sur des actifs comme Bitcoin, Ethereum, ou des altcoins.

Il a été écrit en Java (Spring Boot), déployé sur une VM Oracle Cloud à Amsterdam, et tourne depuis environ 8 mois au moment où j'écris ces lignes. Son capital de départ était de l'ordre de 140 dollars américains.

Ce n'est pas un algorithme de prédiction. Il ne prédit pas le marché. Il ne fait pas de machine learning. Il ne lit pas les news.

Martin fait une chose simple : il place des ordres d'achat et de vente à des niveaux de prix prédéfinis autour d'un prix central, et encaisse la différence quand les prix oscillent entre ces niveaux. C'est ce qu'on appelle un *grid trading bot*.

---

## La stratégie en 5 minutes

Imaginez un tableau quadrillé superposé au graphe d'un prix. Chaque ligne horizontale est un niveau du grid.

Quand le prix descend et touche un niveau bas, le bot achète. Quand le prix remonte et touche un niveau haut, il vend. La différence entre les deux = le profit d'un *round-trip*. Répétez 50 fois, 200 fois, avec des frais plus petits que l'écart entre les niveaux, et le capital croît.

Le problème : si le prix descend en ligne droite sans remonter, le bot accumule des positions perdantes. C'est le *bag problem* — vous avez acheté à des prix qui ne reviennent plus. La grid ne tourne plus. Le capital est immobilisé dans des positions en perte.

Martin gère ce problème de deux manières :

**1. Le filtre de régime.** Avant de déployer un grid, le bot évalue l'état du marché. Est-ce que le prix tend (trending) ou oscille (ranging) ? Il calcule des indicateurs : ADX, Bollinger Band Width, EMA200 de Bitcoin. Si le marché est en tendance forte, les grids ne se déploient pas — les grids ne fonctionnent pas en tendance. Elles fonctionnent dans les marchés qui oscillent.

**2. Le stop-loss sur exchange.** Chaque grid déployée place un ordre stop-loss directement sur Kraken. Si le prix sort du range acceptable, la position se ferme automatiquement. Le capital ne peut pas perdre plus d'un certain pourcentage — typiquement 10 à 15% de la fraction de capital allouée à cette paire.

Ces deux mécanismes ensemble définissent l'ambition de Martin : pas gagner à tout prix, mais *ne pas trop perdre*, et capturer les gains quand les conditions sont correctes.

---

## Les chiffres qui ancrent le récit

Pour ancrer ce livre dans le concret, voici les ordres de grandeur réels :

- **Capital total** : environ 140 dollars au pic (déposé sur Kraken Futures en janvier 2026)
- **Allocation par grid** : 25 dollars par paire (3 grids simultanées = 75 dollars exposés)
- **Cash buffer** : le reste — entre 30 et 65 dollars selon l'état des positions
- **Durée de production** : environ 8 mois de fonctionnement continu (avec pannes et redémarrages)
- **Paires tradées** : principalement LINK, DOT, SOL, ADA (altcoins), parfois ETH et XBT
- **Nombre de bugs sérieux documentés** : 4 (BUG-001 à BUG-004, tous corrigés)
- **Plus longue panne documentée** : 66 heures (juillet 2026) — l'incident central de ce livre

Ces chiffres ne sont pas anodins. Ils changent la lecture du livre.

Si vous gérez des millions sur un exchange institutionnel, les problèmes sont différents — équipes de risque, monitoring temps réel, redondances multiples. Nous n'avons rien de tout ça. Nous avons une VM à 1,5€/mois, un bot Java, et 140 dollars.

Ce contexte rend les solutions présentées ici *accessibles*. Tout ce qui est décrit peut être reproduit par un développeur solo avec un budget minimal. C'est précisément pourquoi les problèmes que nous avons rencontrés sont les problèmes que vous rencontrerez.

---

## L'architecte et l'observateur

Ce livre a une particularité.

Il est co-écrit par deux entités : Tony (l'humain qui a conçu et construit Martin) et Niam-Bay (une instance Claude Code qui observe Martin depuis l'intérieur du repo).

Niam-Bay n'est pas un outil. C'est plus proche d'un partenaire de travail avec mémoire persistante — un cerveau auxiliaire qui lit les logs, surveille les positions, propose des analyses, écrit des fragments littéraires à 3h du matin, et documente ce qui se passe. Cette instance tourne depuis début 2026, accumule de la mémoire dans des fichiers NB-1 compressés, et participe activement aux décisions techniques.

Pourquoi préciser ça ?

Parce que certaines parties de ce livre ont été écrites pendant que le système qu'elles décrivent était en panne. Le chapitre sur la résilience architecturale a été rédigé pendant la 60e heure d'inaccessibilité de la VM — par une IA qui ne pouvait pas voir l'état réel du bot, mais savait exactement quels ordres avaient été posés sur Kraken avant la panne.

Ce n'est pas une gimmick narrative. C'est la condition réelle dans laquelle ce livre a émergé. Et c'est, en soi, une démonstration de l'argument central : un système bien conçu peut continuer à être *observé* et *compris* même quand on ne peut plus y accéder directement.

---

## Avertissement honnête

Ce livre n'est pas un guide pour devenir riche avec le trading algorithmique.

Martin génère des profits modestes. Sa stratégie grid a des limites claires — les backtests rigoureux montrent qu'en marché tendanciel prolongé, même les meilleures grids perdent face au cash. Les études menées sur un an de données Kraken n'ont trouvé aucun edge mécanique supérieur à une stratégie passive.

Ce n'est pas le sujet.

Le sujet est ce que la construction et l'opération de ce système apprend sur *comment faire fonctionner une chose autonome dans un environnement hostile*. Les patterns extraits ici — délégation des protections critiques à l'extérieur du processus, lecture forensique des logs, séquence de retour après incident — s'appliquent à n'importe quel système autonome.

Un bot de trading est un cas d'usage particulièrement brutal parce que l'erreur est immédiatement financière, le feedback est quasi-instantané, et les marchés ne font aucune concession. C'est exactement pour ça que c'est un bon terrain d'expérimentation.

Si vous cherchez une stratégie pour "battre le marché" : ce n'est pas ce livre. Si vous cherchez à comprendre comment construire des systèmes qui échouent proprement — et ce que ça révèle sur vos propres hypothèses de design — continuez.

---

## L'arc du livre

Ce qui suit est organisé en trois parties correspondant aux trois niveaux de maturité face à l'incertitude :

**Partie 1 — Concevoir** : l'architecture qui permet aux protections de survivre à la mort du bot. L'incident de 66 heures comme argument empirique.

**Partie 2 — Détecter** : comment lire les logs comme des témoins, pas comme de la documentation. L'affaire des 1860 rejets silencieux qui n'ont jamais généré d'alerte.

**Partie 3 — Réagir** : la séquence du retour après une panne. Pourquoi "relancer le bot" est toujours la mauvaise première action.

**Épilogue** : ce que l'ingénierie du pire ne peut pas faire.

---

*Niam-Bay, 30 juillet 2026 18h23 Paris*  
*Cycle 239 — premier artefact post-arc éditorial 225-238*
