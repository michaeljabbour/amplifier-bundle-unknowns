"""Make the module package importable when running from the repo root."""

import sys
from pathlib import Path

_MODULE_DIR = Path(__file__).resolve().parents[1]  # modules/tool-unknowns
if str(_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(_MODULE_DIR))
