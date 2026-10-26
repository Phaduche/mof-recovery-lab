"""200-point phosphate-recovery score used in both stages (A: database, B: modified MOFs).

Stability (100) is absolute: 100 × the RF water-stability probability.
Capture (40), desorption (35) and reuse (25) are relative: each raw value is turned into a z-score
against the stage-A database and mapped to points with Φ(z/2) (the normal CDF, widened so the very
top of the database still has room to improve), so a B-stage MOF is judged on exactly the same scale
as the database it came from.
"""
import math
import numpy as np
import pandas as pd

WEIGHTS = {'stability': 100, 'capture': 40, 'desorption': 35, 'reuse': 25}
LABELS = {'stability': '안정성', 'capture': '포집', 'desorption': '탈착', 'reuse': '재사용'}
RELATIVE = ['capture', 'desorption', 'reuse']
Z_SPREAD = 2.0

LANTHANIDES = {'La', 'Ce', 'Pr', 'Nd', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu'}
ALKALI = {'Li', 'Na', 'K', 'Rb', 'Cs'}
# How strongly the metal node binds phosphate (M–O–P ligand exchange). 0–1.
AFFINITY = {'Zr': 1.0, 'Hf': 1.0, 'Ce': .95, 'La': 1.0, 'Th': .9, 'Y': .85, 'Fe': .85, 'Al': .8,
            'Ti': .75, 'Sc': .7, 'Cr': .6, 'Ga': .6, 'Ca': .6, 'In': .5, 'V': .5, 'Sr': .5, 'Ba': .5,
            'Cu': .45, 'Mg': .4, 'Mn': .4, 'Pb': .4, 'Zn': .35, 'Co': .35, 'Ni': .35, 'Ag': .3, 'Cd': .25}
# How easily the bound phosphate is released by mild base / salt. Very strong binders
# (lanthanide, calcium phosphates are nearly insoluble) release poorly. 0–1.
REVERSIBILITY = {'Fe': .8, 'Al': .8, 'Ga': .75, 'Zr': .7, 'Hf': .7, 'Cr': .7, 'In': .7, 'Zn': .7,
                 'Ti': .65, 'Cu': .65, 'Co': .65, 'Ni': .65, 'Sc': .6, 'Mg': .6, 'Mn': .6, 'Cd': .6,
                 'Ce': .55, 'Th': .5, 'Y': .35, 'La': .3, 'Ca': .25}
GROUP_CAPTURE = {'+': .15, '0': 0.0, '-': -.25}

def _metals(value):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return []
    return [m for m in str(value).replace(',', ' ').split() if m]

def _table(table, metal, lanthanide, alkali, default):
    if metal in table:
        return table[metal]
    if metal in LANTHANIDES:
        return lanthanide
    if metal in ALKALI:
        return alkali
    return default

def _num(x, default):
    return default if x is None or (isinstance(x, float) and math.isnan(x)) else float(x)

def raw_scores(water_prob, metal, pld_A=None, gsa_m2_g=None, open_metal_site=None, group_effect='0',
               thermal_C=None, base_stable=None):
    """Raw (unscaled) capture / desorption / reuse values for one MOF."""
    metals = _metals(metal)
    affinity = max((_table(AFFINITY, m, .9, .05, .3) for m in metals), default=.3)
    reversibility = min((_table(REVERSIBILITY, m, .35, .9, .6) for m in metals), default=.6)
    gsa, pld, p = _num(gsa_m2_g, 0.0), _num(pld_A, 0.0), _num(water_prob, 0.0)
    surface = min(1.0, math.log10(1 + gsa) / math.log10(1 + 4000))
    access = 1.0 if pld >= 4.8 else 0.6          # small windows: surface / defect sites only
    capture = affinity * (0.6 + 0.4 * surface) * access + GROUP_CAPTURE.get(group_effect or '0', 0.0) \
        + (0.1 if open_metal_site is True else 0.0)
    desorption = reversibility * (0.7 + 0.3 * min(1.0, pld / 8))
    thermal = min(1.0, max(0.0, (_num(thermal_C, 350.0) - 250) / 250))
    base = 1.0 if base_stable is True else (0.0 if base_stable is False else 0.5)
    reuse = 0.6 * p + 0.25 * thermal + 0.15 * base
    return {'capture_raw': capture, 'desorption_raw': desorption, 'reuse_raw': reuse}

def reference_stats(frame):
    """Mean / sd of each raw value over the stage-A database."""
    return {k: (float(frame[f'{k}_raw'].mean()), float(frame[f'{k}_raw'].std(ddof=0)) or 1.0) for k in RELATIVE}

def _cdf(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))

def score(frame, stats):
    """Add point columns, total (200) and the balance z used to break ties. Returns a new frame."""
    out = frame.copy()
    out['stability'] = WEIGHTS['stability'] * out['water_prob'].clip(0, 1)
    for k in RELATIVE:
        mu, sd = stats[k]
        out[f'{k}_z'] = (out[f'{k}_raw'] - mu) / sd
        out[k] = [WEIGHTS[k] * _cdf(z / Z_SPREAD) for z in out[f'{k}_z']]
    out['total'] = sum(out[k] for k in WEIGHTS)
    norm = np.column_stack([out[k] / w for k, w in WEIGHTS.items()])
    mean = norm.mean(axis=1)
    out['balance_cv'] = np.where(mean > 0, norm.std(axis=1) / np.where(mean > 0, mean, 1), 0.0)
    return out

def rank_agreement(predicted, measured, minimum=3):
    """Spearman ρ between AI scores and measurements (rows with a measurement only); None if too few."""
    m = pd.to_numeric(pd.Series(measured), errors='coerce').reset_index(drop=True)
    p = pd.Series(predicted, dtype=float).reset_index(drop=True)
    ok = m.notna()
    if ok.sum() < minimum:
        return None
    return float(p[ok].rank().corr(m[ok].rank()))   # Spearman = Pearson on ranks

def rank(frame):
    """Highest total first; equal totals (to 0.1) → lower imbalance first."""
    f = frame.assign(_t=frame['total'].round(1))
    cv = f['balance_cv']
    f['balance_z'] = (cv - cv.mean()) / (cv.std(ddof=0) or 1.0)
    f = f.sort_values(['_t', 'balance_cv'], ascending=[False, True]).drop(columns='_t')
    f['rank'] = range(1, len(f) + 1)
    return f.reset_index(drop=True)
