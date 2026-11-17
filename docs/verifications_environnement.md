| # | Vérification | Statut |
|---|---|---|
| 1 | `run_and_read.py` sur le vrai .dat (`results/raw/ct_a050.dat`) donne K = 541,9 MPa√mm | OK le 13/11/2026 |
| 2 | `abaqus information=system` répond | OK (Learning Edition 2026) |
| A | Construction du modèle sans interface (`abaqus cae noGUI=…`) | OK le 13/11/2026 (il faut importer les modules d'Abaqus dans build_ct.py) |
| B | Solveur en ligne de commande, .sta COMPLETED SUCCESSFULLY, K = 544,3 | OK le 13/11/2026 |
| C | Taille du premier élément à la pointe ≈ 0,27 mm, nœuds milieux à 0,5 | OK : [0.0, 0.13627, 0.27254, …] |
| D | Compteur de nœuds sur le .inp | OK : 819 (817 + 2 points de référence) |
## Code_Aster (comparaison inter-solveurs)

| # | Vérification | Statut |
|---|---|---|
| E | `run_aster --version` | OK le 17/11/2026 : code_aster 17.4.0 (Windows, installation native, hors WSL et Docker) |
| F | Cas test `sslv155a` (axisymétrique, K1 et K2 par `CALC_G` et `POST_K1_K2_K3`) : `run_aster --test <chemin>\sslv155a.export`, dossier de travail `C:\aster_calculs` | OK le 17/11/2026 : 8 comparaisons `OK`, 0 `NOOK` |

Détail de F :
- Valeurs recalculées identiques aux valeurs de référence de non-régression (écart de l'ordre de 1e-11 %), par exemple K1 = 1 190 521,84.
- Écart à la solution analytique : K1 1,16 % (tolérance du cas : 2 %), K2 7,6 % (tolérance : 10 %). Ces tolérances sont celles du cas test, pas les nôtres.
- Le diagnostic final affiché par `run_aster` est `NO_TEST_RESU` : sur cette installation Windows, le dossier de sortie est copié vide et les temps affichés sont à 0,00. Le diagnostic n'est donc pas utilisé. La vérification se fait en lisant les lignes `OK` / `NOOK` du journal (`run_aster ... *> aster.log`, puis `Select-String -Pattern "\bNOOK\b"`).
- Les messages rouges `RemoteException` de PowerShell sont la sortie d'erreur de Code_Aster (messages de la bibliothèque MED), sans lien avec le calcul.
- L'option `--tee` n'existe pas dans cette version.
