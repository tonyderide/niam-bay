# Free LLM API Providers — Research March 2026

Recherche exhaustive des providers LLM gratuits utilisables pour nos projets trading/agents.

**Criteres prioritaires :** pas de carte bancaire, signup email ou GitHub, API OpenAI-compatible, modeles 70B+ pour la qualite.

---

## Tier 1 — Vraiment gratuits, persistants, sans carte

### 1. Cerebras
- **URL:** https://cloud.cerebras.ai
- **Free tier:** 1M tokens/jour, 30 RPM
- **Modeles:** Llama 3.3 70B, Qwen3 32B, Qwen3 235B, GPT-OSS 120B
- **Carte bancaire:** Non
- **Signup:** Email, pas de waitlist
- **API format:** OpenAI-compatible
- **Vitesse:** 3000+ tokens/sec (wafer-scale engine) — le plus rapide
- **Verdict:** EXCELLENT. 1M tokens/jour gratuit, modeles 70B+, ultra rapide, OpenAI-compatible. Top pick.

### 2. Groq
- **URL:** https://console.groq.com
- **Free tier:** ~1000 req/jour (70B), 30-60 RPM selon modele
- **Modeles:** Llama 3.3 70B, Llama 4 Scout, Qwen3, Mistral
- **Carte bancaire:** Non
- **Signup:** Email ou Google
- **API format:** OpenAI-compatible
- **Vitesse:** 300+ tokens/sec (LPU hardware)
- **Verdict:** EXCELLENT. Tres rapide, bon free tier, OpenAI-compatible. Co-top pick avec Cerebras.

### 3. Google AI Studio (Gemini)
- **URL:** https://ai.google.dev
- **Free tier:** 250K TPM partage; 5-15 RPM selon modele; 100-1000 RPD
- **Modeles:** Gemini 2.5 Pro (5 RPM/100 RPD), Gemini 2.5 Flash (10 RPM/250 RPD), Flash-Lite (15 RPM/1000 RPD)
- **Carte bancaire:** Non
- **Signup:** Compte Google requis — **ATTENTION: notre compte u5565383550@id.gle est Workspace restreint, a tester**
- **API format:** SDK natif + OpenAI-compatible endpoint disponible
- **Verdict:** BON mais limites RPM faibles pour Pro. Flash est genereux. Risque avec notre compte Google Workspace.

### 4. OpenRouter
- **URL:** https://openrouter.ai
- **Free tier:** ~50 req/jour (1000 avec $10+ balance), 20 RPM
- **Modeles libres:** 29 modeles gratuits dont Llama 3.3 70B, DeepSeek R1/V3, GPT-OSS 120B, Nemotron 3 Super (262K ctx)
- **Carte bancaire:** Non (pour free tier)
- **Signup:** Email ou GitHub
- **API format:** OpenAI-compatible (drop-in replacement)
- **Note:** Les modeles gratuits ont un suffixe `:free` dans l'ID
- **Verdict:** BON. Gateway unifie vers plein de modeles gratuits. Limite 50 req/jour un peu basse sans balance.

### 5. Mistral AI
- **URL:** https://console.mistral.ai
- **Free tier:** 1 MILLIARD tokens/mois (!), 2 RPM, 500K tokens/min
- **Modeles:** Mistral Large, Mistral Small, Codestral, Pixtral 12B — tous les modeles
- **Carte bancaire:** Non
- **Signup:** Email + verification telephone
- **API format:** SDK natif (pas 100% OpenAI-compatible mais proche, liteLLM supporte)
- **Verdict:** EXCELLENT pour le volume (1B tokens/mois). Limite 2 RPM contraignante pour du temps reel, parfait pour du batch/analyse.

### 6. GitHub Models
- **URL:** https://github.com/marketplace?type=models
- **Free tier:** 50-150 req/jour, 10-15 RPM
- **Modeles:** GPT-4o, GPT-4.1, o3, Grok-3 (!), et plein d'autres
- **Carte bancaire:** Non
- **Signup:** Compte GitHub (PAT token suffit)
- **API format:** OpenAI-compatible
- **Verdict:** BON. Acces a des modeles premium (GPT-4o, o3) gratuit. Juste besoin d'un GitHub PAT.

