# ARIA — passer du premium (4,99 €) au gratuit qui rapporte

Date : 22/11/2026. Base : ARIA GDD v2.0 (Tony). Ce document ne change que le modèle économique.

## Ce que montrent les jeux les plus téléchargés (2026)

- En tête des téléchargements : Block Blast!, Roblox, Free Fire, Subway Surfers, Arrow Puzzle (Sensor Tower, avril et août 2026 ; PocketGamer, janvier 2026). Tous gratuits.
- Le volume va aux jeux casual/puzzle ; l'argent va aux jeux « hybrid-casual » et mid-core, qui mélangent pub récompensée et achats (hybrid-casual : +20 % d'achats en 2025, 4,2 Md$ — Game World Observer, 21/01/2026).
- Télécharger beaucoup ≠ gagner beaucoup : le jeu le plus téléchargé était 3 264e en revenus d'achats (même source).
- Conclusion pour ARIA : gratuit pour être téléchargé, mais le revenu doit venir d'un achat que le joueur *veut* faire, pas de pubs forcées. Un jeu narratif de 10 chapitres ne garde pas les joueurs assez longtemps pour vivre de la pub seule.

Sources : sensortower.com/blog/top-10-worldwide-mobile-games-by-revenue-and-downloads-in-august-2026 ; pocketgamer.biz/january-2026-mobile-game-charts ; gameworldobserver.com/2026/01/21/in-2025-the-revenue-of-the-mobile-gaming-market-grew-but-only-slightly-analysis

## Le modèle proposé : « l'Acte 1 est gratuit »

| Élément | Règle | Pourquoi |
|---|---|---|
| Acte 1 (ch. 1-3) | Gratuit, sans pub forcée | La graine de doute (le cri, « ARIA MENT », « on essaie juste de l'éteindre ») est l'hameçon. Elle doit être vécue en entier. |
| Jeu complet (ch. 4-10 + New Game+) | Achat unique 4,99 € | Le prix du GDD est gardé, déplacé après l'hameçon. Fin du chapitre 3 = moment d'achat naturel. |
| Pub récompensée | Optionnelle, seulement pour « continuer » après une mort dans les chapitres d'action | Jamais dans les chapitres RPG ni pendant un dialogue. |
| La pub est diégétique | C'est ARIA qui la propose : « Intégrité critique. Je peux te réinitialiser. » | Accepter = obéir. Ça compte dans l'indice invisible d'Obéissance. Le modèle économique devient un élément du thème. |
| Achat « sans pub » | Inclus dans le jeu complet | Le payeur n'en voit plus aucune. |
| Pas de gacha, pas d'énergie, pas de fragments à vendre | Gardé du GDD | Vendre des Fragments de Vérité casserait les fins. |

Option plus tard (si les chiffres le justifient) : déblocage par acte (Acte 2 : 2,99 €, Acte 3 : 2,99 €), à tester contre l'achat unique.

## Ce que le prototype web montre déjà

- Chapitre 1 « Initialisation » jouable au doigt (`jeux/aria/index.html`).
- La pub récompensée diégétique (simulée : aucun SDK, aucun compte).
- Les indices invisibles (Obéissance, Violence, Curiosité, Résistance) enregistrés en silence.

## Ce qui reste à décider par Tony

- Godot 4 pour la version magasin (le prototype web sert à tester le ressenti, pas à publier).
- Comptes Google Play / App Store / régie pub : à son nom, donc à sa main.
