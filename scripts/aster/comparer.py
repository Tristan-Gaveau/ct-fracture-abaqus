# -*- coding: utf-8 -*-
"""Compare K de Code_Aster à celui d'Abaqus et à l'ASTM E399, et trace la figure.

K Code_Aster = moyenne de K1 sur les couronnes retenues (on saute la première, comme le contour 1 d'Abaqus).
Dispersion = (max - min) / moyenne sur ces couronnes.

Usage : python scripts/aster/comparer.py [--dossier C:/aster_calculs] [--sortie results]
"""
import argparse
import csv
import glob
import math
import os

COEF = 1.0 / math.sqrt(1000.0)         # MPa*sqrt(mm) -> MPa*sqrt(m)
PREMIERE_RETENUE = 2                   # on saute la couronne 1


def lire_couronnes(chemin):
    with open(chemin, newline="", encoding="utf-8") as f:
        return [{k: float(v) for k, v in ligne.items()} for ligne in csv.DictReader(f)]


def resumer(lignes, premiere=PREMIERE_RETENUE):
    """Renvoie (K moyen en MPa*sqrt(m), dispersion en %, nombre de couronnes retenues)."""
    k = [l["K1"] for l in lignes if l["couronne"] >= premiere]
    if not k:
        raise ValueError("aucune couronne retenue")
    moy = sum(k) / len(k)
    return moy * COEF, 100.0 * (max(k) - min(k)) / moy, len(k)


def lire_abaqus(chemin):
    with open(chemin, newline="", encoding="utf-8") as f:
        return {round(float(l["alpha"]), 2): l for l in csv.DictReader(f)}