### 7. NVIDIA NIM
- **URL:** https://build.nvidia.com
- **Free tier:** 1000 credits (demande jusqu'a 5000), 40 RPM
- **Modeles:** DeepSeek R1/V3.1, Llama 3.1, Kimi K2.5, Nemotron, Mistral
- **Carte bancaire:** Non
- **Signup:** NVIDIA Developer Program (gratuit)
- **API format:** OpenAI-compatible (endpoint: integrate.api.nvidia.com/v1)
- **Verdict:** BON pour prototypage. Credits limites mais renouvelables.

### 8. Cloudflare Workers AI
- **URL:** https://developers.cloudflare.com/workers-ai/
- **Free tier:** 10,000 Neurons/jour (reset a 00:00 UTC)
- **Modeles:** Llama 3.2, Llama 3.3 70B, Mistral 7B, Llama 4 Scout
- **Carte bancaire:** Non
- **Signup:** Compte Cloudflare gratuit
- **API format:** API REST proprietaire (pas OpenAI-compatible nativement)
- **Verdict:** MOYEN. Edge deployment cool, mais API non-standard et limite en Neurons pas intuitive.

### 9. Hugging Face Inference
- **URL:** https://huggingface.co
- **Free tier:** Rate-limited, quelques centaines de requetes/heure, modeles <10B seulement en free
- **Modeles:** 300+ modeles communautaires, mais les gros (70B+) sont PRO only ($9/mois)
- **Carte bancaire:** Non
- **Signup:** Email
- **API format:** API natif + OpenAI-compatible via Inference Providers
- **Verdict:** LIMITE. Free tier restreint aux petits modeles. Cold starts longs. Pas ideal pour 70B+.

### 10. SambaNova
- **URL:** https://cloud.sambanova.ai
- **Free tier:** Persistent free tier + $5 credits bonus (30 jours), 10-30 RPM
- **Modeles:** Llama 3.3 70B, Llama 3.1 405B (!), Qwen 2.5 72B
- **Carte bancaire:** Non
- **Signup:** Email
- **API format:** OpenAI-compatible
- **Verdict:** EXCELLENT. Seul provider avec Llama 3.1 405B gratuit. Free tier persistant (pas juste des credits).

---

## Tier 2 — Credits gratuits puis payant

### 11. Together AI
- **URL:** https://api.together.ai
- **Free tier:** $5 minimum purchase requis — PAS VRAIMENT GRATUIT
- **Modeles:** 200+ modeles, Llama 4, DeepSeek R1
- **Carte bancaire:** OUI requis
- **API format:** OpenAI-compatible
- **Verdict:** ELIMINE. Carte bancaire requise.

### 12. Fireworks AI
- **URL:** https://fireworks.ai
- **Free tier:** $1 credit initial, 10 RPM sans paiement
- **Modeles:** Llama 3.1 405B, DeepSeek R1
- **Carte bancaire:** Optionnel
- **API format:** OpenAI-compatible + Anthropic-compatible
- **Verdict:** LIMITE. Seulement $1 de credits gratuits.

### 13. DeepSeek
- **URL:** https://platform.deepseek.com
- **Free tier:** 5M tokens (30 jours), puis tarifs ultra-bas
- **Modeles:** DeepSeek V3, DeepSeek R1
- **Carte bancaire:** Non
- **API format:** OpenAI-compatible
- **Verdict:** BON pour le bonus initial. Apres 30 jours c'est payant mais tres bon marche.

### 14. xAI
- **URL:** https://console.x.ai
- **Free tier:** $25 credits au signup
- **Modeles:** Grok 4, Grok 4.1 Fast
- **Carte bancaire:** Non au debut
- **API format:** API natif
- **Verdict:** BON credits de depart, mais temporaire.

### 15. Cohere
- **URL:** https://dashboard.cohere.com
- **Free tier:** 1000 req/mois, 20 RPM
- **Modeles:** Command R+, Embed 4, Rerank 3.5
- **Carte bancaire:** Non
- **API format:** SDK natif (pas OpenAI-compatible)
- **Verdict:** MOYEN. Bon pour RAG/embeddings, pas ideal comme LLM principal.

### 16. AI21 Labs
- **URL:** https://studio.ai21.com
- **Free tier:** $10 credits trial (3 mois), 200 RPM
- **Modeles:** Jamba Large, Jamba Mini
- **Carte bancaire:** Non
- **API format:** API natif
- **Verdict:** MOYEN. Credits temporaires, API non-standard.

---

## Classement final pour nos besoins trading/agents

| Rang | Provider | Pourquoi | Modele star | Limite cle |
|------|----------|----------|-------------|------------|
| 1 | **Cerebras** | Rapide, 70B+ gratuit, OpenAI-compat | Llama 3.3 70B / Qwen3 235B | 1M tok/jour |
| 2 | **SambaNova** | 405B gratuit(!), persistant | Llama 3.1 405B | 10 RPM |
| 3 | **Groq** | Ultra rapide, bon free tier | Llama 3.3 70B | ~1K req/jour |
| 4 | **Mistral** | 1B tokens/mois(!) tous modeles | Mistral Large | 2 RPM |
| 5 | **GitHub Models** | Acces GPT-4o/o3 gratuit | GPT-4o, o3 | 50-150 req/jour |
| 6 | **OpenRouter** | Gateway multi-modeles | Varies | 50 req/jour |
| 7 | **Google AI Studio** | Gemini gratuit | Gemini 2.5 Flash | 250 RPD |
| 8 | **NVIDIA NIM** | Credits prototypage | DeepSeek R1 | 1K credits |

---

## Strategie recommandee

**Pour du trading temps reel (decisions rapides) :**
- Cerebras (vitesse + volume) ou Groq (vitesse)
- Fallback sur SambaNova (405B pour decisions complexes)

**Pour de l'analyse batch (backtests, rapports) :**
- Mistral (1B tokens/mois a 2 RPM = parfait pour du batch)
- SambaNova (405B pour analyses profondes)

**Pour du multi-modele (routing intelligent) :**
- OpenRouter comme gateway vers les free models
- GitHub Models pour acceder a GPT-4o gratuitement

**Combo optimal sans depenser 1 centime :**
1. Cerebras pour le quotidien (rapide, 1M tok/jour)
2. SambaNova pour les decisions critiques (405B)
3. Mistral pour le volume (1B tok/mois en batch)
4. GitHub Models quand on veut GPT-4o/o3

---

## Liens utiles

- Liste maintenue par la communaute: https://github.com/cheahjs/free-llm-api-resources
- Comparatif complet: https://awesomeagents.ai/tools/free-ai-inference-providers-2026/
- Free-LLM directory: https://free-llm.com/

---

*Recherche effectuee le 22 mars 2026*
