import pytest
from app.analysis.ast_analyzer import parse_python_file
from app.analysis.test_recommender import recommend_tests
from app.config import SAMPLE_PROJECT_DIR
from app.models.schemas import Symbol


def test_recommend_tests_for_calculator():
    test_calc_path = SAMPLE_PROJECT_DIR / "tests" / "test_calculator.py"
    all_modules = {
        "tests/test_calculator.py": parse_python_file(test_calc_path, "tests/test_calculator.py", "tests.test_calculator")
    }

    changed_sym = Symbol(
        id="sym_calculate_total",
        name="calculate_total",
        qualified_name="changestory_sample.calculator.calculate_total",
        type="function",
        file_path="changestory_sample/calculator.py",
        start_line=4,
        end_line=6,
    )

    recs, evidence = recommend_tests(
        SAMPLE_PROJECT_DIR,
        changed_symbols=[changed_sym],
        affected_symbols=[],
        all_modules=all_modules,
        evidence_list=[],
    )

    assert len(recs) >= 1
    titles = [r.title for r in recs]
    assert any("test_calculate_total" in t for t in titles)
    assert any(r.confidence == "high" for r in recs)
