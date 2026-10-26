"""Stage A of the pipeline: score every database MOF out of 200 and pick the top 3.

    python -m scripts.build_pipeline --ws24 /path/to/unzipped   # folder holding features/

Database = CoRE MOF 2025 (with RF predictions) + the MOFSimplify / WS24 labelled set.
Writes data/pipeline/stage_a.parquet and data/pipeline/stats.json.
"""
import argparse, json, math
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from moflab import pipeline
from moflab.descriptors import FEATURES

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/pipeline'
SYMBOLS = ('H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr '
           'Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm '
           'Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U').split()

def core_rows():
    df = pd.read_parquet(ROOT / 'data/catalog.parquet').dropna(subset=['water_prob'])
    # CoRE rows are SI file names; without a common name, describe the MOF by metal, topology and year.
    topo = df.topology.where(~df.topology.isin(['unnamed', 'unstable']) & df.topology.notna())
    described = df.metal + '-MOF·' + topo + ' (' + df.year.astype('string') + ')'
    names = df['common_name'].fillna(described).fillna(df['name'].str.replace(r'_pacman$', '', regex=True))
    return pd.DataFrame({'id': 'core:' + df.material_id, 'name': names, 'source': 'CoRE MOF 2025',
                         'metal': df.metal, 'water_prob': df.water_prob, 'pld_A': df.pld_A, 'lcd_A': df.lcd_A,
                         'gsa_m2_g': df.gsa_m2_g, 'open_metal_site': df.open_metal_site, 'group_effect': '0',
                         'thermal_C': df.source_thermal_C, 'base_stable': None, 'cif_ref': 'core:' + df.material_id})

def ws24_rows(ws):
    f = pd.read_csv(ws / 'features/features_and_labels.csv')
    model = joblib.load(sorted((ROOT / 'models').glob('water_rf_*.joblib'))[0])
    prob = model['estimator'].predict_proba(f[FEATURES].to_numpy(float))[:, 1]
    # mc-Z-0-all = Z(metal)² averaged over metal centres → recovers the metal for single-metal MOFs
    z = np.rint(np.sqrt(f['mc-Z-0-all'].clip(lower=1))).astype(int)
    metal = [SYMBOLS[i - 1] if 0 < i <= len(SYMBOLS) else None for i in z]
    variants = pd.read_csv(ROOT / 'data/variants/variants.csv').set_index('key')
    effect = [variants.effect.get(n, '0') for n in f.MOF_name]
    # WS24 rows are CSD refcodes; show the common name from the curators' label sheet when there is one.
    labels = pd.read_csv(ws / 'data_sets/WS24s/labels.csv', encoding='utf-8-sig')
    common = dict(zip(labels.refcode, labels['name in manuscript'].fillna('').astype(str).str.strip()))
    names = [common.get(n) if common.get(n) and len(common[n]) <= 24 else n for n in f.MOF_name]
    return pd.DataFrame({'id': 'ws24:' + f.MOF_name, 'name': names, 'source': 'MOFSimplify (WS24)',
                         'metal': metal, 'water_prob': prob, 'pld_A': f.Df, 'lcd_A': f.Di, 'gsa_m2_g': f.GSA,
                         'open_metal_site': None, 'group_effect': effect, 'thermal_C': np.nan,
                         'base_stable': f.base_label.astype(bool).where(f.base_label == 1, None),
                         'cif_ref': ['variant:' + n if n in variants.index else 'ws24:' + n for n in f.MOF_name],
                         'refcode': f.MOF_name})

def with_raw(frame):
    raws = [pipeline.raw_scores(r.water_prob, r.metal, r.pld_A, r.gsa_m2_g, r.open_metal_site, r.group_effect,
                                r.thermal_C, r.base_stable) for r in frame.itertuples()]
    return pd.concat([frame.reset_index(drop=True), pd.DataFrame(raws)], axis=1)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ws24', type=Path, required=True)
    ws = ap.parse_args().ws24
    a = with_raw(pd.concat([core_rows(), ws24_rows(ws)], ignore_index=True))
    stats = pipeline.reference_stats(a)
    ranked = pipeline.rank(pipeline.score(a, stats))
    OUT.mkdir(parents=True, exist_ok=True)
    ranked.to_parquet(OUT / 'stage_a.parquet', index=False)
    (OUT / 'stats.json').write_text(json.dumps(stats, indent=1))
    cols = ['rank', 'name', 'source', 'metal', 'total', 'stability', 'capture', 'desorption', 'reuse']
    print(ranked[cols].head(15).round(1).to_string(index=False))

if __name__ == '__main__':
    main()
