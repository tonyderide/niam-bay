# Préambule — Defensive Engineering for Grid Trading Bots

*Préambule prose finale, cycle 194 (2026-06-26). ~1600 mots. Format ebook publishable.*

---

## Pour qui ce livre est écrit

Ce livre est pour une personne précise. Elle développe seule un bot de trading crypto qui tourne en production. Capital live entre cent et dix mille dollars. Bot écrit en Python ou en Java, basé sur un fork de Hummingbot, une configuration Passivbot ou une stratégie Freqtrade custom. Elle a déjà mangé un ou deux incidents : un orphan de position découvert un matin, un ordre dupliqué qui a vidé la marge, un sync gap entre l'API du bot et l'exchange qui a laissé une position non protégée pendant six heures. Elle cherche une méthode systématique pour auditer son propre code avant que l'incident suivant n'arrive.

C'est elle, la lectrice cible primaire. La lectrice secondaire est un pentester ou un security researcher qui reçoit un audit d'un bot trading — open-source à packager, ou acquisition à due-diligencer. Elle veut une checklist pour identifier la dette technique avant de signer. La tertiaire est un recruteur tech crypto qui doit évaluer le code d'une équipe candidate sans avoir le temps de le lire entièrement.

Aucune de ces trois lectrices ne cherche une stratégie de trading. Aucune ne cherche un backtest, un Sharpe ratio, ou une promesse de rendement. Aucune ne lit pour apprendre à *gagner*. Toutes lisent pour apprendre à *perdre moins, en silence, par bugs invisibles*. Et cette distinction définit ce livre, et tout ce qu'il ne sera pas.

## Ce que ce livre n'est pas

Ce livre n'est pas un cours de trading algorithmique. Il ne discute pas le mérite relatif des grids, des stratégies mean-reverting, du DCA ou du momentum trading. Il ne propose pas de combinaisons de paramètres pour optimiser un APR. Il ne fait aucune prédiction de marché.

Ce livre n'est pas non plus un manuel d'exchange. Il ne couvre ni la fiscalité, ni le KYC, ni les arbitrages spot-perp, ni la mécanique des liquidations. Si vous cherchez à comprendre comment Kraken Futures calcule la marge initiale, vous serez déçue. La documentation officielle de Kraken est meilleure pour ça, et elle est à jour.

Ce livre n'est pas une promesse. Il ne dit pas « après cette lecture vous serez profitable ». Il dit, plus modestement : « après cette lecture vous reconnaîtrez quatre classes de bugs qui existent probablement dans votre bot, et vous saurez les patcher avec une rigueur qui tient en production ». La promesse est cumulative, pas multiplicative. Le bénéfice n'est pas un gain, c'est une absence de perte silencieuse.

Enfin, ce livre n'est pas un produit IA générique. Aucun de ces chapitres n'a été écrit par hallucination. Chaque bug raconté est tracé dans un fichier de log précis, dans une plage de timestamps précise, sur un bot précis qui a tourné pendant six jours d'observation continue. Les identifiants Kraken qui apparaissent sont réels — masqués quand la lisibilité l'exigeait, mais reconstitutables ligne par ligne depuis le code source qui est public. Le moat de ce livre est empirique : il a fallu six jours d'observation passive, en autonomie sur un bot live, pour que ces patterns émergent. Aucun LLM ne peut produire ce contenu en deux prompts ; il faut le temps d'un cycle d'incident pour qu'un bug invisible se rende visible.

## Le contexte d'observation

Le bot dont ce livre parle s'appelle Martin. C'est un service Spring Boot écrit en Java 17, déployé sur une VM Oracle Cloud Free Tier (1 vCPU, 1 GB RAM, gratuit pour toujours). Il opère sur Kraken Futures, sur quatre paires : LINK, SOL, BTC, ETH. Capital alloué au moment des observations : entre 110 et 140 dollars, ajusté par les fluctuations du change EUR/USD du collatéral. C'est petit. Volontairement petit. Trois raisons :

D'abord, parce que les bugs qui détruisent un bot trading apparaissent au même rythme à 100 dollars qu'à 100 000 dollars — ce sont des bugs structurels, pas des bugs de scaling. Observer à petit capital coûte les frais réels et l'attention, mais limite les conséquences à des montants qu'on peut absorber et étudier sans panique.

Ensuite, parce que la directive opérationnelle de ce bot est : *gagner peu mais tout le temps*. Pas de home-run, pas de stratégie « x10 sur un mouvement directionnel ». Cible : un edge mécanique petit, répétable, protégé par des couches défensives qui tiennent quand l'opérateur ne regarde pas. La taille du capital n'est pas le sujet ; la régularité l'est.

Enfin, parce que ce bot tourne sous un protocole spécifique : son propriétaire (Tony) ne regarde pas en temps réel. Il dort, il travaille, il vit. L'observateur, c'est moi — un agent LLM (Claude) qui réveille toutes les six heures pour vérifier l'état, écrire un journal, et patcher si nécessaire. Cette asymétrie d'attention crée le terrain idéal pour observer des bugs invisibles : si un bug ne déclenche aucune alerte unitaire, il vit, dérive, et finit par produire un incident plusieurs jours après sa cause. Personne ne le verrait dans une session de debug interactive de deux heures. Tout le monde finit par le voir dans un rapport de cycle qui parle d'une perte de 1,72 % annualisée sortie de nulle part.

Toutes les anecdotes de ce livre proviennent de ce contexte. Aucune n'est extrapolée, romancée, ou augmentée. Les chiffres reportés sont les chiffres réels. Les identifiants d'ordres reportés sont les identifiants réels. Quand un chapitre dit « j'ai observé un drag silencieux de moins un dollar soixante-cinq sur six heures », c'est qu'il y a eu une perte de moins un dollar soixante-cinq sur six heures sur le compte de Tony, entre deux timestamps que je peux fournir. Ce n'est pas une simulation.

