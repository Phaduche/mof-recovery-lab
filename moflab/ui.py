"""Shared look & feel: research-portal styling inspired by AlphaFold DB / MOFSimplify."""
import html
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
from .data import BANDS, band

INK, MUTED, LINE, ACCENT = '#13263A', '#5B6E80', '#E1E8EF', '#0053D6'

CSS = f"""
<style>
html,body,[data-testid="stApp"],input,textarea,select,button{{
  font-family:'MOFKorean',-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo','Malgun Gothic',sans-serif}}
.block-container{{max-width:1320px;padding-top:2.6rem;padding-bottom:4rem}}
h1,h2,h3{{letter-spacing:-.035em;color:{INK}}}
[data-testid="stSidebar"]{{background:#F6F9FC;border-right:1px solid {LINE}}}
[data-testid="stMetric"]{{background:#fff;border:1px solid {LINE};border-radius:12px;padding:16px 18px}}
[data-testid="stMetricLabel"]{{color:{MUTED}}}
.hero{{background:linear-gradient(120deg,#062A55 0%,#0053D6 55%,#24A0C8 100%);color:#fff;border-radius:18px;
  padding:44px 44px 38px;margin-bottom:26px;position:relative;overflow:hidden}}
.hero:after{{content:"";position:absolute;right:-80px;top:-80px;width:360px;height:360px;border-radius:50%;
  background:radial-gradient(circle,rgba(255,255,255,.18),rgba(255,255,255,0) 70%)}}
.hero .eyebrow{{font-size:12px;letter-spacing:.18em;font-weight:700;opacity:.85;text-transform:uppercase}}
.hero h1{{color:#fff;font-size:42px;line-height:1.15;margin:.35em 0 .3em;font-weight:800}}
.hero p{{font-size:17px;line-height:1.7;max-width:820px;opacity:.93;margin:0}}
.eyebrow{{font-size:12px;letter-spacing:.16em;color:{ACCENT};font-weight:700;text-transform:uppercase}}
.lead{{font-size:16.5px;color:{MUTED};line-height:1.75;max-width:960px}}
.card{{background:#fff;border:1px solid {LINE};border-radius:14px;padding:20px 22px;height:100%}}
.card h4{{margin:.1em 0 .4em;font-size:17px;color:{INK}}}
.card p{{color:{MUTED};font-size:14.5px;line-height:1.65;margin:0}}
.step{{display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:50%;
  background:#E8F0FD;color:{ACCENT};font-weight:800;font-size:13px;margin-bottom:8px}}
.pill{{display:inline-block;padding:3px 10px;border-radius:999px;font-size:12px;font-weight:700;margin-right:6px}}
.legend{{display:flex;gap:16px;flex-wrap:wrap;font-size:13px;color:{MUTED};margin:6px 0 2px}}
.legend span:before{{content:"";display:inline-block;width:12px;height:12px;border-radius:3px;
  margin-right:6px;vertical-align:-1px;background:var(--c)}}
.kv{{display:grid;grid-template-columns:150px 1fr;gap:6px 14px;font-size:14px}}
.kv div:nth-child(odd){{color:{MUTED}}}
.kv div:nth-child(even){{color:{INK};font-weight:600;word-break:break-all}}
.conf{{height:10px;border-radius:6px;background:#EDF1F5;overflow:hidden;margin:8px 0 4px}}
.conf i{{display:block;height:100%}}
.note{{font-size:13px;color:{MUTED};border-left:3px solid {LINE};padding-left:10px;margin:8px 0}}
footer{{visibility:hidden}}
</style>"""

def setup():
    pio.templates['moflab'] = go.layout.Template(layout=dict(
        font=dict(family='MOFKorean, sans-serif', color=INK), colorway=[ACCENT, '#24A0C8', '#FF7D45', '#7A5CC8'],
        margin=dict(l=10, r=10, t=40, b=10)))
    pio.templates.default = 'plotly_white+moflab'
    st.markdown(CSS, unsafe_allow_html=True)

def hero(eyebrow, title, text):
    st.markdown(f'<div class="hero"><div class="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{text}</p></div>',
                unsafe_allow_html=True)

def heading(eyebrow, title, text=None):
    st.markdown(f'<div class="eyebrow">{eyebrow}</div>', unsafe_allow_html=True)
    st.title(title)
    if text:
        st.markdown(f'<p class="lead">{text}</p>', unsafe_allow_html=True)

def card(title, text, step=None):
    badge = f'<div class="step">{step}</div>' if step is not None else ''
    st.markdown(f'<div class="card">{badge}<h4>{title}</h4><p>{text}</p></div>', unsafe_allow_html=True)

def legend():
    items = ''.join(f'<span style="--c:{c}">{label} (≥{int(cut*100)})</span>' if cut else
                    f'<span style="--c:{c}">{label} (&lt;50)</span>' for cut, label, c in BANDS)
    st.markdown(f'<div class="legend">{items}</div>', unsafe_allow_html=True)

def confidence(p, title='물 안정성 예측 지수'):
    label, color = band(p)
    value = '—' if p is None or p != p else f'{100*p:.1f}'
    width = 0 if value == '—' else 100 * p
    st.markdown(f'''<div class="card"><div class="eyebrow" style="color:{MUTED}">{title}</div>
      <div style="font-size:38px;font-weight:800;color:{INK};line-height:1.2">{value}
        <span class="pill" style="background:{color}22;color:{INK};vertical-align:middle;font-size:13px">{label}</span></div>
      <div class="conf"><i style="width:{width}%;background:{color}"></i></div>
      <p style="font-size:12.5px">0–100 = 100 × RF 분류기의 '물에 안정' 확률. 구조 유지율·인산염 성능이 아닙니다.</p></div>''',
                unsafe_allow_html=True)

def kv(rows):
    cells = ''.join(f'<div>{html.escape(str(k))}</div><div>{html.escape(str(v))}</div>' for k, v in rows)
    st.markdown(f'<div class="kv">{cells}</div>', unsafe_allow_html=True)

def note(text):
    st.markdown(f'<div class="note">{text}</div>', unsafe_allow_html=True)
