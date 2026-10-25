import plotly.express as px
import streamlit as st
from moflab import data, ui

ui.heading('Database', '후보 탐색', 'CoRE MOF 2025 · 2,737개 구조 + AI 물 안정성 지수')
df = data.catalog()

with st.container(border=True):
    q = st.text_input('검색', placeholder='이름 · 금속 · 화학식 · DOI (예: Zr, Cu, 10.1021)',
                      label_visibility='collapsed')
    f1, f2, f3, f4 = st.columns(4)
    min_idx = f1.slider('물 안정성 지수 ≥', 0, 100, 70)
    metals = f2.multiselect('금속', df.metal.value_counts().index.tolist(),
                            placeholder='전체')
    lcd = f3.slider('최대 기공 지름 LCD (Å)', 0.0, float(df.lcd_A.max().round()), (3.0, 30.0))
    domain_only = f4.toggle('학습 범위 안쪽만', True)
    pld_min = f4.toggle('인산염 통과 가능 (PLD ≥ 4.8 Å)', False,
                        help='인산 이온(PO₄³⁻)의 열화학 반지름 약 2.4 Å → 지름 약 4.8 Å를 기준으로 한 단순 기하 필터입니다. '
                             '수화 껍질은 고려하지 않았고, 표면·결함 자리 흡착은 기공 밖에서도 일어날 수 있습니다.')

view = df[df.water_prob.notna() & (df.water_index >= min_idx) & df.lcd_A.between(*lcd)]
if metals:
    view = view[view.metal.isin(metals)]
if domain_only:
    view = view[view.in_domain == True]  # noqa: E712 (nullable bool column)
if pld_min:
    view = view[view.pld_A >= 4.8]
if q:
    hay = (view.display_name.fillna('') + ' ' + view.metal.fillna('') + ' ' +
           view.formula.fillna('') + ' ' + view.doi.fillna(''))
    view = view[hay.str.contains(q, case=False, regex=False)]

m = st.columns(4)
m[0].metric('조건에 맞는 후보', f'{len(view):,}개')
m[1].metric('평균 지수', f'{view.water_index.mean():.1f}' if len(view) else '—')
m[2].metric('금속 종류', f'{view.metal.nunique()}종')
m[3].metric('중앙 LCD', f'{view.lcd_A.median():.1f} Å' if len(view) else '—')

tab_table, tab_map = st.tabs(['목록', '특성 지도'])
with tab_table:
    cols = {'display_name': '이름', 'metal': '금속', 'formula': '화학식', 'water_index': '물 안정성 지수',
            'band': '신뢰', 'lcd_A': 'LCD (Å)', 'pld_A': 'PLD (Å)', 'gsa_m2_g': '표면적 (m²/g)',
            'void_fraction': '공극률', 'topology': '위상', 'year': '보고 연도', 'doi': 'DOI'}
    table = view.sort_values('water_index', ascending=False)
    event = st.dataframe(
        table[list(cols)].rename(columns=cols), hide_index=True, width='stretch', height=460,
        on_select='rerun', selection_mode='single-row',
        column_config={'물 안정성 지수': st.column_config.ProgressColumn(min_value=0, max_value=100, format='%.1f'),
                       'LCD (Å)': st.column_config.NumberColumn(format='%.2f'),
                       'PLD (Å)': st.column_config.NumberColumn(format='%.2f'),
                       '표면적 (m²/g)': st.column_config.NumberColumn(format='%.0f'),
                       '공극률': st.column_config.NumberColumn(format='%.2f'),
                       '보고 연도': st.column_config.NumberColumn(format='%d')})
    if event.selection.rows:
        picked = table.iloc[event.selection.rows[0]]
        st.session_state['entry_id'] = picked.material_id
        c1, c2 = st.columns([3, 1])
        c1.success(f'선택: **{picked.display_name}** ({picked.metal})')
        c2.page_link('views/entry.py', label='3D 구조 상세 열기 →', icon=':material/deployed_code:')
    st.download_button('필터 결과 CSV', table.to_csv(index=False).encode('utf-8-sig'),
                       file_name='mof_candidates.csv', mime='text/csv')

with tab_map:
    ui.legend()
    plot = view if len(view) else df.dropna(subset=['water_prob'])
    fig = px.scatter(plot, x='lcd_A', y='water_index', color='band', size='void_fraction', size_max=11,
                     hover_name='display_name', hover_data={'metal': True, 'gsa_m2_g': ':.0f', 'band': False},
                     color_discrete_map={label: color for _, label, color in data.BANDS},
                     labels={'lcd_A': '최대 기공 지름 LCD (Å)', 'water_index': '물 안정성 지수', 'band': '신뢰'},
                     log_x=True)
    fig.update_layout(height=520, legend=dict(orientation='h', y=1.08))
    st.plotly_chart(fig, width='stretch')
