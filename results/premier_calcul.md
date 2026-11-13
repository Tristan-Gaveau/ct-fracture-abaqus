# Premier calcul : K, éprouvette CT, a/W = 0,5 (modèle construit à la main dans CAE)

## Conditions
- Géométrie : W = 50 mm, a = 25 mm, modèle 2D d'épaisseur 1 mm, charge P/B = 400 N/mm
- Déformations planes, élasticité linéaire (E = 210 000 MPa, nu = 0,3), Nlgeom off
- Maillage : CPE8R + CPE6, 797 nœuds, 240 éléments
- Disque de pointe : rayon 6 mm, 10 couches, biais 4, 4 quarts, 2 éléments par arc
- Couplage cinématique sur les trous (U1, U2)

## Résultats (10 contours)
| Contour | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| J (N/mm) | 1,208 | 1,238 | 1,255 | 1,261 | 1,267 | 1,271 | 1,275 | 1,279 | 1,288 | 1,284 |

- K officiel (moyenne des contours 3 à 10 de sqrt(J·E')) : 541,9 MPa√mm = 17,14 MPa√m
- Référence ASTM E399 : 17,28 MPa√m
- Écart : −0,8 %
- Dispersion de J (contours 3 à 10) : 2,6 %
- K2 / K1 : 2,6 % (devrait être nul par symétrie ; maillage libre non symétrique)

## À vérifier
- Somme des réactions RF2 (attendu −400 N) : pas encore contrôlée
- Deux éléments « distorted » (2 sur 240, ensemble WarnElemDistorted) : avertissement d'Abaqus, pas une erreur ;
  position exacte à confirmer (Verify Mesh > Analysis Checks > Highlight)
