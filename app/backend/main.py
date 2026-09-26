"""Compatibility entrypoint bridging app/backend to backend/app/main."""

import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parents[2]
backend_dir = root_dir / "backend"
for candidate in (str(root_dir), str(backend_dir)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

try:
    from app.main import app, health_check # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback for direct backend execution
    from backend.app.main import app, health_check

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000)
