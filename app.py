"""MOF Recovery Lab — phosphate-recovery MOF screening tool.  Run: streamlit run app.py"""
import streamlit as st
from moflab import reload, ui

st.set_page_config(page_title='MOF Recovery Lab', page_icon='💧', layout='wide')
reload.refresh_if_changed()
ui.setup()

pages = {
    '': [
        st.Page('views/tool.py', title='스크리닝', icon=':material/biotech:', default=True),
        st.Page('views/metal_swap.py', title='금속 바꾸기', icon=':material/swap_horiz:'),
        st.Page('views/explore.py', title='후보 탐색', icon=':material/travel_explore:'),
        st.Page('views/calculator.py', title='회수 계산기', icon=':material/calculate:'),
    ],
    '연구': [
        st.Page('views/home.py', title='소개', icon=':material/info:'),
        st.Page('views/results.py', title='결과', icon=':material/emoji_events:'),
        st.Page('views/experiment.py', title='실험 계획', icon=':material/science:'),
        st.Page('views/methods.py', title='방법 · 모델', icon=':material/model_training:'),
        st.Page('views/sources.py', title='데이터 출처', icon=':material/database:'),
    ],
}
st.navigation(pages, position='top').run()
