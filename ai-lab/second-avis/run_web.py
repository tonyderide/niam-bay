import json, sys
sys.path.insert(0, "."); from web import check_web
B = json.load(open("bench_web.json")); res = []
for b in B:
    mark, why = check_web(b["claim"]); res.append(dict(b, mark=mark, why=why)); print(b["id"], mark, b["truth"], b["claim"][:50], "|", why[:90], flush=True)
fv = sum(r["mark"] == "✓" and not r["truth"] for r in res); fx = sum(r["mark"] == "✗" and r["truth"] for r in res)
cov = sum(r["mark"] == "✓" and r["truth"] for r in res)
ok = fv == 0 and cov >= 6 and fx <= 1
line = f"v1 web : faux ✓ {fv} | faux ✗ {fx} | vrais confirmés {cov}/10 | faux réfutés {sum(r['mark']=='✗' and not r['truth'] for r in res)}/10 → {'CRITÈRE ATTEINT' if ok else 'critère NON atteint'}"
print(line); open("RESULTATS.md", "a").write("\n" + line + "\n"); json.dump(res, open("resultats_web.json", "w"), indent=1, ensure_ascii=False)
