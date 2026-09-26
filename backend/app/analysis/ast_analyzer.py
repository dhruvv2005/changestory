"""Python AST Analyzer for extracting symbols and mapping changed lines to AST constructs.

Extracts functions, methods, classes, imports, and line ranges.
Maps diff changed lines to corresponding Python AST symbols.
"""

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Literal, Optional, Set, Tuple

from app.models.schemas import Evidence, Symbol


@dataclass
class ParsedSymbolInfo:
    name: str
    qualified_name: str
    symbol_type: Literal["function", "method", "class", "async_function", "async_method"]
    file_path: str
    start_line: int
    end_line: int
    parent_class: Optional[str] = None
    docstring: Optional[str] = None


@dataclass
class ParsedModuleInfo:
    file_path: str
    symbols: List[ParsedSymbolInfo] = field(default_factory=list)
    imports: Dict[str, str] = field(default_factory=dict)  # local_name -> imported_target
    star_imports: List[str] = field(default_factory=list)
    has_syntax_error: bool = False
    error_message: Optional[str] = None


class SymbolVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str, module_prefix: str = ""):
        self.file_path = file_path.replace("\\", "/")
        self.module_prefix = module_prefix
        self.symbols: List[ParsedSymbolInfo] = []
        self.imports: Dict[str, str] = {}
        self.star_imports: List[str] = []
        self.class_stack: List[str] = []

    def _get_qualified_name(self, name: str) -> str:
        parts = []
        if self.module_prefix:
            parts.append(self.module_prefix)
        if self.class_stack:
            parts.extend(self.class_stack)
        parts.append(name)
        return ".".join(parts)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            asname = alias.asname or alias.name
            self.imports[asname] = alias.name
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        module = node.module or ""
        for alias in node.names:
            if alias.name == "*":
                self.star_imports.append(module)
            else:
                asname = alias.asname or alias.name
                full_name = f"{module}.{alias.name}" if module else alias.name
                self.imports[asname] = full_name
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        end_line = getattr(node, "end_lineno", node.lineno)
        qual_name = self._get_qualified_name(node.name)
        sym = ParsedSymbolInfo(
            name=node.name,
            qualified_name=qual_name,
            symbol_type="class",
            file_path=self.file_path,
            start_line=node.lineno,
            end_line=end_line,
            parent_class=self.class_stack[-1] if self.class_stack else None,
            docstring=ast.get_docstring(node),
        )
        self.symbols.append(sym)

        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._record_function(node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._record_function(node, is_async=True)

    def _record_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, is_async: bool):
        end_line = getattr(node, "end_lineno", node.lineno)
        qual_name = self._get_qualified_name(node.name)

        if self.class_stack:
            sym_type: Literal["function", "method", "class", "async_function", "async_method"] = (
                "async_method" if is_async else "method"
            )
            parent = self.class_stack[-1]
        else:
            sym_type = "async_function" if is_async else "function"
            parent = None

        sym = ParsedSymbolInfo(
            name=node.name,
            qualified_name=qual_name,
            symbol_type=sym_type,
            file_path=self.file_path,
            start_line=node.lineno,
            end_line=end_line,
            parent_class=parent,
            docstring=ast.get_docstring(node),
        )
        self.symbols.append(sym)

        # Still visit nested definitions
        self.generic_visit(node)


def parse_python_source(source_code: str, file_path: str, module_prefix: str = "") -> ParsedModuleInfo:
    """Parse python code string into module info and symbols."""
    clean_path = file_path.replace("\\", "/")
    try:
        tree = ast.parse(source_code, filename=clean_path)
    except SyntaxError as e:
        return ParsedModuleInfo(
            file_path=clean_path,
            has_syntax_error=True,
            error_message=f"Python file could not be parsed because of a syntax error at line {e.lineno}: {e.msg}",
        )
    except Exception as e:
        return ParsedModuleInfo(
            file_path=clean_path,
            has_syntax_error=True,
            error_message=f"Python file could not be parsed: {str(e)}",
        )

    visitor = SymbolVisitor(clean_path, module_prefix=module_prefix)
    visitor.visit(tree)

    # Sort symbols deterministically by start_line then name
    visitor.symbols.sort(key=lambda s: (s.start_line, s.name))

    return ParsedModuleInfo(
        file_path=clean_path,
        symbols=visitor.symbols,
        imports=visitor.imports,
        star_imports=visitor.star_imports,
        has_syntax_error=False,
    )


