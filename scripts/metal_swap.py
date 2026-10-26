"""Swap the Zr6 node metal of UiO-66-NH2 and compare energies with a universal ML potential (CHGNet).

Needs extra packages that the web app does not:  pip install chgnet
    python -m scripts.metal_swap                 # all metals in METALS, ~1–3 min each on a laptop

For every metal M, all 6 Zr are replaced and the cell + atoms are relaxed. The swap energy is

    ΔE_swap = [E(M-MOF) − E(Zr-MOF) − 6 (μ_M − μ_Zr)] / 6      (eV per metal atom)

where μ is the energy per atom of the metal's own relaxed bulk crystal. Lower = the node prefers M
more relative to Zr. CHGNet approximates DFT (PBE/PBE+U, Materials Project) and does not fix charge:
a +1 metal in a node built for +4 is simply an unphysical, charge-unbalanced structure.
"""
import json, warnings
from pathlib import Path
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/variants/UiO-66-NH2.cif'
OUT = ROOT / 'data/metal_swap'

# symbol: (usual oxidation state, Shannon ionic radius Å CN8 where available, bulk lattice, a, c, UiO-66 analogue reported)
METALS = {
    'Zr': (4, 0.84, 'hcp', 3.23, 5.15, '보고됨 (원조)'),
    'Hf': (4, 0.83, 'hcp', 3.19, 5.05, '보고됨'),
    'Ce': (4, 0.97, 'fcc', 5.16, None, '보고됨'),
    'Th': (4, 1.05, 'fcc', 5.08, None, '보고됨'),
    'Ti': (4, 0.74, 'hcp', 2.95, 4.68, '부분 치환만'),
    'Al': (3, 0.54, 'fcc', 4.05, None, '없음'),
    'Fe': (3, 0.78, 'bcc', 2.87, None, '없음'),
    'Mg': (2, 0.89, 'hcp', 3.21, 5.21, '없음'),
    'Zn': (2, 0.90, 'hcp', 2.66, 4.95, '없음'),
    'Ca': (2, 1.12, 'fcc', 5.58, None, '없음'),
    'Na': (1, 1.18, 'bcc', 4.29, None, '없음'),
    'K':  (1, 1.51, 'bcc', 5.33, None, '없음'),
}

def bulk(symbol, kind, a, c):
    from pymatgen.core import Lattice, Structure
    if kind == 'hcp':
        return Structure(Lattice.hexagonal(a, c), [symbol] * 2, [[1/3, 2/3, 1/4], [2/3, 1/3, 3/4]])
    if kind == 'bcc':
        return Structure(Lattice.cubic(a), [symbol] * 2, [[0, 0, 0], [.5, .5, .5]])
    return Structure.from_spacegroup('Fm-3m', Lattice.cubic(a), [symbol], [[0, 0, 0]])

def mean_metal_o(structure, metal):
    d = []
    for i, site in enumerate(structure):
        if site.specie.symbol == metal:
            d += [n.nn_distance for n in structure.get_neighbors(site, 3.2) if n.specie.symbol == 'O']
    return float(np.mean(d)) if d else float('nan')

def main():
    from pymatgen.core import Structure
    from pymatgen.io.cif import CifWriter
    from chgnet.model import CHGNet, StructOptimizer
    opt = StructOptimizer()
    cache = OUT / 'cache'
    cache.mkdir(parents=True, exist_ok=True)
    base = Structure.from_file(SOURCE)
    rows = []
    for metal, (ox, radius, kind, a, c, reported) in METALS.items():
        done = cache / f'{metal}.json'
        if done.exists():   # resumable: each metal is saved as soon as it finishes
            rows.append(json.loads(done.read_text()))
            continue
        b = opt.relax(bulk(metal, kind, a, c), fmax=0.05, steps=300, relax_cell=True, verbose=False)
        mu = float(b['trajectory'].energies[-1]) / len(b['final_structure'])
        s = base.copy()
        s.replace_species({'Zr': metal})
        cif = OUT / f'UiO-66-NH2_{metal}.cif'
        if cif.exists():    # relaxed earlier but the run stopped before saving energies
            final, steps = Structure.from_file(cif), None
            energy = float(CHGNet.load().predict_structure(final)['e']) * len(final)
        else:
            r = opt.relax(s, fmax=0.1, steps=500, relax_cell=True, verbose=False)
            final, steps = r['final_structure'], len(r['trajectory'].energies)
            energy = float(r['trajectory'].energies[-1])
            CifWriter(final).write_file(cif)
        disp = np.linalg.norm(final.cart_coords - s.cart_coords, axis=1)
        row = {'metal': metal, 'oxidation_state': ox, 'ionic_radius_A': radius, 'reported': reported,
               'charge_balanced': ox == 4, 'node_charge_vs_zr': 6 * (ox - 4),
               'energy_eV': energy, 'mu_bulk_eV': mu, 'steps': steps,
               'volume_change_pct': 100 * (final.volume / s.volume - 1),
               'max_displacement_A': float(disp.max()), 'metal_o_A': mean_metal_o(final, metal)}
        done.write_text(json.dumps(row))
        rows.append(row)
        print(metal, round(energy, 3), round(row['volume_change_pct'], 1), flush=True)
    df = pd.DataFrame(rows)
    ref = df.set_index('metal').loc['Zr']
    df['swap_energy_eV'] = (df.energy_eV - ref.energy_eV - 6 * (df.mu_bulk_eV - ref.mu_bulk_eV)) / 6
    df.to_csv(OUT / 'results.csv', index=False)
    (OUT / 'meta.json').write_text(json.dumps({
        'source_structure': SOURCE.name, 'potential': 'CHGNet 0.3.0 (Materials Project trajectory, PBE/PBE+U)',
        'relax': {'fmax_eV_A': 0.1, 'max_steps': 500, 'cell': True}, 'bulk_reference': 'relaxed elemental crystal'},
        ensure_ascii=False, indent=1))
    print(df[['metal', 'swap_energy_eV', 'volume_change_pct', 'max_displacement_A']].to_string())

if __name__ == '__main__':
    main()
