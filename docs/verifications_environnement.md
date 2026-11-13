# Vérifications de l'environnement (Abaqus Learning Edition 2026)

| # | Vérification | Statut |
|---|---|---|
| 1 | `run_and_read.py` sur le vrai .dat (`results/raw/ct_a050.dat`) donne K = 541,9 MPa√mm | OK le 13/11/2026 (dispersion J 2,6 %, K2/K1 2,6 %) |
| 2 | `abaqus information=system` répond | OK (Learning Edition 2026) |
| A | `abaqus cae noGUI=test_args.py -- ...` : le script s'exécute et reçoit ses arguments | Sans sortie visible : à diagnostiquer (voir ci-dessous). Plan B prévu : mode manuel (`--manuel`) |
| B | `abaqus job=test_cli interactive ask_delete=OFF` puis `.sta` contient COMPLETED SUCCESSFULLY, K = 541,9 | À faire |
| C | Taille du premier élément à la pointe ≈ 0,27 mm pour le biais 4 (3ᵉ valeur du script de diagnostic) | À faire |
| D | `compter_noeuds_elements` donne (797, 240) ou (799, 240) sur le .inp du calcul manuel | À faire |

## Diagnostic du test A
1. `dir` puis `$LASTEXITCODE` dans le dossier de test.
2. Faire écrire le script dans un fichier (`sortie.txt`) au lieu d'afficher.
3. Sinon, tester via CAE : File > Run Script.
Si le mode sans interface ne marche pas : `python scripts/run_case.py 0.5 4 ct_a050 --manuel`
(build_ct.py lancé à la main dans CAE avec File > Run Script ; solveur et lecture restent automatiques).

## Dossiers (corrigé le 13/11/2026)
- Le dossier de travail de CAE est `C:\Users\trist\` : les fichiers du calcul manuel (`ct_a050.inp`, `.dat`,
  `.sta`, `.odb`) y sont, et non dans `Documents\abaqus`.
- Le modèle `ct-fracture-abaqus.cae` est dans `C:\Users\trist\Documents\abaqus\`.
- Test B : `copy C:\Users\trist\ct_a050.inp C:\abaqus_tests\test_cli.inp`
- Tests C et D : même fichier d'entrée, `C:\abaqus_tests\test_cli.inp`.
- Un fichier .rec ne contient que les commandes depuis la dernière sauvegarde. Pour reconstruire le
  modèle dans build_ct.py, il faut le journal `.jnl` (ou les `abaqus.rpy*`).