def parse_python_file(absolute_file_path: Path, relative_file_path: str, module_prefix: str = "") -> ParsedModuleInfo:
    """Read and parse python file from filesystem."""
    try:
        content = absolute_file_path.read_text(encoding="utf-8")
        return parse_python_source(content, relative_file_path, module_prefix)
    except FileNotFoundError:
        return ParsedModuleInfo(
            file_path=relative_file_path,
            has_syntax_error=True,
            error_message=f"File not found: {relative_file_path}",
        )
    except Exception as e:
        return ParsedModuleInfo(
            file_path=relative_file_path,
            has_syntax_error=True,
            error_message=f"Could not read python file: {str(e)}",
        )


def map_changed_lines_to_symbols(
    module_info: ParsedModuleInfo,
    changed_lines: List[int],
) -> Tuple[List[Symbol], List[Evidence], List[str]]:
    """Map line numbers that were modified in the diff to AST symbols.

    Returns:
        (changed_symbols, evidence_list, limitations)
    """
    if module_info.has_syntax_error:
        limitation = module_info.error_message or "Syntax error in file."
        return [], [], [limitation]

    matched_symbols: Dict[str, Symbol] = {}
    evidence_list: List[Evidence] = []
    limitations: List[str] = []
    unmapped_lines: List[int] = []

    # Map lines from deepest symbol (e.g. method first, then class, etc.)
    # We sort symbols with methods/functions preferred over containing classes
    def symbol_priority(s: ParsedSymbolInfo) -> Tuple[int, int]:
        # Narrower line span comes first
        span = s.end_line - s.start_line
        type_rank = 1 if "method" in s.symbol_type or "function" in s.symbol_type else 2
        return (type_rank, span)

    sorted_symbols = sorted(module_info.symbols, key=symbol_priority)

    for line in changed_lines:
        found_for_line = False
        for s in sorted_symbols:
            if s.start_line <= line <= s.end_line:
                stable_id = f"sym_{s.file_path}_{s.qualified_name}_{s.start_line}".replace("/", "_").replace(".", "_")
                if stable_id not in matched_symbols:
                    matched_symbols[stable_id] = Symbol(
                        id=stable_id,
                        name=s.name,
                        qualified_name=s.qualified_name,
                        type=s.symbol_type,
                        file_path=s.file_path,
                        start_line=s.start_line,
                        end_line=s.end_line,
                        parent_class=s.parent_class,
                    )

                evidence_id = f"ev_line_{s.file_path}_{line}".replace("/", "_").replace(".", "_")
                evidence_list.append(
                    Evidence(
                        id=evidence_id,
                        kind="changed_line",
                        file_path=s.file_path,
                        line_start=line,
                        line_end=line,
                        symbol=s.qualified_name,
                        description=f"Changed line {line} maps to symbol {s.qualified_name} ({s.symbol_type})",
                    )
                )
                found_for_line = True
                break

        if not found_for_line:
            unmapped_lines.append(line)
            # Create a file/line level evidence
            evidence_id = f"ev_line_{module_info.file_path}_{line}".replace("/", "_").replace(".", "_")
            evidence_list.append(
                Evidence(
                    id=evidence_id,
                    kind="changed_line",
                    file_path=module_info.file_path,
                    line_start=line,
                    line_end=line,
                    symbol=None,
                    description=f"Changed line {line} falls outside detected symbols (e.g. module level)",
                )
            )

    if unmapped_lines:
        limitations.append(
            f"{module_info.file_path}: Lines {unmapped_lines} are outside detected function or class definitions."
        )

    # Sort deterministically
    changed_symbol_list = sorted(matched_symbols.values(), key=lambda s: (s.file_path, s.start_line, s.name))
    evidence_list.sort(key=lambda e: (e.file_path, e.line_start, e.id))

    return changed_symbol_list, evidence_list, limitations
