"""Build the lightweight web snapshot from the full local MOF Recovery Lab SQLite.

The full research DB (~100 MB) cannot be pushed to GitHub, so the web app ships
only what it displays: CoRE MOF 2025 candidates with predictions, gzipped CIFs,
and per-source counts.

    python -m scripts.export_snapshot --lab ../mof_recovery_lab
"""
import argparse, gzip, json, shutil, sqlite3
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ZEOPP = {'LCD': 'lcd_A', 'PLD': 'pld_A', 'density': 'density_g_cm3', 'ASA': 'asa_m2_cm3',
         'GSA': 'gsa_m2_g', 'VF': 'void_fraction', 'GPV': 'pore_volume_cm3_g'}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lab', type=Path, required=True, help='full mof_recovery_lab folder')
    lab = ap.parse_args().lab.resolve()
    con = sqlite3.connect(lab / 'data/moflab.sqlite3')
    con.row_factory = sqlite3.Row
    rows = con.execute('''SELECT m.material_id, m.name, m.formula, m.metals, m.structure_status, m.cif_rel,
                                 m.metadata_json, p.probability, p.in_domain, p.distance, p.detail_json
                          FROM materials m LEFT JOIN predictions p USING(material_id)
                          WHERE m.source_id='core2025' ''').fetchall()
    out = []
    for r in rows:
        md = json.loads(r['metadata_json'])
        z = md.get('Zeopp') or {}
        ref = md.get('reference') or {}
        detail = json.loads(r['detail_json']) if r['detail_json'] else {}
        stab = md.get('stability') or {}
        out.append({
            'material_id': r['material_id'], 'name': r['name'],
            'common_name': (md.get('id') or {}).get('common_name'),
            'metal': (md.get('metal') or {}).get('metal_type') or r['metals'],
            'open_metal_site': (md.get('metal') or {}).get('has_OMS') == 'Yes',
            'formula': r['formula'], 'structure_status': r['structure_status'],
            'n_atoms': (md.get('structure_info') or {}).get('n_atoms'),
            'space_group': ((md.get('structure_info') or {}).get('space_group') or {}).get('number'),
            'topology': (md.get('CrystalNets') or {}).get('all_nodes'),
            'doi': ref.get('DOI'), 'year': ref.get('year'),
            **{v: z.get(k) for k, v in ZEOPP.items()},
            'source_thermal_C': pd.to_numeric(stab.get('thermal'), errors='coerce'),
            'water_prob': r['probability'], 'in_domain': None if r['in_domain'] is None else bool(r['in_domain']),
            'domain_distance': r['distance'],
            'tree_sd': detail.get('tree_disagreement_sd'),
            'nearest_training_name': detail.get('nearest_training_name'),
            'has_cif': bool(r['cif_rel']),
        })
    for row, r in zip(out, rows):
        if r['cif_rel'] and not row['formula']:
            tags = {}
            for line in (lab / r['cif_rel']).read_text(errors='ignore').splitlines()[:60]:
                if line.startswith(('_chemical_formula_structural', '_chemical_formula_sum')):
                    key, _, value = line.partition(' ')
                    tags[key] = value.strip(" '\"\t")
            row['formula'] = tags.get('_chemical_formula_structural') or tags.get('_chemical_formula_sum')
    df = pd.DataFrame(out)
    df['year'] = pd.to_numeric(df['year'], errors='coerce').astype('Int64')
    df.to_parquet(ROOT / 'data/catalog.parquet', index=False)

    cif_dir = ROOT / 'data/cifs'
    shutil.rmtree(cif_dir, ignore_errors=True); cif_dir.mkdir(parents=True)
    for r in rows:
        if r['cif_rel']:
            src = lab / r['cif_rel']
            with open(src, 'rb') as f, gzip.open(cif_dir / f"{r['material_id']}.cif.gz", 'wb', compresslevel=9) as g:
                g.write(f.read())

    sources = [dict(s) for s in con.execute(
        "SELECT s.source_id, s.name, s.url, s.version, s.license, COUNT(m.material_id) AS records "
        "FROM sources s LEFT JOIN materials m USING(source_id) WHERE s.source_id!='team' GROUP BY s.source_id")]
    (ROOT / 'data/sources.json').write_text(json.dumps(sources, ensure_ascii=False, indent=1))
    print(f'{len(df)} candidates, {df.water_prob.notna().sum()} predictions, {df.has_cif.sum()} CIFs')

if __name__ == '__main__':
    main()
