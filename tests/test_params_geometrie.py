import pytest

import geometrie as G
import params as P


def test_parametres_derives():
    assert abs(P.E_PRIME - 230769.23) < 0.1
    assert abs(P.P_PAR_MM - 400.0) < 1e-9
    assert abs(P.X_FACE_AVANT + 12.5) < 1e-9
    assert abs(P.Y_TROU - 13.75) < 1e-9
    assert abs(P.R_TROU - 6.25) < 1e-9


def test_pointe_a_60_pourcent_de_l_arete():
    assert abs(G.parametre_pointe(25.0) - 0.6) < 1e-12


def test_points_seam():
    pts = G.points_seam(25.0)
    assert abs(pts[0][0] - 3.25) < 1e-9 and abs(pts[1][0] - 22.0) < 1e-9
    assert pts[0][1] == 0.0 and pts[1][1] == 0.0


def test_disque_valide_pour_toute_la_plage_de_a():
    for a_sur_w in (0.3, 0.4, 0.5, 0.6, 0.7):
        G.verifier_disque(a_sur_w * P.W)


def test_disque_trop_pres_de_la_face_arriere():
    with pytest.raises(ValueError):
        G.verifier_disque(44.0)


def test_taille_premier_element():
    assert abs(G.h1_depuis_biais(4.0) - 0.27) < 0.01
    assert abs(G.h1_depuis_biais(10.0) - 0.15) < 0.01
    assert abs(G.h1_depuis_biais(40.0) - 0.05) < 0.01


def test_somme_des_elements_egale_la_longueur():
    ratio, n, L = 20.0, P.N_COUCHES, P.RAYON_DISQUE
    q = ratio ** (1.0 / (n - 1))
    h1 = G.h1_depuis_biais(ratio)
    assert abs(sum(h1 * q ** i for i in range(n)) - L) < 1e-9
