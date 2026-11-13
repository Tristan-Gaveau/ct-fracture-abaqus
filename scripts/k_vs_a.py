# -*- coding: utf-8 -*-
"""Jour 5 : K en fonction de la longueur de fissure, a/W de 0,3 à 0,7 (9 valeurs).

Usage : python scripts/k_vs_a.py
"""
import csv
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import chemins as C
import params as P
from geometrie import verifier_disque
from k_analytique import calc_k_analytique
from run_case import configurer_mode, lancer_cas



def main():
    configurer_mode(sys.argv[1:])
    C.FIGURES.mkdir(parents=True, exist_ok=True)
    alphas = np.linspace(0.30, 0.70, 9)
    for alpha in alphas:                       # on échoue tôt, avant le premier calcul
        verifier_disque(alpha * P.W)

    lignes = []
    for alpha in alphas:
        a = alpha * P.W
        r = lancer_cas(float(alpha), P.RATIO_BIAIS, "ct_ka%03d" % int(round(alpha * 100)))
        k_ana = float(calc_k_analytique(P.P_REEL, P.B_REEL, P.W, a))
        ecart = 100.0 * (r["k_msqrt"] - k_ana) / k_ana
        lignes.append([round(float(alpha), 3), round(a, 2), r["n_noeuds"],
                       round(r["k_msqrt"], 4), round(k_ana, 4), round(ecart, 3),
                       round(r["dispersion_j_pct"], 2), round(r["k2_sur_k1_pct"], 2)])

    chemin = C.RESULTATS / "K_vs_a.csv"
    with open(chemin, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["alpha", "a_mm", "n_noeuds", "K_FE_MPa_sqrt_m", "K_ASTM_MPa_sqrt_m",
                    "ecart_pct", "dispersion_J_pct", "K2_sur_K1_pct"])
        w.writerows(lignes)

    a_mm = [l[1] for l in lignes]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.5, 6.5), sharex=True,
                                   gridspec_kw={"height_ratios": [3, 1]})
    ax1.plot(a_mm, [l[4] for l in lignes], "k--", label="ASTM E399")
    ax1.plot(a_mm, [l[3] for l in lignes], "bo-", label="Abaqus (intégrale J)")
    ax1.set_ylabel("K_I (MPa.m^0,5)")
    ax1.set_title("K_I en fonction de la longueur de fissure")
    ax1.grid(True, linestyle=":")
    ax1.legend()
    ax2.plot(a_mm, [l[5] for l in lignes], "rs-")
    ax2.axhline(0.0, color="k", linewidth=0.8)
    ax2.set_xlabel("Longueur de fissure a (mm)")
    ax2.set_ylabel("Écart (%)")
    ax2.grid(True, linestyle=":")
    plt.tight_layout()
    plt.savefig(C.FIGURES / "K_vs_a.png", dpi=300)
    plt.close()
    print("Écrit :", chemin)


if __name__ == "__main__":
    main()
