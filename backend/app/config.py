from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SAMPLE_PROJECT_DIR = BASE_DIR / "sample-project"
REPORTS_DIR = BASE_DIR / "reports"
FIXTURES_DIR = BASE_DIR / "fixtures"

# Ensure reports directory exists
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
