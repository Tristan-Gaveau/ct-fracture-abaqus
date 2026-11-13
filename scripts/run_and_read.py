# -*- coding: utf-8 -*-
"""Lecture des résultats Abaqus (.dat, .sta, .inp) et règle de K officiel.

Règle fixée (docs/hypotheses.md) : K officiel = moyenne, sur les contours 3 à 10,
de sqrt(J * E'), avec E' = E / (1 - nu^2) (déformations planes).
Ce module tourne avec le Python normal (pas celui d'Abaqus).
"""
import re
import sys

import numpy as np

import params as P

_NOMBRE = re.compile(r"[-+]?\d+\.\d+(?:[Ee][-+]?\d+)?")


def _nombres(texte):
    """Nombres avec point décimal (ignore les étiquettes comme '-8-' et les numéros de contour)."""
    return [float(x) for x in _NOMBRE.findall(texte)]


def _compact(ligne):
    return ligne.replace(" ", "").upper()


def lire_dat(chemin, n_contours=P.N_CONTOURS):
    """Retourne (J, K1, K2) : trois tableaux de n_contours valeurs.

    J en N/mm ; K1 et K2 en MPa*sqrt(mm) (unités du modèle : mm, N, MPa).
    """
    with open(chemin, encoding="utf-8", errors="replace") as f:
        lignes = f.read().splitlines()

    J, K1, K2 = [], [], []
    mode = None
    for ligne in lignes:
        s = _compact(ligne)
        if "J-INTEGRALESTIMATES" in s:
            mode, J = "J", []
            continue
        if "KFACTORESTIMATES" in s:
            mode, K1, K2 = "K", [], []
            continue
        if "LABELSREFERENCED" in s:
            mode = None
            continue
        if mode == "J":
            J += _nombres(ligne)
        elif mode == "K":
            if "K1:" in ligne:
                K1 += _nombres(ligne.split("K1:")[1])
            elif "K2:" in ligne:
                K2 += _nombres(ligne.split("K2:")[1])

    for nom, valeurs in (("J", J), ("K1", K1), ("K2", K2)):
        if len(valeurs) != n_contours:
            raise ValueError(
                "%s : %d valeurs lues au lieu de %d dans %s (titre du tableau différent ?)"
                % (nom, len(valeurs), n_contours, chemin)
            )
    return np.array(J), np.array(K1), np.array(K2)


def k_depuis_j(J):
    """K en MPa*sqrt(mm) pour chaque contour (déformations planes)."""
    J = np.asarray(J, dtype=float)
    if np.any(J <= 0):
        raise ValueError("J nul ou négatif : le modèle est à vérifier (signe de la charge ?)")
    return np.sqrt(J * P.E_PRIME)


def k_officiel(J):
    """(moyenne, écart-type) de K sur les contours 3 à 10, en MPa*sqrt(mm)."""
    k = k_depuis_j(J)[P.PREMIER_CONTOUR_RETENU - 1:]
    return float(k.mean()), float(k.std())


def indicateurs_qualite(J, K1, K2):
    """Dispersion de J (%) et rapport K2/K1 (%) sur les contours retenus."""
    i = P.PREMIER_CONTOUR_RETENU - 1
    j = np.asarray(J)[i:]
    dispersion = 100.0 * (j.max() - j.min()) / j.mean()
    k2_sur_k1 = 100.0 * np.mean(np.abs(np.asarray(K2)[i:])) / np.mean(np.asarray(K1)[i:])
    return float(dispersion), float(k2_sur_k1)


def compter_noeuds_elements(chemin_inp):
    """Nombre de nœuds et d'éléments d'un fichier .inp (la limite Learning Edition porte sur les nœuds)."""
    n_noeuds = n_elems = 0
    bloc = None
    with open(chemin_inp, encoding="utf-8", errors="replace") as f:
        for ligne in f:
            if ligne.startswith("**"):
                continue
            if ligne.startswith("*"):
                mot = ligne.split(",")[0].strip().upper()
                bloc = mot if mot in ("*NODE", "*ELEMENT") else None
                continue
            if bloc and ligne.strip():
                if bloc == "*NODE":
                    n_noeuds += 1
                else:
                    n_elems += 1
    return n_noeuds, n_elems


def analyse_terminee(chemin_sta):
    """True si le fichier .sta indique une fin normale du calcul."""
    try:
        with open(chemin_sta, encoding="utf-8", errors="replace") as f:
            return "COMPLETED SUCCESSFULLY" in f.read().upper()
    except FileNotFoundError:
        return False


if __name__ == "__main__":
    J, K1, K2 = lire_dat(sys.argv[1])
    k, ecart_type = k_officiel(J)
    disp, k2k1 = indicateurs_qualite(J, K1, K2)
    print("K officiel = %.1f MPa*sqrt(mm) = %.2f MPa*sqrt(m)  (ecart-type %.1f)"
          % (k, k * P.MMSQRT_VERS_MSQRT, ecart_type))
    print("Dispersion de J (contours 3-10) : %.1f %%" % disp)
    print("K2/K1 : %.1f %%" % k2k1)
