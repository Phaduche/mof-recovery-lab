"""AI 예측: a MOF the user describes (12 MOFSimplify descriptors + a few pore/metal facts) gets the same
water-stability probability and 200-point score as the database MOFs."""
import io
import pandas as pd
import streamlit as st
from moflab import data, pipeline, ui
from moflab.descriptors import FEATURES

EXAMPLE = data.DATA / 'finalists/UiO66NH2_WS14s_descriptors_water.csv'
HELP = {'mc-Z-0-all': '금속 원자번호²', 'mc-Z-1-all': '금속-이웃 원자번호 곱 (1칸)', 'mc-Z-3-all': '금속-이웃 원자번호 곱 (3칸)',
        'D_mc-Z-1-all': '금속-이웃 원자번호 차 (1칸)', 'D_mc-Z-2-all': '금속-이웃 원자번호 차 (2칸)', 'D_mc-Z-3-all': '금속-이웃 원자번호 차 (3칸)',
        'mc-chi-3-all': '금속-이웃 전기음성도 곱 (3칸)', 'D_mc-chi-2-all': '금속-이웃 전기음성도 차 (2칸)',
        'f-lig-Z-2': '링커 원자번호 곱 (2칸)', 'f-lig-I-0': '링커 이온화 특성', 'func-S-1-all': '작용기 크기', 'GSA': '표면적 m²/g'}

st.title('AI 예측: 내 MOF 채점하기')
st.caption('MOFSimplify 특성 12개를 넣으면 데이터베이스 MOF와 같은 Random Forest로 물 안정성을 예측하고, 같은 규칙으로 200점을 매깁니다.')

how = st.radio('입력 방법', ['예시 (UiO-66-NH₂)', 'CSV 올리기', '직접 입력'], horizontal=True, label_visibility='collapsed')
frame = None
if how == '예시 (UiO-66-NH₂)':
    frame = pd.read_csv(EXAMPLE)
elif how == 'CSV 올리기':
    st.write('MOFSimplify / molSimplify가 만든 특성 CSV를 올립니다. 아래 12개 열이 있어야 합니다.')
    template = pd.DataFrame(columns=['name'] + FEATURES)
    st.download_button('빈 양식 CSV', template.to_csv(index=False), file_name='mof_features_template.csv')
    up = st.file_uploader('CSV', type='csv', label_visibility='collapsed')
    if up is not None:
        frame = pd.read_csv(up)
else:
    ex = pd.read_csv(EXAMPLE).iloc[0]
    cols = st.columns(3)
    values = {}
    for i, f in enumerate(FEATURES):
        values[f] = cols[i % 3].number_input(f, value=float(ex[f]), help=HELP.get(f), format='%.4f')
    frame = pd.DataFrame([values])

st.subheader('포집 · 탈착 · 재사용 점수에 쓰는 정보')
c = st.columns(4)
metal = c[0].text_input('금속 (원소 기호)', 'Zr')
pld = c[1].number_input('기공 통로 지름 PLD (Å)', value=3.9, min_value=0.0)
oms = c[2].selectbox('열린 금속 자리', ['모름', '있음', '없음'])
group = c[3].selectbox('작용기 효과', ['0 (중성)', '+ (–NH₂, –OH)', '− (–COOH, –SO₃H)'])
GROUP = {'0': '0', '+': '+', '−': '-'}

if frame is not None and st.button('채점하기', type='primary'):
    try:
        pred = data.predict_water(frame)
    except ValueError as e:
        st.error(str(e))
        st.stop()
    names = frame['name'].astype(str).tolist() if 'name' in frame else [f'MOF {i + 1}' for i in range(len(frame))]
    gsa = pd.to_numeric(frame['GSA'], errors='coerce')
    rows = []
    for name, p, g in zip(names, pred.water_prob, gsa):
        raw = pipeline.raw_scores(p, metal, pld, g, {'있음': True, '없음': False}.get(oms), GROUP[group[0]])
        rows.append({'name': name, 'water_prob': p, **raw})
    scored = pipeline.score(pd.DataFrame(rows), {k: tuple(v) for k, v in data.pipeline_stats().items()})
    A = data.stage_a()
    for i, r in scored.iterrows():
        pr = pred.iloc[i]
        st.subheader(r['name'])
        m = st.columns(4)
        m[0].metric('총점 / 200', f'{r.total:.1f}', f'{(A.total < r.total).mean() * 100:.0f}% 보다 높음 (3,657개 중)')
        m[1].metric('안정성 / 100', f'{r.stability:.1f}', data.band(pr.water_prob)[0])
        m[2].metric('포집 / 40 · 탈착 / 35', f'{r.capture:.1f} · {r.desorption:.1f}')
        m[3].metric('재사용 / 25', f'{r.reuse:.1f}')
        ui.kv([('물 안정성 확률', f'{pr.water_prob:.2f}'),
               ('학습 범위', '안 (예측 신뢰 가능)' if pr.in_domain else '밖 (학습 데이터와 멀어서 덜 믿어야 함)'),
               ('가장 비슷한 학습 MOF', pr.nearest_training_name),
               ('트리 180개 의견 차이 (표준편차)', f'{pr.tree_sd:.2f}'),
               ('데이터베이스 순위로 치면', f'{int((A.total > r.total).sum()) + 1}위 / {len(A):,}')])
    st.caption('안정성은 Random Forest(ML) 예측, 나머지 세 항목은 A 단계 3,657개와 같은 규칙과 z-score로 계산합니다.')
