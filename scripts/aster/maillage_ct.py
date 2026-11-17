# -*- coding: utf-8 -*-
"""Maillage Gmsh de l'éprouvette CT pour Code_Aster (2D, éléments quadratiques, export .med).

Même géométrie que l'Abaqus (scripts/params.py, scripts/geometrie.py) :
repère à la ligne de chargement, face avant en x = -12,5, fissure sur y = 0, pointe en (a ; 0).

Fissure : deux lèvres séparées (nœuds distincts) de la face avant à la pointe, un seul nœud à la pointe.
Disque de pointe de rayon R coupé en 4 quarts, avec un biais radial (ratio plus grand / plus petit élément).

Groupes écrits dans le .med :
  PLAQUE (surfaces), LEV_SUP et LEV_INF (arêtes des lèvres), FOND (pointe),
  TR_HAUT et TR_BAS (arêtes des trous), N_HAUT et N_BAS (un nœud sur chaque trou : force et appui).

Usage : python maillage_ct.py --a-sur-w 0.5 --sortie ct_a050.med
"""
import argparse
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import params as P  # noqa: E402


def verifier(a, r):
    if a - r <= P.X_FACE_AVANT + 2.0 or a + r >= P.X_FACE_ARRIERE - 2.0:
        raise ValueError("Disque trop près d'une face (a = %.1f mm)" % a)
    for yc in (P.Y_TROU, -P.Y_TROU):
        if math.hypot(a, yc) - P.R_TROU - r < 2.0:
            raise ValueError("Disque trop près d'un trou (a = %.1f mm)" % a)


def rendre_2d(med):
    """Gmsh écrit toujours un maillage 3D (dimension 3, coordonnées x y z). Code_Aster le prend alors pour du 3D
    et refuse DEFI_FOND_FISS avec GROUP_NO. On réécrit le .med en vrai 2D : dimension 2, coordonnées x et y."""
    import h5py
    with h5py.File(med, "r+") as f:
        nom = list(f["ENS_MAA"].keys())[0]
        maa = f["ENS_MAA"][nom]
        maa.attrs["DIM"] = 2
        maa.attrs["ESP"] = 2
        coo = []
        maa.visititems(lambda n, o: coo.append(n) if n.endswith("NOE/COO") else None)
        for chemin in coo:
            ds = maa[chemin]
            n = int(ds.attrs["NBR"])
            donnees = ds[:]
            attrs = dict(ds.attrs)
            if donnees.size != 3 * n:
                continue
            xy = donnees[:2 * n].copy()          # stockage par blocs : X, puis Y, puis Z (nul)
            del maa[chemin]
            nouveau = maa.create_dataset(chemin, data=xy)
            for k, v in attrs.items():
                nouveau.attrs[k] = v


