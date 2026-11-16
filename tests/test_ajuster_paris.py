import numpy as np
import pytest

import params as P
from ajuster_paris import (KSI_RACINE_POUCE_EN_MPA_RACINE_M, ajuster, convertir_si, lire_points,
                           plage_etude_dk, plus_grand_ecart)


def test_facteur_de_conversion():
    assert abs(KSI_RACINE_POUCE_EN_MPA_RACINE_M - 1.0988) < 1e-3


def test_retrouve_c_et_m_a_partir_de_points_synthetiques():
    c_vrai, m_vrai = 2.0e-11, 3.1
    dk_mpa = np.array([8.0, 10.0, 14.0, 20.0, 28.0, 40.0])
    dadn_m = c_vrai * dk_mpa ** m_vrai
    dk_ksi = dk_mpa / KSI_RACINE_POUCE_EN_MPA_RACINE_M
    dadn_in = dadn_m / 0.0254
    dk, dadn = convertir_si(dk_ksi, dadn_in)
    c, m, ecart = ajuster(dk, dadn)
    assert abs(m - m_vrai) < 1e-9 and abs(c / c_vrai - 1.0) < 1e-9 and ecart < 1e-9


def test_ajustement_avec_dispersion_reste_proche():
    rng = np.random.default_rng(0)
    dk = np.linspace(8.0, 40.0, 40)
    dadn = 2.0e-11 * dk ** 3.1 * 10 ** rng.normal(0.0, 0.05, dk.size)
    c, m, ecart = ajuster(dk, dadn)
    assert abs(m - 3.1) < 0.15 and 0.03 < ecart < 0.08


def test_moins_de_trois_points_refuse():
    with pytest.raises(ValueError):
        ajuster([10.0, 20.0], [1e-8, 5e-8])


def test_lecture_du_csv(tmp_path):
    p = tmp_path / "points.csv"
    p.write_text("# figure 2.3.1.4.9\ndK_ksi_sqrt_in,dadN_in_par_cycle\n10,1e-6\n20,8e-6\n40,6e-5\n", encoding="utf-8")
    dk, dadn = lire_points(p)
    assert dk == [10.0, 20.0, 40.0] and dadn == [1e-6, 8e-6, 6e-5]


def test_plage_de_dk_de_l_etude():
    bas, haut = plage_etude_dk()
    assert 11.0 < bas < 12.5 and 33.0 < haut < 36.0


def test_lecture_du_csv_au_format_francais_de_webplotdigitizer(tmp_path):
    p = tmp_path / "fr.csv"
    p.write_text("# figure\ndK_ksi_sqrt_in,dadN_in_par_cycle\n10,138834266342467; 8,703358868036831e-7\n"
                 "11,1661688715573; 0,000001158751653851105\n", encoding="utf-8")
    dk, dadn = lire_points(p)
    assert abs(dk[0] - 10.138834266342467) < 1e-12 and abs(dadn[0] - 8.703358868036831e-7) < 1e-20
    assert abs(dadn[1] - 1.158751653851105e-6) < 1e-18


def test_ligne_illisible_refusee(tmp_path):
    p = tmp_path / "mauvais.csv"
    p.write_text("dK,dadN\n1;2;3\n", encoding="utf-8")
    with pytest.raises(ValueError):
        lire_points(p)


def test_point_aberrant_detecte():
    dk = np.array([10.0, 12.0, 14.0, 16.0, 18.0, 20.0])
    dadn = 2e-11 * dk ** 3.0
    dadn[2] *= 10.0                                    # un chiffre en trop sur un point
    c, m, _ = ajuster(dk, dadn)
    i, facteur = plus_grand_ecart(dk, dadn, c, m)
    assert i == 2 and facteur > 3.0