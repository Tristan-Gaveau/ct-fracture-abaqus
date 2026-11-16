# -*- coding: utf-8 -*-
"""Paramètres uniques du projet ct-fracture-abaqus (unités : mm, N, MPa).

Tous les autres scripts importent ces valeurs : ne les réécris nulle part ailleurs.
"""
import math

# --- Matériau (acier, élasticité linéaire) ---
E = 210000.0
NU = 0.3
E_PRIME = E / (1.0 - NU ** 2)          # déformations planes (MPa)

# --- Éprouvette CT (ASTM E399) ---
W = 50.0
B_REEL = 25.0                           # épaisseur réelle, pour la formule analytique
P_REEL = 10000.0                        # charge réelle (N)
X_FACE_AVANT = -0.25 * W                # -12,5 mm (la ligne de chargement est en x = 0)
X_FACE_ARRIERE = W
HAUTEUR = 1.2 * W                       # 60 mm, de y = -30 à y = +30
Y_TROU = 0.275 * W                      # 13,75 mm : centres des trous en (0 ; +/-Y_TROU)
R_TROU = 0.125 * W                      # 6,25 mm (diamètre 0,25 W)

# --- Modèle 2D en déformations planes ---
B_MODELE = 1.0                          # épaisseur du modèle (mm)
P_PAR_MM = P_REEL / B_REEL              # 400 N par mm d'épaisseur

# --- Maillage ---
TAILLE_GLOBALE = 5.0                    # mm, zone grossière
RAYON_DISQUE = 6.0                    # mm, disque autour de la pointe
N_COUCHES = 10                          # couches radiales = nombre de contours
N_ARC = 2                               # éléments par arc de 90 degrés
RATIO_BIAIS = 4.0                       # plus grand élément / plus petit, vers la pointe

# --- Calcul de J et règle de K officiel ---
N_CONTOURS = 10
PREMIER_CONTOUR_RETENU = 3              # K officiel = moyenne des contours 3 à 10
A_SUR_W_REF = 0.5

# --- Valeurs du calcul manuel validé (test de non-régression) ---
K_REF_MANUEL = 541.9                    # MPa*sqrt(mm), moyenne des contours 3 à 10
NOEUDS_REF_MANUEL = 797
TOL_NOEUDS = 0.05                       # 5 %
TOL_K = 0.005                           # 0,5 % (idéalement 0,1 %)

MMSQRT_VERS_MSQRT = 1.0 / math.sqrt(1000.0)

# --- Propagation (paris.py) ---
# C et m : ajustés (scripts/ajuster_paris.py) sur la figure 2.3.1.4.9 de la MIL-HDBK-5J (300M, CT, R = 0,08 à 0,5).
C_PARIS = 3.121e-11                     # da/dN en m/cycle, DK en MPa*sqrt(m)
M_PARIS = 2.672
R_CHARGE = 0.1                          # P_min / P_max
GAMMA_WALKER = 0.5                      # exposant de Walker : NON SOURCÉ, traité comme paramètre (voir paris.py)
A_INITIAL_SUR_W = 0.40                  # début de l'intégration : K(a) FE à +/-1 % de l'ASTM à partir de a/W = 0,4
A_FINAL_SUR_W = 0.70                    # fin de l'intégration
K_IC = 62.6                # MPa√m, NASA TP-1288 Table I : 1144 K / 589 K, sigma_y = 1624 MPa
K_IC_PLAGE = (62.6, 86.8)  # lignes de la table proches de Fty 230 / Ftu 280 ksi