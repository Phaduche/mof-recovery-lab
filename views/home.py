import streamlit as st
from moflab import data, viewer

A, best = data.stage_a(), data.final_pick()

left, right = st.columns([1.05, 1], gap='large')
with left:
    st.caption('KJWP 2026 · 옹기종기')
    st.title('버려지는 인(P)을 다시 모으는 MOF')
    st.write(f'AI로 MOF {len(A):,}개를 채점해 최적 MOF를 찾았습니다.')
    b1, b2, _ = st.columns([1, 1, 0.6])
    if b1.button('A-1부터 보기', width='stretch'):
        st.switch_page(st.session_state['step_pages']['a1'])
    if b2.button('Final 보기', width='stretch'):
        st.switch_page(st.session_state['step_pages']['final'])

    st.subheader('왜 인(P)인가')
    st.markdown('''
- 대체할 수 없는 자원이다. 합성할 수 없고, 한국은 거의 전량 수입한다.
- 한 번 쓰면 끝이다. 하천과 바다로 흘러가 회수되지 않는다.
- 농축된 곳에서 회수한다. 하수처리장 반류수처럼 인이 진한 물이 대상이다.
''')
with right:
    viewer.crystal(data.pipeline_cif(best['id']), '스틱', 1, False, True, height=400, highlight=['Zr'])
    st.caption(f"Final: {best['name']} · {best['total']} / 200")
