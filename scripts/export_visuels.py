# Export des visuels du cas a/W = 0,5 depuis le .odb (Abaqus CAE, sans interface) :
#   abaqus cae noGUI=scripts/export_visuels.py
# Sorties dans OUT : maillage_pointe.png, S22_a050.png, frames/f000.png ... f060.png
import os
from abaqus import *
from abaqusConstants import *
import visualization

ODB = r'C:\abaqus_calculs\ct_a050.odb'
OUT = r'C:\abaqus_calculs\visuels'
FRAMES = os.path.join(OUT, 'frames')
for d in (OUT, FRAMES):
    if not os.path.exists(d):
        os.makedirs(d)

SF_MAX = 20.0           # facteur d'amplification de la deformee (a regler)
S22_MIN, S22_MAX = -100.0, 600.0   # echelle de couleur en MPa (pic en pointe : singularite)
N = 60                  # nombre d'images de la video

odb = session.openOdb(name=ODB)
vp = session.viewports[session.currentViewportName]
vp.setValues(displayedObject=odb)
od = vp.odbDisplay

# Image propre : sans bandeau de fenetre, sans texte Abaqus, sans triade
session.printOptions.setValues(rendition=COLOR, vpBackground=OFF, vpDecorations=OFF)
session.pngOptions.setValues(imageSize=(1920, 1080))
vp.viewportAnnotationOptions.setValues(title=OFF, state=OFF, triad=OFF)

# 1. Maillage (toutes les aretes d'elements visibles)
od.display.setValues(plotState=(UNDEFORMED,))
od.commonOptions.setValues(renderStyle=WIREFRAME, visibleEdges=ALL)
vp.view.fitView()
session.printToFile(fileName=os.path.join(OUT, 'maillage_complet'),
                    format=PNG, canvasObjects=(vp,))
# Le zoom sur la pointe se fait a la main dans CAE, puis File > Print.

# 2. Contrainte S22 sur la deformee
od.display.setValues(plotState=(CONTOURS_ON_DEF,))
od.setPrimaryVariable(variableLabel='S', outputPosition=INTEGRATION_POINT,
                      refinement=(COMPONENT, 'S22'))
od.contourOptions.setValues(maxAutoCompute=OFF, maxValue=S22_MAX,
                            minAutoCompute=OFF, minValue=S22_MIN,
                            numIntervals=14)
od.commonOptions.setValues(renderStyle=FILLED, visibleEdges=NONE,
                           deformationScaling=UNIFORM, uniformScaleFactor=SF_MAX)
try:
    # legende en haut a droite pour ne pas recouvrir l'eprouvette
    vp.viewportAnnotationOptions.setValues(legendPosition=(70, 95))
except Exception as e:
    print('Position de la legende non modifiee : %s' % e)
vp.view.fitView()
session.printToFile(fileName=os.path.join(OUT, 'S22_a050'),
                    format=PNG, canvasObjects=(vp,))

# 3. Images de la video : la fissure s'ouvre de 0 a SF_MAX
for i in range(N + 1):
    sf = max(0.01, SF_MAX * i / float(N))
    od.commonOptions.setValues(uniformScaleFactor=sf)
    session.printToFile(fileName=os.path.join(FRAMES, 'f%03d' % i),
                        format=PNG, canvasObjects=(vp,))
print('Termine : ' + OUT)
