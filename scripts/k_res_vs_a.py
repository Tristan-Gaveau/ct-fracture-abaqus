# -*- coding: utf-8 -*-
"""K_res(a) : facteur d'intensité de contrainte dû à une contrainte résiduelle, par superposition.

Aucune charge externe : pression sur les lèvres de la fissure (p = -sigma_res), profil auto-équilibré
sigma0 (1 - 6u + 6u²) sur toute la largeur. K_res est SIGNÉ (K1 du tableau des facteurs d'intensité).
Même plage de a/W que la propagation (params.A_INITIAL_SUR_W à A_FINAL_SUR_W).

Usage : python scripts/k_res_vs_a.py [--manuel] [--reprendre] [--sigma0=100]
Écrit results/K_res_vs_a.csv (colonnes lues par paris.py : a_mm, K_res_MPa_sqrt_m).
"""
import csv
import sys

import numpy as np

import chemins as C
import params as P
from geometrie import verifier_disque
from run_case import configurer_mode, lancer_cas

SIGMA0 = 100.0          # MPa, amplitude du profil : HYPOTHÈSE à justifier dans le README


def main():
    options = sys.argv[1:]
    configurer_mode(options)
    sigma0 = SIGMA0
    for o in options:
        if o.startswith("--sigma0="):
            sigma0 = float(o.split("=")[1])
    alphas = np.round(np.arange(P.A_INITIAL_SUR_W, P.A_FINAL_SUR_W + 1e-9, 0.05), 3)
    for alpha in alphas:
        verifier_disque(alpha * P.W)

    lignes = []
    for alpha in alphas:
        nom = "ct_kr%03d" % int(round(alpha * 100))
        r = lancer_cas(float(alpha), P.RATIO_BIAIS, nom, mode="k_res", sigma0=sigma0, profil="equilibre")
        lignes.append([round(float(alpha), 3), round(alpha * P.W, 2), sigma0, r["n_noeuds"],
                       round(r["k1_msqrt"], 4), round(r["dispersion_j_pct"], 2)])

    C.RESULTATS.mkdir(parents=True, exist_ok=True)
    chemin = C.RESULTATS / "K_res_vs_a.csv"
    with open(chemin, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["alpha", "a_mm", "sigma0_MPa", "n_noeuds", "K_res_MPa_sqrt_m", "dispersion_J_pct"])
        w.writerows(lignes)
    print("Écrit :", chemin)


if __name__ == "__main__":
    main()