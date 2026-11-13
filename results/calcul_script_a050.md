# Calcul du script : K, éprouvette CT, a/W = 0,5 (modèle construit par build_ct.py)

## Conditions
- Mêmes conditions que le calcul manuel (voir premier_calcul.md), modèle construit par scripts/build_ct.py
- Maillage : CPE8R (224) + CPE6 (24), 817 nœuds, 248 éléments
- Disque de pointe : 4 quarts, 10 couches, biais 4 (1er élément 0,2725 mm), 2 éléments par arc
- Nœuds milieux à la moitié des côtés : sans singularité

## Résultats
- K officiel (moyenne des contours 3 à 10) : 544,3 MPa√mm = 17,21 MPa√m
- Référence ASTM E399 : 17,28 MPa√m ; écart : −0,38 %
- Dispersion de J (contours 3 à 10) : 0,2 %
- K2 / K1 : 0,0 %
- Écart avec le calcul manuel (541,9) : +0,44 %

## Remarques
- Le script est plus régulier que le calcul manuel (dispersion 0,2 % contre 2,6 %, K2 nul) : le manuel avait
  un sommet en trop sur un arc du disque et un maillage moins régulier.
- La référence de non-régression devient ce calcul (544,3 MPa√mm, 817 nœuds).
- Un seul maillage : la convergence reste à faire.
- Somme des réactions RF2 (attendu −400 N) : pas encore contrôlée.