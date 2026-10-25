import pandas as pd
import streamlit as st
from moflab import ui

ui.heading('Experiment plan', '실험 계획', '고등학교 실험실에서 2주 안에 할 수 있는 순서 · UiO-66-NH₂ vs UiO-66')

m = st.columns(4)
m[0].metric('비교 소재', 'NH₂ vs 기준')
m[1].metric('반복', '각 3회')
m[2].metric('핵심 측정', '인 농도')
m[3].metric('보고서 마감', '11월 9일')

st.write('')
st.subheader('준비물')
a, b, c = st.columns(3)
with a:
    ui.list_card('소재 · 시약', ['UiO-66-NH₂, UiO-66 분말 (구매 권장)', 'KH₂PO₄ (인산이수소칼륨)',
                                '증류수 · 0.1 M HCl / NaOH (pH 조절)', 'NaCl, 0.01 M NaOH (탈착)'])
with b:
    ui.list_card('측정', ['인산염 비색 키트 (몰리브덴 청법)', '분광광도계 또는 휴대용 비색계',
                         'pH 미터', '정밀 저울 (0.1 mg)'])
with c:
    ui.list_card('기구', ['50 mL 튜브 · 비커', '교반기 또는 진탕기', '주사기 + 0.45 μm 필터', '원심분리기 (있으면)'])

st.write('')
st.subheader('순서')
steps = [
    ('검량선 만들기', '1일차', 'KH₂PO₄ 439 mg → 1 L = 100 mg P/L 원액. 0 · 0.5 · 1 · 2 · 5 mg P/L로 묽혀 흡광도 측정.',
     '직선(R² ≥ 0.99)이 나와야 다음 단계로'),
    ('흡착 비교 ★핵심', '2–3일차', '10 mg P/L 용액 50 mL + MOF 25 mg, pH 7, 2시간 교반 → 필터 → 농도 측정. MOF 없는 공시험도 함께.',
     '포집률(%) = (C₀ − C) / C₀ × 100,  흡착량 q = (C₀ − C) × V / m'),
    ('시간 · pH 영향', '4–6일차', '시간 5 · 15 · 30 · 60 · 120분, pH 4 · 7 · 9에서 반복.',
     '가설: 산성일수록 NH₂가 양전하 → UiO-66-NH₂가 더 유리'),
    ('탈착', '7–8일차', '쓴 MOF를 걸러 말린 뒤 0.1 M NaCl 또는 0.01 M NaOH 10 mL에 1시간.',
     '탈착률 = 탈착액 속 인 / 붙어 있던 인 × 100. 진한 NaOH는 구조를 무너뜨릴 수 있어 묽게, 짧게'),
    ('재사용 3회', '9–12일차', '흡착 → 탈착을 3번 반복. 매번 MOF 질량도 기록.', '재사용률 = 3회차 회수율 / 1회차 회수율 × 100'),
]
for n, (title, when, how, check) in enumerate(steps, 1):
    with st.container(border=True):
        h, body = st.columns([0.28, 1])
        h.markdown(f"<div class='step'><b class='n'>{n}</b><div><b>{title}</b><br><span class='note'>{when}</span></div></div>",
                   unsafe_allow_html=True)
        body.markdown(how)
        body.caption(check)

st.write('')
st.subheader('구조가 버티는지 확인')
k = st.columns(3)
with k[0]:
    ui.card('질량', '실험 전후 건조 질량 비교. 많이 줄면 분해 의심.', '⚖️')
with k[1]:
    ui.card('색 · 상등액', '용액이 노랗게 변하면 링커가 녹아 나온 신호 (NH₂ 링커는 노란색).', '🎨')
with k[2]:
    ui.card('PXRD (가능하면)', '대학 · 연구소 지원 시 결정 구조 유지 여부를 직접 확인.', '📈')

st.write('')
st.subheader('결과를 점수로')
st.markdown('측정값을 **[회수 계산기](/calculator)** 에 넣으면 100점 평가가 나옵니다: '
            '안정성 40 · 포집 20 · 탈착 25 · 재사용 15.')

template = pd.DataFrame(columns=['날짜', 'MOF', '단계', '반복', 'pH', '시간(분)', 'MOF(mg)', '부피(mL)',
                                 'C0(mg P/L)', 'C(mg P/L)', '탈착액(mg P/L)', '탈착액(mL)', '메모'])
st.download_button('실험 기록지 (CSV)', template.to_csv(index=False).encode('utf-8-sig'),
                   file_name='experiment_sheet.csv', icon=':material/download:')

with st.expander('안전'):
    st.markdown('- 보안경 · 장갑 · 마스크 (MOF 분말 흡입 주의)\n'
                '- HCl · NaOH는 선생님 지도 하에\n'
                '- MOF 합성(ZrCl₄ · DMF · 고온)은 하지 말고 구매 권장\n'
                '- 인산염 비색 키트의 황산 시약 취급 주의')
