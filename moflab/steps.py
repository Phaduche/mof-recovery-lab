"""The six pipeline steps (A-1 … Final), each rendered as its own top-level page."""
import plotly.graph_objects as go
import streamlit as st
from . import data, ui, viewer
from .pipeline import LABELS, WEIGHTS

COLORS = {'stability': '#346aff', 'capture': '#e52528', 'desorption': '#f5a623', 'reuse': '#00891a'}
STEPS = ['A-1', 'A-2', 'A-3', 'B-1', 'B-2', 'Final']
TABLE_COLS = {'rank': '순위', 'name': 'MOF', 'source': '출처', 'metal': '금속', 'change': '종류', 'detail': '수정 내용',
              'total': '총점', 'stability': '안정성', 'capture': '포집', 'desorption': '탈착', 'reuse': '재사용'}

PATHS = {'A-1': 'a1', 'A-2': 'a2', 'A-3': 'a3', 'B-1': 'b1', 'B-2': 'b2', 'Final': 'final'}

def _header(step, title, ai=None):
    ui.header(PATHS[step])
    st.title(title)
    st.caption(' > '.join(f'[{s}]' if s == step else s for s in STEPS) + (f'  ·  모델: {ai}' if ai else ''))

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
    _header('A-1', '데이터베이스에서 MOF 가져오기')
    counts = A.source.value_counts()
    cols = st.columns(len(counts) + 1)
    for col, (src, n) in zip(cols, counts.items()):
        col.metric(src, f'{n:,}개')
    cols[-1].metric('합계', f'{len(A):,}개')
    metals = A.metal.value_counts().head(12)
    fig = go.Figure(go.Bar(x=metals.index, y=metals.values, marker_color='#346aff'))
    fig.update_layout(title='금속별 MOF 수', height=300)
    st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})

def a2():
    A = data.stage_a()
    _header('A-2', 'AI로 200점 만점 채점', 'ML · Random Forest + 점수 규칙')
    w = st.columns(4)
    for col, k in zip(w, WEIGHTS):
        col.metric(LABELS[k], f'{WEIGHTS[k]}점')
    fig = go.Figure(go.Histogram(x=A.total, nbinsx=50, marker_color='#346aff'))
    for _, r in A.head(3).iterrows():
        fig.add_vline(x=r.total, line_color='#e52528', line_dash='dot')
    fig.update_layout(title='총점 분포 (점선 = 상위 3개)', height=280, xaxis_title='총점 / 200')
    st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
    q = st.text_input('검색', value=st.query_params.get('q', ''), placeholder='MOF 이름, 금속 (예: UiO-66, Zr)',
                      label_visibility='collapsed')
    view = A if not q else A[(A.name + ' ' + A.metal.fillna('')).str.contains(q, case=False, regex=False)]
    _table(view, ['rank', 'name', 'source', 'metal', 'total', 'stability', 'capture', 'desorption', 'reuse'])

def a3():
    top3 = _finalists()
    _header('A-3', '최고점 3개')
    ui.section('AI가 고른 <em>최종 3개</em>', ('B-1에서 수정하기', 'b1'))
    cols = st.columns(3)
    for col, (_, r) in zip(cols, top3.iterrows()):
        with col:
            viewer.crystal(data.pipeline_cif(r.id.split(':', 1)[1]), '스틱', 1, True, False, height=240, highlight=['Zr'])
            ui.item(r['name'], r.total, rank=int(r['rank']), tag='AI추천', deliv=f'{r.source} · {r.metal}',
                    stars=r.stability / 100)
            ui.kv([('기공 (PLD)', f'{r.pld_A:.1f} Å'), ('표면적', f'{r.gsa_m2_g:,.0f} m²/g'),
                   ('포집 / 탈착 / 재사용', f'{r.capture:.0f} / {r.desorption:.0f} / {r.reuse:.0f}')])
    ui.section('200점 <em>구성</em>')
    _score_bars(top3)

