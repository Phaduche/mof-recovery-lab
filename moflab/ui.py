"""Shared look & feel: a plain Korean shopping-portal layout (grey top bar, big logo, search box,
link row, bordered product-style cards, grey footer)."""
import html
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

BLUE, RED, INK = '#346aff', '#e52528', '#111'
STEPS = [('a1', 'A-1 데이터'), ('a2', 'A-2 채점'), ('a3', 'A-3 최종 3개'), ('b1', 'B-1 수정'),
         ('b2', 'B-2 재채점'), ('final', 'Final')]
RESEARCH = [('home', '소개'), ('methods', '방법 · 모델'), ('sources', '데이터 출처')]

CSS = f"""
<style>
html,body,[data-testid="stApp"],input,textarea,select,button{{
  font-family:-apple-system,"Apple SD Gothic Neo","Malgun Gothic",sans-serif;color:{INK}}}
[data-testid="stHeader"]{{display:none}}
.block-container{{max-width:1020px;padding:0 10px 0;}}
[data-testid="stApp"] h1{{font-size:22px !important;font-weight:700;margin:0}}
[data-testid="stApp"] h2{{font-size:20px !important;font-weight:700}}
[data-testid="stApp"] h3{{font-size:16px !important;font-weight:700}}
p,li{{font-size:14px;line-height:1.6}}
a{{color:inherit;text-decoration:none}}
.topbar{{background:#f0f0f0;border-bottom:1px solid #e3e3e3;font-size:12px;color:#555;height:32px;
  display:flex;align-items:center;justify-content:space-between;padding:0 10px;margin:0 -10px}}
.topbar a{{margin-left:14px}} .topbar a:hover{{color:{BLUE}}}
.hdr{{display:flex;align-items:center;gap:18px;height:96px;border-bottom:1px solid #ddd}}
.logo{{font-size:34px;font-weight:900;letter-spacing:-1.5px;white-space:nowrap;line-height:1}}
.logo span:nth-child(1){{color:#7b2c18}}.logo span:nth-child(2){{color:#e83a24}}.logo span:nth-child(3){{color:#f5a623}}
.logo span:nth-child(4){{color:#8bc34a}}.logo span:nth-child(5){{color:#29a7e1}}.logo span:nth-child(6){{color:#7b2c18}}
.logo small{{display:block;font-size:10px;letter-spacing:0;color:#999;font-weight:400;margin-top:4px}}
.search{{flex:1;display:flex;border:2px solid {BLUE};height:44px}}
.search input{{flex:1;border:0;padding:0 12px;font-size:14px;outline:none;background:#fff}}
.search button{{width:46px;border:0;background:#fff;font-size:20px;cursor:pointer}}
.icons{{display:flex;gap:18px}}
.icons a{{display:flex;flex-direction:column;align-items:center;font-size:11px;color:#333}}
.icons .ic{{font-size:24px;line-height:1.2}}
.gnb{{display:flex;gap:22px;height:42px;align-items:center;font-size:13px;border-bottom:1px solid #ddd;margin-bottom:18px}}
.gnb a:hover{{color:{BLUE}}} .gnb .on{{color:{BLUE};font-weight:700}} .gnb .rocket{{color:{BLUE};font-weight:700;font-style:italic}}
.gnb .sep{{color:#ccc}}
.sec-title{{display:flex;justify-content:space-between;align-items:baseline;margin:26px 0 12px;border-bottom:1px solid #eee;padding-bottom:8px}}
.sec-title h3{{font-size:20px;margin:0}} .sec-title em{{font-style:normal;color:{BLUE}}} .sec-title a{{font-size:12px;color:#777}}
.item{{border:1px solid #eee;background:#fafafa;padding:10px}}
.item .name{{font-size:13px;line-height:1.4;margin:6px 0 2px}}
.price-row{{display:flex;align-items:baseline;gap:6px}}
.rate{{color:{RED};font-weight:700;font-size:16px}} .price{{font-weight:700;font-size:16px}} .orig{{color:#888;text-decoration:line-through;font-size:12px}}
.rocket-tag{{display:inline-block;font-size:11px;color:{BLUE};font-weight:800;font-style:italic;margin-top:3px}}
.deliv{{font-size:12px;color:#00891a;margin-top:2px}}
.stars{{font-size:12px;color:#f5a623;margin-top:2px}} .stars span{{color:#888}}
[data-testid="stMetric"]{{border:1px solid #eee;background:#fafafa;padding:10px 14px}}
[data-testid="stMetricLabel"] p{{font-size:12px;color:#555}}
[data-testid="stMetricValue"]{{font-weight:700;color:{RED};font-size:22px}}
.stButton button,.stDownloadButton button{{border:1px solid {BLUE};color:{BLUE};background:#fff;border-radius:0;
  font-size:12px;font-weight:700;height:30px;min-height:30px;padding:0 14px}}
.stButton button:hover,.stDownloadButton button:hover{{background:{BLUE};color:#fff;border-color:{BLUE}}}
.stButton button p,.stDownloadButton button p{{font-size:12px}}
.kv{{border-collapse:collapse;font-size:13px;width:100%}}
.kv td{{padding:6px 10px;border-bottom:1px solid #eee}} .kv td:first-child{{color:#777;width:110px;background:#fafafa}}
.note{{font-size:12px;color:#777}}
.footer{{margin:50px -10px 0;background:#f8f8f8;border-top:1px solid #e5e5e5;padding:26px 10px 34px;font-size:11px;color:#777;line-height:1.8}}
.footer .links{{margin-bottom:10px;font-size:12px;color:#333}} .footer .links a{{margin-right:16px}}
</style>"""

