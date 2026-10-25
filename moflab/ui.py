"""Shared look & feel: clean research-portal styling (AlphaFold DB / MOFSimplify inspired)."""
import html
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
from .data import BANDS, band

INK, MUTED, LINE, ACCENT, SOFT = '#0F2236', '#62758A', '#E3E9F0', '#0053D6', '#F4F7FB'
VERDICT = {'추천': ('#E6F4EA', '#137333'), '비교군': ('#EEF2F6', '#3C4F63'), '제외': ('#FDECEA', '#B3261E')}

CSS = f"""
<style>
html,body,[data-testid="stApp"],input,textarea,select,button{{
  font-family:'MOFKorean',-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo','Malgun Gothic',sans-serif}}
.block-container{{max-width:1240px;padding-top:4.2rem;padding-bottom:5rem}}
h1,h2,h3{{letter-spacing:-.03em;color:{INK}}}
h3{{font-size:1.25rem;margin-top:.6rem}}
[data-testid="stMetric"]{{background:#fff;border:1px solid {LINE};border-radius:14px;padding:14px 18px}}
[data-testid="stMetricLabel"] p{{color:{MUTED};font-size:13px}}
[data-testid="stMetricValue"]{{font-weight:800}}
.hero{{display:flex;flex-direction:column;justify-content:center;height:100%;padding:8px 4px}}
.hero .tag{{display:inline-block;width:max-content;font-size:12px;font-weight:700;letter-spacing:.08em;
  color:{ACCENT};background:#E8F0FD;border-radius:999px;padding:5px 12px;margin-bottom:14px}}
.hero h1{{font-size:46px;line-height:1.12;font-weight:850;margin:0 0 14px}}
.hero h1 em{{font-style:normal;background:linear-gradient(90deg,#0053D6,#24A0C8);
  -webkit-background-clip:text;background-clip:text;color:transparent}}
.hero p{{font-size:18px;color:{MUTED};line-height:1.6;margin:0}}
.eyebrow{{font-size:12px;letter-spacing:.14em;color:{ACCENT};font-weight:800;text-transform:uppercase}}
.sub{{font-size:16px;color:{MUTED};margin:-6px 0 18px}}
.card{{background:#fff;border:1px solid {LINE};border-radius:16px;padding:18px 20px;height:100%}}
.card h4{{margin:0 0 6px;font-size:16px;color:{INK}}}
.card p,.card li{{color:{MUTED};font-size:14.5px;line-height:1.6;margin:0}}
.card ul{{padding-left:18px;margin:4px 0 0}}
.win{{background:linear-gradient(135deg,#0B3D91 0%,#0053D6 60%,#2A9FD6 100%);color:#fff;border:none}}
.win h4,.win p,.win li{{color:#fff}} .win .big{{font-size:34px;font-weight:850;line-height:1.1;margin:4px 0 10px}}
.icon{{width:38px;height:38px;border-radius:10px;background:#E8F0FD;color:{ACCENT};display:flex;
  align-items:center;justify-content:center;font-size:20px;margin-bottom:10px}}
.pill{{display:inline-block;padding:3px 10px;border-radius:999px;font-size:12px;font-weight:700;margin:0 6px 4px 0}}
.legend{{display:flex;gap:14px;flex-wrap:wrap;font-size:12.5px;color:{MUTED};margin:2px 0 6px}}
.legend span:before{{content:"";display:inline-block;width:11px;height:11px;border-radius:3px;
  margin-right:5px;vertical-align:-1px;background:var(--c)}}
.kv{{display:grid;grid-template-columns:120px 1fr;gap:7px 12px;font-size:14px}}
.kv div:nth-child(odd){{color:{MUTED}}}
.kv div:nth-child(even){{color:{INK};font-weight:600;word-break:break-word}}
.conf{{height:8px;border-radius:6px;background:#EDF1F5;overflow:hidden;margin:8px 0 2px}}
.conf i{{display:block;height:100%}}
.note{{font-size:12.5px;color:{MUTED};margin:6px 0}}
.step{{display:flex;gap:14px;align-items:flex-start}}
.step b.n{{flex:none;width:30px;height:30px;border-radius:50%;background:{ACCENT};color:#fff;display:flex;
  align-items:center;justify-content:center;font-size:14px}}
</style>"""

def setup():
    pio.templates['moflab'] = go.layout.Template(layout=dict(
        font=dict(family='MOFKorean, sans-serif', color=INK, size=13),
        colorway=[ACCENT, '#24A0C8', '#FF7D45', '#7A5CC8'], margin=dict(l=8, r=8, t=36, b=8),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'))
    pio.templates.default = 'plotly_white+moflab'
    st.markdown(CSS, unsafe_allow_html=True)

def hero(tag, title_html, text):
    st.markdown(f'<div class="hero"><span class="tag">{tag}</span><h1>{title_html}</h1><p>{text}</p></div>',
                unsafe_allow_html=True)

def heading(eyebrow, title, sub=None):
    st.markdown(f'<div class="eyebrow">{eyebrow}</div>', unsafe_allow_html=True)
    st.title(title)
    if sub:
        st.markdown(f'<p class="sub">{sub}</p>', unsafe_allow_html=True)

def card(title, text, icon=None, cls=''):
    top = f'<div class="icon">{icon}</div>' if icon else ''
    st.markdown(f'<div class="card {cls}">{top}<h4>{title}</h4><p>{text}</p></div>', unsafe_allow_html=True)

def list_card(title, items, cls=''):
    lis = ''.join(f'<li>{i}</li>' for i in items)
    st.markdown(f'<div class="card {cls}"><h4>{title}</h4><ul>{lis}</ul></div>', unsafe_allow_html=True)

def pill(text, bg='#E8F0FD', fg=ACCENT):
    return f"<span class='pill' style='background:{bg};color:{fg}'>{html.escape(str(text))}</span>"

def verdict_pill(v):
    bg, fg = VERDICT.get(v, VERDICT['비교군'])
    return pill(v, bg, fg)

def legend():
    items = ''.join(f'<span style="--c:{c}">{label} ≥{int(cut*100)}</span>' if cut else
                    f'<span style="--c:{c}">{label} &lt;50</span>' for cut, label, c in BANDS)
    st.markdown(f'<div class="legend">{items}</div>', unsafe_allow_html=True)

def confidence(p, title='물 안정성 지수'):
    label, color = band(p)
    value = '—' if p is None or p != p else f'{100*p:.0f}'
    width = 0 if value == '—' else 100 * p
    st.markdown(f'''<div class="card"><div class="eyebrow" style="color:{MUTED};letter-spacing:.06em">{title}</div>
      <div style="font-size:36px;font-weight:850;color:{INK};line-height:1.25">{value}
        {pill(label, color + '33', INK)}</div>
      <div class="conf"><i style="width:{width}%;background:{color}"></i></div></div>''', unsafe_allow_html=True)

def kv(rows):
    cells = ''.join(f'<div>{html.escape(str(k))}</div><div>{html.escape(str(v))}</div>' for k, v in rows)
    st.markdown(f'<div class="kv">{cells}</div>', unsafe_allow_html=True)

def note(text):
    st.markdown(f'<div class="note">{text}</div>', unsafe_allow_html=True)
