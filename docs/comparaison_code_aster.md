# Comparaison avec Code_Aster

Objectif : vérifier K(a) avec un second solveur, un autre maillage et une autre méthode (G-thêta au lieu de
l'intégrale J d'Abaqus). Critère fixé avant le calcul : écart Code_Aster / Abaqus sous 1 % pour a/W de 0,4 à 0,7 ;
0,30 et 0,35 rapportés tels quels.

## Modèle

- Code_Aster 17.4.0 (version native Windows), Gmsh 4.15.
- Même géométrie que `scripts/params.py` : CT, W = 50 mm, trous de rayon 6,25 mm en (0 ; ±13,75), fissure sur y = 0,
  pointe en x = a (a mesuré depuis la ligne de chargement). Matériau E = 210 GPa, ν = 0,30. Déformations planes (`D_PLAN`).
- Maillage (`scripts/aster/maillage_ct.py`) : triangles quadratiques (TRIA6). Fissure à **lèvres séparées** de la face
  avant à la pointe (nœuds distincts), un seul nœud à la pointe. Disque de pointe de rayon 6 mm coupé en 4 quarts, 10
  éléments radiaux avec le même biais que sous Abaqus (rapport 4), 2 éléments par quart d'arc. Environ 1 600 nœuds.
- Conditions aux limites : le bord de chaque trou est un corps rigide (`LIAISON_SOLIDE`), qui peut tourner, comme le
  couplage cinématique d'Abaqus (translations liées, `ur3` libre). Trou du bas : bloqué en X et Y. Trou du haut : bloqué
  en X, force verticale de 400 N/mm (10 kN sur B = 25 mm).
