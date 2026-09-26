"""ChangeStory Unified Analysis Engine.

Orchestrates diff parsing, AST symbol extraction, static caller resolution,
risk evaluation, test recommendations, and limitation aggregation.
"""

from datetime import datetime, timezone
import hashlib
import re
from pathlib import Path
import subprocess
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
        """Parse Python files Git considers part of the project, respecting ignore rules."""
        modules: Dict[str, ParsedModuleInfo] = {}
        if not self.repo_dir.exists():
            return modules

        try:
            tracked = subprocess.run(
                ["git", "ls-files", "--cached", "--others", "--exclude-standard", "--", "."],
                cwd=str(self.repo_dir), capture_output=True, text=True, shell=False, timeout=10,
            )
        except (OSError, subprocess.SubprocessError):
            tracked = None

        if tracked and tracked.returncode == 0:
            py_files = [self.repo_dir / Path(name) for name in tracked.stdout.splitlines() if name.lower().endswith(".py")]
        else:
            excluded = {".git", ".changestory", ".venv", "venv", "node_modules", "__pycache__", "build", "dist"}
            py_files = [
                path for path in self.repo_dir.rglob("*.py")
                if not any(part.lower() in excluded for part in path.relative_to(self.repo_dir).parts)
            ]

        py_files = sorted(py_files, key=lambda p: str(p))
        for py_file in py_files:
            try:
                if self.repo_dir.resolve() not in py_file.resolve().parents or not py_file.is_file():
                    continue
            except OSError:
                continue
            rel_path = str(py_file.relative_to(self.repo_dir)).replace("\\", "/")
            if "venv" in rel_path or ".git" in rel_path or "__pycache__" in rel_path or "node_modules" in rel_path:
                continue

            # Derive module prefix from path e.g. changestory_sample.calculator
            clean_stem = rel_path.replace(".py", "").replace("/", ".")
            mod_info = parse_python_file(py_file, rel_path, module_prefix=clean_stem)
            modules[rel_path] = mod_info

        return modules

    def _resolve_module(self, file_path: str, repo_modules: Dict[str, ParsedModuleInfo]) -> Optional[ParsedModuleInfo]:
        """Try multiple strategies to resolve a diff file path to a ParsedModuleInfo.

        Handles cases where the diff uses a different path prefix than the scanned repo,
        e.g. 'a/src/calc.py' vs 'src/calc.py' vs 'calc.py'. It also tolerates common
        module naming aliases such as 'api.py' mapping to 'api_routes.py'.
        """
        normalized_file_path = file_path.replace("\\", "/").lstrip("./")
        basename = normalized_file_path.split("/")[-1]
        stem = basename.replace(".py", "")

        def stem_key(name: str) -> str:
            raw = name.replace("\\", "/").split("/")[-1].replace(".py", "")
            for suffix in ("_routes", "_service", "_controller", "_handlers", "_api", "_views"):
                if raw.endswith(suffix):
                    raw = raw[: -len(suffix)]
                    break
            return raw.lower()

        # Strategy 1: exact match
        if normalized_file_path in repo_modules:
            return repo_modules[normalized_file_path]

        # Strategy 2: suffix match — find any scanned module whose path ends with file_path
        for k, v in repo_modules.items():
            if k.endswith(normalized_file_path) or normalized_file_path.endswith(k):
                return v

        # Strategy 3: basename match with common alias suffixes (api.py -> api_routes.py)
        for k, v in repo_modules.items():
            k_base = k.split("/")[-1].replace(".py", "")
            if k_base.lower() == stem.lower():
                return v
            if stem_key(k) == stem.lower() or stem.lower() == stem_key(k):
                return v
            if stem_key(k).startswith(stem.lower()) or stem.lower().startswith(stem_key(k)):
                return v

        # Strategy 4: basename match (last resort for flat projects)
        candidates = [v for k, v in repo_modules.items() if k.split("/")[-1] == basename]
        if len(candidates) == 1:
            return candidates[0]

        # Strategy 5: try loading from disk with various path combinations
        for try_path in [self.repo_dir / normalized_file_path, Path(normalized_file_path), self.repo_dir / basename, Path(basename)]:
            if try_path.exists() and try_path.suffix == ".py":
                mod = parse_python_file(try_path, normalized_file_path)
                repo_modules[normalized_file_path] = mod
                return mod

        # Strategy 6: find the closest module by logical stem when alias paths are used
        toggle_candidates = []
        for k, v in repo_modules.items():
            k_stem = stem_key(k)
            if not k_stem or not stem:
                continue
            if k_stem == stem.lower() or stem.lower().startswith(k_stem) or k_stem.startswith(stem.lower()):
                toggle_candidates.append(v)
        if len(toggle_candidates) == 1:
            return toggle_candidates[0]

        return None

    def _extract_source_from_diff(self, diff_text: str, file_path: str) -> Optional[str]:
        """Reconstruct approximated source from diff hunk lines (+/context) for a given file.

        Used when the file isn't found on disk (e.g. custom diff of a remote repo).
        This lets AST analysis work on the NEW version of the file as shown in the diff.
        """
        lines: List[str] = []
        in_target = False
        for line in diff_text.splitlines():
            if line.startswith("--- ") or line.startswith("+++ "):
                # Check if this hunk block belongs to our file
                raw = line[4:].strip().lstrip("ab/")
                if file_path.endswith(raw) or raw.endswith(file_path.split("/")[-1]):
                    in_target = True
                else:
                    if in_target and line.startswith("--- "):
                        break  # moved to next file
                continue
            if not in_target:
                continue
            if line.startswith("@@"):
                continue
            if line.startswith("+"):
                lines.append(line[1:])
            elif line.startswith("-"):
                pass  # skip deleted lines — we want the new version
            elif line.startswith(" "):
                lines.append(line[1:])
        return "\n".join(lines) if lines else None

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
                # Try all resolution strategies
                mod_info = self._resolve_module(pf.file_path, repo_modules)

                if not mod_info:
                    # Last resort: reconstruct source from diff hunk lines for AST parsing
                    extracted = self._extract_source_from_diff(diff_text, pf.file_path)
                    if extracted and extracted.strip():
                        mod_info = parse_python_source(extracted, pf.file_path)
                        repo_modules[pf.file_path] = mod_info
                        all_limitations.append(
                            f"'{pf.file_path}' not found on disk — AST analysis based on diff hunk content only (partial)."
                        )

                if mod_info:
                    syms, evs, limits = map_changed_lines_to_symbols(mod_info, pf.changed_lines)
                    symbols_for_file.extend(syms)
                    all_evidence.extend(evs)
                    all_limitations.extend(limits)
                else:
                    all_limitations.append(
                        f"Python file '{pf.file_path}' not found in repository or diff. "
                        f"For custom diffs, use 'local' source_mode with a repository_path, "
                        f"or ensure diff paths match files in sample-project/."
                    )
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
