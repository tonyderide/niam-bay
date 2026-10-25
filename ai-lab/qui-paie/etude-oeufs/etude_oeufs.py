"""Réplication œufs (PREREG.md) : même code que l'étude lait, seuls la requête, les exclusions, les mots-clés et le sujet changent."""
import os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "etude-lait"))
import etude as E  # noqa: E402

ICI = os.path.dirname(os.path.abspath(__file__))
E.CORPUS = os.path.join(ICI, "corpus.json"); os.environ.setdefault("RESULTAT", "../etude-oeufs/RESULTAT.md"); os.environ.setdefault("N_ETUDE", "500")
E.REQUETE = '(egg[ti] OR eggs[ti]) AND (systematic review[pt] OR meta-analysis[pt]) AND ("2010"[dp] : "2026"[dp]) AND english[la]'
E.EXCLUS = re.compile(r"allerg|vaccine|oocyte|ivf|in vitro fert|embryo|\bhen|laying|poultry", re.I)
E.LAITIER = ["egg board", "egg nutrition center", "american egg board", "egg farmers", "egg industry", "australian eggs",
             "british egg", "lion code", "eggs canada", "poultry board"]
E.CONSIGNE = E.CONSIGNE.replace("sur les laitages", "sur les œufs").replace("les laitages ont", "les œufs ont")

if __name__ == "__main__":
    {"collecte": E.collecte, "classer": E.classer, "juger": E.juger}[sys.argv[1]]()
