"""AI 예측: pick a metal node and an organic linker, see the real MOF made from them and how the AI scores it.

The AI's 12 inputs and the pore size come from a real crystal structure, so the page looks the chosen
node + linker up among MOFs that were actually made (data/predict/catalog.json) and shows their stage-A
scores with the reasons behind each one. Advanced users can still score their own computed descriptors.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from moflab import builder, data, pipeline, ui, viewer
from moflab.descriptors import FEATURES

NODE_COLORS = {'zr6': '#636efa', 'zn4o': '#EF553B', 'zntet': '#00cc96', 'cupw': '#ab63fa',
               'mchain': '#FFA15A', 'm3o': '#19d3f3', 'm74': '#FF6692'}

st.title('AI 예측: 노드와 링커로 MOF 채점하기')
st.markdown('MOF는 금속 노드(금속 덩어리)와 유기 링커가 이어진 결정이다. 같은 금속이라도 노드 모양이 다르면 전혀 다른 '
            'MOF가 되고(MOF-5와 ZIF-8은 둘 다 Zn이다), 작용기가 같아도 링커 모양이 다르면 기공 크기와 붙잡는 분자가 달라진다.')
st.markdown('그래서 금속 노드와 링커를 직접 고르면, 그 둘로 실제로 만들어진 MOF를 데이터베이스에서 찾아 같은 AI가 매긴 점수를 '
            '보여 준다. 기공 통로 지름(PLD)과 표면적은 구조가 정하는 값이라 실제 결정 구조에서 계산한 값을 그대로 쓴다.')

cat = builder.catalog()
st.subheader('1. 금속 노드 고르기')
node_ids = [n['id'] for n in cat['nodes']]
node_id = st.selectbox('금속 노드', node_ids, format_func=lambda i: f"{builder.node(i)['label']}  ({builder.node(i)['formula']})")
node = builder.node(node_id)
metal = node['metals'][0]
if len(node['metals']) > 1:
    metal = st.radio('이 노드를 만드는 금속', node['metals'], horizontal=True)

st.subheader('2. 유기 링커 고르기')
known = builder.known_linkers(node_id, metal)
linker_ids = known + [l['id'] for l in cat['linkers'] if l['id'] not in known]
linker_id = st.selectbox('유기 링커', linker_ids,
                         format_func=lambda i: builder.linker(i)['label'] + ('  ✓ 실제 MOF 있음' if i in known else ''))
link = builder.linker(linker_id)

left, right = st.columns(2, gap='large')
with left:
    st.markdown(f"**금속 노드: {node['label']}**")
    viewer.molecule(builder.node_sdf(node_id, metal), 'sdf', metals=[metal], height=280)
    ui.kv([('조성', node['formula']), ('금속', metal), ('링커 연결', node['links']), ('열린 금속 자리', node['oms'])])
    st.caption(node['about'] + ' 짧은 막대 끝의 C는 링커가 붙는 자리다.')
with right:
    st.markdown(f"**유기 링커: {link['label']}**")
    viewer.molecule(builder.linker_sdf(linker_id), 'sdf', height=280)
    ui.kv([('팔 (붙는 곳)', link['arms']), ('고리', link['rings']), ('작용기', link['group'])])
    st.caption(link['about'])

st.subheader('3. 이 조합으로 만든 MOF')
R = builder.records()
entry = builder.combo(node_id, metal, linker_id)
pick_id = None
if entry is None:
    st.info('이 노드와 링커로 만들어진 MOF는 데이터에 없다. AI가 쓰는 12개 특성과 기공 크기는 실제 결정 구조에서 계산하는 '
            '값이라, 구조가 없는 조합에는 점수를 매기지 않는다.')
    same_node, same_linker = builder.made_with_node(node_id, metal), builder.made_with_linker(linker_id)
    if same_node:
        st.markdown('이 노드로 만든 MOF: ' + ' / '.join(f'{lk} → **{mof}**' for lk, mof in same_node))
    if same_linker:
        st.markdown('이 링커로 만든 MOF: ' + ' / '.join(f'{nd} → **{mof}**' for nd, mof in same_linker))
else:
    names = [r['name'] for r in entry['records']]
    chosen = names[0]
    if len(names) > 1:
        chosen = st.radio('이 조합의 MOF', names, horizontal=True)
        st.caption('같은 노드와 링커라도 서로 이어지는 방식(위상)이나 시료 상태가 다르면 다른 MOF가 된다.')
    pick_id = entry['records'][names.index(chosen)]['id']
    row = R[R.rec_id == pick_id].iloc[0]
    st.markdown(f'#### {chosen}')
    m = st.columns(4)
    m[0].metric('총점 / 200', f'{row.total:.1f}', f"3,657개 중 {int(row['rank'])}위", delta_color='off')
    m[1].metric('안정성 / 100', f'{row.stability:.1f}', data.band(row.water_prob)[0], delta_color='off')
    m[2].metric('포집 / 40 · 탈착 / 35', f'{row.capture:.1f} · {row.desorption:.1f}')
    m[3].metric('재사용 / 25', f'{row.reuse:.1f}')
    lab = builder.lab_class(row.db_name)
    info, view = st.columns([1, 1.3], gap='large')
    with info:
        ui.kv([('데이터 출처', row.source), ('기공 통로 지름 (PLD)', f'{row.pld_A:.1f} Å (구조에서 계산)'),
               ('가장 큰 기공 (LCD)', f'{row.lcd_A:.1f} Å'), ('표면적', f'{row.gsa_m2_g:,.0f} m²/g'),
               ('AI 물 안정성 확률', f'{row.water_prob:.2f}'),
               ('논문 실험 결과 (물 안정성)', builder.CLASS[lab] if lab else '기록 없음')])
        st.markdown('**점수가 이렇게 나온 이유**')
        for name, pts, why in builder.explain(row):
            st.markdown(f'- **{name} {pts}**: {why}')
        ui.note('포집과 탈착은 공개 실험 데이터가 없어서 화학 규칙으로 계산한다. 그래서 금속이 같으면 링커를 바꿔도 점수가 '
                '비슷하고, 노드의 금속이 바뀌면 크게 달라진다. 포집, 탈착, 재사용은 3,657개 안에서의 위치(z-score)를 '
                '점수로 바꾼 값이다.')
    with view:
        cif = builder.structure_cif(entry['structure'])
        if cif:
            st.markdown('**합친 MOF 결정 구조**')
            viewer.crystal(cif, '스틱', 1, False, False, height=400, highlight=[metal])
            if entry['structure'].startswith('core:'):
                st.caption('그림은 CoRE MOF 2025에 실린 같은 MOF의 결정 구조다.')
        else:
            st.caption('이 MOF는 저장소에 3D 결정 구조 파일이 없어서 위의 노드와 링커 그림만 보여 준다.')

st.subheader('4. 다른 조합과 비교')
st.markdown('노드나 링커를 바꾸면 같은 AI의 점수가 이만큼 달라진다. 막대 색은 금속 노드 종류이고, 테두리가 있는 막대가 지금 고른 MOF다.')
order = R.sort_values('total')
fig = go.Figure(go.Bar(
    x=order.total, y=order.display, orientation='h',
    marker=dict(color=[NODE_COLORS[n] for n in order.node],
                line=dict(color=['#ffffff' if i == pick_id else 'rgba(0,0,0,0)' for i in order.rec_id], width=2.5)),
    customdata=[[builder.node(n)['label'], builder.linker(l)['label'], s, c, d, u]
                for n, l, s, c, d, u in zip(order.node, order.linker, order.stability, order.capture, order.desorption, order.reuse)],
    hovertemplate='%{y} · 총점 %{x:.1f}<br>%{customdata[0]} + %{customdata[1]}<br>'
                  '안정성 %{customdata[2]:.1f} · 포집 %{customdata[3]:.1f} · 탈착 %{customdata[4]:.1f} · 재사용 %{customdata[5]:.1f}<extra></extra>'))
fig.update_layout(height=60 + 22 * len(order), xaxis=dict(range=[0, 200], title='총점 / 200'), yaxis=dict(title=None))
st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
st.caption('  '.join(f"■ {builder.node(n)['label']}" for n in NODE_COLORS))

with st.expander('고급: 직접 계산한 구조 특성으로 채점하기 (CSV)'):
    st.markdown('새 MOF의 결정 구조가 있다면 molSimplify로 12개 특성을, Zeo++ 같은 프로그램으로 기공 통로 지름(PLD)을 계산해 '
                '올릴 수 있다. 값은 모두 구조에서 계산한 것이어야 한다.')
    cols = ['name', *FEATURES, 'metal', 'pld_A']
    st.download_button('빈 양식 CSV', pd.DataFrame(columns=cols + ['open_metal_site', 'group_effect']).to_csv(index=False),
                       file_name='mof_features_template.csv')
    up = st.file_uploader('CSV', type='csv', label_visibility='collapsed')
    if up is not None:
        frame = pd.read_csv(up)
        missing = [c for c in cols if c not in frame.columns]
        if missing:
            st.error('필요한 열이 없다: ' + ', '.join(missing))
        else:
            try:
                pred = data.predict_water(frame)
            except ValueError as e:
                st.error(str(e))
            else:
                oms = frame['open_metal_site'] if 'open_metal_site' in frame else pd.Series([None] * len(frame))
                grp = frame['group_effect'] if 'group_effect' in frame else pd.Series(['0'] * len(frame))
                raw = [pipeline.raw_scores(p, mt, pl, g, {True: True, False: False}.get(o), str(ge) if ge in ('+', '-', '0') else '0')
                       for p, mt, pl, g, o, ge in zip(pred.water_prob, frame['metal'], frame['pld_A'], frame['GSA'], oms, grp)]
                scored = pipeline.score(pd.DataFrame([{'name': n, 'water_prob': p, **r}
                                                      for n, p, r in zip(frame['name'], pred.water_prob, raw)]),
                                        {k: tuple(v) for k, v in data.pipeline_stats().items()})
                scored['학습 범위'] = ['안' if d else '밖 (덜 믿어야 함)' for d in pred.in_domain]
                st.dataframe(scored[['name', 'total', 'stability', 'capture', 'desorption', 'reuse', '학습 범위']].rename(
                    columns={'name': 'MOF', 'total': '총점', 'stability': '안정성', 'capture': '포집',
                             'desorption': '탈착', 'reuse': '재사용'}), hide_index=True, width='stretch')
