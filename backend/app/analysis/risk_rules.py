"""Deterministic Rules Engine for Risk Evaluation.

Evaluates detected changes, caller relationships, and test candidates against
deterministic rules (A, B, C, D, E) without any LLM dependencies.
"""

from typing import Dict, List, Set
from app.models.schemas import Evidence, Relationship, Risk, Symbol, TestRecommendation


def evaluate_risks(
    changed_symbols: List[Symbol],
    affected_symbols: List[Symbol],
    relationships: List[Relationship],
    test_recommendations: List[TestRecommendation],
    evidence_list: List[Evidence],
    limitations: List[str],
) -> List[Risk]:
    """Evaluate deterministic risk rules and return potential risks."""
    risks: List[Risk] = []

    # Map relationships by target (changed symbol)
    callers_by_target: Dict[str, List[Relationship]] = {}
    for rel in relationships:
        callers_by_target.setdefault(rel.target, []).append(rel)

    # Map test recommendations by related symbol
    tests_by_symbol: Dict[str, List[TestRecommendation]] = {}
    for rec in test_recommendations:
        for sym_name in rec.related_symbols:
            tests_by_symbol.setdefault(sym_name, []).append(rec)

    for sym in changed_symbols:
        callers = callers_by_target.get(sym.qualified_name, [])
        sym_evidence_ids = [e.id for e in evidence_list if e.symbol == sym.qualified_name]

        # Rule A: Multiple callers -> Potential shared-impact risk
        if len(callers) >= 2:
            caller_sources = [r.source for r in callers]
            caller_ev_ids = [
                e.id for e in evidence_list
                if any(r.evidence and r.evidence.line == e.line_start and r.evidence.file_path == e.file_path for r in callers)
            ]
            risks.append(
                Risk(
                    id=f"risk_shared_impact_{sym.id}",
                    severity="high" if len(callers) > 3 else "medium",
                    title="Potential shared-impact risk",
                    description=(
                        f"Changed symbol '{sym.name}' ({sym.qualified_name}) has {len(callers)} "
                        f"statically detected callers: {', '.join(caller_sources)}. "
                        "Changes to its behavior or signature may cascade to dependent components."
                    ),
                    related_symbols=[sym.qualified_name] + caller_sources,
                    evidence_ids=sorted(list(set(sym_evidence_ids + caller_ev_ids))),
                    is_potential=True,
                )
            )

        # Rule B: No obvious related test -> Potential test-coverage risk
        recs_for_sym = tests_by_symbol.get(sym.qualified_name, [])
        if not recs_for_sym and "test" not in sym.file_path.lower():
            risks.append(
                Risk(
                    id=f"risk_untested_change_{sym.id}",
                    severity="medium",
                    title="Potential test-coverage risk",
                    description=(
                        f"Changed symbol '{sym.name}' has no directly detected test candidate or test reference. "
                        "Behavioral regressions may not be caught by existing test suites."
                    ),
                    related_symbols=[sym.qualified_name],
                    evidence_ids=sym_evidence_ids,
                    is_potential=True,
                )
            )

        # Rule C: API handler changed -> Recommend integration-level check
        is_api_symbol = (
            "api" in sym.file_path.lower()
            or "route" in sym.file_path.lower()
            or "endpoint" in sym.name.lower()
            or "handler" in sym.name.lower()
        )
        if is_api_symbol:
            risks.append(
                Risk(
                    id=f"risk_api_handler_{sym.id}",
                    severity="medium",
                    title="Potential API contract change risk",
                    description=(
                        f"Symbol '{sym.name}' appears to be an API endpoint or route handler in '{sym.file_path}'. "
                        "Changes may impact external API clients, serialization formats, or response schemas."
                    ),
                    related_symbols=[sym.qualified_name],
                    evidence_ids=sym_evidence_ids,
                    is_potential=True,
                )
            )

        # Rule D: Shared utility changed -> Potential broader-impact finding
        is_shared_util = (
            "util" in sym.file_path.lower()
            or "common" in sym.file_path.lower()
            or "shared" in sym.file_path.lower()
        )
        # Check if callers reside in multiple different files
        caller_files = {r.evidence.file_path for r in callers if r.evidence}
        if is_shared_util or len(caller_files) >= 2:
            risks.append(
                Risk(
                    id=f"risk_shared_utility_{sym.id}",
                    severity="medium",
                    title="Potential broader-impact shared utility risk",
                    description=(
                        f"Changed symbol '{sym.name}' in '{sym.file_path}' is a shared utility or invoked "
                        f"across {max(1, len(caller_files))} distinct file(s). "
                        "Ensure standard formatting, normalization, and invariant contracts are preserved."
                    ),
                    related_symbols=[sym.qualified_name],
                    evidence_ids=sym_evidence_ids,
                    is_potential=True,
                )
            )

    # Deduplicate and sort deterministically
    unique_risks: Dict[str, Risk] = {r.id: r for r in risks}
    sorted_risks = sorted(unique_risks.values(), key=lambda r: (r.severity, r.title, r.id))
    return sorted_risks
