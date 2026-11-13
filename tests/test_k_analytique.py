import numpy as np
import pytest

from k_analytique import calc_k_analytique, f_astm_e399


def test_cas_reference():
    assert abs(f_astm_e399(0.5) - 9.66) < 0.01
    assert abs(calc_k_analytique(10000, 25, 50, 25) - 17.28) < 0.05


def test_proportionnel_a_P():
    k1 = calc_k_analytique(10000, 25, 50, 25)
    k2 = calc_k_analytique(20000, 25, 50, 25)
    assert np.isclose(k2, 2 * k1)


def test_k_croit_avec_a():
    k = calc_k_analytique(10000, 25, 50, np.linspace(15, 40, 20))
    assert np.all(np.diff(k) > 0)


def test_hors_domaine():
    with pytest.raises(ValueError):
        calc_k_analytique(10000, 25, 50, 5)   # a/W = 0,1
