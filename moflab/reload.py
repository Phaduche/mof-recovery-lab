"""Reload moflab modules after a redeploy.

Streamlit Cloud pulls new files into a running process; page scripts re-run but already-imported
modules stay in memory, so a page can call a function the old module doesn't have (AttributeError).
"""
import importlib
import sys
from pathlib import Path
import streamlit as st

PACKAGE = Path(__file__).resolve().parent
# Modules that import siblings go last, so `from .data import ...` picks up the reloaded module.
LAST = ['data', 'viewer', 'ui']

def _loaded():
    names = [n.split('.', 1)[1] for n in sys.modules if n.startswith('moflab.') and n != __name__]
    names.sort(key=lambda n: (LAST.index(n) if n in LAST else -1, n))
    return [(sys.modules[f'moflab.{n}'], PACKAGE / f'{n}.py') for n in names if (PACKAGE / f'{n}.py').exists()]

def refresh_if_changed():
    loaded = _loaded()
    # Modules imported before this guard existed carry no stamp, so they are reloaded once too.
    if all(getattr(m, '__mtime__', None) == p.stat().st_mtime_ns for m, p in loaded):
        return
    for module, path in loaded:
        importlib.reload(module)
        module.__mtime__ = path.stat().st_mtime_ns
    st.cache_data.clear()
