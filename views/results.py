import plotly.graph_objects as go
import streamlit as st
from moflab import data, ui, viewer

var = data.variants()
picks = data.picks()
by_key = var.set_index('key')
best = picks['ranking'][0]

ui.heading('Results', '결과', 'UiO-66 변형체와 최종 후보 19종 중 인산염 회수에 가장 알맞은 MOF')

# ── Winner ───────────────────────────────────────────────────────────
w, v = st.columns([1, 1.25], gap='large')
with w:
    row = by_key.loc[best['key']]
    reasons = ''.join(f'<li>{r}</li>' for r in best['why'])
    st.markdown(f'''<div class="card win"><p style="opacity:.85;font-size:13px;font-weight:700">🏆 최종 선택</p>
      <div class="big">{row["name"]}</div><ul>{reasons}</ul></div>''', unsafe_allow_html=True)
    st.write('')
    a, b = st.columns(2)
    a.metric('물 안정성 (문헌)', f"{row.water_class}등급 / 4")
    b.metric('MOFSimplify (MIT)', f"{picks['mofsimplify_official']['UiO-66-NH2']:.2f}")
    for p in picks['ranking'][1:]:
        r = by_key.loc[p['key']]
        st.markdown(f"**{p['rank']}. {r['name']}** · <span class='note'>{' · '.join(p['why'][:2])}</span>",
                    unsafe_allow_html=True)
    st.markdown(f"**대조군. {by_key.loc[picks['control'], 'name']}** · <span class='note'>작용기 없는 기준</span>",
                unsafe_allow_html=True)
with v:
    viewer.crystal(data.variant_cif(best['key']), '볼 & 스틱', 2, True, False, height=430, highlight=['Zr', 'N'])

# ── Funnel ───────────────────────────────────────────────────────────
st.write('')
st.subheader('어떻게 골랐나')
stable = var[var.water_class >= 3]
not_neg = stable[stable.effect != '-']
helps = not_neg[not_neg.effect == '+']
f1, f2 = st.columns([1.1, 1], gap='large')
with f1:
    fig = go.Figure(go.Funnel(
        y=['변형체 · 후보', '물에 안정 (3등급↑)', '인산염을 밀어내지 않음', '인산염 결합을 도움', '최종 선택'],
        x=[len(var), len(stable), len(not_neg), len(helps), 1], textinfo='value',
        marker=dict(color=['#C9D4DF', '#9DB8D9', '#65A0E0', '#2A7DE1', '#0053D6'])))
    fig.update_layout(height=300, margin=dict(l=8, r=8, t=8, b=8))
    st.plotly_chart(fig, width='stretch')
with f2:
    for n, (title, text) in enumerate([
            ('물 안정성', 'UiO-66-F, F₂는 2등급 → 제외'),
            ('전하', '–COOH, –SO₃H는 pH 7에서 음전하라 인산 이온(음전하)을 밀어냄 → 제외'),
            ('결합 자리', '–NH₂, –OH는 수소결합으로 인산염을 붙잡음 → 추천'),
            ('실험 가능성', '시판 · 문헌이 가장 많은 UiO-66-NH₂ 선택')], 1):
        st.markdown(f"<div class='step'><b class='n'>{n}</b><div><b>{title}</b><br>"
                    f"<span class='note'>{text}</span></div></div>", unsafe_allow_html=True)
        st.write('')

# ── Table ────────────────────────────────────────────────────────────
st.subheader('전체 비교')
order = {'추천': 0, '비교군': 1, '제외': 2}
table = var.assign(o=var.verdict.map(order)).sort_values(['o', 'water_class'], ascending=[True, False])
show = table.assign(verdict=table.verdict.map({'추천': '✅ 추천', '비교군': '▫️ 비교군', '제외': '⛔ 제외'}))
show = show[['name', 'verdict','group', 'effect_reason', 'water_class', 'acid_stable', 'boiling_stable', 'lcd_A', 'gsa_m2_g']]
event = st.dataframe(
    show.rename(columns={'name': 'MOF', 'verdict': '판정', 'group': '작용기', 'effect_reason': '인산염과의 관계',
                         'water_class': '물 안정 등급', 'acid_stable': '산 안정', 'boiling_stable': '끓는 물',
                         'lcd_A': '기공 (Å)', 'gsa_m2_g': '표면적 (m²/g)'}),
    hide_index=True, width='stretch', height=420, on_select='rerun', selection_mode='single-row',
    column_config={'물 안정 등급': st.column_config.ProgressColumn(min_value=0, max_value=4, format='%d'),
                   '기공 (Å)': st.column_config.NumberColumn(format='%.1f'),
                   '표면적 (m²/g)': st.column_config.NumberColumn(format='%.0f')})
ui.note('물 안정 등급: 문헌 실험 분류 (1 불안정 → 4 매우 안정, Burtch et al.). 행을 누르면 아래에서 3D로 비교합니다.')

# ── 3D compare ───────────────────────────────────────────────────────
picked = table.iloc[event.selection.rows[0]] if event.selection.rows else table.iloc[1]
st.subheader(f"3D 비교 · {picked['name']}")
c1, c2 = st.columns([1.5, 1], gap='large')
with c1:
    viewer.crystal(data.variant_cif(picked.key), '볼 & 스틱', 1, True, False, height=380)
with c2:
    st.markdown(ui.verdict_pill(picked.verdict) + ui.pill(picked.group), unsafe_allow_html=True)
    ui.kv([('판정 이유', picked.verdict_reason), ('물 안정', f'{picked.water_class}등급 · {picked.water_class_label}'),
           ('산 / 끓는 물', f"{'O' if picked.acid_stable else '—'} / {'O' if picked.boiling_stable else '—'}"),
           ('기공 지름', f'{picked.lcd_A:.1f} Å'), ('표면적', f'{picked.gsa_m2_g:,.0f} m²/g')])

with st.expander('한계'):
    st.markdown('- 등급은 **물** 안정성이며, 인산염 흡착량은 아직 실험값이 없습니다.\n'
                '- UiO-66 계열은 **염기(NaOH) 안정성 기록이 없습니다** → 탈착 조건은 실험에서 꼭 확인.\n'
                '- 이 19종은 AI 학습 데이터에 포함돼 있어 RF 점수는 참고용(in-sample)입니다. 판정은 문헌 등급 기준.')