def setup():
    pio.templates['moflab'] = go.layout.Template(layout=dict(
        font=dict(family='-apple-system, Apple SD Gothic Neo, Malgun Gothic, sans-serif', color=INK, size=12),
        colorway=[BLUE, RED, '#f5a623', '#00891a', '#8bc34a'], paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=8, r=8, t=36, b=8)))
    pio.templates.default = 'plotly_white+moflab'
    st.markdown(CSS, unsafe_allow_html=True)

def header(current=''):
    """Top bar + logo + search + link row, like a shopping portal. `current` = url path of this page."""
    gnb = ''.join(f'<a href="{p}" class="{"on" if p == current else ""}">{t}</a>' for p, t in STEPS)
    research = ''.join(f'<a href="{p}" class="{"on" if p == current else ""}">{t}</a>' for p, t in RESEARCH)
    st.markdown(f'''
<div class="topbar"><div>KJWP 2026 · 옹기종기 · AI로 인(P) 회수 MOF 찾기</div>
  <div><a href="home">소개</a><a href="methods">방법</a><a href="sources">데이터 출처</a>
  <a href="https://github.com/Phaduche/mof-recovery-lab" target="_blank">GitHub</a></div></div>
<div class="hdr">
  <div class="logo"><span>M</span><span>O</span><span>F</span><span>&nbsp;L</span><span>A</span><span>B</span>
    <small>인(P) 회수 MOF 검색</small></div>
  <form class="search" action="a2" method="get">
    <input name="q" placeholder="MOF 이름이나 금속으로 검색 (예: UiO-66, Zr)">
    <button type="submit">🔍</button></form>
  <div class="icons"><a href="a3"><span class="ic">🏆</span>최종 3개</a><a href="final"><span class="ic">🧪</span>Final</a></div>
</div>
<div class="gnb"><a href="final" class="rocket">AI추천</a>{gnb}<span class="sep">|</span>{research}</div>''',
                unsafe_allow_html=True)

def section(title_html, right=None):
    link = f'<a href="{right[1]}">{right[0]} &gt;</a>' if right else ''
    st.markdown(f'<div class="sec-title"><h3>{title_html}</h3>{link}</div>', unsafe_allow_html=True)

def item(name, score, rank=None, tag=None, deliv=None, stars=None):
    """Product-style info block under a thumbnail: name, red score, tag line, stars."""
    rank_html = f'<span class="rate">{rank}위</span>' if rank else ''
    parts = [f'<div class="name">{html.escape(name)}</div>',
             f'<div class="price-row">{rank_html}<span class="price">{score:.1f}점</span><span class="orig">/ 200</span></div>']
    if tag:
        parts.append(f'<div class="rocket-tag">{html.escape(tag)}</div>')
    if deliv:
        parts.append(f'<div class="deliv">{html.escape(deliv)}</div>')
    if stars is not None:
        n = max(0, min(5, round(stars * 5)))
        parts.append(f'<div class="stars">{"★" * n}{"☆" * (5 - n)} <span>안정성 {stars * 100:.0f}</span></div>')
    st.markdown(f'<div class="item">{"".join(parts)}</div>', unsafe_allow_html=True)

def footer():
    st.markdown('''
<div class="footer"><div class="links"><a href="home">소개</a><a href="methods">방법 · 모델</a><a href="sources">데이터 출처</a>
<a href="https://github.com/Phaduche/mof-recovery-lab" target="_blank">GitHub</a></div>
옹기종기 · 대한민국 청소년 물 대상(KJWP) 2026 본선<br>
데이터: CoRE MOF 2025 (CC BY 4.0), MOFSimplify / WS24 · 모델: Random Forest, CHGNet · 3D: 3Dmol.js<br>
이 사이트의 점수는 연구용 예측값이며 실험으로 검증 중입니다.</div>''', unsafe_allow_html=True)

def kv(rows):
    cells = ''.join(f'<tr><td>{html.escape(str(k))}</td><td>{html.escape(str(v))}</td></tr>' for k, v in rows)
    st.markdown(f'<table class="kv">{cells}</table>', unsafe_allow_html=True)

def note(text):
    st.markdown(f'<div class="note">{text}</div>', unsafe_allow_html=True)
