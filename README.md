# ct-fracture-abaqus

Calcul du facteur d'intensité de contrainte K sur une éprouvette CT (Abaqus, intégrale J),
comparaison à la formule ASTM E399, puis prédiction de durée de vie en propagation
(loi de Paris, puis loi de Walker avec contraintes résiduelles).

**État : en cours.** Les chiffres marqués « à compléter » ne sont pas encore mesurés.

## Résultats clés
- K éléments finis contre formule (a/W = 0,5) : **−0,33 %** (17,22 contre 17,28 MPa√m), maillage convergé à la pointe
- Convergence de maillage : K stable à 0,06 % près pour un premier élément de 0,27 à 0,05 mm (4 maillages, critère 0,2 %)
- K(a) pour 9 longueurs de fissure : écart à l'ASTM inférieur à 1 % de a/W = 0,4 à 0,7 ; +4,0 % et +2,1 % à a/W = 0,3 et 0,35 (cause non établie), d'où une propagation intégrée de 20 à 35 mm
- Durée de vie (C, m illustratifs, R = 0,1) : 3,2 × 10⁵ cycles de 20 à 35 mm, identique à 0,3 % près avec K éléments finis ou K ASTM ; N varie d'un facteur 15 entre m = 2,5 et m = 3,5
- Contraintes résiduelles (bonus, profil et amplitude HYPOTHÉTIQUES) : K_res par superposition, +6,9 MPa√m à 20 mm pour σ0 = 100 MPa, décroissant et nul vers 34 mm ; effet sur la durée de vie (Walker, C, m, γ illustratifs) de −32 % (σ0 = +100 MPa) à +237 % (σ0 = −100 MPa)

## Modèle
Éprouvette CT, W = 50 mm, B = 25 mm, a/W = 0,5. Déformations planes, élasticité linéaire, acier
(E = 210 GPa, nu = 0,3). Charge 10 kN (400 N par mm d'épaisseur dans le modèle 2D). Maillage CPE8R,
disque de pointe de 10 couches avec biais radial. Détails et hypothèses : `docs/hypotheses.md`.

## Méthode
1. Formule analytique (`scripts/k_analytique.py`)
2. Modèle éléments finis et intégrale J, 10 contours (`scripts/build_ct.py`, `scripts/run_case.py`)
3. K officiel = moyenne des contours 3 à 10 de sqrt(J·E') (`scripts/run_and_read.py`)
4. Convergence de maillage (`scripts/convergence.py`)
5. K(a) (`scripts/k_vs_a.py`)
6. Propagation (`scripts/paris.py`)

## Structure
```
scripts/   code (params.py : paramètres uniques ; chemins.py : chemins)
tests/     tests automatiques (pytest)
results/   CSV, figures, fichiers .dat bruts
docs/      hypotheses.md, verifications_environnement.md
```

## Utilisation
```
pip install -r requirements.txt
python -m pytest
python scripts/run_case.py 0.5 4 ct_a050            # un cas (automatique)
python scripts/run_case.py 0.5 4 ct_a050 --manuel   # build_ct.py lancé à la main dans CAE
python scripts/convergence.py
python scripts/k_vs_a.py
python scripts/paris.py
```
Les calculs Abaqus se font dans `C:\abaqus_calculs` (variable `CT_CALCULS` pour changer), hors du dépôt.

## Limites
- 2D déformations planes ; pas de plasticité en pointe ; pas de fermeture de fissure réelle
- Paris et Walker : zone de propagation stable seulement
- Learning Edition : 1 000 nœuds maximum
- Couplage cinématique sur les trous (bord rigide)

## Pour aller plus loin
Code_Aster (comparaison de solveurs), 3D, profil de contraintes résiduelles mesuré.

## Références
ASTM E399 ; T. L. Anderson, *Fracture Mechanics: Fundamentals and Applications* ;
Paris et Erdogan (1963) ; documentation Abaqus (Contour integral evaluation).
