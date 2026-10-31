"""Shared look & feel: dark, terminal-like research tool (system fonts, monospace labels, thin borders)."""
import html
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

FONT = "-apple-system, 'Helvetica Neue', 'Apple SD Gothic Neo', 'Malgun Gothic', Arial, sans-serif"
MONO = "'SF Mono', Menlo, Consolas, 'Courier New', monospace"
BG, PANEL, LINE, INK, MUTED, ACCENT = '#0b0d10', '#14181d', '#2a3038', '#e6e8eb', '#8b949e', '#e3b341'
SERIES = ['#58a6ff', '#e3b341', '#3fb950', '#f85149', '#bc8cff']

CSS = f"""
<style>
html,body,[data-testid="stApp"],input,textarea,select,button{{font-family:{FONT}}}
.block-container{{max-width:1100px;padding-top:4rem;padding-bottom:4rem}}
h1,h2,h3,[data-testid="stHeading"] *{{font-family:{FONT} !important;letter-spacing:-.01em !important;color:{INK}}}
[data-testid="stApp"] h1{{font-size:28px !important;font-weight:600}}
[data-testid="stApp"] h2{{font-size:21px !important;font-weight:600}}
[data-testid="stApp"] h3{{font-size:17px !important;font-weight:600}}
p,li{{line-height:1.7;color:{INK}}}
[data-testid="stCaptionContainer"] p,.steps{{font-family:{MONO};font-size:12.5px;color:{MUTED}}}
[data-testid="stMetric"]{{border-left:2px solid {LINE};padding-left:12px}}
[data-testid="stMetricLabel"] p{{font-family:{MONO};font-size:12px;color:{MUTED};text-transform:uppercase;letter-spacing:.06em}}
[data-testid="stMetricValue"]{{font-family:{MONO};font-weight:500;color:{INK}}}
.stButton button,.stDownloadButton button{{font-family:{MONO};font-size:13px;border-radius:3px;border:1px solid {LINE};
  background:{PANEL};color:{INK}}}
.stButton button:hover,.stDownloadButton button:hover{{border-color:{ACCENT};color:{ACCENT};background:{PANEL}}}
.steps{{margin-bottom:4px}} .steps b{{color:{ACCENT};font-weight:600}}
.kv{{border-collapse:collapse;font-family:{MONO};font-size:13px}}
.kv td{{border-bottom:1px solid {LINE};padding:5px 12px 5px 0}} .kv td:first-child{{color:{MUTED};padding-right:24px}}
.note{{font-family:{MONO};font-size:12.5px;color:{MUTED};margin:6px 0}}
hr{{border-color:{LINE}}}
</style>"""

def setup():
    pio.templates['moflab'] = go.layout.Template(layout=dict(
        font=dict(family=FONT, color=INK, size=12), colorway=SERIES,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=8, r=8, t=36, b=8),
        xaxis=dict(gridcolor=LINE, zerolinecolor=LINE, linecolor=LINE),
        yaxis=dict(gridcolor=LINE, zerolinecolor=LINE, linecolor=LINE),
        title=dict(font=dict(family=MONO, size=13, color=MUTED)), legend=dict(font=dict(size=11))))
    pio.templates.default = 'plotly_dark+moflab'
    st.markdown(CSS, unsafe_allow_html=True)

def kv(rows):
    cells = ''.join(f'<tr><td>{html.escape(str(k))}</td><td>{html.escape(str(v))}</td></tr>' for k, v in rows)
    st.markdown(f'<table class="kv">{cells}</table>', unsafe_allow_html=True)

def note(text):
    st.markdown(f'<div class="note">{text}</div>', unsafe_allow_html=True)
