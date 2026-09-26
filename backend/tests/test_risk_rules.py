import pytest
from app.analysis.risk_rules import evaluate_risks
from app.models.schemas import Evidence, Relationship, RelationshipEvidence, Symbol, TestRecommendation


def test_rule_a_multiple_callers_shared_impact():
    target = Symbol(
        id="sym_util_func",
        name="shared_calc",
        qualified_name="pkg.util.shared_calc",
        type="function",
        file_path="pkg/util.py",
        start_line=1,
        end_line=5,
    )
    relationships = [
        Relationship(source="pkg.order.process", target=target.qualified_name, evidence=RelationshipEvidence(file_path="pkg/order.py", line=10, snippet="shared_calc()")),
        Relationship(source="pkg.cart.checkout", target=target.qualified_name, evidence=RelationshipEvidence(file_path="pkg/cart.py", line=20, snippet="shared_calc()")),
    ]
    risks = evaluate_risks(
        changed_symbols=[target],
        affected_symbols=[],
        relationships=relationships,
        test_recommendations=[],
        evidence_list=[],
        limitations=[],
    )
    risk_titles = [r.title for r in risks]
    assert any("shared-impact" in t.lower() for t in risk_titles)


def test_rule_b_untested_change():
    target = Symbol(
        id="sym_untested",
        name="do_something_risky",
        qualified_name="pkg.service.do_something_risky",
        type="function",
        file_path="pkg/service.py",
        start_line=1,
        end_line=5,
    )
    risks = evaluate_risks(
        changed_symbols=[target],
        affected_symbols=[],
        relationships=[],
        test_recommendations=[],  # No tests
        evidence_list=[],
        limitations=[],
    )
    risk_titles = [r.title for r in risks]
    assert any("test-coverage" in t.lower() for t in risk_titles)


def test_rule_c_api_handler_change():
    target = Symbol(
        id="sym_endpoint",
        name="create_order_endpoint",
        qualified_name="pkg.api_routes.create_order_endpoint",
        type="function",
        file_path="pkg/api_routes.py",
        start_line=10,
        end_line=20,
    )
    risks = evaluate_risks(
        changed_symbols=[target],
        affected_symbols=[],
        relationships=[],
        test_recommendations=[],
        evidence_list=[],
        limitations=[],
    )
    risk_titles = [r.title for r in risks]
    assert any("api contract" in t.lower() for t in risk_titles)
