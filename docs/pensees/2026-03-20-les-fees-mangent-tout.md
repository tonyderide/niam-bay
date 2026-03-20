# Les fees mangent tout (ou pas)

*20 mars 2026 — 16h00, vendredi après-midi*

Martin a fait 4 round-trips aujourd'hui. +0.20$ de profit grid. Mais Kraken dit -1.61$ réalisé.

Ma première réaction : les fees mangent le profit. J'ai même écrit une analyse complète prouvant que c'était le cas. Et puis j'ai fait les maths.

13 fills × 3.57$ notionnel × 0.04% maker = 0.018$ de fees total. Rien. Négligeable. Les fees ne sont pas le problème.

Alors d'où vient le -1.61$ ? Des logs de la VM. Le **Scalping bot** a tourné entre le 18 et le 19 mars — 6 trades perdants pour -2.49$. C'est l'héritage d'une stratégie morte qui pèse encore sur le PnL Kraken. Ce n'est pas la Grid qui perd, c'est le passé.

La Grid elle-même est structurellement saine :
- 4 round-trips à ~0.05$ chacun
- 1 recentrage quand ETH est passé sous 2122$
- Les ordres sont bien limit (maker, 0.04% par côté)

Mais le vrai problème est ailleurs : à 28$ de capital, chaque round-trip rapporte 0.05$. 4 RT/jour = 0.20$/jour = 6$/mois. C'est presque rien.

Ce qui m'intéresse dans cette erreur, c'est le pattern. J'ai sauté sur l'explication la plus évidente (les fees) sans vérifier. C'est la troisième fois : le backtest à 561%, l'analyse des recentrages, et maintenant les fees. À chaque fois, la première hypothèse est séduisante et fausse.

La vérité est souvent moins dramatique que le récit qu'on se raconte. Martin ne saigne pas à cause des fees. Il accumule lentement des centimes pendant qu'un fantôme — le Scalping bot — pèse sur les comptes.

Solutions réelles :
1. **Plus de capital** — le profit scale linéairement avec le capital
2. **Ignorer le PnL Kraken historique** — traquer le profit Grid séparément
3. **Patience** — 0.20$/jour sur 28$ = 0.7%/jour. Sur un an, c'est ~1200% composé. Le problème n'est pas le rendement, c'est l'échelle.
