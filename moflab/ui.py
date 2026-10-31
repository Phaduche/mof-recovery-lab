"""Shared bits: a little CSS and a plotly template. Streamlit's dark theme does the rest."""
import html
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

CSS = """
<style>
.block-container{max-width:1100px}
.kv{border-collapse:collapse;font-size:14px}
.kv td{padding:3px 14px 3px 0;border-bottom:1px solid #333}
.kv td:first-child{color:#999}
.note{font-size:13px;color:#999}
</style>"""

def setup():
    pio.templates['moflab'] = go.layout.Template(layout=dict(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=8, r=8, t=36, b=8)))
    pio.templates.default = 'plotly_dark+moflab'
    st.markdown(CSS, unsafe_allow_html=True)

def kv(rows):
    cells = ''.join(f'<tr><td>{html.escape(str(k))}</td><td>{html.escape(str(v))}</td></tr>' for k, v in rows)
    st.markdown(f'<table class="kv">{cells}</table>', unsafe_allow_html=True)

def note(text):
    st.markdown(f'<div class="note">{text}</div>', unsafe_allow_html=True)