- K : `CALC_G` option `K`, 7 couronnes (R_INF, R_SUP) construites sur les rayons des nœuds du disque, de 0,27 à 4,9 mm
  (le disque fait 6 mm : la couronne extérieure reste à l'intérieur). La couronne 1 est écartée, comme le contour 1
  d'Abaqus. **K officiel = moyenne de K1 sur les couronnes 2 à 7** ; dispersion = (max − min) / moyenne.

## Résultats

K en MPa√m.

| a/W | K Aster | K Abaqus | K ASTM | Aster/Abaqus (%) | Aster/ASTM (%) | dispersion couronnes (%) |
|---|---|---|---|---|---|---|
| 0.30 | 10.447 | 10.458 | 10.055 | -0.10 | +3.90 | 0.25 |
| 0.35 | 11.646 | 11.674 | 11.434 | -0.24 | +1.85 | 0.52 |
| 0.40 | 13.091 | 13.118 | 13.021 | -0.21 | +0.54 | 0.52 |
| 0.45 | 14.881 | 14.915 | 14.918 | -0.23 | -0.25 | 0.52 |
| 0.50 | 17.168 | 17.211 | 17.279 | -0.25 | -0.64 | 0.52 |
| 0.55 | 20.175 | 20.220 | 20.329 | -0.22 | -0.76 | 0.52 |
| 0.60 | 24.250 | 24.319 | 24.425 | -0.29 | -0.72 | 0.52 |
| 0.65 | 29.958 | 30.047 | 30.154 | -0.30 | -0.65 | 0.29 |
| 0.70 | 38.302 | 38.438 | 38.553 | -0.35 | -0.65 | 0.29 |

Les 9 écarts à Abaqus sont entre −0,10 % et −0,35 % : critère atteint (le pire écart sur 0,4 à 0,7 est −0,35 %).
Code_Aster est systématiquement un peu plus bas qu'Abaqus (0,1 à 0,35 %), sans tendance avec a/W.

À a/W = 0,3 et 0,35, Code_Aster retrouve Abaqus (−0,10 % et −0,24 %) et s'écarte donc de l'ASTM comme lui (+3,9 % et
+1,9 %). **L'écart aux petites fissures ne vient ni du solveur, ni du maillage, ni de la méthode de calcul de K.** Il
reste le chargement (bord du trou entier au lieu d'un contact de goupille) ou la validité de la formule ASTM à petite
fissure. Les deux modèles ont les mêmes conditions aux limites : cette comparaison ne permet pas de trancher.

## Convergence de maillage (a/W = 0,5)

| maillage | nœuds | éléments par quart d'arc | éléments radiaux | taille autour du disque (mm) | K (MPa√m) | dispersion (%) | écart au précédent (%) |
|---|---|---|---|---|---|---|---|
| conv_1 | 1 645 | 2 | 10 | 2,5 | 17,1676 | 0,52 | |
| conv_2 | 2 225 | 4 | 14 | 1,5 | 17,1949 | 0,40 | +0,159 |
| conv_3 | 2 889 | 6 | 20 | 1,0 | 17,2076 | 0,26 | +0,074 |

Critère : écart entre les deux derniers maillages sous 0,2 % : atteint (0,074 %). Le maillage le plus fin donne 17,208,
soit −0,02 % d'Abaqus (17,211) : les valeurs de la comparaison (maillage conv_1) sont donc légèrement sous-estimées,
d'environ 0,2 %, ce qui explique en partie le signe constant de l'écart.

## Ce que la vérification a révélé

1. **Dimension du maillage.** Gmsh écrit un `.med` de dimension 3 même pour un maillage plan. `DEFI_FOND_FISS` refusait
   alors le groupe de nœuds de la pointe (message `RUPTURE1_9`). `maillage_ct.py` réécrit le fichier en dimension 2
   (`h5py`).
2. **Syntaxe de la version 17.4.** `CALC_G` n'accepte plus l'option `CALC_K_G` mais `K`, et le mot-clé `THETA` demande
   `FISSURE` et non `FOND_FISS`. La table ne contient pas `G` mais `K1`, `K2` et `G_IRWIN`.
3. **Rotation des trous.** Première version des liaisons : `LIAISON_UNIF`, qui impose le même déplacement à tous les
   nœuds du bord et bloque donc la rotation du pion. K était stable d'une couronne à l'autre (279 MPa√mm, dispersion
   0,7 %) mais **49 % trop bas**. Le contrôle des réactions (400 N/mm, correct) et de l'ouverture des lèvres à la
   face avant (0,026 mm au lieu de 0,085 mm) a montré que l'éprouvette était trop raide : la charge était bonne, pas la
   liaison. Avec `LIAISON_SOLIDE` (rotation libre, comme `ur3` libre dans le couplage cinématique d'Abaqus), K = 543 MPa√mm.

   Leçon : la stabilité de K entre couronnes ne prouve pas que la solution est juste, elle prouve seulement que le calcul
   de K est cohérent avec le champ de déplacement.

## Limites

- Un seul type de maillage (triangles quadratiques) ; Abaqus utilise surtout des quadrilatères CPE8R. Les deux
  méthodes (J, G-thêta) sont de la même famille (intégrale de domaine) : un troisième moyen (corrélation de
  déplacements, extrapolation) aurait une valeur de vérification plus indépendante.
- Les conditions aux limites sont identiques dans les deux modèles : la comparaison valide le solveur, le maillage et
  la méthode, pas le chargement.
- Le nœud de force est sur le bord du trou, à la verticale du centre (pas de moment) ; le centre n'est pas un nœud du
  modèle. L'appui du trou du haut en X est imposé sur ce nœud de bord et non au centre.

## Reproduire

```
python scripts/aster/preparer_serie.py --serie --convergence      # maillages, .comm et .export dans C:\aster_calculs
# dans le terminal « code_aster » :
Get-ChildItem C:\aster_calculs\cas_a*, C:\aster_calculs\conv_* -Directory | ForEach-Object { cd $_.FullName; run_aster cas.export *> run.log }
python scripts/aster/comparer.py                                    # tableau, convergence et figure
```

Les tables brutes de chaque calcul sont dans `results/aster/`.
