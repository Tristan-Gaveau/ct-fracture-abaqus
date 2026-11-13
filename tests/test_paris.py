import math

import numpy as np
import pytest

import params as P
from k_analytique import calc_k_analytique
from paris import cycles, etude_sensibilite, fonction_k, restreindre, vitesse

def k_constant(valeur):
    return lambda a: np.full_like(np.asarray(a, dtype=float), valeur)


def test_k_constant_solution_exacte():
    a, N = cycles(k_constant(20.0), 10.0, 20.0, C_paris=1e-11, m=3.0, R=0.0)
    attendu = 0.010 / (1e-11 * 20.0 ** 3)           # 10 mm = 0,010 m
    assert np.isclose(N[-1], attendu, rtol=1e-9)


def test_fissure_centrale_solution_analytique():
    S, C0, m = 100.0, 1e-11, 3.0
    K = lambda a: S * np.sqrt(math.pi * np.asarray(a) * 1e-3)      # a en mm -> m
    a0, a1 = 2.0, 10.0
    _, N = cycles(K, a0, a1, C0, m, R=0.0)
    e = 1.0 - m / 2.0
    attendu = ((a1 * 1e-3) ** e - (a0 * 1e-3) ** e) / (e * C0 * (S * math.sqrt(math.pi)) ** m)
    assert np.isclose(N[-1], attendu, rtol=1e-4)


def test_n_tres_sensible_a_m():
    a0, a1 = 15.0, 35.0
    K = lambda a: calc_k_analytique(P.P_REEL, P.B_REEL, P.W, a)
    n25 = cycles(K, a0, a1, 1e-11, 2.5, 0.1)[1][-1]
    n35 = cycles(K, a0, a1, 1e-11, 3.5, 0.1)[1][-1]
    assert n25 / n35 > 10


def test_walker_gamma_1_egale_paris():
    k = np.linspace(10.0, 30.0, 5)
    assert np.allclose(vitesse(k, 0.1, 1e-11, 3.0, gamma=1.0, k_res=0.0),
                       vitesse(k, 0.1, 1e-11, 3.0, gamma=1.0, k_res=15.0))


def test_k_res_positif_accelere_et_negatif_ralentit():
    K = k_constant(20.0)
    n0 = cycles(K, 10, 20, 1e-11, 3.0, 0.1, gamma=0.5, k_res=0.0)[1][-1]
    n_plus = cycles(K, 10, 20, 1e-11, 3.0, 0.1, gamma=0.5, k_res=+5.0)[1][-1]
    n_moins = cycles(K, 10, 20, 1e-11, 3.0, 0.1, gamma=0.5, k_res=-5.0)[1][-1]
    assert n_plus < n0 < n_moins


def test_compression_totale_fissure_arretee():
    n = cycles(k_constant(20.0), 10, 20, 1e-11, 3.0, 0.1, gamma=0.5, k_res=-30.0)[1][-1]
    assert np.isinf(n)


def test_fermeture_simplifiee_k_min_nul():
    # K_min + K_res < 0 : on prend K_min = 0, donc DK = K_max,tot
    v = vitesse(20.0, 0.1, 1e-11, 3.0, gamma=1.0, k_res=-5.0)      # K_max,tot = 15, K_min,tot = 0
    assert np.isclose(v, 1e-11 * 15.0 ** 3)


def test_interpolation_k_de_a():
    alphas = np.linspace(0.3, 0.7, 9)
    a_pts = alphas * P.W
    k_pts = calc_k_analytique(P.P_REEL, P.B_REEL, P.W, a_pts)
    K = fonction_k(a_pts, k_pts)
    a_test = (alphas[:-1] + alphas[1:]) / 2.0 * P.W
    ref = calc_k_analytique(P.P_REEL, P.B_REEL, P.W, a_test)
    assert np.max(np.abs(K(a_test) / ref - 1.0)) < 2e-3


def test_pas_d_extrapolation():
    K = fonction_k([15, 20, 25, 30, 35], [10, 13, 17, 24, 38])
    with pytest.raises(ValueError):
        K(40.0)


def test_sensibilite_taille_du_tableau():
    lignes = etude_sensibilite(k_constant(20.0), 10, 20, 0.1)
    assert len(lignes) == 9

def test_restreindre_garde_la_plage():
    a, k = restreindre([15, 20, 25, 35], [1, 2, 3, 4], 20, 35)
    assert a == [20, 25, 35] and k == [2, 3, 4]