def b1():
    top3, B = _finalists(), data.stage_b()
    _header('B-1', '링커 · 원소 바꾸기', 'DL · CHGNet 그래프 신경망')
    names = top3.name.tolist()
    p1, p2 = st.columns([1, 2])
    par = p1.selectbox('원본 MOF', names, key='b1_parent')
    mods = B[(B.parent == par) & (B.change != '원본')]
    mod_name = p2.selectbox('수정', mods.name.tolist(), key='b1_mod')
    m = mods[mods.name == mod_name].iloc[0]
    v1, v2 = st.columns(2)
    with v1:
        st.caption('원본')
        viewer.crystal(data.pipeline_cif(top3[top3.name == par].iloc[0].id.split(':', 1)[1]), '스틱', 1, True, False,
                       height=360)
    with v2:
        st.caption(m.detail)
        viewer.crystal(data.pipeline_cif(m.id), '스틱', 1, True, False, height=360,
                       highlight=[m.metal] if m.change == '원소' else None)

    st.subheader('원소 교체 에너지 (Zr 기준)')
    swap = data.metal_swap().sort_values('swap_energy_eV')
    ox_color = {4: '#346aff', 3: '#e52528', 2: '#f5a623', 1: '#8bc34a'}
    fig = go.Figure(go.Bar(x=swap.metal, y=swap.swap_energy_eV, marker_color=[ox_color[o] for o in swap.oxidation_state],
                           text=[f'{v:+.2f}' for v in swap.swap_energy_eV], textposition='outside',
                           customdata=swap.oxidation_state, hovertemplate='%{x} (+%{customdata}가) · %{y:+.2f} eV<extra></extra>'))
    fig.add_hline(y=0, line_color='#333', line_width=1)
    fig.update_layout(height=340, yaxis_title='eV / 금속', xaxis_title=None)
    st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
    st.caption('막대 색 = 금속 산화수: 파랑 +4, 빨강 +3, 주황 +2, 연두 +1')

def b2():
    top3, B = _finalists(), data.stage_b()
    _header('B-2', '같은 AI로 다시 채점', 'ML · Random Forest + 점수 규칙')
    names = top3.name.tolist()
    par = st.segmented_control('원본', names, default=names[0], key='b2_parent') or names[0]
    group = B[B.parent == par].sort_values('total', ascending=False)
    base = group[group.change == '원본'].total.iloc[0]
    delta = group.total - base
    fig = go.Figure(go.Bar(x=delta, y=group.name, orientation='h', text=[f'{d:+.1f}' for d in delta],
                           marker_color=['#346aff' if d > 0 else '#bbb' if d == 0 else '#e52528' for d in delta],
                           textposition='outside'))
    fig.update_layout(title=f'원본({base:.1f}점) 대비 점수 변화', height=80 + 26 * len(group),
                      yaxis=dict(autorange='reversed', title=None), xaxis_title='점수 변화')
    st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
    _table(B, ['rank', 'name', 'change', 'detail', 'total', 'stability', 'capture', 'desorption', 'reuse'])

def final():
    A, B = data.stage_a(), data.stage_b()
    win = B.iloc[0]
    parent = A[A.name == win.parent].iloc[0]
    _header('Final', win['name'])
    f1, f2 = st.columns([1.2, 1], gap='large')
    with f1:
        viewer.crystal(data.pipeline_cif(win.id), '볼 & 스틱', 1, True, True, height=380, highlight=['Zr', 'O'])
    with f2:
        ui.item(win['name'], win.total, rank=1, tag='AI추천 · 3,657개 중 1위',
                deliv=f'원본 {win.parent} 대비 {win.total - parent.total:+.1f}점 · DFT 1차 검증 완료', stars=win.stability / 100)
        m = st.columns(3)
        m[0].metric('안정성 / 100', f'{win.stability:.1f}')
        m[1].metric('포집 / 40', f'{win.capture:.1f}')
        m[2].metric('탈착 · 재사용', f'{win.desorption:.0f} · {win.reuse:.0f}')
        st.download_button('CIF 다운로드', data.pipeline_cif(win.id), file_name=f'{win.id}.cif')
    ui.section('수정본 <em>상위 5개</em>', ('B-2 전체 보기', 'b2'))
    _score_bars(B.head(5), height=300)
