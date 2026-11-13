# -*- coding: utf-8 -*-
"""
Calcul analytique du facteur d'intensité de contrainte K_I
pour une éprouvette CT selon la norme ASTM E399.
"""
import numpy as np


def f_astm_e399(alpha):
    """Fonction géométrique sans dimension f(a/W) selon ASTM E399."""
    alpha = np.asarray(alpha, dtype=float)
    if np.any((alpha < 0.2) | (alpha >= 1.0)):
        raise ValueError("La formule ASTM E399 n'est valide que pour 0.2 <= a/W < 1.0")

    num = (2.0 + alpha) * (
        0.886 + 4.64 * alpha - 13.32 * alpha**2 + 14.72 * alpha**3 - 5.6 * alpha**4
    )
    den = (1.0 - alpha) ** 1.5
    return num / den


def calc_k_analytique(P_N, B_mm, W_mm, a_mm):
    """K_I en MPa*sqrt(m). P en N, B, W et a en mm (a mesuré depuis la ligne de chargement)."""
    alpha = np.asarray(a_mm, dtype=float) / W_mm
    B_m = B_mm * 1e-3
    W_m = W_mm * 1e-3
    K_Pa_sqrt_m = (P_N / (B_m * np.sqrt(W_m))) * f_astm_e399(alpha)
    return K_Pa_sqrt_m * 1e-6


if __name__ == "__main__":
    f_val = f_astm_e399(0.5)
    K_val = calc_k_analytique(10000.0, 25.0, 50.0, 25.0)
    print(f"f(0,5) = {f_val:.4f} (attendu ~9,66)")
    print(f"K_I    = {K_val:.4f} MPa*sqrt(m) (attendu ~17,28)")
