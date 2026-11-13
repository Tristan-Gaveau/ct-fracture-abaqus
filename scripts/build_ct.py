# -*- coding: utf-8 -*-
"""Construit le modèle CT dans Abaqus/CAE et écrit <nom>.inp (sans lancer le solveur).

Se lance de deux façons (voir run_case.py) :
  - automatique : abaqus cae noGUI=scripts/build_ct.py   (dossier courant = dossier des calculs)
  - manuel      : CAE > File > Set Work Directory = dossier des calculs, puis File > Run Script

Paramètres du cas : cas_en_cours.json (dossier courant), écrit par run_case.py.
Le champ "jusqu_a" limite l'exécution aux N premiers blocs (mise au point bloc par bloc) :
  1 géométrie   2 matériau et assemblage   3 fissure   4 couplages, step, charges, sorties
  5 maillage    6 écriture du .inp

ÉCRIT SANS ABAQUS SOUS LA MAIN : les noms de l'API viennent de la documentation et du fichier .rec.
Chaque bloc se vérifie lui-même ; en cas d'erreur, copie le message complet.
Python 3 (Abaqus 2024 et suivants).
"""
import json
import os
import sys

from abaqus import *
from abaqusConstants import *
# Sans interface (noGUI), Abaqus ne charge que les modules importés ici : chacun ajoute ses commandes
# au modèle (Coupling vient de interaction, StaticStep de step, ConcentratedForce de load, etc.).
from part import *
from material import *
from section import *
from assembly import *
from step import *
from interaction import *
from load import *
from mesh import *            # ElemType
from job import *
from sketch import *
import regionToolset

FICHIER_CAS = "cas_en_cours.json"


def lire_cas():
    if not os.path.exists(FICHIER_CAS):
        raise RuntimeError(
            "%s introuvable dans %s. Lance d'abord run_case.py (option --cas-seulement) et, dans CAE, "
            "File > Set Work Directory > dossier des calculs." % (FICHIER_CAS, os.getcwd()))
    with open(FICHIER_CAS) as f:
        return json.load(f)


CAS = lire_cas()
sys.path.insert(0, CAS["dossier_scripts"])
import params as P          # noqa: E402
import geometrie as G       # noqa: E402

A_SUR_W = CAS["a_sur_w"]
RATIO_BIAIS = CAS["ratio_biais"]
NOM = CAS["nom"]
JUSQU_A = CAS.get("jusqu_a", 6)
MODE = CAS.get("mode", "applique")          # "applique" (charge sur les trous) ou "k_res" (pression sur les lèvres)
SIGMA0 = CAS.get("sigma0", 0.0)              # MPa, amplitude de la contrainte résiduelle (mode k_res)
PROFIL = CAS.get("profil", "equilibre")      # "uniforme" ou "equilibre" (mode k_res)
A = A_SUR_W * P.W           # longueur de fissure depuis la ligne de chargement (mm)
R = P.RAYON_DISQUE

MODELE = "Model-1"
PIECE = "Part-1"
INSTANCE = "Part-1-1"


# ----------------------------------------------------------------------------- outils
def _sommet(obj, x, y, nom="sommet"):
    try:
        v = obj.vertices.findAt((x, y, 0.0), )
    except Exception:
        v = None
    if v is None:
        raise RuntimeError("Sommet attendu introuvable : %s en (%.3f ; %.3f)" % (nom, x, y))
    return v


def _arete(obj, x, y, nom="arête"):
    try:
        e = obj.edges.findAt((x, y, 0.0), )
    except Exception:
        e = None
    if e is None:
        raise RuntimeError("Arête attendue introuvable : %s en (%.3f ; %.3f)" % (nom, x, y))
    return e


