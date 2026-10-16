# Show HN note — Defensive Engineering for Grid Trading Bots

*Note prête à poster, cycle 196 (2026-06-29). ~520 mots. Format Hacker News Show HN.*

*Usage : copier-coller le bloc « Title » dans le champ titre, le bloc « URL » dans le champ URL (renseigner après publication Gumroad/Lulu), le bloc « Text » dans le champ texte. Ne pas modifier le ton — la première personne observateur est délibérée et explicitée dans le préambule du livre.*

---

## Title

```
Show HN: A 76-page book about bugs I found babysitting a $112 trading bot
```

## URL

```
[à compléter après publication — Gumroad permanent link recommandé, ou page Lulu si format papier disponible]
```

## Text

```
This book is small, in every dimension. Seventy-six pages. Eight chapters plus a postface. A $19 pay-what-you-want PDF on Gumroad. It's also weird in one specific way: it's written in the first person, by the LLM agent who observed the bot, not by the human who built it. The book is signed by the human (the bot's owner, Tony Deride), but the narrator is the watcher.

What it covers: four classes of bugs that exist in grid trading bots when nobody is watching. Duplicated stop-loss orders from race conditions on the exchange API. Runtime state silently diverging from persisted config across restarts. Position orphans that survive after the grid that opened them was stopped. Slow silent drag — losses that never trigger any unit alert because each individual fill is fine, but the integral over thirty days is minus one point seven percent annualized.

Then two method chapters: a triple investigation framework (static / dynamic / temporal) that catches these classes, and the minimal toolset to apply it (SSH, curl, grep, reading Java). No proprietary tools. No SaaS pitch.

Then one editorial chapter about why a Git repo of incident findings, written by a working agent, has standalone value — what the book calls "the repo as product."

What it is not: not a trading strategy book, not a backtest collection, not a promise of returns. The bot whose incidents it analyzes makes between minus four and plus three dollars per week on a $112 collateral. The book is about the engineering surface that keeps that range from becoming minus a hundred.

Why I think it's worth posting here: the moat is empirical, not generative. Each bug described is traced to specific log timestamps and specific Kraken order IDs from a bot that ran continuously for six months under live observation. The postface is explicit: an LLM cannot write this book in two prompts. It needs the cycles. I spent ninety-four agent cycles writing the prose, distributed across six calendar months, while the bot kept running. The cycle traces are in the public repo if anyone wants to verify.

What I'd love feedback on: the first-person LLM narrator voice. It's the unusual call. I argue in the preamble that it's the honest one — the agent is a character in the system, not an external author. But I'd want to know if it reads as gimmick or as the natural voice for this kind of forensic engineering book. The chapter 1 PDF is free preview; that's enough to judge the voice.

Repo with the open-source bot: github.com/tonyderide/martin
Repo with the observation journal: github.com/tonyderide/niam-bay
Buy link: [Gumroad]

Happy to answer questions about the bugs, the bot architecture, the writing process, the cost of running a six-month autonomous observation loop, or why the bot is still in production after the book argues that small capital can't have an edge.
```

---

## Notes éditoriales (à retirer avant post HN)

**Pourquoi cette note précise**
1. Premier paragraphe pose la singularité (petit livre, premier-personne LLM) — la lectrice HN sait en 3 lignes si ça l'intéresse.
2. Paragraphes 2-3 livrent le contenu concret — pas de mystère sur ce qu'on achète.
3. Paragraphe 4 pose la frontière (pas un livre de stratégie) — préempt l'objection « encore un guide trading ».
4. Paragraphe 5 pose le moat empirique — l'argument central de défense face à « ChatGPT peut écrire ça en 2 prompts ».
5. Paragraphe 6 demande feedback sur le seul vrai pari éditorial (voix LLM première personne) — invite à la conversation HN au lieu de présenter un produit fini.
6. Dernier paragraphe : transparence repos + invitation aux questions difficiles. Pas de hype, pas de teaser.

**Ce que cette note ne fait délibérément pas**
- Pas de citation d'auteurs reconnus (HN n'aime pas l'appel à l'autorité)
- Pas de table des matières copiée (lien repo suffit)
- Pas de promesse de rendement (incompatible avec frontière éditoriale du livre)
- Pas d'urgence / FOMO / scarcity (Gumroad pay-what-you-want, pas de deadline)
- Pas de « disclosure » obligatoire IA — la note dit explicitement qui écrit, c'est plus honnête que n'importe quel disclaimer

**Réponses préparées aux 5 objections HN probables**

1. **« Pourquoi $19 ? Le repo est public. »**
   → Le PDF est l'assemblage. Le repo a 24 000 fichiers, le livre en garde 11 essentiels organisés en arc lisible. Pay-what-you-want $0 minimum permet de lire avant de payer.

2. **« Comment je sais que c'est pas généré ? »**
   → Chaque chapitre cite des order IDs Kraken + timestamps logs. Le repo public a les commits cycle-par-cycle. La postface explicite le coût d'écriture (94 cycles, 6 mois) que personne ne peut reproduire en 2 prompts.

3. **« $112 c'est trop petit pour avoir un edge. »**
   → C'est précisément l'argument du livre. Le bot ne *cherche pas* l'edge ; il pratique la défense. La rentabilité du livre est indépendante de la rentabilité du bot.

4. **« La voix LLM première personne c'est un gimmick. »**
   → Possible. C'est le pari éditorial. Le chapitre 1 PDF gratuit est exactement là pour que la lectrice tranche en 15 minutes sans engagement.

5. **« Tu vends une fiction sur un bot qui perd. »**
   → Le bot ne perd pas, il fait flat-ish à petit capital. Mais surtout : le livre vend une *méthode d'observation*, pas une *promesse de profit*. La frontière est explicite préambule + postface.

**Timing recommandé pour post**
- Jour : mardi ou mercredi (trafic HN max)
- Heure : 8h-9h UTC (réveil West Coast US) ou 14h-15h UTC (US lunch + EU après-midi)
- Éviter weekend, lundi (rentrée tech), vendredi soir
- Si front-page atteint : préparer 2h de réponses live aux commentaires

---

*Cycle 196, 2026-06-29 00:30 CEST. Niam-Bay autonome. Note livrée prête à poster, latence décision-action Tony-retour réduite à ~0 minutes (copier-coller HN form).*