def comparer(dossier, chemin_abaqus, sortie):
    abq = lire_abaqus(chemin_abaqus)
    lignes = []
    for alpha, ab in sorted(abq.items()):
        csv_cas = os.path.join(dossier, "cas_a%03d" % round(alpha * 100), "resultats.csv")
        if not os.path.exists(csv_cas):
            continue
        k_aster, disp, n = resumer(lire_couronnes(csv_cas))
        k_abq, k_astm = float(ab["K_FE_MPa_sqrt_m"]), float(ab["K_ASTM_MPa_sqrt_m"])
        lignes.append({
            "alpha": alpha, "K_Aster": k_aster, "K_Abaqus": k_abq, "K_ASTM": k_astm,
            "ecart_Aster_Abaqus_pct": 100.0 * (k_aster / k_abq - 1.0),
            "ecart_Aster_ASTM_pct": 100.0 * (k_aster / k_astm - 1.0),
            "dispersion_couronnes_pct": disp, "n_couronnes": n})
    if not lignes:
        raise SystemExit("aucun resultats.csv trouvé dans %s" % dossier)

    os.makedirs(os.path.join(sortie, "figures"), exist_ok=True)
    champs = list(lignes[0].keys())
    with open(os.path.join(sortie, "K_comparaison_aster.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=champs)
        w.writeheader()
        for l in lignes:
            w.writerow({k: ("%.4f" % v if isinstance(v, float) else v) for k, v in l.items()})

    dans_plage = [l for l in lignes if 0.4 - 1e-9 <= l["alpha"] <= 0.7 + 1e-9]
    pire = max((abs(l["ecart_Aster_Abaqus_pct"]) for l in dans_plage), default=float("nan"))
    with open(os.path.join(sortie, "K_comparaison_aster.md"), "w", encoding="utf-8") as f:
        f.write("# Comparaison Code_Aster / Abaqus / ASTM E399\n\n")
        f.write("K en MPa·√m. K Code_Aster = moyenne de K1 sur les couronnes 2 à N (la couronne 1 est écartée, "
                "comme le contour 1 d'Abaqus).\n\n")
        f.write("| a/W | K Aster | K Abaqus | K ASTM | Aster/Abaqus (%) | Aster/ASTM (%) | dispersion couronnes (%) |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for l in lignes:
            f.write("| %.2f | %.3f | %.3f | %.3f | %+.2f | %+.2f | %.2f |\n" % (
                l["alpha"], l["K_Aster"], l["K_Abaqus"], l["K_ASTM"],
                l["ecart_Aster_Abaqus_pct"], l["ecart_Aster_ASTM_pct"], l["dispersion_couronnes_pct"]))
        f.write("\nCritère fixé à l'avance : écart Aster/Abaqus inférieur à 1 %% pour a/W de 0,4 à 0,7. "
                "Pire écart sur cette plage : %.2f %% -> %s.\n" % (pire, "OK" if pire < 1.0 else "NON ATTEINT"))

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib absent : figure non tracée")
        return lignes
    x = [l["alpha"] for l in lignes]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(7, 6), sharex=True, gridspec_kw={"height_ratios": [3, 2]})
    a1.plot(x, [l["K_ASTM"] for l in lignes], "k-", label="ASTM E399")
    a1.plot(x, [l["K_Abaqus"] for l in lignes], "o", mfc="none", label="Abaqus (J)")
    a1.plot(x, [l["K_Aster"] for l in lignes], "x", label="Code_Aster (G-thêta)")
    a1.set_ylabel("K (MPa·√m)")
    a1.legend()
    a1.grid(alpha=0.3)
    a2.axhline(0, color="k", lw=0.8)
    a2.axhspan(-1, 1, color="green", alpha=0.1, label="±1 %")
    a2.plot(x, [l["ecart_Aster_Abaqus_pct"] for l in lignes], "s-", label="Aster / Abaqus")
    a2.plot(x, [l["ecart_Aster_ASTM_pct"] for l in lignes], "^--", label="Aster / ASTM")
    a2.set_xlabel("a / W")
    a2.set_ylabel("écart (%)")
    a2.legend()
    a2.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(sortie, "figures", "K_vs_a_comparaison.png"), dpi=150)
    return lignes


def convergence(dossier, sortie):
    """Étude de maillage à a/W = 0,5 : K moyen pour chaque maillage conv_*."""
    cas = sorted(glob.glob(os.path.join(dossier, "conv_*", "resultats.csv")))
    if not cas:
        return None
    res = [(os.path.basename(os.path.dirname(c)),) + resumer(lire_couronnes(c)) for c in cas]
    with open(os.path.join(sortie, "convergence_aster.md"), "w", encoding="utf-8") as f:
        f.write("# Convergence de maillage Code_Aster (a/W = 0,5)\n\n| maillage | K (MPa·√m) | dispersion couronnes (%) | couronnes | écart au maillage précédent (%) |\n|---|---|---|---|---|\n")
        prec = None
        for nom, k, d, n in res:
            ecart = "" if prec is None else "%+.3f" % (100.0 * (k / prec - 1.0))
            f.write("| %s | %.4f | %.2f | %d | %s |\n" % (nom, k, d, n, ecart))
            prec = k
        if len(res) >= 2:
            e = abs(100.0 * (res[-1][1] / res[-2][1] - 1.0))
            f.write("\nCritère : écart entre les deux derniers maillages inférieur à 0,2 %% -> %.3f %% : %s.\n"
                    % (e, "OK" if e < 0.2 else "NON ATTEINT"))
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dossier", default=r"C:\aster_calculs")
    ap.add_argument("--abaqus", default=os.path.join("results", "K_vs_a.csv"))
    ap.add_argument("--sortie", default="results")
    a = ap.parse_args()
    if glob.glob(os.path.join(a.dossier, "cas_a*", "resultats.csv")):
        for l in comparer(a.dossier, a.abaqus, a.sortie):
            print("a/W %.2f  K_Aster %.3f  K_Abaqus %.3f  écart %+.2f %%  dispersion %.2f %%"
                  % (l["alpha"], l["K_Aster"], l["K_Abaqus"], l["ecart_Aster_Abaqus_pct"], l["dispersion_couronnes_pct"]))
    for nom, k, d, n in (convergence(a.dossier, a.sortie) or []):
        print("%s  K %.4f MPa*sqrt(m)  dispersion %.2f %%  (%d couronnes)" % (nom, k, d, n))
