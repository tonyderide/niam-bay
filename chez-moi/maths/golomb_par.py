"""Golomb en parallèle : pour chaque longueur L (dans l'ordre), on répartit les valeurs de la 2e marque sur 7 cœurs.
La première longueur qui donne une règle est l'optimum, puisque toutes les longueurs plus courtes ont été réfutées en entier."""
import concurrent.futures as cf, os, subprocess, sys, time
# golomb_large (256 bits) par défaut : golomb_branche (128 bits) déborde dès L >= 128
B = os.environ.get("GOLOMB_BIN", "/tmp/claude-1000/-home-tony/2c25ff3c-37a9-4b0e-a8fd-9600199a4cb4/scratchpad/golomb_large")
n, L = int(sys.argv[1]), int(sys.argv[2])
def job(pq): return pq, subprocess.run(["nice", "-n", "15", B, str(n), str(L)] + [str(v) for v in pq], capture_output=True, text=True).stdout.strip()
while True:
    t = time.time(); trouve = None
    with cf.ThreadPoolExecutor(7) as ex:
        travaux = [(p, q) for p in range(1, L // 2 + 1) for q in range(p + 1, L)] if "golomb_large" in B else [(p,) for p in range(1, L // 2 + 1)]
        for p, out in ex.map(job, travaux):
            if out != "rien" and trouve is None: trouve = out
    print(f"n={n} L={L} : {'RÈGLE ' + trouve if trouve else 'impossible'}  ({time.time()-t:.0f} s)", flush=True)
    if trouve: break
    L += 1
