# Hypothèses, règles et limites

## Règle de K officiel (fixée le 13/11/2026, appliquée à tous les calculs)
K officiel = moyenne, sur les contours 3 à 10, de sqrt(J · E'), avec E' = E / (1 − nu²).
Le contour 1 est écarté (peu précis). On rapporte aussi la dispersion de J (contours 3 à 10) et K2/K1.

## Modèle
- 2D, déformations planes (CPE), élasticité linéaire, petites déformations (Nlgeom off).
- Matériau : acier, E = 210 000 MPa, nu = 0,3.
- Épaisseur du modèle = 1 mm ; charge appliquée = P/B = 10 000 N / 25 mm = 400 N/mm.
  K dépend de P/B : 10 000 N sur 1 mm donnerait un K 25 fois trop grand.
- Repère : origine sur la ligne de chargement ; face avant à x = −12,5 mm ; trous de rayon 6,25 mm
  centrés en (0 ; ±13,75) ; fissure le long de y = 0 de la face avant à x = a.
- L'entaille mécanique est modélisée comme une fissure de largeur nulle (seam) jusqu'à la face avant.
- Trous : couplage cinématique (U1, U2) sur le bord. Il rigidifie le bord du trou ; effet attendu faible
  sur K (trou à 37 mm de la pointe), à confirmer par une étude de sensibilité.
- Éléments : CPE8R (quadrilatères) et CPE6 (triangles). Jamais CPE6M (mélange refusé par Abaqus), jamais CPS.
- Pointe : le script impose des nœuds milieux à 0,5 (sans singularité). Le modèle manuel a laissé la valeur
  par défaut de CAE, non vérifiée : le test C (2ᵉ valeur ≈ moitié de la 3ᵉ) le dira. Si le manuel est à 0,25,
  le script passera à 0,25 pour garder la non-régression.

## Maillage
- Disque de pointe de rayon 6 mm, 4 quarts, 10 couches radiales (une couche = un contour),
  biais radial vers la pointe (ratio 4 pour le calcul de référence), 2 éléments par arc de 90°.
- Zone grossière : taille 5 mm.
- Limite Learning Edition : 1 000 nœuds. Calcul de référence : 797 nœuds.

## Critères de validation du script (non-régression)
Le script doit reproduire le calcul manuel pour a/W = 0,5, biais 4 :
- types d'éléments : CPE8R et CPE6 uniquement ;
- nombre de nœuds : 797 ± 5 % ;
- K officiel : 541,9 MPa√mm à 0,5 % près (idéalement 0,1 %) ;
- K2/K1 du même ordre que le calcul manuel (quelques %).

## Contraintes résiduelles (bonus)
- Méthode : pression sur les lèvres de la fissure (superposition), profil auto-équilibré
  sigma(xi) = sigma0 (1 − 6 xi + 6 xi²), xi = x/W de 0 à 1 (force et moment nuls sur la section).
  Profil hypothétique, pas une mesure.
- K_res est signé (J = K²/E' perd le signe : le signe vient du signe du chargement).
- Superposition : K_res s'ajoute à K_max et à K_min ; DK inchangé tant que la fissure reste ouverte,
  mais R_eff change. D'où la loi de Walker (Paris pur ne verrait aucun effet).
- Si K_min + K_res < 0 : fermeture simplifiée (K_min = 0).

## Propagation
- Loi de Paris : da/dN = C (DK)^m ; loi de Walker : da/dN = C [K_max (1 − R)^gamma]^m.
- C, m, gamma de params.py : valeurs illustratives, à remplacer par une source citée.
- C et m sont corrélés : varier m seul à C fixé exagère l'effet sur N.
- Zone de propagation stable seulement : ni seuil DK_th, ni rupture finale.
- À contrôler : K_max < K_Ic sur tout l'intervalle de a (K_Ic à renseigner dans params.py).

## Limites
- 2D, pas d'effet de bord d'épaisseur ; pas de plasticité en pointe ; pas de fermeture de fissure réelle.
- Maillage libre non symétrique : K2 non nul.
- Deux éléments sur 240 sont signalés « distorted » par Abaqus (angles isoparamétriques hors des limites
  suggérées ou qualité de triangle) : avertissement, pas une erreur ; ils sont dans l'ensemble
  WarnElemDistorted. Leur effet sur J est jugé faible (loin de la pointe), à confirmer par une étude
  de sensibilité sur le maillage des trous.
