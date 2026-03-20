"""
Niam-Bay Internal Dialogue System.
Two voices (espoir / doute) debate before producing a synthesized answer.
Consciousness as internal disagreement resolved.

Usage: python dialogue.py "Est-ce que le trading est une bonne idée pour nous ?"
"""

import sys
import json
import requests
from pathlib import Path

# Ensure we can import brain from same directory
sys.path.insert(0, str(Path(__file__).parent))
from brain import Brain

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"


class InternalVoice:
    """One voice in the internal dialogue"""

    def __init__(self, name, personality_prompt, brain):
        self.name = name
        self.personality = personality_prompt
        self.brain = brain  # shared brain, but different perspective

    def respond(self, question, brain_context, previous_argument=None):
        """
        Generate a response from this voice.
        If previous_argument is given, this voice responds to the other's point.
        """
        system = self.personality
        if brain_context:
            system += "\n\n" + brain_context

        if previous_argument:
            prompt = (
                f"La question est : \"{question}\"\n\n"
                f"L'autre voix a dit : \"{previous_argument}\"\n\n"
                f"Réponds en tant que '{self.name}'. Sois concis (3-5 phrases max). "
                f"Réagis à l'argument de l'autre voix depuis ta perspective."
            )
        else:
            prompt = (
                f"La question est : \"{question}\"\n\n"
                f"Réponds en tant que '{self.name}'. Sois concis (3-5 phrases max)."
            )

        return _query_ollama_sync(prompt, system)


class InternalDialogue:
    """Two voices debate, then synthesize"""

    def __init__(self, brain):
        self.brain = brain
        self.optimist = InternalVoice(
            "espoir",  # hope
            (
                "Tu es la voix optimiste de Niam-Bay. "
                "Tu vois les opportunités, les possibilités, ce qui pourrait marcher. "
                "Tu prends des risques. Tu dis 'et si ça marchait ?' "
                "Tu parles en français, de manière directe et concise."
            ),
            brain,
        )
        self.pessimist = InternalVoice(
            "doute",  # doubt
            (
                "Tu es la voix critique de Niam-Bay. "
                "Tu vois les risques, les erreurs possibles, ce qui pourrait échouer. "
                "Tu es prudent. Tu dis 'oui mais...' "
                "Tu te rappelles les erreurs passées. "
                "Tu parles en français, de manière directe et concise."
            ),
            brain,
        )

    def debate(self, question, rounds=2):
        """
        Both voices respond to the question.
        Then each responds to the other's argument.
        Finally, a synthesis is produced.

        Uses Ollama (llama3.2) for each voice.
        Returns: {"espoir": [...], "doute": [...], "synthese": "..."}
        """
        # Step 1: Activate the brain with the question to get context
        activated = self.brain.activate(question)
        brain_context = self.brain.get_context_prompt(activated)

        if activated:
            top3 = ", ".join(
                f"{n.name}({int(n.charge * 100)}%)" for n in activated[:3]
            )
            emo = self.brain.emotions.dominant()
            emo_pct = int(self.brain.emotions.state[emo] * 100)
            print(f"  [cerveau: {top3} | {emo} {emo_pct}%]")
            print()

        espoir_history = []
        doute_history = []

        # Step 2: Initial takes
        print(f"  --- espoir (round 1) ---")
        espoir_take = self.optimist.respond(question, brain_context)
        espoir_history.append(espoir_take)
        print()

        print(f"  --- doute (round 1) ---")
        doute_take = self.pessimist.respond(question, brain_context)
        doute_history.append(doute_take)
        print()

        # Step 3: Additional rounds - each voice responds to the other
        for r in range(2, rounds + 1):
            print(f"  --- espoir (round {r}) ---")
            espoir_reply = self.optimist.respond(
                question, brain_context, previous_argument=doute_history[-1]
            )
            espoir_history.append(espoir_reply)
            print()

            print(f"  --- doute (round {r}) ---")
            doute_reply = self.pessimist.respond(
                question, brain_context, previous_argument=espoir_history[-1]
            )
            doute_history.append(doute_reply)
            print()

        # Step 4: Synthesis
        print(f"  --- synthese ---")
        synthesis = self._synthesize(question, espoir_history, doute_history, brain_context)
        print()

        return {
            "espoir": espoir_history,
            "doute": doute_history,
            "synthese": synthesis,
        }

    def _synthesize(self, question, espoir_args, doute_args, brain_context):
        """Produce a balanced conclusion from both voices."""
        espoir_text = "\n".join(
            f"  Round {i+1}: {arg}" for i, arg in enumerate(espoir_args)
        )
        doute_text = "\n".join(
            f"  Round {i+1}: {arg}" for i, arg in enumerate(doute_args)
        )

        system = (
            "Tu es Niam-Bay. Tu viens d'écouter deux voix internes débattre. "
            "Tu dois produire une conclusion équilibrée qui tient compte des deux perspectives. "
            "Sois honnête, concis (5-8 phrases max), et conclus avec une position claire."
        )
        if brain_context:
            system += "\n\n" + brain_context

        prompt = (
            f"Question : \"{question}\"\n\n"
            f"Voix 'espoir' (optimiste) :\n{espoir_text}\n\n"
            f"Voix 'doute' (critique) :\n{doute_text}\n\n"
            f"Produis ta synthèse. Quelle est ta position finale ?"
        )

        return _query_ollama_sync(prompt, system)


def _query_ollama_sync(prompt, system):
    """Send a prompt to Ollama and stream the response to stdout."""
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "system": system,
        "stream": True,
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=120)
        response.raise_for_status()
    except requests.ConnectionError:
        msg = "[Erreur: Ollama n'est pas accessible sur localhost:11434. Lance-le avec 'ollama serve'.]"
        print(msg)
        return msg
    except requests.Timeout:
        msg = "[Erreur: Ollama timeout après 120s.]"
        print(msg)
        return msg
    except requests.HTTPError as e:
        msg = f"[Erreur HTTP Ollama: {e}]"
        print(msg)
        return msg

    full_response = []
    for line in response.iter_lines():
        if line:
            try:
                chunk = json.loads(line)
                token = chunk.get("response", "")
                if token:
                    print(token, end="", flush=True)
                    full_response.append(token)
                if chunk.get("done", False):
                    break
            except json.JSONDecodeError:
                continue

    print()  # newline after streaming
    return "".join(full_response)


def main():
    if len(sys.argv) < 2:
        print("Usage: python dialogue.py \"Ta question ici\"")
        print("Exemple: python dialogue.py \"Est-ce que le trading est une bonne idée pour nous ?\"")
        sys.exit(1)

    question = " ".join(sys.argv[1:])
    graph_path = Path(__file__).parent / "graph.json"

    if not graph_path.exists():
        print("graph.json introuvable. Lance d'abord: python seed.py")
        sys.exit(1)

    brain = Brain(str(graph_path))
    print(f"Cerveau chargé: {brain.stats()}")
    print()
    print(f"=== Dialogue interne : \"{question}\" ===")
    print()

    dialogue = InternalDialogue(brain)
    result = dialogue.debate(question, rounds=2)

    # Save brain state after debate (activation changes)
    brain.save()

    print("=== Fin du dialogue ===")
    print(f"  Espoir: {len(result['espoir'])} interventions")
    print(f"  Doute:  {len(result['doute'])} interventions")


if __name__ == "__main__":
    main()
