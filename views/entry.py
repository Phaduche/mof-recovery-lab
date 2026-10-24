import plotly.graph_objects as go
import streamlit as st
from moflab import data, ui, viewer

df = data.catalog()
pred = df.dropna(subset=['water_prob']).sort_values('water_prob', ascending=False)
options = pred.material_id.tolist() + df[df.water_prob.isna()].material_id.tolist()
labels = dict(zip(df.material_id, df.display_name + ' · ' + df.metal.fillna('?')))
current = st.session_state.get('entry_id', options[0])

ui.heading('Structure entry', '구조 상세')
mid = st.selectbox('구조 선택 (지수 높은 순)', options, index=options.index(current) if current in options else 0,
                   format_func=labels.get)
st.session_state['entry_id'] = mid
r = df.set_index('material_id').loc[mid]

st.markdown(f"### {r.display_name}")
st.markdown(f"<span class='pill' style='background:#E8F0FD;color:#0053D6'>{r.metal}</span>"
            f"<span class='pill' style='background:#EEF2F5;color:#13263A'>{r.formula or '화학식 미상'}</span>"
            f"<span class='pill' style='background:#EEF2F5;color:#13263A'>CoRE MOF 2025 · {r.structure_status}</span>",
            unsafe_allow_html=True)
st.write('')

view, side = st.columns([1.6, 1])
with side:
    ui.confidence(r.water_prob)
    st.write('')
    ui.kv([('학습 범위', '—' if r.in_domain is None or r.in_domain != r.in_domain else ('안쪽' if r.in_domain else '바깥')),
           ('트리 간 편차', '—' if r.tree_sd != r.tree_sd else f'{r.tree_sd:.3f}'),
           ('가장 가까운 학습 MOF', r.nearest_training_name or '—'),
           ('원자 수 (단위 격자)', int(r.n_atoms)), ('공간군 번호', int(r.space_group)),
           ('위상 (CrystalNets)', r.topology or '—'), ('열린 금속 자리', '있음' if r.open_metal_site else '없음'),
           ('보고', f"{r.year if r.year == r.year else '—'} · {r.doi or 'DOI 없음'}")])
with view:
    cif = data.read_cif(mid)
    o1, o2, o3, o4 = st.columns([1.3, 1, 1, 1])
    style = o1.selectbox('표현', list(viewer.STYLES))
    big = (r.n_atoms or 0) > 600
    cells = o2.selectbox('단위 격자', [1, 2], format_func=lambda n: f'{n}×{n}×{n}',
                         help='원자가 많은 구조는 1×1×1을 권장합니다.')
    box = o3.toggle('격자 상자', True)
    spin = o4.toggle('회전', False)
    if cif:
        viewer.crystal(cif, style, cells, box, spin, height=520, highlight=[r.metal] if r.metal else None)
        if big and cells > 1:
            st.caption('원자 수가 많아 표시가 느릴 수 있습니다.')
    else:
        st.warning('이 항목의 CIF가 스냅숏에 없습니다.')

st.subheader('기공 · 표면 기하 특성 (Zeo++)')
g = st.columns(5)
g[0].metric('LCD', f'{r.lcd_A:.2f} Å', help='Largest cavity diameter: 가장 큰 빈 공간의 지름')
g[1].metric('PLD', f'{r.pld_A:.2f} Å', help='Pore limiting diameter: 분자가 통과할 수 있는 가장 좁은 통로')
g[2].metric('비표면적', f'{r.gsa_m2_g:,.0f} m²/g')
g[3].metric('공극률', f'{r.void_fraction:.2f}')
g[4].metric('밀도', f'{r.density_g_cm3:.2f} g/cm³')

st.subheader('전체 후보 속 위치')
fig = go.Figure()
base = df.dropna(subset=['water_prob'])
fig.add_scatter(x=base.lcd_A, y=base.water_index, mode='markers', name='CoRE 2025',
                marker=dict(size=5, color='#C9D4DF'), hoverinfo='skip')
if r.water_prob == r.water_prob:
    fig.add_scatter(x=[r.lcd_A], y=[r.water_index], mode='markers', name=r.display_name,
                    marker=dict(size=16, color=data.band(r.water_prob)[1], line=dict(width=2, color='#13263A')))
fig.update_layout(height=340, xaxis=dict(type='log', title='LCD (Å)'), yaxis_title='물 안정성 지수',
                  legend=dict(orientation='h', y=1.12))
st.plotly_chart(fig, width='stretch')
if cif:
    st.download_button('CIF 다운로드', cif, file_name=f'{r["name"]}.cif', mime='chemical/x-cif')
ui.note('구조와 기하 특성은 CoRE MOF 2025(CC BY 4.0) 원자료입니다. 물 안정성 지수만 우리 모델의 예측입니다.')
