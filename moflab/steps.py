"""The six pipeline steps (A-1 … Final), each rendered as its own top-level page."""
import plotly.graph_objects as go
import streamlit as st
from . import data, ui, viewer
from .pipeline import LABELS, WEIGHTS

COLORS = {'stability': '#636efa', 'capture': '#EF553B', 'desorption': '#00cc96', 'reuse': '#ab63fa'}
TABLE_COLS = {'rank': '순위', 'name': 'MOF', 'source': '출처', 'metal': '금속', 'change': '종류', 'detail': '수정 내용',
              'total': '총점', 'stability': '안정성', 'capture': '포집', 'desorption': '탈착', 'reuse': '재사용'}

def _header(title, intro, ai=None):
    """Page title, the model used (if any) and a plain explanation for first-time visitors."""
    st.title(title)
    if ai:
        st.caption(f'모델: {ai}')
    for para in intro:
        st.markdown(para)

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
    counts = A.source.value_counts()
    _header('데이터베이스에서 MOF 가져오기', [
        '인산염을 붙잡았다가 다시 떼어 낼 MOF를 찾기 위해, 먼저 후보가 될 MOF를 공개 데이터베이스 두 곳에서 모으는 단계다.',
        f'CoRE MOF 2025는 실제로 합성되었다고 보고된 MOF 구조를 모은 데이터베이스이고({counts.get("CoRE MOF 2025", 0):,}개), '
        f'MOFSimplify(WS24)는 물 안정성 실험 결과가 붙어 있는 MOF 모음이다({counts.get("MOFSimplify (WS24)", 0):,}개). '
        f'둘을 합친 {len(A):,}개가 다음 단계에서 채점할 후보다.',
        '아래 그래프는 후보들을 금속 종류별로 센 것이다. 금속은 MOF 뼈대의 마디(노드)를 이루고, 인산염이 달라붙는 자리가 된다.',
    ])
    cols = st.columns(len(counts) + 1)
    for col, (src, n) in zip(cols, counts.items()):
        col.metric(src, f'{n:,}개')
    cols[-1].metric('합계', f'{len(A):,}개')
    metals = A.metal.value_counts().head(12)
    fig = go.Figure(go.Bar(x=metals.index, y=metals.values, marker_color='#636efa'))
    fig.update_layout(title='금속별 MOF 수', height=300)
    st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})

def a2():
    A = data.stage_a()
    _header('AI로 200점 만점 채점', [
        f'모은 {len(A):,}개 각각에 200점 만점 점수를 매기는 단계다. 점수는 물 안정성(100점), 인 포집(40점), 탈착(35점), '
        '재사용(25점)을 더한 값이다.',
        '물 안정성은 논문 실험값으로 학습한 Random Forest가 예측한 "물속에서 구조가 유지될 확률"에 100을 곱한 점수다. '
        '나머지 세 항목은 금속과 인산염의 결합력, 표면적, 기공 크기 같은 화학 원리로 값을 계산한 뒤, '
        f'{len(A):,}개 가운데 얼마나 위쪽에 있는지로 점수를 매겼다.',
        '그래프는 총점이 어떻게 퍼져 있는지 보여 주고, 점선은 가장 높은 3개다. 아래 검색창에 MOF 이름이나 금속(예: Zr)을 '
        '넣으면 표에서 항목별 점수를 볼 수 있다.',
    ], 'ML · Random Forest + 점수 규칙')
    w = st.columns(4)
    for col, k in zip(w, WEIGHTS):
        col.metric(LABELS[k], f'{WEIGHTS[k]}점')
    fig = go.Figure(go.Histogram(x=A.total, nbinsx=50, marker_color='#636efa'))
    for _, r in A.head(3).iterrows():
        fig.add_vline(x=r.total, line_color='#ccc', line_dash='dot')
    fig.update_layout(title='총점 분포 (점선 = 상위 3개)', height=280, xaxis_title='총점 / 200')
    st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
    q = st.text_input('검색', placeholder='MOF 이름 · 금속 (예: UiO-66, Zr)', label_visibility='collapsed')
    view = A if not q else A[(A.name + ' ' + A.metal.fillna('')).str.contains(q, case=False, regex=False)]
    _table(view, ['rank', 'name', 'source', 'metal', 'total', 'stability', 'capture', 'desorption', 'reuse'])

