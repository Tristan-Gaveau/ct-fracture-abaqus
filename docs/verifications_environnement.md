| # | Vérification | Statut |
|---|---|---|
| 1 | `run_and_read.py` sur le vrai .dat (`results/raw/ct_a050.dat`) donne K = 541,9 MPa√mm | OK le 13/11/2026 |
| 2 | `abaqus information=system` répond | OK (Learning Edition 2026) |
| A | Construction du modèle sans interface (`abaqus cae noGUI=…`) | OK le 13/11/2026 (il faut importer les modules d'Abaqus dans build_ct.py) |
| B | Solveur en ligne de commande, .sta COMPLETED SUCCESSFULLY, K = 544,3 | OK le 13/11/2026 |
| C | Taille du premier élément à la pointe ≈ 0,27 mm, nœuds milieux à 0,5 | OK : [0.0, 0.13627, 0.27254, …] |
| D | Compteur de nœuds sur le .inp | OK : 819 (817 + 2 points de référence) |