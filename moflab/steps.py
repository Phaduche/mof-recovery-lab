"""The six pipeline steps (A-1 … Final), each rendered as its own top-level page."""
import plotly.graph_objects as go
import streamlit as st
from . import data, ui, viewer
from .pipeline import LABELS, WEIGHTS

COLORS = {'stability': '#0053D6', 'capture': '#24A0C8', 'desorption': '#2BB673', 'reuse': '#FFB020'}
STEPS = ['A-1', 'A-2', 'A-3', 'B-1', 'B-2', 'Final']
TABLE_COLS = {'rank': '순위', 'name': 'MOF', 'source': '출처', 'metal': '금속', 'change': '종류', 'detail': '수정 내용',
              'total': '총점', 'stability': '안정성', 'capture': '포집', 'desorption': '탈착', 'reuse': '재사용'}

def _header(step, title, sub, ai=None):
    chips = ''.join(
        f"<span class='pill' style='background:{'#0053D6' if s == step else '#EEF2F6'};"
        f"color:{'#fff' if s == step else '#62758A'}'>{s}</span>" + ('' if s == 'Final' else
                                                                    "<span style='color:#B8C2CC'>→ </span>")
        for s in STEPS)
    st.markdown(f'<div style="margin-bottom:10px">{chips}</div>', unsafe_allow_html=True)
    ui.heading(f'Step {step}', title, sub)
    if ai:
        st.markdown(ui.pill(f'🤖 {ai}', '#F2EEFC', '#5B3FB0'), unsafe_allow_html=True)

def _score_bars(frame, height=None):
    """Stacked horizontal bars: the four parts of the 200-point score."""
    fig = go.Figure()
    for k in WEIGHTS:
        fig.add_bar(y=frame['name'], x=frame[k], name=f'{LABELS[k]} ({WEIGHTS[k]})', orientation='h',
                    marker_color=COLORS[k], hovertemplate='%{y} · ' + LABELS[k] + ' %{x:.1f}<extra></extra>')
    fig.update_layout(barmode='stack', height=height or 60 + 36 * len(frame), xaxis=dict(range=[0, 200], title=None),
                      yaxis=dict(autorange='reversed', title=None), margin=dict(t=48),
                      legend=dict(orientation='h', yanchor='bottom', y=1.02, x=0))
    st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})

def _table(frame, cols, height=360):
    st.dataframe(frame[cols].rename(columns=TABLE_COLS), hide_index=True, width='stretch', height=height,
                 column_config={'총점': st.column_config.ProgressColumn(min_value=0, max_value=200, format='%.1f'),
                                **{c: st.column_config.NumberColumn(format='%.1f') for c in ['안정성', '포집', '탈착', '재사용']}})

def _finalists():
    return data.stage_a().head(3)

def a1():
    A = data.stage_a()
    _header('A-1', '데이터베이스에서 MOF 가져오기', '실험으로 보고된 MOF 구조 + 문헌 안정성 기록')
    counts = A.source.value_counts()
    cols = st.columns(len(counts) + 1)
    for col, (src, n) in zip(cols, counts.items()):
        col.metric(src, f'{n:,}개')
    cols[-1].metric('합계', f'{len(A):,}개')
    metals = A.metal.value_counts().head(12)
    fig = go.Figure(go.Bar(x=metals.index, y=metals.values, marker_color='#9DB8D9'))
    fig.update_layout(title='금속별 MOF 수', height=300)
    st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})

def a2():
    A = data.stage_a()
    _header('A-2', '모든 MOF를 AI로 200점 만점 채점', '안정성은 절대평가 · 나머지는 데이터베이스 안에서 상대평가',
            'ML · Random Forest (물 안정성) + 점수 규칙')
    w = st.columns(4)
    for col, (k, how) in zip(w, [('stability', '절대 · AI 확률 × 100'), ('capture', '상대 · z-score'),
                                 ('desorption', '상대 · z-score'), ('reuse', '상대 · z-score')]):
        col.metric(LABELS[k], f'{WEIGHTS[k]}점', how, delta_color='off')
    fig = go.Figure(go.Histogram(x=A.total, nbinsx=50, marker_color='#65A0E0'))
    for _, r in A.head(3).iterrows():
        fig.add_vline(x=r.total, line_color='#0053D6', line_dash='dot')
    fig.update_layout(title='총점 분포 (점선 = 상위 3개)', height=280, xaxis_title='총점 / 200')
    st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
    q = st.text_input('검색', placeholder='MOF 이름 · 금속 (예: UiO-66, Zr)', label_visibility='collapsed')
    view = A if not q else A[(A.name + ' ' + A.metal.fillna('')).str.contains(q, case=False, regex=False)]
    _table(view, ['rank', 'name', 'source', 'metal', 'total', 'stability', 'capture', 'desorption', 'reuse'])

def a3():
    top3 = _finalists()
    _header('A-3', '최고점 3개 = 최종 MOF', '데이터베이스 전체에서 총점이 가장 높은 3개')
    _score_bars(top3)
    names = top3.name.tolist()
    pick = st.segmented_control('MOF', names, default=names[0], key='a3_pick') or names[0]
    r = top3[top3.name == pick].iloc[0]
    v, info = st.columns([1.5, 1], gap='large')
    with v:
        viewer.crystal(data.pipeline_cif(r.id.split(':', 1)[1]), '스틱', 1, True, False, height=420, highlight=['Zr'])
    with info:
        ui.kv([('순위', f'{r["rank"]}위'), ('총점', f'{r.total:.1f} / 200'), ('출처', r.source), ('금속', r.metal),
               ('기공 (PLD)', f'{r.pld_A:.1f} Å'), ('표면적', f'{r.gsa_m2_g:,.0f} m²/g')])

