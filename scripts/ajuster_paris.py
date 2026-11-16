# -*- coding: utf-8 -*-
"""Ajuste C et m de la loi de Paris sur des points lus sur une courbe (figure numérisée).

Entrée : un CSV à deux colonnes, dans les unités de la MIL-HDBK-5J :
    dK_ksi_sqrt_in, dadN_in_par_cycle
(lignes commençant par # ignorées). Sortie : C et m en unités SI (da/dN en m/cycle, DK en MPa*sqrt(m)),
écart-type du résidu en log10, plage de DK couverte, et plage de DK de l'étude (pour vérifier qu'elle est
couverte par les données).

Usage : python scripts/ajuster_paris.py results/raw/mil_hdbk_fig_2_3_1_4_9.csv
"""
import csv
import sys

import numpy as np

import params as P
from k_analytique import calc_k_analytique

POUCE_EN_M = 0.0254
KSI_EN_MPA = 6.894757
KSI_RACINE_POUCE_EN_MPA_RACINE_M = KSI_EN_MPA * POUCE_EN_M ** 0.5      # = 1,0988


def convertir_si(dk_ksi_racine_pouce, dadn_pouce_par_cycle):
    """(DK en MPa*sqrt(m), da/dN en m/cycle) à partir des unités du handbook."""
    dk = np.asarray(dk_ksi_racine_pouce, dtype=float) * KSI_RACINE_POUCE_EN_MPA_RACINE_M
    dadn = np.asarray(dadn_pouce_par_cycle, dtype=float) * POUCE_EN_M
    return dk, dadn


def ajuster(dk_mpa, dadn_m):
    """Régression linéaire en log-log : log10(da/dN) = log10(C) + m log10(DK). Retourne (C, m, écart-type)."""
    x = np.log10(np.asarray(dk_mpa, dtype=float))
    y = np.log10(np.asarray(dadn_m, dtype=float))
    if len(x) < 3:
        raise ValueError("Il faut au moins 3 points pour ajuster C et m")
    m, log_c = np.polyfit(x, y, 1)
    residu = y - (m * x + log_c)
    return 10.0 ** log_c, float(m), float(residu.std(ddof=2))


def _nombre(texte):
    return float(texte.strip().replace(",", "."))


def lire_points(chemin):
    """Lit un CSV « DK, da/dN ». Accepte le format anglais (virgule entre colonnes, point décimal) et le
    format français de WebPlotDigitizer (point-virgule entre colonnes, virgule décimale)."""
    with open(chemin, encoding="utf-8") as f:
        lignes = [l.strip() for l in f if l.strip() and not l.lstrip().startswith("#")]
    dk, dadn = [], []
    for l in lignes[1:]:                                   # la première ligne est l'en-tête
        morceaux = l.split(";" if ";" in l else ",")
        if len(morceaux) != 2:
            raise ValueError("Ligne illisible (2 colonnes attendues) : %r" % l)
        dk.append(_nombre(morceaux[0]))
        dadn.append(_nombre(morceaux[1]))
    return dk, dadn


def plus_grand_ecart(dk_mpa, dadn_m, c, m):
    """Indice du point le plus éloigné de la droite ajustée et facteur d'écart (>= 1) sur da/dN."""
    x = np.log10(np.asarray(dk_mpa, dtype=float))
    y = np.log10(np.asarray(dadn_m, dtype=float))
    residu = y - (np.log10(c) + m * x)
    i = int(np.argmax(np.abs(residu)))
    return i, float(10.0 ** abs(residu[i]))


def plage_etude_dk():
    """Plage de DK (MPa*sqrt(m)) de l'étude : (1 - R) K(a) de a_initial à a_final, K de la formule ASTM."""
    a = np.array([P.A_INITIAL_SUR_W * P.W, P.A_FINAL_SUR_W * P.W])
    k = calc_k_analytique(P.P_REEL, P.B_REEL, P.W, a)
    return float((1.0 - P.R_CHARGE) * k[0]), float((1.0 - P.R_CHARGE) * k[1])


if __name__ == "__main__":
    dk_ksi, dadn_in = lire_points(sys.argv[1])
    dk, dadn = convertir_si(dk_ksi, dadn_in)
    c, m, ecart = ajuster(dk, dadn)
    print("%d points ; DK couvert : %.1f à %.1f MPa*sqrt(m) (%.1f à %.1f ksi*sqrt(in))"
          % (len(dk), dk.min(), dk.max(), min(dk_ksi), max(dk_ksi)))
    print("C = %.3e (m/cycle, MPa*sqrt(m)) ; m = %.3f ; écart-type du résidu = %.3f en log10 (facteur %.2f)"
          % (c, m, ecart, 10 ** ecart))
    i, facteur = plus_grand_ecart(dk, dadn, c, m)
    print("Point le plus éloigné de l'ajustement : n° %d (ligne %d du fichier de données), DK = %.1f ksi*sqrt(in), "
          "écart d'un facteur %.2f sur da/dN%s" % (i + 1, i + 1, dk_ksi[i], facteur,
                                                  "  <- à vérifier (point aberrant ?)" if facteur > 2.0 else ""))
    bas, haut = plage_etude_dk()
    print("DK de l'étude (R = %.2f) : %.1f à %.1f MPa*sqrt(m) -> %s"
          % (P.R_CHARGE, bas, haut, "couvert par les données" if dk.min() <= bas and haut <= dk.max()
             else "ATTENTION : en dehors des données"))