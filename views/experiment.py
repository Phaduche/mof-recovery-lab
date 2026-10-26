import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from moflab import data, ui
from moflab.pipeline import WEIGHTS, rank_agreement

ui.heading('Experiment plan', 'AI 검증 실험',
           f"Final {data.final_pick()['name']}은 시판품이 아니므로, 살 수 있는 MOF 5개로 AI 점수가 맞는지 확인")

# MOFs you can buy, spanning the AI score range; ids point at stage-A rows.
VALIDATION = {'ws24:ZIF-8': 'ZIF-8', 'ws24:UiO-66-NH2': 'UiO-66-NH₂', 'ws24:mil-100-fe': 'MIL-100(Fe)',
              'ws24:UiO-66': 'UiO-66', 'ws24:HKUST-1': 'HKUST-1'}
A = data.stage_a().set_index('id')
ai = A.loc[list(VALIDATION)].assign(MOF=list(VALIDATION.values())).reset_index()

# ── AI predictions for the test set ─────────────────────────────────
st.subheader('AI가 예측한 순위')
fig = go.Figure()
COLORS = {'stability': '#0053D6', 'capture': '#24A0C8', 'desorption': '#2BB673', 'reuse': '#FFB020'}
NAMES = {'stability': '안정성', 'capture': '포집', 'desorption': '탈착', 'reuse': '재사용'}
for k in WEIGHTS:
    fig.add_bar(y=ai.MOF, x=ai[k], name=f'{NAMES[k]} ({WEIGHTS[k]})', orientation='h', marker_color=COLORS[k])
fig.update_layout(barmode='stack', height=250, xaxis=dict(range=[0, 200]), margin=dict(t=48),
                  yaxis=dict(autorange='reversed', title=None), legend=dict(orientation='h', yanchor='bottom', y=1.02, x=0))
st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
ui.note('같은 MOF라도 항목마다 순위가 다름 (예: ZIF-8은 안정성 1위 · 포집 꼴찌) → 항목별로 따로 검증')

EXPERIMENTS = [
    {'title': '물 안정성', 'key': 'stability', 'days': (1, 2), 'measure': '남은 질량 (%)',
     'goal': 'AI 안정성 점수가 맞나',
     'how': ['MOF 25 mg + 증류수 50 mL, pH 7', '24시간 교반', '걸러서 건조 → 질량 측정', '상등액 색 변화 기록'],
     'calc': r'\text{안정성}(\%) = \frac{m_{\text{후}}}{m_{\text{전}}}\times100'},
    {'title': '인 포집', 'key': 'capture', 'days': (3, 4), 'measure': '포집률 (%)',
     'goal': 'AI 포집 점수가 맞나',
     'how': ['10 mg P/L (KH₂PO₄) 용액 50 mL + MOF 25 mg', 'pH 7, 2시간 교반', '0.45 μm 필터 → 인 농도 측정',
             'MOF 없는 공시험 함께'],
     'calc': r'\text{포집률}(\%) = \frac{C_0 - C}{C_0}\times100'},
    {'title': '탈착', 'key': 'desorption', 'days': (5, 6), 'measure': '탈착률 (%)',
     'goal': 'AI 탈착 점수가 맞나',
     'how': ['2번에서 쓴 MOF를 걸러 건조', '0.01 M NaOH 10 mL, 1시간', '탈착액 인 농도 측정'],
     'calc': r'\text{탈착률}(\%) = \frac{\text{탈착액 속 인}}{\text{붙어 있던 인}}\times100'},
    {'title': '재사용', 'key': 'reuse', 'days': (7, 11), 'measure': '유지율 (%)',
     'goal': 'AI 재사용 점수가 맞나',
     'how': ['포집 → 탈착을 3번 반복', '매 회차 포집률 기록'],
     'calc': r'\text{유지율}(\%) = \frac{\text{3회차 포집률}}{\text{1회차 포집률}}\times100'},
    {'title': 'AI 검증', 'key': None, 'days': (12, 13), 'measure': None,
     'goal': '측정 순위 vs AI 순위 비교', 'how': [], 'calc': r'\rho = \text{Spearman 순위 상관}'},
]

# ── Timeline ────────────────────────────────────────────────────────
tl = go.Figure()
for i, e in enumerate(EXPERIMENTS):
    s, t = e['days']
    tl.add_bar(y=[f"{i+1}. {e['title']}"], x=[t - s + 1], base=[s - 0.5], orientation='h',
               marker=dict(color=['#0053D6', '#24A0C8', '#2BB673', '#FFB020', '#7A5CC8'][i], cornerradius=6),
               text=f'{s}–{t}일', textposition='inside', insidetextanchor='middle', hoverinfo='skip', showlegend=False)
