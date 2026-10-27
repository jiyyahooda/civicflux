"""Shared prerequisite checks without platform-dependent shell quoting."""
import sys
if sys.version_info[:2] != (3, 13):
    raise SystemExit('Use Python 3.13 and recreate this machine-local .venv.')
import xgboost
from ortools.sat.python import cp_model
if '--configured' in sys.argv:
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from backend.config import ADMIN_PASSWORD
    if not ADMIN_PASSWORD:
        raise SystemExit('Set CIVICFLUX_ADMIN_PASSWORD in your private .env file.')
print('Python, XGBoost and OR-Tools runtime checks passed.')
