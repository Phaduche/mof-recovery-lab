import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sklearn.metrics import roc_curve
from moflab import data, ui

ui.heading('Methods', '방법 · 모델', '어떻게 고르고, 얼마나 믿을 수 있는지')
val = data.validation()
oof = data.oof_predictions()

st.subheader('인산염이 MOF에 붙는 원리')
c = st.columns(3)
with c[0]:
    ui.card('① 리간드 교환', 'Zr–OH의 OH⁻ 자리에 인산염이 들어가 Zr–O–P 결합.', '🔗')
with c[1]:
    ui.card('② 인력', '–NH₂ 수소결합, 산성에서 –NH₃⁺ 양전하가 음이온을 끌어당김.', '🧲')
with c[2]:
    ui.card('③ 탈착', '염 · 묽은 염기 용액이 인산염을 밀어내 농축 회수.', '♻️')

st.write('')
st.subheader('어떤 AI를 쓰나요?')
st.dataframe(pd.DataFrame({
    '단계': ['A-2 · B-2 안정성', 'A-2 · B-2 포집 · 탈착 · 재사용', 'B-1 원소 바꾸기', 'B-1 링커 바꾸기', 'DFT (참고)'],
    '종류': ['ML (머신러닝)', 'AI 아님 · 점수 규칙', 'DL (딥러닝)', 'ML 결과 활용', '양자역학 계산'],
    '모델': ['Random Forest 분류기 · 결정 트리 180개 (지도학습)', '화학 규칙 + 통계 (z-score)',
           'CHGNet · 그래프 신경망(GNN) · 41만 개 파라미터', 'UiO-66 변형체의 RF 점수 변화를 적용', '—'],
    '배운 것': ['문헌 실험 물 안정성 1,081개', '—', 'Materials Project DFT 계산 약 158만 개 구조 (MPtrj)', '—', '—'],
    'DFT 실행': ['안 함', '안 함', '안 함 (DFT 결과로 학습한 근사)', '안 함', '직접'],
}), hide_index=True, width='stretch')
ui.note('A-2 입력 숫자는 Zeo++(기공)와 molSimplify(RAC)로 만들지만, 둘 다 에너지 계산이 아닌 구조 분석 도구입니다.')

st.write('')
st.subheader('AI 모델')
m = st.columns(4)
m[0].metric('학습 데이터', f"{val['training_rows']:,}개")
m[1].metric('ROC-AUC', f"{val['metrics']['roc_auc']:.2f}", f"{val['metrics']['roc_auc']-0.5:+.2f} vs 무작위")
m[2].metric('균형 정확도', f"{val['metrics']['balanced_accuracy']:.2f}")
m[3].metric('검증', '그룹 5-fold')
ui.note('Random Forest · 입력 = 금속 노드 · 링커 · 작용기 RAC 11개 + 표면적 · 라벨 = MOFSimplify 문헌 물 안정성')

c1, c2 = st.columns(2)
with c1:
    fpr, tpr, _ = roc_curve(oof.stable_label, oof.oof_probability)
    fig = go.Figure()
    fig.add_scatter(x=fpr, y=tpr, name='RF', line=dict(color='#0053D6', width=3), fill='tozeroy',
                    fillcolor='rgba(0,83,214,.08)')
    fig.add_scatter(x=[0, 1], y=[0, 1], name='무작위', line=dict(color='#B8C2CC', dash='dot'))
    fig.update_layout(title='ROC 곡선', height=330, xaxis_title='위양성률', yaxis_title='민감도', showlegend=False)
    st.plotly_chart(fig, width='stretch')
with c2:
    imp = data.feature_importance()
    fig = px.bar(imp, x='importance', y='feature', orientation='h', color_discrete_sequence=['#24A0C8'],
                 labels={'importance': '중요도', 'feature': ''})
    fig.update_layout(title='어떤 특성을 많이 봤나', height=330)
    st.plotly_chart(fig, width='stretch')

with st.expander('더 보기 · 신뢰도 곡선 · fold별 성능'):
    c3, c4 = st.columns(2)
    bins = np.linspace(0, 1, 11)
    oof['bin'] = np.clip(np.digitize(oof.oof_probability, bins) - 1, 0, 9)
    cal = oof.groupby('bin').agg(pred=('oof_probability', 'mean'), obs=('stable_label', 'mean'))
    fig = go.Figure()
    fig.add_scatter(x=cal.pred, y=cal.obs, mode='lines+markers', line=dict(color='#0053D6'))
    fig.add_scatter(x=[0, 1], y=[0, 1], line=dict(color='#B8C2CC', dash='dot'))
    fig.update_layout(title='예측 확률 vs 실제 비율', height=300, showlegend=False)
    c3.plotly_chart(fig, width='stretch')
    folds = val['folds']
    fig = go.Figure(go.Bar(x=[f"F{f['fold']}" for f in folds], y=[f['roc_auc'] for f in folds],
                           marker_color='#0053D6', text=[f"{f['roc_auc']:.2f}" for f in folds], textposition='outside'))
    fig.update_layout(title='fold별 AUC', height=300, yaxis=dict(range=[0.5, 0.9]))
    c4.plotly_chart(fig, width='stretch')
    st.markdown(f"학습 범위: 가장 가까운 학습 MOF까지 거리가 {val['domain_distance_p95']:.2f}보다 멀면 '범위 밖'(외삽).")

st.subheader('점수 (200점)')
s = st.columns(4)
for col, (k, w, d) in zip(s, [('안정성', 100, '절대평가'), ('포집', 40, '상대평가 (z)'),
                               ('탈착', 35, '상대평가 (z)'), ('재사용', 25, '상대평가 (z)')]):
    col.metric(k, f'{w}점', d, delta_color='off')
st.dataframe(pd.DataFrame({
    '항목': ['안정성', '포집', '탈착', '재사용'],
    'AI가 보는 것': ['RF 물 안정성 확률 × 100',
                  '금속의 인산염 결합력 × 표면적 · 기공 통과 + 작용기 전하 + 열린 금속 자리',
                  '결합의 되돌림 쉬움(금속) × 기공 크기',
                  '물 안정성 · 열분해 온도 · 염기 안정성'],
}), hide_index=True, width='stretch')
st.latex(r'z = \frac{x - \mu_A}{\sigma_A},\qquad \text{점수} = \text{배점}\times\Phi\!\left(\tfrac{z}{2}\right)')
ui.note('μ, σ는 A 단계 데이터베이스 전체 기준 → B 단계 수정 MOF도 같은 잣대 · 동점이면 네 점수 불균형(z)이 낮은 MOF 우선')
