import streamlit as st
from moflab import data, ui, viewer

A, B, best = data.stage_a(), data.stage_b(), data.final_pick()
ui.header('home')

left, right = st.columns([1.05, 1], gap='large')
with left:
    st.title('버려지는 인(P)을 다시 모으는 MOF')
    st.write(f'AI로 MOF {len(A):,}개를 채점해 최적 MOF를 찾았습니다.')
    b1, b2, _ = st.columns([1, 1, 0.6])
    if b1.button('A-1부터 보기', width='stretch'):
        st.switch_page(st.session_state['step_pages']['a1'])
    if b2.button('Final 보기', width='stretch'):
        st.switch_page(st.session_state['step_pages']['final'])
    ui.section('왜 <em>인(P)</em>인가')
    st.markdown('''
- 대체할 수 없는 자원이다. 합성할 수 없고, 한국은 거의 전량 수입한다.
- 한 번 쓰면 끝이다. 하천과 바다로 흘러가 회수되지 않는다.
- 농축된 곳에서 회수한다. 하수처리장 반류수처럼 인이 진한 물이 대상이다.
''')
with right:
    viewer.crystal(data.pipeline_cif(best['id']), '스틱', 1, False, True, height=300, highlight=['Zr'])
    ui.item(best['name'], best['total'], rank=1, tag='AI추천 · Final', deliv='DFT 1차 검증 완료', stars=B.iloc[0].stability / 100)

ui.section('오늘의 <em>MOF 베스트</em>', ('A-3 전체 보기', 'a3'))
cols = st.columns(3)
for col, (_, r) in zip(cols, A.head(3).iterrows()):
    with col:
        viewer.crystal(data.pipeline_cif(r.id.split(':', 1)[1]), '스틱', 1, False, False, height=180, highlight=['Zr'])
        ui.item(r['name'], r.total, rank=int(r['rank']), tag='AI추천', deliv=r.source, stars=r.stability / 100)
