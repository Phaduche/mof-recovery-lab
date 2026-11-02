// Shared bits for every page: the link row at the top, the footer, data loading, small helpers.
const PAGES = [['a1.html', 'A-1 데이터'], ['a2.html', 'A-2 채점'], ['a3.html', 'A-3 최종 3개'],
  ['b1.html', 'B-1 수정'], ['b2.html', 'B-2 재채점'], ['final.html', 'Final']];
const RESEARCH = [['index.html', '소개'], ['methods.html', '방법과 모델'], ['sources.html', '데이터 출처']];
const WEIGHTS = { stability: 100, capture: 40, desorption: 35, reuse: 25 };
const LABELS = { stability: '안정성', capture: '포집', desorption: '탈착', reuse: '재사용' };
const COLORS = { stability: '#1f77b4', capture: '#ff7f0e', desorption: '#2ca02c', reuse: '#d62728' };

function nav() {
  const here = location.pathname.split('/').pop() || 'index.html';
  const row = items => items.map(([p, t]) => p === here ? `<b>${t}</b>` : `<a href="${p}">${t}</a>`).join(' | ');
  document.getElementById('nav').innerHTML =
    `<b>MOF Recovery Lab</b> · 옹기종기 · KJWP 2026<br>${row(PAGES)}<br>${row(RESEARCH)} | ` +
    `<a href="https://github.com/Phaduche/mof-recovery-lab">GitHub</a><hr>`;
  const f = document.getElementById('footer');
  if (f) f.innerHTML = '<hr><small>데이터: CoRE MOF 2025 (CC BY 4.0), MOFSimplify / WS24 · 모델: Random Forest, CHGNet · 3D: 3Dmol.js<br>' +
    '점수는 연구용 예측값이며 실험으로 검증 중입니다.</small>';
}

const loadJSON = path => fetch(path).then(r => r.json());
const fmt1 = x => x == null ? '' : Number(x).toFixed(1);
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

// Table from an array of rows and [key, header, formatter?] columns.
function table(el, rows, cols) {
  const head = '<tr>' + cols.map(c => `<th>${c[1]}</th>`).join('') + '</tr>';
  const body = rows.map(r => '<tr>' + cols.map(c => `<td>${c[2] ? c[2](r[c[0]], r) : esc(r[c[0]] ?? '')}</td>`).join('') + '</tr>').join('');
  el.innerHTML = `<table>${head}${body}</table>`;
}

// Stacked horizontal bars of the four score parts.
function scoreBars(el, rows, height) {
  const traces = Object.keys(WEIGHTS).map(k => ({
    type: 'bar', orientation: 'h', name: `${LABELS[k]} (${WEIGHTS[k]})`, y: rows.map(r => r.name), x: rows.map(r => r[k]),
    marker: { color: COLORS[k] }, hovertemplate: '%{y} · ' + LABELS[k] + ' %{x:.1f}<extra></extra>' }));
  Plotly.newPlot(el, traces, { barmode: 'stack', height: height || 60 + 36 * rows.length, margin: { l: 150, r: 10, t: 30, b: 30 },
    xaxis: { range: [0, 200] }, yaxis: { autorange: 'reversed' }, legend: { orientation: 'h', y: 1.15 }, font: { family: 'sans-serif' } },
    { displayModeBar: false, responsive: true });
}

// 3Dmol viewer for a CIF file (symmetry-expanded). highlight = element symbols drawn larger.
function crystal(id, cifPath, opts) {
  const o = Object.assign({ style: 'stick', cell: true, spin: false, highlight: ['Zr'] }, opts || {});
  const div = document.getElementById(id);
  div.textContent = '구조를 불러오는 중…';
  fetch(cifPath).then(r => r.text()).then(cif => {
    div.textContent = '';
    const v = $3Dmol.createViewer(div, { backgroundColor: 'white' });
    const m = v.addModel(cif, 'cif', { doAssembly: true, normalizeAssembly: true, duplicateAssemblyAtoms: true });
    v.setStyle({}, o.style === 'ballstick' ? { stick: { radius: 0.14 }, sphere: { scale: 0.25 } } : { stick: { radius: 0.18 } });
    if (o.highlight.length) v.setStyle({ elem: o.highlight }, { sphere: { scale: 0.45 }, stick: { radius: 0.16 } });
    if (o.cell) v.addUnitCell(m, { box: { color: 'black' }, astyle: { hidden: true }, bstyle: { hidden: true }, cstyle: { hidden: true } });
    v.zoomTo(); v.render();
    if (o.spin) v.spin('y', 0.6);
  }).catch(e => { div.textContent = '3D 구조를 표시하지 못했습니다: ' + e; });
}

document.addEventListener('DOMContentLoaded', nav);
