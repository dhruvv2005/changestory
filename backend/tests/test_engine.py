import pytest
from app.analysis.engine import ChangeStoryEngine
from app.config import FIXTURES_DIR, SAMPLE_PROJECT_DIR


def test_engine_scenario_a():
    diff_path = FIXTURES_DIR / "diffs" / "scenario_a.diff"
    diff_text = diff_path.read_text(encoding="utf-8")

    engine = ChangeStoryEngine(SAMPLE_PROJECT_DIR)
    report = engine.analyze(diff_text)

    assert report.schema_version == "1.0"
    assert report.change_summary.files_changed == 1
    assert report.change_summary.symbols_changed >= 1

    changed_names = [s.name for s in report.changed_symbols]
    assert "calculate_total" in changed_names

    # Check caller detected in order_service
    caller_names = [a.name for a in report.affected_symbols]
    assert "process_order" in caller_names or "summarize_cart" in caller_names

    # Check test recommendation
    assert len(report.test_recommendations) >= 1
    test_titles = [r.title for r in report.test_recommendations]
    assert any("test_calculate_total" in t for t in test_titles)

    # Check explanations
    assert len(report.explanations) >= 1
    assert any(e.symbol == "changestory_sample.calculator.calculate_total" for e in report.explanations)


def test_engine_scenario_b():
    diff_path = FIXTURES_DIR / "diffs" / "scenario_b.diff"
    diff_text = diff_path.read_text(encoding="utf-8")

    engine = ChangeStoryEngine(SAMPLE_PROJECT_DIR)
    report = engine.analyze(diff_text)

    assert report.change_summary.files_changed == 1
    # Check API contract risk or test rec
    assert report.change_summary.potential_risks >= 1


def test_engine_scenario_c():
    diff_path = FIXTURES_DIR / "diffs" / "scenario_c.diff"
    diff_text = diff_path.read_text(encoding="utf-8")

    engine = ChangeStoryEngine(SAMPLE_PROJECT_DIR)
    report = engine.analyze(diff_text)

    assert report.change_summary.files_changed == 1
    changed_names = [s.name for s in report.changed_symbols]
    assert "format_currency" in changed_names

    # Utility should have callers across multiple files
    assert len(report.affected_symbols) >= 1
    risk_titles = [r.title for r in report.risks]
    assert any("shared utility" in t.lower() or "shared-impact" in t.lower() for t in risk_titles)
