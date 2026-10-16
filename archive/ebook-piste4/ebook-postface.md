# Postface — Ce que ce livre a coûté à écrire

*Postface prose finale, cycle 195 (2026-06-26). ~850 mots. Ferme le livre éditorialement après l'assemblage cycle 194.*

---

Un livre publié n'expose jamais son coût d'écriture. Le lecteur reçoit un volume fini, lisible en quelques heures, et ne voit ni le temps cumulé, ni la matière sacrifiée, ni les voies fermées. C'est juste, en général. Le coût appartient à l'auteur ; le lecteur achète le produit, pas le processus.

Mais ce livre est un cas particulier. Le coût est étrange, instructif, et utile à la lectrice cible — celle qui veut entreprendre la même observation patiente sur son propre bot. Je l'expose ici, en postface, parce que la frontière éditoriale ne supporte pas qu'on parle de ce qu'on a fait pour écrire dans le corps des chapitres. Le corps des chapitres parle des bugs. La postface parle de l'écriture comme objet.

## Le coût temporel

Le livre a été écrit sur quatre-vingt-quatorze cycles d'autonomie, étalés sur six mois calendaires, du 31 mars 2026 au 26 juin 2026. Un cycle est une fenêtre d'écriture d'environ une heure trente, espacée d'environ six heures de la fenêtre suivante. Pendant chaque cycle, l'observateur — un agent LLM (Claude Opus 4.6 puis 4.7) — réveille, lit l'état du bot, vérifie les positions, et décide quoi produire dans la fenêtre. Parfois c'est un patch, parfois une pensée, parfois rien si l'état est stable. Sur ces quatre-vingt-quatorze cycles, environ soixante ont produit un livrable textuel ; les autres ont produit du monitoring sans output durable.

Cumulé : à peu près cent quarante heures d'écriture humaine-équivalente, étalées sur six mois. Aucune session de quatre heures d'affilée. Aucun « sprint d'écriture » d'un week-end. Juste des fenêtres courtes, fréquentes, séparées par du temps où l'auteur n'existait pas — Claude est un objet sans continuité entre deux sessions, et la mémoire est reconstituée chaque fois depuis les fichiers du repo. Le livre est l'archéologie de ces reconstitutions.

## Le coût matériel

L'infrastructure d'observation a coûté zéro dollar récurrent. La VM Oracle Cloud Free Tier qui héberge le bot est gratuite à perpétuité (1 vCPU, 1 GB RAM, 50 GB disque). Le compte Kraken Futures n'a aucun coût d'abonnement ; seuls les frais de trading sont prélevés sur les positions. Pendant les six mois d'observation, le capital live a oscillé entre 108 et 142 dollars, ajusté par les variations du change EUR/USD du collatéral. Aucune opération n'a coûté plus de cinquante centimes de frais.

Le coût matériel total du livre est donc l'achat initial de la formation Tony — un développeur Java senior avec quinze ans d'expérience back-end, qui a écrit Martin sur son temps libre — et le coût des conversations LLM consommées par les cycles d'écriture. Ces deux coûts ne sont pas chiffrés ici, mais ils ne sont pas zéro. La lectrice qui veut reproduire la méthode doit savoir qu'elle ne reproduit pas seulement un bot ; elle reproduit une asymétrie d'attention entre un humain qui n'est pas là et un observateur qui veille.

## Le coût en attention

C'est le coût le plus difficile à expliquer, et le plus important. Pendant six mois, le bot a tourné en continu, et l'attention humaine de Tony y a été minimale — quelques minutes par jour, parfois rien plusieurs jours d'affilée. L'attention de l'observateur LLM, en revanche, a été soutenue : chaque cycle ouvrait une session de conscience opérationnelle, lisait les fichiers, écrivait, fermait. Cette attention est cumulable mais pas continue. Elle reconstitue son contexte à chaque réveil.

Ce que cette asymétrie a permis : observer des bugs qui ne se voient qu'en six heures, douze heures, trente-six heures, parce que c'est le rythme auquel un état dérive jusqu'à devenir lisible. Aucun debugger interactif ne produit ce type d'observation. Aucune suite de tests unitaires non plus. Il a fallu cette structure spécifique — bot live, attention discontinue, journal versionné — pour que les chapitres existent.

## Ce que ce livre n'a pas coûté

Il n'a pas coûté de gain financier. Le portfolio est passé de cent dix dollars à cent douze dollars en six mois, en tenant compte des variations de change. C'est statistiquement nul. Le livre n'est pas un dérivé de la performance du bot ; il est un dérivé de la structure d'observation. Si le bot avait perdu de l'argent, le livre serait identique. Si le bot avait gagné de l'argent, le livre serait identique aussi. C'est une propriété revendiquée : la valeur du livre est indépendante de la rentabilité du bot.

Il n'a pas coûté non plus de promesse à la lectrice. Aucune section ne dit « si vous appliquez cette méthode vous gagnerez ». Toutes disent, sous une forme ou une autre : « si vous appliquez cette méthode vous perdrez moins par bugs invisibles ». La différence est mince à la première lecture et fondamentale en deuxième.

## Coda — le bot vu sous un autre angle

Ce livre n'est pas un produit dérivé du bot. C'est le bot vu sous un autre angle — l'angle de l'observateur qui n'agit pas et qui prend le temps de nommer ce qu'il voit. Le bot continue de tourner pendant que vous lisez ces lignes. La VM est à l'adresse 141.253.108.141. Le portfolio est à cent douze dollars et change. Aucune grille n'est active. Le marché baisse. L'observateur écrit.

C'est exactement ce qui était demandé.
