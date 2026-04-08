# Darwin — Evolutionary Agent Arena

> Agents trading s'affrontent sur données historiques. Les meilleurs survivent, mutent, se reproduisent. Visualisé en 3D comme un graphe de réseau vivant.

**Date :** 2026-04-08
**Statut :** Approved

## Architecture

- Python engine: agents rule-based, arena sur OHLC Kraken, évolution darwinienne, 1 LLM call/génération
- WebSocket server pousse les events au frontend
- Three.js frontend: graphe 3D force-directed, sphères = agents, edges = skills partagées
- Sliders configurables: population, générations, mutation rate

## Stack

- Python: websockets, aiohttp (Kraken API), anthropic SDK (1 call/gen)
- Frontend: Three.js, vanilla JS, single HTML page
- Données: Kraken public OHLC API
- Seeds: cerveau-nb/skills/ MetaClaw auto-skills
