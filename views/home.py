import streamlit as st
from moflab import data, ui, viewer

A, B, best = data.stage_a(), data.stage_b(), data.final_pick()

left, right = st.columns([1.05, 1], gap='large', vertical_alignment='center')
with left:
    ui.hero('KJWP 2026 · 옹기종기', '버려지는 <em>인(P)</em>을<br>다시 모으는 MOF',
            f'AI로 {len(A):,}개 MOF를 200점 만점으로 채점하고, 상위 3개를 고쳐 다시 채점해 최적 MOF를 골랐습니다.')
    st.write('')
    b1, b2, _ = st.columns([1, 1, 0.6])
    if b1.button('A-1부터 보기', icon=':material/route:', type='primary', width='stretch'):
        st.switch_page(st.session_state['step_pages']['a1'])
    if b2.button('Final 보기', icon=':material/emoji_events:', width='stretch'):
        st.switch_page(st.session_state['step_pages']['final'])
    st.link_button('AI 검증 실험 계획 (Google Docs)', data.EXPERIMENT_DOC, icon=':material/science:')
with right:
    viewer.crystal(data.pipeline_cif(best['id']), '스틱', 1, False, True, height=400, highlight=['Zr'], frame=False)
    st.markdown(f"<p class='note' style='text-align:center'>Final · <b>{best['name']}</b> · {best['total']} / 200</p>",
                unsafe_allow_html=True)

st.write('')
m = st.columns(4)
m[0].metric('A · 채점한 MOF', f'{len(A):,}')
m[1].metric('A · 최종 3개', '3')
m[2].metric('B · 수정한 MOF', f"{(B.change != '원본').sum()}")
m[3].metric('Final', f"{best['total']} / 200")

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
steps = [('🗂️', 'A-1 · 데이터', 'CoRE + MOFSimplify'), ('🤖', 'A-2 · 채점', '200점 만점'),
         ('🥉', 'A-3 · 최종 3개', '최고점 3개'), ('🧪', 'B · 수정 · 재채점', '링커 7 · 원소 6'),
         ('🏆', 'Final', best['name'])]
for col, (icon, t, d) in zip(st.columns(5), steps):
    with col:
        ui.card(t, d, icon)
