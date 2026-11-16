# Propagation de fissure : lois de Paris et de Walker (acier 300M)

Paris : da/dN = C·ΔK^m avec C = 3,121 × 10⁻¹¹ (m/cycle, MPa√m) et m = 2,672, ajustés sur la figure 2.3.1.4.9 du
MIL-HDBK-5J (15 points numérisés). R = 0,1. Intégration de a = 20 mm (a/W = 0,4) à a = 35 mm (a/W = 0,7) ; le choix
de la borne basse est expliqué dans `K_vs_a_resultats.md`.

| Source de K | N (cycles) |
|---|---|
| K analytique (ASTM) | 252 461 |
| K éléments finis | 253 264 (+0,32 %) |

Marge à la rupture : K_max = 38,4 MPa√m à 35 mm (éléments finis), K_Ic = 62,6 MPa√m (NASA TP-1288), soit
K_max/K_Ic = 0,62 (0,44 avec la borne haute de la plage, 86,8 MPa√m).

## Sensibilité à C et m (K éléments finis)

| m | C × 0,8 | C nominal | C × 1,2 |
|---|---|---|---|
| 2,17 | 1 250 024 | 1 000 019 | 833 349 |
| 2,67 | 316 580 | 253 264 | 211 054 |
| 3,17 | 81 290 | 65 032 | 54 193 |

- N varie d'un facteur 15 entre m = 2,17 et m = 3,17 (à C nominal) : ΔK est élevé à la puissance m.
- C ± 20 % donne N de +25 % à −17 % (à m = 2,67).
- C et m sont corrélés : varier m seul à C fixé exagère l'effet.

## Effet d'une contrainte résiduelle (Walker, profil et amplitude hypothétiques)

Variation de N par rapport à σ0 = 0, selon l'exposant γ (aucune source ne le fixe) :

| γ | σ0 = −100 MPa | −50 | +50 | +100 |
|---|---|---|---|---|
| 0,50 | +181 % | +41 % | −17 % | −28 % |
| 0,75 | +162 % | +32 % | −9 % | −16 % |
| 1,00 | +145 % | +24 % | 0 % | 0 % |

## Limites

- Zone de propagation stable seulement (ni seuil ΔK_th, ni rupture finale).
- Les points numérisés couvrent ΔK de 11,0 à 31,8 MPa√m ; l'étude va jusqu'à 34,7 MPa√m : le dernier tronçon est une
  extrapolation, qui surestime la durée de vie (côté non conservatif).
- Valeurs brutes : `paris_resultats.csv`.
