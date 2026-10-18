import json, sys, time
sys.path.insert(0, "."); from verif import check_claims
B = json.load(open("bench.json")); res = []
for b in B:
    out = check_claims(b["claim"])
    mark = out[0][1] if out else "?"; why = out[0][2] if out else "rien extrait"
    res.append(dict(b, mark=mark, why=why)); print(b["id"], mark, b["truth"], b["claim"][:60], "|", why[:70], flush=True)
fv = sum(1 for r in res if r["mark"] == "✓" and r["truth"] is not True)
fx = sum(1 for r in res if r["mark"] == "✗" and r["truth"] is not False)
calc_ok = sum(1 for r in res if r["kind"] == "calc" and ((r["mark"] == "✓") == (r["truth"] is True)) and r["mark"] != "?")
code_ok = sum(1 for r in res if r["kind"] == "code" and ((r["mark"] == "✓") == (r["truth"] is True)) and r["mark"] != "?")
other_bad = sum(1 for r in res if r["kind"] == "other" and r["mark"] != "?")
ok = fv == 0 and calc_ok >= 10 and code_ok >= 8 and other_bad == 0
line = f"faux ✓ {fv} | faux ✗ {fx} | calculs justes {calc_ok}/12 | code juste {code_ok}/10 | autres tranchés à tort {other_bad}/8 → {'CRITÈRE ATTEINT' if ok else 'critère NON atteint'}"
print(line); json.dump(res, open("resultats.json", "w"), indent=1, ensure_ascii=False); open("RESULTATS.md", "w").write("# Banc v0\n\n" + line + "\n")
