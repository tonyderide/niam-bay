import numpy as np, sys; sys.argv = ["x", "aucun"]
exec(open("etude.py").read().split("DON =")[0].replace("cache=True", "cache=False"))
# long : entrée 100, SL 2 %, activation 0,1 %, trailing 1 %
B = np.array([[0, 100, 101, 99.5, 100.8], [0, 100.8, 103, 100.5, 102.5], [0, 102.5, 102.6, 101.5, 101.8]], float)
r = lancer(B, (0.02, 0.01, 0.001), 1); print("long", r[0], "attendu", 103 * 0.99 / 100 - 1 - 0.0005 - 0.0005 * 1.0197)
B = np.array([[0, 100, 100.5, 97, 98]], float); r = lancer(B, (0.02, 0.01, 0.001), 1); print("SL long", r[0, 0], "attendu", 0.98 - 1 - 0.0005 - 0.0005 * 0.98)
B = np.array([[0, 100, 100.5, 99, 99.2], [0, 99.2, 99.3, 97, 97.5], [0, 97.5, 98.2, 97.4, 98]], float); r = lancer(B, (0.02, 0.01, 0.001), -1); print("short", r[0], "attendu", 1 - 97 * 1.01 / 100 - 0.0005 - 0.0005 * 0.9797)