def b1():
    top3, B = _finalists(), data.stage_b()
    _header('B-1', '최종 3개의 연결 · 원소 바꾸기', '링커 작용기 7종 · 노드 금속 6종 → 39개',
            'DL · CHGNet 그래프 신경망 (원소 교체 에너지)')
    names = top3.name.tolist()
    p1, p2 = st.columns([1, 2])
    par = p1.selectbox('원본 MOF', names, key='b1_parent')
    mods = B[(B.parent == par) & (B.change != '원본')]
    mod_name = p2.selectbox('수정', mods.name.tolist(), key='b1_mod')
    m = mods[mods.name == mod_name].iloc[0]
    v1, v2 = st.columns(2)
    with v1:
        st.caption(f'원본 · {par}')
        viewer.crystal(data.pipeline_cif(top3[top3.name == par].iloc[0].id.split(':', 1)[1]), '스틱', 1, True, False,
                       height=360)
    with v2:
        st.caption(f'수정 · {m.detail}')
        viewer.crystal(data.pipeline_cif(m.id), '스틱', 1, True, False, height=360,
                       highlight=[m.metal] if m.change == '원소' else None)

    st.subheader('원소를 바꾸면 에너지가 어떻게 되나')
    swap = data.metal_swap().sort_values('swap_energy_eV')
    ox_color = {4: '#0053D6', 3: '#24A0C8', 2: '#FFB020', 1: '#E5484D'}
    fig = go.Figure(go.Bar(x=swap.metal, y=swap.swap_energy_eV, marker_color=[ox_color[o] for o in swap.oxidation_state],
                           text=[f'{v:+.2f}' for v in swap.swap_energy_eV], textposition='outside',
                           customdata=swap.oxidation_state, hovertemplate='%{x} (+%{customdata}가) · %{y:+.2f} eV<extra></extra>'))
    fig.add_hline(y=0, line_color='#0F2236', line_width=1)
    fig.update_layout(height=340, yaxis_title='Zr 대비 교체 에너지 (eV / 금속)', xaxis_title=None)
    st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
    st.markdown(' '.join(ui.pill(f'+{o}가', c + '22', '#0F2236') for o, c in ox_color.items()), unsafe_allow_html=True)
    k = swap.set_index('metal').loc['K']
    ui.note(f"0 = Zr와 같음 · 양수 = 불리 · 예: Zr → K는 {k.swap_energy_eV:+.2f} eV, 부피 {k.volume_change_pct:+.0f}% "
            '(+1가라 전하가 맞지 않아 구조가 무너짐)')
    with st.expander('어떻게 계산했나'):
        st.markdown('Zr₆ 노드의 Zr를 다른 금속으로 바꾸고 **CHGNet**으로 원자 위치 · 격자를 이완한 뒤, '
                    '각 금속의 순수 결정 에너지(μ)와 비교')
        st.latex(r'\Delta E = \frac{E(\text{M-MOF}) - E(\text{Zr-MOF}) - 6(\mu_\text{M} - \mu_\text{Zr})}{6}')

def b2():
    top3, B = _finalists(), data.stage_b()
    _header('B-2', '수정한 MOF를 같은 AI로 다시 채점', 'A 단계와 같은 잣대 (같은 평균 · 표준편차)',
            'ML · Random Forest + 점수 규칙')
    names = top3.name.tolist()
    par = st.segmented_control('원본', names, default=names[0], key='b2_parent') or names[0]
    group = B[B.parent == par].sort_values('total', ascending=False)
    base = group[group.change == '원본'].total.iloc[0]
    delta = group.total - base
    fig = go.Figure(go.Bar(x=delta, y=group.name, orientation='h', text=[f'{d:+.1f}' for d in delta],
                           marker_color=['#0053D6' if d > 0 else '#C9D4DF' if d == 0 else '#FF7D45' for d in delta],
                           textposition='outside'))
    fig.update_layout(title=f'원본({base:.1f}점) 대비 점수 변화', height=80 + 26 * len(group),
                      yaxis=dict(autorange='reversed', title=None), xaxis_title='점수 변화')
    st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
    _table(B, ['rank', 'name', 'change', 'detail', 'total', 'stability', 'capture', 'desorption', 'reuse'])

def final():
    A, B = data.stage_a(), data.stage_b()
    win = B.iloc[0]
    parent = A[A.name == win.parent].iloc[0]
    _header('Final', win['name'], f'{win.parent}의 {win.change} 수정 · 원본·수정 {len(B)}개 중 1위')
    m = st.columns(4)
    m[0].metric('최종 점수 / 200', f'{win.total:.1f}', f'{win.total - parent.total:+.1f} (원본 대비)')
    m[1].metric('안정성 / 100', f'{win.stability:.1f}')
    m[2].metric('포집 · 탈착 · 재사용', f'{win.capture:.0f} · {win.desorption:.0f} · {win.reuse:.0f}')
    m[3].metric('A 단계 평가 수', f'{len(A):,}')
    f1, f2 = st.columns([1.4, 1], gap='large')
    with f1:
        viewer.crystal(data.pipeline_cif(win.id), '볼 & 스틱', 1, True, True, height=440, highlight=['Zr', 'O'])
    with f2:
        _score_bars(B.head(5), height=300)
        ui.kv([('원본', f'{win.parent} ({parent.total:.1f}점)'), ('수정', win.detail)])
    st.download_button('최종 MOF 구조 (CIF)', data.pipeline_cif(win.id), file_name=f'{win.id}.cif',
                       icon=':material/download:')
