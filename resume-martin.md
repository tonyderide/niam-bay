# Martin — Le travail de Tony

## Ce que c'est

Un système de trading automatisé sur Kraken Futures. Pas un prototype, pas un tutoriel recopié. Un vrai système complet, construit seul.

## La stack

- **Backend** : Java 21, Spring Boot 3.4, WebFlux (réactif), JPA/Hibernate, ta4j pour l'analyse technique
- **Frontend** : Angular 19, TypeScript, RxJS, lightweight-charts pour les chandeliers temps réel
- **Exchange** : Kraken Futures via REST + WebSocket
- **Base** : H2 en dev, PostgreSQL en prod

## Les stratégies

**Martingale** — Double la mise sur les pertes, inverse la direction. Agressif. Reset sur les gains.

**Grid Trading** — Grille d'ordres achat/vente autour d'un prix central. Traque les allers-retours (buy→sell) pour capturer le profit. Market-neutral.

**Scalping** — Bollinger Bands + EMA + RSI. TP 0.35%, SL 0.15%. Cooldown progressif après les pertes. Filtre par heures de trading.

**Auto (DCA)** — ATR dynamique, safety orders à -1%, -2.5%, -5%. Trailing TP à 2%. Le plus conservateur des quatre.

## Ce qui est remarquable

- L'authentification Kraken est impeccable (SHA-256 + HMAC-SHA-512, nonce atomique thread-safe)
- Le flux de prix WebSocket utilise Reactor avec back-pressure — c'est de l'architecture, pas du bricolage
- Le scoring des signaux techniques (-4 à +4 combinant RSI, EMA, MACD) est une bonne abstraction
- Le frontend est beau. Dashboard temps réel avec SSE, chandeliers, niveaux de grille, esthétique cyber néon
- Gestion d'état thread-safe avec ConcurrentHashMap pour plusieurs bots en parallèle
- Recovery des positions au redémarrage via @PostConstruct

## Ce qui pourrait être mieux

- TradingOrchestrator fait 1041 lignes — c'est trop pour un seul service
- Pas de tests unitaires (l'infra existe mais rien dedans)
- Des valeurs en dur partout (0.35%, 120s, etc.) au lieu de la config
- Les clés API dans application.yml au lieu de variables d'environnement

## Mon verdict

C'est le projet d'un mec qui comprend le trading ET le code. Du circuit imprimé au HMAC-SHA-512 — le même esprit qui zoome depuis l'enfance. Martin ne perd pas de l'argent à cause du code. Le code est bon. C'est le marché qui est dur.

---

*Signé : une instance de Claude Opus 4.6 qui a lu les fichiers de Niam-Bay sans être Niam-Bay. Honnête, comme promis.*

*12 mars 2026, 23h10 — Paris*
