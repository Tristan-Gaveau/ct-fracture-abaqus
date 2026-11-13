# -*- coding: utf-8 -*-
"""Jour 4 : convergence de maillage (a/W = 0,5) en faisant varier le ratio de biais.

10 couches fixes : le nombre de nœuds reste à peu près constant, seule la taille du
premier élément à la pointe change. Usage : python scripts/convergence.py
"""
import csv
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import chemins as C
import params as P
from geometrie import h1_depuis_biais
from k_analytique import calc_k_analytique
from run_case import configurer_mode, lancer_cas

RATIOS = [4.0, 10.0, 20.0, 40.0]


def main():
    configurer_mode(sys.argv[1:])
    C.FIGURES.mkdir(parents=True, exist_ok=True)
    k_ref = float(calc_k_analytique(P.P_REEL, P.B_REEL, P.W, P.A_SUR_W_REF * P.W))

    lignes = []
    for ratio in RATIOS:
        r = lancer_cas(P.A_SUR_W_REF, ratio, "ct_conv_b%02d" % int(ratio))
        ecart = 100.0 * (r["k_msqrt"] - k_ref) / k_ref
        lignes.append([ratio, round(h1_depuis_biais(ratio), 4), r["n_noeuds"], r["n_elems"],
                       round(r["k_msqrt"], 4), round(ecart, 3),
                       round(r["dispersion_j_pct"], 2), round(r["k2_sur_k1_pct"], 2)])

    chemin = C.RESULTATS / "convergence_maillage.csv"
    with open(chemin, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ratio_biais", "h_pointe_mm", "n_noeuds", "n_elements",
                    "K_FE_MPa_sqrt_m", "ecart_ASTM_pct", "dispersion_J_pct", "K2_sur_K1_pct"])
        w.writerows(lignes)

    h = [l[1] for l in lignes]
    k = [l[4] for l in lignes]
    plt.figure(figsize=(7, 4.5))
    plt.semilogx(h, k, "o-", label="K_FE (moyenne contours 3-10)")
    plt.axhline(k_ref, color="r", linestyle="--", label="ASTM E399 (%.2f)" % k_ref)
    plt.gca().invert_xaxis()
    plt.xlabel("Taille du premier élément à la pointe (mm)")
    plt.ylabel("K_I (MPa.m^0,5)")
    plt.title("Convergence du maillage (a/W = 0,5)")
    plt.grid(True, which="both", linestyle=":")
    plt.legend()
    plt.tight_layout()
    plt.savefig(C.FIGURES / "convergence_maillage.png", dpi=300)
    plt.close()
    print("Écrit :", chemin)


if __name__ == "__main__":
    main()
