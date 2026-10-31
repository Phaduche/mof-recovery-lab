"""Shared look & feel: plain, document-like styling (system fonts, no cards or gradients)."""
import html
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

FONT = "Arial, 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif"

CSS = f"""
<style>
html,body,[data-testid="stApp"],input,textarea,select,button{{font-family:{FONT}}}
.block-container{{max-width:1100px;padding-top:4rem;padding-bottom:4rem}}
h1,h2,h3,[data-testid="stHeading"] *{{font-family:{FONT} !important;letter-spacing:0 !important;color:#000}}
[data-testid="stApp"] h1{{font-size:30px !important;font-weight:700}}
[data-testid="stApp"] h2{{font-size:23px !important;font-weight:700}}
[data-testid="stApp"] h3{{font-size:19px !important;font-weight:700}}
[data-testid="stMetricValue"]{{font-family:{FONT}}}
p,li{{line-height:1.7}}
[data-testid="stMetricLabel"] p{{color:#444;font-size:14px}}
[data-testid="stMetricValue"]{{font-weight:700}}
.stButton button,.stDownloadButton button{{border-radius:2px;border:1px solid #767676;background:#efefef;color:#000}}
.stButton button:hover,.stDownloadButton button:hover{{background:#e2e2e2;border-color:#4a4a4a;color:#000}}
.steps{{color:#666;margin-bottom:6px}} .steps b{{color:#000}}
.kv{{border-collapse:collapse;font-size:15px}}
.kv td{{border:1px solid #ccc;padding:4px 10px}} .kv td:first-child{{color:#444;background:#f6f6f6}}
.note{{font-size:13px;color:#555;margin:6px 0}}
</style>"""

def setup():
    pio.templates['moflab'] = go.layout.Template(layout=dict(
        font=dict(family=FONT, color='#000', size=13),
        colorway=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'], margin=dict(l=8, r=8, t=36, b=8)))
    pio.templates.default = 'simple_white+moflab'
    st.markdown(CSS, unsafe_allow_html=True)

def kv(rows):
    cells = ''.join(f'<tr><td>{html.escape(str(k))}</td><td>{html.escape(str(v))}</td></tr>' for k, v in rows)
    st.markdown(f'<table class="kv">{cells}</table>', unsafe_allow_html=True)

def note(text):
    st.markdown(f'<div class="note">{text}</div>', unsafe_allow_html=True)
