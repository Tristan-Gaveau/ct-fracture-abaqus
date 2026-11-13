# -*- coding: utf-8 -*-
"""Propagation en fatigue : loi de Paris et loi de Walker, avec K(a) du calcul éléments finis.

Unités : a en mm, K en MPa*sqrt(m), da/dN en m/cycle (C en conséquence).

K_res (contrainte résiduelle) s'ajoute à K_max ET à K_min (superposition, fissure ouverte) :
DK ne change pas, mais R_eff change. Si K_min + K_res < 0 la fissure se ferme : on prend K_min = 0
(fermeture simplifiée). Si K_max + K_res <= 0, la fissure ne progresse pas (vitesse nulle).
Avec gamma = 1, Walker devient Paris (DK seul) : K_res n'a alors aucun effet tant que la fissure
reste ouverte.

Valeurs de C, m, gamma : ILLUSTRATIVES (params.py). Cite ta source dans le README.
Limite : la loi décrit la zone de propagation stable seulement (ni seuil DK_th, ni rupture finale).
Usage : python scripts/paris.py
"""
import csv
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import chemins as C
import params as P
from k_analytique import calc_k_analytique


def fonction_k(a_mm, k_msqrt, deg=6):
    """K(a) lissé (polynôme de Tchebychev) sur les points calculés ; refuse l'extrapolation.
    deg=6 sur 7 points = interpolation exacte ; un degré plus bas lisse le bruit numérique."""
    a_mm = np.asarray(a_mm, dtype=float)
    k = np.asarray(k_msqrt, dtype=float)
    ajuste = np.polynomial.Chebyshev.fit(a_mm, k, deg=min(deg, len(a_mm) - 1))
    a_min, a_max = float(a_mm.min()), float(a_mm.max())

    def K(a):
        a = np.asarray(a, dtype=float)
        if np.any(a < a_min - 1e-9) or np.any(a > a_max + 1e-9):
            raise ValueError("a hors du domaine calculé [%.1f ; %.1f] mm" % (a_min, a_max))
        return ajuste(a)
    return K


def fonction_k_analytique():
    def K(a):
        return calc_k_analytique(P.P_REEL, P.B_REEL, P.W, a)
    return K


