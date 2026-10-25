import json
import pandas as pd
import streamlit as st
from moflab import data, screen, ui, viewer
from moflab.cif import inspect_cif

df = data.catalog()
var = data.variants()

st.markdown('<div class="eyebrow">MOF Recovery Lab</div>', unsafe_allow_html=True)
st.title('인산염 회수용 MOF 스크리닝')
st.markdown('<p class="sub">MOF를 고르면 → 물 안정성 AI 예측 · 인산염 적합성 체크 · 3D 구조</p>', unsafe_allow_html=True)

# ── ① Select ────────────────────────────────────────────────────────
SOURCES = [f'데이터베이스 ({len(df):,})', f'UiO-66 변형체 ({len(var)})', '내 구조 업로드']
source = st.segmented_control('MOF 선택', SOURCES, default=SOURCES[0], key='tool_source') or SOURCES[0]
mof = None  # dict(name, cif, water_prob, in_domain, metal, pld, lcd, gsa, water_class, effect, nearest)

if source == SOURCES[0]:
    f1, f2 = st.columns([1, 3])
    st.session_state.setdefault('tool_metals', ['Zr'])
    metals = f1.multiselect('금속', df.metal.value_counts().index.tolist(), placeholder='전체', key='tool_metals')
    pool = df[df.metal.isin(metals)] if metals else df
    pool = pool.sort_values('water_prob', ascending=False, na_position='last')
    labels = {r.material_id: f"{r.display_name} · {r.metal} · "
              f"{'—' if r.water_prob != r.water_prob else f'{100*r.water_prob:.0f}'}"
              for r in pool.itertuples()}
    current = st.session_state.get('entry_id')
    ids = list(labels)
    mid = f2.selectbox('구조 (이름 · 금속 · 지수, 지수 높은 순)', ids, format_func=labels.get,
                       index=ids.index(current) if current in ids else 0)
    st.session_state['entry_id'] = mid
    r = df.set_index('material_id').loc[mid]
    mof = dict(name=r.display_name, cif=data.read_cif(mid), water_prob=r.water_prob,
               in_domain=None if r.in_domain != r.in_domain else r.in_domain, metal=r.metal,
               pld=r.pld_A, lcd=r.lcd_A, gsa=r.gsa_m2_g, nearest=r.nearest_training_name,
               water_class=None, effect=None, file=f"{r['name']}.cif")

elif source == SOURCES[1]:
    names = dict(zip(var.key, var.name))
    key = st.selectbox('변형체', list(names), format_func=names.get, index=list(names).index('UiO-66-NH2'))
    r = var.set_index('key').loc[key]
    mof = dict(name=r['name'], cif=data.variant_cif(key), water_prob=r.rf_in_sample, in_domain=None,
               metal='Fe' if key == 'mil-100-fe' else 'Zr', pld=r.pld_A, lcd=r.lcd_A, gsa=r.gsa_m2_g,
               water_class=r.water_class, effect=r.effect, nearest=None, file=r.cif,
               group=r.group, verdict=r.verdict)

else:
    u1, u2 = st.columns(2)
    csv = u1.file_uploader('descriptor CSV', type='csv',
                           help='MOFSimplify에 CIF 업로드 → “Download descriptors”로 받은 파일')
    cif_up = u2.file_uploader('CIF (3D 표시용, 선택)', type='cif')
    cif_text, metal = None, None
    if cif_up:
        try:
            info = inspect_cif(cif_up.getvalue())
            cif_text = cif_up.getvalue().decode('utf-8-sig', errors='replace')
            metal = ' '.join(e for e in info['elements_site_counts'] if e in screen.PHOSPHATE_METALS
                             or e not in {'H', 'C', 'N', 'O', 'F', 'Cl', 'Br', 'I', 'S', 'P'})
        except ValueError as exc:
            st.error(str(exc))
    if csv is not None:
        try:
            pred = data.predict_water(pd.read_csv(csv)).iloc[0]
            mof = dict(name=csv.name.removesuffix('.csv'), cif=cif_text, water_prob=float(pred.water_prob),
                       in_domain=bool(pred.in_domain), metal=metal, pld=None, lcd=None, gsa=None,
                       water_class=None, effect=None, nearest=pred.nearest_training_name,
                       file=cif_up.name if cif_up else None)
        except ValueError as exc:
            st.error(str(exc))
    elif cif_text:
        mof = dict(name=cif_up.name, cif=cif_text, water_prob=None, in_domain=None, metal=metal, pld=None,
                   lcd=None, gsa=None, water_class=None, effect=None, nearest=None, file=cif_up.name)
    if mof is None:
        st.info('descriptor CSV를 올리면 AI 예측, CIF를 올리면 3D 구조가 나옵니다.')