tl.add_vline(x=14.5, line_dash='dot', line_color='#B3261E', annotation_text='보고서 11/9', annotation_position='top')
tl.update_layout(height=220, barmode='overlay', margin=dict(l=8, r=8, t=24, b=8),
                 xaxis=dict(range=[0.5, 15], dtick=1, gridcolor='#EEF2F6'), yaxis=dict(autorange='reversed'))
st.subheader('5개 실험')
st.plotly_chart(tl, width='stretch', config={'displayModeBar': False})

tabs = st.tabs([f"{i+1} · {e['title']}" for i, e in enumerate(EXPERIMENTS)])
for tab, e in zip(tabs[:4], EXPERIMENTS[:4]):
    with tab:
        left, right = st.columns([1.3, 1], gap='large')
        with left:
            st.markdown(f"#### {e['goal']}")
            st.markdown('\n'.join(f'{n}. {h}' for n, h in enumerate(e['how'], 1)))
        with right:
            st.latex(e['calc'])
            order = ai.sort_values(e['key'], ascending=False).MOF.tolist()
            st.success('AI 예측 순위: ' + ' > '.join(order), icon=':material/smart_toy:')

# ── 5. Validation: enter results, compare rankings ──────────────────
with tabs[4]:
    st.markdown('#### 측정값을 넣으면 AI 순위와 비교')
    blank = pd.DataFrame({'MOF': ai.MOF, **{e['measure']: [None] * len(ai) for e in EXPERIMENTS[:4]}})
    measured = st.data_editor(blank, hide_index=True, width='stretch', disabled=['MOF'], key='validation_editor',
                              column_config={e['measure']: st.column_config.NumberColumn(min_value=0, max_value=100,
                                                                                         format='%.1f')
                                             for e in EXPERIMENTS[:4]})
    rows = []
    for e in EXPERIMENTS[:4]:
        rho = rank_agreement(ai[e['key']], measured[e['measure']])
        n = int(pd.to_numeric(measured[e['measure']], errors='coerce').notna().sum())
        if rho is not None:
            rows.append({'항목': e['title'], 'MOF 수': n, 'ρ': round(rho, 2),
                         '판정': 'AI 맞음' if rho >= 0.7 else ('부분적으로 맞음' if rho >= 0.3 else 'AI와 다름')})
        else:
            rows.append({'항목': e['title'], 'MOF 수': n, 'ρ': None, '판정': '3개 이상 입력 필요'})
    st.dataframe(pd.DataFrame(rows), hide_index=True, width='stretch')
    st.latex(EXPERIMENTS[4]['calc'] + r'\quad (1 = \text{순위 완전 일치},\ 0 = \text{무관})')
    ui.note('ρ ≥ 0.7이면 해당 항목의 AI 예측이 실험과 같은 순서 → Final MOF 선택을 뒷받침')

# ── Prep ────────────────────────────────────────────────────────────
st.subheader('준비물')
groups = {'MOF (시판품)': list(VALIDATION.values()),
          '시약': ['KH₂PO₄', 'NaOH 0.01 M', 'HCl · NaOH (pH 조절)', '증류수'],
          '측정 · 기구': ['인산염 비색 키트 + 비색계', 'pH 미터', '정밀 저울 (0.1 mg)', '주사기 + 0.45 μm 필터', '교반기 · 50 mL 튜브']}
for col, (name, items) in zip(st.columns(3), groups.items()):
    with col, st.container(border=True):
        st.markdown(f'**{name}**')
        for item in items:
            st.checkbox(item, key=f'prep_{item}')
ui.note('시작 전: KH₂PO₄ 439 mg/L = 100 mg P/L 원액으로 0 · 0.5 · 1 · 2 · 5 mg P/L 검량선 (R² ≥ 0.99) · 모든 조건 3회 반복')

template = pd.DataFrame(columns=['날짜', '실험', 'MOF', '반복', 'pH', '시간(분)', 'MOF(mg)', '부피(mL)',
                                 'C0(mg P/L)', 'C(mg P/L)', '질량 전(mg)', '질량 후(mg)', '메모'])
st.download_button('기록지 CSV', template.to_csv(index=False).encode('utf-8-sig'), file_name='ai_validation_sheet.csv',
                   icon=':material/download:')
with st.expander('안전'):
    st.markdown('보안경 · 장갑 · 마스크 (MOF 분말) · NaOH · HCl은 선생님 지도 하에 · 비색 키트 시약 취급 주의')