def vitesse(k_max, R, C_paris, m, gamma=1.0, k_res=0.0):
    """da/dN (m/cycle). k_max (pour la charge maximale) et k_res en MPa*sqrt(m)."""
    k_max = np.asarray(k_max, dtype=float)
    k_max_tot = k_max + k_res
    k_min_tot = np.maximum(R * k_max + k_res, 0.0)           # fermeture simplifiée
    positif = np.maximum(k_max_tot, 0.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        r_eff = np.where(k_max_tot > 0.0, k_min_tot / k_max_tot, 0.0)
    return C_paris * (positif * (1.0 - r_eff) ** gamma) ** m


def cycles(K, a0_mm, a1_mm, C_paris, m, R, gamma=1.0, k_res=0.0, n=2000):
    """Intègre da/(da/dN) de a0 à a1. Retourne (a en mm, N cumulé) ; N = inf si la fissure s'arrête."""
    a = np.linspace(a0_mm, a1_mm, n)
    kr = k_res(a) if callable(k_res) else k_res
    v = vitesse(K(a), R, C_paris, m, gamma, kr)
    with np.errstate(divide="ignore"):
        inverse = 1.0 / v
    dN = 0.5 * (inverse[1:] + inverse[:-1]) * np.diff(a) * 1e-3      # mm -> m
    return a, np.concatenate([[0.0], np.cumsum(dN)])


def etude_sensibilite(K, a0_mm, a1_mm, R, C0=P.C_PARIS, ms=(2.5, 3.0, 3.5), facteurs_C=(0.8, 1.0, 1.2)):
    """N pour C +/- 20 % et plusieurs m. Attention : C et m sont corrélés ; varier m seul à C fixé
    exagère l'effet (à écrire dans le README)."""
    lignes = []
    for m in ms:
        for f in facteurs_C:
            _, N = cycles(K, a0_mm, a1_mm, C0 * f, m, R)
            lignes.append({"m": m, "C": C0 * f, "N": float(N[-1])})
    return lignes


def etude_k_res(K, k_res_unitaire, sigma0_calcul, a0_mm, a1_mm, valeurs_sigma0=(-100.0, -50.0, -25.0, 0.0, 25.0, 50.0, 100.0)):
    """N (loi de Walker) pour plusieurs amplitudes sigma0 de la contrainte résiduelle.

    K_res est linéaire en sigma0 (vérifié : 2 sigma0 donne 2 K_res, -sigma0 donne -K_res) : on met à
    l'échelle le K_res calculé pour sigma0_calcul. Retourne une liste de (sigma0, N)."""
    lignes = []
    for s0 in valeurs_sigma0:
        echelle = s0 / sigma0_calcul
        _, N = cycles(K, a0_mm, a1_mm, P.C_PARIS, P.M_PARIS, P.R_CHARGE, P.GAMMA_WALKER,
                      lambda a, e=echelle: e * k_res_unitaire(a))
        lignes.append((float(s0), float(N[-1])))
    return lignes


def charger_csv(chemin, col_a, col_k):
    with open(chemin, newline="", encoding="utf-8") as f:
        lignes = list(csv.DictReader(f))
    return [float(l[col_a]) for l in lignes], [float(l[col_k]) for l in lignes]


def restreindre(a_mm, k_msqrt, a_min, a_max):
    """Garde les points de a_min à a_max : plage de validité retenue pour la propagation."""
    garde = [(a, k) for a, k in zip(a_mm, k_msqrt) if a_min - 1e-9 <= a <= a_max + 1e-9]
    return [a for a, _ in garde], [k for _, k in garde]


def main():
    C.FIGURES.mkdir(parents=True, exist_ok=True)
    a0, a1 = P.A_INITIAL_SUR_W * P.W, P.A_FINAL_SUR_W * P.W
    cas = {"K analytique (ASTM)": fonction_k_analytique()}
    chemin_k = C.RESULTATS / "K_vs_a.csv"
    if chemin_k.exists():
        a_pts, k_pts = restreindre(*charger_csv(chemin_k, "a_mm", "K_FE_MPa_sqrt_m"), a0, a1)
        cas["K éléments finis"] = fonction_k(a_pts, k_pts)
    else:
        print("K_vs_a.csv absent : calcul avec le K analytique seulement (illustratif).")

    if P.K_IC is None:
        print("ATTENTION : K_IC non renseigné dans params.py ; vérifie K_max < K_Ic à a_final.")
    else:
        k_fin = float(cas["K analytique (ASTM)"](a1))
        if k_fin >= P.K_IC:
            print("ATTENTION : K_max = %.1f >= K_Ic = %.1f à a_final : Paris n'est plus valable." % (k_fin, P.K_IC))

    plt.figure(figsize=(7, 4.5))
    sorties = []
    for nom, K in cas.items():
        a, N = cycles(K, a0, a1, P.C_PARIS, P.M_PARIS, P.R_CHARGE)
        plt.plot(N, a, label="Paris, " + nom)
        sorties.append(("Paris", nom, float(N[-1])))
        for ligne in etude_sensibilite(K, a0, a1, P.R_CHARGE):
            sorties.append(("sensibilite m=%.1f C=%.2e" % (ligne["m"], ligne["C"]), nom, ligne["N"]))

    chemin_kres = C.RESULTATS / "K_res_vs_a.csv"      # colonnes : a_mm, sigma0_MPa, K_res_MPa_sqrt_m
    if chemin_kres.exists() and "K éléments finis" in cas:
        K = cas["K éléments finis"]
        a_kr, k_kr = charger_csv(chemin_kres, "a_mm", "K_res_MPa_sqrt_m")
        sigma0_calcul = charger_csv(chemin_kres, "a_mm", "sigma0_MPa")[1][0]
        k_res = fonction_k(a_kr, k_kr, deg=3)          # degré 3 : lisse le bruit numérique (~0,1 MPa√m)
        for s0, N in etude_k_res(K, k_res, sigma0_calcul, a0, a1):
            sorties.append(("Walker sigma0=%+.0f MPa" % s0, "K éléments finis", N))
        for s0 in (-50.0, 0.0, 50.0):
            e = s0 / sigma0_calcul
            a, N = cycles(K, a0, a1, P.C_PARIS, P.M_PARIS, P.R_CHARGE, P.GAMMA_WALKER,
                          lambda x, e=e: e * k_res(x))
            plt.plot(N, a, "--", label="Walker, sigma0 = %+.0f MPa" % s0)

    plt.xlabel("Nombre de cycles N")
    plt.ylabel("Longueur de fissure a (mm)")
    plt.title("Propagation : a(N)")
    plt.grid(True, linestyle=":")
    plt.legend()
    plt.tight_layout()
    plt.savefig(C.FIGURES / "a_de_N.png", dpi=300)
    plt.close()

    with open(C.RESULTATS / "paris_resultats.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["cas", "source_K", "N_cycles"])
        w.writerows(sorties)
    for s in sorties[:1]:
        print("%s (%s) : N = %.3e cycles de a = %.1f à %.1f mm" % (s[0], s[1], s[2], a0, a1))


if __name__ == "__main__":
    main()