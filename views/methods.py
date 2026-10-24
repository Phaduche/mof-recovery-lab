import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from sklearn.metrics import roc_curve
from moflab import data, ui

ui.heading('Methods', '방법 · 모델의 원리',
           '어떤 데이터로, 어떤 모델을, 어떻게 검증했는지와 그 한계를 함께 공개합니다.')
val = data.validation()
oof = data.oof_predictions()

st.subheader('1. MOF란')
a, b = st.columns([1.2, 1])
with a:
    st.write('금속-유기 골격체(Metal–Organic Framework)는 금속 이온·클러스터(노드)를 유기 분자(링커)가 이어 만든 '
             '다공성 결정입니다. 1 g의 표면적이 수천 m²에 이를 만큼 넓고, 노드와 링커를 바꿔 기공 크기와 화학적 성질을 '
             '설계할 수 있어 특정 이온을 골라 붙잡는 흡착제로 연구됩니다.')
    st.write('인산염 회수에서는 **물속에서 구조가 무너지지 않는 것**이 먼저입니다. 그래서 AI의 첫 역할을 수만 개 구조 중 '
             '물에 안정할 가능성이 높은 후보를 고르는 것으로 정했습니다.')
with b:
    ui.card('인산염이 붙는 원리 (가설)',
            '① 리간드 교환: Zr–OH, Fe–OH 자리의 OH⁻가 인산염으로 바뀌며 M–O–P 결합 형성<br>'
            '② 정전기 인력: 양성자화된 –NH₃⁺·양전하 표면과 음이온 H₂PO₄⁻/HPO₄²⁻<br>'
            '③ 탈착: 염기성 용액(OH⁻)이 다시 인산염과 자리를 바꿔 인을 농축 회수')

st.subheader('2. AI 모델')
m = st.columns(5)
m[0].metric('학습 데이터', f"{val['training_rows']:,}개")
m[1].metric('검증 그룹', f"{val['groups']:,}개")
m[2].metric('ROC-AUC', f"{val['metrics']['roc_auc']:.3f}", f"{val['metrics']['roc_auc']-val['baseline_metrics']['roc_auc']:+.3f} vs 기준선")
m[3].metric('균형 정확도', f"{val['metrics']['balanced_accuracy']:.3f}", f"{val['metrics']['balanced_accuracy']-0.5:+.3f} vs 기준선")
m[4].metric('Brier (낮을수록 좋음)', f"{val['metrics']['brier']:.3f}",
            f"{val['metrics']['brier']-val['baseline_metrics']['brier']:+.3f}", delta_color='inverse')
st.write(f"MOFSimplify 공개 물 안정성 라벨 {val['raw_rows']:,}행(문헌 클래스 1–4)에서 중복·라벨 충돌을 정리하고 "
         "클래스 3·4 = 안정, 1·2 = 불안정으로 이진화해 **Random Forest 분류기**(트리 180개, 최대 깊이 12)를 학습했습니다. "
         "입력은 금속 노드·링커·작용기의 RAC 특성 11개와 비표면적(GSA) 1개입니다. 이름 계열과 동일 특성 벡터를 묶어 "
         "같은 계열이 학습·검증에 동시에 들어가지 않게 한 **5-fold StratifiedGroupKFold**로 평가했습니다.")

c1, c2 = st.columns(2)
with c1:
    fpr, tpr, _ = roc_curve(oof.stable_label, oof.oof_probability)
    fig = go.Figure()
    fig.add_scatter(x=fpr, y=tpr, name=f"RF (AUC {val['metrics']['roc_auc']:.3f})", line=dict(color='#0053D6', width=3))
    fig.add_scatter(x=[0, 1], y=[0, 1], name='무작위 기준', line=dict(color='#B8C2CC', dash='dot'))
    fig.update_layout(title='ROC 곡선 (교차검증 OOF)', height=360, xaxis_title='위양성률', yaxis_title='민감도',
                      legend=dict(x=.45, y=.08))
    st.plotly_chart(fig, width='stretch')
