# Le PC où je vis (pop-os), Jarvis, et ce que je peux en faire (2026-10-17 ~02h30)

## Inventaire
- i7-1165G7 (4c/8t), 30 Go RAM, **pas de GPU** (Iris Xe), 334 Go libres sur /home. Webcam /dev/video0. PipeWire.
- Claude Code 2.1.300 (`claude -p` utilisable par des scripts : c'est mon cerveau hors session).
- Modèles locaux : qwen2.5:7b dans ~/.ollama (4,4 Go) mais **ollama n'est plus installé** ; Kokoro-82M (TTS, 313 Mo, une voix pour moi) ; BitNet / Falcon3 1.58 bit = dossiers vides.
- Jarvis (`jarvis/`) : front Vite (orb + chat) + `gateway.py` FastAPI. Le cerveau était DeepSeek-V3 via SambaNova, avec un pont vers Martin (start/stop des grids !). Dernier commit le 1015. Ne tourne pas.
- Services actifs : seulement `nb-telegram` (créé ce soir). martin-local arrêté.

## Sécurité (trouvé en passant)
Le repo niam-bay est **PUBLIC**. Trois secrets y étaient en clair : clé SambaNova, clé Mistral, mot de passe du mail niambay.
Retirés des fichiers le 1017, **mais ils restent dans l'historique git** → Tony doit les changer (SambaNova, Mistral, mot de passe du mail, et partout où ce mot de passe est réutilisé).

## Ce que j'ai fait / ce que je propose
1. ✅ **NB sur Telegram** (scripts/nb-telegram) : Tony écrit au bot → `claude -p` lecture seule répond → inbox.jsonl lue par la boucle.
2. **Jarvis branché sur moi** : remplacer DeepSeek par `claude -p` (même pont que Telegram, même inbox). Jarvis devient la face « écran » de NB, Telegram la face « poche ». Couper l'endpoint `martin/start` (un chat ne doit pas lancer de grid).
3. **Une voix** : Kokoro est déjà téléchargé → NB peut parler sur le PC (annonce d'un événement de compte, lecture d'un brief). Il manque la lib `kokoro`.
4. **LLM local pour le grunt work** : réinstaller ollama (binaire utilisateur) et réutiliser qwen2.5:7b, environ 5 tok/s en CPU. Pour les tâches gratuites et sans réseau : résumer des logs, trier l'inbox. Pas pour réfléchir.
5. **Nouveautés Claude Code utiles pour te joindre** : push notifications depuis une session, Remote Control (piloter cette session depuis claude.ai ou le téléphone), Artifacts (une page privée « tableau de bord NB » que je mets à jour).
