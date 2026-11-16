"""Vérifie K_max < K_Ic sur l'intervalle d'étude (formule ASTM E399)."""
import numpy as np
import params as p


def k_astm(a_mm):
    """K en MPa√m, avec P, B, W, a en N et mm."""
    al = np.asarray(a_mm) / p.W
    f = (2 + al) * (0.886 + 4.64*al - 13.32*al**2 + 14.72*al**3
                    - 5.6*al**4) / (1 - al)**1.5
    k_mpa_sqrt_mm = p.P_REEL / (p.B_REEL * np.sqrt(p.W)) * f
    return k_mpa_sqrt_mm / np.sqrt(1000.0)  # MPa√mm -> MPa√m


if __name__ == "__main__":
    if p.K_IC is None:
        raise SystemExit("K_IC non renseigné dans params.py")
    a_fin = p.A_FINAL_SUR_W * p.W
    k_max = float(k_astm(a_fin))
    if not 30.0 < k_max < 50.0:
        raise SystemExit(f"K_max = {k_max:.1f} MPa√m hors de l'ordre attendu : erreur d'unités ?")
    print(f"K_max à a_final = {k_max:.1f} MPa√m")
    for nom, kic in (("K_Ic retenu", p.K_IC),
                     ("borne basse", p.K_IC_PLAGE[0]),
                     ("borne haute", p.K_IC_PLAGE[1])):
        print(f"{nom:12s} K_Ic = {kic:5.1f}  K_max/K_Ic = {k_max / kic:.2f}")
    print("OK" if k_max < min(p.K_IC, p.K_IC_PLAGE[0]) else "ATTENTION : K_max >= K_Ic")