"""Draw the parts used by the AI 예측 page: one metal node and one linker per entry in data/predict/catalog.json.

Nodes are cut out of real crystal structures already in this repo (CoRE MOF 2025 CIFs, the UiO-66 and
MIL-100(Fe) files): the metal atoms of one node, the O/N atoms bonded to them, H on bridging OH, and the
first carbon of each linker as a stub that shows where linkers attach. Linkers are built in 3D from their
SMILES with RDKit (ETKDG + MMFF). Output: data/predict/nodes/<id>__<metal>.sdf (one per metal the node is
made with) and data/predict/linkers/<id>.sdf.

Run once after editing the catalog (needs rdkit and pymatgen, which the web app itself does not use):
    pip install rdkit pymatgen
    python -m scripts.build_predict_assets
"""
import gzip, json, warnings
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUT = DATA / 'predict'
BOND = {'O': 2.6, 'N': 2.3}      # metal–ligand atom
METAL_METAL = 3.0                # paddlewheel Cu–Cu ≈ 2.6 Å; Zr–Zr (3.5 Å) is reached through μ3-O instead


def load_structure(rel):
    from pymatgen.core import Structure
    path = DATA / rel
    text = gzip.open(path, 'rt').read() if path.suffix == '.gz' else path.read_text(errors='replace')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        return Structure.from_str(text, fmt='cif')


def cut_node(structure, metal, max_metals):
    """Breadth-first walk from one metal over metal–O/N–metal bridges (and short metal–metal contacts)."""
    from pymatgen.core import PeriodicSite
    lattice = structure.lattice
    start = next(s for s in structure if s.specie.symbol == metal)
    atoms, seen = [], set()

    def add(symbol, coords):
        key = tuple(np.round(coords, 2))
        if key in seen:
            return False
        seen.add(key)
        atoms.append((symbol, np.array(coords)))
        return True

    def site(symbol, coords):
        return PeriodicSite(symbol, coords, lattice, coords_are_cartesian=True)

    add(metal, start.coords)
    queue, n_metals = [start.coords], 1
    while queue:
        m = queue.pop(0)
        for nb in structure.get_neighbors(site(metal, m), 3.2):
            el, d = nb.specie.symbol, np.linalg.norm(nb.coords - m)
            if el == metal and d <= METAL_METAL and n_metals < max_metals and add(el, nb.coords):
                n_metals += 1
                queue.append(nb.coords)
            if el not in BOND or d > BOND[el]:
                continue
            add(el, nb.coords)
            for nb2 in structure.get_neighbors(site(el, nb.coords), 2.7):
                el2, d2 = nb2.specie.symbol, np.linalg.norm(nb2.coords - nb.coords)
                if el2 == metal and d2 <= BOND[el] and n_metals < max_metals and add(el2, nb2.coords):
                    n_metals += 1               # bridging O joins this metal to the node
                    queue.append(nb2.coords)
                elif el2 == 'H' and d2 <= 1.15:
                    add('H', nb2.coords)        # μ-OH hydrogen
                elif el2 == 'C' and d2 <= 1.45:
                    add('C', nb2.coords)        # linker stub
    center = np.mean([c for s, c in atoms if s == metal], axis=0)
    return [(s, c - center) for s, c in atoms]


LIGAND_BOND = {('C', 'O'): 1.45, ('C', 'N'): 1.5, ('C', 'C'): 1.6, ('H', 'O'): 1.15, ('C', 'H'): 1.15}


def molblock(atoms, title, metal):
    """V2000 mol block with explicit bonds, so the viewer draws metal–O / metal–N sticks too."""
    bonds = []
    for i, (a, ca) in enumerate(atoms):
        for j in range(i + 1, len(atoms)):
            b, cb = atoms[j]
            d = np.linalg.norm(ca - cb)
            if metal in (a, b):
                other = b if a == metal else a
                ok = other in BOND and d <= BOND[other]
            else:
                ok = d <= LIGAND_BOND.get(tuple(sorted((a, b))), 0)
            if ok:
                bonds.append((i + 1, j + 1))
    lines = [title, '  build_predict_assets', '', f'{len(atoms):3d}{len(bonds):3d}  0  0  0  0  0  0  0  0999 V2000']
    lines += [f'{x:10.4f}{y:10.4f}{z:10.4f} {s:<3s} 0  0  0  0  0  0  0  0  0  0  0  0' for s, (x, y, z) in atoms]
    lines += [f'{i:3d}{j:3d}  1  0' for i, j in bonds]
    return '\n'.join(lines) + '\nM  END\n$$$$\n'


def build_linker(smiles):
    from rdkit import Chem
    from rdkit.Chem import AllChem
    mol = Chem.AddHs(Chem.MolFromSmiles(smiles))
    params = AllChem.ETKDGv3()
    params.randomSeed = 7
    if AllChem.EmbedMolecule(mol, params) != 0:
        raise ValueError(f'3D 좌표를 만들지 못했습니다: {smiles}')
    AllChem.MMFFOptimizeMolecule(mol, maxIters=2000)
    return Chem.MolToMolBlock(mol)


def main():
    catalog = json.loads((OUT / 'catalog.json').read_text())
    (OUT / 'nodes').mkdir(exist_ok=True)
    (OUT / 'linkers').mkdir(exist_ok=True)
    for node in catalog['nodes']:
        src = node['source']
        atoms = cut_node(load_structure(src['cif']), src['metal'], src['max_metals'])
        metals = sum(1 for s, _ in atoms if s == src['metal'])
        for metal in node['metals']:          # isostructural nodes (Fe₃O / Cr₃O / Al₃O …): same geometry, metal relabelled
            swapped = [(metal if s == src['metal'] else s, c) for s, c in atoms]
            (OUT / 'nodes' / f"{node['id']}__{metal}.sdf").write_text(
                molblock(swapped, f"{node['label']} ({metal}); geometry from {src['cif']}", metal))
        print(f"node   {node['id']:7s} {len(atoms):3d} atoms, {metals} {src['metal']} -> {', '.join(node['metals'])}")
    for linker in catalog['linkers']:
        block = build_linker(linker['smiles'])
        (OUT / 'linkers' / f"{linker['id']}.sdf").write_text(block + '$$$$\n')
        print(f"linker {linker['id']:7s} {block.splitlines()[3][:6].strip()} atoms")


if __name__ == '__main__':
    main()
