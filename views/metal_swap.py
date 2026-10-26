import plotly.graph_objects as go
import streamlit as st
from moflab import data, ui, viewer

ui.heading('Metal swap', '금속 노드 바꾸기',
           'UiO-66-NH₂의 Zr₆ 노드를 다른 금속으로 바꾸면 에너지가 어떻게 변하나 · AI 원자간 퍼텐셜(CHGNet)')

df = data.metal_swap()
if df is None:
    st.info('아직 계산 결과가 없습니다. `python -m scripts.metal_swap`을 실행하세요.')
    st.stop()

OX_COLOR = {4: '#0053D6', 3: '#24A0C8', 2: '#FFB020', 1: '#E5484D'}
metals = df.metal.tolist()
pick = st.segmented_control('금속', metals, default='K' if 'K' in metals else metals[0], key='swap_metal') or 'Zr'
r = df.set_index('metal').loc[pick]
verdict, tone = data.swap_verdict(r)

left, right = st.columns([1, 1.3], gap='large')
with left:
    st.markdown(f'''<div class="card" style="background:{tone[0]};border-color:{tone[0]}">
      <div style="font-size:13px;font-weight:700;color:{tone[1]}">Zr → {pick} 교체 에너지</div>
      <div style="font-size:34px;font-weight:850;color:{tone[1]};line-height:1.25">{r.swap_energy_eV:+.2f}
      <span style="font-size:15px;font-weight:600">eV / 금속 원자</span></div>
      <div style="font-size:14px;font-weight:700;color:{tone[1]}">{verdict}</div></div>''', unsafe_allow_html=True)
    st.write('')
    ui.kv([('산화수', f'+{r.oxidation_state}  (Zr는 +4)'),
           ('전하 균형', '맞음' if r.charge_balanced else f'안 맞음 · 노드 전하 {r.node_charge_vs_zr:+d}'),
           ('이온 반지름', f'{r.ionic_radius_A:.2f} Å  (Zr 0.84)'),
           ('부피 변화', f'{r.volume_change_pct:+.1f} %'),
           ('평균 금속–O', f'{r.metal_o_A:.2f} Å'),
           ('UiO-66형 합성', r.reported)])
    ui.note('0 = Zr와 같음 · 양수 = Zr보다 불리 · 음수 = 계산상 더 유리 (합성 가능성과는 별개)')
with right:
    viewer.crystal(data.metal_swap_cif(pick), '볼 & 스틱', 1, True, False, height=400, highlight=[pick])
    st.caption(f'CHGNet으로 구조 이완한 Zr → {pick} 구조')

st.subheader('모든 금속 비교')
d = df.sort_values('swap_energy_eV')
fig = go.Figure(go.Bar(
    x=d.metal, y=d.swap_energy_eV, marker_color=[OX_COLOR[o] for o in d.oxidation_state],
    marker_line=dict(width=[3 if m == pick else 0 for m in d.metal], color='#0F2236'),
    text=[f'{v:+.2f}' for v in d.swap_energy_eV], textposition='outside',
    customdata=d[['oxidation_state', 'reported']], hovertemplate='%{x} (+%{customdata[0]}) · %{y:+.2f} eV<br>%{customdata[1]}<extra></extra>'))
fig.add_hline(y=0, line_color='#0F2236', line_width=1)
fig.update_layout(height=360, yaxis_title='교체 에너지 (eV / 금속)', xaxis_title=None)
st.plotly_chart(fig, width='stretch')
st.markdown(' '.join(f"<span class='pill' style='background:{c}22;color:#0F2236'>+{o}가</span>"
                     for o, c in OX_COLOR.items()), unsafe_allow_html=True)

with st.expander('어떻게 계산했나 · 한계'):
    meta = data.metal_swap_meta()
    st.markdown(f"""
1. UiO-66-NH₂ 구조에서 Zr 6개를 모두 다른 금속으로 바꿈
2. **{meta['potential']}** 으로 원자 위치와 격자를 함께 이완 (힘 < {meta['relax']['fmax_eV_A']} eV/Å)
3. 각 금속의 순수 결정(벌크)도 이완해서 기준 에너지 μ를 구함
""")
    st.latex(r'\Delta E_{\text{swap}} = \frac{E(\text{M-MOF}) - E(\text{Zr-MOF}) - 6(\mu_\text{M} - \mu_\text{Zr})}{6}')
    st.markdown('- CHGNet은 DFT(Materials Project) 결과로 학습한 **AI 퍼텐셜**입니다. DFT를 직접 돌린 값이 아니라 근사치입니다.\n'
                '- +1가(K, Na), +2가 금속은 전하가 맞지 않는 **가상의 구조**입니다. 실제로는 이런 노드가 만들어지지 않습니다.\n'
                '- 물 · 인산염과의 결합 에너지는 아직 계산하지 않았습니다.')
