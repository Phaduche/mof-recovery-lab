"""Stage B: modify the stage-A top 3 (linker functional groups, node metal) and rescore out of 200.

    python -m scripts.build_stage_b --ws24 /path/to/unzipped     # needs pymatgen (structures only)

Stability of a modified MOF = parent RF probability adjusted with the same data the rest of the
project uses:
  * linker group X: logit(p) + [logit RF(UiO-66-X) − logit RF(UiO-66)]; pore / surface scaled like UiO-66 → UiO-66-X
  * node metal M: × exp(−max(ΔE_swap, 0) / 1 eV), ×0.1 if the metal's charge doesn't match Zr⁴⁺,
    with ΔE_swap from the CHGNet metal-swap run on the Zr₆ node (data/metal_swap/results.csv)
Capture / desorption / reuse are recomputed with moflab.pipeline against the stage-A statistics.
"""
import argparse, gzip, json, math
from pathlib import Path
import numpy as np
import pandas as pd
from moflab import pipeline

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/pipeline'
STRUCT = OUT / 'structures'

# group label -> (variant key used for the data-driven deltas, display suffix)
LINKERS = {'NH2': ('UiO-66-NH2', '–NH₂'), 'OH': ('MOF-804', '–OH'), 'NO2': ('UiO-66-NO2', '–NO₂'),
           'COOH': ('UiO-66-CO2H', '–COOH'), 'SO3H': ('UiO-66-SO3H', '–SO₃H'), 'F': ('UiO-66-F', '–F'),
           'CH3': ('UiO-66-MM', '–CH₃')}
METALS = ['Hf', 'Ce', 'Th', 'Ti', 'Fe', 'Al']

# substituent geometry: (first atom, C–X bond, [(element, bond from X, in-plane angle°, out-of-plane°), ...])
GROUPS = {'NH2': ('N', 1.38, [('H', 1.01, 60, 0), ('H', 1.01, -60, 0)]),
          'OH': ('O', 1.36, [('H', 0.97, 60, 0)]),
          'F': ('F', 1.35, []),
          'NO2': ('N', 1.47, [('O', 1.22, 60, 0), ('O', 1.22, -60, 0)]),
          'COOH': ('C', 1.49, [('O', 1.25, 60, 0), ('O', 1.32, -60, 0)]),
          'SO3H': ('S', 1.77, [('O', 1.45, 0, 70.5), ('O', 1.45, 120, 70.5), ('O', 1.45, 240, 70.5)]),
          'CH3': ('C', 1.50, [('H', 1.09, 0, 70.5), ('H', 1.09, 120, 70.5), ('H', 1.09, 240, 70.5)])}

def logit(p):
    p = min(max(p, 1e-6), 1 - 1e-6)
    return math.log(p / (1 - p))

def shift(p, delta):
    """Move a probability by `delta` in log-odds, so it can approach but never reach 0 or 1."""
    return 1 / (1 + math.exp(-(logit(p) + delta)))

def parent_cif(row, ws):
    kind, key = row.cif_ref.split(':', 1)
    if kind == 'core':
        return gzip.open(ROOT / 'data/cifs' / f'{key}.cif.gz', 'rt').read()
    if kind == 'variant':
        return (ROOT / 'data/variants' / f'{key}.cif').read_text()
    return (ws / 'data_sets/WS24s/CIFs' / f'{key}.cif').read_text()

def functionalize(structure, group, min_sep=5.0):
    """Replace roughly one aromatic H per ring with `group`, built in the ring plane."""
    from pymatgen.core import Structure
    s = structure.copy()
    first, d_cx, subs = GROUPS[group]
    cart = s.cart_coords
    chosen, new_species, new_coords, drop = [], [], [], []
    for i, site in enumerate(s):
        if site.specie.symbol != 'H':
            continue
        nb = s.get_neighbors(site, 1.2)
        if len(nb) != 1 or nb[0].specie.symbol != 'C':
            continue
        c = nb[0]
        ring = [n for n in s.get_neighbors(c, 1.6) if n.specie.symbol == 'C']
        if len(ring) != 2 or any(np.linalg.norm(cart[i] - cart[j]) < min_sep for j in chosen):
            continue
        u = site.coords - c.coords
        u /= np.linalg.norm(u)
        n = np.cross(ring[0].coords - c.coords, ring[1].coords - c.coords)
        n /= np.linalg.norm(n)
        v = np.cross(n, u)
        x = c.coords + d_cx * u
        atoms = [(first, x)]
        for el, d, phi, tilt in subs:
            if tilt:   # tetrahedral fan around the C–X axis
                t, p = math.radians(tilt), math.radians(phi)
                direction = math.cos(t) * u + math.sin(t) * (math.cos(p) * v + math.sin(p) * n)
            else:      # planar, in the ring plane
                p = math.radians(phi)
                direction = math.cos(p) * u + math.sin(p) * v
            atoms.append((el, x + d * direction))
        chosen.append(i)
        drop.append(i)
        for el, pos in atoms:
            new_species.append(el)
            new_coords.append(pos)
    s.remove_sites(drop)
    for el, pos in zip(new_species, new_coords):
        s.append(el, pos, coords_are_cartesian=True)
    return s, len(chosen)

