"""Metal node + organic linker → the real MOFs made from them (data/predict/catalog.json).

The AI needs a real crystal structure (its 12 inputs and the pore size come from atom positions), so a
chosen node + linker is looked up among MOFs that were actually made and are already scored in stage A.
Combinations nobody has made are reported as such instead of being given an invented score.
"""
import json, math
import pandas as pd
import streamlit as st
from . import data, pipeline

CLASS = {1: '불안정', 2: '낮은 동역학적 안정', 3: '높은 동역학적 안정', 4: '열역학적 안정'}   # MOFSimplify water classes


@st.cache_data
def catalog():
    return json.loads((data.DATA / 'predict/catalog.json').read_text())


def node(node_id):
    return next(n for n in catalog()['nodes'] if n['id'] == node_id)


def linker(linker_id):
    return next(l for l in catalog()['linkers'] if l['id'] == linker_id)


def combo(node_id, metal, linker_id):
    """The catalog entry for this node + metal + linker, or None if no such MOF is known."""
    return next((m for m in catalog()['mofs']
                 if (m['node'], m['metal'], m['linker']) == (node_id, metal, linker_id)), None)


def known_linkers(node_id, metal):
    return [m['linker'] for m in catalog()['mofs'] if (m['node'], m['metal']) == (node_id, metal)]


def made_with_node(node_id, metal):
    return [(linker(m['linker'])['label'], m['records'][0]['name'])
            for m in catalog()['mofs'] if (m['node'], m['metal']) == (node_id, metal)]


def made_with_linker(linker_id):
    return [(f"{node(m['node'])['label']} ({m['metal']})", m['records'][0]['name'])
            for m in catalog()['mofs'] if m['linker'] == linker_id]


@st.cache_data
def node_sdf(node_id, metal):
    """The node cut from a real structure (isostructural nodes such as Fe₃O / Cr₃O / Al₃O share one geometry)."""
    return (data.DATA / 'predict/nodes' / f'{node_id}__{metal}.sdf').read_text()


@st.cache_data
def linker_sdf(linker_id):
    return (data.DATA / 'predict/linkers' / f'{linker_id}.sdf').read_text()


@st.cache_data
def records():
    """Every curated MOF record joined to its stage-A row (score, rank, pore size …)."""
    A = data.stage_a().set_index('id')
    rows = []
    for m in catalog()['mofs']:
        for rec in m['records']:
            r = A.loc[rec['id']]
            rows.append({'rec_id': rec['id'], 'display': rec['name'], 'node': m['node'], 'metal': m['metal'],
                         'linker': m['linker'], 'structure': m['structure'], 'db_name': r['name'], **r.to_dict()})
    return pd.DataFrame(rows)


@st.cache_data
def lab_class(db_name):
    """MOFSimplify's literature water-stability class for this MOF, if it has one."""
    W = pd.read_csv(data.DATA / 'validation/water_labels.csv')
    hit = W[W['name'] == db_name]
    return None if hit.empty else int(hit.iloc[0]['water_label'])


@st.cache_data
def effect_reason(db_name):
    """Why a MOF carries a ± capture adjustment (data/variants/variants.csv), if recorded."""
    V = data.variants()
    hit = V[V['key'] == db_name]
    return None if hit.empty else str(hit.iloc[0]['effect_reason'])


def structure_cif(ref):
    """Whole-MOF CIF for the 3D view: 'variant:KEY', 'core:ID' or 'pipeline:ID' (None when not shipped)."""
    if not ref:
        return None
    kind, key = ref.split(':', 1)
    if kind == 'finalist':
        folder = (data.DATA / 'finalists').resolve()
        path = (folder / key).resolve()
        return path.read_text(errors='replace') if path.is_relative_to(folder) and path.exists() else None
    return {'variant': data.variant_cif, 'core': data.read_cif, 'pipeline': data.pipeline_cif}[kind](key)


