import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from moflab import data, ui, viewer

ui.heading('Final candidates', '최종 후보 MOF',
           'AI 1차 선별과 문헌 근거로 고른 실험 후보입니다. 구조를 회전·확대해 금속 노드와 링커의 배열을 확인할 수 있습니다.')

items = data.finalists()
names = [f"{f['name']} · {f['role']}" for f in items]
choice = st.segmented_control('후보', names, default=names[0], label_visibility='collapsed') or names[0]
f = items[names.index(choice)]

view, info = st.columns([1.6, 1])
with info:
    pred = data.predict_water(f['descriptor_frame']).iloc[0] if f['descriptor_frame'] is not None else None
    ui.confidence(None if pred is None else float(pred.water_prob), '우리 RF 모델 · 물 안정성 지수')
    st.write('')
    ui.kv([('역할', f['role']), ('금속', f['metal']), ('노드', f['node']), ('링커', f['linker']),
           ('MOFSimplify', f['mofsimplify_status']),
           ('학습 범위', '—' if pred is None else ('안쪽' if pred.in_domain else '바깥 (외삽 주의)')),
           ('가장 가까운 학습 MOF', '—' if pred is None else pred.nearest_training_name),
           ('구조 출처', f['cif_source'])])
with view:
    o1, o2, o3, o4 = st.columns([1.3, 1, 1, 1])
    style = o1.selectbox('표현', list(viewer.STYLES), key='fin_style')
    cells = o2.selectbox('단위 격자', [1, 2, 3], index=1 if len(f['cif_text']) < 20000 else 0,
                         format_func=lambda n: f'{n}×{n}×{n}', key=f"fin_cells_{f['id']}")
    show_cell = o3.toggle('격자 상자', True, key='fin_box')
    spin = o4.toggle('회전', False, key='fin_spin')
    viewer.crystal(f['cif_text'], style, cells, show_cell, spin, height=540, highlight=[f['metal']])

st.subheader('선정 근거')
a, b = st.columns(2)
with a:
    ui.card('인산염과의 상호작용 가설', f['rationale'])
with b:
    ui.card('다음 실험에서 확인할 것', f['check_next'])

st.subheader('후보 비교')
rows = []
for x in items:
    p = data.predict_water(x['descriptor_frame']).iloc[0] if x['descriptor_frame'] is not None else None
    rows.append({'MOF': x['name'], '역할': x['role'], '금속': x['metal'],
                 'MOFSimplify (MIT)': x['mofsimplify_score'],
                 '우리 RF 모델': None if p is None else round(float(p.water_prob), 3),
                 '학습 범위': None if p is None else ('안쪽' if p.in_domain else '바깥')})
table = pd.DataFrame(rows)
fig = go.Figure()
for col, color in [('MOFSimplify (MIT)', '#0053D6'), ('우리 RF 모델', '#24A0C8')]:
    fig.add_bar(name=col, x=table.MOF, y=table[col], marker_color=color,
                text=[('' if v != v or v is None else f'{v:.2f}') for v in table[col]], textposition='outside')
fig.add_hline(y=0.5, line_dash='dot', line_color='#FF7D45', annotation_text='안정 판정 기준 0.5')
fig.update_layout(barmode='group', height=330, yaxis=dict(range=[0, 1.05], title='물에 안정할 확률'),
                  legend=dict(orientation='h', y=1.15))
c1, c2 = st.columns([1.2, 1])
c1.plotly_chart(fig, width='stretch')
c2.dataframe(table, hide_index=True, width='stretch')
ui.note('두 모델은 같은 계열의 공개 라벨을 쓰지만 서로 다른 모델입니다(우리 RF는 독립 재학습). 둘 다 문헌 클래스 기반 '
        '"물 안정성" 분류이며, 인산염 포집·탈착 성능을 예측하지 않습니다. MIL-100(Fe)는 특성 계산 실패로 '
        '판정을 비워 두었고 이를 불안정으로 해석하지 않습니다.')
st.download_button('선택한 구조 CIF 다운로드', f['cif_text'], file_name=f['cif'], mime='chemical/x-cif')
