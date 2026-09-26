"""ChangeStory application package.

This package intentionally exposes both the compatibility wrappers under
app/backend and the actual backend application modules under backend/app.
"""

from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_BACKEND_APP_DIR = _ROOT / "backend" / "app"

if _BACKEND_APP_DIR.exists():
    __path__.insert(0, str(_BACKEND_APP_DIR))

# Also keep the root-level compatibility package available without requiring
# an extra PYTHONPATH tweak when the project is run from the repository root.
__path__.insert(0, str(Path(__file__).resolve().parent))
