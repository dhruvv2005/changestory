"""Backend application package with root-level compatibility modules."""

from pathlib import Path

# Backend tests and commands commonly put ``backend`` on ``sys.path``, which
# makes this directory the ``app`` package. Also expose the repository-level
# ``app`` directory so ``app.backend`` compatibility imports work in that mode.
_REPOSITORY_APP_DIR = Path(__file__).resolve().parents[2] / "app"
if _REPOSITORY_APP_DIR.is_dir() and str(_REPOSITORY_APP_DIR) not in __path__:
    __path__.append(str(_REPOSITORY_APP_DIR))
