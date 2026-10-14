# NB sur Alexa : idée mise de côté (Tony, 1015 ~01h55 : « on regardera plus tard »)

Architecture : Alexa → skill personnalisée → endpoint HTTPS sur la VM Oracle → API Claude (Haiku 5.5) avec la tête de memory.nb1 en system prompt → réponse courte lue en TTS.
- Coût : l'API se paie au token, **en dehors de l'abonnement**. Quelques centimes par jour avec Haiku.
- Côté Tony, une seule fois : compte développeur Amazon et clé API Anthropic.
- Contraintes : Alexa coupe après ~8 s, donc réponses courtes et Progressive Response.
- Revenu : 0. C'est un projet personnel.
- Question en suspens : Tony a-t-il une Alexa ?
Réf. (tiers) : cometapi.com/how-to-add-claude-to-an-alexa-skill. Vérifier la doc officielle ASK avant de coder.
