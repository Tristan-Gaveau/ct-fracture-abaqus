# -*- coding: utf-8 -*-
"""Lance UN calcul complet : construction du modèle, solveur, lecture des résultats.

Usage (depuis la racine du dépôt, avec le Python normal) :
    python scripts/run_case.py 0.5 4 ct_a050              # mode automatique
    python scripts/run_case.py 0.5 4 ct_a050 --manuel     # tu lances build_ct.py dans CAE
    python scripts/run_case.py 0.5 4 ct_a050 --reprendre  # saute les cas déjà calculés
    python scripts/run_case.py 0.5 4 ct_a050 --cas-seulement --jusqu-a=2   # écrit seulement le JSON
    python scripts/run_case.py 0.5 4 ct_kr_test --mode=k_res --sigma0=100 --profil=uniforme   # K_res

Deux façons de construire le modèle :
  auto    : abaqus cae noGUI=build_ct.py (si ta Learning Edition l'accepte)
  manuel  : tu ouvres CAE, File > Set Work Directory = dossier des calculs,
            File > Run Script > build_ct.py ; le reste (solveur, lecture) reste automatique.
Dans les deux cas, build_ct.py lit ses paramètres dans cas_en_cours.json (écrit ici).
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import chemins as C
import params as P
from run_and_read import (analyse_terminee, compter_noeuds_elements, indicateurs_qualite,
                          k1_officiel, k_officiel, lire_dat)

NOM_FICHIER_CAS = "cas_en_cours.json"
EXTENSIONS_A_NETTOYER = (".sta", ".dat", ".msg", ".odb", ".lck", ".prt", ".sim", ".com")


def configurer_mode(argv):
    """Lit --manuel / --reprendre, les range dans l'environnement, retourne les autres arguments."""
    if "--manuel" in argv:
        os.environ["CT_MODE"] = "manuel"
    if "--reprendre" in argv:
        os.environ["CT_REPRENDRE"] = "1"
    return [a for a in argv if not a.startswith("--")]


def ecrire_cas(a_sur_w, ratio_biais, nom, dossier=None, jusqu_a=6, mode="applique", sigma0=0.0, profil="equilibre"):
    """Écrit cas_en_cours.json, lu par build_ct.py. jusqu_a : nombre de blocs à exécuter (1 à 6)."""
    dossier = Path(dossier or C.CALCULS)
    dossier.mkdir(parents=True, exist_ok=True)
    chemin = dossier / NOM_FICHIER_CAS
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump({"a_sur_w": a_sur_w, "ratio_biais": ratio_biais, "nom": nom,
                   "dossier_scripts": str(C.SCRIPTS), "jusqu_a": jusqu_a,
                   "mode": mode, "sigma0": sigma0, "profil": profil}, f, indent=2)
    return chemin


def _construire_auto(dossier, nom):
    abaqus = shutil.which("abaqus") or "abaqus"
    subprocess.run([abaqus, "cae", "noGUI=" + str(C.SCRIPTS / "build_ct.py")],
                   cwd=dossier, check=True)


def _construire_manuel(dossier, nom):
    print("\n--- MODE MANUEL : cas %s ---" % nom)
    print("1. Dans Abaqus/CAE : File > Set Work Directory > %s" % dossier)
    print("2. File > Run Script > %s" % (C.SCRIPTS / "build_ct.py"))
    print("3. Attends l'affichage de la ligne NOEUDS ... (le fichier %s.inp est alors écrit)" % nom)
    input("Appuie sur Entrée quand c'est fait... ")


def _lancer_solveur(dossier, nom):
    for ext in EXTENSIONS_A_NETTOYER:           # évite de relire un résultat périmé
        (dossier / (nom + ext)).unlink(missing_ok=True)
    abaqus = shutil.which("abaqus") or "abaqus"
    subprocess.run([abaqus, "job=" + nom, "interactive", "ask_delete=OFF"],
                   cwd=dossier, check=True)