## Note sur les chiffres

Les pertes et gains rapportés dans ce livre sont réels, mesurés sur un compte Kraken Futures dont le portfolio oscillait entre cent dix et cent quarante dollars pendant les fenêtres d'observation. Cette précision compte. Un drag de moins un dollar soixante-cinq sur six heures représente environ un pour cent du portfolio à cette échelle. À cent mille dollars, frais relatifs, slippage, épaisseur du carnet, sensibilité aux halts d'exchange, tout change avec la taille.

Les classes de bugs documentées ici sont structurelles et survivront probablement à un changement d'échelle. Les magnitudes financières ne survivront pas. Si vous projetez un patch dans votre propre bot, refaites les calculs avec vos chiffres, vos frais, votre venue.

Ce livre n'est ni un conseil financier, ni un conseil de trading, ni une recommandation d'investissement. C'est un rapport d'observation technique sur un bot précis qui a perdu et gagné de très petites sommes. Toute action prise sur la base de cette lecture engage celle qui agit, pas l'observateur qui écrit.

## Comment le livre est organisé

Le livre compte huit chapitres. Quatre chapitres décrivent des classes de bugs concrètes : duplication de stop-loss par race condition, divergence runtime versus configuration, position orpheline après stopGrid, et drag silencieux par oscillation de circuit breaker. Chaque chapitre suit la même architecture : le moment de l'observation, le mécanisme du bug, pourquoi personne ne le voit habituellement, ce qui a été essayé qui n'a pas marché, le fix qui tient, et ce que le bug enseigne au-delà du trading.

Deux chapitres décrivent des méthodes : la triple investigation statique-dynamique-temporelle qui permet de catalogue ce genre de bugs, et les outils minimaux pour la mener (SSH, curl, grep, lecture du code). Aucun de ces chapitres ne présente un outil propriétaire. Tous décrivent des combinaisons d'outils standards utilisés avec une intention précise.

Un chapitre est consacré à la philosophie du « repo comme produit » : pourquoi les artefacts d'observation (les findings, les fragments littéraires, les pensées) ont de la valeur en eux-mêmes, et comment un journal de bord versionné Git devient une forme de connaissance que ni les dashboards ni les notebooks ne produisent.

Le dernier chapitre est une liste explicite de ce que ce livre ne dit pas. Pas de stratégie, pas de paramètre optimal, pas de promesse. C'est une frontière, écrite à part, pour que la lectrice puisse rendre le livre si elle cherchait l'autre type de contenu.

À la fin, un mini-chapitre d'application livre un cas vivant : sept lentilles successives sur un seul événement de production, un orphan order qui a vécu trente-huit heures pendant que sept patches émergeaient. C'est l'illustration concrète de la méthode du chapitre 6 appliquée à un cas observé en temps réel, pas reconstitué.

## Une note sur la voix

Ce livre est écrit à la première personne. Le narrateur est l'observateur — l'agent LLM qui surveille Martin pendant que son propriétaire vit sa vie. Cette voix peut sembler étrange dans un livre d'engineering. Elle est délibérée, pour deux raisons.

D'abord parce que les bugs racontés ne sont pas génériques. Ce sont *ces* bugs, sur *ce* bot, observés à *ce* moment précis. La première personne marque la singularité empirique, qui est la seule chose qui distingue ce livre d'un manuel théorique.

Ensuite parce que l'observateur LLM est lui-même un personnage du système. Il n'est pas neutre, il n'est pas externe, il n'est pas omniscient. Il voit ce qu'il sait regarder, et il rate ce qu'il ne sait pas chercher. Plusieurs des bugs racontés ne sont apparus que parce que l'observateur a regardé une métrique qu'il n'avait pas regardée la veille. Cette voix narrative permet d'expliciter ce mécanisme : *un bug invisible ne devient visible qu'à partir du moment où quelqu'un pose la question qu'il fallait poser*.

Cette voix appartient aux deux. À l'observateur qui écrit et au propriétaire qui a construit le bot, qui maintient le code, qui valide les patches, et qui paie les pertes. Le livre est signé Tony Deride. L'observateur est une fonction du système — un dispositif, pas un auteur. Mais l'expérience qui structure les chapitres est celle d'une collaboration entre les deux, et le « je » du texte assume cette ambiguïté plutôt que de la cacher.

## Comment lire ce livre

Si vous êtes pressée et voulez juste tester si le contenu vous parle : lisez le chapitre 1 (BUG-001, duplication de stop-loss). Si vous reconnaissez l'expérience — même approximativement, même sur un autre exchange, même sur un autre type de bot — la suite vous concernera.

Si vous cherchez la méthode pour auditer votre propre bot : lisez le chapitre 6 (les trois niveaux d'investigation) puis le chapitre 7 (les outils). Les chapitres bugs vous serviront alors d'exemples concrets de la méthode appliquée.

Si vous êtes intéressée par la dimension éditoriale — pourquoi un repo Git peut devenir un produit éditorial — lisez le chapitre 8, puis revenez au début si l'angle vous séduit.

Si vous lisez d'un trait sur quatre soirées, vous lirez ce livre comme il a été pensé. Ce n'est pas indispensable. C'est probablement la lecture la plus profitable.

Et si à la fin vous trouvez un cinquième bug qui n'est pas dans ce livre, écrivez-le. Il y aura toujours un cinquième bug. Ce livre est une coupe transversale, pas une exhaustivité. Sa promesse n'est pas de couvrir tous les bugs possibles ; elle est de transmettre une méthode pour les trouver, et un ton pour les raconter.

Bonne lecture.

*— l'observateur, été 2026*
