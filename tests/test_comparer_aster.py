# -*- coding: utf-8 -*-
"""Tests de scripts/aster/comparer.py (lecture des tables Code_Aster, moyenne, dispersion)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts", "aster"))
import comparer  # noqa: E402

ENTETE = "couronne,r_inf,r_sup,G,K1,G_IRWIN,K1_depuis_G\n"


def _ecrire(tmp_path, k_list):
    chemin = tmp_path / "resultats.csv"
    lignes = [ENTETE] + ["%d,0,1,1,%s,1,%s\n" % (i, k, k) for i, k in enumerate(k_list, start=1)]
    chemin.write_text("".join(lignes), encoding="utf-8")
    return str(chemin)


def test_la_premiere_couronne_est_ecartee(tmp_path):
    k, disp, n = comparer.resumer(comparer.lire_couronnes(_ecrire(tmp_path, [999.0, 100.0, 100.0])))
    assert n == 2
    assert abs(k - 100.0 / 1000 ** 0.5) < 1e-12
    assert disp == 0.0


def test_dispersion_en_pourcent(tmp_path):
    _, disp, _ = comparer.resumer(comparer.lire_couronnes(_ecrire(tmp_path, [0.0, 99.0, 101.0])))
    assert abs(disp - 2.0) < 1e-9


def test_conversion_mmsqrt_vers_msqrt(tmp_path):
    k, _, _ = comparer.resumer(comparer.lire_couronnes(_ecrire(tmp_path, [0.0, 544.3, 544.3])))
    assert abs(k - 17.2123) < 1e-3
