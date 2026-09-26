"""ChangeStory Unified Analysis Engine.

Orchestrates diff parsing, AST symbol extraction, static caller resolution,
risk evaluation, test recommendations, and limitation aggregation.
"""

from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.analysis.ast_analyzer import (
    ParsedModuleInfo,
    map_changed_lines_to_symbols,
    parse_python_file,
    parse_python_source,
)
from app.analysis.caller_analyzer import analyze_direct_callers
from app.analysis.diff_parser import parse_unified_diff
from app.analysis.explanations import generate_explanations
from app.analysis.risk_rules import evaluate_risks
from app.analysis.test_recommender import recommend_tests
from app.models.schemas import (
    ChangeStoryReport,
    ChangeSummary,
    Evidence,
    FileChange,
    Relationship,
    Risk,
    Symbol,
    TestRecommendation,
)


STANDARD_LIMITATIONS = [
    "ChangeStory MVP currently analyzes Python source code only.",
    "Caller detection is strictly static; dynamic imports, reflection, and runtime dispatch are omitted.",
    "Runtime test coverage mapping is heuristic and based on static AST naming and import conventions.",
]


def generate_session_id(diff_text: str) -> str:
    """Generate deterministic session ID from diff content."""
    clean_diff = diff_text.strip()
    hasher = hashlib.sha256(clean_diff.encode("utf-8"))
    digest = hasher.hexdigest()[:12]
    # Include timestamp prefix to ensure uniqueness across repeated analyses if needed,
    # or purely deterministic digest
    return f"cs_{digest}"


