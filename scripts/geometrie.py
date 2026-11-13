# -*- coding: utf-8 -*-
"""Coordonnées calculées à partir de a : à utiliser avec findAt() dans build_ct.py.

Repère : origine sur la ligne de chargement (axe des trous), y = 0 dans le plan de la fissure.
Python pur : testable sans Abaqus.
"""
import math

import params as P


def pointe(a):
    return (a, 0.0)


def parametre_pointe(a):
    """Paramètre (0 à 1) de la pointe sur l'arête y = 0, mesuré depuis la face avant."""
    return (a - P.X_FACE_AVANT) / (P.X_FACE_ARRIERE - P.X_FACE_AVANT)


def points_seam(a, r=P.RAYON_DISQUE):
    """Un point au milieu de chaque arête de la fissure, de la face avant à la pointe."""
    return [((P.X_FACE_AVANT + (a - r)) / 2.0, 0.0), (a - r / 2.0, 0.0)]


def centres_trous():
    return [(0.0, P.Y_TROU), (0.0, -P.Y_TROU)]


def points_aretes_radiales(a, r=P.RAYON_DISQUE):
    """Un point sur chacune des 4 arêtes radiales (gauche, droite, haut, bas)."""
    return [(a - r / 2.0, 0.0), (a + r / 2.0, 0.0), (a, r / 2.0), (a, -r / 2.0)]


def points_arcs(a, r=P.RAYON_DISQUE):
    """Un point au milieu de chacun des 4 arcs du disque."""
    c = r / math.sqrt(2.0)
    return [(a + c, c), (a - c, c), (a - c, -c), (a + c, -c)]


def verifier_disque(a, r=P.RAYON_DISQUE, marge=2.0):
    """Le disque de pointe ne doit toucher ni les faces ni les trous (marge en mm)."""
    if a - r <= P.X_FACE_AVANT + marge:
        raise ValueError("Disque trop proche de la face avant (a = %.1f mm)" % a)
    if a + r >= P.X_FACE_ARRIERE - marge:
        raise ValueError("Disque trop proche de la face arrière (a = %.1f mm)" % a)
    for yc in (P.Y_TROU, -P.Y_TROU):
        ecart = math.hypot(a, yc) - P.R_TROU - r
        if ecart < marge:
            raise ValueError("Disque trop proche d'un trou (a = %.1f mm)" % a)


def h1_depuis_biais(ratio, longueur=P.RAYON_DISQUE, n=P.N_COUCHES):
    """Taille du premier élément à la pointe (mm) pour n éléments en progression
    géométrique, ratio = plus grand / plus petit."""
    q = ratio ** (1.0 / (n - 1))
    return longueur * (q - 1.0) / (q ** n - 1.0)
