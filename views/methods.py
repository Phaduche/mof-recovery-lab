import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sklearn.metrics import roc_curve
from moflab import data

st.title('방법 · 모델')
val = data.validation()
oof = data.oof_predictions()

st.subheader('인산염이 MOF에 붙는 원리')
st.markdown('''
- 리간드 교환: Zr–OH 자리에 인산염이 결합한다 (Zr–O–P).
- 인력: –NH₂가 수소결합을 하고, 산성에서는 양전하를 띤다.
- 탈착: 묽은 염기가 인산염을 밀어낸다.
''')
st.subheader('어떤 AI를 쓰나요?')
st.dataframe(pd.DataFrame({
    '단계': ['A-2 · B-2 안정성', 'A-2 · B-2 포집 · 탈착 · 재사용', 'B-1 원소 바꾸기', 'B-1 링커 바꾸기', 'DFT (참고)'],
    '종류': ['ML (머신러닝)', 'AI 아님 · 점수 규칙', 'DL (딥러닝)', 'ML 결과 활용', '양자역학 계산'],
    '모델': ['Random Forest 분류기 · 결정 트리 180개 (지도학습)', '화학 규칙 + 통계 (z-score)',
           'CHGNet · 그래프 신경망(GNN) · 41만 개 파라미터', 'UiO-66 변형체의 RF 점수 변화를 적용', '—'],
    '배운 것': ['문헌 실험 물 안정성 1,081개', '—', 'Materials Project DFT 계산 약 158만 개 구조 (MPtrj)', '—', '—'],
    'DFT 실행': ['안 함', '안 함', '안 함 (DFT 결과로 학습한 근사)', '안 함', '직접'],
}), hide_index=True, width='stretch')

st.subheader('AI 모델')
m = st.columns(4)
m[0].metric('학습 데이터', f"{val['training_rows']:,}개")
m[1].metric('ROC-AUC', f"{val['metrics']['roc_auc']:.2f}", f"{val['metrics']['roc_auc']-0.5:+.2f} vs 무작위")
m[2].metric('균형 정확도', f"{val['metrics']['balanced_accuracy']:.2f}")
m[3].metric('검증', '그룹 5-fold')

c1, c2 = st.columns(2)
with c1:
    fpr, tpr, _ = roc_curve(oof.stable_label, oof.oof_probability)
    fig = go.Figure()
    fig.add_scatter(x=fpr, y=tpr, name='RF', line=dict(color='#636efa', width=2))
    fig.add_scatter(x=[0, 1], y=[0, 1], name='무작위', line=dict(color='#999', dash='dot'))
    fig.update_layout(title='ROC 곡선', height=330, xaxis_title='위양성률', yaxis_title='민감도', showlegend=False)
    st.plotly_chart(fig, width='stretch')
with c2:
    imp = data.feature_importance()
    fig = px.bar(imp, x='importance', y='feature', orientation='h', color_discrete_sequence=['#636efa'],
                 labels={'importance': '중요도', 'feature': ''})
    fig.update_layout(title='어떤 특성을 많이 봤나', height=330)
    st.plotly_chart(fig, width='stretch')

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

