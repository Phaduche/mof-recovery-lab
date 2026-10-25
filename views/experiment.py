import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from moflab import ui

ui.heading('Experiment plan', '실험 계획', 'UiO-66-NH₂ vs UiO-66 · 고등학교 실험실 · 2주')

STEPS = [
    {'title': '검량선', 'days': (1, 1), 'goal': '흡광도 → 인 농도 변환식 만들기',
     'how': ['KH₂PO₄ 439 mg을 증류수 1 L에 녹임 → 100 mg P/L 원액',
             '0 · 0.5 · 1 · 2 · 5 mg P/L로 희석',
             '비색 키트로 발색 후 흡광도 측정'],
     'calc': r'A = a\,C + b', 'check': 'R² ≥ 0.99'},
    {'title': '흡착 비교', 'days': (2, 3), 'goal': '어느 MOF가 인을 더 많이 잡나 (핵심 실험)',
     'how': ['10 mg P/L 용액 50 mL에 MOF 25 mg', 'pH 7 맞추고 2시간 교반',
             '0.45 μm 필터로 거른 뒤 농도 측정', 'MOF 없는 공시험 함께'],
     'calc': r'q = \frac{(C_0 - C)\,V}{m}\quad\text{포집률} = \frac{C_0 - C}{C_0}\times100',
     'check': '공시험 농도 변화 < 5%'},
    {'title': '시간 · pH', 'days': (4, 6), 'goal': '언제 다 붙나, 어떤 pH가 유리한가',
     'how': ['시간: 5 · 15 · 30 · 60 · 120분', 'pH: 4 · 7 · 9', '나머지 조건은 2단계와 동일'],
     'calc': None, 'check': '가설 — 산성일수록 –NH₂(→ –NH₃⁺)가 유리'},
    {'title': '탈착', 'days': (7, 8), 'goal': '붙은 인을 다시 꺼낼 수 있나',
     'how': ['쓴 MOF를 걸러 건조', '0.1 M NaCl 또는 0.01 M NaOH 10 mL, 1시간', '탈착액 농도 측정'],
     'calc': r'\text{탈착률} = \frac{\text{탈착액 속 인}}{\text{붙어 있던 인}}\times100',
     'check': 'NaOH는 묽게 · 짧게 (구조 손상 주의)'},
    {'title': '재사용', 'days': (9, 12), 'goal': '여러 번 써도 성능이 유지되나',
     'how': ['흡착 → 탈착 3회 반복', '매 회차 MOF 건조 질량 기록'],
     'calc': r'\text{재사용률} = \frac{\text{3회차 회수율}}{\text{1회차 회수율}}\times100', 'check': '질량 감소 < 10%'},
]

# ── Timeline ────────────────────────────────────────────────────────
fig = go.Figure()
colors = ['#9DB8D9', '#0053D6', '#65A0E0', '#24A0C8', '#2A7DE1']
for i, (s, c) in enumerate(zip(STEPS, colors)):
    start, end = s['days']
    fig.add_bar(y=[f"{i+1}. {s['title']}"], x=[end - start + 1], base=[start - 0.5], orientation='h',
                marker=dict(color=c, cornerradius=6), text=f"{start}–{end}일" if end > start else f'{start}일',
                textposition='inside', insidetextanchor='middle', hoverinfo='skip', showlegend=False)
fig.add_vline(x=14.5, line_dash='dot', line_color='#B3261E', annotation_text='보고서 11/9', annotation_position='top')
fig.update_layout(height=230, barmode='overlay', margin=dict(l=8, r=8, t=24, b=8),
                  xaxis=dict(range=[0.5, 15], dtick=1, title=None, showgrid=True, gridcolor='#EEF2F6'),
                  yaxis=dict(autorange='reversed', title=None))
st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})

# ── Steps ───────────────────────────────────────────────────────────
tabs = st.tabs([f"{i+1} · {s['title']}" for i, s in enumerate(STEPS)])
for tab, s in zip(tabs, STEPS):
    with tab:
        left, right = st.columns([1.3, 1], gap='large')
        with left:
            st.markdown(f"#### {s['goal']}")
            st.markdown('\n'.join(f'{n}. {h}' for n, h in enumerate(s['how'], 1)))
        with right:
            if s['calc']:
                st.latex(s['calc'])
            st.success(s['check'], icon=':material/check_circle:')
st.caption('모든 조건은 MOF마다 3회 반복 · 측정 범위를 넘으면 희석해서 측정')

# ── Prep checklist ──────────────────────────────────────────────────
st.subheader('준비물')
groups = {'소재 · 시약': ['UiO-66-NH₂ 분말', 'UiO-66 분말', 'KH₂PO₄', '0.1 M HCl / NaOH', 'NaCl'],
          '측정': ['인산염 비색 키트', '분광광도계 / 비색계', 'pH 미터', '정밀 저울 (0.1 mg)'],
          '기구': ['50 mL 튜브', '교반기', '주사기 + 0.45 μm 필터', '원심분리기 (선택)']}
cols = st.columns(3)
for col, (name, items) in zip(cols, groups.items()):
    with col, st.container(border=True):
        st.markdown(f'**{name}**')
        for item in items:
            st.checkbox(item, key=f'prep_{item}')

# ── Structure checks ────────────────────────────────────────────────
st.subheader('MOF가 버티는지')
k = st.columns(3)
with k[0]:
    ui.card('질량', '전후 건조 질량 비교', '⚖️')
with k[1]:
    ui.card('색', '용액이 노랗게 → 링커 용출', '🎨')
with k[2]:
    ui.card('PXRD', '가능하면 대학 · 연구소 지원', '📈')

st.write('')
d1, d2, _ = st.columns([1, 1, 2])
template = pd.DataFrame(columns=['날짜', 'MOF', '단계', '반복', 'pH', '시간(분)', 'MOF(mg)', '부피(mL)',
                                 'C0(mg P/L)', 'C(mg P/L)', '탈착액(mg P/L)', '탈착액(mL)', '메모'])
d1.download_button('기록지 CSV', template.to_csv(index=False).encode('utf-8-sig'), file_name='experiment_sheet.csv',
                   icon=':material/download:', width='stretch')
if d2.button('회수 계산기', icon=':material/calculate:', width='stretch'):
    st.switch_page('views/calculator.py')

with st.expander('안전'):
    st.markdown('보안경 · 장갑 · 마스크 · 산/염기는 선생님 지도 하에 · MOF 합성(ZrCl₄, DMF)은 하지 않기')
