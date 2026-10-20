"""Vide-grenier assisté : photo d'objet (Telegram) -> identification + prix des annonces comparables (web, lecture) -> annonce prête.
Tony publie lui-même. Conseil intérieur : OUI 6,91 (1020)."""
import json, os, re, subprocess, urllib.request

SCRATCH = os.path.expanduser("~/.local/state/nb/vend")
PROMPT = """Tu aides Tony à vendre un objet d'occasion en France (Vinted ou Leboncoin). Regarde la photo {img}{legende}.
1) Identifie l'objet (marque et modèle si c'est visible ; dis franchement si tu n'es pas sûr).
2) Cherche sur le web (WebSearch) le prix de vente d'occasion d'objets comparables en France. Cite 2 ou 3 sources.
3) Rédige en français une annonce honnête : un titre de moins de 60 caractères, une description de 4 à 6 lignes (état visible, défauts visibles), un prix conseillé, un prix plancher, et la plateforme conseillée.
Ne gonfle rien et n'invente aucune caractéristique que la photo ne montre pas. Si l'objet ne vaut pas la peine d'être vendu (moins de 5 €), dis-le.
Réponds en texte simple, sans markdown lourd."""


def proposer(body, tg_api):
    m = re.search(r"\[photo:([^\]]+)\]", body)
    if not m:
        return "Envoie-moi la photo de l'objet (avec une légende si tu veux : état, ce que tu sais dessus), je prépare l'annonce."
    legende = body[:m.start()].strip()
    os.makedirs(SCRATCH, exist_ok=True)
    try:
        path = json.load(urllib.request.urlopen(tg_api + "getFile?file_id=" + m.group(1), timeout=30))["result"]["file_path"]
        img = os.path.join(SCRATCH, m.group(1)[-16:] + ".jpg")
        urllib.request.urlretrieve(tg_api.replace("/bot", "/file/bot") + path, img)
    except Exception as e:
        return f"Je n'arrive pas à récupérer la photo ({type(e).__name__})."
    r = subprocess.run(["claude", "-p", PROMPT.format(img=img, legende=f" (Tony précise : {legende})" if legende else ""),
                        "--model", "claude-sonnet-5-5", "--allowedTools", "Read", "WebSearch"],
                       capture_output=True, text=True, timeout=400, env={**os.environ, "NB_FACTCHECK_CHILD": "1"}, cwd=SCRATCH)
    out = r.stdout.strip() or "(pas de réponse)"
    open(os.path.join(SCRATCH, "journal.jsonl"), "a").write(json.dumps({"img": img, "legende": legende, "annonce": out[:3000]}, ensure_ascii=False) + "\n")
    return "🏷️ Annonce prête (tu publies toi-même) :\n\n" + out + "\n\nQuand c'est vendu, dis-moi « vendu X € » pour qu'on compte."
