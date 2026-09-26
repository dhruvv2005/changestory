"""Deterministic Test Recommendation Engine.

Identifies existing candidate tests in the test suite that cover or reference
changed symbols and their affected callers through static inspection.
"""

from pathlib import Path
from typing import Dict, List, Set, Tuple
from app.analysis.ast_analyzer import ParsedModuleInfo
from app.models.schemas import Evidence, Symbol, TestRecommendation


def recommend_tests(
    repo_dir: Path,
    changed_symbols: List[Symbol],
    affected_symbols: List[Symbol],
    all_modules: Dict[str, ParsedModuleInfo],
    evidence_list: List[Evidence],
) -> Tuple[List[TestRecommendation], List[Evidence]]:
    """Recommend targeted existing tests for changed and affected symbols."""
    recommendations: List[TestRecommendation] = []
    new_evidence: List[Evidence] = []

    # Find all test modules
    test_modules: Dict[str, ParsedModuleInfo] = {}
    for rel_path, mod_info in all_modules.items():
        if "test" in rel_path.lower():
            test_modules[rel_path] = mod_info

    # Map symbols for matching
    all_target_symbols = changed_symbols + affected_symbols
    rec_keys_seen: Set[str] = set()

    for sym in all_target_symbols:
        is_direct_change = sym in changed_symbols
        clean_name = sym.name.lower()
        module_stem = Path(sym.file_path).stem.lower()

        for test_path, test_mod in test_modules.items():
            test_stem = Path(test_path).stem.lower()
            is_file_match = (
                test_stem == f"test_{module_stem}"
                or test_stem == module_stem
                or module_stem in test_stem
            )

            for test_sym in test_mod.symbols:
                if not test_sym.name.startswith("test_") and not test_sym.name.startswith("Test"):
                    continue

                test_fn_name = test_sym.name.lower()

                # Level 1: Test function explicitly names the symbol (e.g. test_calculate_total -> calculate_total)
                explicit_name_match = (
                    test_fn_name == f"test_{clean_name}"
                    or test_fn_name.endswith(f"_{clean_name}")
                    or clean_name in test_fn_name
                )

                # Check if test file actually imports or references the target
                imports_target = (
                    sym.name in test_mod.imports
                    or any(sym.name in target for target in test_mod.imports.values())
                )

                confidence = None
                reason = ""

                if explicit_name_match and (is_file_match or imports_target):
                    confidence = "high" if is_direct_change else "medium"
                    reason = (
                        f"Target test '{test_sym.name}' in '{test_path}' directly tests "
                        f"symbol '{sym.name}' with matching naming and module proximity."
                    )
                elif imports_target and is_file_match:
                    confidence = "medium" if is_direct_change else "low"
                    reason = (
                        f"Test '{test_sym.name}' is within dedicated test suite '{test_path}' "
                        f"which imports '{sym.name}'."
                    )
                elif is_file_match and is_direct_change:
                    confidence = "low"
                    reason = (
                        f"Test '{test_sym.name}' is in test suite '{test_path}' "
                        f"covering module '{module_stem}'."
                    )

                if confidence:
                    rec_key = f"{test_path}::{test_sym.name}::{sym.qualified_name}"
                    if rec_key not in rec_keys_seen:
                        rec_keys_seen.add(rec_key)

                        ev_id = f"ev_test_{test_path}_{test_sym.start_line}".replace("/", "_").replace(".", "_")
                        test_ev = Evidence(
                            id=ev_id,
                            kind="test_ref",
                            file_path=test_path,
                            line_start=test_sym.start_line,
                            line_end=test_sym.end_line,
                            symbol=test_sym.qualified_name,
                            description=f"Existing test candidate '{test_sym.name}' in '{test_path}'",
                        )
                        new_evidence.append(test_ev)

                        rec_id = f"rec_{test_path}_{test_sym.name}_{sym.id}".replace("/", "_").replace(".", "_")
                        recommendations.append(
                            TestRecommendation(
                                id=rec_id,
                                title=f"Run {test_sym.name} ({test_path})",
                                reason=reason,
                                related_symbols=[sym.qualified_name],
                                evidence_ids=[ev_id],
                                confidence=confidence,
                                test_file=test_path,
                                test_symbol=test_sym.qualified_name,
                            )
                        )

    # Sort deterministically: high confidence first, then file/title
    confidence_order = {"high": 1, "medium": 2, "low": 3}
    recommendations.sort(key=lambda r: (confidence_order.get(r.confidence, 4), r.test_file or "", r.title))
    new_evidence.sort(key=lambda e: (e.file_path, e.line_start, e.id))

    return recommendations, new_evidence
