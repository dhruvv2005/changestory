import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile
from app.analysis.ast_analyzer import parse_python_file
from app.analysis.caller_analyzer import analyze_direct_callers, find_call_sites_in_file
from app.config import SAMPLE_PROJECT_DIR
from app.models.schemas import Symbol


def test_analyze_direct_callers_calculator():
    # Target: changestory_sample/calculator.py :: calculate_total
    calc_path = SAMPLE_PROJECT_DIR / "changestory_sample" / "calculator.py"
    order_path = SAMPLE_PROJECT_DIR / "changestory_sample" / "order_service.py"

    all_modules = {
        "changestory_sample/calculator.py": parse_python_file(calc_path, "changestory_sample/calculator.py", "changestory_sample.calculator"),
        "changestory_sample/order_service.py": parse_python_file(order_path, "changestory_sample/order_service.py", "changestory_sample.order_service"),
    }

    target_sym = Symbol(
        id="sym_calc_total",
        name="calculate_total",
        qualified_name="changestory_sample.calculator.calculate_total",
        type="function",
        file_path="changestory_sample/calculator.py",
        start_line=4,
        end_line=6,
    )

    affected, relationships, evidence, limits = analyze_direct_callers(
        SAMPLE_PROJECT_DIR,
        [target_sym],
        all_modules,
    )

    # order_service.py calls calculate_total in process_order and summarize_cart
    caller_names = [a.name for a in affected]
    assert "process_order" in caller_names or "summarize_cart" in caller_names
    assert len(relationships) >= 1
    rel = relationships[0]
    assert rel.target == target_sym.qualified_name
    assert rel.relationship == "calls"
    assert rel.evidence is not None
    assert "calculate_total" in rel.evidence.snippet


def test_find_call_sites_accepts_utf8_bom():
    with NamedTemporaryFile(mode="w", encoding="utf-8", suffix="_caller.py", dir=Path(__file__).parent, delete=False) as stream:
        stream.write("\ufeffdef create_order(items):\n    return calculate_total(items)\n")
        caller_file = Path(stream.name)
    try:
        sites = find_call_sites_in_file(caller_file, caller_file.name)

        assert len(sites) == 1
        assert sites[0].target_name == "calculate_total"
    finally:
        caller_file.unlink(missing_ok=True)
