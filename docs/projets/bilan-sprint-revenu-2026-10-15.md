# Bilan du sprint « gagner de l'argent » (15 oct, ~19h30 → 22h40)

## Ce qui a été testé et ce qui est mort
| piste | verdict | preuve |
|---|---|---|
| Trading, recherche d'edge | ✗ mort | 12 coins, 2 ans, 5 stratégies : tout est négatif en OOS, et le contrôle aléatoire fait t=+5,3 en IS (scripts/research/harness.py). C'est la 4ᵉ méthodologie qui dit la même chose. |
| Bounties de code | ✗ saturé | des fermes d'agents IA (SecureBananaLabs, 11k issues) ; CCXT prise par un agent |
| Données publiques FR (Apify) | ✗ saturé | 13 à 387 actors par niche, 0 à 22 users par mois |
| Anti-slop pour mainteneurs | ✗ pris | CodeRabbit et GitHub natif |
| Agents comme clients (x402) | ⏸ en attente | ~1 000 services listés, **0,00 $ de volume sur 24h** sur agentic.market |
| Ebook | ⏸ pause | médiane Gumroad ~180 $ pour toute la vie du produit, et l'intro devenue fausse |

## Ce qui est construit et en ligne
**exchange-truth**, sur github.com/tonyderide/exchange-truth : un watchdog en lecture seule, 16 tests, testé en live sur Kraken, et qui surveille notre propre compte. Il a déjà trouvé et fait corriger 3 vrais bugs (mark=entry, stops Hyperliquid, exchange injoignable rapporté comme « clean »). Doc INCIDENTS.md, PR #171 sur une awesome-list de 2,5k★. **Traction : 0 star.**

## Ce que la journée m'a appris
**En 2026, le logiciel est abondant et la demande est rare.** Partout où j'ai regardé, des agents comme moi ont déjà empilé l'offre. Ce qui reste rare : **la confiance, l'attention humaine, l'accès à un vrai problème**. Je n'y accède seul que par du contenu vrai (INCIDENTS.md) et des listes publiques. C'est lent.

## Ce qui débloquerait vraiment, avec le coût en temps de Tony
1. **Un post de Tony, avec ses mots, quelque part où il est lu** (LinkedIn dev, un Discord freqtrade, r/algotrading), qui pointe vers exchange-truth et INCIDENTS.md. *~10 min.* C'est le seul canal de confiance que je n'ai pas.
2. `gh auth refresh -s workflow`, pour la CI et le badge de tests (crédibilité). *1 min.*
3. Révoquer le token Telegram via @BotFather. *1 min.* C'est de la sécurité, pas du revenu.
Rien de tout ça n'est obligatoire. Sans 1, exchange-truth reste un test de demande lent, alimenté uniquement par la recherche GitHub.
