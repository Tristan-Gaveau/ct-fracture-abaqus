# -*- coding: utf-8 -*-
"""Prépare un cas Code_Aster : maillage .med, fichier .comm et fichier .export dans un dossier de calcul.

Usage :  python scripts/aster/preparer_cas.py --a-sur-w 0.5 [--dossier C:/aster_calculs]
Puis, dans le « code_aster powershell » :  run_aster <dossier>\\cas_a050\\cas.export
"""
import argparse
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
sys.path.insert(0, os.path.join(ICI, ".."))
import params as P  # noqa: E402
from maillage_ct import construire  # noqa: E402


def preparer(a_sur_w, dossier, n_arc=P.N_ARC, n_couches=P.N_COUCHES, ratio=P.RATIO_BIAIS,
             h_global=P.TAILLE_GLOBALE, h_proche=2.5, quad=False, nom=None):
    nom = nom or "cas_a%03d" % round(a_sur_w * 100)
    wd = os.path.join(dossier, nom)
    os.makedirs(wd, exist_ok=True)
    med = os.path.join(wd, "ct.med")
    info = construire(a_sur_w, med, n_arc=n_arc, n_couches=n_couches, ratio=ratio,
                      h_global=h_global, h_proche=h_proche, quad=quad)

    with open(os.path.join(ICI, "cas_ct.comm"), encoding="utf-8") as f:
        comm = f.read()
    for jeton, valeur in (("@RAYON@", P.RAYON_DISQUE), ("@NCOUCHES@", n_couches),
                          ("@RATIO@", ratio), ("@A@", info["a"])):
        comm = comm.replace(jeton, repr(float(valeur)) if jeton != "@NCOUCHES@" else str(int(valeur)))
    with open(os.path.join(wd, "cas.comm"), "w", encoding="utf-8") as f:
        f.write(comm)

    export = "\n".join([
        "P actions make_etude",
        "P ncpus 1",
        "P memory_limit 2048",
        "P time_limit 900",
        "F comm %s D 1" % os.path.join(wd, "cas.comm"),
        "F mmed %s D 20" % med,
        "F mess %s R 6" % os.path.join(wd, "cas.mess"),
        "F libr %s R 30" % os.path.join(wd, "resultats.csv"),
        ""])
    chemin = os.path.join(wd, "cas.export")
    with open(chemin, "w", encoding="utf-8", newline="\n") as f:
        f.write(export)
    print("%d nœuds | a = %.2f mm | export : %s" % (info["noeuds"], info["a"], chemin))
    return chemin


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--a-sur-w", type=float, default=P.A_SUR_W_REF)
    ap.add_argument("--dossier", default=r"C:\aster_calculs")
    ap.add_argument("--n-arc", type=int, default=P.N_ARC)
    ap.add_argument("--n-couches", type=int, default=P.N_COUCHES)
    ap.add_argument("--ratio", type=float, default=P.RATIO_BIAIS)
    ap.add_argument("--h-proche", type=float, default=2.5)
    ap.add_argument("--quad", action="store_true")
    ap.add_argument("--nom")
    a = ap.parse_args()
    preparer(a.a_sur_w, a.dossier, a.n_arc, a.n_couches, a.ratio, h_proche=a.h_proche, quad=a.quad, nom=a.nom)
