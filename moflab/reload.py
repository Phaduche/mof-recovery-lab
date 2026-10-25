"""Reload moflab modules after a redeploy.

Streamlit Cloud pulls new files into a running process; page scripts re-run but already-imported
modules stay in memory, so a page can call a function the old module doesn't have (AttributeError).
"""
import importlib
import sys
from pathlib import Path
import streamlit as st

PACKAGE = Path(__file__).resolve().parent
# Dependencies first, so `from .data import ...` in ui picks up the reloaded module.
ORDER = ['descriptors', 'physics', 'scoring', 'cif', 'data', 'viewer', 'ui']

def refresh_if_changed():
    loaded = [(sys.modules[f'moflab.{n}'], PACKAGE / f'{n}.py') for n in ORDER if f'moflab.{n}' in sys.modules]
    # Modules imported before this guard existed carry no stamp, so they are reloaded once too.
    if all(getattr(m, '__mtime__', None) == p.stat().st_mtime_ns for m, p in loaded):
        return
    for module, path in loaded:
        importlib.reload(module)
        module.__mtime__ = path.stat().st_mtime_ns
    st.cache_data.clear()
