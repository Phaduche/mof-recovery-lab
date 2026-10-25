import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from moflab import ui
from moflab.physics import concentration_as_p, mass_balance, scenario_recovery
from moflab.scoring import CRITERIA, LABELS, ScorePolicy, capacity_index, evaluate

ui.heading('Tool', '회수 계산기', '실험값 → 포집률 · 탈착률 · 100점 평가')

tab_mb, tab_score, tab_scale = st.tabs(['① 물질수지', '② 100점 평가', '③ 적용 시나리오'])

with tab_mb:
    a, b, c = st.columns(3)
    with a:
        st.markdown('**흡착 단계**')
        unit = st.selectbox('농도 단위', ['mg P/L', 'mg PO4/L'])
        c0 = st.number_input('초기 농도 C₀', 0.0, value=10.0, step=0.5)
        ce = st.number_input('잔류 농도 Cₑ', 0.0, value=2.0, step=0.5)
        v0 = st.number_input('용액 부피 (mL)', 0.1, value=50.0)
    with b:
        st.markdown('**탈착 단계**')
        cd = st.number_input('탈착액 농도', 0.0, value=60.0, step=1.0)
        vd = st.number_input('탈착액 부피 (mL)', 0.1, value=5.0)
        mof = st.number_input('건조 MOF 질량 (mg)', 0.1, value=20.0)
    with c:
        st.markdown('**보정 (선택)**')
        sampled = st.number_input('분석용 채취 인 (mg P)', 0.0, value=0.0, step=0.001, format='%.3f')
        blank = st.number_input('공시험 손실 인 (mg P)', 0.0, value=0.0, step=0.001, format='%.3f')
        wash = st.number_input('세척액 손실 인 (mg P)', 0.0, value=0.0, step=0.001, format='%.3f')
    try:
        mb = mass_balance(concentration_as_p(c0, unit), concentration_as_p(ce, unit), v0, v0, mof,
                          concentration_as_p(cd, unit), vd, sampled, blank, wash)
    except ValueError as exc:
        st.error(str(exc))
    else:
        st.session_state['mb'] = mb
        m = st.columns(4)
        m[0].metric('포집률', f"{mb['capture_pct']:.1f}%")
        m[1].metric('탈착 회수율', f"{mb['desorption_pct']:.1f}%" if mb['desorption_pct'] is not None else '—')
        m[2].metric('전체 회수율', f"{mb['overall_recovery_pct']:.1f}%")
        m[3].metric('흡착량 (mg P/g)', f"{mb['capture_mgP_g']:.2f}")
        flow = go.Figure(go.Sankey(
            node=dict(label=['유입 인', 'MOF에 포집', '잔류액', '탈착 회수', 'MOF에 잔존·손실'],
                      color=['#0053D6', '#24A0C8', '#C9D4DF', '#2BB673', '#FF7D45'], pad=18),
            link=dict(source=[0, 0, 1, 1], target=[1, 2, 3, 4],
                      value=[mb['captured_p_mg'], mb['initial_p_mg'] - mb['captured_p_mg'],
                             mb['recovered_p_mg'], max(mb['captured_p_mg'] - mb['recovered_p_mg'], 0)])))
        flow.update_layout(height=280, title='인 질량 흐름 (mg P)')
        st.plotly_chart(flow, width='stretch')
        st.caption(f"농축 배율 {mb['concentration_factor']:.1f}× · {mb['interpretation']}")

with tab_score:
    policy = ScorePolicy()
    mb = st.session_state.get('mb')
    ui.note('총점 = 안정성 40 + 포집 20 + 탈착 25 + 재사용 15 · 안정성 70 미만은 순위 제외')
    s1, s2, s3, s4 = st.columns(4)
    stability = s1.number_input('안정성 (0–100, 실험 지수)', 0.0, 100.0, 80.0,
                                help='PXRD 결정성 유지·금속 용출 등 팀이 정한 공통 평가법으로 환산한 값. AI 예측값이 아닙니다.')
    target_q = s2.number_input('목표 흡착량 (mg P/g)', 0.1, value=30.0)
    capture = capacity_index(mb['capture_mgP_g'], target_q) if mb else 0.0
    s2.caption(f'포집 점수 {capture:.1f} (계산기 ① 결과 사용)')
    desorption = min(100.0, mb['desorption_pct']) if mb and mb['desorption_pct'] is not None else 0.0
    s3.metric('탈착 회수 점수', f'{desorption:.1f}')
    reuse = s4.number_input('재사용 (목표 회차 / 1회차 × 100)', 0.0, 100.0, 85.0)
    res = evaluate({'name': '현재 입력', 'stability': stability, 'capture': capture, 'desorption': desorption,
                    'reuse': reuse, 'structure_supported': True, 'comparable': True}, policy)
    left, right = st.columns([1, 1.2])
    with left:
        st.metric('총점', f"{res['total_score']:.1f} / 100")
        st.metric('불균형 CV (낮을수록 균형)', f"{res['balance_cv']:.3f}")
        (st.success if res['eligible'] else st.warning)('순위 대상' if res['eligible'] else res['reason'])
    with right:
        scores = [res[k] for k in CRITERIA]
        radar = go.Figure(go.Scatterpolar(r=scores + scores[:1], theta=[LABELS[k] for k in CRITERIA] + [LABELS['stability']],
                                          fill='toself', line_color='#0053D6'))
        radar.update_layout(height=320, polar=dict(radialaxis=dict(range=[0, 100])), showlegend=False)
        st.plotly_chart(radar, width='stretch')
    st.dataframe(pd.DataFrame({'항목': [LABELS[k] for k in CRITERIA], '배점': [policy.weights[k] for k in CRITERIA],
                               '점수': scores, '기여': [s * policy.weights[k] / 100 for s, k in zip(scores, CRITERIA)]}),
                 hide_index=True, width='stretch')

with tab_scale:
    presets = {'하수처리장 반류수 (예시)': (5000.0, 30.0), '혐기성 소화 탈리액 (예시)': (500.0, 100.0),
               '하천수 (비교용)': (2_000_000.0, 0.1)}
    p = st.selectbox('흐름 유형', list(presets))
    q, conc = presets[p]
    x1, x2, x3 = st.columns(3)
    flow = x1.number_input('처리량 (m³/일)', 0.0, value=q, key=f'q_{p}')
    conc = x2.number_input('인 농도 (mg P/L)', 0.0, value=conc, key=f'c_{p}')
    eta = x3.slider('전체 회수율 (%)', 0, 100, 40) / 100
    kg = scenario_recovery(flow, conc, eta)
    st.metric('하루 회수 인', f'{kg:,.1f} kg P/일', help='처리량 × 농도 × 회수율')
    st.caption(f'연간 약 {kg*365/1000:,.1f} t P · 프리셋은 계산 예시')
