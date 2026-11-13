# Propagation de fissure : loi de Paris (valeurs ILLUSTRATIVES)

C = 1e-11 (m/cycle, MPa√m), m = 3, R = 0,1. Ces valeurs ne viennent d'aucune source : à remplacer
par des valeurs citées avant toute conclusion chiffrée.

Intégration de a = 20 mm (a/W = 0,4) à a = 35 mm (a/W = 0,7) ; le choix de la borne basse est expliqué
dans K_vs_a_resultats.md.

| Source de K | N (cycles) |
|---|---|
| K analytique (ASTM) | 322 570 |
| K éléments finis | 323 526 (+0,30 %) |

## Sensibilité (K éléments finis)
| m | C = 8e-12 | C = 1e-11 | C = 1,2e-11 |
|---|---|---|---|
| 2,5 | 1 582 097 | 1 265 678 | 1 054 731 |
| 3,0 | 404 407 | 323 525 | 269 605 |
| 3,5 | 104 678 | 83 743 | 69 786 |

- N varie d'un facteur 15 entre m = 2,5 et m = 3,5 (à C = 1e-11) : ΔK est élevé à la puissance m.
- C ±20 % donne N de +25 % à −17 %.
- C et m sont corrélés : varier m seul à C fixé exagère l'effet.

## Limites
- Zone de propagation stable seulement (ni seuil ΔK_th, ni rupture finale).
- K_Ic non renseigné : K_max à a = 35 mm (38,6 MPa√m) n'est pas encore comparé à K_Ic.