class ChangeStoryEngine:
    def __init__(self, repo_dir: Path):
        self.repo_dir = repo_dir

    def scan_repository_modules(self) -> Dict[str, ParsedModuleInfo]:
        """Scan and parse all Python files in the repository."""
        modules: Dict[str, ParsedModuleInfo] = {}
        if not self.repo_dir.exists():
            return modules

        py_files = sorted(list(self.repo_dir.rglob("*.py")), key=lambda p: str(p))
        for py_file in py_files:
            rel_path = str(py_file.relative_to(self.repo_dir)).replace("\\", "/")
            if "venv" in rel_path or ".git" in rel_path or "__pycache__" in rel_path or "node_modules" in rel_path:
                continue

            # Derive module prefix from path e.g. changestory_sample.calculator
            clean_stem = rel_path.replace(".py", "").replace("/", ".")
            mod_info = parse_python_file(py_file, rel_path, module_prefix=clean_stem)
            modules[rel_path] = mod_info

        return modules

    def analyze(self, diff_text: str, session_id: Optional[str] = None) -> ChangeStoryReport:
        """Run complete deterministic analysis pipeline."""
        if not session_id:
            session_id = generate_session_id(diff_text)

        # 1. Parse unified diff
        parsed_files, diff_limitations = parse_unified_diff(diff_text)

        # 2. Collect repository AST modules
        repo_modules = self.scan_repository_modules()

        all_limitations: List[str] = list(STANDARD_LIMITATIONS)
        all_limitations.extend(diff_limitations)

        all_evidence: List[Evidence] = []
        all_changed_symbols: List[Symbol] = []
        file_changes: List[FileChange] = []

        total_lines_added = 0
        total_lines_deleted = 0

        # 3. For each changed file, map lines to AST symbols
        for pf in parsed_files:
            total_lines_added += pf.lines_added
            total_lines_deleted += pf.lines_deleted

            # Generate file-level evidence
            fev_id = f"ev_file_{pf.file_path}".replace("/", "_").replace(".", "_")
            fev = Evidence(
                id=fev_id,
                kind="file_change",
                file_path=pf.file_path,
                line_start=pf.changed_lines[0] if pf.changed_lines else 1,
                line_end=pf.changed_lines[-1] if pf.changed_lines else 1,
                symbol=None,
                description=f"File {pf.file_path} {pf.status} (+{pf.lines_added}, -{pf.lines_deleted})",
            )
            all_evidence.append(fev)

            # Map changed lines to symbols if Python file
            symbols_for_file: List[Symbol] = []
            if pf.file_path.endswith(".py"):
                mod_info = repo_modules.get(pf.file_path)
                if not mod_info:
                    # Try checking if file exists on disk
                    file_disk_path = self.repo_dir / pf.file_path
                    if file_disk_path.exists():
                        mod_info = parse_python_file(file_disk_path, pf.file_path)
                        repo_modules[pf.file_path] = mod_info

                if mod_info:
                    syms, evs, limits = map_changed_lines_to_symbols(mod_info, pf.changed_lines)
                    symbols_for_file.extend(syms)
                    all_evidence.extend(evs)
                    all_limitations.extend(limits)
                else:
                    all_limitations.append(f"Python file '{pf.file_path}' not found in active repository.")
            else:
                all_limitations.append(f"Non-Python file '{pf.file_path}' detected; AST analysis skipped.")

            all_changed_symbols.extend(symbols_for_file)

            file_changes.append(
                FileChange(
                    file_path=pf.file_path,
                    status=pf.status,
                    lines_added=pf.lines_added,
                    lines_deleted=pf.lines_deleted,
                    changed_lines=pf.changed_lines,
                    added_lines=pf.added_lines,
                    deleted_lines=pf.deleted_lines,
                    related_symbols=[s.qualified_name for s in symbols_for_file],
                    evidence_ids=[fev_id],
                )
            )

        # Deduplicate changed symbols
        unique_changed: Dict[str, Symbol] = {}
        for s in all_changed_symbols:
            unique_changed[s.id] = s
        changed_symbols = sorted(unique_changed.values(), key=lambda s: (s.file_path, s.start_line, s.name))

        # 4. Caller Analysis
        affected_symbols, relationships, caller_evidence, caller_limits = analyze_direct_callers(
            self.repo_dir,
            changed_symbols,
            repo_modules,
        )
        all_evidence.extend(caller_evidence)
        all_limitations.extend(caller_limits)

        # 5. Test Recommendations
        test_recs, test_evidence = recommend_tests(
            self.repo_dir,
            changed_symbols,
            affected_symbols,
            repo_modules,
            all_evidence,
        )
        all_evidence.extend(test_evidence)

        # 6. Risk Evaluation
        risks = evaluate_risks(
            changed_symbols=changed_symbols,
            affected_symbols=affected_symbols,
            relationships=relationships,
            test_recommendations=test_recs,
            evidence_list=all_evidence,
            limitations=all_limitations,
        )

        # 7. Explanations
        explanations = generate_explanations(
            changed_symbols=changed_symbols,
            affected_symbols=affected_symbols,
            relationships=relationships,
        )

        # Deduplicate evidence
        unique_ev: Dict[str, Evidence] = {}
        for e in all_evidence:
            unique_ev[e.id] = e
        final_evidence = sorted(unique_ev.values(), key=lambda e: (e.file_path, e.line_start, e.id))

        # Deduplicate limitations
        unique_limitations = list(dict.fromkeys(all_limitations))

        # 8. Summary
        change_summary = ChangeSummary(
            files_changed=len(file_changes),
            lines_added=total_lines_added,
            lines_deleted=total_lines_deleted,
            symbols_changed=len(changed_symbols),
            symbols_affected=len(affected_symbols),
            potential_risks=len(risks),
            test_recommendations=len(test_recs),
        )

        report = ChangeStoryReport(
            schema_version="1.0",
            session_id=session_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            change_summary=change_summary,
            files=file_changes,
            changed_symbols=changed_symbols,
            affected_symbols=affected_symbols,
            relationships=relationships,
            evidence=final_evidence,
            risks=risks,
            test_recommendations=test_recs,
            verification=None,
            limitations=unique_limitations,
            explanations=explanations,
        )

        return report
