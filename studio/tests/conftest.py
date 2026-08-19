import sys
from pathlib import Path

_STUDIO_ROOT = Path(__file__).resolve().parent.parent
for p in (_STUDIO_ROOT, _STUDIO_ROOT / "core"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
