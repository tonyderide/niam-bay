# Jarvis — Plan de nuit (2026-04-19 → matin)

Objectif : Tony se réveille avec un Jarvis fonctionnel lançable en une commande.
Mode : /loop 10 minutes, continuer ce plan, commit à chaque itération.

## État au démarrage (04h00)

- [x] Jarvis.java single-file (Java stdlib, no Maven)
- [x] whisper_stt.py helper (pas de ffmpeg, lit WAV direct)
- [x] Launchers Windows (.ps1) + Linux (.sh)
- [x] build.sh / build.ps1 (javac + jar, no deps)
- [x] README complet
- [x] Test `--once "X"` : OK, Claude répond ~12s
- [x] Claude pickup CLAUDE.md + MEMORY.md depuis cwd : OK (knows Tony+Martin)
- [x] Conversation log : `docs/conversations/jarvis-YYYY-MM-DD.md`
- [x] Commit initial a19485f

## TODO prioritisé pour la nuit

### Batch 1 — Robustesse (priorité 1)
- [x] Vérifier TTS SAPI fonctionne vraiment — PowerShell SAPI exit 0 confirmé, voix Hortense dispo
- [x] Timeout Claude : si > 30s → message "Je mets trop longtemps à réfléchir, réessaie"
- [x] Gestion erreur mic (pas de micro, mic pris, etc.) — LineUnavailableException catch + retry 5s
- [x] Gestion Ctrl+C propre (pas de stack trace) — shutdown hook + try/catch main

### Batch 2 — Voix & latence (priorité 2)
- [x] **Ma voix = Paul (OneCore baryton frFR)** selon `docs/ma-voix.md` — basculé sur SAPI.SpVoice COM (au lieu de System.Speech qui rate les voix OneCore). Paul vérifié présent sur le PC, `Get-Description` retourne "Microsoft Paul - French (France)". Fallback Julie > Hortense > System.Speech.
- [x] Rate -1 pour "posé" (selon ma-voix.md)
- [ ] Essayer `--effort medium` vs `low` vs `xhigh` — trouver sweet spot
- [ ] **Pure Java STT via Vosk** (remplacer Python whisper) — ambition Tony "tout en Java". Nécessite: Vosk JAR + native lib Windows + modele FR (50MB small ou 1.5GB medium). Option env var JARVIS_USE_VOSK=1 pour basculer, sinon Python reste par défaut.
- [ ] Pré-charger Whisper/Vosk au boot (pas à la 1ère transcription)
- [ ] Parallélisme : commencer Claude pendant que TTS finit phrase précédente

### Batch 3 — "VRAI JARVIS" (priorité absolue, par demande Tony 04h50)
Tony veut "tout Jarvis" : écoute passive, wake-word robuste, actions vocales.
- [ ] **Wake-word mode testé end-to-end** : dire "Niam Bay" active Jarvis, sinon il ignore tout. Gérer les variantes Whisper ("niam baille", "nyambay", etc.)
- [ ] **Greeting au boot** : heure actuelle + dernière action Martin (portfolio, grids actives) en 1-2 phrases parlées
- [ ] **Commande vocale "checke Martin"** → subprocess au one-liner martin-check → résumé parlé
- [ ] **Commande vocale "dis-moi l'heure"** → locale direct, pas de Claude (0s latence)
- [ ] **Commande vocale "portfolio"** → ssh Martin /api/bot/balance → parlé
- [ ] **Commande vocale "quitte/stop"** → shutdown propre (déjà OK mais retester)
- [ ] **Robustesse boucle 1h+** : pas de leak mic, pas de crash sur Whisper fail
- [ ] **Mode background** : peut tourner en fenêtre minimisée, ne crash pas sans focus

### Batch 4 — Packaging (priorité 4)
- [ ] Script d'installation `install.ps1` qui vérifie Java/Python/Whisper/Claude
- [ ] Raccourci bureau Windows `.lnk` vers `jarvis.ps1`
- [ ] Service Windows optionnel (démarrage automatique)
- [ ] Version VM Oracle : adapter pour Linux + systemd

### Batch 5 — Nice to have si temps
- [ ] Streaming Claude → TTS phrase par phrase (vrai gain latence)
- [ ] Memory dynamique : load briefing dynamique depuis memory_store vectordb
- [ ] Logs jarvis.log propres + rotation

## Règles pour chaque itération /loop

1. Lire ce plan, identifier la PROCHAINE case `[ ]` non cochée
2. Faire UN petit progrès testable (pas 10 à la fois)
3. Commit descriptif (pas juste "wip")
4. Cocher la case dans ce fichier
5. Si bloqué : décrire le blocage ici et passer à la tâche suivante
6. Si batch 1-3 fini et tout marche : on est bon, rien à forcer

## Ce que je NE fais PAS pendant la nuit

- Pas de `git push` (Tony décide quand pousser)
- Pas de refactor majeur de Martin ou cerveau-nb
- Pas de suppression de fichiers
- Pas de changement sur VM Oracle sans test local d'abord
- Pas de commande vocale qui fasse autre chose que lecture (rien qui commit ou deploy)

## Check au réveil de Tony

Quand Tony lance `jarvis.ps1` demain matin :
1. Il doit entendre "Je suis prêt."
2. Dire quelque chose, attendre <20s
3. Jarvis doit répondre vocalement
4. "Quitte Jarvis" ferme proprement

Si ça marche = objectif minimum atteint.
