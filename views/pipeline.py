import plotly.graph_objects as go
import streamlit as st
from moflab import data, ui, viewer
from moflab.pipeline import LABELS, WEIGHTS

A, B, final = data.stage_a(), data.stage_b(), data.final_pick()
top3 = A.head(3)
COLORS = {'stability': '#0053D6', 'capture': '#24A0C8', 'desorption': '#2BB673', 'reuse': '#FFB020'}

def score_bars(frame, height=None):
    """Stacked horizontal bars: the four parts of the 200-point score."""
    fig = go.Figure()
    for k in WEIGHTS:
        fig.add_bar(y=frame['name'], x=frame[k], name=f'{LABELS[k]} ({WEIGHTS[k]})', orientation='h',
                    marker_color=COLORS[k], hovertemplate='%{y} · ' + LABELS[k] + ' %{x:.1f}<extra></extra>')
    fig.update_layout(barmode='stack', height=height or 60 + 36 * len(frame), xaxis=dict(range=[0, 200], title=None),
                      yaxis=dict(autorange='reversed', title=None), margin=dict(t=48),
                      legend=dict(orientation='h', yanchor='bottom', y=1.02, x=0))
    st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})

st.markdown('<div class="eyebrow">MOF Recovery Lab</div>', unsafe_allow_html=True)
st.title('인 포집 최적 MOF 찾기')
st.markdown('<p class="sub">A. 현존 MOF 중 최고점 3개 → B. 연결 · 원소를 바꿔 다시 측정 → Final · 200점 만점</p>',
            unsafe_allow_html=True)

# ── Final summary ───────────────────────────────────────────────────
win = B.iloc[0]
parent = A[A.name == win.parent].iloc[0]
c1, c2, c3, c4 = st.columns([1.4, 1, 1, 1])
c1.markdown(f'''<div class="card win" style="padding:14px 18px"><p style="opacity:.85;font-size:12px;font-weight:700">
  🏆 FINAL</p><div class="big" style="font-size:26px;margin:2px 0 4px">{win["name"]}</div>
  <p style="font-size:13px">{win.parent}의 {win.change} 수정</p></div>''', unsafe_allow_html=True)
c2.metric('최종 점수 / 200', f'{win.total:.1f}', f'{win.total - parent.total:+.1f} (원본 대비)')
c3.metric('A 단계 평가', f'{len(A):,}개')
c4.metric('B 단계 수정', f'{(B.change != "원본").sum()}개')

st.write('')
tabs = st.tabs(['A-1 · 데이터', 'A-2 · 점수 측정', 'A-3 · 최종 3개', 'B-1 · 수정', 'B-2 · 재측정', 'Final'])

# ── A-1 ─────────────────────────────────────────────────────────────
with tabs[0]:
    st.markdown('#### 데이터베이스에서 MOF 가져오기')
    counts = A.source.value_counts()
    cols = st.columns(len(counts) + 1)
    for col, (src, n) in zip(cols, counts.items()):
        col.metric(src, f'{n:,}개')
    cols[-1].metric('합계', f'{len(A):,}개')
    ui.note('CoRE MOF 2025: 실험 구조 + 기공 특성 · MOFSimplify(WS24): 문헌 안정성 라벨이 있는 MOF')
    metals = A.metal.value_counts().head(12)
    fig = go.Figure(go.Bar(x=metals.index, y=metals.values, marker_color='#9DB8D9'))
    fig.update_layout(title='금속별 MOF 수', height=280)
    st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})

# ── A-2 ─────────────────────────────────────────────────────────────
with tabs[1]:
    st.markdown('#### 모든 MOF를 같은 AI 모델로 200점 만점 채점')
    w = st.columns(4)
    for col, (k, how) in zip(w, [('stability', '절대평가 · AI 물 안정성'), ('capture', '상대평가 · z-score'),
                                 ('desorption', '상대평가 · z-score'), ('reuse', '상대평가 · z-score')]):
        col.metric(LABELS[k], f'{WEIGHTS[k]}점', how, delta_color='off')
    ui.note('동점이면 네 점수가 고른(불균형 z가 낮은) MOF가 앞')
    fig = go.Figure(go.Histogram(x=A.total, nbinsx=50, marker_color='#65A0E0'))
    for _, r in top3.iterrows():
        fig.add_vline(x=r.total, line_color='#0053D6', line_dash='dot')
    fig.update_layout(title='총점 분포 (점선 = 상위 3개)', height=280, xaxis_title='총점 / 200')
    st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
    q = st.text_input('검색', placeholder='MOF 이름 · 금속 (예: UiO-66, Zr)', label_visibility='collapsed')
    view = A if not q else A[(A.name + ' ' + A.metal.fillna('')).str.contains(q, case=False, regex=False)]
    st.dataframe(view[['rank', 'name', 'source', 'metal', 'total', 'stability', 'capture', 'desorption', 'reuse']]
                 .rename(columns={'rank': '순위', 'name': 'MOF', 'source': '출처', 'metal': '금속', 'total': '총점',
                                  'stability': '안정성', 'capture': '포집', 'desorption': '탈착', 'reuse': '재사용'}),
                 hide_index=True, width='stretch', height=360,
                 column_config={'총점': st.column_config.ProgressColumn(min_value=0, max_value=200, format='%.1f'),
                                **{c: st.column_config.NumberColumn(format='%.1f') for c in ['안정성', '포집', '탈착', '재사용']}})

