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
