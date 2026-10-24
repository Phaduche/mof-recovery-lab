"""MOF Recovery Lab — web edition.  Run: streamlit run app.py"""
import streamlit as st
from moflab import ui

st.set_page_config(page_title='MOF Recovery Lab', page_icon='💧', layout='wide',
                   initial_sidebar_state='expanded')
ui.setup()

pages = {
    '연구': [
        st.Page('views/home.py', title='개요', icon=':material/home:', default=True),
        st.Page('views/finalists.py', title='최종 후보 3D', icon=':material/view_in_ar:'),
    ],
    '데이터베이스': [
        st.Page('views/explore.py', title='후보 탐색', icon=':material/travel_explore:'),
        st.Page('views/entry.py', title='구조 상세', icon=':material/deployed_code:'),
    ],
    'AI 도구': [
        st.Page('views/predict.py', title='물 안정성 예측', icon=':material/model_training:'),
        st.Page('views/calculator.py', title='회수 성능 계산기', icon=':material/calculate:'),
    ],
    '원리': [
        st.Page('views/methods.py', title='방법 · 모델', icon=':material/science:'),
        st.Page('views/sources.py', title='데이터 출처', icon=':material/database:'),
    ],
}
nav = st.navigation(pages)
with st.sidebar:
    st.markdown('**MOF Recovery Lab**')
    st.caption('옹기종기 · KJWP 2026 본선\n\nAI 기반 인(P) 자원 회수용 MOF 스크리닝')
nav.run()
