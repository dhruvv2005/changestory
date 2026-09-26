import sys
from pathlib import Path

# Add backend and sample-project to sys.path
backend_dir = Path(__file__).resolve().parent
sample_dir = backend_dir.parent / "sample-project"

if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(sample_dir) not in sys.path:
    sys.path.insert(0, str(sample_dir))