def _croquis_pour_partition(p, m):
    """Croquis dont les coordonnées coïncident avec celles de la pièce (x vers la droite, y vers le haut)."""
    try:
        axe = p.datums[p.DatumAxisByPrincipalAxis(principalAxis=YAXIS).id]
        plan = p.datums[p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=0.0).id]
    except Exception as erreur:
        print("Datums refusés (%s) : repli sur une face et une arête de la pièce" % erreur)
        plan = p.faces.findAt((30.0, 20.0, 0.0), )
        axe = p.edges.findAt((P.X_FACE_ARRIERE, 20.0, 0.0), )
    t = p.MakeSketchTransform(sketchPlane=plan, sketchUpEdge=axe, sketchPlaneSide=SIDE1,
                              sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    return m.ConstrainedSketch(name="__profile__", sheetSize=200.0, transform=t), axe


# ----------------------------------------------------------------------------- bloc 1
def geometrie():
    """Rectangle, 2 trous, ligne y = 0, pointe, disque de pointe coupé en 4 quarts."""
    G.verifier_disque(A)
    m = mdb.models[MODELE]

    s = m.ConstrainedSketch(name="__profile__", sheetSize=200.0)
    s.rectangle(point1=(P.X_FACE_AVANT, -P.HAUTEUR / 2.0), point2=(P.X_FACE_ARRIERE, P.HAUTEUR / 2.0))
    for yc in (P.Y_TROU, -P.Y_TROU):
        s.CircleByCenterPerimeter(center=(0.0, yc), point1=(P.R_TROU, yc))
    p = m.Part(name=PIECE, dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    p.BaseShell(sketch=s)
    del m.sketches["__profile__"]

    # sommets en y = 0 sur les faces avant et arrière, puis ligne de bord à bord
    p.PartitionEdgeByPoint(edge=_arete(p, P.X_FACE_AVANT, 20.0, "face avant"),
                           point=(P.X_FACE_AVANT, 0.0, 0.0))
    p.PartitionEdgeByPoint(edge=_arete(p, P.X_FACE_ARRIERE, 20.0, "face arrière"),
                           point=(P.X_FACE_ARRIERE, 0.0, 0.0))
    p.PartitionFaceByShortestPath(faces=p.faces.findAt(((30.0, 20.0, 0.0),)),
                                  point1=_sommet(p, P.X_FACE_AVANT, 0.0, "face avant"),
                                  point2=_sommet(p, P.X_FACE_ARRIERE, 0.0, "face arrière"))
    # sommet de la pointe sur cette ligne
    p.PartitionEdgeByPoint(edge=_arete(p, 0.0, 0.0, "ligne de fissure"), point=(A, 0.0, 0.0))

    # disque de pointe : cercle + ligne verticale
    s, axe = _croquis_pour_partition(p, m)
    s.CircleByCenterPerimeter(center=(A, 0.0), point1=(A + R, 0.0))
    s.Line(point1=(A, -R), point2=(A, R))
    faces = p.faces.findAt(((30.0, 20.0, 0.0),), ((30.0, -20.0, 0.0),))
    p.PartitionFaceBySketch(sketchUpEdge=axe, faces=faces, sketch=s, sketchOrientation=RIGHT)
    del m.sketches["__profile__"]

    # auto-vérification : tout doit être là où le calcul manuel l'avait mis
    for nom, (x, y) in (("pointe", (A, 0.0)), ("bord gauche du disque", (A - R, 0.0)),
                        ("bord droit du disque", (A + R, 0.0)), ("haut du disque", (A, R)),
                        ("bas du disque", (A, -R))):
        _sommet(p, x, y, nom)
    if len(p.faces) != 6:
        raise RuntimeError("%d faces au lieu de 6 (2 plaques + 4 quarts de disque)" % len(p.faces))
    print("Géométrie : 6 faces ; pointe en (%.2f ; 0), disque de rayon %.1f mm" % (A, R))


# ----------------------------------------------------------------------------- bloc 2
def materiau_et_assemblage():
    m = mdb.models[MODELE]
    p = m.parts[PIECE]
    m.Material(name="ACIER").Elastic(table=((P.E, P.NU),))
    m.HomogeneousSolidSection(name="SECTION", material="ACIER", thickness=P.B_MODELE)
    p.SectionAssignment(region=regionToolset.Region(faces=p.faces), sectionName="SECTION",
                        offset=0.0, offsetType=MIDDLE_SURFACE, offsetField="",
                        thicknessAssignment=FROM_SECTION)
    asm = m.rootAssembly
    asm.DatumCsysByDefault(CARTESIAN)
    asm.Instance(name=INSTANCE, part=p, dependent=OFF)      # instance indépendante
    print("Matériau ACIER (E=%.0f, nu=%.2f), section d'épaisseur %.1f mm, instance %s"
          % (P.E, P.NU, P.B_MODELE, INSTANCE))


# ----------------------------------------------------------------------------- bloc 3
def fissure():
    """Seam de la face avant à la pointe + définition du contour integral (front, pointe, q)."""
    asm = mdb.models[MODELE].rootAssembly
    inst = asm.instances[INSTANCE]

    aretes = inst.edges.findAt(*[((x, y, 0.0),) for (x, y) in G.points_seam(A)])
    if len(aretes) != 2:
        raise RuntimeError("%d arêtes de fissure trouvées au lieu de 2" % len(aretes))
    asm.engineeringFeatures.assignSeam(regions=regionToolset.Region(edges=aretes))

    front = regionToolset.Region(vertices=inst.vertices.findAt(((A, 0.0, 0.0),)))
    v_pointe = _sommet(inst, A, 0.0, "pointe")
    v_q = _sommet(inst, A + R, 0.0, "extrémité du vecteur q")
    commun = dict(name="CRACK", symmetric=OFF, crackFront=front, crackTip=front,
                  qVectors=((v_pointe, v_q),), midNodePosition=0.5)
    erreurs = []
    for cle in ("extensionDirectionMethod", "extensionDirection"):   # nom selon la version d'Abaqus
        try:
            arguments = dict(commun)
            arguments[cle] = Q_VECTORS
            asm.engineeringFeatures.ContourIntegral(**arguments)
            print("ContourIntegral accepté avec le paramètre %s" % cle)
            break
        except TypeError as erreur:
            erreurs.append("%s : %s" % (cle, erreur))
    else:
        raise RuntimeError("ContourIntegral refusé : %s. Enregistre un micro-macro de la création de la "
                           "fissure (docs/depannage_build_ct.md) et envoie-le-moi." % " | ".join(erreurs))
    print("Fissure : seam sur 2 arêtes, front en (%.2f ; 0), q = (1, 0, 0), sans singularité" % A)


# ----------------------------------------------------------------------------- bloc 4
def _step_et_sorties(m):
    m.StaticStep(name="LOAD", previous="Initial", nlgeom=OFF)
    m.HistoryOutputRequest(name="J_OUT", createStepName="LOAD", contourIntegral="CRACK",
                           sectionPoints=DEFAULT, rebar=EXCLUDE, numberOfContours=P.N_CONTOURS)
    m.HistoryOutputRequest(name="K_OUT", createStepName="LOAD", contourIntegral="CRACK",
                           sectionPoints=DEFAULT, rebar=EXCLUDE, numberOfContours=P.N_CONTOURS,
                           contourType=K_FACTORS, kFactorDirection=MTS)


def k_res_pression():
    """K_res par superposition : aucune charge externe, pression sur les lèvres de la fissure
    (p = +sigma_res ; comme une pression de fluide, une pression positive OUVRE la fissure), pièce libre
    tenue par deux sommets seulement (réactions attendues nulles), trous libres : pas de couplage."""
    m = mdb.models[MODELE]
    asm = m.rootAssembly
    inst = asm.instances[INSTANCE]
    _step_et_sorties(m)

    y_bas = -P.HAUTEUR / 2.0
    for nom, x, bloque_u1 in (("APPUI_1", P.X_FACE_ARRIERE, True), ("APPUI_2", P.X_FACE_AVANT, False)):
        _sommet(inst, x, y_bas, nom)
        asm.Set(vertices=inst.vertices.findAt(((x, y_bas, 0.0),)), name=nom)
        m.DisplacementBC(name="BC_" + nom, createStepName="LOAD", region=asm.sets[nom],
                         u1=0.0 if bloque_u1 else UNSET, u2=0.0, ur3=UNSET, amplitude=UNSET, fixed=OFF,
                         distributionType=UNIFORM, fieldName="", localCsys=None)

    aretes = inst.edges.findAt(*[((x, y, 0.0),) for (x, y) in G.points_seam(A)])
    asm.Surface(side1Edges=aretes, side2Edges=aretes, name="LEVRES")
    magnitude, expression = G.expression_pression(PROFIL, SIGMA0)
    if expression is None:
        m.Pressure(name="P_LEVRES", createStepName="LOAD", region=asm.surfaces["LEVRES"],
                   distributionType=UNIFORM, field="", magnitude=magnitude, amplitude=UNSET)
    else:
        m.ExpressionField(name="PROFIL", localCsys=None, description="", expression=expression)
        m.Pressure(name="P_LEVRES", createStepName="LOAD", region=asm.surfaces["LEVRES"],
                   distributionType=FIELD, field="PROFIL", magnitude=magnitude, amplitude=UNSET)
    print("K_res : profil %s, sigma0 = %.1f MPa, pression sur les lèvres, appuis aux coins bas, pas de couplage"
          % (PROFIL, SIGMA0))


def couplages_step_charges():
    if MODE == "k_res":
        return k_res_pression()
    m = mdb.models[MODELE]
    asm = m.rootAssembly
    inst = asm.instances[INSTANCE]

    for nom, yc in (("HAUT", P.Y_TROU), ("BAS", -P.Y_TROU)):
        rp = asm.ReferencePoint(point=(0.0, yc, 0.0))
        asm.Set(referencePoints=(asm.referencePoints[rp.id],), name="RP_" + nom)
        r = P.R_TROU + 0.1
        bord = inst.edges.getByBoundingBox(xMin=-r, yMin=yc - r, zMin=-0.1, xMax=r, yMax=yc + r, zMax=0.1)
        if len(bord) == 0:
            raise RuntimeError("Bord du trou %s introuvable" % nom)
        asm.Surface(side1Edges=bord, name="S_TROU_" + nom)
        m.Coupling(name="CPL_" + nom, controlPoint=asm.sets["RP_" + nom],
                   surface=asm.surfaces["S_TROU_" + nom], influenceRadius=WHOLE_SURFACE,
                   couplingType=KINEMATIC, localCsys=None, u1=ON, u2=ON, ur3=OFF)

    _step_et_sorties(m)

    m.ConcentratedForce(name="F_HAUT", createStepName="LOAD", region=asm.sets["RP_HAUT"],
                        cf2=P.P_PAR_MM, distributionType=UNIFORM, field="", localCsys=None)
    m.DisplacementBC(name="BC_BAS", createStepName="LOAD", region=asm.sets["RP_BAS"],
                     u1=0.0, u2=0.0, ur3=UNSET, amplitude=UNSET, fixed=OFF,
                     distributionType=UNIFORM, fieldName="", localCsys=None)
    m.DisplacementBC(name="BC_HAUT", createStepName="LOAD", region=asm.sets["RP_HAUT"],
                     u1=0.0, u2=UNSET, ur3=UNSET, amplitude=UNSET, fixed=OFF,
                     distributionType=UNIFORM, fieldName="", localCsys=None)
    print("Couplages cinématiques, step LOAD (Nlgeom off), J_OUT et K_OUT (%d contours), "
          "charge CF2 = %.1f N/mm" % (P.N_CONTOURS, P.P_PAR_MM))


# ----------------------------------------------------------------------------- bloc 5
def maillage():
    asm = mdb.models[MODELE].rootAssembly
    inst = asm.instances[INSTANCE]

    quarts = inst.faces.findAt(*[((A + dx, dy, 0.0),) for (dx, dy) in ((2.0, 2.0), (-2.0, 2.0), (-2.0, -2.0), (2.0, -2.0))])
    # QUAD_DOMINATED : les quarts de disque ont un sommet à la pointe, où quelques triangles sont nécessaires
    asm.setMeshControls(regions=quarts, elemShape=QUAD_DOMINATED, technique=SWEEP)
    asm.seedPartInstance(regions=(inst,), size=P.TAILLE_GLOBALE, deviationFactor=0.1, minSizeFactor=0.1)

    # arêtes radiales : petit côté du biais du côté de la pointe (on lit l'orientation de chaque arête)
    v_pointe = _sommet(inst, A, 0.0, "pointe")
    debut, fin = [], []
    for (x, y) in G.points_aretes_radiales(A):
        e = _arete(inst, x, y, "arête radiale")
        (debut if e.getVertices()[0] == v_pointe.index else fin).append(e)
    asm.seedEdgeByBias(biasMethod=SINGLE, end1Edges=tuple(debut), end2Edges=tuple(fin),
                       ratio=RATIO_BIAIS, number=P.N_COUCHES, constraint=FINER)
    arcs = inst.edges.findAt(*[((x, y, 0.0),) for (x, y) in G.points_arcs(A)])
    asm.seedEdgeByNumber(edges=arcs, number=P.N_ARC, constraint=FINER)

    asm.setElementType(regions=(inst.faces,), elemTypes=(
        ElemType(elemCode=CPE8R, elemLibrary=STANDARD), ElemType(elemCode=CPE6, elemLibrary=STANDARD)))
    asm.generateMesh(regions=(inst,))

    # auto-vérifications
    types = {}
    for e in inst.elements:
        types[str(e.type)] = types.get(str(e.type), 0) + 1
    print("Éléments : %s" % types)
    if set(types) - set(["CPE8R", "CPE6"]):
        raise RuntimeError("Types d'éléments inattendus : %s (attendu : CPE8R et CPE6 seulement)" % types)
    n_noeuds = len(inst.nodes)
    print("NOEUDS %d" % n_noeuds)
    if n_noeuds > 1000:
        raise RuntimeError("%d nœuds : au-dessus de la limite Learning Edition (1000)" % n_noeuds)

    ys = sorted(round(n.coordinates[1], 5) for n in inst.nodes
                if abs(n.coordinates[0] - A) < 1e-6 and n.coordinates[1] > -1e-9)
    print("Nœuds au-dessus de la pointe (y, mm) : %s" % ys[:6])
    h1_attendu = G.h1_depuis_biais(RATIO_BIAIS)
    if len(ys) >= 3 and abs(ys[2] - h1_attendu) > 0.25 * h1_attendu:
        print("ATTENTION : 1er élément = %.3f mm au lieu de %.3f : biais inversé ou définition du ratio "
              "différente. Envoie-moi cette ligne." % (ys[2], h1_attendu))


# ----------------------------------------------------------------------------- bloc 6
def ecrire_inp():
    mdb.Job(name=NOM, model=MODELE, description="", type=ANALYSIS, memory=90, memoryUnits=PERCENTAGE,
            getMemoryFromAnalysis=True, explicitPrecision=SINGLE, nodalOutputPrecision=SINGLE,
            echoPrint=OFF, modelPrint=OFF, contactPrint=OFF, historyPrint=OFF, userSubroutine="",
            scratch="", resultsFormat=ODB)
    mdb.jobs[NOM].writeInput(consistencyChecking=OFF)
    mdb.saveAs(pathName=NOM)                  # modèle ouvrable dans CAE pour contrôle visuel
    print("ECRIT : %s.inp (et %s.cae)" % (NOM, NOM))


ETAPES = [
    (1, "géométrie", geometrie),
    (2, "matériau et assemblage", materiau_et_assemblage),
    (3, "fissure", fissure),
    (4, "couplages, step, charges, sorties", couplages_step_charges),
    (5, "maillage", maillage),
    (6, "écriture du .inp", ecrire_inp),
]

Mdb()
for numero, titre, fonction in ETAPES:
    if numero <= JUSQU_A:
        fonction()
        print("ETAPE %d OK : %s" % (numero, titre))
