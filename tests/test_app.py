"""Every page renders without exceptions on the shipped snapshot."""
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['views/home.py', 'views/experiment.py', 'views/methods.py', 'views/sources.py']
STEPS = ['a1', 'a2', 'a3', 'b1', 'b2', 'final']

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

def test_metal_swap_results_are_consistent():
    from moflab import data
    df = data.metal_swap()
    assert df is not None
    zr = df.set_index('metal').loc['Zr']
    assert abs(zr.swap_energy_eV) < 1e-9          # reference is zero by definition
    k = df.set_index('metal').loc['K']
    assert data.swap_verdict(k)[0].startswith('전하 불균형')

def test_pipeline_order_and_final():
    from moflab import data
    a, b, final = data.stage_a(), data.stage_b(), data.final_pick()
    assert a.total.round(1).is_monotonic_decreasing and list(a['rank'][:3]) == [1, 2, 3]   # ties → balance z
    assert set(b[b.change == '원본'].parent) == set(a.head(3).name)       # B starts from A's top 3
    assert b.iloc[0].id == final['id']                                    # Final = best of B
    assert b.total.max() >= a.total.max()
    assert (b.total <= 200).all() and (b.stability <= 100).all()

def test_validation_page_compares_rankings():
    at = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=60).run()
    at.switch_page(str(ROOT / 'views/experiment.py')).run()
    assert not at.exception, [e.message for e in at.exception]
    table = at.dataframe[-1].value
    assert list(table['항목']) == ['물 안정성', '인 포집', '탈착', '재사용']

def test_rank_agreement():
    from moflab.pipeline import rank_agreement
    ai = [93.2, 74.9, 57.9, 67.9, 69.4]
    assert rank_agreement(ai, [95, 90, 70, None, None]) == 1.0          # same order
    assert rank_agreement(ai, [70, 90, 95, None, None]) == -1.0         # reversed
    assert rank_agreement(ai, [95, None, None, None, None]) is None     # fewer than 3

@pytest.mark.parametrize('step', STEPS)
def test_step_page_renders(step):
    at = AppTest.from_string(f"from moflab import steps, ui\nui.setup()\nsteps.{step}()", default_timeout=60).run()
    assert not at.exception, [e.message for e in at.exception]

def test_top_menu_is_the_pipeline():
    at = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=60).run()
    assert not at.exception, [e.message for e in at.exception]
    assert list(at.session_state['step_pages']) == STEPS
