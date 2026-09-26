"""Conservative Static Direct Caller Analyzer.

Inspects Python ASTs to find direct call expressions that statically resolve
to changed functions or methods.
"""

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from app.analysis.ast_analyzer import ParsedModuleInfo, ParsedSymbolInfo, parse_python_file, parse_python_source
from app.models.schemas import Evidence, Relationship, RelationshipEvidence, Symbol


@dataclass
class CallSite:
    caller_symbol: Optional[str]  # qualified name or None (if module level)
    caller_file: str
    target_name: str
    line: int
    snippet: str


class CallVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str, lines: List[str], module_prefix: str = ""):
        self.file_path = file_path.replace("\\", "/")
        self.lines = lines
        self.module_prefix = module_prefix
        self.call_sites: List[CallSite] = []
        self.current_caller_stack: List[str] = []

    def _get_snippet(self, lineno: int) -> str:
        if 1 <= lineno <= len(self.lines):
            return self.lines[lineno - 1].strip()
        return ""

    def visit_FunctionDef(self, node: ast.FunctionDef):
        name = node.name
        if self.current_caller_stack:
            qual = f"{self.current_caller_stack[-1]}.{name}"
        elif self.module_prefix:
            qual = f"{self.module_prefix}.{name}"
        else:
            qual = name
        self.current_caller_stack.append(qual)
        self.generic_visit(node)
        self.current_caller_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        name = node.name
        if self.current_caller_stack:
            qual = f"{self.current_caller_stack[-1]}.{name}"
        elif self.module_prefix:
            qual = f"{self.module_prefix}.{name}"
        else:
            qual = name
        self.current_caller_stack.append(qual)
        self.generic_visit(node)
        self.current_caller_stack.pop()

    def visit_ClassDef(self, node: ast.ClassDef):
        name = node.name
        if self.current_caller_stack:
            qual = f"{self.current_caller_stack[-1]}.{name}"
        elif self.module_prefix:
            qual = f"{self.module_prefix}.{name}"
        else:
            qual = name
        self.current_caller_stack.append(qual)
        self.generic_visit(node)
        self.current_caller_stack.pop()

    def visit_Call(self, node: ast.Call):
        caller = self.current_caller_stack[-1] if self.current_caller_stack else f"{self.file_path}:<module>"
        lineno = node.lineno
        snippet = self._get_snippet(lineno)

        # Case 1: Simple Name call: func(...)
        if isinstance(node.func, ast.Name):
            self.call_sites.append(
                CallSite(
                    caller_symbol=caller,
                    caller_file=self.file_path,
                    target_name=node.func.id,
                    line=lineno,
                    snippet=snippet,
                )
            )
        # Case 2: Attribute call: obj.func(...) or module.func(...)
        elif isinstance(node.func, ast.Attribute):
            self.call_sites.append(
                CallSite(
                    caller_symbol=caller,
                    caller_file=self.file_path,
                    target_name=node.func.attr,
                    line=lineno,
                    snippet=snippet,
                )
            )

        self.generic_visit(node)


def find_call_sites_in_file(
    file_path: Path,
    relative_path: str,
    module_prefix: str = "",
) -> List[CallSite]:
    """Find all function call sites in a python file."""
    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        tree = ast.parse(content, filename=relative_path)
        visitor = CallVisitor(relative_path, lines, module_prefix)
        visitor.visit(tree)
        return visitor.call_sites
    except Exception:
        return []