def a3():
    top3 = _finalists()
    listed = ', '.join(f'{r["name"]} {r.total:.1f}점' for _, r in top3.iterrows())
    zr_only = (top3.metal == 'Zr').all()
    _header('최고점 3개', [
        f'A-2에서 총점이 가장 높은 3개를 고르는 단계다. {listed}이다.'
        + (' 셋 다 지르코늄(Zr) MOF다. Zr⁴⁺ 이온은 전하가 크고 단단해서 링커와 강하게 결합하기 때문에, '
           '물 분자가 끼어들어도 구조가 잘 무너지지 않는다.' if zr_only else ''),
        '막대는 총점이 네 항목으로 어떻게 나뉘는지 보여 준다. 아래에서 MOF 이름을 누르면 3D 구조와 기공 크기(PLD), '
        '표면적이 나온다. 구조는 마우스로 끌어서 돌리고, 스크롤로 확대할 수 있다.',
    ])
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
    mods = B[B.change != '원본']
    n_link = mods[mods.change == '링커'].groupby('parent').size().max()
    n_metal = mods[mods.change == '원소'].groupby('parent').size().max()
    swap_n = len(data.metal_swap()) - 1
    _header('링커 · 원소 바꾸기', [
        f'상위 3개를 더 좋게 만들 수 있는지 컴퓨터로 구조를 바꿔 보는 단계다. 링커에 작용기 {n_link}종'
        '(–NH₂, –OH, –NO₂, –COOH, –SO₃H, –F, –CH₃)을 붙이거나, 마디의 금속 Zr을 다른 금속 '
        f'{n_metal}종(Hf, Ce, Th, Ti, Fe, Al)으로 바꿨다. 3개마다 {n_link + n_metal}가지씩, 모두 {len(mods)}개다.',
        '아래에서 원본 MOF와 수정 내용을 고르면 원본과 바꾼 구조를 나란히 볼 수 있다.',
        '아래 그래프는 금속을 바꿨을 때 에너지가 얼마나 달라지는지(ΔE, 금속 1개당)를 딥러닝 모델 CHGNet으로 계산한 것이다. '
        f'같은 Zr 마디를 가진 UiO-66-NH₂에서 Zr을 금속 {swap_n}종으로 바꿔 계산했고, 0보다 작으면 Zr보다 에너지가 낮아 '
        '더 안정하다는 뜻이다.',
    ], 'DL · CHGNet 그래프 신경망')
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
    ox_color = {4: '#636efa', 3: '#EF553B', 2: '#00cc96', 1: '#ab63fa'}
    fig = go.Figure(go.Bar(x=swap.metal, y=swap.swap_energy_eV, marker_color=[ox_color[o] for o in swap.oxidation_state],
                           text=[f'{v:+.2f}' for v in swap.swap_energy_eV], textposition='outside',
                           customdata=swap.oxidation_state, hovertemplate='%{x} (+%{customdata}가) · %{y:+.2f} eV<extra></extra>'))
    fig.add_hline(y=0, line_color='#ccc', line_width=1)
    fig.update_layout(height=340, yaxis_title='eV / 금속', xaxis_title=None)
    st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
    st.caption('막대 색 = 금속 산화수: 파랑 +4, 빨강 +3, 초록 +2, 보라 +1')

def b2():
    top3, B = _finalists(), data.stage_b()
    n_mod = int((B.change != '원본').sum())
    _header('같은 AI로 다시 채점', [
        f'B-1에서 만든 {n_mod}개를 원본 3개와 함께, A-2와 똑같은 AI와 기준으로 다시 채점하는 단계다. '
        '같은 기준으로 매겨야 원본보다 나아졌는지 바로 비교할 수 있다.',
        '아래에서 원본 MOF를 고르면, 바꾼 구조들이 원본보다 몇 점 오르거나 내렸는지 막대로 보여 준다. '
        f'파란색은 오른 것, 빨간색은 내린 것이다. 아래 표에는 {len(B)}개 전체의 순위와 항목별 점수가 있다.',
    ], 'ML · Random Forest + 점수 규칙')
    names = top3.name.tolist()
    par = st.segmented_control('원본', names, default=names[0], key='b2_parent') or names[0]
    group = B[B.parent == par].sort_values('total', ascending=False)
    base = group[group.change == '원본'].total.iloc[0]
    delta = group.total - base
    fig = go.Figure(go.Bar(x=delta, y=group.name, orientation='h', text=[f'{d:+.1f}' for d in delta],
                           marker_color=['#636efa' if d > 0 else '#666' if d == 0 else '#EF553B' for d in delta],
                           textposition='outside'))
    fig.update_layout(title=f'원본({base:.1f}점) 대비 점수 변화', height=80 + 26 * len(group),
                      yaxis=dict(autorange='reversed', title=None), xaxis_title='점수 변화')
    st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
    _table(B, ['rank', 'name', 'change', 'detail', 'total', 'stability', 'capture', 'desorption', 'reuse'])

def final():
    A, B = data.stage_a(), data.stage_b()
    win = B.iloc[0]
    parent = A[A.name == win.parent].iloc[0]
    why = ''
    if '–OH' in win['name'] and win.capture > parent.capture and win.stability > parent.stability:
        why = ' –OH는 인산염과 수소 결합을 할 수 있어서 인 포집 점수가 올랐고, 물 안정성 점수도 함께 올랐다.'
    _header(win['name'], [
        f'B-2에서 점수가 가장 높은 구조를 최종 MOF로 고르는 단계다. 최종 MOF는 {win["name"]}({win.total:.1f}점)으로, '
        f'원본 {parent["name"]}({parent.total:.1f}점)보다 {win.total - parent.total:.1f}점 높았다.' + why,
        '아래 숫자는 총점과 항목별 점수다. 그 밑 왼쪽에서 최종 MOF의 3D 구조를 돌려 볼 수 있고, 오른쪽 막대는 점수 상위 5개다. '
        '아래 버튼으로 구조 파일(CIF)을 내려받을 수 있다.',
    ])
    m = st.columns([1, 1, 1.4])
    m[0].metric('최종 점수 / 200', f'{win.total:.1f}', f'{win.total - parent.total:+.1f} (원본 대비)')
    m[1].metric('안정성 / 100', f'{win.stability:.1f}')
    m[2].metric('포집 · 탈착 · 재사용', f'{win.capture:.0f} · {win.desorption:.0f} · {win.reuse:.0f}')
    f1, f2 = st.columns([1.4, 1], gap='large')
    with f1:
        viewer.crystal(data.pipeline_cif(win.id), '볼 & 스틱', 1, True, True, height=440, highlight=['Zr', 'O'])
    with f2:
        _score_bars(B.head(5), height=300)
    st.download_button('CIF 다운로드', data.pipeline_cif(win.id), file_name=f'{win.id}.cif')
