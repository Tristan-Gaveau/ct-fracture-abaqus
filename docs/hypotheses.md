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
- Trous : couplage cinématique (U1, U2) sur le bord. Il rigidifie le bord du trou. Effet sur K non vérifié :
  hypothèse possible pour l'écart aux petites fissures (voir plus bas), à tester avec un couplage distribué.
- Éléments : CPE8R (quadrilatères) et CPE6 (triangles). Jamais CPE6M (mélange refusé par Abaqus), jamais CPS.
- Pointe : nœuds milieux à 0,5 (sans singularité), vérifié sur le maillage du script (nœuds au-dessus de la
  pointe : 0 ; 0,136 ; 0,273 ; 0,432 mm…). Le modèle manuel n'a pas été vérifié sur ce point.

## Maillage
- Disque de pointe de rayon 6 mm, 4 quarts, 10 couches radiales (une couche = un contour),
  biais radial vers la pointe (ratio 4 pour le calcul de référence), 2 éléments par arc de 90°.
- Zone grossière : taille 5 mm.
- Limite Learning Edition : 1 000 nœuds. Calcul manuel : 797 nœuds. Calcul du script : 817 nœuds
  (819 avec les 2 points de référence).

## Validation du script (non-régression)
- Comparaison avec le calcul manuel (a/W = 0,5, biais 4) : K +0,44 % (544,3 contre 541,9 MPa√mm),
  nœuds +2,5 % : critères de 0,5 % et de 5 % satisfaits. Types d'éléments : CPE8R et CPE6 uniquement.
- Le script est plus régulier que le calcul manuel : dispersion de J 0,2 % contre 2,6 %, K2/K1 0,0 % contre
  2,6 %. Le manuel avait un sommet en trop sur un arc du disque et un maillage moins régulier.
- La référence de non-régression devient donc le calcul du script : K = 544,3 MPa√mm (17,21 MPa√m), 817 nœuds.

## Convergence de maillage
- Critère énoncé avant le lancement de convergence.py (13/11/2026) : la variation de K entre deux maillages
  successifs doit être inférieure à 0,2 %, pour les deux derniers pas du raffinement. Variable raffinée :
  taille du premier élément à la pointe (ratios de biais 4, 10, 20, 40 ; 10 couches fixes ; 819 nœuds).
- Résultat : variations de +0,044 %, +0,010 % et +0,010 % ; K converge vers 17,22 MPa√m, soit −0,33 % par
  rapport à l'ASTM. Critère atteint.
- Limite : les autres paramètres (2 éléments par arc, taille globale 5 mm, maillage des trous, couplage
  cinématique) ne sont pas explorés. L'écart restant de −0,33 % ne vient pas du maillage à la pointe.

## K en fonction de la longueur de fissure et plage de propagation
- Écart à l'ASTM inférieur à 1 % de a/W = 0,4 à 0,7. À a/W = 0,3 et 0,35, K éléments finis dépasse l'ASTM de
  +4,0 % et +2,1 %. Qualité du calcul inchangée (dispersion de J 0,23 à 0,31 %, K2/K1 de 0 à 0,04 %).
- Hypothèse (non vérifiée) : le couplage cinématique, dont l'effet est plus fort quand la pointe est proche
  des trous.
- Décision prise APRÈS avoir vu l'écart : la propagation est intégrée de a/W = 0,4 à 0,7 (20 à 35 mm).
  Effet sur la durée de vie (C et m illustratifs) : N éléments finis / N ASTM = −3,9 % en intégrant dès 15 mm,
  +0,3 % dès 20 mm.
- Lecture du .dat : au-dessus de K = 1000 MPa√mm, Abaqus écrit K1 sans décimales (« 1210. ») ; le lecteur
  l'accepte (test dédié).

## Contraintes résiduelles (bonus)
- Méthode : superposition. K_res est calculé dans un calcul séparé, sans aucune charge externe, avec une
  pression sur les lèvres de la fissure.
