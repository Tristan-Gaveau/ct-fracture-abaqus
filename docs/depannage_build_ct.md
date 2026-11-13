# Mise au point de build_ct.py, bloc par bloc

`build_ct.py` est écrit sans Abaqus sous la main : les noms de l'API viennent de la documentation et du
fichier `.rec`. Il s'exécute par blocs (1 géométrie, 2 matériau et assemblage, 3 fissure,
4 couplages / step / charges, 5 maillage, 6 écriture du .inp), chacun avec des auto-vérifications.

## Lancer jusqu'au bloc N
1. PowerShell, à la racine du dépôt :
   `python scripts/run_case.py 0.5 4 ct_a050 --cas-seulement --jusqu-a=N`
2. Abaqus/CAE : File > Set Work Directory > `C:\abaqus_calculs`, puis File > Run Script > `scripts\build_ct.py`.
3. Attendu dans la zone de messages : `ETAPE N OK : ...` et le modèle visible dans CAE.
4. Chaque lancement repart de zéro (`Mdb()`), donc on peut relancer autant de fois que nécessaire.

## En cas d'erreur
Copier le message complet (toutes les lignes, de « Traceback » à la dernière). Si une commande de l'API
est refusée, enregistrer un micro-macro de cette seule action :
File > Macro Manager > Create, refaire l'action dans une COPIE du modèle, arrêter l'enregistrement, puis
ouvrir `abaqusMacros.py` (dossier de travail ou dossier utilisateur) et en envoyer les quelques lignes utiles.

## Contrôles visuels
- Bloc 1 : 6 faces ; pointe à 37,5 mm de la face avant (x = 25) ; disque en 4 quarts.
- Bloc 3 : seam de la face avant à la pointe seulement ; flèche q horizontale vers la droite.
- Bloc 4 : 2 couplages, charge sur RP_HAUT (vers le haut), BC sur les deux RP.
- Bloc 5 : 797 nœuds environ ; CPE8R et CPE6 seulement ; 10 couches dans le disque.
- Bloc 6 : `ct_a050.inp` et `ct_a050.cae` écrits ; non-régression avec `run_case.py` (sans --cas-seulement).