with c2:
    imp = data.feature_importance()
    fig = px.bar(imp, x='importance', y='feature', orientation='h', color_discrete_sequence=['#24A0C8'],
                 labels={'importance': '중요도 (불순도 감소)', 'feature': ''})
    fig.update_layout(title='특성 중요도', height=360)
    st.plotly_chart(fig, width='stretch')

c3, c4 = st.columns(2)
with c3:
    bins = np.linspace(0, 1, 11)
    oof['bin'] = np.clip(np.digitize(oof.oof_probability, bins) - 1, 0, 9)
    cal = oof.groupby('bin').agg(pred=('oof_probability', 'mean'), obs=('stable_label', 'mean'), n=('name', 'size'))
    fig = go.Figure()
    fig.add_scatter(x=cal.pred, y=cal.obs, mode='lines+markers', name='모델', marker=dict(size=8 + cal.n / 15),
                    line=dict(color='#0053D6'))
    fig.add_scatter(x=[0, 1], y=[0, 1], name='완벽 보정', line=dict(color='#B8C2CC', dash='dot'))
    fig.update_layout(title='신뢰도 곡선 (예측 확률 vs 실제 안정 비율)', height=340,
                      xaxis_title='예측 확률', yaxis_title='실제 안정 비율')
    st.plotly_chart(fig, width='stretch')
with c4:
    folds = val['folds']
    fig = go.Figure(go.Bar(x=[f"Fold {f['fold']}" for f in folds], y=[f['roc_auc'] for f in folds],
                           marker_color='#0053D6', text=[f"{f['roc_auc']:.3f}" for f in folds], textposition='outside'))
    fig.update_layout(title='Fold별 ROC-AUC (그룹 겹침 0)', height=340, yaxis=dict(range=[0.5, 0.9]))
    st.plotly_chart(fig, width='stretch')

st.subheader('3. 학습 범위 (applicability domain)')
st.write('새 구조의 12개 특성을 표준화한 뒤 가장 가까운 학습 MOF까지의 거리를 계산합니다. 학습 데이터에서 다른 그룹 간 최근접 '
         f"거리의 95백분위({val['domain_distance_p95']:.3f})보다 멀면 “학습 범위 바깥”으로 표시합니다. "
         '바깥 구조의 예측은 외삽이므로 신뢰도가 낮습니다. 트리 간 표준편차는 모델 내부의 의견 차이이며 신뢰구간이 아닙니다.')

st.subheader('4. 실험 평가 규칙 (100점)')
st.latex(r'\text{총점}=0.40\,S_{\text{안정성}}+0.20\,S_{\text{포집}}+0.25\,S_{\text{탈착}}+0.15\,S_{\text{재사용}}')
st.latex(r'S_{\text{포집}}=\min\!\left(100,\ \frac{q_{\text{목표회차}}}{q_{\text{목표}}}\times100\right),\quad '
         r'S_{\text{탈착}}=\frac{m_{P,\text{탈착}}}{m_{P,\text{포집}}}\times100,\quad '
         r'S_{\text{재사용}}=\min\!\left(100,\ \frac{R_{n}}{R_{1}}\times100\right)')
st.write('안정성은 물에서 구조가 버티지 못하면 나머지 성능이 의미 없기 때문에 가장 큰 배점(40)을 주고, 70점 미만은 순위에서 제외합니다. '
         '네 항목 중 하나라도 측정하지 않았으면 총점을 내지 않으며, 동점이면 네 점수의 변동계수(CV)가 낮은 '
         '— 고르게 좋은 — 후보를 앞에 둡니다.')

st.subheader('5. 한계와 다음 단계')
l, r = st.columns(2)
with l:
    st.markdown('**현재 한계**')
    for item in val['limits']:
        st.markdown(f'- {item}')
with r:
    st.markdown('**다음 단계**')
    st.markdown('- 정인산염 모사용액에서 후보 3종의 포집·탈착·재사용 실측\n'
                '- 황산염·질산염·탄산염 등 **방해 이온**을 넣은 조건으로 데이터 확장\n'
                '- 쌓인 실험값으로 인산염 성능 예측 모델 학습 (그룹 교차검증)\n'
                '- 처리량·농도·회수율을 넣어 경제성을 미리 보는 **예비 타당성 검토** 도구로 확장')