def construire(a_sur_w, sortie, n_arc=P.N_ARC, n_couches=P.N_COUCHES, ratio=P.RATIO_BIAIS,
               rayon=P.RAYON_DISQUE, h_global=P.TAILLE_GLOBALE, h_proche=2.5, n_trou=6, n_levre=12,
               quad=False):
    """Écrit le .med et renvoie un dict (nombre de nœuds, d'éléments...)."""
    import gmsh

    A = a_sur_w * P.W
    R = rayon
    verifier(A, R)
    x0, x1, yh = P.X_FACE_AVANT, P.X_FACE_ARRIERE, P.HAUTEUR / 2.0
    q = ratio ** (1.0 / (n_couches - 1))        # raison de la progression géométrique

    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.model.add("ct")
        g = gmsh.model.geo

        def pt(x, y, h=h_global):
            return g.addPoint(x, y, 0.0, h)

        # points : chaque lèvre a ses propres points (mêmes coordonnées, nœuds distincts)
        O = pt(A, 0.0, h_proche)
        PR, PH, PB = pt(A + R, 0.0), pt(A, R), pt(A, -R)
        PLh, PLb = pt(A - R, 0.0), pt(A - R, 0.0)
        FAh, FAb = pt(x0, 0.0), pt(x0, 0.0)
        BP = pt(x1, 0.0)
        cHD, cHG, cBD, cBG = pt(x1, yh), pt(x0, yh), pt(x1, -yh), pt(x0, -yh)

        # lignes
        lev_h, lev_b = g.addLine(FAh, PLh), g.addLine(FAb, PLb)        # lèvres hors disque
        lev_h_d, lev_b_d = g.addLine(PLh, O), g.addLine(PLb, O)        # lèvres dans le disque
        dev = g.addLine(PR, BP)                                        # devant la pointe
        r_PR, r_PH, r_PB = g.addLine(O, PR), g.addLine(O, PH), g.addLine(O, PB)   # rayons depuis la pointe
        a_hd, a_hg = g.addCircleArc(PR, O, PH), g.addCircleArc(PH, O, PLh)
        a_bg, a_bd = g.addCircleArc(PLb, O, PB), g.addCircleArc(PB, O, PR)
        haut = [g.addLine(BP, cHD), g.addLine(cHD, cHG), g.addLine(cHG, FAh)]
        bas = [g.addLine(FAb, cBG), g.addLine(cBG, cBD), g.addLine(cBD, BP)]

        trous, noeuds_trou = {}, {}
        for nom, yc, i_nd in (("HAUT", P.Y_TROU, 1), ("BAS", -P.Y_TROU, 3)):
            c = g.addPoint(0.0, yc, 0.0, h_global)
            p = [pt(P.R_TROU, yc), pt(0.0, yc + P.R_TROU), pt(-P.R_TROU, yc), pt(0.0, yc - P.R_TROU)]
            arcs = [g.addCircleArc(p[i], c, p[(i + 1) % 4]) for i in range(4)]
            trous[nom] = (g.addCurveLoop(arcs), arcs)
            noeuds_trou[nom] = p[i_nd]

        # surfaces
        s_h = g.addPlaneSurface([g.addCurveLoop([lev_h, -a_hg, -a_hd, dev] + haut), trous["HAUT"][0]])
        s_b = g.addPlaneSurface([g.addCurveLoop(bas + [-dev, -a_bd, -a_bg, -lev_b]), trous["BAS"][0]])
        quarts = [g.addPlaneSurface([g.addCurveLoop(b)]) for b in (
            [r_PR, a_hd, -r_PH], [r_PH, a_hg, lev_h_d], [-lev_b_d, a_bg, -r_PB], [r_PB, a_bd, -r_PR])]
        g.synchronize()

        # nombre d'éléments imposé : rayons (biais), arcs, lèvres, trous
        tf = gmsh.model.geo.mesh.setTransfiniteCurve
        for c in (r_PR, r_PH, r_PB):
            tf(c, n_couches + 1, "Progression", q)
        for c in (lev_h_d, lev_b_d):                 # orientées vers la pointe : progression inverse
            tf(c, n_couches + 1, "Progression", 1.0 / q)
        for c in (a_hd, a_hg, a_bg, a_bd):
            tf(c, n_arc + 1, "Progression", 1.0)
        for c in (lev_h, lev_b):
            tf(c, n_levre + 1, "Progression", 1.0)
        for nom in trous:
            for c in trous[nom][1]:
                tf(c, n_trou + 1, "Progression", 1.0)

        # raffinement progressif autour du disque
        f1 = gmsh.model.mesh.field.add("Distance")
        gmsh.model.mesh.field.setNumbers(f1, "PointsList", [O])
        f2 = gmsh.model.mesh.field.add("Threshold")
        gmsh.model.mesh.field.setNumber(f2, "InField", f1)
        gmsh.model.mesh.field.setNumber(f2, "SizeMin", h_proche)
        gmsh.model.mesh.field.setNumber(f2, "SizeMax", h_global)
        gmsh.model.mesh.field.setNumber(f2, "DistMin", R)
        gmsh.model.mesh.field.setNumber(f2, "DistMax", R + 20.0)
        gmsh.model.mesh.field.setAsBackgroundMesh(f2)
        gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
        gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
        gmsh.option.setNumber("Mesh.Algorithm", 6)
        gmsh.option.setNumber("Mesh.ElementOrder", 2)
        gmsh.option.setNumber("Mesh.SecondOrderLinear", 1)
        if quad:
            for s in [s_h, s_b] + quarts:
                gmsh.model.geo.mesh.setRecombine(2, s)
            gmsh.option.setNumber("Mesh.RecombinationAlgorithm", 3)
        g.synchronize()

        # groupes physiques
        pg = gmsh.model.addPhysicalGroup
        sn = gmsh.model.setPhysicalName
        for dim, tags, nom in (
                (2, [s_h, s_b] + quarts, "PLAQUE"),
                (1, [lev_h, lev_h_d], "LEV_SUP"), (1, [lev_b, lev_b_d], "LEV_INF"),
                (0, [O], "FOND"),
                (1, trous["HAUT"][1], "TR_HAUT"), (1, trous["BAS"][1], "TR_BAS"),
                (0, [noeuds_trou["HAUT"]], "N_HAUT"), (0, [noeuds_trou["BAS"]], "N_BAS")):
            sn(dim, pg(dim, tags), nom)

        gmsh.model.mesh.generate(2)
        types, _, _ = gmsh.model.mesh.getElements(2)
        n_noeuds = len(gmsh.model.mesh.getNodes()[0])
        info = {"a": A, "noeuds": n_noeuds, "types_2d": [gmsh.model.mesh.getElementProperties(t)[0] for t in types]}
        if os.path.dirname(sortie):
            os.makedirs(os.path.dirname(sortie), exist_ok=True)
        gmsh.write(sortie)
    finally:
        gmsh.finalize()
    rendre_2d(sortie)
    return info


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--a-sur-w", type=float, default=P.A_SUR_W_REF)
    ap.add_argument("--sortie", required=True, help="fichier .med à écrire")
    ap.add_argument("--n-arc", type=int, default=P.N_ARC, help="éléments par quart d'arc du disque")
    ap.add_argument("--n-couches", type=int, default=P.N_COUCHES, help="éléments radiaux dans le disque")
    ap.add_argument("--ratio", type=float, default=P.RATIO_BIAIS)
    ap.add_argument("--h-global", type=float, default=P.TAILLE_GLOBALE)
    ap.add_argument("--h-proche", type=float, default=2.5, help="taille autour du disque (mm)")
    ap.add_argument("--quad", action="store_true", help="recombiner en quadrangles (QUAD8)")
    a = ap.parse_args()
    info = construire(a.a_sur_w, a.sortie, a.n_arc, a.n_couches, a.ratio, P.RAYON_DISQUE,
                      a.h_global, a.h_proche, quad=a.quad)
    print("a = %.2f mm | %d nœuds | éléments 2D : %s | écrit : %s"
          % (info["a"], info["noeuds"], ", ".join(info["types_2d"]), a.sortie))


if __name__ == "__main__":
    main()
