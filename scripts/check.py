from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jla.validation import validate_core

errs = validate_core()
if errs:
    raise SystemExit("Validation failed:\n- " + "\n- ".join(errs))
print("JLA validation passed.")
