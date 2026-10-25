"""Every page renders without exceptions on the shipped snapshot."""
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['views/home.py', 'views/results.py', 'views/experiment.py', 'views/explore.py', 'views/entry.py',
         'views/predict.py', 'views/calculator.py', 'views/methods.py', 'views/sources.py']

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
    for name in reload.ORDER:
        mod = __import__(f'moflab.{name}', fromlist=['_'])
        mod.__dict__.pop('__mtime__', None)
    reload.refresh_if_changed()
    assert callable(data.variants)
