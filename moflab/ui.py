"""Shared bits: plain-HTML look (default fonts, blue underlined links, no cards), a link-row
header, a footer, and a plotly template."""
import html
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

STEPS = [('a1', 'A-1 데이터'), ('a2', 'A-2 채점'), ('a3', 'A-3 최종 3개'), ('b1', 'B-1 수정'),
         ('b2', 'B-2 재채점'), ('final', 'Final')]
RESEARCH = [('home', '소개'), ('methods', '방법과 모델'), ('sources', '데이터 출처')]

CSS = """
<style>
html,body,[data-testid="stApp"],input,textarea,select,button{font-family:system-ui,-apple-system,"Apple SD Gothic Neo","Malgun Gothic",sans-serif;color:#000}
[data-testid="stHeader"]{display:none}
.block-container{max-width:860px;padding-top:2rem;padding-bottom:3rem}
[data-testid="stApp"] h1{font-size:2em !important;font-weight:700;margin:0 0 .4em}
[data-testid="stApp"] h2{font-size:1.5em !important;font-weight:700}
[data-testid="stApp"] h3{font-size:1.17em !important;font-weight:700}
p,li{font-size:16px;line-height:1.5}
.plain a,.plain a:visited{color:#0000ee;text-decoration:underline}
.plain a:visited{color:#551a8b}
.plain{font-size:16px;line-height:1.6}
.plain hr,hr{border:0;border-top:1px solid #ccc;margin:12px 0 18px}
[data-testid="stMetric"]{padding:0}
[data-testid="stMetricLabel"] p{font-size:14px;color:#444}
[data-testid="stMetricValue"]{font-weight:700;font-size:26px}
.stButton button,.stDownloadButton button{border-radius:3px;border:1px solid #767676;background:#efefef;color:#000;font-size:14px}
.stButton button:hover,.stDownloadButton button:hover{background:#e5e5e5;border-color:#4a4a4a;color:#000}
.kv{border-collapse:collapse;font-size:15px}
.kv td{border:1px solid #bbb;padding:4px 10px} .kv td:first-child{background:#f2f2f2}
.note{font-size:14px;color:#444}
</style>"""

def setup():
    pio.templates['moflab'] = go.layout.Template(layout=dict(
        font=dict(family='system-ui, sans-serif', color='#000', size=13), margin=dict(l=8, r=8, t=36, b=8)))
    pio.templates.default = 'plotly_white+moflab'
    st.markdown(CSS, unsafe_allow_html=True)

def header(current=''):
    """Plain link row: site name, the six steps, the three research pages. The current page is bold."""
    def links(items):
        return ' | '.join(f'<b>{t}</b>' if p == current else f'<a href="{p}">{t}</a>' for p, t in items)
    st.markdown(f'<div class="plain"><b>MOF Recovery Lab</b> · 옹기종기 · KJWP 2026<br>'
                f'{links(STEPS)}<br>{links(RESEARCH)} | '
                f'<a href="https://github.com/Phaduche/mof-recovery-lab" target="_blank">GitHub</a><hr></div>',
                unsafe_allow_html=True)

def footer():
    st.markdown('<div class="plain"><hr><small>데이터: CoRE MOF 2025 (CC BY 4.0), MOFSimplify / WS24 · '
                '모델: Random Forest, CHGNet · 3D: 3Dmol.js<br>점수는 연구용 예측값이며 실험으로 검증 중입니다.'
                '</small></div>', unsafe_allow_html=True)

def kv(rows):
    cells = ''.join(f'<tr><td>{html.escape(str(k))}</td><td>{html.escape(str(v))}</td></tr>' for k, v in rows)
    st.markdown(f'<table class="kv">{cells}</table>', unsafe_allow_html=True)

def note(text):
    st.markdown(f'<div class="note">{text}</div>', unsafe_allow_html=True)
