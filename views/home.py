import streamlit as st
from moflab import data, ui, viewer

A, best = data.stage_a(), data.final_pick()

left, right = st.columns([1.05, 1], gap='large', vertical_alignment='center')
with left:
    ui.hero('KJWP 2026 · 옹기종기', '버려지는 <em>인(P)</em>을<br>다시 모으는 MOF',
            f'AI로 MOF {len(A):,}개를 채점해 최적 MOF를 찾았습니다.')
    st.write('')
    b1, b2, _ = st.columns([1, 1, 0.6])
    if b1.button('A-1부터 보기', icon=':material/route:', type='primary', width='stretch'):
        st.switch_page(st.session_state['step_pages']['a1'])
    if b2.button('Final 보기', icon=':material/emoji_events:', width='stretch'):
        st.switch_page(st.session_state['step_pages']['final'])
with right:
    viewer.crystal(data.pipeline_cif(best['id']), '스틱', 1, False, True, height=400, highlight=['Zr'], frame=False)
    st.markdown(f"<p class='note' style='text-align:center'><b>{best['name']}</b> · {best['total']} / 200</p>",
                unsafe_allow_html=True)

st.write('')
st.subheader('왜 인(P)인가')
c = st.columns(3)
with c[0]:
    ui.card('대체 불가 자원', '합성할 수 없고, 한국은 거의 전량 수입.', '🌾')
with c[1]:
    ui.card('한 번 쓰면 끝', '하천 · 바다로 흘러가 회수되지 않음.', '🌊')
with c[2]:
    ui.card('농축된 곳에서 회수', '하수처리장 반류수처럼 인이 진한 물이 대상.', '🏭')
