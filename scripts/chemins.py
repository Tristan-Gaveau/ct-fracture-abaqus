# -*- coding: utf-8 -*-
"""Tous les chemins du projet, au même endroit.

Les calculs Abaqus se font HORS du dépôt (et hors OneDrive) : OneDrive peut verrouiller
les fichiers temporaires d'Abaqus. Pour changer le dossier : variable d'environnement
CT_CALCULS (exemple PowerShell : $env:CT_CALCULS = "D:\\abaqus_calculs").
"""
import os
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SCRIPTS = RACINE / "scripts"
RESULTATS = RACINE / "results"
RAW = RESULTATS / "raw"                 # .dat bruts gardés dans Git (petits fichiers texte)
FIGURES = RESULTATS / "figures"

_DEFAUT = Path(r"C:\abaqus_calculs") if os.name == "nt" else RACINE / "calculs"
CALCULS = Path(os.environ.get("CT_CALCULS", str(_DEFAUT)))
