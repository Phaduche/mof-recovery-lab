"""Interactive 3D crystal viewer (3Dmol.js) embedded as a Streamlit component."""
import json
import streamlit.components.v1 as components

_3DMOL = 'https://cdnjs.cloudflare.com/ajax/libs/3Dmol/2.4.2/3Dmol-min.js'
STYLES = {'볼 & 스틱': {'stick': {'radius': 0.14}, 'sphere': {'scale': 0.25}},
          '스틱': {'stick': {'radius': 0.18}},
          '공간 채움': {'sphere': {'scale': 0.9}},
          '와이어': {'line': {'linewidth': 1.2}}}

def crystal(cif_text, style='볼 & 스틱', supercell=1, unit_cell=True, spin=False, height=520,
            highlight=None, frame=True):
    """Render a CIF with symmetry expansion. `highlight` = element symbols drawn larger (e.g. metal nodes)."""
    payload = json.dumps(cif_text).replace('</', '<\\/')  # never close the <script> early
    style_js = json.dumps(STYLES.get(style, STYLES['볼 & 스틱']))
    hl = json.dumps(highlight or [])
    box = ('background:radial-gradient(circle at 30% 20%,#fff 0%,#eef3f8 75%);border:1px solid #e3e9f0'
           if frame else 'background:transparent')
    hint = ('<div style="position:absolute;left:12px;bottom:10px;font:11px sans-serif;color:#7b8b9b">'
            '드래그 회전 · 스크롤 확대</div>') if frame else ''
    html = f"""
<div id="wrap" style="position:relative;width:100%;height:{height}px;border-radius:16px;overflow:hidden;{box}">
  <div id="v" style="width:100%;height:100%"></div>
  <div id="msg" style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;
       font:14px sans-serif;color:#5a6b7b">구조를 불러오는 중…</div>
  {hint}
</div>
<script src="{_3DMOL}"></script>
<script>
(function() {{
  const msg = document.getElementById('msg');
  try {{
    const viewer = $3Dmol.createViewer('v', {{backgroundAlpha: 0}});
    const m = viewer.addModel({payload}, 'cif',
        {{doAssembly: true, normalizeAssembly: true, duplicateAssemblyAtoms: true}});
    viewer.setStyle({{}}, {style_js});
    const hl = {hl};
    if (hl.length) viewer.setStyle({{elem: hl}}, {{sphere: {{scale: 0.45}}, stick: {{radius: 0.16}}}});
    if ({str(bool(unit_cell)).lower()}) viewer.addUnitCell(m, {{box: {{color: '#0053D6'}},
        astyle: {{hidden: true}}, bstyle: {{hidden: true}}, cstyle: {{hidden: true}}}});
    if ({int(supercell)} > 1) viewer.replicateUnitCell({int(supercell)}, {int(supercell)}, {int(supercell)}, m);
    viewer.zoomTo(); viewer.render();
    if ({str(bool(spin)).lower()}) viewer.spin('y', 0.6);
    msg.remove();
  }} catch (e) {{ msg.textContent = '3D 구조를 표시하지 못했습니다: ' + e; }}
}})();
</script>"""
    components.html(html, height=height + 8)