if mof is None:
    st.stop()

# ── ② Result ────────────────────────────────────────────────────────
st.divider()
checks = screen.checklist(mof['water_prob'], mof['in_domain'], mof['metal'], mof['pld'],
                          mof['water_class'], mof['effect'])
verdict, passed, total = screen.summary(checks)
tone = {'유망': ('#E6F4EA', '#137333'), '검토': ('#FFF4E5', '#8A5300'), '부적합': ('#FDECEA', '#B3261E')}[verdict]

left, right = st.columns([1, 1.35], gap='large')
with left:
    st.markdown(f"### {mof['name']}")
    st.markdown(f'''<div class="card" style="background:{tone[0]};border-color:{tone[0]}">
      <div style="font-size:13px;font-weight:700;color:{tone[1]}">인산염 회수 스크리닝</div>
      <div style="font-size:32px;font-weight:850;color:{tone[1]};line-height:1.25">{verdict}
      <span style="font-size:15px;font-weight:600"> · {passed}/{total} 통과</span></div></div>''',
                unsafe_allow_html=True)
    st.write('')
    for label, ok, detail in checks:
        icon = {True: '✅', False: '❌', None: '➖'}[ok]
        st.markdown(f"{icon} **{label}** <span class='note'>{detail}</span>", unsafe_allow_html=True)
    st.write('')
    title = 'AI 물 안정성 지수 (참고: 학습 데이터 포함)' if mof['water_class'] is not None else 'AI 물 안정성 지수'
    ui.confidence(mof['water_prob'], title)
    if mof.get('nearest'):
        ui.note(f"가장 비슷한 학습 MOF: {mof['nearest']}")

with right:
    if mof['cif']:
        s1, s2, s3 = st.columns(3)
        style = s1.selectbox('표현', list(viewer.STYLES), key='tool_style')
        cells = s2.selectbox('격자', [1, 2], format_func=lambda n: f'{n}×{n}×{n}', key='tool_cells')
        spin = s3.toggle('회전', False, key='tool_spin')
        viewer.crystal(mof['cif'], style, cells, True, spin, height=440,
                       highlight=[m for m in str(mof['metal'] or '').split() if m])
    else:
        st.info('CIF가 없어 3D 구조를 표시할 수 없습니다.')
    if mof['lcd'] is not None:
        g = st.columns(3)
        g[0].metric('최대 기공 LCD', f"{mof['lcd']:.1f} Å")
        g[1].metric('통로 PLD', f"{mof['pld']:.1f} Å")
        g[2].metric('표면적', f"{mof['gsa']:,.0f} m²/g")

# ── ③ Export ────────────────────────────────────────────────────────
result = {'name': mof['name'], 'screening': verdict, 'passed': f'{passed}/{total}',
          'water_index': None if mof['water_prob'] is None or mof['water_prob'] != mof['water_prob']
          else round(100 * float(mof['water_prob']), 1),
          'checks': [{'item': l, 'pass': p, 'detail': d} for l, p, d in checks]}
d1, d2, _ = st.columns([1, 1, 2])
d1.download_button('결과 JSON', json.dumps(result, ensure_ascii=False, indent=1, default=str),
                   file_name=f"{mof['name']}_screening.json", icon=':material/download:', width='stretch')
if mof['cif']:
    d2.download_button('CIF', mof['cif'], file_name=mof['file'] or 'structure.cif', icon=':material/download:',
                       width='stretch')
with st.expander('판정 기준'):
    st.markdown(f"- 물 안정성: 문헌 3등급↑ 또는 AI 지수 {screen.WATER_INDEX_MIN}↑ (가장 중요 — 실패하면 부적합)\n"
                f"- 인산염 결합 금속: {', '.join(sorted(screen.PHOSPHATE_METALS))} (M–O–P 결합 보고)\n"
                f"- 기공 통과: PLD ≥ {screen.PHOSPHATE_DIAMETER_A} Å면 내부까지 들어감 (작아도 탈락은 아님)\n"
                "- 작용기 전하: pH 7에서 음전하(–COOH, –SO₃H)면 반발\n"
                "- 경험 규칙 기반 1차 선별이며, 인산염 흡착량은 실험으로 확인해야 합니다.")
