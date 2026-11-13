from pathlib import Path

import numpy as np
import pytest

import params as P
from run_and_read import (compter_noeuds_elements, indicateurs_qualite, k_depuis_j,
                          k_officiel, lire_dat)

DAT_EXEMPLE = (Path(__file__).parent / "data" / "dat_exemple.txt").read_text(encoding="utf-8")


@pytest.fixture
def dat(tmp_path):
    p = tmp_path / "ct_a050.dat"
    p.write_text(DAT_EXEMPLE, encoding="utf-8")
    return p


def test_lecture_j(dat):
    J, K1, K2 = lire_dat(dat)
    assert list(J) == [1.208, 1.238, 1.255, 1.261, 1.267, 1.271, 1.275, 1.279, 1.288, 1.284]


def test_lecture_k1_k2(dat):
    J, K1, K2 = lire_dat(dat)
    assert len(K1) == 10 and len(K2) == 10
    assert K1[0] == 523.3 and K1[9] == 543.1
    assert K2[1] == 25.69 and K2[9] == 2.970


def test_k_officiel_premier_calcul(dat):
    J, _, _ = lire_dat(dat)
    k, _ = k_officiel(J)
    assert abs(k - 541.9) < 0.1


def test_k_en_msqrt(dat):
    J, _, _ = lire_dat(dat)
    k, _ = k_officiel(J)
    assert abs(k * P.MMSQRT_VERS_MSQRT - 17.14) < 0.01


def test_indicateurs_qualite(dat):
    J, K1, K2 = lire_dat(dat)
    dispersion, k2k1 = indicateurs_qualite(J, K1, K2)
    assert 2.0 < dispersion < 3.0
    assert 2.0 < k2k1 < 4.0


def test_titre_introuvable(tmp_path):
    p = tmp_path / "vide.dat"
    p.write_text("rien d'utile ici", encoding="utf-8")
    with pytest.raises(ValueError):
        lire_dat(p)


def test_j_negatif_refuse():
    with pytest.raises(ValueError):
        k_depuis_j(np.array([1.2, -0.1]))


def test_compter_noeuds_elements(tmp_path):
    inp = tmp_path / "m.inp"
    inp.write_text(
        "*Heading\n** commentaire\n*Node\n1, 0., 0.\n2, 1., 0.\n3, 1., 1.\n"
        "*Element, type=CPE8R\n1, 1, 2, 3, 1, 2, 3, 1, 2\n*Nset, nset=A\n1,\n",
        encoding="utf-8",
    )
    assert compter_noeuds_elements(inp) == (3, 1)

DAT_K_GRAND = """
                          J - I N T E G R A L     E S T I M A T E S
 J_OUT_CRACK
        -8-                     6.380        6.390        6.400        6.410        6.420
                                6.425        6.430        6.435        6.440        6.445

   LABELS REFERENCED IN THE ABOVE TABLE

                          K   F A C T O R     E S T I M A T E S
 K_OUT_CRACK
        -8-        K1:          1217.        1219.        1221.        1222.        1223.
                   K2:          6.348        25.69        21.26        18.67        16.68
                   K1:          1.224E+03    1225         1226.        1227.        1228.5
                   K2:          15.07        13.73        12.71        11.42        2.970

   LABELS REFERENCED IN THE ABOVE TABLE
"""


def test_k1_superieur_a_1000_formats_sans_decimales(tmp_path):
    p = tmp_path / "grand.dat"
    p.write_text(DAT_K_GRAND, encoding="utf-8")
    J, K1, K2 = lire_dat(p)
    assert list(K1) == [1217.0, 1219.0, 1221.0, 1222.0, 1223.0, 1224.0, 1225.0, 1226.0, 1227.0, 1228.5]
    assert len(K2) == 10 and len(J) == 10