# ── A-3 ─────────────────────────────────────────────────────────────
with tabs[2]:
    st.markdown('#### 최고점 3개 = 최종 MOF')
    score_bars(top3)
    names = top3.name.tolist()
    pick = st.segmented_control('MOF', names, default=names[0], key='a3_pick') or names[0]
    r = top3[top3.name == pick].iloc[0]
    v, info = st.columns([1.5, 1], gap='large')
    with v:
        viewer.crystal(data.pipeline_cif(r.id.split(':', 1)[1]), '스틱', 1, True, False, height=400, highlight=['Zr'])
    with info:
        ui.kv([('순위', f'{r["rank"]}위'), ('총점', f'{r.total:.1f} / 200'), ('출처', r.source), ('금속', r.metal),
               ('기공 (PLD)', f'{r.pld_A:.1f} Å'), ('표면적', f'{r.gsa_m2_g:,.0f} m²/g')])

# ── B-1 ─────────────────────────────────────────────────────────────
with tabs[3]:
    st.markdown('#### 최종 3개의 연결(링커) · 원소를 바꿈')
    a, b = st.columns(2)
    with a:
        ui.card('링커 바꾸기 · 7종', '고리의 H를 –NH₂ · –OH · –NO₂ · –COOH · –SO₃H · –F · –CH₃로 치환', '🔗')
    with b:
        ui.card('원소 바꾸기 · 6종', '노드의 Zr를 Hf · Ce · Th · Ti · Fe · Al로 교체 (CHGNet 에너지)', '⚛️')
    st.write('')
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

# ── B-2 ─────────────────────────────────────────────────────────────
with tabs[4]:
    st.markdown('#### 수정한 MOF를 같은 AI 모델로 다시 채점')
    par2 = st.segmented_control('원본', names, default=names[0], key='b2_parent') or names[0]
    group = B[B.parent == par2].sort_values('total', ascending=False)
    base = group[group.change == '원본'].total.iloc[0]
    fig = go.Figure(go.Bar(x=group.total - base, y=group.name, orientation='h',
                           marker_color=['#0053D6' if d > 0 else '#C9D4DF' if d == 0 else '#FF7D45'
                                         for d in group.total - base],
                           text=[f'{d:+.1f}' for d in group.total - base], textposition='outside'))
    fig.update_layout(title=f'원본({base:.1f}점) 대비 점수 변화', height=80 + 26 * len(group),
                      yaxis=dict(autorange='reversed', title=None), xaxis_title='점수 변화')
    st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
    st.dataframe(B[['rank', 'name', 'change', 'detail', 'total', 'stability', 'capture', 'desorption', 'reuse']]
                 .rename(columns={'rank': '순위', 'name': 'MOF', 'change': '종류', 'detail': '수정 내용', 'total': '총점',
                                  'stability': '안정성', 'capture': '포집', 'desorption': '탈착', 'reuse': '재사용'}),
                 hide_index=True, width='stretch', height=360,
                 column_config={'총점': st.column_config.ProgressColumn(min_value=0, max_value=200, format='%.1f'),
                                **{c: st.column_config.NumberColumn(format='%.1f') for c in ['안정성', '포집', '탈착', '재사용']}})

# ── Final ───────────────────────────────────────────────────────────
with tabs[5]:
    st.markdown(f'#### 가장 점수가 높은 MOF · {win["name"]}')
    f1, f2 = st.columns([1.4, 1], gap='large')
    with f1:
        viewer.crystal(data.pipeline_cif(win.id), '볼 & 스틱', 1, True, True, height=420, highlight=['Zr', 'O'])
    with f2:
        score_bars(B.head(5), height=280)
        ui.kv([('원본', f'{win.parent} ({parent.total:.1f}점)'), ('수정', win.detail),
               ('최종 점수', f'{win.total:.1f} / 200'), ('안정성', f'{win.stability:.1f} / 100'),
               ('포집 · 탈착 · 재사용', f'{win.capture:.1f} · {win.desorption:.1f} · {win.reuse:.1f}')])
    st.download_button('최종 MOF 구조 (CIF)', data.pipeline_cif(win.id), file_name=f'{win.id}.cif',
                       icon=':material/download:')
