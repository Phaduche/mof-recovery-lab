"""Every page renders without exceptions on the shipped snapshot."""
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['views/tool.py', 'views/metal_swap.py', 'views/explore.py', 'views/calculator.py', 'views/home.py', 'views/results.py',
         'views/experiment.py', 'views/methods.py', 'views/sources.py']

@pytest.mark.parametrize('page', PAGES)
def test_page_renders(page):
    at = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=60).run()
    at.switch_page(str(ROOT / page)).run()
    assert not at.exception, [e.message for e in at.exception]

def test_finalist_predictions_are_in_range():
    from moflab import data
    for f in data.finalists():
        if f['descriptor_frame'] is not None:
            p = data.predict_water(f['descriptor_frame']).water_prob.iloc[0]
            assert 0 <= p <= 1

def test_stale_module_is_reloaded():
    """Simulates Streamlit Cloud keeping an old moflab.data in memory after a redeploy."""
    from moflab import data, reload
    del data.variants
    for module, _ in reload._loaded():
        module.__dict__.pop('__mtime__', None)
    reload.refresh_if_changed()
    assert callable(data.variants)

def test_tool_variant_and_upload_modes_render():
    at = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=60).run()
    for mode in [1, 2]:
        at.segmented_control(key='tool_source').set_value(at.segmented_control(key='tool_source').options[mode]).run()
        assert not at.exception, [e.message for e in at.exception]

def test_screening_rules():
    from moflab import screen
    good = screen.checklist(water_prob=0.9, in_domain=True, metal='Zr', pld_A=5.0)
    assert screen.summary(good)[0] == '유망'
    unstable = screen.checklist(water_class=2, metal='Zr', pld_A=5.0)
    assert screen.summary(unstable)[0] == '부적합'
    repel = screen.checklist(water_class=3, metal='Zr', pld_A=5.0, group_effect='-')
    assert screen.summary(repel)[0] == '검토'

def test_final_pick_screens_as_promising():
    from moflab import data, screen
    r = data.variants().set_index('key').loc['UiO-66-NH2']
    rows = screen.checklist(r.rf_in_sample, None, 'Zr', r.pld_A, r.water_class, r.effect)
    assert screen.summary(rows)[0] == '유망'

def test_metal_swap_results_are_consistent():
    from moflab import data
    df = data.metal_swap()
    assert df is not None
    zr = df.set_index('metal').loc['Zr']
    assert abs(zr.swap_energy_eV) < 1e-9          # reference is zero by definition
    k = df.set_index('metal').loc['K']
    assert data.swap_verdict(k)[0].startswith('전하 불균형')
