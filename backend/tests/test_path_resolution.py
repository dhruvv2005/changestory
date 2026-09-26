from app.analysis.engine import ChangeStoryEngine
from app.config import SAMPLE_PROJECT_DIR


def test_resolve_module_handles_api_aliases_and_route_suffixes():
    engine = ChangeStoryEngine(SAMPLE_PROJECT_DIR)
    repo_modules = engine.scan_repository_modules()

    resolved = engine._resolve_module("changestory_sample/api.py", repo_modules)
    assert resolved is not None
    assert resolved.file_path.endswith("api_routes.py")
    assert any(sym.name == "get_order_endpoint" for sym in resolved.symbols)
