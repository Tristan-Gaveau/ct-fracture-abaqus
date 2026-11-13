# K en fonction de la longueur de fissure (a/W de 0,3 à 0,7)

| a/W | a (mm) | K FE (MPa√m) | K ASTM (MPa√m) | Écart |
|---|---|---|---|---|
| 0,30 | 15,0 | 10,458 | 10,055 | +4,00 % |
| 0,35 | 17,5 | 11,674 | 11,434 | +2,10 % |
| 0,40 | 20,0 | 13,118 | 13,021 | +0,75 % |
| 0,45 | 22,5 | 14,915 | 14,918 | −0,02 % |
| 0,50 | 25,0 | 17,211 | 17,279 | −0,39 % |
| 0,55 | 27,5 | 20,220 | 20,329 | −0,54 % |
| 0,60 | 30,0 | 24,319 | 24,425 | −0,43 % |
| 0,65 | 32,5 | 30,047 | 30,155 | −0,36 % |
| 0,70 | 35,0 | 38,438 | 38,553 | −0,30 % |

Qualité du calcul sur toute la plage : 807 à 831 nœuds, dispersion de J de 0,23 à 0,31 %, K2/K1 de 0,00 à 0,04 %.

## Constat
- De a/W = 0,4 à 0,7, l'écart à l'ASTM est inférieur à 1 %.
- À a/W = 0,3 et 0,35, K éléments finis dépasse l'ASTM de +4,0 % et +2,1 %.

## Hypothèse sur l'écart (non vérifiée)
Le couplage cinématique rend le bord du trou rigide ; quand la fissure est courte, la pointe est plus
proche des trous et l'effet de ce modèle de chargement est plus fort. Un test avec un couplage
distribué permettrait de le vérifier.

## Décision (prise après avoir vu l'écart)
La propagation (Paris, Walker) est intégrée de a/W = 0,4 à 0,7 (20 à 35 mm). Effet sur la durée de vie
(C et m illustratifs) : en intégrant de 15 mm, N éléments finis / N ASTM = −3,9 % ; de 20 mm, +0,3 %.