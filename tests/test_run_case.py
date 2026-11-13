import json
import os
from pathlib import Path

import pytest

import chemins as C
import params as P
import run_case
from run_and_read import analyse_terminee

DAT = (Path(__file__).parent / "data" / "dat_exemple.txt").read_text(encoding="utf-8")


@pytest.fixture
def faux_abaqus(tmp_path, monkeypatch):
    """Remplace les appels à Abaqus par des fichiers factices (797 nœuds, calcul réussi)."""
    monkeypatch.setattr(C, "CALCULS", tmp_path / "calculs")
    monkeypatch.setattr(C, "RAW", tmp_path / "raw")
    monkeypatch.delenv("CT_MODE", raising=False)
    monkeypatch.delenv("CT_REPRENDRE", raising=False)
    appels = []

    def faux_run(cmd, cwd=None, check=True):
        appels.append(list(cmd))
        if "cae" in cmd:
            nom = json.load(open(cwd / "cas_en_cours.json"))["nom"]
            lignes = ["*Heading", "*Node"] + ["%d, 0., 0." % i for i in range(1, 798)] \
                + ["*Element, type=CPE8R"] + ["%d, 1,2,3,4,5,6,7,8" % i for i in range(1, 241)]
            (cwd / (nom + ".inp")).write_text("\n".join(lignes), encoding="utf-8")
        else:
            nom = [c for c in cmd if str(c).startswith("job=")][0][4:]
            (cwd / (nom + ".dat")).write_text(DAT, encoding="utf-8")
            (cwd / (nom + ".sta")).write_text(" THE ANALYSIS HAS COMPLETED SUCCESSFULLY\n", encoding="utf-8")

    monkeypatch.setattr(run_case.subprocess, "run", faux_run)
    return appels


def test_ecrire_cas(tmp_path):
    chemin = run_case.ecrire_cas(0.5, 4.0, "ct_a050", tmp_path)
    cas = json.load(open(chemin))
    assert cas["a_sur_w"] == 0.5 and cas["ratio_biais"] == 4.0 and cas["nom"] == "ct_a050"
    assert cas["dossier_scripts"] == str(C.SCRIPTS)
    assert cas["jusqu_a"] == 6


def test_ecrire_cas_jusqu_a(tmp_path):
    chemin = run_case.ecrire_cas(0.5, 4.0, "ct_a050", tmp_path, jusqu_a=2)
    assert json.load(open(chemin))["jusqu_a"] == 2


def test_cas_de_reference_non_regression(faux_abaqus):
    r = run_case.lancer_cas(0.5, 4.0, "ct_a050")
    assert r["n_noeuds"] == 797 and r["n_elems"] == 240
    assert abs(r["k_mmsqrt"] - 541.9) < 0.1
    ok, _, _ = run_case.verifier_non_regression(r)
    assert ok
    assert (C.RAW / "ct_a050.dat").exists()


def test_le_solveur_est_lance_apres_la_construction(faux_abaqus):
    run_case.lancer_cas(0.5, 4.0, "ct_a050")
    assert "cae" in faux_abaqus[0]
    assert "job=ct_a050" in faux_abaqus[1]


def test_reprendre_saute_les_cas_deja_calcules(faux_abaqus, monkeypatch):
    run_case.lancer_cas(0.5, 4.0, "ct_a050")
    n_appels = len(faux_abaqus)
    monkeypatch.setenv("CT_REPRENDRE", "1")
    run_case.lancer_cas(0.5, 4.0, "ct_a050")
    assert len(faux_abaqus) == n_appels


def test_calcul_non_termine_leve_une_erreur(faux_abaqus, monkeypatch):
    def run_ko(cmd, cwd=None, check=True):
        if "cae" in cmd:
            nom = json.load(open(cwd / "cas_en_cours.json"))["nom"]
            (cwd / (nom + ".inp")).write_text("*Node\n1, 0., 0.\n", encoding="utf-8")
        else:
            nom = [c for c in cmd if str(c).startswith("job=")][0][4:]
            (cwd / (nom + ".sta")).write_text(" THE ANALYSIS HAS NOT BEEN COMPLETED\n", encoding="utf-8")
    monkeypatch.setattr(run_case.subprocess, "run", run_ko)
    with pytest.raises(RuntimeError):
        run_case.lancer_cas(0.5, 4.0, "ct_ko")


def test_trop_de_noeuds_refuse(faux_abaqus, monkeypatch):
    def run_gros(cmd, cwd=None, check=True):
        nom = json.load(open(cwd / "cas_en_cours.json"))["nom"]
        lignes = ["*Node"] + ["%d, 0., 0." % i for i in range(1, 1100)]
        (cwd / (nom + ".inp")).write_text("\n".join(lignes), encoding="utf-8")
    monkeypatch.setattr(run_case.subprocess, "run", run_gros)
    with pytest.raises(RuntimeError, match="1000"):
        run_case.lancer_cas(0.5, 4.0, "ct_gros")


def test_options_de_ligne_de_commande(monkeypatch):
    monkeypatch.delenv("CT_MODE", raising=False)
    reste = run_case.configurer_mode(["0.5", "4", "nom", "--manuel"])
    assert reste == ["0.5", "4", "nom"]
    assert os.environ["CT_MODE"] == "manuel"
    monkeypatch.delenv("CT_MODE")


def test_chemins_coherents():
    assert C.SCRIPTS.name == "scripts" and C.RESULTATS.name == "results"
    assert C.RAW.parent == C.RESULTATS and C.FIGURES.parent == C.RESULTATS

def test_ecrire_cas_mode_k_res(tmp_path):
    chemin = run_case.ecrire_cas(0.5, 4.0, "ct_kr050", tmp_path, mode="k_res", sigma0=100.0, profil="uniforme")
    cas = json.load(open(chemin))
    assert cas["mode"] == "k_res" and cas["sigma0"] == 100.0 and cas["profil"] == "uniforme"


def test_lancer_cas_renvoie_k1_signe(faux_abaqus):
    r = run_case.lancer_cas(0.5, 4.0, "ct_kr050", mode="k_res", sigma0=100.0, profil="equilibre")
    assert r["mode"] == "k_res" and abs(r["k1_mmsqrt"] - 537.35) < 0.01