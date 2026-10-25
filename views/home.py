import streamlit as st
from moflab import data, ui, viewer

df = data.catalog()
var = data.variants().set_index('key')
best = data.picks()['ranking'][0]

left, right = st.columns([1.05, 1], gap='large', vertical_alignment='center')
with left:
    ui.hero('KJWP 2026 · 옹기종기', '버려지는 <em>인(P)</em>을<br>다시 모으는 MOF',
            'AI로 2,700여 개 구조를 거르고, UiO-66 변형체 19종을 비교해 실험할 소재를 골랐습니다.')
    st.write('')
    b1, b2, _ = st.columns([1, 1, 0.6])
    if b1.button('스크리닝 시작', icon=':material/biotech:', type='primary', width='stretch'):
        st.switch_page('views/tool.py')
    if b2.button('결과 보기', icon=':material/emoji_events:', width='stretch'):
        st.switch_page('views/results.py')
with right:
    viewer.crystal(data.variant_cif(best['key']), '볼 & 스틱', 2, False, True, height=400,
                   highlight=['Zr'], frame=False)
    st.markdown(f"<p class='note' style='text-align:center'>최종 선택 · <b>{var.loc[best['key'], 'name']}</b></p>",
                unsafe_allow_html=True)

st.write('')
m = st.columns(4)
m[0].metric('공개 레코드', f"{sum(s['records'] for s in data.sources()):,}")
m[1].metric('AI 예측 구조', f"{df.water_prob.notna().sum():,}")
m[2].metric('비교한 변형체', f'{len(var)}종')
m[3].metric('최종 후보', '3종')

st.write('')
st.subheader('왜 인(P)인가')
c = st.columns(3)
with c[0]:
    ui.card('대체 불가 자원', '비료·식품에 꼭 필요하지만 합성할 수 없고, 한국은 거의 전량 수입.', '🌾')
with c[1]:
    ui.card('한 번 쓰면 끝', '하천·바다로 흘러가 녹조를 만들고 회수되지 않음.', '🌊')
with c[2]:
    ui.card('농축된 곳에서 회수', '하천수 대신 하수처리장 반류수처럼 인이 진한 물을 대상으로.', '🏭')

st.write('')
st.subheader('연구 흐름')
steps = [('🗂️', '데이터', '공개 DB 36,857건'), ('🤖', 'AI 선별', '물 안정성 예측'),
         ('🧪', '변형 비교', 'UiO-66 작용기 19종'), ('🔬', '실험 검증', '포집 · 탈착 · 재사용')]
for col, (icon, t, d) in zip(st.columns(4), steps):
    with col:
        ui.card(t, d, icon)
