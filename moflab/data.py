"""Read-only access to the shipped web snapshot (catalog, CIFs, model, finalists)."""
import gzip, hashlib, json, math
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.neighbors import NearestNeighbors
from .descriptors import FEATURES

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
MODELS = ROOT / 'models'
EXPERIMENT_DOC = 'https://docs.google.com/document/d/1vxpzNFfKXFvV6KkGYU8D0JXRZ9S28gkWapIRNVsO5w8/edit'  # 1-week AI-validation experiment plan (Google Docs)

# AlphaFold-style confidence bands, applied to the water-stability probability.
BANDS = [(0.85, '매우 높음', '#0053D6'), (0.70, '높음', '#65CBF3'),
         (0.50, '낮음', '#FFDB13'), (0.0, '매우 낮음', '#FF7D45')]

def band(p):
    if p is None or (isinstance(p, float) and math.isnan(p)):
        return '예측 없음', '#B8C2CC'
    for cut, label, color in BANDS:
        if p >= cut:
            return label, color

@st.cache_data
def catalog():
    df = pd.read_parquet(DATA / 'catalog.parquet')
    df['display_name'] = df['common_name'].fillna(df['name'].str.replace(r'_pacman$', '', regex=True))
    df['water_index'] = df['water_prob'] * 100
    df['band'] = [band(p)[0] for p in df['water_prob']]
    return df

@st.cache_data
def sources():
    return json.loads((DATA / 'sources.json').read_text())

@st.cache_data
def read_cif(material_id):
    path = DATA / 'cifs' / f'{material_id}.cif.gz'
    if not path.resolve().is_relative_to((DATA / 'cifs').resolve()) or not path.exists():
        return None
    with gzip.open(path, 'rt', errors='replace') as f:
        return f.read()

@st.cache_data
def finalists():
    items = json.loads((DATA / 'finalists/finalists.json').read_text())
    for item in items:
        item['cif_text'] = (DATA / 'finalists' / item['cif']).read_text(errors='replace')
        csv = item.get('descriptors')
        item['descriptor_frame'] = pd.read_csv(DATA / 'finalists' / csv) if csv else None
    return items

@st.cache_data
def variants():
    return pd.read_csv(DATA / 'variants/variants.csv')

@st.cache_data
def variant_cif(key):
    path = (DATA / 'variants' / f'{key}.cif').resolve()
    if not path.is_relative_to((DATA / 'variants').resolve()) or not path.exists():
        return None
    return path.read_text(errors='replace')

@st.cache_data
def stage_a():
    return pd.read_parquet(DATA / 'pipeline/stage_a.parquet')

@st.cache_data
def stage_b():
    return pd.read_parquet(DATA / 'pipeline/stage_b.parquet')

@st.cache_data
def pipeline_stats():
    return json.loads((DATA / 'pipeline/stats.json').read_text())

@st.cache_data
def final_pick():
    return json.loads((DATA / 'pipeline/final.json').read_text())

@st.cache_data
def pipeline_cif(structure_id):
    folder = (DATA / 'pipeline/structures').resolve()
    path = (folder / f'{structure_id}.cif').resolve()
    if not path.is_relative_to(folder) or not path.exists():
        return None
    return path.read_text(errors='replace')

@st.cache_data
def metal_swap():
    path = DATA / 'metal_swap/results.csv'
    return pd.read_csv(path) if path.exists() else None

@st.cache_data
def metal_swap_meta():
    return json.loads((DATA / 'metal_swap/meta.json').read_text())

@st.cache_data
def metal_swap_cif(metal):
    path = (DATA / 'metal_swap' / f'UiO-66-NH2_{metal}.cif').resolve()
    if not path.is_relative_to((DATA / 'metal_swap').resolve()) or not path.exists():
        return None
    return path.read_text(errors='replace')

def swap_verdict(row):
    """Label a metal-swap result; thresholds are rough, per metal atom."""
    e = row.swap_energy_eV
    if not row.charge_balanced:
        return '전하 불균형 · 가상 구조', ('#FDECEA', '#B3261E')
    if e <= 0.5:
        return 'Zr와 비슷하거나 유리', ('#E6F4EA', '#137333')
    if e <= 2.0:
        return 'Zr보다 불리', ('#FFF4E5', '#8A5300')
    return '매우 불리', ('#FDECEA', '#B3261E')

@st.cache_data
def validation():
    return json.loads((MODELS / 'water_validation.json').read_text())

@st.cache_data
def oof_predictions():
    return pd.read_csv(MODELS / 'water_oof_predictions.csv')

@st.cache_resource
def water_model():
    manifest = validation()
    path = MODELS / f"{manifest['model_id']}.joblib"
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest['artifact_sha256']:
        raise ValueError('모델 파일 체크섬이 학습 기록과 다릅니다.')
    # Only the checksum-verified artifact shipped in this repo is loaded; there is no upload path.
    return joblib.load(path)

def predict_water(frame):
    """12 MOFSimplify RAC/geometry descriptors -> stable probability + applicability domain."""
    art = water_model()
    missing = sorted(set(FEATURES) - set(frame.columns))
    if missing:
        raise ValueError('구조 특성 열 누락: ' + ', '.join(missing))
    x = frame[FEATURES].apply(pd.to_numeric, errors='coerce').to_numpy(float)
    if not len(x) or not np.isfinite(x).all():
        raise ValueError('12개 특성에 빈 값·문자·무한대가 있으면 예측할 수 없습니다.')
    p = art['estimator'].predict_proba(x)[:, 1]
    nn = NearestNeighbors(n_neighbors=1).fit(art['reference_scaled'])
    dist, idx = nn.kneighbors(art['scaler'].transform(x))
    dist = dist[:, 0] / math.sqrt(len(FEATURES))
    trees = np.array([t.predict_proba(x)[:, 1] for t in art['estimator'].estimators_])
    return pd.DataFrame({'water_prob': p, 'water_index': 100 * p, 'domain_distance': dist,
                         'in_domain': dist <= art['domain_cutoff'], 'tree_sd': trees.std(axis=0),
                         'nearest_training_name': [art['reference_names'][i] for i in idx[:, 0]]})

def feature_importance():
    art = water_model()
    return pd.DataFrame({'feature': FEATURES, 'importance': art['estimator'].feature_importances_}
                        ).sort_values('importance')
