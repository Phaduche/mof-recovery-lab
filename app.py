"""MOF Recovery Lab — web edition.  Run: streamlit run app.py"""
import streamlit as st
from moflab import reload, ui

st.set_page_config(page_title='MOF Recovery Lab', page_icon='💧', layout='wide')
reload.refresh_if_changed()
ui.setup()

pages = {
    '': [
        st.Page('views/home.py', title='홈', icon=':material/home:', default=True),
        st.Page('views/results.py', title='결과', icon=':material/emoji_events:'),
        st.Page('views/experiment.py', title='실험 계획', icon=':material/biotech:'),
    ],
    '데이터베이스': [
        st.Page('views/explore.py', title='후보 탐색', icon=':material/travel_explore:'),
        st.Page('views/entry.py', title='구조 상세', icon=':material/deployed_code:'),
    ],
    '도구': [
        st.Page('views/predict.py', title='물 안정성 예측', icon=':material/model_training:'),
        st.Page('views/calculator.py', title='회수 계산기', icon=':material/calculate:'),
    ],
    '원리': [
        st.Page('views/methods.py', title='방법 · 모델', icon=':material/science:'),
        st.Page('views/sources.py', title='데이터 출처', icon=':material/database:'),
    ],
}
st.navigation(pages, position='top').run()
