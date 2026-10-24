import plotly.express as px
import streamlit as st
from moflab import data, ui

df = data.catalog()
val = data.validation()
src = data.sources()

ui.hero('Korea Junior Water Prize 2026 · 옹기종기',
        'AI로 찾는 인(P) 자원 회수용 MOF',
        '인은 인공적으로 만들 수 없고 자연에서 순환하지 않는 자원입니다. 우리는 하수처리장 반류수·소화 탈리액처럼 '
        '인이 농축된 흐름에서 인산염을 선택적으로 붙잡고 다시 떼어낼 수 있는 금속-유기 골격체(MOF)를, '
        '공개 구조 데이터베이스와 머신러닝으로 먼저 걸러낸 뒤 실험으로 검증합니다.')

c = st.columns(4)
c[0].metric('공개 출처 레코드', f"{sum(s['records'] for s in src):,}건")
c[1].metric('3D 구조(CIF) 후보', f'{len(df):,}개')
c[2].metric('AI 물 안정성 예측', f"{df.water_prob.notna().sum():,}건")
c[3].metric('모델 OOF ROC-AUC', f"{val['metrics']['roc_auc']:.3f}")

st.write('')
st.subheader('왜 인(P)인가')
a, b, cc = st.columns(3)
with a:
    ui.card('대체 불가능한 자원', '인은 비료·세제·식품·배터리 소재에 쓰이며 인공적으로 합성할 수 없습니다. '
            '인광석은 한정된 국가에 매장되어 있고, 한국은 거의 전량을 수입에 의존합니다.')
with b:
    ui.card('비순환 구조', '사용된 인은 하천과 바다로 흘러가 녹조(부영양화)의 원인이 되고 다시 회수되지 않습니다. '
            '버려지는 인을 되찾으면 오염 저감과 자원 확보를 동시에 할 수 있습니다.')
with cc:
    ui.card('고농도 흐름에 집중', '하천수는 인 농도가 낮아(수질 기준 수준 0.02–0.5 mg/L) 경제성이 없습니다. '
            '본선에서는 대상을 하수처리장 반류수·소화 탈리액 등 고농도 흐름의 소재 기술로 한정했습니다.')

st.write('')
st.subheader('연구 파이프라인')
steps = [('데이터 수집', 'CoRE MOF 2025·QMOF·MOFSimplify 등 6개 공개 출처에서 구조·특성·문헌 라벨 36,857건 정리'),
         ('AI 1차 선별', '문헌 물 안정성 라벨로 학습한 Random Forest가 2,565개 구조의 물 안정성 지수를 예측'),
         ('후보 결정', '물 안정성·기공 크기·금속 노드(Zr·Fe 등 인산염 친화성)를 함께 보고 후보 압축'),
         ('실험 검증', '정인산염 모사용액으로 포집·탈착·재사용을 측정하고 100점 규칙으로 평가'),
         ('데이터 환류', '실험값과 방해 이온 조건을 다시 학습 데이터로 쌓아 인산염 성능 모델로 확장')]
cols = st.columns(len(steps))
for i, (col, (t, d)) in enumerate(zip(cols, steps), 1):
    with col:
        ui.card(t, d, step=i)

st.write('')
left, right = st.columns([1.35, 1])
with left:
    st.subheader('예측 분포 한눈에 보기')
    ui.legend()
    plot = df.dropna(subset=['water_prob'])
    fig = px.histogram(plot, x='water_index', color='band', nbins=40,
                       color_discrete_map={label: color for _, label, color in data.BANDS},
                       category_orders={'band': [b[1] for b in data.BANDS]},
                       labels={'water_index': '물 안정성 예측 지수', 'band': '신뢰 구간'})
    fig.update_layout(height=330, bargap=0.05, legend=dict(orientation='h', y=1.12))
    st.plotly_chart(fig, width='stretch')
with right:
    st.subheader('최종 후보')
    for f in data.finalists():
        score = f"MOFSimplify {f['mofsimplify_score']:.2f}" if f['mofsimplify_score'] else '판정 보류'
        st.markdown(f"**{f['name']}** · {f['role']}  \n<span style='color:#5B6E80;font-size:14px'>"
                    f"{f['metal']} · {f['linker']} · {score}</span>", unsafe_allow_html=True)
    st.page_link('views/finalists.py', label='3D 구조 보기', icon=':material/view_in_ar:')
    st.page_link('views/explore.py', label='2,737개 후보 직접 탐색', icon=':material/travel_explore:')

st.write('')
st.subheader('기술 성숙도와 범위')
ui.note('이 연구는 TRL 3–4(실험실 수준의 소재 개발·검증)를 목표로 합니다. 하천 전체를 처리하는 플랜트가 아니라, '
        '인이 농축된 흐름에 적용할 수 있는 <b>회수 소재 원천 기술</b>과 그 소재를 고르는 <b>AI 스크리닝 방법</b>이 결과물입니다. '
        'AI 예측은 실험 대상을 줄이는 1차 필터이며, 최종 판단은 실험값으로 합니다.')
