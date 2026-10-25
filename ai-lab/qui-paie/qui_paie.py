"""Qui paie ? — pour une question de santé, les revues d'études récentes de PubMed, avec QUI les finance
et les conflits d'intérêts déclarés par leurs auteurs. Aucun jugement automatique sur le contenu :
on montre l'argent, le lecteur juge.

Usage : python3 qui_paie.py "cow milk children growth" [--n 10] [--industrie dairy,milk,nestle]
Sources : API publique NCBI E-utilities (PubMed + PubMed Central), sans clé."""
import argparse, re, sys, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

E = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
# mots qui signalent un financeur ou un lien industriel (on montre la phrase, on ne conclut pas)
INDUSTRIE = ["dairy council", "dairy farmers", "dairy research", "dairy management", "dairy uk", "dairy australia", "build dairy", "global dairy", "milk board", "milk council", "cniel", "farm fresh", "nestl", "danone", "lactalis", "arla", "fonterra",
             "friesland", "abbott", "mead johnson", "yili", "mengniu", "unilever", "pepsico", "coca-cola", "mars inc",
             "industry", "consultant", "honorari", "speaker", "advisory board"]
AUCUN = re.compile(r"(no|none|not any|nothing)\s+(conflict|competing|relevant)|declare[sd]? (that they have )?no|"
                   r"no (financial|potential) (conflict|interest)|have nothing to disclose|no competing", re.I)


def get(endpoint, **p):
    p.setdefault("tool", "qui-paie"); url = E + endpoint + "?" + urllib.parse.urlencode(p)
    for essai in range(4):
        try:
            return urllib.request.urlopen(url, timeout=40).read()
        except Exception:
            time.sleep(1 + essai)
    raise RuntimeError("NCBI injoignable")


def texte(n):
    return " ".join("".join(n.itertext()).split()) if n is not None else ""


def chercher(question, n):
    terme = f"({question}) AND (systematic review[pt] OR meta-analysis[pt])"
    r = ET.fromstring(get("esearch.fcgi", db="pubmed", term=terme, retmax=n, sort="relevance"))
    return [i.text for i in r.findall(".//Id")]


def pubmed(pmids):
    r = ET.fromstring(get("efetch.fcgi", db="pubmed", id=",".join(pmids), retmode="xml"))
    out = []
    for a in r.findall(".//PubmedArticle"):
        m = a.find("MedlineCitation")
        pmc = next((i.text for i in a.findall(".//ArticleId") if i.get("IdType") == "pmc"), None)
        out.append({
            "pmid": m.findtext("PMID"), "titre": texte(m.find(".//ArticleTitle")),
            "revue": m.findtext(".//Journal/ISOAbbreviation") or m.findtext(".//Journal/Title"),
            "annee": m.findtext(".//JournalIssue/PubDate/Year") or (m.findtext(".//JournalIssue/PubDate/MedlineDate") or "")[:4],
            "financeurs": sorted({g.findtext("Agency") for g in m.findall(".//Grant") if g.findtext("Agency")}),
            "coi": texte(m.find(".//CoiStatement")), "pmc": pmc, "financement": ""})
    return out


def pmc_details(art):
    """Dans PubMed Central (texte intégral libre) : déclaration de financement et de conflits d'intérêts."""
    if not art["pmc"]:
        return
    x = ET.fromstring(get("efetch.fcgi", db="pmc", id=art["pmc"].replace("PMC", ""), retmode="xml"))
    fin = [texte(f) for f in x.iter() if f.tag in ("funding-group", "funding-statement")]
    fin += [texte(s) for s in x.iter("sec") if re.match(r"(funding|financial support|sources? of funding)", texte(s.find("title")), re.I)]
    coi = [texte(f) for f in x.iter("fn") if f.get("fn-type") in ("COI-statement", "conflict", "competing-interests")]
    coi += [texte(s) for s in x.iter("sec") if re.match(r"(conflicts? of interest|competing interests|disclosure|declaration of interest)", texte(s.find("title")), re.I)]
    art["financement"] = " | ".join(dict.fromkeys(f for f in fin if f))[:600]
    if not art["coi"]:
        art["coi"] = " | ".join(dict.fromkeys(c for c in coi if c))[:600]


def phrases_argent(art, mots):
    """Les phrases des déclarations qui citent un lien industriel ou rémunéré (3 au plus, raccourcies)."""
    tout = re.split(r"(?<=[.;])\s+", art["financement"] + " " + art["coi"])
    return [p[:220] for p in tout if any(m in p.lower() for m in mots)][:3]


def drapeaux(art, mots):
    tout = " ".join([art["financement"], art["coi"], " ".join(art["financeurs"])]).lower()
    trouves = sorted({m for m in mots if m in tout})
    if trouves:
        return "lien industriel ou rémunéré cité (" + ", ".join(trouves) + ")"
    if AUCUN.search(art["coi"]):
        return "aucun conflit déclaré"
    if not art["coi"] and not art["financement"] and not art["financeurs"]:
        return "rien de déclaré dans les données accessibles"
    return "financement public ou non précisé"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("question"); ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--industrie", default=""); a = ap.parse_args()
    mots = INDUSTRIE + [m.strip().lower() for m in a.industrie.split(",") if m.strip()]
    ids = chercher(a.question, a.n)
    if not ids:
        sys.exit("aucune revue trouvée")
    arts = pubmed(ids)
    for art in arts:
        try:
            pmc_details(art)
        except Exception:
            art["financement"] = art["financement"] or "(texte intégral illisible)"
        time.sleep(0.35)  # NCBI : 3 requêtes/s sans clé
    print(f"# Qui paie ? « {a.question} »\n\n{len(arts)} revues systématiques ou méta-analyses (PubMed, par pertinence).\n")
    for art in arts:
        print(f"## {art['titre']}\n{art['revue']}, {art['annee']} · https://pubmed.ncbi.nlm.nih.gov/{art['pmid']}/")
        print(f"- **Verdict argent** : {drapeaux(art, mots)}")
        if art["financeurs"]:
            print(f"- Subventions (PubMed) : {', '.join(art['financeurs'])}")
        if art["financement"]:
            print(f"- Financement (texte) : {art['financement'][:300]}")
        lignes = phrases_argent(art, mots)
        for l in lignes:
            print(f"  - « {l} »")
        if not lignes:
            print(f"- Conflits déclarés : {art['coi'][:300] or '(non trouvés)'}")
        print()


if __name__ == "__main__":
    main()
