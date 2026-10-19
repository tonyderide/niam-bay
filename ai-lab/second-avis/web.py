"""Second avis v1 : faits publics (protocole f050c08). ✓/✗ seulement si recherche + citation présente sur la page + 2e juge aveugle concordent."""
import html, ipaddress, json, os, re, socket, subprocess, urllib.parse, urllib.request
ENV = {**os.environ, "NB_FACTCHECK_CHILD": "1"}


def claude(prompt, tools=""):
    args = ["claude", "-p", prompt, "--model", "claude-haiku-5-5"] + (["--allowedTools", *tools.split()] if tools else ["--tools", ""])
    return subprocess.run(args, capture_output=True, text=True, timeout=240, env=ENV).stdout


def safe_url(u):
    p = urllib.parse.urlparse(u)
    if p.scheme != "https" or not p.hostname: return False
    try:
        return all(ipaddress.ip_address(a[4][0]).is_global for a in socket.getaddrinfo(p.hostname, 443))
    except Exception:
        return False


def page_text(u):
    req = urllib.request.Request(u, headers={"User-Agent": "NiamBay-second-avis/0.1 (lecture seule)"})
    raw = urllib.request.urlopen(req, timeout=20).read(3_000_000).decode("utf-8", "replace")
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", raw))).lower()


def check_web(claim):
    r = claude("Vérifie cette affirmation avec une recherche web. Réponds UNIQUEMENT en JSON : "
               '{"verdict": "vrai"|"faux"|"inconnu", "url": "<page source https>", "quote": "<citation EXACTE, courte, copiée de la page>"}\n'
               f"Affirmation : {claim}", tools="WebSearch WebFetch")
    m = re.search(r"\{.*\}", r, re.S)
    if not m: return "?", "pas de réponse exploitable"
    v = json.loads(m.group(0))
    if v.get("verdict") not in ("vrai", "faux"): return "?", "la recherche n'a pas tranché"
    u, q = v.get("url", ""), re.sub(r"\s+", " ", v.get("quote", "")).strip().lower()
    if len(q) < 12 or not safe_url(u): return "?", "source ou citation inutilisable"
    try:
        if q not in page_text(u): return "?", f"citation introuvable sur {u}"
    except Exception as e:
        return "?", f"page illisible ({type(e).__name__})"
    j = claude(f"Affirmation : {claim}\nCitation d'une source : « {v['quote']} »\nLa citation SOUTIENT-elle, CONTREDIT-elle l'affirmation, ou ne tranche-t-elle PAS ? Un seul mot : SOUTIENT, CONTREDIT ou PAS.").upper()
    second = "vrai" if "SOUTIENT" in j else "faux" if "CONTREDIT" in j else None
    if second != v["verdict"]: return "?", "le 2e juge ne confirme pas"
    return ("✓" if second == "vrai" else "✗"), f"{u} : « {v['quote'][:100]} »"