def analyze_direct_callers(
    repo_dir: Path,
    changed_symbols: List[Symbol],
    all_modules: Dict[str, ParsedModuleInfo],
) -> Tuple[List[Symbol], List[Relationship], List[Evidence], List[str]]:
    """Conservatively detect direct callers for changed symbols across all repo modules.

    Returns:
        (affected_symbols, relationships, evidence_list, limitations)
    """
    if not changed_symbols:
        return [], [], [], []

    # Map target symbol names to changed symbols
    # A target name can match a function name (e.g. 'calculate_total')
    # and we check if caller file imports or defines it
    changed_by_name: Dict[str, List[Symbol]] = {}
    changed_by_qual: Dict[str, Symbol] = {}

    for sym in changed_symbols:
        changed_by_qual[sym.qualified_name] = sym
        changed_by_name.setdefault(sym.name, []).append(sym)

    affected_symbols_map: Dict[str, Symbol] = {}
    relationships: List[Relationship] = []
    evidence_list: List[Evidence] = []
    limitations: List[str] = [
        "Direct caller detection is conservative and static; dynamic calls and complex dispatch are omitted."
    ]

    # Inspect all python files in repo
    py_files = sorted(list(repo_dir.rglob("*.py")), key=lambda p: str(p))

    for py_file in py_files:
        rel_path = str(py_file.relative_to(repo_dir)).replace("\\", "/")
        if "venv" in rel_path or ".git" in rel_path or "__pycache__" in rel_path:
            continue

        module_info = all_modules.get(rel_path)
        if not module_info or module_info.has_syntax_error:
            continue

        # Extract call sites
        call_sites = find_call_sites_in_file(py_file, rel_path)

        for site in call_sites:
            target_candidates = changed_by_name.get(site.target_name, [])
            if not target_candidates:
                continue

            for target_sym in target_candidates:
                # Resolve if this call site confidently refers to target_sym
                is_match = False

                # Case A: Same file
                if rel_path == target_sym.file_path:
                    is_match = True

                # Case B: Imported from module
                if not is_match and site.target_name in module_info.imports:
                    imported_target = module_info.imports[site.target_name]
                    # e.g., 'changestory_sample.calculator.calculate_total'
                    if (
                        target_sym.qualified_name.endswith(imported_target)
                        or imported_target.endswith(target_sym.name)
                        or target_sym.name == imported_target.split(".")[-1]
                    ):
                        is_match = True

                # Case C: Star import present from target's package
                if not is_match and module_info.star_imports:
                    # Conservative check if target module package matches
                    target_mod = target_sym.file_path.replace("/", ".").replace(".py", "")
                    if any(target_mod.startswith(pkg) for pkg in module_info.star_imports):
                        is_match = True

                if is_match:
                    caller_qual = site.caller_symbol or f"{rel_path}:<module>"
                    # Don't create self-loop relationships on same symbol
                    if caller_qual == target_sym.qualified_name:
                        continue

                    # Record caller as affected symbol if it's a real symbol in module_info
                    caller_obj: Optional[ParsedSymbolInfo] = None
                    for s in module_info.symbols:
                        if s.qualified_name == caller_qual or caller_qual.endswith(s.name):
                            caller_obj = s
                            break

                    caller_id = f"sym_{rel_path}_{caller_qual}_{site.line}".replace("/", "_").replace(".", "_")
                    if caller_obj:
                        aff_sym = Symbol(
                            id=f"sym_{rel_path}_{caller_obj.qualified_name}_{caller_obj.start_line}".replace("/", "_").replace(".", "_"),
                            name=caller_obj.name,
                            qualified_name=caller_obj.qualified_name,
                            type=caller_obj.symbol_type,
                            file_path=rel_path,
                            start_line=caller_obj.start_line,
                            end_line=caller_obj.end_line,
                            parent_class=caller_obj.parent_class,
                        )
                    else:
                        aff_sym = Symbol(
                            id=caller_id,
                            name=caller_qual.split(".")[-1],
                            qualified_name=caller_qual,
                            type="function",
                            file_path=rel_path,
                            start_line=site.line,
                            end_line=site.line,
                        )

                    affected_symbols_map[aff_sym.id] = aff_sym

                    # Record relationship
                    rel = Relationship(
                        source=aff_sym.qualified_name,
                        target=target_sym.qualified_name,
                        relationship="calls",
                        evidence=RelationshipEvidence(
                            file_path=rel_path,
                            line=site.line,
                            snippet=site.snippet,
                        ),
                    )
                    # Check duplicate relationship
                    if not any(
                        r.source == rel.source and r.target == rel.target and r.evidence and r.evidence.line == site.line
                        for r in relationships
                    ):
                        relationships.append(rel)

                    # Record evidence
                    ev_id = f"ev_call_{rel_path}_{site.line}_{target_sym.name}".replace("/", "_").replace(".", "_")
                    evidence_list.append(
                        Evidence(
                            id=ev_id,
                            kind="call_site",
                            file_path=rel_path,
                            line_start=site.line,
                            line_end=site.line,
                            symbol=aff_sym.qualified_name,
                            description=f"Direct call site of {target_sym.qualified_name} inside {aff_sym.qualified_name} at line {site.line}",
                        )
                    )

    # Sort deterministically
    affected_symbols = sorted(affected_symbols_map.values(), key=lambda s: (s.file_path, s.start_line, s.name))
    relationships.sort(key=lambda r: (r.source, r.target, r.evidence.line if r.evidence else 0))
    evidence_list.sort(key=lambda e: (e.file_path, e.line_start, e.id))

    return affected_symbols, relationships, evidence_list, limitations