- Pièce libre : pas de couplages (trous libres), deux appuis seulement contre le mouvement de corps rigide
  (coin arrière bas : U1 et U2 ; coin avant bas : U2), réactions attendues nulles. K_res correspond donc à la
  pièce sans goupilles dans les trous.
- Profil hypothétique, pas une mesure : sigma_res(u) = sigma0 (1 − 6u + 6u²), u de 0 à 1 entre la face avant
  (x = −12,5 mm) et la face arrière (x = 50 mm) ; force et moment nuls sur la section y = 0.
  Amplitude sigma0 = 100 MPa : valeur de départ, à justifier.
- Signe : p = +sigma_res. Comme une pression de fluide dans une fissure, une pression positive OUVRE la
  fissure dans Abaqus. Premier essai le 13/11/2026 avec p = −sigma_res : K1 négatif pour une contrainte
  résiduelle en traction ; corrigé.
- Test de méthode (pression uniforme, a/W = 0,5) : linéarité (sigma0 = 200 donne 2,00 fois le K1 de
  sigma0 = 100) et antisymétrie (±sigma0 donne ±K1) vérifiées ; dispersion de J 0,3 %.
- K_res est SIGNÉ : K1 du tableau des facteurs d'intensité (moyenne des contours 3 à 10), car J = K²/E' perd
  le signe. K(a) du chargement vient de J ; les deux estimateurs diffèrent de quelques dixièmes de % :
  effet négligeable devant l'incertitude sur sigma0.
- Limite : K2/K1 = ±3 % en mode K_res (0,0 % en mode appliqué), cause non établie.
- Superposition : K_res s'ajoute à K_max et à K_min ; DK inchangé tant que la fissure reste ouverte, mais
  R_eff change. D'où la loi de Walker (Paris pur ne verrait aucun effet).
- Si K_min + K_res < 0 : fermeture simplifiée (K_min = 0).

## Propagation
- Loi de Paris : da/dN = C (DK)^m ; loi de Walker : da/dN = C [K_max (1 − R)^gamma]^m.
- C, m, gamma de params.py : valeurs illustratives, à remplacer par une source citée.
- C et m : ajustés sur la figure 2.3.1.4.9 de la MIL-HDBK-5J (scripts/ajuster_paris.py, 15 points numérisés avec
  WebPlotDigitizer, ΔK de 10 à 29 ksi√po) : C = 3,121e-11 (m/cycle, MPa√m), m = 2,672, dispersion autour de
  la droite d'un facteur 1,07. La pente locale baisse de 2,69 (10-18 ksi√po) à 2,28 (18-29) : la loi à un
  seul exposant est une approximation. La bande regroupe R = 0,08 à 0,5.
- γ (Walker) : aucune source ; étudié de 0,5 à 1. Pour γ = 1, une contrainte résiduelle en traction n'a
  aucun effet (DK inchangé) ; une compression ralentit quand même la fissure par fermeture simplifiée.
- N varie d'un facteur 15 entre m = 2,5 et m = 3,5 (C = 1e-11) : DK est élevé à la puissance m.
- Zone de propagation stable seulement : ni seuil DK_th, ni rupture finale.
- À contrôler : K_max < K_Ic sur tout l'intervalle de a (K_Ic à renseigner dans params.py).

## Limites
- 2D, pas d'effet de bord d'épaisseur ; pas de plasticité en pointe ; pas de fermeture de fissure réelle.
- Le calcul manuel avait un K2/K1 de 2,6 % (maillage libre non symétrique) ; le script donne 0,0 % en mode
  appliqué.
- Deux éléments sur 240 du calcul manuel sont signalés « distorted » par Abaqus (ensemble WarnElemDistorted) :
  avertissement, pas une erreur. À vérifier pour le maillage du script.
- Learning Edition : 1 000 nœuds maximum.