def compare_table(frame, selected=None):
    """Side-by-side view of catalog records: parts, pore size and the four scores (▶ marks the chosen MOF)."""
    f = frame.sort_values('total', ascending=False)
    return pd.DataFrame({
        'MOF': [('▶ ' if i == selected else '') + d for i, d in zip(f.rec_id, f.display)],
        '금속 노드': [f"{node(n)['label']} ({m})" for n, m in zip(f.node, f.metal)],
        '링커': [linker(l)['label'] for l in f.linker],
        '링커 고리': [linker(l)['rings'] for l in f.linker],
        'PLD (Å)': f.pld_A.round(1), '표면적 (m²/g)': f.gsa_m2_g.round(0),
        '인산염': ['기공 안까지' if p >= pipeline.ACCESS_PLD else '겉면만' for p in f.pld_A],
        '안정성': f.stability.round(1), '포집': f.capture.round(1), '탈착': f.desorption.round(1),
        '재사용': f.reuse.round(1), '총점': f.total.round(1)})


def unscored_notes(row):
    """Things the parts suggest but this database row does not carry, so they are not in its score."""
    notes = []
    if node(row['node']).get('has_oms') and _na(row['open_metal_site']) is None:
        notes.append('이 노드에는 열린 금속 자리가 있지만, 이 MOF의 데이터에는 그 표시가 없어서 포집 점수의 가산점(+0.1)은 들어가 있지 않다.')
    if linker(row['linker'])['group'] in ('–NH₂', '–SO₃H', '–OH 2개') and row['group_effect'] == '0':
        notes.append('작용기 효과(–NH₂는 +, –SO₃H는 −)는 UiO-66 계열 19종에만 손으로 표시해 둔 값이라, 이 MOF의 포집 점수에는 들어가 있지 않다.')
    return notes


def _na(x):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else x


def explain(row):
    """Plain-language reasons for each of the four scores of one stage-A row."""
    f = pipeline.raw_parts(row['water_prob'], row['metal'], _na(row['pld_A']), _na(row['gsa_m2_g']),
                           _na(row['open_metal_site']), row['group_effect'], _na(row['thermal_C']),
                           _na(row['base_stable']))
    gate = (f"기공 통로 {f['pld']:.1f} Å ≥ {pipeline.ACCESS_PLD} Å라서 인산염이 기공 안까지 들어감 (×1.0)"
            if f['access'] == 1.0 else
            f"기공 통로 {f['pld']:.1f} Å < {pipeline.ACCESS_PLD} Å라서 인산염이 겉면에만 붙음 (×0.6)")
    reason = effect_reason(row.get('db_name', row['name']))
    group = {0.15: f" + 결합을 돕는 자리 +0.15 ({reason or '인산염과 결합을 돕는 작용기'})",
             -0.25: f" − 밀어내는 작용기 0.25 ({reason or '음전하가 인산염을 밀어냄'})"}.get(f['group'], '')
    oms = ' + 열린 금속 자리 0.1' if f['oms'] else ''
    thermal = '모름 → 350 °C로 봄' if _na(row['thermal_C']) is None else f"{row['thermal_C']:.0f} °C"
    base = {1.0: '강함', 0.0: '약함', 0.5: '모름'}[f['base']]
    return [
        ('안정성', f"{row['stability']:.1f} / 100",
         f"AI(Random Forest)가 예측한 물 안정성 확률 {f['p']:.2f} × 100"),
        ('포집', f"{row['capture']:.1f} / 40",
         f"금속 {row['metal']}의 인산염 결합력 {f['affinity']:.2f} × 표면적 보정 {0.6 + 0.4 * f['surface']:.2f} "
         f"(표면적 {f['gsa']:,.0f} m²/g) × {gate}{group}{oms}"),
        ('탈착', f"{row['desorption']:.1f} / 35",
         f"금속 {row['metal']}에서 인산염이 다시 떨어지는 정도 {f['reversibility']:.2f} × 기공 크기 보정 {f['pore']:.2f}"),
        ('재사용', f"{row['reuse']:.1f} / 25",
         f"0.6 × 물 안정성 {f['p']:.2f} + 0.25 × 열 안정성 {f['thermal']:.2f} ({thermal}) + 0.15 × 염기 안정성 {f['base']:.1f} ({base})"),
    ]