def lancer_cas(a_sur_w, ratio_biais, nom, mode="applique", sigma0=0.0, profil="equilibre"):
    """Construit, calcule et lit un cas. Retourne un dictionnaire de résultats.

    mode "applique" : charge de 400 N/mm sur les trous (K du chargement) ;
    mode "k_res" : aucune charge externe, pression sur les lèvres (K_res d'une contrainte résiduelle).
    """
    dossier = Path(C.CALCULS)
    dossier.mkdir(parents=True, exist_ok=True)
    inp, dat, sta = (dossier / (nom + ext) for ext in (".inp", ".dat", ".sta"))

    deja_calcule = (os.environ.get("CT_REPRENDRE") == "1"
                    and inp.exists() and dat.exists() and analyse_terminee(sta))
    if not deja_calcule:
        ecrire_cas(a_sur_w, ratio_biais, nom, dossier, mode=mode, sigma0=sigma0, profil=profil)
        inp.unlink(missing_ok=True)             # on veut un .inp neuf, pas un ancien
        if os.environ.get("CT_MODE", "auto") == "manuel":
            _construire_manuel(dossier, nom)
        else:
            _construire_auto(dossier, nom)
        if not inp.exists():
            raise RuntimeError("%s n'a pas été créé : build_ct.py a échoué" % inp)

        n_noeuds, _ = compter_noeuds_elements(inp)
        if n_noeuds > 1000:
            raise RuntimeError("%d nœuds : au-dessus de la limite Learning Edition (1000)" % n_noeuds)

        _lancer_solveur(dossier, nom)
        if not analyse_terminee(sta):
            raise RuntimeError("Calcul %s non terminé normalement : lis %s.msg" % (nom, nom))

    n_noeuds, n_elems = compter_noeuds_elements(inp)
    J, K1, K2 = lire_dat(dat)
    k, _ = k_officiel(J)
    k1 = k1_officiel(K1)
    dispersion, k2_sur_k1 = indicateurs_qualite(J, K1, K2)

    C.RAW.mkdir(parents=True, exist_ok=True)
    shutil.copy(dat, C.RAW / (nom + ".dat"))     # trace brute, versionnée dans Git
    return {
        "nom": nom, "a_sur_w": a_sur_w, "ratio_biais": ratio_biais,
        "n_noeuds": n_noeuds, "n_elems": n_elems,
        "k_mmsqrt": k, "k_msqrt": k * P.MMSQRT_VERS_MSQRT,
        "k1_mmsqrt": k1, "k1_msqrt": k1 * P.MMSQRT_VERS_MSQRT,
        "mode": mode, "sigma0": sigma0, "profil": profil,
        "dispersion_j_pct": dispersion, "k2_sur_k1_pct": k2_sur_k1,
    }


def verifier_non_regression(r):
    """Compare le cas de référence (a/W = 0,5, biais 4) au calcul manuel validé."""
    ecart_k = abs(r["k_mmsqrt"] - P.K_REF_MANUEL) / P.K_REF_MANUEL
    ecart_n = abs(r["n_noeuds"] - P.NOEUDS_REF_MANUEL) / P.NOEUDS_REF_MANUEL
    ok = ecart_k <= P.TOL_K and ecart_n <= P.TOL_NOEUDS
    return ok, ecart_k, ecart_n


if __name__ == "__main__":
    options = sys.argv[1:]
    args = configurer_mode(options)
    a_sur_w, ratio, nom = float(args[0]), float(args[1]), args[2]
    mode, sigma0, profil = "applique", 0.0, "equilibre"
    for o in options:
        if o.startswith("--mode="):
            mode = o.split("=")[1]
        elif o.startswith("--sigma0="):
            sigma0 = float(o.split("=")[1])
        elif o.startswith("--profil="):
            profil = o.split("=")[1]
    if "--cas-seulement" in options:          # mise au point de build_ct.py bloc par bloc
        jusqu_a = 6
        for o in options:
            if o.startswith("--jusqu-a="):
                jusqu_a = int(o.split("=")[1])
        print("Écrit :", ecrire_cas(a_sur_w, ratio, nom, jusqu_a=jusqu_a, mode=mode, sigma0=sigma0, profil=profil))
        sys.exit(0)
    r = lancer_cas(a_sur_w, ratio, nom, mode=mode, sigma0=sigma0, profil=profil)
    print("%d noeuds, %d elements" % (r["n_noeuds"], r["n_elems"]))
    print("K officiel = %.1f MPa*sqrt(mm) = %.3f MPa*sqrt(m)" % (r["k_mmsqrt"], r["k_msqrt"]))
    print("K1 signé = %.1f MPa*sqrt(mm) = %.3f MPa*sqrt(m)" % (r["k1_mmsqrt"], r["k1_msqrt"]))
    print("Dispersion J = %.1f %%, K2/K1 = %.1f %%" % (r["dispersion_j_pct"], r["k2_sur_k1_pct"]))
    if mode == "applique" and abs(a_sur_w - P.A_SUR_W_REF) < 1e-9 and abs(ratio - P.RATIO_BIAIS) < 1e-9:
        ok, ek, en = verifier_non_regression(r)
        print("NON-REGRESSION : %s (K ecart %.2f %%, noeuds ecart %.1f %%)"
              % ("OK" if ok else "ECHEC", 100 * ek, 100 * en))