"""Aplatit des PNG a fond transparent sur fond blanc (ecrase les fichiers).

Usage : python scripts/aplatir_fond.py fichier.png dossier_de_png [...]
"""
import sys
from pathlib import Path

from PIL import Image


def aplatir(chemin):
    image = Image.open(chemin).convert("RGBA")
    fond = Image.new("RGBA", image.size, (255, 255, 255, 255))
    fond.alpha_composite(image)
    fond.convert("RGB").save(chemin)


def main(arguments):
    for argument in arguments:
        cible = Path(argument)
        fichiers = sorted(cible.glob("*.png")) if cible.is_dir() else [cible]
        for fichier in fichiers:
            aplatir(fichier)
        print(f"{len(fichiers)} image(s) aplatie(s) : {argument}")


if __name__ == "__main__":
    main(sys.argv[1:])
