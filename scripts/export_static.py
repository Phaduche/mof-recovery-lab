"""Write the static site's data (docs/data) from the shipped snapshot.  python -m scripts.export_static"""
import json, shutil
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import roc_curve

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/data'
OUT.mkdir(parents=True, exist_ok=True)
R = lambda x: None if pd.isna(x) else round(float(x), 2)

a = pd.read_parquet(ROOT / 'data/pipeline/stage_a.parquet')
rows = [{'rank': int(r.rank), 'id': r.id, 'name': r.name, 'source': r.source, 'metal': r.metal if isinstance(r.metal, str) else '',
         'total': R(r.total), 'stability': R(r.stability), 'capture': R(r.capture), 'desorption': R(r.desorption),
         'reuse': R(r.reuse), 'pld': R(r.pld_A), 'gsa': R(r.gsa_m2_g)} for r in a.itertuples()]
(OUT / 'stage_a.json').write_text(json.dumps(rows, ensure_ascii=False))

b = pd.read_parquet(ROOT / 'data/pipeline/stage_b.parquet')
rows = [{'rank': int(r.rank), 'id': r.id, 'name': r.name, 'parent': r.parent, 'parent_id': r.parent_id.split(':', 1)[1],
         'change': r.change, 'detail': r.detail, 'metal': r.metal, 'total': R(r.total), 'stability': R(r.stability),
         'capture': R(r.capture), 'desorption': R(r.desorption), 'reuse': R(r.reuse)} for r in b.itertuples()]
(OUT / 'stage_b.json').write_text(json.dumps(rows, ensure_ascii=False))
shutil.copyfile(ROOT / 'data/pipeline/final.json', OUT / 'final.json')

sw = pd.read_csv(ROOT / 'data/metal_swap/results.csv')
(OUT / 'metal_swap.json').write_text(json.dumps([{'metal': r.metal, 'ox': int(r.oxidation_state), 'dE': R(r.swap_energy_eV),
    'reported': r.reported, 'balanced': bool(r.charge_balanced)} for r in sw.itertuples()], ensure_ascii=False))

val = json.loads((ROOT / 'models/water_validation.json').read_text())
oof = pd.read_csv(ROOT / 'models/water_oof_predictions.csv')
fpr, tpr, _ = roc_curve(oof.stable_label, oof.oof_probability)
keep = np.unique(np.linspace(0, len(fpr) - 1, 120).astype(int))
import joblib
art = joblib.load(sorted((ROOT / 'models').glob('water_rf_*.joblib'))[0])
imp = sorted(zip(val['features'], art['estimator'].feature_importances_), key=lambda t: t[1])
(OUT / 'validation.json').write_text(json.dumps({
    'training_rows': val['training_rows'], 'metrics': val['metrics'], 'baseline': val['baseline_metrics'],
    'folds': [{'fold': f['fold'], 'auc': R(f['roc_auc']), 'balacc': R(f['balanced_accuracy'])} for f in val['folds']],
    'roc': {'fpr': [R(x) for x in fpr[keep]], 'tpr': [R(x) for x in tpr[keep]]},
    'importance': [{'feature': f, 'value': round(float(v), 4)} for f, v in imp],
    'parameters': val['parameters']}, ensure_ascii=False))
shutil.copyfile(ROOT / 'data/sources.json', OUT / 'sources.json')
for cif in (ROOT / 'data/pipeline/structures').glob('*.cif'):
    shutil.copyfile(cif, OUT / 'structures' / cif.name)
print('stage_a', len(a), 'stage_b', len(b), 'cifs', len(list((OUT / 'structures').glob('*.cif'))))
