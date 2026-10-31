"""MOF Recovery Lab — phosphate-recovery MOF pipeline (A → B → Final).  Run: streamlit run app.py"""
import streamlit as st
from moflab import reload, steps, ui

st.set_page_config(page_title='MOF Recovery Lab', page_icon='💧', layout='wide')
reload.refresh_if_changed()
ui.setup()

pages = {
    '': [
        st.Page(steps.a1, title='A-1 · 데이터', url_path='a1', default=True),
        st.Page(steps.a2, title='A-2 · 채점', url_path='a2'),
        st.Page(steps.a3, title='A-3 · 최종 3개', url_path='a3'),
        st.Page(steps.b1, title='B-1 · 수정', url_path='b1'),
        st.Page(steps.b2, title='B-2 · 재채점', url_path='b2'),
        st.Page(steps.final, title='Final', url_path='final'),
    ],
    '연구': [
        st.Page('views/home.py', title='소개'),
        st.Page('views/methods.py', title='방법 · 모델'),
        st.Page('views/sources.py', title='데이터 출처'),
    ],
}
# Keyed explicitly: the default page reports an empty url_path.
st.session_state['step_pages'] = dict(zip(['a1', 'a2', 'a3', 'b1', 'b2', 'final'], pages['']))
st.navigation(pages, position='top').run()
