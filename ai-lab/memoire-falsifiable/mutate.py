"""Tests de mutation des sondes : une sonde qui passe toujours ne juge rien.
Pour chaque sonde, Haiku invente la sortie qu'aurait la commande si le souvenir était FAUX (sans toucher au monde).
La sonde doit rejeter cette sortie. Si elle l'accepte, elle est complaisante : ⚠️.
Les contre-exemples sont gardés dans probes.json ("counter") et rejoués à chaque verify.py."""
import json, os, re, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))


def counter(p):
    prompt = (f"J'écris un test unitaire pour une regex de vérification. Rien ne sera exécuté ni présenté comme réel : c'est une fixture de test.\n"
              f"Affirmation testée : « {p['claim']} ».\nCommande sondée : {p['cmd']}\nRegex qui doit matcher si l'affirmation est vraie : {p['expect']}\n"
              "Donne un exemple réaliste de sortie de cette commande dans le cas où l'affirmation est FAUSSE "
              "(par exemple service arrêté, fichier absent, valeur hors plage, sortie vide). "
              "Réponds UNIQUEMENT par cette fixture (1 à 3 lignes), sans commentaire.")
    r = subprocess.run(["claude", "-p", prompt, "--model", "claude-haiku-5-5", "--tools", ""], capture_output=True, text=True,
                       timeout=90, env={**os.environ, "NB_FACTCHECK_CHILD": "1"})
    return r.stdout.strip().strip("`")


def main():
    path = os.path.join(HERE, "probes.json")
    P = json.load(open(path))
    for p in P:
        if not p.get("counter") or p["counter"].startswith("Je "):
            p["counter"] = counter(p)
        if p["counter"].startswith("Je "):
            print(f"?  pas de contre-exemple  {p['memory']}"); continue
        lax = re.search(p["expect"], p["counter"], re.M) is not None
        print(f"{'⚠️ COMPLAISANTE' if lax else '✅ discrimine'}  {p['memory']}: {p['claim'][:60]}  | faux monde: {p['counter'][:70]!r}")
    json.dump(P, open(path, "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