def main():
    from pymatgen.core import Structure
    from pymatgen.io.cif import CifWriter
    ap = argparse.ArgumentParser()
    ap.add_argument('--ws24', type=Path, required=True)
    ws = ap.parse_args().ws24
    a = pd.read_parquet(OUT / 'stage_a.parquet')
    stats = json.loads((OUT / 'stats.json').read_text())
    var = pd.read_csv(ROOT / 'data/variants/variants.csv').set_index('key')
    swap = pd.read_csv(ROOT / 'data/metal_swap/results.csv').set_index('metal')
    base = var.loc['UiO-66']
    STRUCT.mkdir(parents=True, exist_ok=True)
    rows = []
    for parent in a.head(3).itertuples():
        pid = parent.id.split(':', 1)[1]
        structure = Structure.from_str(parent_cif(parent, ws), fmt='cif')
        CifWriter(structure).write_file(STRUCT / f'{pid}.cif')
        common = dict(parent=parent.name, parent_id=parent.id, thermal_C=parent.thermal_C,
                      open_metal_site=parent.open_metal_site)
        for group, (key, suffix) in LINKERS.items():
            v = var.loc[key]
            mod, count = functionalize(structure, group)
            CifWriter(mod).write_file(STRUCT / f'{pid}__{group}.cif')
            rows.append({**common, 'id': f'{pid}__{group}', 'name': f'{parent.name} {suffix}', 'change': '링커',
                         'detail': f'{suffix} ×{count}', 'metal': parent.metal, 'group_effect': v.effect,
                         'water_prob': shift(parent.water_prob, logit(v.rf_in_sample) - logit(base.rf_in_sample)),
                         'pld_A': parent.pld_A * float(np.clip(v.pld_A / base.pld_A, .5, 1)),
                         'gsa_m2_g': parent.gsa_m2_g * float(np.clip(v.gsa_m2_g / base.gsa_m2_g, .5, 1)),
                         'base_stable': parent.base_stable})
        for metal in METALS:
            s = swap.loc[metal]
            mod = structure.copy()
            mod.replace_species({'Zr': metal})
            CifWriter(mod).write_file(STRUCT / f'{pid}__{metal}.cif')
            penalty = math.exp(-max(s.swap_energy_eV, 0) / 1.0) * (1 if s.charge_balanced else 0.1)
            rows.append({**common, 'id': f'{pid}__{metal}', 'name': f'{parent.name} (Zr→{metal})', 'change': '원소',
                         'detail': f'Zr → {metal} · ΔE {s.swap_energy_eV:+.2f} eV', 'metal': metal,
                         'group_effect': parent.group_effect, 'water_prob': parent.water_prob * penalty,
                         'pld_A': parent.pld_A, 'gsa_m2_g': parent.gsa_m2_g, 'base_stable': None})
        print(parent.name, 'done', flush=True)
    b = pd.DataFrame(rows)
    raws = [pipeline.raw_scores(r.water_prob, r.metal, r.pld_A, r.gsa_m2_g, r.open_metal_site, r.group_effect,
                                r.thermal_C, r.base_stable) for r in b.itertuples()]
    b = pipeline.score(pd.concat([b, pd.DataFrame(raws)], axis=1), stats)
    parents = a.head(3).assign(parent=a.head(3).name, parent_id=a.head(3).id, change='원본', detail='수정 없음',
                               id=[i.split(':', 1)[1] for i in a.head(3).id])
    final = pipeline.rank(pd.concat([parents[b.columns.intersection(parents.columns)], b], ignore_index=True))
    final.to_parquet(OUT / 'stage_b.parquet', index=False)
    best = final.iloc[0]
    (OUT / 'final.json').write_text(json.dumps({'id': best.id, 'name': best['name'], 'parent': best.parent,
                                                'total': round(float(best.total), 1)}, ensure_ascii=False, indent=1))
    print(final[['rank', 'name', 'change', 'total', 'stability', 'capture', 'desorption', 'reuse']].head(12).round(1).to_string(index=False))

if __name__ == '__main__':
    main()
