# -*- coding: utf-8 -*-
"""Prépare toutes les études Code_Aster d'un coup.

  python scripts/aster/preparer_serie.py --serie          # 9 longueurs de fissure, a/W = 0,30 à 0,70
  python scripts/aster/preparer_serie.py --convergence    # 3 maillages de plus en plus fins, a/W = 0,50

Dossiers créés dans C:\\aster_calculs (cas_a030 ... cas_a070, conv_1 ... conv_3).
Lancement (« code_aster powershell ») :
  Get-ChildItem C:\\aster_calculs\\cas_a*, C:\\aster_calculs\\conv_* -Directory | ForEach-Object { cd $_.FullName; run_aster cas.export *> run.log }
"""
import argparse
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
from preparer_cas import preparer  # noqa: E402

ALPHAS = [0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70]
# (nom, éléments par quart d'arc, éléments radiaux, taille autour du disque en mm)
MAILLAGES = [("conv_1", 2, 10, 2.5), ("conv_2", 4, 14, 1.5), ("conv_3", 6, 20, 1.0)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--serie", action="store_true")
    ap.add_argument("--convergence", action="store_true")
    ap.add_argument("--dossier", default=r"C:\aster_calculs")
    a = ap.parse_args()
    if not (a.serie or a.convergence):
        ap.error("choisis --serie et/ou --convergence")
    if a.serie:
        for alpha in ALPHAS:
            preparer(alpha, a.dossier)
    if a.convergence:
        for nom, n_arc, n_couches, h in MAILLAGES:
            preparer(0.5, a.dossier, n_arc=n_arc, n_couches=n_couches, h_proche=h, nom=nom)


if __name__ == "__main__":
    main()
