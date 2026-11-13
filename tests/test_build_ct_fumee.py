"""Test de fumée : exécute build_ct.py avec un FAUX Abaqus.

Il ne prouve pas que l'API d'Abaqus est bien utilisée (seul CAE peut le dire). Il attrape les fautes
de Python : noms mal écrits, variables oubliées, enchaînement des blocs, lecture du JSON.
"""
import json
import runpy
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import chemins as C

NOMS_CONSTANTES = (
    "TWO_D_PLANAR DEFORMABLE_BODY YAXIS XYPLANE SIDE1 RIGHT OFF ON MIDDLE_SURFACE FROM_SECTION CARTESIAN "
    "Q_VECTORS DEFAULT EXCLUDE K_FACTORS MTS WHOLE_SURFACE KINEMATIC UNIFORM UNSET SINGLE FINER QUAD QUAD_DOMINATED SWEEP "
    "STANDARD CPE8R CPE6 ANALYSIS PERCENTAGE ODB SIDE2 J_INTEGRAL"
).split()


@pytest.fixture
def faux_abaqus(tmp_path, monkeypatch):
    mdb = MagicMock()
    modele = mdb.models.__getitem__.return_value
    modele.Part.return_value.faces.__len__.return_value = 6
    instance = modele.rootAssembly.instances.__getitem__.return_value
    instance.edges.findAt.return_value.__len__.return_value = 2
    instance.edges.getByBoundingBox.return_value.__len__.return_value = 4
    modele.rootAssembly.instances.__getitem__.return_value = instance

    abaqus = types.ModuleType("abaqus")
    abaqus.mdb = mdb
    abaqus.Mdb = MagicMock()
    constantes = types.ModuleType("abaqusConstants")
    for nom in NOMS_CONSTANTES:
        setattr(constantes, nom, nom)
    constantes.__all__ = list(NOMS_CONSTANTES)
    maillage = types.ModuleType("mesh")
    maillage.ElemType = MagicMock()
    maillage.__all__ = ["ElemType"]
    for nom in ("part material section assembly step interaction load job sketch").split():
        vide = types.ModuleType(nom)
        vide.__all__ = []
        monkeypatch.setitem(sys.modules, nom, vide)
    regions = types.ModuleType("regionToolset")
    regions.Region = MagicMock()
    for nom, module in (("abaqus", abaqus), ("abaqusConstants", constantes), ("mesh", maillage),
                        ("regionToolset", regions)):
        monkeypatch.setitem(sys.modules, nom, module)
    monkeypatch.chdir(tmp_path)
    return mdb


def ecrire_json(jusqu_a, a_sur_w=0.5):
    json.dump({"a_sur_w": a_sur_w, "ratio_biais": 4.0, "nom": "ct_test",
               "dossier_scripts": str(C.SCRIPTS), "jusqu_a": jusqu_a}, open("cas_en_cours.json", "w"))


def test_les_six_blocs_s_enchainent(faux_abaqus, capsys):
    ecrire_json(6)
    runpy.run_path(str(C.SCRIPTS / "build_ct.py"), run_name="__main__")
    sortie = capsys.readouterr().out
    assert "ETAPE 6 OK" in sortie and "ECRIT : ct_test.inp" in sortie


def test_jusqu_a_limite_les_blocs(faux_abaqus, capsys):
    ecrire_json(2)
    runpy.run_path(str(C.SCRIPTS / "build_ct.py"), run_name="__main__")
    sortie = capsys.readouterr().out
    assert "ETAPE 2 OK" in sortie and "ETAPE 3" not in sortie


def test_toutes_les_longueurs_de_fissure_passent(faux_abaqus, capsys):
    for a_sur_w in (0.3, 0.4, 0.5, 0.6, 0.7):
        ecrire_json(6, a_sur_w)
        runpy.run_path(str(C.SCRIPTS / "build_ct.py"), run_name="__main__")
    assert capsys.readouterr().out.count("ETAPE 6 OK") == 5


def test_json_absent_message_clair(faux_abaqus):
    with pytest.raises(RuntimeError, match="cas_en_cours.json"):
        runpy.run_path(str(C.SCRIPTS / "build_ct.py"), run_name="__main__")


def test_fissure_trop_longue_refusee_avant_abaqus(faux_abaqus):
    ecrire_json(1, a_sur_w=0.9)
    with pytest.raises(ValueError, match="face arrière"):
        runpy.run_path(str(C.SCRIPTS / "build_ct.py"), run_name="__main__")
